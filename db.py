import json
import os

DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'db.json')


class Database(object):
    def __init__(self):
        path = DATABASE_FILE
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)
        else:
            raise IOError(
                'Database file not found. Please see README.md for '
                'details on how to create initial database file.')
        self._path = path

    def __getitem__(self, item):
        return self._data[item]

    def __contains__(self, item):
        return item in self._data

    def setdefault(self, key, value):
        return self._data.setdefault(key, value)

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def sync(self):
        # serialize first - this way we won't corrupt the database in case of exception
        s = json.dumps(self._data, indent=4)
        with open(self._path, 'w') as f:
            f.write(s)
