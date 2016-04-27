import os
import random

import sqlalchemy

from WikipediaScraper import download_image


def execute_db_query(query, engine):
    connection = engine.connect()
    response = engine.execute(query).fetchall()
    connection.close()

    return response


def download_aircraft_images(aircraft, engine, image_limit=50):
    aircraft_page = 'https://commons.wikimedia.org/wiki/Category:Aircraft_by_location_by_aircraft_type'
    image_directory = '/home/wbw/pycharmprojects/wiki-subcatscraper/Images/{}'

    select_images = """ SELECT
                          image_id,
                          image_url,
                          name,
                          location
                        FROM
                          images
                        WHERE
                          aircraft = '{}'
                          AND redownload_flag = 1""".format(aircraft)

    images = execute_db_query(select_images, engine)

    # randomize images so it's not all just the same plane
    random.shuffle(images)

    for image in images[:image_limit]:
        image_id = image[0]
        image_url = image[1]
        image_name = image[2]
        image_location = image[3]

        print(os.getcwd())

        print('Downloading image {} with image id {}'.format(image_name, image_id))

        download_image(image_directory.format(image_location), image_name, image_url)

        update_image = """UPDATE
                            images
                          SET
                            redownload_flag = 0
                          WHERE
                            image_id = {}""".format(image_id)

        engine.execute(update_image)


def download_useful_images(engine):
    image_directory = '/home/wbw/pycharmprojects/wiki-subcatscraper/Images/{}'

    useful_images = select_images = """ SELECT
                          image_id,
                          image_url,
                          name,
                          location
                        FROM
                          images
                        WHERE
                          use_flag = 1
                          and redownload_flag = 1"""

    update_image = """UPDATE
                            images
                          SET
                            redownload_flag = 0
                          WHERE
                            image_id = {}"""

    images = execute_db_query(useful_images, engine)

    for image in images:
        image_id = image[0]
        image_url = image[1]
        image_name = image[2]
        image_location = image[3]

        print('Downloading image {} with image id {}'.format(image_name, image_id))

        download_image(image_directory.format(image_location), image_name, image_url)

        engine.execute(update_image.format(image_id))


def create_folders(engine):

    folders = execute_db_query(""" SELECT
          DISTINCT
          location
        FROM
          images
        WHERE
          location != ''""", engine)

    os.mkdir('Images')
    os.chdir('Images')

    for folder in folders:
        folder = folder[0].replace('/', '_')
        os.mkdir(folder)

    engine.dispose()


def download_representative_images(engine):

    aircraft_select = """
        SELECT aircraft FROM images
        WHERE redownload_flag = 1 AND aircraft IS NOT NULL AND aircraft IN (
        SELECT aircraft FROM images
        WHERE aircraft IS NOT NULL
        GROUP BY aircraft
        HAVING SUM(CASE WHEN redownload_flag = 1 THEN 0 WHEN redownload_flag = 0 THEN 1 END) < 20)
        GROUP BY aircraft"""

    aircraft_list = execute_db_query(aircraft_select, engine)

    for aircraft in aircraft_list:
        aircraft = aircraft[0]
        download_aircraft_images(aircraft, engine)


if __name__ == '__main__':

    # setup SQL alchemy connection
    engine = sqlalchemy.create_engine('sqlite:////home/wbw/Dropbox/Programming/Projects/PlaneViewer/images.sqlite3')

    download_aircraft_images('Boeing 747', engine)

    # create_folders(engine)
    # download_useful_images(engine)
    # download_representative_images(engine)

    engine.dispose()
