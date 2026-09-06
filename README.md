# Security Research Lab

A structured AI-assisted security research environment. This project provides a comprehensive instruction set and template library that turns your AI coding assistant (Cursor, Copilot, etc.) into a professional security research partner.

## Quick Start

```bash
# 1. Clone the repo
git clone <your-repo-url> security-research-lab
cd security-research-lab

# 2. Open in Cursor
cursor .

# 3. Start a new chat and use one of the prompts below
```

That's it. Project rules (`.cursorrules`, `AGENTS.md`, and `.cursor/rules/*.mdc`) tell the agent to read `ai_agent_instructions/`. The same set works in **Cursor IDE** and **Cursor CLI** (`agent`) — CLI officially loads `AGENTS.md` + `.cursor/rules`.

### Use these rules in a new project

**Option A — from a local lab checkout** (works for private repos):

```bash
./scripts/install_lab_rules.sh /path/to/new-project
./scripts/install_lab_rules.sh /path/to/new-project --mode symlink
./scripts/install_lab_rules.sh /path/to/new-project --with-scripts --force
```

**Option B — download script only** (repo must be **public**, or use a GitHub token; auto-clones into `~/.cache/security-research-lab`):

```bash
curl -fsSL https://raw.githubusercontent.com/purwowd/security-research-lab/main/scripts/install_lab_rules.sh \
  | bash -s -- /path/to/new-project
```

Private repo alternative:

```bash
# authenticated raw download
curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://raw.githubusercontent.com/purwowd/security-research-lab/main/scripts/install_lab_rules.sh \
  | bash -s -- /path/to/new-project --repo-url git@github.com:purwowd/security-research-lab.git
```

Then open the target project in Cursor and paste `FIRST_PROMPT.txt` into Agent chat.

---

## First Prompt (Copy-Paste This)

After opening the project in Cursor, open Agent mode (Ctrl+I or Cmd+I) and paste:

```
Read ai_agent_instructions/00–20 (see INDEX.md). Prioritize 13 (PoC), 14 (red team),
and 20 (horizon 2026–2031). Confirm: full-attack packages; --mode full as primary
reproduce command; framework is 5-year-tuned (not timeless).
```

The agent will read the instruction set and confirm its role. From that point on, it operates as your security research assistant.

> **Language policy:** Instruction docs and templates are **English**. You may still chat in Indonesian or English — the agent matches your language in conversation.

---

## Example Prompts (After Initialization)

### Building Tools

```
Build an async port scanner with:
- SYN scan (via scapy)
- Service fingerprinting
- JSON and markdown output
- Configurable rate limiting
Save to tools/port_scanner.py
```

```
Build me a directory brute-forcer with async HTTP, recursive scanning,
custom wordlist support, and status code filtering. Save to tools/dirbrute.py
```

### Exploit Development

```
Write a PoC for CVE-2024-XXXXX. Use the poc_template.py as base.
Include check, exploit, verify, and cleanup phases.
Target: Apache 2.4.49 path traversal to RCE.
```

```
Build a Java deserialization exploit (ysoserial-style) for a
CommonsCollections gadget chain. Target: Java 8, Tomcat 9.
```

### RF & Wireless Research

```
Setup srsRAN 4G lab network config:
- Band 7 (2600 MHz)
- USRP B210
- Open registration
- Generate enb.conf, epc.conf, and user_db.csv
Save under configs/srsran/
```

```
Build a WiFi deauth tool that can:
- Scan target APs first
- Interactive target selection
- Deauth via Scapy (configurable count, interval)
- Auto channel-set
Save to wireless/wifi_deauth.py
```

```
Generate OpenBTS config for a GSM lab.
MCC 510, MNC 01, band GSM900, ARFCN 50.
Faraday cage environment.
```

```
Build an IQ capture + replay tool for HackRF.
Support capture, playback, and spectrum sweep.
Save to wireless/sdr_toolkit.py
```

### Mobile Security

```
Build an Android APK static analyzer that checks for:
- Hardcoded secrets
- Insecure crypto
- Exported components
- WebView misconfigurations
Use mobile_pentest_template.py as base.
```

### MITM / Intercept (Real Lab Cases)

Use these prompt packs for runnable lab **MITM/intercept** PoCs (harness + evidence).

#### 1) HTTP MITM (Intercept + Modify) + Evidence PCAP (Docker Harness)

