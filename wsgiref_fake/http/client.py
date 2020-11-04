import json as json_

import six
from six.moves import http_client

from .. import const
from .. import socket


class HTTPClient(object):
    def __init__(self, server):
        self._server = server

    def request(self, method, path, json=None, headers=None):
        client_socket = socket.FakeSocket()
        server_socket = socket.FakeSocket()

        sock = socket.FakeSocketPipe(client_socket, server_socket)
        sock.connect((const.FAKE_HTTP_HOST, const.FAKE_HTTP_PORT))

        # Build a request
        headers = headers or {}

        if json:
            body = json_.dumps(json)
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = len(body)
        else:
            body = b""

        fake_client = http_client.HTTPConnection(host=const.FAKE_HTTP_HOST, port=const.FAKE_HTTP_PORT)
        fake_client.putrequest(method=method, url=path)

        for header_name, header_value in six.iteritems(headers):
            fake_client.putheader(header_name, header_value)
        fake_client._buffer.extend((b"", body, b"", b""))  # noqa pylint: disable=protected-access
        raw_request = b"\r\n".join(fake_client._buffer)  # noqa pylint: disable=protected-access

        # Make a request
        client_socket.sendall(raw_request)

        self._server.finish_request(sock, (const.FAKE_HTTP_HOST, const.FAKE_HTTP_PORT))

        # Parse a response
        response = http_client.HTTPResponse(sock=server_socket)
        response.begin()

        return response
