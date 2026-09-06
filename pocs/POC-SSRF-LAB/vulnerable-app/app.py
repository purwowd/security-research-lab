"""
Intentionally vulnerable SSRF lab harness — DO NOT use in production.

Flaw: allowlist uses urlparse().netloc.startswith("cdn.lab"), which is bypassed by
userinfo form: http://cdn.lab@127.0.0.1:5000/internal/metadata
(requests follows the real host 127.0.0.1; netloc still starts with cdn.lab).
"""

from __future__ import annotations

from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

LAB_TOKEN = "LAB_META_TOKEN=srl-ssrf-lab-9f3a"
ALLOWED_PREFIX = "cdn.lab"


def _allowlisted(url: str) -> bool:
    """Broken allowlist — treats userinfo@host as if host were the userinfo prefix."""
    try:
        netloc = urlparse(url).netloc
    except Exception:
        return False
    if not netloc:
        return False
    # Vulnerable check (do not copy to production)
    return netloc.startswith(ALLOWED_PREFIX)


@app.get("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "lab": "POC-SSRF-LAB",
            "endpoints": {
                "/fetch?url=": "SSRF fetch (broken allowlist: host must start with cdn.lab)",
                "/internal/metadata": "Internal-only metadata (token)",
                "/health": "health",
            },
        }
    )


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/internal/metadata")
def metadata():
    """Simulated cloud/instance metadata — should not be reachable via /fetch."""
    return jsonify(
        {
            "role": "lab-metadata",
            "token": LAB_TOKEN,
            "note": "dummy lab secret — not a real cloud credential",
        }
    )


@app.get("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "missing url"}), 400
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "only http/https"}), 400
    if not _allowlisted(url):
        return jsonify({"error": "url not in allowlist", "hint": f"netloc must start with {ALLOWED_PREFIX}"}), 403

    try:
        # SSRF: server-side request to attacker-controlled URL
        resp = requests.get(url, timeout=5, allow_redirects=False)
        body = resp.text[:4000]
        return jsonify(
            {
                "ok": True,
                "status_code": resp.status_code,
                "body": body,
            }
        )
    except requests.RequestException as exc:
        return jsonify({"error": "upstream failed", "detail": str(exc)}), 502


if __name__ == "__main__":
    # 0.0.0.0 so Docker port publish works; metadata still "internal" via allowlist intent
    app.run(host="0.0.0.0", port=5055, debug=False)
