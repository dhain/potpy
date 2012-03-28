from webob import Request
from webob.exc import HTTPCreated
from potpy.wsgi import PathRouter, MethodRouter, App
from potpy.router import Route

from . import presenters, reader, repository


index = MethodRouter(
    (('GET', 'HEAD'), [
        (Route.context.repository.getall, 'todos'),
        presenters.TodoListPresenter
    ]),
    (('POST',), [
        (reader.TodoReader, 'todo', [
            (reader.InvalidTodoError, presenters.InvalidTodoResponse)
        ]),
        (Route.context.repository.put, 'todo_id'),
        lambda todo_id: HTTPCreated(location=str(todo_id))
    ]),
)


todo = MethodRouter(
    (('GET', 'HEAD'), [
        (Route.context.repository.get, 'todo',
         [(
             repository.Repository.NotFound,
             presenters.NotFoundResponse
         )]),
        presenters.TodoPresenter
    ]),
)


urls = PathRouter(
    ('index', '/', index),
    ('todo', ('/{todo_id:\d+}', {'todo_id': int}), todo),
)


def factory(global_config, **local_config):
    default_context = {
        'repository': repository.Repository(),
        'request': lambda environ: Request(environ),
        'postdata': lambda request: request.POST,
    }
    return App(urls, default_context)
