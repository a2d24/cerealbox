import builtins

from inspect import signature

NoneType = type(None)


class Cereal:
    _builtin_names = dir(builtins)

    def __init__(self, encoders):
        self.encoders = {}
        self.extend_encoders(encoders)

    def __call__(self, v):
        return self.serialize(v)

    def extend_encoders(self, encoders):
        for _type, _fn in (encoders or {}).items():
            self.encoders[_type] = self._parse_function(_fn)

    def _parse_function(self, fn):

        # Use builtins and NoneType as is
        if self._is_builtin(fn) or fn is NoneType:
            return fn

        # Inspect custom functions, if it has a serializer arg/kwarg then wrap it in a lambda
        params = signature(fn).parameters
        for name, param in params.items():
            if name == 'serialize':
                return lambda x: fn(x, serialize=self)
        else:
            return fn

    def _is_builtin(self, fn):
        return fn.__name__ in self._builtin_names and fn == getattr(builtins, fn.__name__)

    def serialize(self, v):
        # Check the class type and its superclasses for a matching encoder
        for base in v.__class__.__mro__[:-1]:
            try:
                encoder = self.encoders[base]
                return v if base is encoder else encoder(v)
            except KeyError:
                continue
        else:  # We have exited the for loop without finding a suitable encoder
            raise TypeError(f"Unable to serialize value {v} of type {v.__class__.__name__}")
