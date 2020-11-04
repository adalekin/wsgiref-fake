import base64
import hashlib
import logging
from wsgiref.handlers import SimpleHandler
from wsgiref.simple_server import WSGIRequestHandler

from .websocket import Stream, WebSocket

logger = logging.getLogger("wsgiref_fake")


class FakeWebSocketWSGIHandler(SimpleHandler):
    SUPPORTED_VERSIONS = ("13", "8", "7")
    WS_KEY = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def setup_environ(self):
        """
        Setup the environ dictionary and add the
        `'wsgi.socket'` key. Its associated value
        is the real socket underlying socket.
        """
        SimpleHandler.setup_environ(self)
        self.environ["wsgi.socket"] = self.request_handler.request
        self.http_version = self.environ["SERVER_PROTOCOL"].rsplit("/")[-1]

    def run(self, application):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.

        try:
            self.setup_environ()

            self.result = self.upgrade_websocket()

            if "wsgi.websocket" in self.environ:
                if self.status and not self.headers_sent:
                    self.write(b"")
                application(self.environ, lambda s, h, e=None: [])
            else:
                self.result = application(self.environ, self.start_response)
            self.finish_response()
        except:  # noqa pylint: disable=bare-except
            try:
                self.handle_error()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                # ...and let the actual server figure it out.
                raise

    def upgrade_websocket(self):
        if self.environ.get("REQUEST_METHOD", "") != "GET":
            # This is not a websocket request, so we must not handle it
            logger.debug("Can only upgrade connection if using GET method.")
            return None

        upgrade = self.environ.get("HTTP_UPGRADE", "").lower()

        if upgrade == "websocket":
            connection = self.environ.get("HTTP_CONNECTION", "").lower()

            if "upgrade" not in connection:
                # This is not a websocket request, so we must not handle it
                logger.warning("Client didn't ask for a connection " "upgrade")
                return None
        else:
            # This is not a websocket request, so we must not handle it
            return None

        if self.http_version != "1.1":
            self.start_response("400 Bad Request", [])
            logger.warning("Bad server protocol in headers")

            return ["Bad protocol version"]

        if self.environ.get("HTTP_SEC_WEBSOCKET_VERSION"):
            return self.upgrade_connection()

        logger.warning("No protocol defined")
        self.start_response(
            "426 Upgrade Required",
            [("Sec-WebSocket-Version", ", ".join(self.SUPPORTED_VERSIONS))],
        )

        return ["No Websocket protocol version defined"]

    def upgrade_connection(self):
        """
        Validate and 'upgrade' the HTTP request to a WebSocket request.

        If an upgrade succeeded then then handler will have `start_response`
        with a status of `101`, the environ will also be updated with
        `wsgi.websocket` and `wsgi.websocket_version` keys.

        :param environ: The WSGI environ dict.
        :param start_response: The callable used to start the response.
        :param stream: File like object that will be read from/written to by
            the underlying WebSocket object, if created.
        :return: The WSGI response iterator is something went awry.
        """

        logger.debug("Attempting to upgrade connection")

        version = self.environ.get("HTTP_SEC_WEBSOCKET_VERSION")

        if version not in self.SUPPORTED_VERSIONS:
            msg = "Unsupported WebSocket Version: {0}".format(version)

            logger.warning(msg)
            self.start_response(
                "400 Bad Request",
                [("Sec-WebSocket-Version", ", ".join(self.SUPPORTED_VERSIONS))],
            )

            return [msg]

        key = self.environ.get("HTTP_SEC_WEBSOCKET_KEY", "").strip()

        if not key:
            # 5.2.1 (3)
            msg = "Sec-WebSocket-Key header is missing/empty"

            logger.warning(msg)
            self.start_response("400 Bad Request", [])

            return [msg]

        try:
            key_len = len(base64.b64decode(key))
        except TypeError:
            msg = "Invalid key: {0}".format(key)

            logger.warning(msg)
            self.start_response("400 Bad Request", [])

            return [msg]

        if key_len != 16:
            # 5.2.1 (3)
            msg = "Invalid key: {0}".format(key)

            logger.warning(msg)
            self.start_response("400 Bad Request", [])

            return [msg]

        # Check for WebSocket Protocols
        self.environ.update(
            {
                "wsgi.websocket_version": version,
                "wsgi.websocket": WebSocket(
                    self.environ, Stream(self.request_handler), self.request_handler
                ),
            }
        )

        headers = [
            (
                "Sec-WebSocket-Accept",
                base64.b64encode(
                    hashlib.sha1((key + self.WS_KEY).encode("utf-8")).digest()
                ),
            )
        ]

        logger.debug("WebSocket request accepted, switching protocols")
        self.start_response("101 Switching Protocols", headers)

        return []


class FakeWebSocketWSGIRequestHandler(WSGIRequestHandler):
    handler_class = FakeWebSocketWSGIHandler

    def __init__(self, request, client_address, server):
        # NOTE: compatibility with geventwebsocket.websocket.WebSocket
        self.logger = logger
        self.socket = request

        WSGIRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        """
        Unfortunately the base class forces us
        to override the whole method to actually provide our wsgi handler.
        """
        self.raw_requestline = self.rfile.readline()
        if not self.parse_request():
            # An error code has been sent, just exit
            return

        # next line is where we'd have expect a configuration key somehow
        handler = self.handler_class(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = (  # noqa pylint: disable=attribute-defined-outside-init
            self
        )
        handler.run(self.server.get_app())

    def finish(self):
        pass
