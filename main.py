import csv
import urllib.parse as urlparse
from urllib.parse import parse_qs
import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup as bs
from aiohttp import ClientSession

BASE = "https://shop.prosv.ru/"
URL_PATTERN = urlparse.urljoin(BASE, "/katalog?pagenumber={}")
HEADERS = {
    "user-agent": "Chrome"
}


async def get_soup(session: ClientSession, url: str) -> bs:
    r = await session.get(url, headers=HEADERS)
    return bs(await r.text(), 'html.parser')


async def get_links(session: ClientSession, url: str):
    soup = await get_soup(session, url)
    items = soup.select(".item-box .picture > a")
    links = []
    for item in items:
        href = item.get('href')
        if href:
            links.append(urlparse.urljoin(BASE, href))

    return links


async def get_max_pages(session: aiohttp.ClientSession) -> int:
    soup = await get_soup(session, URL_PATTERN.format(1))
    a = soup.select_one("li.last-page > a")
    if a:
        url = urlparse.urlparse(urlparse.urljoin(BASE, a.get('href')))
        return int(parse_qs(url.query)['pagenumber'][0])
    else:
        return 1


def set_property(book, name, block) -> None:
    if block:
        book[re.sub(' +', ' ', name.strip().strip(':'))] = re.sub(' +', ' ', block.text.strip())


async def get_book(session: aiohttp.ClientSession, url: str):
    soup = await get_soup(session, url)
    res = {
        'Изображение': urlparse.urljoin(BASE, soup.select_one("img[id^=main-product-img]").get('src')),
        'Url': url
    }

    set_property(res, 'Название', soup.select_one("h1"))
    set_property(res, 'Аннотация', soup.select_one('div.full-description-text'))
    set_property(res, 'Ваша цена', soup.select_one('span[class^=price-value]'))
    set_property(res, 'Цена без скидки', soup.select_one('div.non-discounted-price > span'))

    for series in soup.select('div.series, table.data-table tr'):
        set_property(res, series.findChildren()[0].text, series.findChildren()[1])

    return res


async def get_books(session: aiohttp.ClientSession,):
    books = []
    max_page = await get_max_pages(session)
    for i in range(1, max_page + 1):
        print(f"Обрабатываю страницу {i} из {max_page}...")
        tasks = []
        for link in await get_links(session, URL_PATTERN.format(i)):
            tasks.append(get_book(session, link))
        books.extend(await asyncio.gather(*tasks))

    return books


def save(books):
    keys = set()
    for book in books:
        for key in book.keys():
            keys.add(key)

    with open("res.csv", 'w') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(books)


async def main():
    async with aiohttp.ClientSession() as session:
        save(await get_books(session))


if '__main__' == __name__:
    asyncio.run(main())
