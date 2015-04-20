import logging
import pytz

from datetime import datetime, time
from yahoo_finance.quote import Quote

import util

log = logging.getLogger(__name__)

from plugin.command import Command

class Price(Command):

    def help(self):
        return ".price <symbol> - Get price info about a particular stock"

    def triggers(self):
        return ['.price']

    def run(self, source, channel, trigger, args):
        if trigger == '.price' and len(args) == 1:
            return self._price(args[0])

    def _price(self, symbol):
        BAR_SEP = "\x0307|\x03"
        try:
            stock = Quote(symbol)
        except Exception as e:
            log.exception(e)
            return ["Query failed."]
        title = util.format_title(stock.get_name(), stock.get_symbol())
        prev_close = stock.get_prev_close()
        day_open = stock.get_open()
        day_high = stock.get_day_high()
        day_low = stock.get_day_low()
        volume = stock.get_volume()
        current = stock.get_price()
        now = datetime.now(pytz.timezone('US/Eastern'))
        # Between market close and open (4:00pm and 9:30am)
        if time(16,00) <= now.time() or time(9,30) >= now.time():
            close = util.format_change(current, prev_close)
            close_str = "%s %s previous close: %s %s open: %s %s high: %s %s low: %s %s volume: %s %s close: %s" % \
            (title, BAR_SEP, prev_close, BAR_SEP, day_open, BAR_SEP, day_high, BAR_SEP, day_low, BAR_SEP, volume, BAR_SEP, close)
            updated = None
            try:
                updated = stock.get_after_hours()
            except:
                return [close_str]
            # At or after 4:00pm but before 8:30am
            if time(16,00) <= now.time() or time(8,30) >= now.time():
                after_hours = util.format_after_hours(updated, current)
                if after_hours:
                    return ["%s %s %s" % (close_str, BAR_SEP, after_hours)]
            # At or after 8:30am but before 9:30am
            if time(8,30) <= now.time():
                pre_market = util.format_pre_market(updated, current)
                if pre_market:
                    return ["%s %s %s" % (close_str, BAR_SEP, pre_market)]
            return [close_str]
        change = util.format_change(current, prev_close)
        return ["%s %s previous close: %s %s open: %s %s high: %s %s low: %s %s volume: %s %s current: %s" % \
        (title, BAR_SEP, prev_close, BAR_SEP, day_open, BAR_SEP, day_high, BAR_SEP, day_low, BAR_SEP, volume, BAR_SEP, change)]   
