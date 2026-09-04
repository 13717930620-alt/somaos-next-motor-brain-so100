#!/usr/bin/env python3
"""
SomaOS weight client (framework, dependency-free).

Fetches model weights at container startup from a maintainer-controlled
source. The weights themselves are NOT published in this repository and are
NOT included in the public image; the fetch source is supplied at runtime
via environment variables by the deployment operator.

Protocol: plain HTTPS GET of a single archive file, verified by SHA-256.

    python weight_client.py --url URL --sha256 HEX --dest DIR

Environment equivalents used by the entrypoint:
    SOMAOS_WEIGHT_URL      direct download URL of the weights archive
    SOMAOS_WEIGHT_SHA256   expected sha256 hex digest (optional but recommended)

Zero third-party dependencies (urllib only). Python 3.8+.
"""

import argparse
import hashlib
import os
import sys
import urllib.request
import zipfile

CHUNK = 1 << 20  # 1 MiB


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def fetch(url: str, dest: str, expected_sha256: str = "") -> str:
    os.makedirs(dest, exist_ok=True)
    tmp_path = os.path.join(dest, "weights.download")

    req = urllib.request.Request(url, headers={"User-Agent": "somaos-weight-client/1.0"})
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_path, "wb") as fh:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            fh.write(chunk)
            digest.update(chunk)
            total += len(chunk)
            print(f"  downloaded {total / (1 << 20):.1f} MiB", flush=True)

    got = digest.hexdigest()
    if expected_sha256 and got != expected_sha256.lower():
        os.remove(tmp_path)
        raise SystemExit(f"sha256 mismatch: expected {expected_sha256}, got {got}")

    if zipfile.is_zipfile(tmp_path):
        with zipfile.ZipFile(tmp_path) as zf:
            zf.extractall(dest)
        os.remove(tmp_path)

    print(f"weights ready at {dest} ({total / (1 << 20):.1f} MiB, sha256={got[:16]}...)")
    return got


def main() -> int:
    ap = argparse.ArgumentParser(description="SomaOS weight fetch client")
    ap.add_argument("--url", default=_env("SOMAOS_WEIGHT_URL"))
    ap.add_argument("--sha256", default=_env("SOMAOS_WEIGHT_SHA256"))
    ap.add_argument("--dest", default=_env("SOMAOS_WEIGHTS_DIR") or "/var/lib/somaos/weights")
    ap.add_argument("--check-only", action="store_true",
                    help="report configuration status without downloading")
    args = ap.parse_args()

    if args.check_only:
        if args.url:
            print(f"weight source configured: {args.url}")
        else:
            print("weight source not configured (SOMAOS_WEIGHT_URL empty)")
        return 0

    if not args.url:
        print("SOMAOS_WEIGHT_URL is not configured; nothing to fetch.")
        return 1

    fetch(args.url, args.dest, args.sha256)
    return 0


if __name__ == "__main__":
    sys.exit(main())
