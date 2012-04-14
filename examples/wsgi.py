from potpy.wsgi import PathRouter, MethodRouter, App

# Our domain objects
# ------------------

class Greeter(object):
    """A WSGI app that displays a greeting."""
    def __init__(self, greeting):
        self.greeting = greeting

    def __call__(self, environ, start_response):
        start_response('200 OK', [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(self.greeting))),
        ])
        return [self.greeting]


def get_greeting(name):
    """Generate a greeting for the given name."""
    return 'Hello, %s' % (name,)



# PotPy plumbing
# --------------

hello = MethodRouter(
    (('GET', 'HEAD'), [                 # when the request is a GET or HEAD

        (get_greeting, 'greeting'),     # generate a greeting and save it
                                        # to the context under the
                                        # 'greeting' key

        Greeter                         # then show the greeting
    ]),
)


urls = PathRouter(
    ('hello', '/hello/{name}', hello),  # expose the greeter at /hello/{name}
)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('', 8000, App(urls)).serve_forever()
