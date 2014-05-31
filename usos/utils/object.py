class SanitizedAttribute(object):
    def __init__(self, func, name=None):
        self.func = func
        self.name = func.__name__ if name is None else name

    def __get__(self, instance, owner):
        if isinstance is None:
            return self
        else:
            try:
                return instance.__dict__[self.name]
            except KeyError:
                raise AttributeError('{0!r} has no attribute {1!r}'.format(instance, self.name))

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.func(instance, value)


def sanitized_attr(f):
    return SanitizedAttribute(f)
