import os

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
import sqlalchemy
import os


def confirm_image_download(image, folders):
    # necessary information to lookup image in dictionary
    name = image[2]
    location = image[5]

    try:
        if name in folders[location]:
            return True
        else:
            return False
    except KeyError:
        return False


def mark_image_for_download(image, db_connection):
    url = image[0]
    update_statement = """UPDATE images SET redownload_flag = 1 WHERE image_page = '{}'""".format(url)
    db_connection.execute(update_statement)


def get_image_lists(base_directory):
    # for performance purposes, create a dict with the lists of files in each image folder
    image_lists = {}
    os.chdir(base_directory)
    for folder in os.listdir():
        os.chdir(folder)
        image_lists[folder] = os.listdir()
        os.chdir(base_directory)
    return image_lists

    
class Image(declarative_base):
    __tablename__ = 'images'
    image_page = Column(String(200), primary_key=True)
    image_url = Column(String(200))
    name = Column(String(100))
    image_license = Column(String(100))
    license_text = Column(String(1000))
    location = Column(String(200))
    author = Column(String(100))
    aircraft = Column(String(100))
    aircraft_type = Column(String(50))

    def __init__(self, image_page, image_url, name, image_license, license_text, location, author,
                 aircraft, aircraft_type):
        self.image_page = image_page
        self.image_url = image_url
        self.name = name
        self.image_license = image_license
        self.license_text = license_text
        self.location = location
        self.author = author
        self.aircraft = aircraft
        self.aircraft_type = aircraft_type

    def __repr__(self):
        return "<Image(url='{}', name='{}', license='{}', location='{}', author='{}'".format(
                      self.image_page, self.name, self.image_license, self.location, self.author)


def create_table():
    engine = sqlalchemy.create_engine('sqlite:///' + os.getcwd() + '\\images.db')
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    # setup DB connection
    engine = sqlalchemy.create_engine('sqlite:///' + os.getcwd() + '\\planes.sqlite3')
    connection = engine.connect()

    # get each image from the DB that has an Aircraft assigned to it
    identified_aircraft = connection.execute('''SELECT * FROM images WHERE redownload_flag = 0''')

    missing_image_count = 0
    image_lists = get_image_lists(r'A:\Projects\PycharmProjects\PlaneScraper\images')

    for i, row in enumerate(identified_aircraft):
        if i % 1000 == 0:
            print("Missing images:", missing_image_count)
        if not confirm_image_download(row, image_lists):
            mark_image_for_download(row, connection)
            missing_image_count += 1

    connection.close()