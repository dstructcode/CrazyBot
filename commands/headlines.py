from yahoo.yql import YQLQuery
from yahoo_finance.quote import Quote

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


def run(nick, userhost, args=[], database=None):
    if len(args) != 1:
        return
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
            return headlines[:3]


def get_help():
    return ".headlines <symbol> - Get the last 3 headlines for this symbol"
