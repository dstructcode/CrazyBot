from yahoo_finance.quote import Quote

def run(nick, userhost, args=[], database=None):
    if len(args) != 1:
        return
    stock = Quote(args[0])
    return ["http://finance.yahoo.com/echarts?s=%s" % stock.get_symbol()]
