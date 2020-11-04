def test_basic_get(http_client):
    response = http_client.request(method="GET", path="/")

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/plain"


def test_basic_post(http_client):
    response = http_client.request(method="POST", path="/", json={"test": 1})

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/plain"


def test_basic_multiple_requests(http_client):
    response = http_client.request(method="GET", path="/")

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/plain"

    response = http_client.request(method="GET", path="/")

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/plain"
