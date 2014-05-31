import signal
import traceback
import threading
import weakref

_default_handler = None

_lock = threading.Lock()
_extra_handlers = {}
_interrupted = False


class _WeakHandler(object):
    def __init__(self, obj, func):
        self._obj = weakref.ref(obj, lambda ref: remove_handler(self))
        self._func = func
        add_handler(self)

    def __call__(self):
        obj = self._obj()
        if obj is not None:
            if self._func is None:
                obj()
            else:
                self._func(obj)


class InterruptibleCondition(threading._Condition):
    def __init__(self, *args, **kwargs):
        super(InterruptibleCondition, self).__init__(*args, **kwargs)
        self._interrupted = False
        add_weak_handler(self, InterruptibleCondition._interrupt)

    def _interrupt(self):
        with self:
            self._interrupted = True
            self.notify_all()

    def wait(self, timeout=None):
        if self._interrupted:
            raise KeyboardInterrupt
        super(InterruptibleCondition, self).wait(timeout)
        if self._interrupted:
            raise KeyboardInterrupt


def add_handler(f):
    with _lock:
        if _interrupted:
            raise KeyboardInterrupt
        _extra_handlers[id(f)] = f


def remove_handler(f):
    with _lock:
        del _extra_handlers[id(f)]


def add_weak_handler(obj, func=None):
    _WeakHandler(obj, func)


def _handle_int(signum, frame):
    global _interrupted

    handlers = None
    with _lock:
        if not _interrupted:
            _interrupted = True
            handlers = _extra_handlers.values()

    if handlers is not None:
        for handler in handlers:
            try:
                handler()
            except:
                traceback.print_exc()

    _default_handler(signum, frame)


def _is_main_thread():
    # Ugly hack described at:
    # http://comments.gmane.org/gmane.comp.python.devel/141370
    return threading.current_thread().ident == threading._shutdown.__self__.ident


def init():
    global _default_handler

    if _default_handler is None:
        _default_handler = signal.signal(signal.SIGINT, _handle_int)


if _is_main_thread():
    init()
