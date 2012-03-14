from webob import Request
from webob.exc import HTTPCreated
from potpy.wsgi import PathRouter, MethodRouter, App

from . import presenters, reader, repository


index = MethodRouter(
    (('GET', 'HEAD'), [
        (lambda repository: repository.getall(), 'todos'),
        presenters.TodoListPresenter
    ]),
    (('POST',), [
        (reader.TodoReader, 'todo', [
            (reader.InvalidTodoError, presenters.InvalidTodoResponse)
        ]),
        (lambda repository, todo: repository.put(todo), 'todo_id'),
        lambda todo_id: HTTPCreated(location=str(todo_id))
    ]),
)


todo = MethodRouter(
    (('GET', 'HEAD'), [
        (lambda repository, todo_id: repository.get(int(todo_id)), 'todo',
         [(
             repository.Repository.NotFound,
             presenters.NotFoundResponse
         )]),
        presenters.TodoPresenter
    ]),
)


urls = PathRouter(
    ('index', '/', index),
    ('todo', '/{todo_id:\d+}', todo),
)


def factory(global_config, **local_config):
    default_context = {
        'repository': repository.Repository(),
        'request': lambda environ: Request(environ),
        'postdata': lambda request: request.POST,
    }
    return App(urls, default_context)
