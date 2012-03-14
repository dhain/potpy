class InvalidTodoError(Exception):
    pass


def TodoReader(postdata):
    try:
        return postdata['todo']
    except KeyError:
        raise InvalidTodoError()
