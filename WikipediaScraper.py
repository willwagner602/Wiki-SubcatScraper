__author__ = 'wwagner'

import os
import logging
import time
import sys

import urllib.request
import socket
import sqlalchemy
import requests
from bs4 import BeautifulSoup
from DB import Image
from sqlalchemy.orm import sessionmaker

logging.basicConfig(filename='PlaneScraper.log', level=logging.DEBUG)

wikipedia_base = 'https://commons.wikimedia.org'
aircraft_page = wikipedia_base + '/wiki/Category:Aircraft_by_location_by_aircraft_type'
link_class = 'CategoryTreeLabel  CategoryTreeLabelNs14 CategoryTreeLabelCategory'

image_directory = 'A:\Projects\PycharmProjects\PlaneScraper\images'


def get_page(page):
    """
    A simple wrapper around the BeautifulSoup.get function.
    :param page:
    :return HTML document:
    """
    try:
        return BeautifulSoup(requests.get(page).text.encode('ascii', 'replace'), 'html.parser')
    except requests.exceptions.ConnectionError:
        time.sleep(5)
        return get_page(page)


def combine_ResultsSet(ResultsSet):
    text = ''
    for entry in ResultsSet:
        text += entry.text
    return text


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
        return False, False

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
        attribution_text = 'The copyright holder of this file allows anyone to use it for any purpose,' +\
                           'provided that the copyright holder is properly attributed.'
        if cc2_text in full_license:
            short_license = full_license[full_license.find(cc2_text):full_license.find('license.') + 8]
        elif attribution_text in full_license:
            short_license = attribution_text
        else:
            logging.debug('No license found in Creative Commons 2 format')
            logging.debug(full_license)
            short_license = False
        return short_license, full_license

    # parse common layouts for Public Domain
    elif page.find('table', class_='layouttemplate mw-content-ltr'):
        full_license = ' '.join(combine_ResultsSet(page.find_all('table',
                                                                 class_='layouttemplate mw-content-ltr')).split())
        public_domain_text = ['This work is in the public domain in the United States',
                              'This work has been released into the public domain',
                              'I, the copyright holder of this work, release this work into the public domain']
        federal_govt_text = 'a work of the U.S. federal government'
        if any(text in full_license for text in public_domain_text):
            short_license = 'Public Domain'
        elif federal_govt_text in full_license:
            short_license = 'Public Domain - Federal Government'
        else:
            logging.debug('No license found in Public Domain format')
            logging.debug(full_license)
            short_license = False
        return short_license, full_license

    # If the pattern isn't matched by any of these, return placeholders.  These should trigger an error up the line
    else:
        print("Failed to find license")
        return False, False


def download_image(location, file_name, url, timeout=1):

    socket.setdefaulttimeout(timeout)

    os.chdir(image_directory)
    try:
        os.chdir(location)
    except FileNotFoundError:
        os.mkdir(location)
        os.chdir(location)
    try:
        urllib.request.urlretrieve(url, file_name)
    except (urllib.error.URLError, socket.timeout):
        logging.debug("Failed to download picture: " + url)

def find_extension(file_name, extension_buffer=''):
    while file_name[-1] != '.':
        return find_extension(file_name[:-1], extension_buffer = file_name[-1] + extension_buffer)
    return '.' + extension_buffer

def generate_local_file_name(remote_file_name):
    # if name length isn't an issue, just return the whole file name
    if len(remote_file_name) < 50:
        return remote_file_name
    else:
        # truncate file name and return with correct file extension
        extension = find_extension(remote_file_name)
        return remote_file_name[:50 - len(extension)] + extension


def commit_to_database(session, image_object, commit_count=0):
    if commit_count < 10:
        try:
            session.add(image_object)
            session.commit()
        except sqlalchemy.exc.OperationalError:
            commit_to_database(session, image_object, commit_count=commit_count+1)
    else:
        print("Failed to commit object to database:", image_object)


def get_image_and_info(image_page, folder_name):
    page = get_page(image_page)

    # get picture info
    try:
        author = page.find('a', class_='new').text
    except AttributeError:
        try:
            author = page.find('td', id='fileinfotpl_aut').text
        except AttributeError:
            author = "Author not found"
    name = generate_local_file_name(image_page[image_page.find('File:') + 5:])
    try:
        image_url = page.find('div', class_='fullImageLink').contents[0]['href']
    except AttributeError:
        print("Could not find image on page", image_page)
    image_page = image_page
    short_license, full_license = get_license_table(page)

    if not short_license:
        new_image = Image(image_page, image_url, name, 'License not found', full_license, folder_name, author)
    else:
        new_image = Image(image_page, image_url, name, short_license, full_license, folder_name, author)

    # save this object to the database
    session.add(new_image)
    session.commit()

    # download and save the image
    # download_image(folder_name, name, image_url)

    return True


def get_downloaded_image_count(folder_name):
    current_dir = os.getcwd()
    try:
        os.chdir(r'A:\Projects\PycharmProjects\PlaneScraper\images\\' + folder_name)
        image_count = len([x for x in os.listdir() if '.' in x])
    except FileNotFoundError:
        image_count = 0
    os.chdir(current_dir)
    return image_count


def clean_folder_name(name):
    """ Returns a name that can be used for valid windows path"""
    new_name = ""
    reserved_characters = ":;><\/|?*"
    for char in name:
        if char not in reserved_characters:
            new_name += char
    return new_name


