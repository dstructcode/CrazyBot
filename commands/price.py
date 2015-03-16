import logging
import pytz

from datetime import datetime, time
from yahoo_finance.quote import Quote

log = logging.getLogger(__name__)

def format_title(name, symbol):
    return "\x02%s\x02 (\x02%s\x02)" % (name, symbol)

def format_change(curr, prev):
    if not curr or not prev:
        return None
    curr = str(curr).replace(',', '')
    prev = str(prev).replace(',', '')
    diff = float(curr) - float(prev)
    percent = (diff / float(prev)) * 100
    color = '\x0f'
    if percent < 0:
        color = '04'
    elif percent > 0:
        color = '09'
    return "%s \x03%s%.2f\x03 (\x03%s%.2f%%\x03)\x0f" % (curr, color, diff, color, percent) 

def format_after_hours(current, close):
    if current and close:
        return "after hours: %s" % format_change(current, close)
    return None

def format_pre_market(current, close):
    if current and close:
        return "pre-market: %s" % format_change(current, close)
    return None

def run(nick, userhost, args=[], database=None):
    if len(args) != 1:
        return
    BAR_SEP = "\x0307|\x03"
    try:
        stock = Quote(args[0])
    except Exception, e:
        import traceback
        traceback.print_exc()
        log.exception(e)
        return ["Query failed."]
    title = format_title(stock.get_name(), stock.get_symbol())
    prev_close = stock.get_prev_close()
    day_open = stock.get_open()
    day_high = stock.get_day_high()
    day_low = stock.get_day_low()
    current = stock.get_price()
    trend = stock.get_trend()
    now = datetime.now(pytz.timezone('US/Eastern'))
    # Between market close and open (4:00pm and 9:30am)
    if time(16,00) <= now.time() or time(9,30) >= now.time():
        close = format_change(current, prev_close)
        close_str = "%s %s previous close: %s %s open: %s %s high: %s %s low: %s %s trend: %s %s close: %s" % \
        (title, BAR_SEP, prev_close, BAR_SEP, day_open, BAR_SEP, day_high, BAR_SEP, day_low, BAR_SEP, trend, BAR_SEP, close)
        updated = None
        try:
            updated = stock.get_after_hours()
        except:
            return [close_str]
        # At or after 4:00pm but before 8:30am
        if time(16,00) <= now.time() or time(8,30) >= now.time():
            after_hours = format_after_hours(updated, current)
            if after_hours:
                return ["%s %s %s" % (close_str, BAR_SEP, after_hours)]
        # At or after 8:30am but before 9:30am
        if time(8,30) <= now.time():
            pre_market = format_pre_market(updated, current)
            if pre_market:
                return ["%s %s %s" % (close_str, BAR_SEP, pre_market)]
        return [close_str]
    change = format_change(current, prev_close)
    return ["%s %s previous close: %s %s open: %s %s high: %s %s low: %s %s trend: %s %s current: %s" % \
    (title, BAR_SEP, prev_close, BAR_SEP, day_open, BAR_SEP, day_high, BAR_SEP, day_low, BAR_SEP, trend, BAR_SEP, change)]

def get_help():
    return ".price <symbol> - Get price info about a particular stock"
