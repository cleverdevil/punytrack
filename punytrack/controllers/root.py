from pecan import expose, request, redirect, abort
from pecan.hooks import HookController, PecanHook
from datetime import date, timedelta
from dateutil.parser import parse
from pytz import utc, timezone

from .. import storage

from pecan.hooks import PecanHook


class CorsHook(PecanHook):

    def after(self, state):
        state.response.headers['Access-Control-Allow-Origin'] = 'https://cleverdevil.io'
        state.response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        state.response.headers['Access-Control-Allow-Headers'] = 'origin, authorization, accept'


class APIController(HookController):

    __hooks__ = [CorsHook()]

    @expose('json')
    def input(self, token):
        result = storage.store(token, request.json)
        return dict(result='ok' if result else 'denied')

    @expose('json')
    def current(self, token):
        return storage.get_current(token)

    @expose('json')
    def day(self, token, year, month, day):
        return storage.get_day(
            token,
            date(int(year), int(month), int(day))
        )

    @expose('json')
    def range(self, token, tz='US/Pacific', start=None, duration=24):
        zone = timezone(tz)

        print('~' * 80)
        print(zone)
        print('~' * 80)

        start = zone.localize(parse(start)).astimezone(utc)
        end = start + timedelta(hours=int(duration))

        print('=' * 80)
        print('Start: ', start.isoformat())
        print('End: ', end.isoformat())
        print('=' * 80)

        return storage.get_range(token=token, start=start, end=end)


class RootController(object):

    @expose(template='index.html')
    def index(self):
        return dict()

    api = APIController()
