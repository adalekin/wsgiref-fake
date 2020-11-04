from wsgiref.simple_server import WSGIRequestHandler


class FakeWSGIRequestHandler(WSGIRequestHandler):
    def finish(self):
        pass
