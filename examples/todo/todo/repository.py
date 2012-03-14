class Repository(object):
    class NotFound(Exception):
        def __init__(self, todo_id):
            self.todo_id = todo_id

    def __init__(self):
        self.todos = []

    def put(self, todo):
        self.todos.append(todo)
        return len(self.todos) - 1

    def get(self, todo_id):
        try:
            return self.todos[todo_id]
        except IndexError:
            raise self.NotFound(todo_id)

    def getall(self):
        return self.todos
