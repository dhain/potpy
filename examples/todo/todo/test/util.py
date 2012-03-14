import urllib2
from urllib import urlencode
from urlparse import urljoin
import wsgi_intercept
from wsgi_intercept.urllib2_intercept import WSGI_HTTPHandler


class WSGIInterceptClient(object):
    HTTPError = urllib2.HTTPError

    def __init__(self, app):
        self.app = app
        host = 'example.com'
        port = 80
        self.base = 'http://%s:%d' % (host, port)
        wsgi_intercept.add_wsgi_intercept(host, port, lambda: self.app)
        self.opener = urllib2.build_opener(WSGI_HTTPHandler())

    def open(self, path, data=None, headers=None):
        if headers is None:
            headers = {}
        req = urllib2.Request(urljoin(self.base, path), data, headers)
        return self.opener.open(req)

    def get(self, path):
        return self.open(path)

    def post(self, path, data, headers=None):
        if not isinstance(data, basestring):
            data = urlencode(data)
        return self.open(path, data, headers)
