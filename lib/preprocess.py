import pandas as pd


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
