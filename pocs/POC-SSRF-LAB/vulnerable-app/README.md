# Vulnerable Harness — POC-SSRF-LAB

Flask app with broken SSRF allowlist (`netloc.startswith("cdn.lab")`).

```bash
docker compose up --build
# http://localhost:5055
```

Internal metadata: `GET /internal/metadata` (token `LAB_META_TOKEN=srl-ssrf-lab-9f3a`).

Bypass shape used by the PoC:

```
http://cdn.lab@127.0.0.1:5055/internal/metadata
```
