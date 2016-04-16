from WikipediaScraper import download_image

import sqlalchemy
from sqlalchemy.orm import sessionmaker



if __name__ == '__main__':

    aircraft_page = 'https://commons.wikimedia.org/wiki/Category:Aircraft_by_location_by_aircraft_type'
    image_directory = 'A:\Projects\PycharmProjects\PlaneScraper\images\{}'

    # setup SQL alchemy connection
    engine = sqlalchemy.create_engine('sqlite:///A:\Projects\PycharmProjects\Viewer\\images.sqlite3')
    Session = sessionmaker(bind=engine)
    session = Session()

    aircraft = 'Airbus A380'
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

    images = session.execute(select_images).fetchall()
    session.close()

    for image in images[:100]:
        image_id = image[0]
        image_url = image[1]
        image_name = image[2]
        image_location = image[3]

        print('Downloading image {} with image id {}'.format(image_name, image_id))

        download_image(image_directory.format(image_location), image_name, image_url)

        update_image = """UPDATE
                            images
                          SET
                            redownload_flag = 0
                          WHERE
                            image_id = {}""".format(image_id)

        engine.execute(update_image)