__author__ = 'wwagner'

import requests
from bs4 import BeautifulSoup

wikipedia_base = 'https://commons.wikimedia.org'
aircraft_page = wikipedia_base + '/wiki/Category:Aircraft'


def get_page(page):
    return BeautifulSoup(requests.get(page).text.encode('ascii', 'replace'), 'html.parser')


def get_image_and_info(href):
    print(href['href'])


def find_subcategories(href):
    """
    Recursively finds subcategory page links, stopping when reaching a final image.
    :param href:
    :return:
    """
    link_class = 'CategoryTreeLabel  CategoryTreeLabelNs14 CategoryTreeLabelCategory'
    subcategories = []
    page = get_page(href)
    for link in page.find_all('a', class_=link_class):
        subcategories.append(wikipedia_base + link['href'])
    if subcategories:
        for href in subcategories:
            find_subcategories(href)
            break
    else:
        for link in page.find_all('a', class_='image'):
            get_image_and_info(wikipedia_base + link)

test = find_subcategories(aircraft_page)
print(test)