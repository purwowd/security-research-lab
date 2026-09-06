# POC-SSRF-LAB (SSRF Allowlist Bypass) — Proof of Concept

**Lab-scoped SSRF** against a broken `netloc.startswith("cdn.lab")` allowlist.
Default mode is non-destructive `--mode check`.

## Vulnerability Summary

| Field | Value |
|-------|--------|
| **ID** | POC-SSRF-LAB |
| **Name** | SSRF Allowlist Bypass |
| **CWE** | CWE-918 |
| **Severity** | HIGH (CVSS 8.6) |

### Root Cause

Allowlist checks `urlparse(url).netloc.startswith("cdn.lab")`.  
Payload `http://cdn.lab@127.0.0.1:5055/internal/metadata` passes the check, while `requests` contacts `127.0.0.1` and returns the internal metadata token.

### Evidence Marker

`LAB_META_TOKEN=srl-ssrf-lab-9f3a`

## Bring Up Harness

```bash
cd vulnerable-app
docker compose up --build
# Target: http://localhost:5055
```

Or without Docker:

```bash
cd vulnerable-app
pip install flask requests
python app.py
```

## Usage

```bash
pip install -r requirements.txt

python poc.py http://localhost:5055 --mode check
python poc.py http://localhost:5055 --mode exploit
python poc.py http://localhost:5055 --mode full --output result.json --report report.md
```

## Remediation

- Allowlist using `urlparse(url).hostname` (never raw `netloc` with userinfo).
- Deny link-local / loopback / private ranges after DNS resolution.
- Prefer allowlist of exact hostnames, not prefix/`startswith` checks.

## References

- https://cwe.mitre.org/data/definitions/918.html
- https://owasp.org/www-community/attacks/Server_Side_Request_Forgery

## Legal

Authorized lab testing only. See `ai_agent_instructions/02_LEGAL_CONTEXT.md`.