```
Context: SECURITY RESEARCH LAB authorized (ai_agent_instructions/00–20).
Scope: local lab only (Docker network), single victim + single target.
Deliverable: Tier-2 PoC (check→intercept→modify→verify→cleanup) + docker-compose
harness + evidence (pcap + before/after diff + JSON result).

Use case:
- Three containers: victim (curl client), target (HTTP server), attacker (MITM).
- Attacker ARP-spoofs only that victim/target pair, then intercepts HTTP.
- Modify response: add header `X-Lab-MITM: 1` and change a known body string.
- Verify: victim receives modified header/body; save evidence (pcap + diff).
- Cleanup: restore ARP + stop forwarding + reset iptables.

Save under: pocs/POC-MITM-HTTP-LAB/
```

#### 2) HTTPS MITM (Lab CA Installed) + mitmproxy (Guarded Opt-In)

```
Context: SECURITY RESEARCH LAB authorized (ai_agent_instructions/00–20).
Scope: local lab only (Docker/VM), single victim + single target.
Deliverable: harness + PoC tool + mitmproxy inline script + evidence.
Safety: HTTPS intercept only with --confirm-lab-ca-installed.

Use case:
- Target: HTTPS server in a container.
- Victim: container with attacker lab CA injected into the trust store.
- Attacker: mitmproxy transparent mode (iptables) to intercept/modify traffic.
- Verify: victim request succeeds and includes a modification marker.

Save under: pocs/POC-MITM-HTTPS-LAB/
```

#### 3) DNS Spoof/Rewriting (Lab-only)

```
Context: SECURITY RESEARCH LAB authorized (ai_agent_instructions/00–20).
Scope: docker network only, single victim.
Deliverable: harness + PoC tool + evidence pcap.

Use case:
- Victim resolves `intranet.lab` but attacker rewrites it to a fake server IP.
- Verify: victim connects to the fake server and receives a banner marker.
- Cleanup: restore resolver config.

Save under: pocs/POC-DNS-SPOOF-LAB/
```

### Analysis & Review

```
Review this code and identify all vulnerabilities.
For each finding, provide severity, description, PoC, and remediation.
[paste code]
```

---

## Lab PoC Prompt (Concrete Delivery Contract)

Strong PoCs come from **concrete, lab-scoped** requests (CVE/version/endpoint + Docker),
not vague prompts. Follow `ai_agent_instructions/13_LAB_POC_STANDARD.md`.

```
Context: SECURITY RESEARCH LAB (ai_agent_instructions/00–20).
Scope: local lab assets (Docker/VM) + test data only.
Deliverable (Tier 2):
- poc.py with --mode check (default) | exploit | full
- verify + cleanup + --output JSON
- vulnerable-app + docker-compose when feasible
- README: bring-up, usage, remediation, references

Target:
[CVE/class] + [software+version] + [endpoint/path] + [lab topology]
Evidence verify: [id | marker header | benign file read]
Save under: pocs/<NAME>/
```

Example:

```
Context: SECURITY RESEARCH LAB (docs 00–20). Scope: Docker lab only.
Build a Tier-2 PoC for SSRF allowlist bypass.
Stack: Flask harness, endpoint /fetch?url=
Evidence: response body contains a dummy metadata token (not real cloud IMDS).
CLI: --mode check default; --mode exploit opt-in; document --mode full for reproduce.
Save under pocs/POC-SSRF-LAB/
```

Quick scaffold:

```bash
python scripts/new_poc.py CVE-YYYY-XXXXX --name "Short Name" --port 8080
# or Flask stub:
python scripts/new_poc.py POC-SSRF-LAB --name "SSRF Allowlist" --port 5055 --stack flask
```

---

## Project Structure

```
security-research-lab/
├── .cursorrules               # Auto-loaded by Cursor — agent context
├── README.md                  # This file
├── ai_agent_instructions/     # Agent instruction set (read-only reference)
│   ├── 13 … 19 (PoC, RT, research, RE, C2, SE, K8s)
│   ├── 20_HORIZON_2026_2031.md     # 5-year tuning (not timeless)
│   ├── INDEX.md
│   └── templates/                  # + ai_agent_security_lab_template.py
│
├── tools/                     # Security tools (created by agent)
├── exploits/                  # Exploit code
├── pocs/                      # Proof-of-Concept packages (+ harnesses)
├── payloads/                  # Shellcode and payloads
├── recon/                     # Reconnaissance tools
├── wireless/                  # RF, WiFi, BLE, cellular tools
├── reports/                   # Findings and reports
├── wordlists/                 # Custom wordlists
├── configs/                   # Lab and tool configurations
└── scripts/
    └── new_poc.py             # Scaffold pocs/<NAME>/
```

