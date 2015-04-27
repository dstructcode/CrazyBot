# -*- coding: utf-8 -*-

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from commands.weather import User, Location
from plugin.command import Command

import httplib, urllib, simplejson, logging, forecastio, re, socket

log = logging.getLogger(__name__)

API_KEY = ''


class Weather(Command):
    def __init__(self, engine):
        self.engine = engine

    def help(self, trigger):
        return [".w [place] [+ <place>] [--]"]

    def triggers(self):
        return ['.w', '.weather']

    def run(self, source, channel, trigger, args):
        nick = source.nick
        userhost = source.userhost
        if len(args) == 0:
            return self.get_weather(nick, userhost)
        if args[0] == '+':
            location = ' '.join(args[1:])
            user = self.get_user(nick, userhost)
            if user:
                return self.update(nick, user, location)
            return self.add(nick, userhost, location)
        if args[0] == '--':
            return self.reset(nick, userhost)
        user = self.get_user(args[0], None)
        if user:
            return self.get_weather_by_user(user)
        return self.get_weather_by_location(' '.join(args))

    def add(self, nick, userhost, location):
        if not self.get_weather_by_location(location):
            return "[{nick}] Not a valid location.".format(nick=nick)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        user = User(nick=nick, userhost=userhost)
        location = Location(user_id=user.id, user=user, location=location)
        session.add(user)
        session.add(location)
        session.commit()
        session.refresh(location)
        session.close()
        return "[{nick}] Location added.".format(nick=nick)

    def update(self, nick, user, new):
        if not self.get_weather_by_location(new):
            return "[{nick}] Not a valid location.".format(nick=user.nick)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        location.location = new
        session.commit()
        session.close()
        return "[{nick}] Location updated.".format(nick=nick)

    def reset(self, nick, userhost):
        user = self.get_user(nick, userhost)
        if not user:
            return
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        location.location = None
        session.commit()
        session.close()
        return "[{nick}] Location reset.".format(nick=user.nick)

    def get_weather_by_user(self, user):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        location = session.query(Location).filter(Location.user.has(id=user.id)).one()
        session.refresh(location)
        session.close()
        return self.get_weather_by_location(location.location)

    def get_forecast(self, lat, lng):
        return forecastio.load_forecast(API_KEY, lat, lng, units='us')

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
            if not response['status'] == 'OK':
                return
            results = response['results'][0]
            latlng = results['geometry']['location']
            name = results['formatted_address']
            forecast = self.get_forecast(latlng['lat'], latlng['lng'])
            curr = forecast.currently()
            return name + sep + curr.summary + sep + str(curr.temperature) + unicode(' ºF', "utf-8") 
        except Exception as e:
            log.exception(e)
            log.info(response)

    def get_weather_by_ip(self, ip):
        if not ip:
            return
        sep = " \x0307|\x03 "
        api = '/json'
        connection = httplib.HTTPConnection('ip-api.com')
        requesturl = '{api}/{ip}'.format(api=api, ip=ip)
        connection.request('GET', requesturl)
        response = connection.getresponse().read()
        connection.close()
        try:
            response = simplejson.loads(response)
            if response['status'] != 'success':
                return
            name = response['city'] + ', ' + response['region'] + ' ' + response['zip']
            forecast = self.get_forecast(response['lat'], response['lon'])
            curr = forecast.currently()
            return name + sep + curr.summary + sep + str(curr.temperature) + unicode(' ºF', "utf-8")
        except Exception as e:
            log.exception(e)
            log.info(response)

    def get_weather(self, nick, userhost):
        location = self.get_location(nick, userhost)
        if not location:
            try:
                # socket.getaddrinfo returns the following format:
                # (family, socktype, proto, canonname, (ip, port[, flow info, scope]))
                ip = socket.getaddrinfo(userhost.split('@')[1], 80)[0][4][0]
                if ip:
                    return self.get_weather_by_ip(ip)
            except Exception as e:
                log.exception(e)
                pass
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
