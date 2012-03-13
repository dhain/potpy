from potpy.wsgi import PathRouter, MethodRouter, App


class Greeter(object):
    def __init__(self, greeting):
        self.greeting = greeting

    def __call__(self, environ, start_response):
        start_response('200 OK', [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(self.greeting))),
        ])
        return [self.greeting]


def get_greeting(name):
    return 'Hello, %s' % (name,)


hello = MethodRouter(
    (('GET', 'HEAD'), [
        (get_greeting, 'greeting'),
        Greeter
    ]),
)


urls = PathRouter(
    ('hello', '/hello/{name}', hello),
)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('', 8000, App(urls)).serve_forever()
