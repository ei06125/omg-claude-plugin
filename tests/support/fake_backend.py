"""A local stand-in for an OpenAI-compatible model endpoint (`/v1/models`), served over real HTTP.

It cannot prove how Ollama, llama-server or exo behave; it lets tests drive the real probing code.
"""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def closed_url(path="/v1/models"):
    """The URL of a port nothing listens on: a backend that is not running."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}{path}"


class FakeBackend:
    def __init__(self, models):
        self.models = list(models)
        self.requests = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def probe_url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}/v1/models"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def _handler(self):
        backend = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                backend.requests.append(self.path)
                body = json.dumps(
                    {"object": "list", "data": [{"id": m} for m in backend.models]}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        return Handler
