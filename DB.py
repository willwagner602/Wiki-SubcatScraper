__author__ = 'wwagner'

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
import sqlalchemy
import os

Base = declarative_base()


class Image(Base):
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