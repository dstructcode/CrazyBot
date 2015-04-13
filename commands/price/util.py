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
