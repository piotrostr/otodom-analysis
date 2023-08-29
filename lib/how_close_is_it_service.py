import os
import pickle
import googlemaps
import hashlib

from itertools import chain
from typing import Any
from pprint import pprint

Coords = list[float]  # [lat, lng]

GeocodeResponse = dict

Cache = dict[str, GeocodeResponse]

Ammenity = dict[str, Any]  # place_id: { name, coords, address, rating, ... }
AmmenitiesCache = dict[str, Ammenity]

# the str is a hash of tuple of coords (origin, dest)
DistanceCache = dict[str, float]


class HowCloseIsItService:

    """
    defining a class for this for caching
    """

    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    def __init__(self):
        self._cache = self._load_cache()
        self._ammenities_cache: AmmenitiesCache = self._load_ammenities_cache()
        self._distance_cache: DistanceCache = self._load_distance_cache()
        self.gmaps = googlemaps.Client(key=self.GOOGLE_MAPS_API_KEY)

    @staticmethod
    def _hash(obj: Any) -> str:
        return hashlib.sha256(str(obj).encode()).hexdigest()

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

    def _load_distance_cache(self) -> dict:
        if os.path.exists("distance_cache.pkl"):
            with open("distance_cache.pkl", "rb") as f:
                distance_cache = pickle.load(f)
                print(
                    f"Loaded Distance cache of length: {len(distance_cache)}")
                return distance_cache
        else:
            return {}

    def _write_to_distance_cache(self, origin: list[float], dest: list[float], meters: float):
        self._distance_cache[self._hash((origin, dest,))] = meters
        with open("distance_cache.pkl", "wb+") as f:
            pickle.dump(self._distance_cache, f)

    def _get_from_distance_cache(self, origin: list[float], dest: list[float]) -> float:
        return self._distance_cache[self._hash((origin, dest,))]

    def _is_in_distance_cache(self, origin: list[float], dest: list[float]) -> bool:
        return self._hash((origin, dest,)) in self._distance_cache

    def _is_cached(self, key: str) -> bool:
        return key in self._cache if self._cache is not None else False

    def _get_from_cache(self, key: str) -> GeocodeResponse:
        return self._cache[key]

    def _write_to_cache(self, key: str, value: GeocodeResponse):
        self._cache[key] = value
        with open("cache.pkl", "wb+") as f:
            pickle.dump(self._cache, f)

    def get_all_of_ammenity(
        self,
        location: list[float],
        ammenity: str = "zabka",
        dry_run=False,
        use_cache=False,
    ) -> Ammenity:
        # the coordinates might be useful so that you don't repeat if the coordinates have been used
        # just read-in to go easy on the free-tier
        if ammenity not in self._ammenities_cache:
            self._ammenities_cache[ammenity] = {}

        if use_cache:
            return self._ammenities_cache[ammenity]

        responses = []
        res = self._make_places_request(location=location, ammenity=ammenity)
        responses.append(res)
        used_tokens = set()
        i = 0
        try:
            while "next_page_token" in res and res["next_page_token"] not in used_tokens:
                used_tokens.add(res["next_page_token"])

                res = self._make_places_request(
                    ammenity=ammenity,
                    page_token=res["next_page_token"],
                    location=location,
                )
                responses.append(res)

                i += 1
                if i == 10:
                    # dont want to run too long, paging seems weird and no total
                    # items count returned 10 iterations seem to provide enough
                    # data, there are many repeats
                    break

                if dry_run:
                    break
        except KeyboardInterrupt:
            # do the KeyboardInterrupt to stop the paging and preserve the cache
            pass

        places = list(
            chain(
                *[self._process_places_response(res) for res in responses],
            )
        )

        for place in places:
            if place["place_id"] in self._ammenities_cache[ammenity]:
                print(f"Skipping {place['place_id']}")
                continue
            self._ammenities_cache[ammenity][place["place_id"]] = {
                **place,
                "ammenity": ammenity,
            }

        with open("ammenities_cache.pkl", "wb+") as f:
            pickle.dump(self._ammenities_cache, f)

        return self._ammenities_cache[ammenity]

    def _make_places_request(
        self,
        location: list[float],
        ammenity: str = "",
        page_token: str = "",
    ):
        res = self.gmaps.places(  # type: ignore
            query=ammenity,
            location=location,
            radius=10_000,
            page_token=page_token,
        )
        if not res["status"] == "ZERO_RESULTS":
            assert res["status"] == "OK", res
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
        results = [
            {
                "place_id": result["place_id"],
                "name": result["name"],
                "coords": [
                    result["geometry"]["location"]["lat"],
                    result["geometry"]["location"]["lng"],
                ],
                "address": result["formatted_address"],
                "rating": result["rating"],
                "types": result["types"],
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

    def get_distance(
        self,
        origin: list[float],
        dest: list[float],
        mode: str = "walking",
    ) -> float:
        """
        :param mode: 
        valid values are “driving”, “walking”, “transit” or “bicycling” this
        param is not currently used; only returning distance as of now

        :return: distance in meters
        """
        if self._is_in_distance_cache(origin, dest):
            return self._get_from_distance_cache(origin, dest)
        res = self.gmaps.distance_matrix(  # type: ignore
            origins=origin,
            destinations=dest,
            mode=mode,
        )
        print("sent distance req for ", origin, dest)
        assert res["status"] == "OK", res
        meters = res["rows"][0]["elements"][0]["distance"]["value"]
        self._write_to_distance_cache(origin, dest, meters)
        return meters

    def response_to_coords(self, response: GeocodeResponse) -> Coords:
        return [
            response[0]["geometry"]["location"]["lat"],
            response[0]["geometry"]["location"]["lng"],
        ]

    @property
    def cache(self):
        return self._cache

    @property
    def ammenities_cache(self):
        return self._ammenities_cache
