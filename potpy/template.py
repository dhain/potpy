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
    def __init__(self, template, **type_converters):
        self.template = template
        self.type_converters = type_converters
        parsed = _parse(template)
        self.regex = re.compile(_make_pattern(parsed))
        self.fill_template = _make_fill_template(parsed)

    def match(self, string):
        m = self.regex.match(string)
        if m:
            c = self.type_converters
            return dict((k, c[k](v) if k in c else v)
                        for k, v in m.groupdict().iteritems())
        return None

    def fill(self, **kwargs):
        return self.fill_template % kwargs
