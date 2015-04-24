from sqlalchemy.orm import sessionmaker
from yahoo_finance.quote import GroupQuote, Quote
from commands.portfolio import User, Portfolio, Stock
from plugin.command import Command

import logging

log = logging.getLogger(__name__)


class Portfolios(Command):

    def __init__(self, engine):
        self.engine = engine

    def help(self):
       return ".portfolio [nickname] [add <symbol> [price]] [del <symbol>] - Get the portfolio for a user"

    def triggers(self):
        return ['.portfolio']

    def run(self, source, channel, trigger, args):
        nick = source.nick
        userhost = source.userhost
        if len(args) == 0:
            p = self.user_portfolio(nick, userhost)
            if not p:
                return ['You have not created a portfolio, %s' % nick]
            response = []
            for r in p:
                response.append("[%s] %s" % (nick, r))
            return response
        if args[0] == 'add':
            return self.add_portfolio(nick, userhost, args[1:])
        if args[0] in ['del', 'delete', 'rm', 'remove']:
            return self.del_portfolio(nick, userhost, args[1:])
        if len(args) == 1:
            p = self.user_portfolio(args[0], '')
            if not p:
                return ['No portfolio found for %s' % args[0]]
            response = []
            for r in p:
                response.append("[%s] %s" % (args[0], r))
            return response
        return ['HAHAHA no']

    def get_portfolio(self, nick, userhost):
        Session = sessionmaker(bind=self.engine)
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

    def create_portfolio(self, nick, userhost):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        user = User(nick=nick, userhost=userhost)
        portfolio = Portfolio(user_id=user.id, user=user)
        session.add(user)
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
        session.close()
        return portfolio

    def format_change(self, curr, prev):
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

    def user_portfolio(self, nick, userhost):
        log.info("Retrieving portfolio")
        BAR_SEP = "\x0307|\x03"
        portfolio = self.get_portfolio(nick, userhost)
        if not portfolio:
            return None
        Session = sessionmaker(bind=self.engine)
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
                    change = self.format_change(quote.get_price(), price)
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

    def stock_exists(self, symbol, portfolio):
        stock = Quote(symbol)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
        r = session.query(Stock).filter(Stock.portfolio==p).filter(Stock.symbol==stock.get_symbol()).all()
        session.close()
        return len(r) != 0

    def add_stock_market(self, symbol, portfolio):
        stock = Quote(symbol)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
        s = Stock(portfolio=p, portfolio_id=p.id, symbol=stock.get_symbol(), price=stock.get_price())
        session.add(s)
        session.commit()
        session.close()
        return ['Added %s at %.2f to %s\'s portfolio' % (stock.get_symbol(), float(stock.get_price()), portfolio.user.nick)]

    def add_stock_price(self, symbol, price, portfolio):
        try:
            price = float(price)
        except ValueError:
            return ['Invalid price: %s' % price]
        stock = Quote(symbol)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = session.query(Portfolio).filter(Portfolio.id == portfolio.id).one()
        s = Stock(portfolio=p, portfolio_id=p.id, symbol=stock.get_symbol(), price=price)
        session.add(s)
        session.commit()
        session.close()
        return ['Added %s at %.2f to %s\'s portfolio' % (stock.get_symbol(), float(price), portfolio.user.nick)]

    def add_portfolio(self, nick, userhost, args):
        portfolio = self.get_portfolio(nick, userhost)
        if not portfolio:
            portfolio = self.create_portfolio(nick, userhost)
        if len(args) == 1:
            return self.add_stock_market(args[0], portfolio)
        if len(args) == 2:
            return self.add_stock_price(args[0], args[1], portfolio)
        return ['Invalid arguments']

    def del_stock(self, stock, portfolio):
        Session = sessionmaker(bind=self.engine)
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

    def del_portfolio(self, nick, userhost, args):
        portfolio = self.get_portfolio(nick, userhost)
        if not portfolio:
            return ['You have not created a portfolio, %s' % nick]
        if len(args) == 1:
            stock = Quote(args[0])
            return self.del_stock(stock, portfolio)
        return ['Invalid arguments']
