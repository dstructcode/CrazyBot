from plugin.command import Command
from apiclient.discovery import build

import urllib
import unirest

UD_API_KEY = ""
G_API_KEY = ""
G_CX = ""

class LookUp(Command):
    def help(self, trigger):
        if trigger == '.ud':
            return ".ud <term>[:<index>]"

    def triggers(self):
        return ['.g', '.ud']

    def run(self, source, channel, trigger, args):
        donothing = lambda: None
        return getattr(self, trigger.replace('.', '_'), donothing)(args)

    def _g(self, args):
        sep = " \x0307|\x03 "
        term = ' '.join(args)
        service = build("customsearch", "v1", developerKey=G_API_KEY)
        result = service.cse().list(
            q=term,
            cx = G_CX,
        ).execute()
        if result and 'items' in result:
            items = result['items']
            first = items[0]
            out = "{title}{sep}{snippet}{sep}{link}"
            title = first['title']
            snippet = first['snippet'].replace('\n', '').encode('ascii', 'ignore')
            link = first['link']
            return out.format(title=title, sep=sep, snippet=snippet, link=link)

    def _ud(self, args):
        sep = " \x0307|\x03 "
        api = "https://mashape-community-urban-dictionary.p.mashape.com/define?{term}"

        term = ' '.join(args).split(':')
        if len(term) == 2 and isint(term[1]):
            index = int(term[1])
            term = term[0]
        else:
            index = 1
            term = ' '.join(term)
        term = urllib.urlencode({'term': term}, True)
        response = unirest.get(api.format(term=term),
            headers={
                'X-Mashape-Key': UD_API_KEY,
                'Accept': 'text/plain'
            }
        ).body

        if not response or response['result_type'] == 'no_results':
            return "No results."

        defs = response['list']
        if index-1 >= len(defs):
            return "No Results."

        item = defs[index-1]
        word = item['word'].strip()
        desc = filter(None, item['definition'].strip().splitlines())
        out = "{word}{sep}{desc}{sep}{index} of {total}"
        output = []
        for d in desc:
            for c in chunks(d, 384):
                output.append(out.format(word=word, sep=sep, desc=c, index=index, total=len(defs)))

        return output


def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
