from yahoo_finance.yql import YQLQuery
from yahoo_finance.quote import Quote

from plugin.command import Command

import logging

log = logging.getLogger(__name__)

class Press(Command):

    def help(self, trigger):
        return ".press <symbol> - Get the latest press release"

    def triggers(self):
        return ['.press']

    def run(self, source, channel, trigger, args):
        if len(args) == 1:
            stock = Quote(args[0])
            symbol = stock.get_symbol()
            query = "select * from html where url='http://finance.yahoo.com/q?s=%s' and xpath='//div[@id=\"yfi_press_releases\"]/div[2]/ul/li'" % symbol
            response = YQLQuery().execute(query)
            if 'query' in response and 'results' in response['query']:
                results = response['query']['results']
                if 'li' in results and len(results['li']) > 0:
                    press_releases = results['li']
                    try:
                        if 'a' not in press_releases[0]:
                            return
                        release = press_releases[0]['a']
                        title = release['content']
                        urls = release['href'].split('/*')
                        url = ''
                        if len(url) > 1:
                            url = urls[1]
                        else:
                            url = urls[0]
                        
                        if 'cite' in press_releases[0] and 'span' in press_releases[0]['cite']:
                            date = press_releases[0]['cite']['span']
                            return ["%s %s: %s" % (date, title, url)]
                        else:
                            return ["%s: %s" % (title, url)]
                    except Exception, e:
                        log.exception(e)