def count_categories(href, depth=0, folder_name='', subcat_name=1, counts=None):
    """
    Recursively finds subcategory page links, stopping when reaching a final image.  Takes a specific level of subcat
    to use for folder naming on local drive.
    :param href:
    :return:
    """

    skip_pages = []

    if counts is None:
        subcategory_counts = {}
    else:
        subcategory_counts = counts
    page = get_page(href)
    max_count = 50

    # create a list of all subcategories below this page
    subcategories = []
    for link in page.find_all('a', class_=link_class):
            subcategories.append(wikipedia_base + link['href'])

    # if we're on the correct level of subcategory, set the folder name
    if depth == subcat_name:
        title = page.find('title').text
        folder_name = title[title.find(':') + 1: title.find(' -')].replace(' ', '_')
        folder_name = folder_name[:folder_name.find('_by')]
        print(folder_name)

    # if this folder hasn't been counted already, add it to the list with a count of 0
    if folder_name not in subcategory_counts:
        subcategory_counts[folder_name] = 0

    # if there are subcategories, and user hasn't chosen to skip this category, recursively search those pages
    if subcategory_counts[folder_name] > max_count:
        return
    elif subcategories and folder_name not in skip_pages:
        print(folder_name + ': ', subcategory_counts[folder_name])
        for href in subcategories:
            if subcategory_counts[folder_name] < max_count:
                count_categories(href, depth=depth+1, folder_name=folder_name, counts=subcategory_counts)
            else:
                break

    # base case - at a bottom level page without subcategories, count the number of images
    # and add them to the list for this folder until we have at least max_count
    elif subcategory_counts[folder_name] < max_count:
        print(folder_name + ': ', subcategory_counts[folder_name])
        subcategory_counts[folder_name] += len(page.find_all('a', class_='image'))
        print(subcategory_counts[folder_name])


def download_subcategories(href, picture_counts=None, depth=0, folder_name='', subcategory_name=1, image_limit=sys.maxsize,
                           completed_folders=None, overflow_folders=None):
    """
    Recursively finds subcategory page links, stopping when reaching a final image.  Takes a specific level of subcat
    to use for folder naming on local drive.
    :param href:
    :return dictionary of folder names and pictures downloaded, list of folder names that have pictures over
    specified limit:
    """

    if picture_counts is None:
        picture_counts = {}
    else:
        picture_counts = picture_counts

    if completed_folders is None:
        completed_folders = []
    else:
        completed_folders = completed_folders

    if overflow_folders is None:
        overflow_folders = []
    else:
        overflow_folders = overflow_folders

    # create a list of all subcategories below this page
    subcategories = []
    try:
        page = get_page(href)
    except requests.exceptions.ConnectionError:
        print("Failed to get page:", href)
        return

    if depth == subcategory_name:
        title = page.find('title').text
        folder_name = title[title.find(':') + 1: title.find(' -')].replace(' ', '_')
        folder_name = clean_folder_name(folder_name[:folder_name.find('_by')])
        # figure out how many pictures we have for this folder already downloaded
        picture_counts[folder_name] = get_downloaded_image_count(folder_name)
        print('"' + folder_name + '", : ', href)

    for link in page.find_all('a', class_=link_class):
        subcategories.append(wikipedia_base + link['href'])

    # 2 options - either we want to skip this because we already have enough, or get the image and info
    # for folders not yet added to picture_counts, or who we have collected fewer than the limit, collect them
    # as long as we aren't explicitly told to skip them
    if (not picture_counts or picture_counts[folder_name] < image_limit) and folder_name not in completed_folders:
        # if there are subcategories, recursively analyze them
        if subcategories:
            for href in subcategories:
                download_subcategories(href, picture_counts=picture_counts, depth=depth+1, folder_name=folder_name,
                                           completed_folders=completed_folders, overflow_folders=overflow_folders)

        # base case - at a bottom level page without subcategories, count the number of images
        # and add them to the list for this folder until we have at least the image limit
        else:
            for link in page.find_all('a', class_='image'):
                if picture_counts[folder_name] < image_limit:

                    # get list of already downloaded image pages
                    already_downloaded_images = []
                    for image in session.query(Image.image_page):
                        already_downloaded_images.append(image[0])

                    # if this particular image hasn't been downloaded yet, get it's info and
                    # add it to the count downloaded for this folder
                    link_url = wikipedia_base + link['href']
                    if link_url not in already_downloaded_images:
                        get_image_and_info(link_url, folder_name)
                        picture_counts[folder_name] += 1
    else:
        overflow_folders.append(folder_name)

    return picture_counts, overflow_folders

if __name__ == '__main__':

    # setup SQL alchemy connection
    engine = sqlalchemy.create_engine('sqlite:///' + os.getcwd() + '\\images.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    skip_folders = ["A-10_Thunderbolt_II",
                    "A-4_Skyhawk",
                    "A-6_Intruder",
                    "AC-130_Hercules",
                    "Aero_Commander_aircraft",
                    "Aero_Vodochody_aircraft",
                    "AgustaWestland_aircraft",
                    "AH-64_Apache",
                    "Airbus_A330_MRTT",
                    "Airbus_aircraft",
                    "Airspeed_AS.57_Ambassador",
                    "Alpha_Jet",
                    "Antonov_aircraft",
                    "ARCHIVE",
                    "ATR_aircraft",
                    "AV-8B_Harrier",
                    "Aviat_aircraft",
                    "Avro_aircraft",
                    "B-66_Destroyer",
                    "BAC_aircraft",
                    "BAE_aircraft",
                    "BAe_ATP",
                    "Beechcraft_aircraft",
                    "Bell_aircraft",
                    "Beriev_aircraft",
                    "Boeing_747SP",
                    "Boeing_aircraft",]

    # get counts of pages!
    counts, overflow = download_subcategories(aircraft_page, completed_folders=skip_folders)
    print(counts)
    print(overflow)