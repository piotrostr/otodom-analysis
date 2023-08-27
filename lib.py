import os
import pickle
import googlemaps
import os
import requests
import json
import pandas as pd
import requests
import re
import pickle

from bs4 import BeautifulSoup

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

Coords = list[float]  # [lat, lng]

GeocodeResponse = dict

Cache = dict[str, GeocodeResponse]


def get_page_count(soup: BeautifulSoup) -> int:
    text = str(soup)

    # Search for "page_count":XX in the text
    match = re.search('"page_count":([0-9]+)', text)

    # If a match is found, convert it to an integer
    if match:
        page_count = int(match.group(1))
        return page_count
    else:
        raise Exception("No match found.")


def get_page(
    page_number: int = 1, region: str = "pomorskie/gdansk/gdansk/gdansk"
) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    }

    params = {"viewType": "listing", "limit": 72, "page": page_number}

    r = requests.get(
        f"https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/{region}",
        headers=headers,
        params=params,
    )
    print(page_number, end=" ")
    if not r.ok:
        raise Exception(r.text)

    return r.text


def save_pages(pages: list):
    with open("pages.pkl", "wb+") as f:
        pickle.dump(pages, f)


def get_pages(load: bool = True, save: bool = True) -> list:
    if os.path.exists("pages.pkl") and load:
        with open("pages.pkl", "rb") as f:
            return pickle.load(f)
    else:
        soup = BeautifulSoup(get_page(), "lxml")

        page_count = get_page_count(soup)

        pages = []
        for i in range(1, page_count):
            import time

            time.sleep(3)
            pages.append(get_page(i))

    if save:
        save_pages(pages)

    return pages


def get_items_from_page(page: str, save: bool = True) -> list:
    """
    uses the __NEXT_DATA__ script tag to get the search results

    :param page: HTML of the page
    :param save: if True, saves the data to data.json, useful for debugging
    :return: list of items
    """
    soup = BeautifulSoup(page, "lxml")
    next_data_script = soup.find("script", {"id": "__NEXT_DATA__"})
    assert next_data_script is not None, "No __NEXT_DATA__ script tag found"
    data = json.loads(next_data_script.string)  # type: ignore
    if save:
        with open("data.json", "w+") as f:
            f.write(json.dumps(data))
    return data["props"]["pageProps"]["data"]["searchAds"]["items"]


def number_of_rooms_to_int(number_of_rooms: str) -> int | None:
    if number_of_rooms == "ONE":
        return 1
    elif number_of_rooms == "TWO":
        return 2
    elif number_of_rooms == "THREE":
        return 3
    elif number_of_rooms == "FOUR":
        return 4
    elif number_of_rooms == "FIVE":
        return 5


def preprocess_items_df(df: pd.DataFrame) -> pd.DataFrame:
    _df = pd.DataFrame()
    _df["title"] = df["title"]
    _df["price_hidden"] = df["hidePrice"]
    _df["price"] = df.apply(
        lambda x: x["totalPrice"]["value"]
        if x["hidePrice"] == False else None, axis=1  # type: ignore
    )
    _df["price_per_m2"] = df.apply(
        lambda x: x["pricePerSquareMeter"]["value"]
        if x["hidePrice"] == False else None,  # type: ignore
        axis=1,
    )
    _df["floor_size"] = df["areaInSquareMeters"]
    _df["city"] = df["location"].apply(lambda x: x["address"]["city"]["name"])
    _df["address"] = df["locationLabel"].apply(lambda x: x["value"])
    _df["number_of_rooms"] = df["roomsNumber"].apply(
        lambda x: number_of_rooms_to_int(x)
    )

    # fill the number of rooms with the floor size divided by 35
    # TODO 35 is an arbitrary number
    # could use the sample mean instead
    # the price and floor_size are still relevant from those entries, so it's
    # better to keep them
    _df["number_of_rooms"].fillna(_df["floor_size"] / 35, inplace=True)

    _df["url"] = df["slug"].map(
        lambda x: "https://otodom.pl/pl/oferta/{}".format(x),
    )

    # get rid of properties with hidden price
    _df = _df[_df["price_hidden"] == False]

    return _df


class HowCloseIsItService:
    """
    defining a class for this for caching
    """

    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    def __init__(self):
        self._cache = self._load_cache()
        self.gmaps = googlemaps.Client(key=self.GOOGLE_MAPS_API_KEY)

    def _load_cache(self) -> Cache:
        if os.path.exists("cache.pkl"):
            with open("cache.pkl", "rb") as f:
                cache = pickle.load(f)
                print(f"Loaded cache of length: {len(cache)}")
                return cache
        else:
            return {}

    def _is_cached(self, key: str) -> bool:
        return key in self._cache if self._cache is not None else False

    def _get_from_cache(self, key: str) -> GeocodeResponse:
        return self._cache[key]

    def _write_to_cache(self, key: str, value: GeocodeResponse):
        self._cache[key] = value
        with open("cache.pkl", "wb+") as f:
            pickle.dump(self._cache, f)

    def city_center(self) -> Coords:
        return self.response_to_coords(self.geocode("Gdańsk"))

    def geocode(self, address: str) -> GeocodeResponse:
        if self._is_cached(address):
            return self._get_from_cache(address)
        geocode_result = self.gmaps.geocode(address)  # type: ignore
        if geocode_result is not None:
            self._write_to_cache(address, geocode_result)
        return geocode_result

    def get_car_distance(self, origin: Coords, dest: Coords) -> Coords:
        return []

    def get_walking_distance(self) -> Coords:
        return []

    def get_distance(self, origin, dest) -> Coords:
        return []

    def get_distance_to_center(self, coords: Coords) -> Coords:
        gdansk_coords = self.city_center()
        return self.get_distance(coords, gdansk_coords)

    def get_distance_to_nearest_skm_station(self, coords: Coords) -> Coords:
        res = self.gmaps.places(  # type: ignore
            type="train_station",
            query="SKM",
            location=self.city_center(),
            radius=10_000,
        )
        if "next_page_token" in res:
            pass
        return res

    def get_distance_to_nearest_zabka(self, coords: Coords) -> Coords:
        return []

    def get_distance_to_nearest_store(self, coords: Coords) -> Coords:
        return []

    def get_distance_to_nearest_train_station(self, coords: Coords) -> Coords:
        return []

    def response_to_coords(self, response: GeocodeResponse) -> Coords:
        return [
            response[0]["geometry"]["location"]["lat"],
            response[0]["geometry"]["location"]["lng"],
        ]


def run_preds(df: pd.DataFrame):
    X = df[["floor_size", "number_of_rooms"]].to_numpy()
    y = df["price"].to_numpy()

    # Step 2: Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    print(X_train.shape, y_train.shape)

    # Step 3: Model Training
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Step 4: Model Evaluation
    y_pred = model.predict(X_test)
    print(
        f"Root Mean Squared Error: {mean_squared_error(y_test, y_pred, squared=False)}"
    )
