def make_regex(template):
    bracket_level = 0
    start = 0
    parts = []
    for i, c in enumerate(template):
        if c == '{':
            if not bracket_level:
                part = template[start:i].replace('\\', '\\\\')
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
        raise ValueError()
    part = template[start:].replace('\\', '\\\\')
    parts.append((part, None))
    return ''.join(
        '(?P<%s>%s)' % (name, part) if name else part
        for part, name in parts
    )
