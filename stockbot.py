#! /usr/bin/env python

from threading import Thread

import daemon
import logging
import os
import sys
import irc.buffer
import irc.bot
import irc.client
import yaml

LOG_FILENAME = 'stockbot.log'

install_dir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(filename=install_dir+'/'+LOG_FILENAME, level=logging.DEBUG)
log = logging.getLogger(__name__)
fh = logging.root.handlers[0]
context = daemon.DaemonContext(
    files_preserve = [
        fh.stream,
    ],
)

class IgnoreErrorsBuffer(irc.buffer.DecodingLineBuffer):
    def handle_exception(self):
        pass
irc.client.ServerConnection.buffer_class = IgnoreErrorsBuffer

class StockBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, password, channels, server, port=6667, database=None):
        log.info("Instantiating StockBot for server %s" % server)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.password = password
        self.channel_list = channels
        self.database = database

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        if self.password:
            c.privmsg('nickserv', 'identify %s' % self.password)
        for channel in self.channel_list:
            c.join(channel)

    def on_pubmsg(self, c, e):
        if e.arguments[0][0] != '.':
            return
        a = e.arguments[0].strip().lstrip('.').split(' ')
        cmd = a[0]
        args = a[1:]
        self.do_command(e, cmd, args)

    def do_command(self, e, cmd, args):
        nick = e.source.nick
        c = self.connection

        hlp = False
        if cmd == "help":
            hlp = True
            if len(args) > 0:
                cmd = args[0]

        try:
            module = __import__('commands.%s' % cmd, fromlist='commands')
            reload(module)

            if hlp:
                c.privmsg(e.target,  module.get_help())
            else:
                log.info("Executing %s command" % cmd)
                for response in module.run(e.source.nick, e.source.userhost, args, self.database):
                    c.privmsg(e.target, response)
        except ImportError:
            pass # Module does not exist
        except Exception, e:
            log.exception(e)

class BotThread(Thread):
    def __init__(self, bot):
        self._bot = bot
        Thread.__init__(self)

    def run(self):
        self._bot.start()

def main():
    try: 
        f = open(install_dir+'/stockbot.yaml')
        conf = yaml.safe_load(f)
        f.close()

        if 'database' not in conf:
            log.error('No sqlite database specified')
            sys.exit(-1)
        database = conf['database']

        bots = []
        for server, meta in conf['connections'].iteritems():
            s = server.split(":", 1)
            server = s[0]
            if len(s) == 2:
                try:
                    port = int(s[1])
                except ValueError:
                    log.error("Invalid port")
                    sys.exit(-1)
            else:
                port = 6667

            if 'nickname' not in meta:
                log.error('No nickname specified for server [%s]' % server)
                sys.exit(-1)
            nickname = meta['nickname']

            password = None
            if 'password' in meta:
                password = meta['password']

            if 'channels' not in meta:
                log.error('No channels specified for server [%s]' % server)
                sys.exit(-1)
            channels = meta['channels']

            bots.append(BotThread(StockBot(nickname, password, channels, server, port, database)))

        for bot in bots:
            bot.start()
    except Exception, e:
        log.exception(e)

if __name__ == "__main__":
    with context:
        main()
