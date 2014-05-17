import subprocess
import fcntl
import os

import fakedev

DEVICE_FILES = map('/dev/ttyACM{}'.format, xrange(4))
DEVICE_SPEED = 9600


def discard_available_data(f):
    fcntl.fcntl(f.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    while True:
        try:
            f.readline()
        except IOError:
            break

    fcntl.fcntl(f.fileno(), fcntl.F_SETFL, 0)


def open_real_device():
    for path in DEVICE_FILES:
        if os.path.exists(path):
            break
    else:
        raise ValueError('Device not found')

    # setup the device
    subprocess.check_call(
        'stty -F {} cs8 {} ignbrk -brkint -icrnl -imaxbel -opost -onlcr -isig -icanon -iexten -echo '
        '-echoe -echok -echoctl -echoke noflsh -ixon -crtscts min 100 time 2'.format(
            path,
            DEVICE_SPEED
        ),
        shell=True
    )

    f = open(path)
    discard_available_data(f)
    return f


def open_fake_device():
    f = fakedev.open_device()
    discard_available_data(f)
    return f


def open_device(fake=False):
    if fake:
        return open_fake_device()
    else:
        return open_real_device()
