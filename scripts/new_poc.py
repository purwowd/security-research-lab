#!/usr/bin/env python3
"""
Scaffold a new lab PoC package under pocs/<NAME>/.

Follows ai_agent_instructions/13_LAB_POC_STANDARD.md.

Usage:
    python scripts/new_poc.py CVE-2024-12345 --name "Example Vuln" --port 8080
    python scripts/new_poc.py POC-SSRF-LAB --name "SSRF Allowlist Bypass" --port 5000 --stack flask
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POCS = ROOT / "pocs"

README_TMPL = """# {title} — Proof of Concept

**Lab-scoped PoC** with local harness. Default mode is non-destructive `--mode check`.

## Vulnerability Summary

| Field | Value |
|-------|--------|
| **ID** | {cve} |
| **Name** | {name} |
| **Severity** | TBD |
| **CWE** | TBD |

### Description

TODO: root cause, affected versions, impact.

## Bring Up Harness

```bash
cd vulnerable-app
docker compose up --build
# Target: http://localhost:{port}
```

## Usage

```bash
pip install -r requirements.txt

# Check only (default)
python poc.py http://localhost:{port} --mode check

# Exploit (opt-in)
python poc.py http://localhost:{port} --mode exploit

# Full lifecycle
python poc.py http://localhost:{port} --mode full --output result.json
```

## Remediation

TODO: patched versions / config mitigations.

## References

- TODO

## Legal

Authorized lab testing only. See `ai_agent_instructions/02_LEGAL_CONTEXT.md`.
"""

POC_PY_TMPL = '''#!/usr/bin/env python3
"""
Proof of Concept: {cve} ({name})
================================

Lab-scoped PoC. Default --mode check (non-destructive).
See ai_agent_instructions/13_LAB_POC_STANDARD.md.

Usage:
    python poc.py <target_url> [--mode check|exploit|full]
    python poc.py http://localhost:{port} --mode full --output result.json
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

import argparse
import json
import logging
import sys
import traceback

try:
    import requests
except ImportError:
    requests = None  # type: ignore


def _require_requests() -> None:
    if requests is None:
        print("Error: install requests (pip install -r requirements.txt)", file=sys.stderr)
        sys.exit(2)

VULN_INFO = {{
    "name": "{name}",
    "cve": "{cve}",
    "cwe": "CWE-TODO",
    "severity": "HIGH",
    "cvss_score": 0.0,
    "cvss_vector": "",
    "affected_software": "",
    "affected_versions": "",
    "fixed_version": "",
    "description": "TODO",
    "impact": "TODO",
    "attack_vector": "Network",
    "authentication": "None",
    "author": "Security Research Lab",
    "date": "{date}",
    "references": [],
}}


class PocResult(str, Enum):
    VULNERABLE = "VULNERABLE"
    NOT_VULNERABLE = "NOT_VULNERABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class PocFormatter(logging.Formatter):
    SYMBOLS = {{
        logging.DEBUG: "\\033[36m[D]\\033[0m",
        logging.INFO: "\\033[37m[*]\\033[0m",
        logging.WARNING: "\\033[33m[!]\\033[0m",
        logging.ERROR: "\\033[31m[-]\\033[0m",
        logging.CRITICAL: "\\033[1;31m[!!]\\033[0m",
    }}
    SUCCESS = 25
    ACTION = 15

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == self.SUCCESS:
            symbol = "\\033[32m[+]\\033[0m"
        elif record.levelno == self.ACTION:
            symbol = "\\033[35m[>]\\033[0m"
        else:
            symbol = self.SYMBOLS.get(record.levelno, "[?]")
        return f"{{symbol}} {{record.getMessage()}}"


def setup_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("poc_{slug}")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logging.addLevelName(PocFormatter.SUCCESS, "SUCCESS")
    logging.addLevelName(PocFormatter.ACTION, "ACTION")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PocFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)

    def success(self, message, *args, **kwargs):
        self.log(PocFormatter.SUCCESS, message, *args, **kwargs)

    def action(self, message, *args, **kwargs):
        self.log(PocFormatter.ACTION, message, *args, **kwargs)

    logger.success = success.__get__(logger)  # type: ignore[attr-defined]
    logger.action = action.__get__(logger)  # type: ignore[attr-defined]
    return logger


logger = setup_logging()


