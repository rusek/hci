#!/usr/bin/env python
# coding=utf-8

import argparse
import datetime
import threading
import sys
import re
import time

from state import State, START_PANEL_DATA
from dev import open_device
from server import run_server


class DeviceThread(threading.Thread):
    def __init__(self, state, fake=False):
        super(DeviceThread, self).__init__()
        self.state = state
        self._fake = fake
        self.daemon = True

    def run(self):
        # Extra loop to support restarting fakedev
        while True:
            self._run()

    def _run(self):
        print 'Opening device fake={}'.format(self._fake)
        with open_device(fake=self._fake) as f:
            while True:
                line = f.readline()
                if not line:
                    return
                print 'Received command', repr(line)
                sys.stdout.flush()
                with self.state as state:
                    state.set_panel(
                        dict(type='loading')
                    )

                start_time = time.time()
                panel = self._build_panel(line)
                end_time = time.time()

                with self.state as state:
                    state.set_panel(panel)

                print 'Panel created, delay: %.6f' % (end_time - start_time)

    def _build_tt_panel(self, client):
        start = (datetime.datetime.today() + self.state.tt_time_shift).strftime('%Y-%m-%d')
        response = client.services.tt.user(
            fields='type|start_time|end_time|name|course_name|group_number|building_name|room_number|classtype_name',
            start=start,
            days=3
        )

        return dict(
            type='tt',
            activities=response,
            start=start,
        )

    def _build_crstests_panel(self, client):
        return dict(
            text=u'Tutaj będą oceny ze sprawdzianów'
        )

    def _build_panel(self, line):
        line = line.strip()

        match = re.match('^tt ([0-9a-fA-F]{8})$', line)
        if match:
            try:
                with self.state as state:
                    client = state.make_client_by_card(match.group(1))
            except KeyError:
                return dict(type='bad_card')
            return self._build_tt_panel(client)

        match = re.match('^crstests ([0-9a-fA-F]{8})$', line)
        if match:
            try:
                with self.state as state:
                    client = state.make_client_by_card(match.group(1))
            except KeyError:
                return dict(type='bad_card')
            return self._build_crstests_panel(client)

        if line == 'greeting':
            return START_PANEL_DATA

        return dict(
            text=line
        )


def _prepare_time_shift(s):
    if s is None:
        return datetime.timedelta()

    expected_date = datetime.datetime.strptime(s, '%Y-%m-%d')
    now = datetime.datetime.today()
    now_date = datetime.datetime(now.year, now.month, now.day)
    if expected_date != now_date:
        return expected_date - now_date
    else:
        return datetime.timedelta()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fakedev', action='store_true')
    parser.add_argument('--date')
    args = parser.parse_args()
    tt_time_shift = _prepare_time_shift(args.date)

    state = State(tt_time_shift=tt_time_shift)
    device_thread = DeviceThread(state, fake=args.fakedev)
    device_thread.start()
    run_server(state)


if __name__ == '__main__':
    main()
