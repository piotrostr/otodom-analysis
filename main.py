#!/usr/bin/env python3

import pandas as pd
import numpy as np
import simplekml

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from lib import (
    HowCloseIsItService,
    get_items_from_page,
    get_pages,
    preprocess_items_df,
    find_closest_coordinates,
)


def show_best_offers(df: pd.DataFrame):
    pd.set_option("max_colwidth", 100)
    df[df["address"].notna()].sort_values(by="price_per_m2")[
        (df["price"] >= 0) & (df["price"] <= 500_000)
    ].head(30)


def get_ammenities_df(
    how_close_service: HowCloseIsItService,
    location: list[float],
    use_cache=True,
):
    zabki = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="zabka",
        use_cache=use_cache,
    )
    biedronki = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="biedronka",
        use_cache=use_cache,
    )
    lidle = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="lidl",
        use_cache=use_cache,
    )
    stacje = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="stacja paliw",
        use_cache=use_cache,
    )
    restauracje = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="restauracja",
        use_cache=use_cache,
    )
    skm = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="skm",
        use_cache=use_cache,
    )
    pociagi = how_close_service.get_all_of_ammenity(
        location=location,
        ammenity="pociag",
        use_cache=use_cache,
    )
    return pd.DataFrame(
        [
            *zabki.values(),
            *biedronki.values(),
            *lidle.values(),
            *stacje.values(),
            *restauracje.values(),
            *skm.values(),
            *pociagi.values(),
        ]
    )


def save_klm(file_name: str, list_of_coords: list[list[float]]):
    kml = simplekml.Kml()

    for coords in list_of_coords:
        lat, lon = coords
        kml.newpoint(name="Cluster Center", coords=[(lon, lat)])

    file_path = file_name + ".kml"
    kml.save(file_path)

    print(f"KML file saved at: {file_path}")


def get_top_clusters_centers(coords: list[list[float]]):
    kmeans = KMeans(n_clusters=10, random_state=0,)
    coordinates = np.array(coords)
    kmeans.fit(coordinates)
    cluster_centers = kmeans.cluster_centers_
    cluster_labels = kmeans.labels_
    cluster_counts = np.bincount(cluster_labels)
    top_clusters_indices = np.argsort(cluster_counts)[::-1][:10]
    top_clusters_centers = cluster_centers[top_clusters_indices]
    return top_clusters_centers


if __name__ == "__main__":
    pages = get_pages(load=True)

    assert get_items_from_page(pages[2]) is not None

    all_items = []
    for page in pages:
        items = get_items_from_page(page)
        if items is not None and len(items):
            all_items += items
    all_items_df = pd.DataFrame(all_items)

    df = preprocess_items_df(all_items_df)
    print("got: ", df.shape)

    how_close_service = HowCloseIsItService()

    coords = []
    for address in df["address"].values:
        res = how_close_service.geocode(address)
        coords.append(how_close_service.response_to_coords(res))

    df["coords"] = coords

    df["distance_to_center"] = [
        how_close_service.get_distance(
            [coords],
            [how_close_service.city_center()],  # type: ignore
        )
        for coords in df["coords"].values
    ]

    print("dropping far out of center: ", len(
        df[df["distance_to_center"] > 20_000]))
    df = df[df["distance_to_center"] < 20_000]

    coordinates = df["coords"].tolist()
    save_klm("apartments", coordinates)

    def get_places_around_clusters(
            coordinates: list[list[float]],
            how_close_service: HowCloseIsItService,
    ):
        """
        get all ammenities around 10 clusters of coordinates to picture the
        region of all of the aparments

        this is useful to fill the cache of the HowCloseIsItService to return
        larger ammenities df that covers more area

        :param coordinates: array of coordinates
        :param how_close_service: HowCloseIsItService
        """
        top_clusters_centers = get_top_clusters_centers(coordinates)
        save_klm("clusters", top_clusters_centers.tolist())
        for location in top_clusters_centers:
            get_ammenities_df(
                how_close_service=how_close_service,
                location=location,
                use_cache=False,
            )

    ammenities_df = get_ammenities_df(
        how_close_service=how_close_service,
        location=how_close_service.city_center(),
        use_cache=True,
    )

    # TODO include labels of the places in the kml files
    save_klm("ammenities", ammenities_df["coords"].to_numpy().tolist())
    save_klm("biedronki", ammenities_df[ammenities_df["ammenity"]
             == "biedronka"]["coords"].to_numpy().tolist())

    for ammenity_type in ammenities_df["ammenity"].unique():
        ammenity_df = ammenities_df[ammenities_df["ammenity"] == ammenity_type]
        if ammenity_type == "restauracja":
            print("filtering out restaurants with rating less than 4")
            ammenity_df = ammenity_df[ammenity_df["rating"] >= 4]
        df["closest_" + ammenity_type] = [
            find_closest_coordinates(
                np.array(coords),
                ammenity_df["coords"].to_numpy(),
            )
            for coords in df["coords"].values
        ]

        apartment_coords = df["coords"]
        closest_ammenity_coords = df["closest_" + ammenity_type]
        distance_to_closest = []
        for apartment_coord, closest_ammenity_coord in zip(apartment_coords, closest_ammenity_coords):
            distance_to_closest.append(
                how_close_service.get_distance(
                    [apartment_coord],
                    [closest_ammenity_coord],
                )
            )
        df["distance_to_closest_" + ammenity_type] = distance_to_closest

    with open("final_df.pkl", "wb+") as f:
        df.to_pickle(f)
