import copy
from urllib import urlencode

from ws4py.client import WebSocketBaseClient
from ws4py.exc import HandshakeError
from ws4py.messaging import BinaryMessage

from .. import const
from .. import socket

__all__ = ["BinaryMessage", "WebSocketClient"]


class WebSocketClient(WebSocketBaseClient):
    fake_socket_class = socket.FakeSocket
    reading_buffer_size = 1000

    def __init__(self, server, url=None, params=None):
        if url is None:
            url = "ws://{}:{}".format(const.FAKE_HTTP_HOST, const.FAKE_HTTP_PORT)

        if params is not None:
            url = "{}?{}".format(url, urlencode(params))

        super(WebSocketClient, self).__init__(url=url)

        self.client_socket = self.fake_socket_class()
        self.server_socket = self.fake_socket_class()

        self.sock = socket.FakeSocketPipe(self.client_socket, self.server_socket)
        self.sock.connect((const.FAKE_HTTP_HOST, const.FAKE_HTTP_PORT))

        self._server = server
        self._messages = []

    def connect(self):
        """
        Connects this websocket and starts the upgrade handshake
        with the remote endpoint.
        """
        if self.scheme == "wss":
            raise NotImplementedError

        self.sock.sendall(self.handshake_request)

        self._server.finish_request(
            socket.FakeSocketPipe(self.server_socket, self.client_socket), (const.FAKE_HTTP_HOST, const.FAKE_HTTP_PORT)
        )

        response = b""
        double_clrf = b"\r\n\r\n"
        while True:
            chunk = self.sock.recv(128)
            if not chunk:
                break
            response += chunk
            if double_clrf in response:
                break

        if not response:
            self.close_connection()
            raise HandshakeError("Invalid response")

        headers, _, body = response.partition(double_clrf)
        response_line, _, headers = headers.partition(b"\r\n")

        try:
            self.process_response_line(response_line)
            self.protocols, self.extensions = self.process_handshake_header(headers)
        except HandshakeError:
            self.close_connection()
            raise

        self.handshake_ok()
        if body:
            self.process(body)

    def received_message(self, message):
        """
        Override the base class to store the incoming message
        in the `messages` queue.
        """
        self._messages.append(copy.deepcopy(message))

    def ponged(self, pong):
        """
        Override the base class to store the incoming pong
        in the `messages` queue.
        """
        self._messages.append(copy.deepcopy(pong))

    def receive(self):
        """
        Returns messages that were stored into the
        `messages` queue and returns `None` when the
        """
        try:
            message = self._messages.pop(0)
        except IndexError:
            return None

        return message

    def once(self):
        old_size = len(self._messages)

        while old_size == len(self._messages):
            if not super(WebSocketClient, self).once():
                return False

        return True

    def receive_next_message(self):
        self.once()
        return self.receive()