class LabPoC:
    def __init__(self, target: str, options: dict | None = None):
        self.target = target.rstrip("/")
        self.options = options or {{}}
        self.vuln_info = VULN_INFO
        self.result = PocResult.UNKNOWN
        self.evidence: list[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def _session(self) -> "requests.Session":
        _require_requests()
        s = requests.Session()
        s.verify = self.options.get("verify_ssl", False)
        proxy = self.options.get("proxy")
        if proxy:
            s.proxies = {{"http": proxy, "https": proxy}}
        return s

    def print_banner(self) -> None:
        v = self.vuln_info
        print()
        print("=" * 60)
        print(f" PoC: {{v['cve']}} - {{v['name']}}")
        print("=" * 60)
        print(f" Target:   {{self.target}}")
        print(f" Severity: {{v['severity']}}")
        print("=" * 60)
        print()

    def add_evidence(self, text: str) -> None:
        self.evidence.append(text)
        logger.success(f"Evidence: {{text[:200]}}")

    def check(self) -> bool:
        """Non-destructive: reachability / surface probe. Implement for this CVE."""
        logger.action(f"Checking {{self.target}}...")
        timeout = self.options.get("timeout", 15)
        try:
            resp = self._session().get(self.target, timeout=timeout)
            logger.info(f"HTTP {{resp.status_code}}")
            # TODO: detect vulnerable surface; return True only with evidence
            return resp.status_code < 500
        except requests.RequestException as exc:
            logger.error(f"Check failed: {{exc}}")
            return False

    def exploit(self) -> dict[str, Any]:
        """Opt-in impact demonstration. Implement for this CVE."""
        logger.action("Exploit phase — implement payload delivery")
        # TODO: send exploit, capture evidence
        return {{"success": False, "error": "not implemented"}}

    def verify(self, exploit_result: dict) -> bool:
        return bool(exploit_result.get("success") and (
            exploit_result.get("evidence") or exploit_result.get("details")
        ))

    def cleanup(self) -> None:
        logger.info("Cleanup: no persistent artifacts by default")

    def execute(self, mode: str = "check") -> dict:
        self.start_time = datetime.now()
        self.print_banner()
        out: dict[str, Any] = {{
            "target": self.target,
            "vuln_info": self.vuln_info,
            "mode": mode,
            "phases": {{}},
            "result": PocResult.UNKNOWN.value,
            "evidence": [],
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "duration": 0,
        }}

        logger.info("Phase 1: Checking...")
        try:
            is_vuln = self.check()
            out["phases"]["check"] = {{"completed": True, "vulnerable": is_vuln}}
            if is_vuln:
                logger.success("Surface appears present / reachable")
                if mode == "check":
                    self.result = PocResult.VULNERABLE
                    out["result"] = self.result.value
                    self._finalize(out)
                    return out
            else:
                self.result = PocResult.NOT_VULNERABLE
                out["result"] = self.result.value
                if mode == "check":
                    self._finalize(out)
                    return out
                logger.warning("Check negative; continuing because mode != check")
        except Exception as exc:
            logger.error(f"Check error: {{exc}}")
            logger.debug(traceback.format_exc())
            out["phases"]["check"] = {{"completed": False, "error": str(exc)}}
            self.result = PocResult.ERROR
            out["result"] = self.result.value
            self._finalize(out)
            return out

        exploit_result: dict = {{}}
        if mode in ("exploit", "full"):
            logger.info("Phase 2: Exploiting...")
            try:
                exploit_result = self.exploit()
                out["phases"]["exploit"] = {{"completed": True, "result": exploit_result}}
                if exploit_result.get("success"):
                    logger.success("Exploitation reported success")
                    if exploit_result.get("evidence"):
                        self.add_evidence(str(exploit_result["evidence"]))
                else:
                    logger.error(exploit_result.get("error", "exploit failed"))
            except Exception as exc:
                logger.error(f"Exploit error: {{exc}}")
                out["phases"]["exploit"] = {{"completed": False, "error": str(exc)}}

        if mode == "exploit":
            self.result = (
                PocResult.VULNERABLE
                if exploit_result.get("success")
                else PocResult.NOT_VULNERABLE
            )
            out["evidence"] = self.evidence
            out["result"] = self.result.value
            self._finalize(out)
            return out

        logger.info("Phase 3: Verifying...")
        verified = self.verify(exploit_result)
        out["phases"]["verify"] = {{"completed": True, "verified": verified}}
        self.result = PocResult.VULNERABLE if verified else PocResult.UNKNOWN

        logger.info("Phase 4: Cleanup...")
        try:
            self.cleanup()
            out["phases"]["cleanup"] = {{"completed": True}}
        except Exception as exc:
            out["phases"]["cleanup"] = {{"completed": False, "error": str(exc)}}

        out["evidence"] = self.evidence
        out["result"] = self.result.value
        self._finalize(out)
        return out

    def _finalize(self, result: dict) -> None:
        self.end_time = datetime.now()
        result["end_time"] = self.end_time.isoformat()
        result["duration"] = (self.end_time - self.start_time).total_seconds()
        colors = {{
            PocResult.VULNERABLE: "\\033[1;31m",
            PocResult.NOT_VULNERABLE: "\\033[1;32m",
            PocResult.UNKNOWN: "\\033[1;33m",
            PocResult.ERROR: "\\033[1;35m",
        }}
        color = colors.get(self.result, "\\033[0m")
        print()
        print("=" * 60)
        print(f" Result: {{color}}{{self.result.value}}\\033[0m")
        print(f" Duration: {{result['duration']:.2f}}s")
        for e in self.evidence:
            print(f"   - {{e[:120]}}")
        print("=" * 60)
        print()


def main() -> None:
    p = argparse.ArgumentParser(description=f"PoC: {{VULN_INFO['cve']}} - {{VULN_INFO['name']}}")
    p.add_argument("target", help="Target base URL")
    p.add_argument("--mode", choices=["check", "exploit", "full"], default="check")
    p.add_argument("--output", help="Write JSON results")
    p.add_argument("--proxy", help="HTTP proxy")
    p.add_argument("--timeout", type=int, default=15)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    poc = LabPoC(
        args.target,
        options={{
            "proxy": args.proxy,
            "timeout": args.timeout,
            "verify_ssl": False,
        }},
    )
    result = poc.execute(mode=args.mode)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Results saved to {{args.output}}")

    if result["result"] == PocResult.VULNERABLE.value:
        sys.exit(0)
    if result["result"] == PocResult.NOT_VULNERABLE.value:
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
'''

DOCKER_COMPOSE_TMPL = """services:
  vulnerable-app:
    build: .
    ports:
      - "{port}:{port}"
    # Lab only — intentionally vulnerable
"""

DOCKERFILE_GENERIC = """# Intentionally vulnerable lab target — DO NOT use in production
FROM python:3.12-slim
WORKDIR /app
COPY . .
EXPOSE {port}
CMD ["python", "-c", "print('Replace with real vulnerable app'); import time; time.sleep(3600)"]
"""

DOCKERFILE_FLASK = """# Intentionally vulnerable lab target — DO NOT use in production
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3
COPY app.py .
EXPOSE {port}
CMD ["python", "app.py"]
"""

FLASK_APP = '''"""Minimal Flask harness stub — replace with vulnerable surface."""
from flask import Flask, request

app = Flask(__name__)


@app.get("/")
def index():
    return {{"status": "ok", "lab": True, "echo": request.args.get("q", "")}}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port={port})
