from plugin.listener import Listener
from bs4 import BeautifulSoup

import urllib2
import logging
import re

log = logging.getLogger(__name__)

class LinkTitle(Listener):
    def run(self, line):
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
        if not urls:
            return
        try:
            response = []
            for url in urls:
                openurl = urllib2.urlopen(url)
                html = openurl.read()
                openurl.close()
                soup = BeautifulSoup(html)
                if not soup or not soup.html:
                    return
                response.append(soup.html.head.title.string.strip())
            return response
        except Exception as e:
            log.error(e)
