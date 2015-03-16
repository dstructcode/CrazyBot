from sqlalchemy import Column, DateTime, Float, String, Integer, ForeignKey, create_engine, func
from sqlalchemy.orm import relationship, backref, sessionmaker, subqueryload
from sqlalchemy.ext.declarative import declarative_base
from yahoo_finance.quote import GroupQuote, Quote

import logging

log = logging.getLogger(__name__)

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


def get_portfolio(nick, userhost):
    Session = sessionmaker(bind=engine)
    session = Session()
    p = None
   
    try:
        user = session.query(User).filter(User.userhost == userhost).one()
        p = session.query(Portfolio).filter(Portfolio.user.has(id=user.id)).one()
    except Exception, e:
        log.exception(e)
        try:
            user = session.query(User).filter(User.nick == nick).one()
            p = session.query(Portfolio).filter(Portfolio.user.has(id=user.id)).one()
        except Exception, e:
            log.exception(e)
            pass
    session.close()
    return p;

def create_portfolio(nick, userhost):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(nick=nick, userhost=userhost)
    portfolio = Portfolio(user_id=user.id, user=user)
    session.add(user)
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    session.close()
    return portfolio

def format_change(curr, prev):
    curr = str(curr).replace(',', '')
    prev = str(prev).replace(',', '')
    diff = float(curr) - float(prev)
    percent = (diff / float(prev)) * 100
    color = '\x0f'
    if percent < 0:
        color = '04'
    elif percent > 0:
        color = '09'
    return "%s \x03%s%.2f\x03 (\x03%s%.2f%%\x03)\x0f" % (curr, color, diff, color, percent) 

def user_portfolio(nick, userhost):
    log.info("Retrieving portfolio")
    BAR_SEP = "\x0307|\x03"
    portfolio = get_portfolio(nick, userhost)
    if not portfolio:
        return None
    Session = sessionmaker(bind=engine)
    session = Session()
    stocks = []
    for stock in session.query(Stock).filter(Stock.portfolio_id == portfolio.id).all():
        stocks.append((stock.symbol,stock.price))
    quotes = GroupQuote([x for x,y in stocks])
    response = ''
    response_list = []
    for symbol, price in stocks:
        quote = quotes.get(symbol)
        if quote:
            try:
                change = format_change(quote.get_price(), price)
                response = response + '%s \x1F%s\x1F (%.2f): %s ' % (BAR_SEP, symbol, price, change)
                if len(response) > 256:
                    response_list.append(response)
                    response = ''
            except Exception, e:
                log.exception(e)
                response = response + '%s \x1F%s\x1F (%.2f): %s ' % (BAR_SEP, symbol, 0.00, "Unknown")
    if len(response) > 0:
        response_list.append(response)
#    response = response + '%s' % (BAR_SEP)
    log.info("Sending portfolio")
    return response_list

def stock_exists(symbol, portfolio):
    stock = Quote(symbol)
    Session = sessionmaker(bind=engine)
    session = Session()
    p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
    r = session.query(Stock).filter(Stock.portfolio==p).filter(Stock.symbol==stock.get_symbol()).all()
    session.close()
    return len(r) != 0

def add_stock_market(symbol, portfolio):
    stock = Quote(symbol)
    Session = sessionmaker(bind=engine)
    session = Session()
    p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
    s = Stock(portfolio=p, portfolio_id=p.id, symbol=stock.get_symbol(), price=stock.get_price())
    session.add(s)
    session.commit()
    session.close()
    return ['Added %s at %.2f to %s\'s portfolio' % (stock.get_symbol(), float(stock.get_price()), portfolio.user.nick)]

def add_stock_price(symbol, price, portfolio):
    try:
        price = float(price)
    except ValueError:
        return ['Invalid price: %s' % price]
    stock = Quote(symbol)
    Session = sessionmaker(bind=engine)
    session = Session()
    p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
    s = Stock(portfolio=p, portfolio_id=p.id, symbol=stock.get_symbol(), price=price)
    session.add(s)
    session.commit()
    session.close()
    return ['Added %s at %.2f to %s\'s portfolio' % (stock.get_symbol(), float(price), portfolio.user.nick)]

def add_portfolio(nick, userhost, args):
    portfolio = get_portfolio(nick, userhost)
    if not portfolio:
        portfolio = create_portfolio(nick, userhost)
    if len(args) == 1:
        return add_stock_market(args[0], portfolio)
    if len(args) == 2:
        return add_stock_price(args[0], args[1], portfolio)
    return ['Invalid arguments']

def del_stock(stock, portfolio):
    Session = sessionmaker(bind=engine)
    session = Session()
    p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
    stocks = session.query(Stock).filter(Stock.portfolio==p).filter(Stock.symbol==stock.get_symbol()).all()
    response = '[%s] Symbol not found' % portfolio.user.nick
    for s in stocks:
        session.delete(s)
    if stocks:
        response = '[%s] %s deleted from portfolio' % (portfolio.user.nick, stock.get_symbol())
    session.commit()
    session.close()
    return [response]

def del_portfolio(nick, userhost, args):
    portfolio = get_portfolio(nick, userhost)
    if not portfolio:
        return ['You have not created a portfolio, %s' % nick]
    if len(args) == 1:
        stock = Quote(args[0])
        return del_stock(stock, portfolio)
    return ['Invalid arguments']

def get_help():
   return ".portfolio [nickname] [add <symbol> [price]] [del <symbol>] - Get the portfolio for a user"

def run(nick, userhost, args=[], database=None):
    if not database:
        return ['No database specified']

    global engine
    engine = create_engine('sqlite:///%s' % database)
    Base.metadata.create_all(engine)

    if len(args) == 0:
        p = user_portfolio(nick, userhost)
        if not p:
            return ['You have not created a portfolio, %s' % nick]
        response = []
        for r in p:
            response.append("[%s] %s" % (nick, r))
        return response
    if args[0] == 'add':
        return add_portfolio(nick, userhost, args[1:])
    if args[0] == 'del':
        return del_portfolio(nick, userhost, args[1:])
    if len(args) == 1:
        p = user_portfolio(args[0], '')
        if not p:
            return ['No portfolio found for %s' % args[0]]
        response = []
        for r in p:
            response.append("[%s] %s" % (args[0], r))
        return response
    return ['HAHAHA no']
