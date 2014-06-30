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


class Cache(object):
    def __init__(self):
        self._timeout = datetime.timedelta(minutes=15)
        self._entries = dict()

    def __getitem__(self, key):
        ts, value = self._entries[key]
        ts_now = datetime.datetime.utcnow()
        if ts + self._timeout < ts_now:
            del self._entries[key]
            raise KeyError('Timed out')
        return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        self._entries[key] = datetime.datetime.utcnow(), value


class DeviceThread(threading.Thread):
    def __init__(self, state, fake=False):
        super(DeviceThread, self).__init__()
        self.state = state
        self._fake = fake
        self._cache = Cache()
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

    def _select_current_crstests(self, participant_crstests):
        terms = participant_crstests['terms'].values()
        if not terms:
            return []
        terms.sort(key=lambda term: term['order_key'], reverse=True)
        # KR: my grade
        # return participant_crstests['tests']['2012L'].values()
        return participant_crstests['tests'][terms[0]['id']].values()

    def _load_crstest_tree(self, client, test):
        response = client.services.crstests.node(
            node_id=test['root_id'],
            recursive=True,
            fields='node_id|name|type|subnodes|visible_for_students',
        )
        test['subnodes'] = response['subnodes']

        self._load_crstest_grades(client, test)
        self._load_crstest_points(client, test)

    def _load_crstest_grades(self, client, test):
        grade_nodes = {}

        def visit(node):
            if node['type'] == 'oc':
                node['type'] = 'grade'
            if node['type'] == 'grade':
                grade_nodes[node['node_id']] = node
            for subnode in node['subnodes']:
                visit(subnode)

        visit(test)
        if not grade_nodes:
            return

        response = client.services.crstests.user_grades(
            node_ids='|'.join(map(str, grade_nodes.iterkeys())),
        )
        for user_grade in response:
            grade_nodes[user_grade['node_id']]['user_grade'] = user_grade

    def _load_crstest_points(self, client, test):
        task_nodes = {}

        def visit(node):
            if node['type'] == 'pkt':
                node['type'] = 'task'
            if node['type'] == 'task':
                task_nodes[node['node_id']] = node
            for subnode in node['subnodes']:
                visit(subnode)

        visit(test)
        if not task_nodes:
            return

        response = client.services.crstests.user_points(
            node_ids='|'.join(map(str, task_nodes.iterkeys())),
        )
        for user_grade in response:
            task_nodes[user_grade['node_id']]['user_points'] = user_grade

    def _build_crstests_panel(self, client):
        cache_key = 'crstests', client.token
        panel = self._cache.get(cache_key)
        if panel is None:
            response = client.services.crstests.participant()
            tests = self._select_current_crstests(response)
            for test in tests:
                self._load_crstest_tree(client, test)
            panel = dict(
                type='crstests',
                tests=tests
            )

            self._cache[cache_key] = panel

        return panel

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
