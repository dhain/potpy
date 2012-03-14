from webob import Response
from webob.exc import HTTPBadRequest, HTTPNotFound
from potpy.router import Route


def TodoListPresenter(todos):
    return Response('\n'.join(todos))


def TodoPresenter(todo):
    return Response(todo)


def InvalidTodoResponse():
    raise Route.Stop(HTTPBadRequest())


def NotFoundResponse():
    raise Route.Stop(HTTPNotFound())
