import os
import pickle
import googlemaps

from itertools import chain
from typing import Any

Coords = list[float]  # [lat, lng]

GeocodeResponse = dict

Cache = dict[str, GeocodeResponse]

Ammenity = dict[str, Any]  # place_id: { name, coords, address, rating, ... }
AmmenitiesCache = dict[str, Ammenity]


class HowCloseIsItService:

    """
    defining a class for this for caching
    """

    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    def __init__(self):
        self._cache = self._load_cache()
        self._ammenities_cache: AmmenitiesCache = self._load_ammenities_cache()
        self.gmaps = googlemaps.Client(key=self.GOOGLE_MAPS_API_KEY)

    def _load_cache(self) -> Cache:
        if os.path.exists("cache.pkl"):
            with open("cache.pkl", "rb") as f:
                cache = pickle.load(f)
                print(f"Loaded Geocode cache of length: {len(cache)}")
                return cache
        else:
            return {}

    def _load_ammenities_cache(self) -> AmmenitiesCache:
        if os.path.exists("ammenities_cache.pkl"):
            with open("ammenities_cache.pkl", "rb") as f:
                ammenities_cache = pickle.load(f)
                print(
                    f"Loaded Ammenities cache of length: {len(ammenities_cache)}")
                return ammenities_cache
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

    def get_all_of_ammenity(self, ammenity: str = "zabka", dry_run=False):
        # the coordinates might be useful so that you don't repeat if the coordinates have been used
        # just read-in to go easy on the free-tier
        if ammenity not in self._ammenities_cache:
            self._ammenities_cache[ammenity] = {}

        responses = []
        res = self._make_places_request(ammenity)
        responses.append(res)
        i = 0
        while "next_page_token" in res:
            print(res["status"])
            res = self._make_places_request(ammenity, res["next_page_token"])
            responses.append(res)
            if dry_run:
                i += 1
                if i > 3:
                    break

        places = list(
            chain(
                *[self._process_places_response(res) for res in responses],
            )
        )

        for place in places:
            if place['place_id'] in self._ammenities_cache[ammenity]:
                print(f"Skipping {place['place_id']}")
                continue
            self._ammenities_cache[ammenity][place["place_id"]] = place

        with open("ammenities_cache.pkl", "wb+") as f:
            pickle.dump(self._ammenities_cache, f)

        return self._ammenities_cache[ammenity]

    def _make_places_request(self, ammenity: str = "", page_token: str = ""):
        res = self.gmaps.places_nearby(  # type: ignore
            keyword=ammenity,
            location=self.city_center(),
            radius=10_000,
            page_token=page_token,
        )
        assert res["status"] == "OK"
        return res

    def _process_places_response(self, res: dict) -> list[dict]:
        """
        extract just the name, coordinates, address and rating in
        a single-level dict

        :param res: the response from the Google Maps Places API
        :return: a dict with the above mentioned fields

        ```Python
        {
            "place_id": "123",
            "name": "Zabka",
            "coords": [54.123, 18.123],
            "address": "ul. Dluga 1, Gdansk",
            "rating": 4.5
        }
        ```
        """
        assert res["status"] == "OK"
        results = [
            {
                "place_id": result["place_id"],
                "name": result["name"],
                "coords": [
                    result["geometry"]["location"]["lat"],
                    result["geometry"]["location"]["lng"],
                ],
                "address": result["vicinity"],
                "rating": result["rating"],
            }
            for result in res["results"]
        ]
        return results

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
            location=self.city_center(),
            radius=10_000,
        )
        # how to handle next pages? do we care if we would be repeating this for
        # every one of the 1000s of flats?  caching the results could work, we
        # also are looking for specific things which might even be hand-pickable
        assert res["status"] == "OK"

        def format_res(res):
            return []

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