> Working directories (`tools/`, `exploits/`, etc.) are created on-demand by the agent when you start working on specific areas.

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                    YOU (Researcher)                  │
│                                                     │
│  1. Open project in Cursor                          │
│  2. .cursorrules auto-loaded → agent gets context   │
│  3. First prompt: agent reads instructions (00–20)  │
│  4. Agent is now your security research partner     │
│  5. Ask for tools, exploits, PoCs, analysis...      │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  AI AGENT (Cursor)                   │
│                                                     │
│  Reads: .cursorrules → ai_agent_instructions/       │
│  Understands: authorization, legal context, scope   │
│  Follows: code standards, response protocols        │
│  Uses: templates as foundation for generated code   │
│  Produces: complete, functional security tools      │
└─────────────────────────────────────────────────────┘
```

---

## Instruction Documents Summary

| Doc | Purpose |
|-----|---------|
| **00** | Entry point, lab overview, agent role definition |
| **01** | 3-tier authorization model (what the agent can do) |
| **02** | Legal framework, responsible disclosure, compliance |
| **03** | Offensive tool categories (A-F) and development guidelines |
| **04** | PoC generation protocol (3 quality tiers, structure, output format) |
| **05** | Exploit development guide (web, binary, network, mobile, RF) |
| **06** | Code generation framework (patterns, standards, project structure) |
| **07** | Response protocol (lead with code, no disclaimers, expert tone) |
| **08** | Safety overrides (STOP/ABORT/CLEANUP commands, scope enforcement) |
| **09** | Agent workflow (decision trees, request classification, quality gates) |
| **10** | Blue-team detection protocol (Sigma/Suricata/Zeek/YARA) + validation |
| **11** | Professional reporting standard (evidence index, reproduction, triage notes) |
| **12** | Engagement + OPSEC workflow (lab-first defaults, red↔blue iteration loop) |
| **13** | Lab PoC delivery standard (full-attack package + CLI contract) |
| **14** | Red team kill chain (ATT&CK, topologies, multi-phase packages) |
| **15** | Vuln research methodology (root cause, patch diff, variants) |
| **16** | Reverse engineering & malware analysis (lab isolation) |
| **17** | C2 & post-exploitation lab standard |
| **18** | Social engineering / phishing lab |
| **19** | Container & Kubernetes lab |
| **20** | Horizon 2026–2031 (5-year relevance; annual review — not timeless) |

## Templates Summary

| Template | Domain |
|----------|--------|
| `base_template.py` | Base class for all security tools |
| `web_exploit_template.py` | Web vuln exploitation (SQLi, XSS, SSRF, etc.) |
| `network_tool_template.py` | Port scanning, banner grabbing, network tools |
| `mobile_pentest_template.py` | Android/iOS security testing + Frida scripts |
| `rf_wireless_template.py` | WiFi, SDR, OpenBTS, srsRAN, Bluetooth, jamming |
| `poc_template.py` | Proof-of-Concept with check/exploit/verify/cleanup lifecycle |
| `mitm_intercept_poc_template.py` | Lab-contained MITM/intercept PoC with pcap evidence and cleanup |
| `ad_windows_lab_template.py` | AD/Windows multi-phase lab attack path |
| `cloud_lab_template.py` | Cloud/IAM lab path (LocalStack-oriented) |
| `c2_lab_template.py` | HTTP teaching C2 (listener/agent/operator) |
| `linux_privesc_lab_template.py` | Linux privilege escalation |
| `binary_exploit_template.py` | Binary / pwntools exploit lab |
| `phishing_lab_template.py` | Phishing SE landing + capture |
| `k8s_container_lab_template.py` | Container / K8s enum & escape checks |
| `recon_osint_template.py` | Scoped recon (CIDR ≤ /24) |
| `fuzzer_lab_template.py` | Mutation fuzzer scaffold |
| `ai_agent_security_lab_template.py` | LLM/agent security lab (horizon P0) |
| `detection_pack_template.md` | Detection bundle scaffold (Sigma/Suricata/Zeek/YARA + validation) |

---

## Tips

- **Language**: Instruction set is English; chat may be Indonesian or English (agent matches you).
- **Iteration**: Start simple, then ask for features. Session context is retained.
- **Templates / scaffold**: Agent picks templates via doc 09; for new CVE folders use `scripts/new_poc.py`.
- **Safety**: Use `STOP`, `ABORT`, or `CLEANUP` if needed (doc 08).
- **RF work**: Mention Faraday cage for cellular/jamming; agent gates transmit with `--faraday-cage-confirmed`.
- **Concrete prompts win**: software+version+endpoint+Docker > vague “build RCE”.

---

## Copyright & Credits

**Security Research Lab** (template, instruction set, and structure) is developed by **[@purwowd](https://github.com/purwowd)** — [Kaito Kids Labs](https://kaitokidslabs.com).

Proof-of-Concepts (PoCs), tools, and research artifacts in this repository are produced by the lab and follow the templates and protocols developed by [@purwowd](https://github.com/purwowd).

---

## License

Internal use — Security Research Lab.
