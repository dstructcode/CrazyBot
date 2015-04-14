#! /usr/bin/env python

from importlib import import_module
from threading import Thread

import logging
import os
import pkgutil
import sys
import types

import daemon
import irc.buffer
import irc.bot
import irc.client
import yaml

LOG_FILENAME = 'crazybot.log'

install_dir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(filename=os.path.join(install_dir, LOG_FILENAME), level=logging.DEBUG)
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
    def __init__(self, nickname, password, channels, server, port=6667):
        log.info("Instantiating StockBot for server %s" % server)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.password = password
        self.channel_list = channels
        self._register_commands()
        self._register_listeners()

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        if self.password:
            c.privmsg('nickserv', 'identify %s' % self.password)
        for channel in self.channel_list:
            c.join(channel)

    def on_pubmsg(self, c, e):
        if not irc.client.is_channel(e.target):
            return
        msg = e.arguments[0].strip().split()
        trigger = msg[0]

        method = getattr(self, "_" + trigger.lstrip('.'), None)
        if method:
            response = method()
            for msg in self._iterable(response):
                c.privmsg(e.target, msg)

        for cmd in self.commands:
            if trigger in cmd.triggers():
                if len(msg) > 1 and msg[1] == '-help':
                    for response in self._iterable(cmd.help(trigger)):
                        c.privmsg(e.target, response)
                    return

                channel = self.channels[e.target]
                try:
                    response = cmd.run(e.source, channel, trigger, msg[1:])
                    for msg in self._iterable(response):
                        c.privmsg(e.target, msg)
                except Exception as e:
                    log.exception(e)
                
    def _iterable(self, obj):
        if not obj:
            return []
        if hasattr(obj, '__iter__'):
            return obj
        return [obj]

    def _help(self):
        triggers = []
        for cmd in self.commands:
            triggers += cmd.triggers()
        return ['Commands: {cmds}'.format(cmds=' '.join(triggers)), '<command> -help']

    def _rehash(self):
        self._register_commands()
        self._register_listeners()
        return 'Rehash complete.'

    def _list_modules(self, path):
        ignore = ('.', '__')
        dirs = next(os.walk(path))[1]
        return [ d for d in dirs if not d.startswith(ignore) ]

    def _reloader(self, base, path):
        mnames = [name for _, name, _ in pkgutil.iter_modules([os.path.join(base, path)])]
        if not mnames:
            return
        for m in mnames:
            sub_module = os.path.join(path, m)
            self._reloader(base, sub_module)
            module = import_module(sub_module.replace('/', '.'))
            reload(module)

    def _register_commands(self):
        self.commands = []
        cmds = self._list_modules(os.path.join(install_dir, 'commands'))
        for c in cmds:
            self._reloader(install_dir, os.path.join('commands', c))
            module = import_module('commands.' + c)
            reload(module)

            do_nothing = lambda: None
            load = getattr(module, 'load_command', do_nothing)
            cmd = load()
            if cmd:
                self.commands.append(cmd)

    def _register_listeners(self):
        self.listeners = []


class BotThread(Thread):
    def __init__(self, bot):
        self._bot = bot
        Thread.__init__(self)

    def run(self):
        self._bot.start()


def main():
    try: 
        f = open(os.path.join(install_dir, 'crazybot.yaml'))
        conf = yaml.safe_load(f)
        f.close()

        bots = []
        for server, meta in conf['connections'].items():
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

            bots.append(BotThread(StockBot(nickname, password, channels, server, port)))

        for bot in bots:
            bot.start()
    except Exception as e:
        log.exception(e)

if __name__ == "__main__":
    with context:
        main()