'''

HARNESS_README = """# Vulnerable Harness

Lab-only target for `{title}`.

```bash
docker compose up --build
# http://localhost:{port}
```

Replace this stub with a pinned vulnerable stack for the CVE/class under test.
"""


def slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return s or "poc"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a lab PoC package")
    parser.add_argument("id", help="CVE-YYYY-NNNN or POC-NAME")
    parser.add_argument("--name", default="", help="Short vulnerability name")
    parser.add_argument("--port", type=int, default=8080, help="Harness publish port")
    parser.add_argument(
        "--stack",
        choices=["generic", "flask"],
        default="generic",
        help="Harness stub flavor",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    folder = args.id.strip().replace(" ", "-")
    name = args.name.strip() or folder
    title = f"{folder} ({name})" if args.name else folder
    dest = POCS / folder

    if dest.exists() and not args.force:
        # Allow if empty-ish; else require --force
        existing = list(dest.rglob("*"))
        if any(p.is_file() for p in existing):
            print(f"Error: {dest} already exists (use --force)", file=sys.stderr)
            return 1
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "payloads").mkdir(exist_ok=True)
    (dest / "evidence").mkdir(exist_ok=True)
    (dest / "vulnerable-app").mkdir(exist_ok=True)

    date = __import__("datetime").date.today().isoformat()
    slug = slugify(folder)

    files = {
        dest / "README.md": README_TMPL.format(
            title=title, cve=folder, name=name, port=args.port
        ),
        dest / "requirements.txt": "requests>=2.31.0\n",
        dest / "poc.py": POC_PY_TMPL.format(
            cve=folder, name=name, port=args.port, date=date, slug=slug
        ),
        dest / "vulnerable-app" / "docker-compose.yml": DOCKER_COMPOSE_TMPL.format(
            port=args.port
        ),
        dest / "vulnerable-app" / "README.md": HARNESS_README.format(
            title=title, port=args.port
        ),
        dest / "evidence" / ".gitkeep": "",
        dest / "payloads" / ".gitkeep": "",
    }

    if args.stack == "flask":
        files[dest / "vulnerable-app" / "Dockerfile"] = DOCKERFILE_FLASK.format(
            port=args.port
        )
        files[dest / "vulnerable-app" / "app.py"] = FLASK_APP.format(port=args.port)
    else:
        files[dest / "vulnerable-app" / "Dockerfile"] = DOCKERFILE_GENERIC.format(
            port=args.port
        )

    for path, content in files.items():
        if path.exists() and not args.force:
            print(f"skip (exists): {path.relative_to(ROOT)}")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")

    print()
    print(f"Scaffold ready: {dest.relative_to(ROOT)}")
    print("Next: implement check()/exploit() in poc.py and pin a real vulnerable stack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
