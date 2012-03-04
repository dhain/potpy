def _parse_template(template):
    bracket_level = 0
    start = 0
    for i, c in enumerate(template):
        if c == '{':
            if not bracket_level:
                part = template[start:i].replace('\\', '\\\\')
                yield (part, None)
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
                yield (regex, name)
                start = i + 1
    if bracket_level:
        raise ValueError()
    part = template[start:].replace('\\', '\\\\')
    yield (part, None)


def make_regex(template):
    return ''.join(
        '(?P<%s>%s)' % (name, part) if name else part
        for part, name in _parse_template(template)
    )


def make_fill_template(template):
    return ''.join(
        '%%(%s)s' % (name,) if name else part.replace('%', '%%')
        for part, name in _parse_template(template)
    )


def fill(template, **kwargs):
    return make_fill_template(template) % kwargs
