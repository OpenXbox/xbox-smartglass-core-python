"""
Custom construct fields and utilities
"""
import construct


COMPILED = True


class XStruct(construct.Subconstruct):
    def __init__(self, *args, **kwargs):
        struct = construct.Struct(*args, **kwargs)
        super(XStruct, self).__init__(struct)
        self.compiled = self.compile() if COMPILED else None

    def parse(self, data, **contextkw):
        res = super(XStruct, self).parse(data, **contextkw)
        return XStructObj(self, res)

    def _parse(self, stream, context, path):
        if self.compiled:
            res = self.compiled._parse(stream, context, path)
        else:
            res = self.subcon._parse(stream, context, path)

        return res

    def _emitparse(self, code):
        return self.subcon._emitparse(code)

    def _find(self, item):
        sub = next(
            (s for s in self.subcon.subcons if s.name == item), None
        )
        if sub:
            return sub

        return None

    def __call__(self, **kwargs):
        return XStructObj(self)(**kwargs)

    def __contains__(self, item):
        return self._find(item) is not None

    def __getattr__(self, item):
        subcon = self._find(item)

        if subcon:
            return subcon

        return super(XStruct, self).__getattribute__(item)


class XStructObj(construct.Subconstruct):
    __slots__ = ['_obj']

    def __init__(self, struct, container=None):
        super(XStructObj, self).__init__(struct)
        self._obj = container if container else construct.Container({
            sc.name: None for sc in self.subcon.subcon.subcons
        })

    @property
    def container(self):
        return self._obj

    def __call__(self, **kwargs):
        self._obj.update(kwargs)
        return self

    def _parse(self, stream, context, path):
        self._obj = self.subcon._parse(stream, context, path)
        return self

    def build(self, **contextkw):
        return self.subcon.build(self._obj, **contextkw)

    def _build(self, stream, context, path):
        return self.subcon._build(self._obj, stream, context, path)

    def __getattr__(self, item):
        if item in self._obj:
            return getattr(self._obj, item)
        return super(XStructObj, self).__getattribute__(item)

    def __repr__(self):
        return '<XStructObj: %s>(%s)' % (
            self.subcon.name, self._obj
        )


def flatten(container):
    """
    Flattens `StructWrap` objects into just `Container`'s.

    Recursively walks down each value of the `Container`, flattening
    possible `StructWrap` objects.

    Args:
        container (Container): The container to flatten.

    Returns:
        `Container`: A flattened container.
    """
    obj = container.copy()
    for k, v in obj.items():
        if isinstance(v, XStructObj):
            obj[k] = flatten(v.container)

    return obj
