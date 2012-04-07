import re
import inspect
from pkg_resources import resource_stream

from .wsgi import PathRouter, MethodRouter


_trailing_spaces_or_comment = re.compile(r'\s*(?:#.*)?$')
_tabsp = ' ' * 8
_leading_spaces = re.compile(r'\s*')
_identifier = '[a-zA-Z_][a-zA-Z0-9_]*'
_dotted_identifier = r'%s(?:\.%s)*' % (_identifier, _identifier)
_path_spec = re.compile(
    r'(?:(%s)\s+)?(.+?)(?:\s+\((%s:\s*%s(?:,\s*%s:\s*%s)*)\))?:$' % (
        _identifier,
        _identifier, _dotted_identifier,
        _identifier, _dotted_identifier))
_method_name = '[^%s\x7f()<>@,;:\\\\"/[\]?={} \t%s]+' % (
    ''.join(chr(x) for x in xrange(32)),
    ''.join(chr(x) for x in xrange(128, 256))
)
_method_spec = re.compile(r'(%s(?:,\s*%s)*):$' % (
    _method_name, _method_name))
_handler_spec = re.compile(r'(%s)(?:\s+\((%s)\))?:?$' % (
    _dotted_identifier, _identifier))
_exc_spec = re.compile(r'(%s(?:,\s*%s)*):\s*(%s)$' % (
    _dotted_identifier, _dotted_identifier, _dotted_identifier))


def parse_path_spec(spec):
    m = _path_spec.match(spec)
    if not m:
        raise SyntaxError('expecting path spec')
    name, path, types = m.groups()
    types = dict(tuple(s.strip() for s in t.split(':'))
                 for t in types.split(',')) if types else {}
    return name, path, types


def parse_method_spec(spec):
    m = _method_spec.match(spec)
    if not m:
        raise SyntaxError('expecting method spec')
    return [method.strip() for method in m.group(1).split(',')]


def parse_handler_spec(spec):
    m = _handler_spec.match(spec)
    if not m:
        raise SyntaxError('expecting handler spec')
    return tuple(m.groups())


def parse_exception_handler_spec(spec):
    m = _exc_spec.match(spec)
    if not m:
        raise SyntaxError('expecting exception handler spec')
    types, handler = m.groups()
    types = tuple(t.strip() for t in types.split(','))
    return types, handler


def split_indent(line):
    spaces = _leading_spaces.match(line).group(0).replace('\t', _tabsp)
    trailing = _trailing_spaces_or_comment.search(line)
    if trailing:
        line = line[:trailing.start()]
    return len(spaces), line.strip()


class IndentChecker(object):
    def __init__(self, lines):
        self.lines = iter(lines)
        self.indents = []
        self._it = self._iter()

    def _iter(self):
        for line in self.lines:
            if _trailing_spaces_or_comment.match(line):
                continue
            indent, line = split_indent(line)
            if not self.indents:
                self.indents.append(indent)
            if indent > self.indents[-1]:
                self.indents.append(indent)
            while indent < self.indents[-1]:
                self.indents.pop()
                yield -1, None
            if indent > self.indents[-1]:
                raise SyntaxError('incorrect indent')
            yield len(self.indents) - 1, line

    def __iter__(self):
        return self._it


def find_object(module, name):
    path = name.split('.')
    try:
        obj = getattr(module, path[0])
    except AttributeError:
        try:
            obj = __builtins__[path[0]]
        except KeyError:
            raise LookupError()
    for name in path[1:]:
        try:
            obj = getattr(obj, name)
        except AttributeError:
            raise LookupError()
    return obj


def read_exception_handler_block(lines, module):
    exc_handlers = []
    for depth, line in lines:
        if depth < 3:
            break
        types, handler = parse_exception_handler_spec(line)
        types = tuple(find_object(module, t) for t in types)
        handler = find_object(module, handler)
        exc_handlers.append((types, handler))
    return exc_handlers


def read_handler_block(lines, module):
    handlers = []
    for depth, line in lines:
        if depth < 2:
            break
        handler, name = parse_handler_spec(line)
        handler = find_object(module, handler)
        if line.endswith(':'):
            exc_handlers = read_exception_handler_block(lines, module)
        else:
            exc_handlers = ()
        handlers.append((handler, name, exc_handlers))
    return handlers


def read_method_block(lines, module):
    method_router = MethodRouter()
    for depth, line in lines:
        if depth < 1:
            break
        methods = parse_method_spec(line)
        handlers = read_handler_block(lines, module)
        if '*' in methods:
            if len(methods) > 1:
                raise SyntaxError('wildcard must be specified by itself')
            return handlers
        method_router.add(tuple(methods), handlers)
    return method_router


def _calling_module():
    frm = inspect.stack()[2]
    try:
        return inspect.getmodule(frm[0])
    finally:
        del frm


def parse_config(lines, module=None):
    if module is None:
        module = _calling_module()
    lines = IndentChecker(lines)
    path_router = PathRouter()
    for depth, line in lines:
        if depth > 0:
            raise SyntaxError('unexpected indent')
        name, path, types = parse_path_spec(line)
        if types:
            template_arg = (path, dict(
                (k, find_object(module, v))
                for k, v in types.iteritems()
            ))
        else:
            template_arg = path
        method_router = read_method_block(lines, module)
        path_router.add(name, template_arg, method_router)
    return path_router


def load_config(name='urls.conf'):
    module = _calling_module()
    config = resource_stream(module.__name__, name)
    return parse_config(config, module)
