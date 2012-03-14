import os
import urllib2
import unittest
from paste.deploy import loadapp
from .util import WSGIInterceptClient

PROJECT_BASE = os.path.join(os.path.dirname(__file__), '..', '..')
PASTE_CONFIG = os.environ.get('TODO_PASTE_CONFIG', 'deployment.ini')


class TestTodo(unittest.TestCase):
    def setUp(self):
        self.app = loadapp(
            'config:%s' % (PASTE_CONFIG,), relative_to=PROJECT_BASE)
        self.client = WSGIInterceptClient(self.app)
        self.repo = self.app.default_context['repository']

    def test_index_shows_all_todos(self):
        todos = ['Todo 1', 'Todo 2']
        todo_ids = [self.repo.put(todo) for todo in todos]
        resp = self.client.get('/')
        self.assertEqual(resp.getcode(), 200)
        self.assertEqual(resp.read(), '\n'.join(todos))

    def test_can_get_specific_todo(self):
        todos = ['Todo 1', 'Todo 2']
        todo_ids = [self.repo.put(todo) for todo in todos]
        for todo_id, todo in zip(todo_ids, todos):
            resp = self.client.get('/%d' % (todo_id,))
            self.assertEqual(resp.getcode(), 200)
            self.assertEqual(resp.read(), todo)

    def test_can_post_new_todos(self):
        todo = 'Todo 1'
        resp = self.client.post('/', {'todo': todo})
        self.assertEqual(resp.getcode(), 201)
        todo_id = int(resp.info()['location'].rsplit('/')[-1])
        self.assertEqual(self.repo.get(todo_id), todo)

    def test_missing_todo_in_postdata_returns_400_response(self):
        with self.assertRaises(urllib2.HTTPError) as assertion:
            self.client.post('/', {'foo': 'bar'})
        self.assertEqual(assertion.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
