#!/usr/bin/env python

import argparse

from dev import open_device


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fakedev', action='store_true')
    args = parser.parse_args()

    with open_device(fake=args.fakedev) as f:
        while True:
            line = f.readline()
            if not line:
                return
            print repr(line)


if __name__ == '__main__':
    main()
