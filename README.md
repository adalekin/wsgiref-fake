# wsgiref-fake

In-process **WSGI** test doubles: fake sockets and a minimal server harness so you can exercise HTTP (and optionally WebSocket) applications **without binding a real port** or talking over the network.

Useful for fast, deterministic tests against code built on `wsgiref` and similar stacks.

## Requirements

- Python 3.10 or newer
- Runtime dependency: [`six`](https://pypi.org/project/six/) (Python 2/3 compatibility helpers used in this library)

## Installation

```bash
pip install wsgiref-fake
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv add wsgiref-fake
```

### Optional extras

| Extra   | Purpose                                      |
| ------- | -------------------------------------------- |
| `gevent` | Gevent-based WebSocket client helpers       |
| `ws4py`  | Integration helpers around `ws4py`        |

```bash
pip install "wsgiref-fake[gevent]"
pip install "wsgiref-fake[ws4py]"
```

## Quick start (HTTP)

Wire your WSGI app to an in-process server, then drive it with `HTTPClient`:

```python
from wsgiref_fake.http.client import HTTPClient
from wsgiref_fake.server import make_server


def app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello World"]


server = make_server(app=app)
client = HTTPClient(server=server)

response = client.request(method="GET", path="/")
assert response.status == 200
body = response.read()
```

`HTTPClient.request` accepts `method`, `path`, optional `json` (sets `Content-Type` and body), and optional `headers`.

## Why this exists

- **No listening socket** — tests stay hermetic and parallel-friendly.
- **Same WSGI surface** as production-oriented `wsgiref` servers, without TCP overhead.
- **WebSocket-related helpers** are available when you install the optional dependency groups above.

## Development

Clone the repository, then install the project with dev dependencies:

```bash
uv sync
```

Run the test suite:

```bash
uv run pytest
```

Lint and format tests (library code is excluded from Ruff in this repo’s config):

```bash
uv run ruff check tests
uv run ruff format tests
```

## Contributing

Issues and pull requests are welcome. Please run tests before opening a PR.

- [Issue tracker](https://github.com/adalekin/wsgiref-fake/issues)
- [Source code](https://github.com/adalekin/wsgiref-fake)

## License

This project is licensed under the [MIT License](LICENSE).
