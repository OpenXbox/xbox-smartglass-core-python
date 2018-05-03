"""
Wrapper around gevent's greenlets
"""
import gevent


class Event(object):
    def __init__(self, green=False):
        self.handlers = []
        self.green = green

    def add(self, handler):
        if not callable(handler):
            raise TypeError("Handler should be callable")
        self.handlers.append(handler)

    def remove(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    def __iadd__(self, handler):
        self.add(handler)
        return self

    def __isub__(self, handler):
        self.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        for handler in self.handlers:
            if self.green:
                gevent.spawn(handler, *args, **kwargs)
            else:
                handler(*args, **kwargs)
