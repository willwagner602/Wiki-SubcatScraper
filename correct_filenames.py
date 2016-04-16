import os
import logging

import sqlalchemy
from sqlalchemy.orm import sessionmaker

if __name__ == '__main__':

    logging.basicConfig(filename='Failed_Filenames.txt', level=logging.DEBUG)

    aircraft_page = 'https://commons.wikimedia.org/wiki/Category:Aircraft_by_location_by_aircraft_type'
    image_directory = 'A:\Projects\PycharmProjects\PlaneScraper\images\{}\{}'

    # setup SQL alchemy connection
    engine = sqlalchemy.create_engine('sqlite:///A:\Projects\PycharmProjects\Viewer\\images.sqlite3')
    Session = sessionmaker(bind=engine)
    session = Session()

    select_images = """SELECT image_id, image_page, image_url, name, location, redownload_flag FROM images"""

    images = session.execute(select_images).fetchall()
    session.close()

    last_id = 48517

    for image in images[last_id - 1:]:
        image_id = image[0]
        image_page = image[1]
        image_url = image[2]
        image_name = image[3]
        image_location = image[4]
        redownload_flag = image[5]

        corrected_name = image_page[image_page.find('File:')+5:].replace('%', '')
        print('Analyzing image name: {} with image id {}'.format(image_name, image_id))

        if corrected_name != image_name:

            print("updating image name to {}".format(corrected_name))

            # check to see if the original file exists
            file = image_directory.format(image_location, image_name)
            if os.path.isfile(file):
                new_file = image_directory.format(image_location, corrected_name)
                try:
                    os.rename(file, new_file)
                except FileNotFoundError:
                    logging.info('File: {}, \n New File: {}'.format(file, new_file))
                redownload_flag = 0

            else:
                redownload_flag = 1

            update_image = """
              UPDATE
                images
              SET
                name = '{}',
                redownload_flag = {}
              WHERE
                image_id = {}""".format(corrected_name, redownload_flag, image_id)

            try:
                engine.execute(update_image)
            except sqlalchemy.exc.OperationalError as e:
                print(e)
                print(update_image)
                exit()
