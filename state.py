import threading
from usos.client import Client

from db import Database
from interrupt import InterruptibleCondition

BASE_URL = 'https://usosapps.uw.edu.pl/'
START_PANEL_DATA = dict(type='greeting')


class ExclusiveError(Exception):
    pass


class _ExclusiveToken(object):
    pass


class State(object):
    def __init__(self, tt_time_shift):
        self._panel = (1, START_PANEL_DATA)
        self._lock = threading.Lock()
        self._cond = InterruptibleCondition(self._lock)
        self._exclusive_token = None
        self.db = Database()
        self.tt_time_shift = tt_time_shift

    def make_client(self, token=None):
        return Client(BASE_URL, consumer=self.db['consumer'], token=token)

    def make_client_by_card(self, card_uid):
        # raises KeyError if specified card was not found
        return self.make_client(self.db['cards'][card_uid]['token'])

    @property
    def panel(self):
        return self._panel

    def set_panel(self, panel_data):
        panel_index, _ = self._panel
        self._panel = panel_index + 1, panel_data
        self._cond.notify_all()

    def wait_panel_exclusive(self, timeout=None):
        if self._exclusive_token is not None:
            self._cond.notify_all()
        token = _ExclusiveToken()
        self._exclusive_token = token

        self._cond.wait(timeout)

        if self._exclusive_token is not token:
            raise ExclusiveError
        self._exclusive_token = None

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
