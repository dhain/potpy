from webob import Request
from potpy.wsgi import App
from potpy.router import Route
from potpy.configparser import parse_config

from . import presenters, reader, repository


urls = parse_config("""
index /:
    GET, HEAD:
        Route.context.repository.getall (todos)
        presenters.TodoList
    POST:
        reader.TodoReader (todo):
            reader.InvalidTodoError: presenters.InvalidTodo
        Route.context.repository.put (todo_id)
        presenters.TodoCreated
todo /{todo_id:\d+} (todo_id: int):
    GET, HEAD:
        Route.context.repository.get (todo):
            repository.Repository.NotFound: presenters.NotFound
        presenters.Todo
""".splitlines())


def factory(global_config, **local_config):
    default_context = {
        'repository': repository.Repository(),
        'request': lambda environ: Request(environ),
        'postdata': lambda request: request.POST,
    }
    return App(urls, default_context)
