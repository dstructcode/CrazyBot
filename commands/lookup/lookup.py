from plugin.command import Command

import urllib
import unirest


API_KEY = ""


class LookUp(Command):
    def help(self, trigger):
        if trigger == '.ud':
            return ".ud <term>"

    def triggers(self):
        return ['.ud']

    def run(self, source, channel, trigger, args):
        donothing = lambda: None
        return getattr(self, trigger.replace('.', '_'), donothing)(args)

    def _ud(self, args):
        sep = " \x0307|\x03 "
        api = "https://mashape-community-urban-dictionary.p.mashape.com/define?{term}"

        if isint(args[-1]):
            index = int(args.pop(-1))
        else:
            index = 1

        term = urllib.urlencode({'term': args}, True)
        response = unirest.get(api.format(term=term),
            headers={
                'X-Mashape-Key': API_KEY,
                'Accept': 'text/plain'
            }
        ).body

        if not response or response['result_type'] == 'no_results':
            return "No results."

        defs = response['list']
        if index >= len(defs):
            return "No Results."

        item = defs[index-1]
        word = item['word'].strip()
        desc = ' '.join(item['definition'].strip().splitlines())
        out = "{word}{sep}{desc}{sep}{index} of {total}"
        return out.format(word=word, sep=sep, desc=desc, index=index, total=len(defs))


def isint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
