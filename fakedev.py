#!/usr/bin/env python

import os

DEVICE_FILE = os.path.join(os.path.dirname(__file__), '.fakedev')


def open_device(mode='r'):
    if not os.path.exists(DEVICE_FILE):
        os.mkfifo(DEVICE_FILE)
    return open(DEVICE_FILE, mode)


def main():
    import readline  # activate readline

    with open_device(mode='w') as f:
        while True:
            line = raw_input('> ')
            if line == 'quit':
                return
            if line.startswith('send '):
                f.write(line[5:] + '\r\n')
                f.flush()
            elif line:
                print 'Unrecognized command: {}'.format(line)


if __name__ == '__main__':
    main()
