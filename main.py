import csv
import urllib.parse as urlparse
from urllib.parse import parse_qs
import requests
import re
from bs4 import BeautifulSoup as bs

BASE = "https://shop.prosv.ru/"
URL_PATTERN = urlparse.urljoin(BASE, "/katalog?pagenumber={}")
HEADERS = {
    "user-agent": "Chrome",
    "accept": '*/*'
}


def get_soup(url):
    r = requests.get(url, headers=HEADERS)
    return bs(r.content, 'html.parser')


def get_links(url):
    soup = get_soup(url)
    items = soup.select(".item-box .picture > a")
    for item in items:
        href = item.get('href')
        if href:
            yield urlparse.urljoin(BASE, href)


def get_max_pages():
    soup = get_soup(URL_PATTERN.format(1))
    a = soup.select_one("li.last-page > a")
    if a:
        url = urlparse.urlparse(urlparse.urljoin(BASE, a.get('href')))
        return int(parse_qs(url.query)['pagenumber'][0])
    else:
        return 1


def set_property(book, name, block):
    if block:
        book[re.sub(' +', ' ', name.strip().strip(':'))] = re.sub(' +', ' ', block.text.strip())


def get_book(url):
    soup = get_soup(url)
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


def parse():
    books = []
    max_page = get_max_pages()
    for i in range(1, max_page + 1):
        url = URL_PATTERN.format(i)
        print(f"Обрабатываю страницу {i} из {max_page}...")
        links = get_links(url)
        for link in links:
            book = get_book(link)
            books.append(book)

    keys = set()
    for book in books:
        for key in book.keys():
            keys.add(key)

    with open("res.csv", 'w') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(books)


if '__main__' == __name__:
    parse()
