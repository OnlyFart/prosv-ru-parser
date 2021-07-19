import csv
import urllib.parse as urlparse
from urllib.parse import parse_qs
import requests
from bs4 import BeautifulSoup as bs

URL = "https://shop.prosv.ru/katalog?pagenumber={}"
BASE = "https://shop.prosv.ru/"
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
    soup = get_soup(URL.format(1))
    a = soup.select_one("li.last-page > a")
    url = urlparse.urlparse(urlparse.urljoin(BASE, a.get('href')))
    return int(parse_qs(url.query)['pagenumber'][0])


def get_book(url):
    soup = get_soup(url)
    res = {
        'Название': soup.select_one("h1").text.strip(),
        'Изображение': urlparse.urljoin(BASE, soup.select_one("img[id^=main-product-img]").get('src')),
        'Url': url
    }

    annotation = soup.select_one('div.full-description-text')
    if annotation:
        res['Аннтотация'] = annotation.text.strip()

    for series in soup.select('div.series'):
        name = series.findChildren()[0].text.strip().strip(':')
        value = series.findChildren()[1].text.strip()
        res[name] = value

    for row in soup.select('table.data-table tr'):
        name = row.findChildren()[0].text.strip()
        value = row.findChildren()[1].text.strip()
        res[name] = value

    return res


def parse():
    books = []
    max_page = get_max_pages() + 1
    for i in range(1, max_page):
        url = URL.format(i)
        print(f"Обрабатываю страницу {i} из {max_page} ...")
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


parse()
