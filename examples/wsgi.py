from potpy.context import Context
from potpy.wsgi import PathRouter


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


class Application(object):
    router = PathRouter(
        ('hello', '/hello/{name}', [
            (get_greeting, 'greeting'),
            Greeter
        ]),
    )

    def not_found(self, environ, start_response):
        message = 'The requested resource could not be found.'
        start_response('404 Not Found', [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(message)))
        ])
        return [message]

    def __call__(self, environ, start_response):
        context = Context(environ=environ, path=environ['PATH_INFO'])
        try:
            response = context.inject(self.router)
        except self.router.NoRoute:
            return self.not_found(environ, start_response)
        return response(environ, start_response)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('', 8000, Application()).serve_forever()
