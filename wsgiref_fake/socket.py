import os


class FileDescriptor:
    __slots__ = ["origin", "pointer"]

    def __init__(self, origin=None, pointer=None):
        self.origin = origin
        self.pointer = pointer

    def close(self):
        if self.pointer is not None:
            self.pointer.close()
            self.pointer = None


class FakeSocket:
    def __init__(self):
        self._closed = False

        self.fd_r = FileDescriptor()
        self.fd_w = FileDescriptor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self._closed:
            self.close()

    def connect(self, address):
        self.fd_r.origin, self.fd_w.origin = os.pipe()

    def makefile(self, mode="r", bufsize=-1):
        file_descriptor = {"rb": self.fd_r, "wb": self.fd_w}.get(mode)

        if file_descriptor is None:
            raise ValueError(f"Mode '{mode}' is not supported")

        if file_descriptor.pointer is None:
            file_descriptor.pointer = os.fdopen(file_descriptor.origin, mode, 0)

        return file_descriptor.pointer

    def close(self):
        self._closed = True

        self.fd_r.close()
        self.fd_w.close()

    def sendall(self, data, flags=0):
        os.write(self.fd_w.origin, data)

    def recv(self, buffersize, flags=None):
        return os.read(self.fd_r.origin, buffersize)

    def settimeout(self, value):
        pass


class FakeSocketPipe:
    def __init__(self, socket1, socket2):
        self._closed = False

        self.socket1 = socket1
        self.socket2 = socket2

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self._closed:
            self.close()

    def connect(self, address):
        self.socket1.connect(address)
        self.socket2.connect(address)

    def makefile(self, mode="r", bufsize=-1):
        if mode.startswith("r"):
            return self.socket1.makefile(mode=mode, bufsize=bufsize)

        return self.socket2.makefile(mode=mode, bufsize=bufsize)

    def close(self):
        if self._closed:
            raise ValueError("Socket is already closed")

        self._closed = True

        # NOTE: Do not close sockets cause the FakeSocketPipe is a wrapper

    def sendall(self, data, flags=0):
        return self.socket2.sendall(data, flags)

    def recv(self, buffersize, flags=None):
        return self.socket1.recv(buffersize, flags)

    def settimeout(self, value):
        pass
