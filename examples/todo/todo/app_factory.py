from webob import Request
from potpy.wsgi import App
from potpy.router import Route
from potpy.configparser import load_config

from . import presenters, reader, repository


urls = load_config()


def factory(global_config, **local_config):
    default_context = {
        'repository': repository.Repository(),
        'request': lambda environ: Request(environ),
        'postdata': lambda request: request.POST,
    }
    return App(urls, default_context)
