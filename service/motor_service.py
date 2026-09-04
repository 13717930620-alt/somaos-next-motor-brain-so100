"""SomaOS Brain Next — closed runtime service shell.

The production motor core ships inside the container as compiled binary
extensions (``core/*.so``). This shell is the only public part of the
service layer: it loads the compiled core and exposes a local HTTP control
endpoint for RCAN-style motor command ingestion. No algorithm logic lives
here.

If the compiled core is absent (e.g. a source-only/demo build), the shell
exits with a clear message instead of emulating the core.
"""

import argparse
import importlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.normpath(os.path.join(HERE, "..", "core"))


def load_core():
    """Import the compiled motor core, or return None if absent."""
    if not os.path.isdir(CORE_DIR):
        return None
    binaries = [f for f in os.listdir(CORE_DIR) if f.endswith(".so")]
    if not binaries:
        return None
    if CORE_DIR not in sys.path:
        sys.path.insert(0, CORE_DIR)
    try:
        return importlib.import_module("motor_core")
    except ImportError as exc:
        print(f"[motor_service] core present but import failed: {exc}")
        return None


CORE = load_core()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send(200, {
                "service": "somaos-motor",
                "core_loaded": CORE is not None,
                "mode": "closed-core" if CORE else "shell-only",
            })
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if CORE is None:
            self._send(503, {"error": "motor core not loaded"})
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            request = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        # The compiled core owns all motor processing; the shell never
        # inspects or transforms the command semantics.
        result = CORE.handle(request)
        self._send(200, result)

    def log_message(self, fmt, *args):  # keep container logs quiet
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()

    if CORE is None:
        print("[motor_service] compiled core not found in ./core — "
              "this build cannot start the closed runtime. "
              "Use --mode demo (entrypoint) for the runnable demo loop.")
        sys.exit(1)

    print(f"[motor_service] core loaded; serving on {args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
