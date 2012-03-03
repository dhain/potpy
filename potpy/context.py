import inspect


class Context(dict):
    def _get_argspec(self, obj):
        if not callable(obj):
            raise TypeError('%r is not callable' % (obj,))
        if inspect.isfunction(obj):
            return inspect.getargspec(obj)
        if hasattr(obj, 'im_func'):
            spec = self._get_argspec(obj.im_func)
            del spec[0][0]
            return spec
        if inspect.isclass(obj):
            return self._get_argspec(obj.__init__)
        return self._get_argspec(obj.__call__)

    def __getitem__(self, key):
        if key == 'context':
            value = dict.get(self, key, self)
        else:
            value = dict.__getitem__(self, key)
        if callable(value):
            return self.inject(value)
        return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def inject(self, func, **kwargs):
        args, varargs, keywords, defaults = self._get_argspec(func)
        if defaults:
            required_args = args[:-len(defaults)]
            optional_args = args[len(required_args):]
        else:
            required_args = args
            optional_args = []
        values = [
            kwargs[arg] if arg in kwargs else self[arg]
            for arg in required_args
        ]
        if defaults:
            values.extend(
                kwargs[arg] if arg in kwargs else self.get(arg, default)
                for arg, default in zip(optional_args, defaults)
            )
        return func(*values)
