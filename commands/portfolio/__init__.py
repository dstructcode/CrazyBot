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


class Portfolio(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, lazy='subquery', backref=backref('portfolio', uselist=True, lazy="subquery", cascade='delete,all'))


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    price = Column(Float)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship(Portfolio, lazy='subquery', backref=backref('stock', uselist=True, lazy="subquery", cascade='delete,all'))


def load_command(): 
    engine = create_engine('sqlite:///%s/portfolio.db' % os.path.dirname(__file__))
    Base.metadata.create_all(engine)

    from portfolio import Portfolios
    return Portfolios(engine)
