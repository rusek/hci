import threading
from usos.client import Client

from db import Database
from interrupt import InterruptibleCondition

BASE_URL = 'https://usosapps.uw.edu.pl/'
START_PANEL_DATA = dict(text='Default panel')


class State(object):
    def __init__(self):
        self._panel = (1, START_PANEL_DATA)
        self._lock = threading.Lock()
        self._cond = InterruptibleCondition(self._lock)
        self.db = Database()

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

    def wait_panel(self):
        self._cond.wait()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
