from yahoo_finance.quote import Quote
from plugin.command import Command

class Info(Command):
    
    def help(self, trigger):
        return ".info <symbol> - Get more info about a particular stock"

    def triggers(self):
        return ['.info']

    def run(self, source, channel, trigger, args):
        if args:
            stock = Quote(args[0])
            symbol = stock.get_symbol()
            name = stock.get_name()
            div = stock.get_dividend()
            eps = stock.get_earnings_share()
            pe = stock.get_price_earnings()
            peg = stock.get_price_earnings_growth()
            short = stock.get_short()
            return ["\x02%s\x02 (\x02%s\x02) \x0307|\x03 dividend: %s \x0307|\x03 eps: %s \x0307|\x03 pe: %s \x0307|\x03 peg: %s \x0307|\x03 short: %s" % \
            (name, symbol, div, eps, pe, peg, short)]
