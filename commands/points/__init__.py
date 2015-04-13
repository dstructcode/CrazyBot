from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nick = Column(String)
    userhost = Column(String)


class Point(Base):
    __tablename__ = 'point'
    id = Column(Integer, primary_key=True, autoincrement=True)
    count = Column(Integer)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, lazy='subquery', backref=backref('point', uselist=True, lazy='subquery', cascade='delete,all'))


def load_command():
    engine = create_engine('sqlite:///%s/points.db' % os.path.dirname(__file__))
    Base.metadata.create_all(engine)

    from points import Points
    
    return Points(engine)
