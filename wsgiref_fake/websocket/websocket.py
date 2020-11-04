from geventwebsocket.websocket import WebSocket as BaseWebSocket
from gevent.event import Event


class WebSocket(BaseWebSocket):
    def __init__(self, *args, **kwargs):
        self.pong_event = Event()

        super(WebSocket, self).__init__(*args, **kwargs)

    def handle_pong(self, header, payload):
        self.pong_event.set()


class Stream(object):  # noqa pylint: disable=too-few-public-methods
    """
    Wraps the handler's socket/rfile attributes and makes it in to a file like
    object that can be read from/written to by the lower level websocket api.
    """

    __slots__ = ('handler', 'read', 'write')

    def __init__(self, handler):
        self.handler = handler
        self.read = handler.rfile.read
        self.write = handler.connection.sendall
