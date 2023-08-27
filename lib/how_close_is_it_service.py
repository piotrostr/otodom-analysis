import os
import pickle
import googlemaps

Coords = list[float]  # [lat, lng]

GeocodeResponse = dict

Cache = dict[str, GeocodeResponse]


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
                print(f"Loaded HowCloseIsIt cache of length: {len(cache)}")
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
        assert res['status'] == 'OK'
        while "next_page_token" in res:
            new_res = self.gmaps.places(  # type: ignore
                page_token=res['next_page_token'],
            )
            res['results'] += new_res['results']
            if "next_page_token" in new_res:
                res['next_page_token'] = new_res['next_page_token']
            else:
                del res['next_page_token']

        def format_res(res):
            return [

            ]
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
