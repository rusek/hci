#!/usr/bin/env python

import argparse
import threading
import sys

from state import State
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
                        dict(
                            text=line.strip()
                        )
                    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fakedev', action='store_true')
    args = parser.parse_args()

    state = State()
    device_thread = DeviceThread(state, fake=args.fakedev)
    device_thread.start()
    run_server(state)


if __name__ == '__main__':
    main()
