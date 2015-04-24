from yahoo_finance.yql import YQLQuery
from yahoo_finance.quote import Quote

from plugin.command import Command

import logging

log = logging.getLogger(__name__)

class Headline(object):
    def __init__(self, headline):
        self._parse_headline(headline)

    def _parse_headline(self, headline):
        try:
            self.date = headline['cite']['span']
        except KeyError:
            pass
        headline = headline['a']
        self.title = headline['content']
        urls = headline['href'].split('/*')
        self.url = urls[len(urls)-1]

    def get_date(self):
        return self.date

    def get_url(self):
        return self.url

    def __str__(self):
        if self.date:
            return "%s %s: %s" % (self.date, self.title, self.url)
        return "%s: %s" % (self.title, self.url)


class News(Command):

    def help(self, trigger=None):
        return ".news <symbol> [amount] - Get news articles for the specified symbol"

    def triggers(self):
        return ['.news']

    def run(self, source, channel, trigger, args):
        if len(args) == 0 or len(args) > 2:
            return [self.help()]

        count = 1
        if len(args) == 2:
            try:
                count = int(args[1])
            except ValueError, e:
                log.exception(e)
                return [get_help()]

        stock = Quote(args[0])
        symbol = stock.get_symbol()
        query = "select * from html where url='http://finance.yahoo.com/q?s=%s' and xpath='//div[@id=\"yfi_headlines\"]/div[2]/ul/li'" % symbol
        response = YQLQuery().execute(query)
        if 'query' in response and 'results' in response['query']:
            results = response['query']['results']
            if 'li' in results and len(results['li']) > 0:
                headline_list = results['li']
                headlines = []
                for headline in headline_list:
                    headlines.append(Headline(headline))
                if len(headlines) < count:
                    count = len(headlines) - 1
                return headlines[:count]
