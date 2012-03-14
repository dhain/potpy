import unittest
from mock import sentinel

from todo import repository


class TestRepository(unittest.TestCase):
    def test_stores_todos(self):
        repo = repository.Repository()
        todo_id = repo.put(sentinel.todo)
        self.assertEqual(repo.get(todo_id), sentinel.todo)

    def test_raises_NotFound_for_invalid_id(self):
        repo = repository.Repository()
        todo_id = 0
        with self.assertRaises(repo.NotFound) as assertion:
            repo.get(todo_id)
        self.assertEqual(assertion.exception.todo_id, todo_id)

    def test_getall_returns_all_todos(self):
        repo = repository.Repository()
        repo.put(sentinel.todo1)
        repo.put(sentinel.todo2)
        repo.put(sentinel.todo3)
        self.assertEqual(
            repo.getall(),
            [sentinel.todo1, sentinel.todo2, sentinel.todo3]
        )


if __name__ == '__main__':
    unittest.main()
