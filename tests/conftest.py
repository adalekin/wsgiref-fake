import pytest

from wsgiref_fake.http.client import HTTPClient
from wsgiref_fake.server import make_server


def hello_world_app(_environ, start_response):
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)

    return ["Hello World"]


@pytest.fixture
def wsgi_server():
    return make_server(app=hello_world_app)


@pytest.fixture
def http_client(wsgi_server):
    return HTTPClient(server=wsgi_server)
