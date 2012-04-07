from webob import Response
from webob.exc import HTTPBadRequest, HTTPNotFound, HTTPCreated
from potpy.router import Route


def TodoList(todos):
    return Response('\n'.join(todos))


def Todo(todo):
    return Response(todo)


def InvalidTodo():
    raise Route.Stop(HTTPBadRequest())


def NotFound():
    raise Route.Stop(HTTPNotFound())


def TodoCreated(todo_id):
    return HTTPCreated(location=str(todo_id))
