import re
import requests
import pickle
import os
import json

from bs4 import BeautifulSoup


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
        print("getting pages from pages.pkl file")
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
