from sqlalchemy import Column, DateTime, Float, String, Integer, ForeignKey, create_engine, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nick = Column(String)
    userhost = Column(String)


class Location(Base):
    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, lazy='subquery', backref=backref('location', uselist=True, lazy="subquery", cascade='delete,all'))
    location = Column(String)



def load_command():
    engine = create_engine('sqlite:///%s/weather.db' % os.path.dirname(__file__))
    Base.metadata.create_all(engine)

    from weather import Weather
    return Weather(engine)
