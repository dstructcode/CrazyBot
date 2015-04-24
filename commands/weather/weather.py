# -*- coding: utf-8 -*-

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from commands.weather import User, Location
from plugin.command import Command

import httplib, urllib, simplejson, logging, forecastio

log = logging.getLogger(__name__)

API_KEY = '4bb7463604cfc639a4fe526ed688052b'


class Weather(Command):
    def __init__(self, engine):
        self.engine = engine

    def help(self, trigger):
        return ".w [place] [add <place>]"

    def triggers(self):
        return ['.w', '.weather']

    def run(self, source, channel, trigger, args):
        nick = source.nick
        userhost = source.userhost
        if len(args) == 0:
            return self.get_weather(nick, userhost)
        if args[0] == 'add':
            user = self.get_user(nick, userhost)
            if user:
                self.update_location(user, args[1:])
                return "[{nick}] Location updated.".format(nick=nick)
            location = self.add_location(nick, userhost, args[1:])
            return "[{nick}] Location added.".format(nick=nick)
        user = self.get_user(args[0], None)
        if user:
            return self.get_weather_by_user(user)
        return self.get_weather_by_location(' '.join(args))

    def add_location(self, nick, userhost, location):
        location = ' '.join(location)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        user = User(nick=nick, userhost=userhost)
        location = Location(user_id=user.id, user=user, location=location)
        session.add(user)
        session.add(location)
        session.commit()
        session.refresh(location)
        session.close()
        return location

    def update_location(self, user, new):
        new = ' '.join(new)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        location.location = new
        session.commit()
        session.close()

    def get_weather_by_user(self, user):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        session.refresh(location)
        session.close()
        return self.get_weather_by_location(location.location)

    def get_weather_by_location(self, location):
        if not location:
            return
        sep = " \x0307|\x03 "
        api = '/maps/api/geocode/json'
        connection = httplib.HTTPSConnection('maps.googleapis.com')
        params = urllib.urlencode({'address': location}, True)
        requesturl = '{api}?{params}'.format(api=api, params=params)
        connection.request('GET', requesturl)
        response = connection.getresponse().read()
        connection.close()
        try:
            response = simplejson.loads(response)
            results = response['results'][0]
            latlng = results['geometry']['location']
            name = results['formatted_address']
            forecast = forecastio.load_forecast(API_KEY, latlng['lat'], latlng['lng'], units='us')
            curr = forecast.currently()
            return name + sep + curr.summary + sep + str(curr.temperature) + unicode(' ºF', "utf-8")
        except Exception as e:
            log.exception(e)
            log.info(response)

    def get_weather(self, nick, userhost):
        location = self.get_location(nick, userhost)
        if not location:
            return
        return self.get_weather_by_location(location)

    def get_location(self, nick, userhost):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = None

        user = self.get_user(nick, userhost)
        if not user:
            session.close()
            return
        try:
            location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        except NoResultFound:
            pass
        except Exception as e:
            log.exception(e)
        session.close()
        if location:
            return location.location;

    def get_user(self, nick, userhost):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        user = None

        try:
            user = session.query(User).filter(User.userhost == userhost).one()
        except NoResultFound:
            try:
                user = session.query(User).filter(User.nick == nick).one()
            except NoResultFound:
                pass
        except Exception, e:
            log.exception(e)
        session.close()
        return user
