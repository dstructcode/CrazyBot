import httplib, urllib2, simplejson, logging

PUBLIC_API_URL = 'http://query.yahooapis.com/v1/public/yql'
DATATABLES_URL = 'store://datatables.org/alltableswithkeys'

log = logging.getLogger(__name__)

class YQLQuery(object):

    def __init__(self):
        self.connection = httplib.HTTPConnection('query.yahooapis.com')

    def execute(self, yql, token = None):
        self.connection.request('GET', PUBLIC_API_URL + '?' + urllib2.urlencode({'q': yql, 'format': 'json', 'env': DATATABLES_URL}, True))
        response = self.connection.getresponse().read()
        try:
            response = simplejson.loads(response)
        except Exception as e:
            log.exception(e)
            log.debug(response)
        return response
