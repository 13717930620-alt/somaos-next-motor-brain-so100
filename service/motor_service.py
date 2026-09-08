"""SomaOS Brain Next — container service shell (optional).

The production motor brain ships as a closed-source Node.js runtime
(``node loader.js``, see the GitHub Release). This Python shell is an
optional thin proxy: when the Node runtime is unreachable from the
container's network namespace, it proxies HTTP requests to the runtime's
``/health`` and ``/goal`` endpoints. No algorithm logic lives here.

If the Node runtime is not running, the shell exits with a clear message.
"""

import argparse
import json
import os
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NODE_HOST = os.environ.get("SOMAOS_NODE_HOST", "127.0.0.1")
NODE_PORT = int(os.environ.get("SOMAOS_NODE_PORT", "3002"))


class Handler(BaseHTTPRequestHandler):
    def _proxy(self, method: str) -> None:
        try:
            conn = HTTPConnection(NODE_HOST, NODE_PORT, timeout=5)
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None
            conn.request(method, self.path, body=body,
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            data = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            conn.close()
        except Exception as exc:
            self._send(503, {"error": f"node runtime unreachable: {exc}"})

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        self._proxy("GET")

    def do_POST(self):  # noqa: N802
        self._proxy("POST")

    def log_message(self, fmt, *args):  # keep container logs quiet
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()

    # Verify the Node runtime is reachable before starting the proxy
    try:
        conn = HTTPConnection(NODE_HOST, NODE_PORT, timeout=3)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        if resp.status != 200:
            raise ConnectionError(f"HTTP {resp.status}")
        conn.close()
    except Exception:
        print(f"[motor_service] Node runtime not reachable at "
              f"{NODE_HOST}:{NODE_PORT}. Start it first: node loader.js")
        return

    print(f"[motor_service] proxying to {NODE_HOST}:{NODE_PORT}; "
          f"listening on {args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
