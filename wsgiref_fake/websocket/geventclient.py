import gevent.fileobject
import gevent.os

from . import client
from .. import socket


class GeventFakeSocket(socket.FakeSocket):
    def makefile(self, mode="r", bufsize=-1):  # noqa pylint: disable=unused-argument
        fobj = super(GeventFakeSocket, self).makefile(mode, 0)

        return gevent.fileobject.FileObjectThread(fobj, mode=mode, bufsize=0)

    def sendall(self, data, flags=0):  # noqa pylint: disable=unused-argument
        gevent.os.tp_write(self.fd_w.origin, data)

    def recv(self, buffersize, flags=None):  # noqa pylint: disable=unused-argument
        return gevent.os.tp_read(self.fd_r.origin, buffersize)


class GeventWebSocketClient(client.WebSocketClient):
    fake_socket_class = GeventFakeSocket
