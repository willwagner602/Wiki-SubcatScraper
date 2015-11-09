__author__ = 'wwagner'

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import os

engine = sqlalchemy.create_engine('sqlite:///' + os.getcwd() + '\\images.db')

Base = declarative_base()


class Image(Base):
    __tablename__ = 'images'
    url = Column(String(200), primary_key=True)
    name = Column(String(100))
    image_license = Column(String(100))
    license_text = Column(String(1000))
    location = Column(String(200))
    author = Column(String(100))

    def __init__(self, url, name, image_license, license_text, location, author):
        self.url = url
        self.name = name
        self.image_license = image_license
        self.license_text = license_text
        self.location = location
        self.author = author

    def __repr__(self):
        return "<Image(url='{}', name='{}', license='{}', location='{}', author='{}'".format(
                      self.url, self.name, self.image_license, self.location, self.author)

    def commit_image(self):
        """
        An inefficient wrapper that commits this single image to the database
        :param Image:
        :return bool:
        """
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(test_image)
        session.commit()

        return True