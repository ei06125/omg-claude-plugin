"""A local stand-in for the GitHub pull request endpoints, served over real HTTP.

It cannot prove how github.com behaves; it lets tests drive the real HTTP client code.
"""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOT_PERMITTED = "GitHub Actions is not permitted to create or approve pull requests."


class FakeGitHub:
    def __init__(self, repo="octo/omg"):
        self.repo = repo
        self.prs = []
        self.requests = []
        self.pr_creation_allowed = True
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def open_prs(self):
        return [pr for pr in self.prs if pr["state"] == "open"]

    def seed(self, head, base="main", title="seeded", state="open", head_repo=None):
        pr = {
            "number": len(self.prs) + 1,
            "title": title,
            "head": head,
            "head_repo": head_repo or self.repo,
            "base": base,
            "body": "",
            "state": state,
            "comments": [],
        }
        self.prs.append(pr)
        return pr

    def posts_to_pulls(self):
        return [
            r
            for r in self.requests
            if r["method"] == "POST" and r["path"].endswith("/pulls")
        ]

    def _view(self, pr):
        return {
            "number": pr["number"],
            "state": pr["state"],
            "title": pr["title"],
            "html_url": f"{self.url}/{self.repo}/pull/{pr['number']}",
            "head": {"ref": pr["head"], "repo": {"full_name": pr["head_repo"]}},
            "base": {"ref": pr["base"]},
        }

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, payload):
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length) or b"{}")

            def route(self, method):
                path = self.path.split("?")[0]
                fake.requests.append(
                    {
                        "method": method,
                        "path": path,
                        "auth": self.headers.get("Authorization"),
                    }
                )
                prefix = f"/repos/{fake.repo}"
                if not path.startswith(prefix):
                    return self.reply(404, {"message": "Not Found"})
                rest = path[len(prefix) :]
                if method == "GET" and rest == "/pulls":
                    return self.reply(200, [fake._view(pr) for pr in fake.open_prs()])
                if method == "POST" and rest == "/pulls":
                    return self.create(self.body())
                pull = re.fullmatch(r"/pulls/(\d+)", rest)
                if method == "PATCH" and pull:
                    target = fake.prs[int(pull.group(1)) - 1]
                    target["state"] = self.body().get("state", target["state"])
                    return self.reply(200, fake._view(target))
                comment = re.fullmatch(r"/issues/(\d+)/comments", rest)
                if method == "POST" and comment:
                    fake.prs[int(comment.group(1)) - 1]["comments"].append(
                        self.body().get("body", "")
                    )
                    return self.reply(201, {})
                return self.reply(404, {"message": "Not Found"})

            def create(self, payload):
                if not fake.pr_creation_allowed:
                    return self.reply(403, {"message": NOT_PERMITTED})
                if any(pr["head"] == payload["head"] for pr in fake.open_prs()):
                    return self.reply(
                        422,
                        {
                            "message": "Validation Failed",
                            "errors": [{"message": "A pull request already exists."}],
                        },
                    )
                pr = fake.seed(payload["head"], payload["base"], payload["title"])
                pr["body"] = payload.get("body", "")
                return self.reply(201, fake._view(pr))

            def do_GET(self):
                self.route("GET")

            def do_POST(self):
                self.route("POST")

            def do_PATCH(self):
                self.route("PATCH")

        return Handler
