import httplib, urllib, simplejson, traceback

PUBLIC_API_URL = 'htp://query.yahooapis.com/v1/public/yql'
DATATABLES_URL = 'store://datatables.org/alltableswithkeys'

class YQLQuery(object):

    def __init__(self):
        self.connection = httplib.HTTPConnection('query.yahooapis.com')

    def execute(self, yql, token = None):
        self.connection.request('GET', PUBLIC_API_URL + '?' + urllib.urlencode({'q': yql, 'format': 'json', 'env': DATATABLES_URL}))
        response = self.connection.getresponse().read()
        try:
            response = simplejson.loads(response)
        except:
            traceback.print_exc()
            print response
        return response
