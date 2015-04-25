#! /usr/bin/env python

from importlib import import_module
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

logging.basicConfig(filename=os.path.join(install_dir, LOG_FILENAME), level=logging.INFO)
log = logging.getLogger(__name__)
fh = logging.root.handlers[0]
context = daemon.DaemonContext(
    files_preserve = [
        fh.stream,
    ],
)

irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer

class UpdateHandler(FileSystemEventHandler):
    def __init__(self, bot):
        self.bot = bot

    def on_created(self, event):
        if not os.path.basename(event.src_path).startswith('.'):
            self.bot.rehash()

    def on_modified(self, event):
        if not os.path.basename(event.src_path).startswith('.'):
            self.bot.rehash()

class CrazyBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, password, channels, server, port=6667):
        log.info("Instantiating CrazyBot for server %s" % server)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.password = password
        self.channel_list = channels
        self.commands = []
        self.listeners = []
        self.rehash()
        self.observer = Observer()
        self.observer.schedule(UpdateHandler(self), os.path.join(install_dir, 'commands'), recursive=True)
        self.observer.schedule(UpdateHandler(self), os.path.join(install_dir, 'listeners'), recursive=True)
        self.observer.start()

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

        line = e.arguments[0].strip()
        if not all(ord(c) < 128 for c in line):
            return

        line = line.split()
        trigger, msg = line[0], line[1:]

        method = getattr(self, "_" + trigger.lstrip('.'), None)
        if method:
            response = method(msg)
            for msg in self._iterable(response):
                c.privmsg(e.target, msg)
            return

        for listener in self.listeners:
            try:
                for response in self._iterable(listener.run(' '.join(line))):
                    c.privmsg(e.target, response)
            except Exception as e:
                log.exception(e)

        for cmd in self.commands:
            if trigger in cmd.triggers():
                channel = self.channels[e.target]
                try:
                    response = cmd.run(e.source, channel, trigger, msg)
                    for msg in self._iterable(response):
                        c.privmsg(e.target, msg)
                except Exception as e:
                    log.exception(e)

    def rehash(self):
        self._register_plugins()
        log.debug('Rehash complete')

    def _iterable(self, obj):
        if not obj:
            return []
        if hasattr(obj, '__iter__'):
            return obj
        return [obj]

    def _help(self, msg):
        if not msg:
            triggers = ' '.join([ t for c in self.commands for t in c.triggers() ])
            return ['Commands: {cmds}'.format(cmds=triggers), '.help <command>']

        if len(msg) == 1:
            trigger = msg[0]
            for cmd in self.commands:
                if trigger in cmd.triggers():
                    return cmd.help(trigger)

    def _list_modules(self, path):
        ignore = ('.', '__')
        dirs = next(os.walk(path))[1]
        return [ d for d in dirs if not d.startswith(ignore) ]

    def _reload(self, module):
        try:
            m = import_module(module)
            reload(m)
            return m
        except Exception as e:
            log.exception(e)

    def _reloader(self, base, path):
        mnames = [name for _, name, _ in pkgutil.iter_modules([os.path.join(base, path)])]
        if not mnames:
            return
        for m in mnames:
            sub_module = os.path.join(path, m)
            self._reloader(base, sub_module)
            self._reload(sub_module.replace('/', '.'))

    def _register_plugins(self):
        types = ['commands', 'listeners']
        for t in types:
            plugins = getattr(self, t)
            plugins[:] = []
            modules = self._list_modules(os.path.join(install_dir, t))
            for m in modules:
                self._reloader(install_dir, os.path.join(t, m))
                module = self._reload(t+'.'+m)
                if not module:
                    pass
                func = 'load_{t}'.format(t=t.rstrip('s'))
                do_nothing = lambda: None
                load = getattr(module, func, do_nothing)
                plugin = load()
                if plugin:
                    plugins.append(plugin)


class BotThread(Thread):
    def __init__(self, bot):
        self._bot = bot
        Thread.__init__(self)

    def run(self):
        try:
            self._bot.start()
        except Exception as e:
            log.exception(e)


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

            bots.append(BotThread(CrazyBot(nickname, password, channels, server, port)))

        for bot in bots:
            bot.start()
    except Exception as e:
        log.exception(e)

if __name__ == "__main__":
    with context:
        main()
