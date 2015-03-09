#! /usr/bin/env python

import logging
import sys
import traceback
import irc.bot

class StockBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, channels, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel_list = channels

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
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
                for response in module.run(e.source.nick, e.source.userhost, args):
                    c.privmsg(e.target, response)
        except:
            traceback.print_exc()

def main():
    if len(sys.argv) < 4:
        print("Usage: stockbot <server[:port]> <nickname> <channel> <channel> ...")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: invalid port")
            sys.exit(1)
    else:
        port = 6667
    nickname = sys.argv[2]
    channels = sys.argv[3:]

    bot = StockBot(nickname, channels, server, port)
    bot.start()

if __name__ == "__main__":
    main()
