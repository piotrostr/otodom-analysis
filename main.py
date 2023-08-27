import pandas as pd
import json
import matplotlib.pyplot as plt

from lib import get_pages, get_items_from_page, preprocess_items_df, HowCloseIsItService


def show_best_offers(df: pd.DataFrame):
    pd.set_option('max_colwidth', 100)
    df[df['address'].notna()].sort_values(by="price_per_m2")[(
        df['price'] >= 0) & (df['price'] <= 500_000)].head(30)


def plot(df: pd.DataFrame):
    # Scatter plot
    fig, ax = plt.subplots()
    ax.scatter(df['floor_size'], df['price'])
    ax.set_xlabel('Floor Size (m^2)')
    ax.set_ylabel('Price (PLN)')
    ax.set_title('Price vs Floor Size')

    plt.show()


if __name__ == '__main__':
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
    for address in df['address'].values:
        res = how_close_service.geocode(address)
        coords.append(how_close_service.response_to_coords(res))

    df['coords'] = coords
    out = how_close_service.get_distance_to_nearest_skm_station(
        df.iloc[0].coords,
    )
    with open("out.json", "w+") as f:
        # pretty print json
        f.write(json.dumps(out, indent=4))
        from pprint import pprint
        pprint(out)
