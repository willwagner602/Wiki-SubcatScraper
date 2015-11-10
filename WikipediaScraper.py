__author__ = 'wwagner'

import requests
from bs4 import BeautifulSoup
from DB import Image

wikipedia_base = 'https://commons.wikimedia.org'
aircraft_page = wikipedia_base + '/wiki/Category:Aircraft'
link_class = 'CategoryTreeLabel  CategoryTreeLabelNs14 CategoryTreeLabelCategory'


def get_page(page):
    """
    A simple wrapper around the BeautifulSoup.get function.
    :param page:
    :return HTML document:
    """
    return BeautifulSoup(requests.get(page).text.encode('ascii', 'replace'), 'html.parser')


def combine_ResultsSet(ResultsSet):
    text = ''
    for entry in ResultsSet:
        text += entry.text
    return text


class LicenseError(AttributeError):
    """
    Raised when license code cannot find correct text to classify license
    """


def get_license_table(page):

    # parse common layout for Creative Commons 3
    if page.find('table', class_='licensetpl_wrapper'):
        license_text = page.find('table', class_='licensetpl_wrapper').contents
        # get license type and details
        for license_line in license_text:
            if license_line.name == 'tr':
                full_license = ' '.join(license_line.text.split())
                short_license = full_license[full_license.find('licensed under the') + 19:]
                short_license = short_license[:short_license.find(".")]
        return short_license, full_license

    # parse common layout for GNU license
    elif page.find('table', class_='layouttemplate licensetpl'):
        full_license = combine_ResultsSet(page.find_all('table', class_='layouttemplate licensetpl'))
        short_license = full_license[full_license.find('terms of the') + 13:]
        short_license = short_license[:short_license.find(' only as')]
        return short_license, full_license

    #parse common layout for Creative Commons 2
    elif page.find_all('table', class_='layouttemplate licensetpl mw-content-ltr'):
        full_license = ' '.join(page.find('table', class_='layouttemplate licensetpl mw-content-ltr').text.split())
        cc2_text = 'This file is licensed under the Creative Commons'
        attribution_text = 'The copyright holder of this file allows anyone to use it for any purpose, provided that the copyright holder is properly attributed.'
        if cc2_text in full_license:
            short_license = full_license[full_license.find(cc2_text):full_license.find('license.') + 8]
        elif attribution_text in full_license:
            short_license = attribution_text
        else:
            print(full_license)
            short_license = False
        return short_license, full_license

    # parse common layouts for Public Domain
    elif page.find('table', class_='layouttemplate mw-content-ltr'):
        full_license = combine_ResultsSet(page.find_all('table', class_='layouttemplate mw-content-ltr'))
        public_domain_text = ['This work is in the public domain in the United States',
                              'This work has been released into the public domain',
                              'I, the copyright holder of this work, release this work into the public domain']
        federal_govt_text = 'a work of the U.S. federal government'
        if any(text in full_license for text in public_domain_text):
            short_license = public_domain_text
        elif federal_govt_text in full_license:
            short_license = public_domain_text
        else:
            short_license = False
        return short_license, full_license

    # If the patten isn't matched by any of these, return placeholders.  These should trigger an error up the line
    else:
        "Failed to find license"
        return False, False


def get_image_and_info(href, folder_name):
    page = get_page(href)

    # get picture info
    try:
        author = page.find('a', class_='new').text
    except AttributeError:
        try:
            author = page.find('td', id='fileinfotpl_aut').text
        except AttributeError:
            print(href)
            exit()
    name = href[href.find('File:') + 5:]
    image = page.find('div', class_='fullImageLink').contents[0]['href']
    url = href
    location = folder_name + '/' + name

    short_license, full_license = get_license_table(page)

    if not short_license:
        print('Failed to find license.')
        print(href)
        exit()

    # put this all together to create an Image object and save it to DB
    image = Image(url, name, short_license, full_license, location, author)
    print(image)


def find_subcategories(href, depth=0, folder_name='', subcat_name=2,):
    """
    Recursively finds subcategory page links, stopping when reaching a final image.  Takes a specific level of subcat
    to use for folder naming on local drive.
    :param href:
    :return:
    """
    subcategories = []
    page = get_page(href)
    if depth == subcat_name:
        title = page.find('title').text
        title = title[title.find(':') + 1: title.find(' -')].replace(' ', '_')
        folder_name = title
        print("Make folder:", title)
    for link in page.find_all('a', class_=link_class):
        subcategories.append(wikipedia_base + link['href'])
    if subcategories:
        for href in subcategories:
            find_subcategories(href, depth=depth+1, folder_name=folder_name)
    else:
        for link in page.find_all('a', class_='image'):
            get_image_and_info(wikipedia_base + link['href'], folder_name)

if __name__ == '__main__':
    find_subcategories(aircraft_page)
