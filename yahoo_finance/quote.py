from datetime import datetime
from urllib import quote
from yql import YQLQuery
import traceback

class InvalidSymbolError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Invalid symbol [%s]" % repr(self.value)


class YQLQueryError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Query failed: %s" % repr(self.value)


class DataPoint(object):
    def __init__(self, symbol, date, day_open, day_high, day_low, day_close, day_volume, day_adj_close):
        self.symbol = symbol
        self.date = self._str_to_datetime(date)
        self.day_open = day_open
        self.day_high = day_high
        self.day_low = day_low
        self.day_close = day_close
        self.day_volume = day_volume
        self.day_adj_close = day_adj_close

    def _str_to_datetime(self, date):
        return datetime.strptime(date, "%Y-%m-%d")

    def get_symbol(self):
        return self.symbol.upper()

    def get_date(self):
        return self.date

    def get_day_open(self):
        return self.day_open

    def get_day_high(self):
        return self.day_high

    def get_day_low(self):
        return self.day_low
    
    def get_day_close(self):
        return self.day_close

    def get_day_volume(self):
        return self.day_volume

    def get_day_adj_close(self):
        return self.day_adj_close


class GroupQuote(object):
    def __init__(self, symbols=[]):
        if len(symbols) == 0:
            raise InvalidSymbolError("No symbol(s) specified")
        self.symbols = symbols
        self.quotes = {}
        self.refresh()

    def _process_query_error(self, response):
        try:
            raise YQLQueryError(response['error']['description'])
        except (TypeError, KeyError):
            raise YQLQueryError(response)

    def refresh(self):
        symbols_str = ''
        for symbol in self.symbols:
            symbols_str = symbols_str + "\"%s\"," % symbol
        symbols_str = symbols_str.rstrip(',')
        query = "select * from yahoo.finance.quotes where symbol in (%s)" % symbols_str
        response = YQLQuery().execute(query)
        try:
            quote = response['query']['results']['quote']
            if isinstance(quote, list):
                quotes = {}
                for q in quote:
                    bq = BaseQuote(q)
                    quotes[bq.get_symbol()] = bq
                self.quotes = quotes
            else:
                bq = BaseQuote(quote)
                self.quotes[bq.get_symbol()] = bq
        except (TypeError, KeyError):
            traceback.print_exc()
            self._process_query_error(response)

    def symbols(self):
        return self.quotes.keys()

    def get(self, symbol):
        symbol = symbol.upper()
        if symbol in self.quotes:
            return self.quotes[symbol.upper()]
        return None


class BaseQuote(object):

    def __init__(self, quote):
        self.quote = quote
        self.symbol = self.get_symbol()

    def _process_query_error(self, response):
        try:
            raise YQLQueryError(response['error']['description'])
        except (TypeError, KeyError):
            raise YQLQueryError(response)

    def get_price(self):
        query = "select * from html where url='http://finance.yahoo.com/q?s=%s' and xpath='//span[@class=\"time_rtq_ticker\"]'" % quote(self.symbol)
        response = YQLQuery().execute(query)
        try:
            return response['query']['results']['span']['span']['content']
        except (TypeError, KeyError):
            self._process_query_error(response)

    def get_after_hours(self):
        query = "select * from html where url='http://finance.yahoo.com/q?s=%s' and xpath='//span[@class=\"yfs_rtq_quote\"]'" % quote(self.symbol)
        response = YQLQuery().execute(query)
        try:
            return response['query']['results']['span']['span']['content']
        except (TypeError, KeyError):
            self._process_query_error(response)

    def get_symbol(self):
        return self.quote['Symbol'].upper()

    def get_name(self):
        return self.quote['Name']

    def get_open(self):
        return self.quote['Open']

    def get_prev_close(self):
        return self.quote['PreviousClose']

    def get_change_percent(self):
        return self.quote['PercentChange']

    def get_ask(self):
        return self.quote['AskRealtime']

    def get_bid(self):
        return self.quote['BidRealTime']

    def get_dividend(self):
        return self.quote['DividendYield']

    def get_earnings_share(self):
        return self.quote['EarningsShare']

    def get_price_earnings(self):
        return self.quote['PERatio']

    def get_price_earnings_growth(self):
        return self.quote['PEGRatio']

    def get_short(self):
        return self.quote['ShortRatio']

    def get_day_high(self):
        return self.quote['DaysHigh']

    def get_day_low(self):
        return self.quote['DaysLow']

    def get_day_range(self):
        return self.quote['DaysRange']

    def get_trend(self):
        # Sometimes the TickerTrend comes back as null
        trend = self.quote['TickerTrend']
        if trend:
            trend = trend.strip('&nbsp;')
        return trend

    def get_historical(self, start, end):
        query = "select * from yahoo.finance.historicaldata where symbol = \"%s\" and startDate = \"%s\" and endDate = \"%s\"" % (self.symbol, start, end)
        response = YQLQuery().execute(query)
        try:
            data = []
            points = response['query']['results']['quote']
            for point in points:
                data.append(DataPoint(point['Symbol'], point['Date'], point['Open'], point['High'], point['Low'], point['Close'], point['Volume'], point['Adj_Close']))
            return data
        except (TypeError, KeyError):
            self._process_query_error(response)


class Quote(BaseQuote):
    def __init__(self, symbol):
        if len(symbol) == 0:
            raise InvalidSymbolError("No symbol specified")
        self.symbol = symbol
        self.refresh()

    def _process_query_error(self, response):
        try:
            raise YQLQueryError(response['error']['description'])
        except (TypeError, KeyError):
            raise YQLQueryError(response)

    def refresh(self):
        query = "select * from yahoo.finance.quotes where symbol=\"%s\"" % self.symbol
        response = YQLQuery().execute(query)
        try:
            self.quote = response['query']['results']['quote']
            if self.quote['ErrorIndicationreturnedforsymbolchangedinvalid']:
                raise InvalidSymbolError(self.get_symbol())
        except (TypeError, KeyError):
            self._process_query_error(response)
