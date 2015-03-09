from yahoo_finance.quote import Quote

def run(nick, userhost, args=None):
    if args:
        stock = Quote(args[0])
        symbol = stock.get_symbol()
        name = stock.get_name()
        eps = stock.get_earnings_share()
        pe = stock.get_price_earnings()
        peg = stock.get_price_earnings_growth()
        short = stock.get_short()
        return ["\x02%s\x02 (\x02%s\x02) \x0307|\x03 eps: %s \x0307|\x03 pe: %s \x0307|\x03 peg: %s \x0307|\x03 short: %s" % \
        (name, symbol, eps, pe, peg, short)]

def get_help():
    return ".info <symbol> - Get more info about a particular stock"
