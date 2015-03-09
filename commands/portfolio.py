from sqlalchemy import Column, DateTime, Float, String, Integer, ForeignKey, create_engine, func
from sqlalchemy.orm import relationship, backref, sessionmaker, subqueryload
from sqlalchemy.ext.declarative import declarative_base
from yahoo_finance.quote import Quote
import traceback

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


engine = create_engine('sqlite:///portfolio.db')
Base.metadata.create_all(engine)

def get_portfolio(nick, userhost):
    Session = sessionmaker(bind=engine)
    session = Session()
    p = None
   
    try:
        user = session.query(User).filter(User.userhost == userhost).one()
        p = session.query(Portfolio).filter(Portfolio.user.has(id=user.id)).one()
    except:
        traceback.print_exc()
        try:
            user = session.query(User).filter(User.nick == nick).one()
            p = session.query(Portfolio).filter(Portfolio.user.has(id=user.id)).one()
        except:
            traceback.print_exc()
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
    BAR_SEP = "\x0307|\x03"
    portfolio = get_portfolio(nick, userhost)
    if not portfolio:
        return None
    Session = sessionmaker(bind=engine)
    session = Session()
    response = ''
    for stock in session.query(Stock).filter(Stock.portfolio_id == portfolio.id).all():
        quote = Quote(stock.symbol)
        price = quote.get_price()
        change = format_change(price, stock.price)
        response = response + '%s %s: (%.2f) - %s ' % (BAR_SEP, stock.symbol, stock.price, change)
    response = response + '%s' % (BAR_SEP)
    return [response]

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
    for s in stocks:
        session.delete(s)
    session.commit()
    session.close()
    return ['[%s] %s deleted from portfolio' % (portfolio.user.nick, stock.get_symbol())]

def del_portfolio(nick, userhost, args):
    portfolio = get_portfolio(nick, userhost)
    if not portfolio:
        return ['You have not created a portfolio, %s' % nick]
    if len(args) == 1:
        stock = Quote(args[0])
        return del_stock(stock, portfolio)
    return ['Invalid arguments']

def get_help():
   return ".portfolio [<nickname>|add <symbol> [price]|del <symbol>] - Get the portfolio for a user"

def run(nick, userhost, args=[]):
    if len(args) == 0:
        p = user_portfolio(nick, userhost)
        if not p:
            return ['You have not created a portfolio, %s' % nick]
        return ["[%s] %s" % (nick, p[0])]
    if args[0] == 'add':
        return add_portfolio(nick, userhost, args[1:])
    if args[0] == 'del':
        return del_portfolio(nick, userhost, args[1:])
    if len(args) == 1:
        p = user_portfolio(args[0], '')
        if not p:
            return ['No portfolio found for %s' % args[0]]
        return ["[%s] %s" % (args[0], p[0])]
    return ['HAHAHA no']
