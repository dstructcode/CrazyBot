from sqlalchemy.orm import sessionmaker

from plugin.command import Command
from commands.points import User, Point

import datetime
import logging

log = logging.getLogger(__name__)

class Points(Command):

    def __init__(self, engine):
        self.engine = engine

    def help(self, trigger):
        if trigger == '.more':
            return '.more <nick> -- Give a user more points'
        if trigger == '.less':
            return '.less <nick> -- Remove points from a user'
        if trigger == '.points':
            return '.points <nick> -- Get a user\'s total points'

    def triggers(self):
        return ['.more', '.less', '.points']

    def run(self, source, channel, trigger, args):
        if trigger == '.points':
            if len(args) == 0:
                return self._count(source.nick)
            if len(args) == 1:
                return self._count(args[0])
        if trigger == '.more':
            if len(args) == 1:
                if source.nick == args[0]:
                    return ['So greedy.']
                return self._add(args[0], channel.users())
        if trigger == '.less':
            if len(args) == 1:
                return self._sub(args[0], channel.users())

    def _count(self, nick):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = None
        user = session.query(User).filter(User.nick == nick).one()
        point = session.query(Point).filter(Point.user.has(id=user.id)).one()
        response = ['[{nick}] {count} point(s)'.format(nick=nick, count=point.count)]
        session.close()
        return response

    def _add(self, nick, users):
        if nick not in users:
            return # TODO: raise error
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = None
        try:
            user = session.query(User).filter(User.nick == nick).one()
            point = session.query(Point).filter(Point.user.has(id=user.id)).one()
            delta = datetime.timedelta(minutes=1) + point.time
            now = datetime.datetime.utcnow()
            if now < delta:
                session.close()
                return
            point.time = now
            point.count += 1
            session.commit()
            session.close()
        except Exception, e:
            log.exception(e)
            log.info("Adding point tracking for %s" % nick)
            user = User(nick=nick)
            point = Point(user_id=user.id, user=user)
            point.count = 1
            session.add(user)
            session.add(point)
            session.commit()
            session.close()
        return ['{nick} has gained a point.'.format(nick=nick)]

    def _sub(self, nick, users):
        if nick not in users:
            return # TODO: raise error
        Session = sessionmaker(bind=self.engine)
        session = Session()
        p = None
        try:
            user = session.query(User).filter(User.nick == nick).one()
            point = session.query(Point).filter(Point.user.has(id=user.id)).one()
            delta = datetime.timedelta(minutes=1) + point.time
            now = datetime.datetime.utcnow()
            if now < delta:
                session.close()
                return
            point.time = now
            point.count -= 1
            session.commit()
            session.close()
        except Exception, e:
            log.exception(e)
            log.info("Adding point tracking for %s" % nick)
            user = User(nick=nick)
            point = Point(user_id=user.id, user=user)
            point.count = -1
            session.add(user)
            session.add(point)
            session.commit()
            session.close()
        return ['{nick} has lost a point.'.format(nick=nick)]
