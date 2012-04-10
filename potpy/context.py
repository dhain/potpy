import inspect


class Context(dict):
    """
    A dict class that can call callables with arguments from itself.

    Best explained with an example:

    >>> def answer(question, foo):
    ...     return 'The answer to the %s question is: %d' % (question, foo)
    ...
    >>> ctx = Context(foo=42, question='ultimate')
    >>> ctx.inject(answer)
    'The answer to the ultimate question is: 42'

    Callable items are called before being passed to the callable:

    >>> ctx = Context(foo=lambda bar: bar.upper(), bar='qux')
    >>> ctx.inject(lambda foo: foo)
    'QUX'

    .. note::

        Callable items are called during :meth:`__getitem__`:

            >>> Context(foo=lambda: 42)['foo']
            42

    Contexts have ``'context'`` as an implicit a member, so callables can
    refer to the context itself:

    >>> ctx = Context(foo='foo')
    >>> ctx.inject(lambda context: dict(context))
    {'foo': 'foo'}

    When injecting a call, you may override context items (or provide missing
    items) with keyword arguments:

    >>> ctx.inject(lambda foo, bar: (foo, bar), bar='bar')
    ('foo', 'bar')

    .. note::

        ``*args``- and ``**kwargs``-style arguments cannot be injected at this
        time.

    .. note::

        Due to limitations of the :mod:`inspect` module, builtin and extension
        functions cannot be injected. You may work around this by wrapping the
        function in Python:

            >>> ctx = Context(n='42')
            >>> ctx.inject(lambda n: int(n))
            42
    """
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
            if '__init__' not in obj.__dict__:
                return [], [], None, None
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
        """Inject arguments from context into a callable.

        :param func: The callable to inject arguments into.
        :param \*\*kwargs: Specify values to override context items.
        """
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
