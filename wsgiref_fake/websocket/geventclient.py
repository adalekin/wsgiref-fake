import gevent.fileobject
import gevent.os

from .. import socket
from . import client


class GeventFakeSocket(socket.FakeSocket):
    def makefile(self, mode="r", bufsize=-1):
        fobj = super().makefile(mode, 0)

        return gevent.fileobject.FileObjectThread(fobj, mode=mode, bufsize=0)

    def sendall(self, data, flags=0):
        gevent.os.tp_write(self.fd_w.origin, data)

    def recv(self, buffersize, flags=None):
        return gevent.os.tp_read(self.fd_r.origin, buffersize)


class GeventWebSocketClient(client.WebSocketClient):
    fake_socket_class = GeventFakeSocket
