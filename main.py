#!/usr/bin/env python3

import pandas as pd

from pprint import pprint
from lib import HowCloseIsItService, get_items_from_page, get_pages, preprocess_items_df


def show_best_offers(df: pd.DataFrame):
    pd.set_option("max_colwidth", 100)
    df[df["address"].notna()].sort_values(by="price_per_m2")[
        (df["price"] >= 0) & (df["price"] <= 500_000)
    ].head(30)


def get_ammenities_df(how_close_service: HowCloseIsItService, use_cache=False):
    zabki = how_close_service.get_all_of_ammenity(
        "zabka",
        use_cache=use_cache,
    )
    biedronki = how_close_service.get_all_of_ammenity(
        "biedronka",
        use_cache=use_cache,
    )
    lidle = how_close_service.get_all_of_ammenity(
        "lidl",
        use_cache=use_cache,
    )
    stacje = how_close_service.get_all_of_ammenity(
        "stacja paliw",
        use_cache=use_cache,
    )
    restauracje = how_close_service.get_all_of_ammenity(
        "restauracja",
        use_cache=use_cache,
    )
    skm = how_close_service.get_all_of_ammenity(
        "skm",
        use_cache=use_cache,
    )
    pociagi = how_close_service.get_all_of_ammenity(
        "pociag",
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

    ammenities_df = get_ammenities_df(
        how_close_service,
        use_cache=True,
    )
    print(ammenities_df["ammenity"].unique())
    exit()

    origin = df.iloc[0]["coords"]
    dest = ammenities_df.iloc[0]["coords"]

    for origin in df["coords"].values:
        for dest in ammenities_df[["coords"]].values:
            distance = how_close_service.get_distance(
                [origin], [dest], mode="walking")
            print(distance)
    distance = how_close_service.get_distance([origin], [dest], mode="walking")
    print(distance)
