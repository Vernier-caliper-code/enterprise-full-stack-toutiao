from __future__ import annotations

import argparse
import http.client
import mimetypes
import os
import socketserver
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SpaProxyHandler(SimpleHTTPRequestHandler):
    api_url: str

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy()
            return
        parsed = urllib.parse.urlparse(self.path)
        candidate = Path(self.directory) / parsed.path.lstrip("/")
        if (
            parsed.path != "/"
            and not candidate.exists()
            and "." not in Path(parsed.path).name
        ):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        self._proxy()

    def do_PUT(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        target = urllib.parse.urlparse(self.api_url)
        body_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(body_length) if body_length else None
        connection = http.client.HTTPConnection(
            target.hostname, target.port, timeout=10
        )
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection"}
        }
        connection.request(self.command, self.path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        self.send_response(response.status, response.reason)
        for key, value in response.getheaders():
            if key.lower() not in {"transfer-encoding", "connection", "content-length"}:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        connection.close()

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    SpaProxyHandler.api_url = args.api_url
    handler = lambda *a, **kw: SpaProxyHandler(*a, directory=args.directory, **kw)
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
