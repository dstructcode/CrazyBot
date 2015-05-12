from plugin.listener import Listener
from commands.price.price import Price

import re


class Stock(Listener):
    def run(self, line):
        price = Price()
        symbols = re.findall(r'([$]\w*)\b', line)
        response = []
        for symbol in symbols:
            response += price._price(symbol.lstrip('$'))
        return response
