from pecan import expose, request, redirect, abort
from datetime import date

from .. import storage


class APIController(object):

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


class RootController(object):

    @expose(template='index.html')
    def index(self):
        return dict()

    api = APIController()
