from wsgiref.simple_server import WSGIServer
from wsgiref.simple_server import make_server as make_server_

import six
from six.moves.socketserver import BaseServer

from . import const, handlers


class FakeWSGIServer(WSGIServer):
    def __init__(self, server_address, RequestHandlerClass):
        BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.server_bind()

    def server_bind(self):
        host, port = self.server_address
        self.server_name = host
        self.server_port = port
        self.setup_environ()


def make_server(app, server_class=FakeWSGIServer, handler_class=handlers.FakeWSGIRequestHandler):
    def _wsgi_app_encoding_hack(app):
        def wrapper(*args, **kwargs):
            result = app(*args, **kwargs)

            if result is not None:
                if six.PY2:
                    return [x.encode("iso-8859-1") for x in result]
                # Python 3 WSGI requires byte chunks; keep str responses working.
                return [x.encode("utf-8") if isinstance(x, str) else x for x in result]

            return result

        return wrapper

    return make_server_(
        host=const.FAKE_HTTP_HOST,
        port=const.FAKE_HTTP_PORT,
        app=_wsgi_app_encoding_hack(app),
        server_class=server_class,
        handler_class=handler_class,
    )
