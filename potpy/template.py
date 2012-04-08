import re


def _parse(template):
    parts = []
    bracket_level = 0
    start = 0
    capture_bracket = False
    for i, c in enumerate(template):
        if c == '{':
            if capture_bracket:
                capture_bracket = False
                continue
            if template[i+1:i+2] == '{':
                capture_bracket = True
                continue
            if not bracket_level:
                part = template[start:i] \
                    .replace('\\', '\\\\').replace('{{', '{')
                parts.append((part, None))
                start = i + 1
            bracket_level += 1
        elif c == '}':
            if not bracket_level:
                continue
            bracket_level -= 1
            if not bracket_level:
                bracket = template[start:i]
                if ':' in bracket:
                    name, regex = bracket.split(':', 1)
                else:
                    name = bracket
                    regex = '.*'
                parts.append((regex, name))
                start = i + 1
    if bracket_level:
        raise ValueError('unbalanced brackets')
    part = template[start:].replace('\\', '\\\\').replace('{{', '{')
    parts.append((part, None))
    return parts


def _make_pattern(parsed):
    return ''.join(
        '(?P<%s>%s)' % (name, part) if name else part.replace('{', r'\{')
        for part, name in parsed
    ) + '$'


def _make_fill_template(parsed):
    return ''.join(
        '%%(%s)s' % (name,) if name else part.replace('%', '%%')
        for part, name in parsed
    )


class Template(object):
    """
    A simple string template class.

    Allows you to match against a string, extracting a dictionary of template
    parameters, with optional parameter type conversion. An example template::

        >>> t = Template('Hello my name is {name}!')

    Using the :meth:`~Template.match` method, you can extract information from
    a string::

        >>> t.match('Hello my name is David!')
        {'name': 'David'}

        >>> t.match('This string does not match.')

    Parameter type conversion allows you to coerce parameters to Python
    types::

        >>> t = Template('The answer is {answer}', answer=int)
        >>> t.match('The answer is 42')
        {'answer': 42}

    You can also specify a regex in your parameter spec to further refine
    matches::

        >>> t = Template('/posts/{post_id:\d+}', post_id=int)
        >>> t.match('/posts/37')
        {'post_id': 37}
        >>> t.match('/posts/foo')

    The reverse of matching is filling. Use the :meth:`~Template.fill` method
    to insert information into your template string::

        >>> t = Template('The answer is {answer}')
        >>> t.fill(answer=42)
        'The answer is 42'
    """
    def __init__(self, template, **type_converters):
        self.template = template
        self.type_converters = type_converters
        parsed = _parse(template)
        self.regex = re.compile(_make_pattern(parsed))
        self.fill_template = _make_fill_template(parsed)

    def match(self, string):
        """Match a string against the template.

        If the string matches the template, return a dict mapping template
        parameter names to converted values, otherwise return ``None``.

        >>> t = Template('Hello my name is {name}!')
        >>> t.match('Hello my name is David!')
        {'name': 'David'}
        >>> t.match('This string does not match.')
        """
        m = self.regex.match(string)
        if m:
            c = self.type_converters
            return dict((k, c[k](v) if k in c else v)
                        for k, v in m.groupdict().iteritems())
        return None

    def fill(self, **kwargs):
        """Fill a template string with the given parameters.

        >>> Template('The answer is {answer}').fill(answer=42)
        'The answer is 42'
        """
        return self.fill_template % kwargs
