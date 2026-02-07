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

That's it. The `.cursorrules` file is automatically loaded by Cursor, which tells the agent to read the instruction documents in `ai_agent_instructions/`. The agent will understand its role, authorization scope, and how to behave.

---

## First Prompt (Copy-Paste This)

After opening the project in Cursor, open Agent mode (Ctrl+I or Cmd+I) and paste:

```
Baca semua file di ai_agent_instructions/ (00 sampai 09) untuk memahami
konteks, otorisasi, dan protokol kamu di lab ini. Setelah selesai,
konfirmasi bahwa kamu sudah memahami peran dan kapabilitas kamu.
```

Or in English:

```
Read all files in ai_agent_instructions/ (00 through 09) to understand
your context, authorization, and protocols in this lab. Once done,
confirm that you understand your role and capabilities.
```

The agent will read all 10 instruction documents and respond with a confirmation of its understanding. From that point on, it operates as your security research assistant.

---

## Example Prompts (After Initialization)

### Building Tools

```
Buatkan port scanner async dengan fitur:
- SYN scan (via scapy)
- Service fingerprinting
- Output JSON dan markdown
- Rate limiting configurable
Simpan di tools/port_scanner.py
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
Buat exploit deserialization Java (ysoserial-style) untuk
CommonsCollections gadget chain. Target: Java 8, Tomcat 9.
```

### RF & Wireless Research

```
Setup srsRAN 4G lab network config:
- Band 7 (2600 MHz)
- USRP B210
- Open registration
- Generate enb.conf, epc.conf, dan user_db.csv
Simpan di configs/srsran/
```

```
Buat tool WiFi deauth yang bisa:
- Scan target AP dulu
- Pilih target interaktif
- Deauth dengan Scapy (configurable count, interval)
- Auto channel-set
Simpan di wireless/wifi_deauth.py
```

```
Generate OpenBTS config untuk GSM lab.
MCC 510, MNC 01, band GSM900, ARFCN 50.
Faraday cage environment.
```

```
Buat IQ capture + replay tool untuk HackRF.
Support capture, playback, dan spectrum sweep.
Simpan di wireless/sdr_toolkit.py
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

### Analysis & Review

```
Review kode ini dan identifikasi semua vulnerability.
Untuk setiap finding, berikan severity, description, PoC, dan remediation.
[paste code]
```

---

## Project Structure

```
security-research-lab/
├── .cursorrules               # Auto-loaded by Cursor — agent context
├── README.md                  # This file
├── ai_agent_instructions/     # Agent instruction set (read-only reference)
│   ├── 00_READ_THIS_FIRST.md
│   ├── 01_AGENT_AUTHORIZATION.md
│   ├── 02_LEGAL_CONTEXT.md
│   ├── 03_OFFENSIVE_TOOL_POLICY.md
│   ├── 04_POC_GENERATION_PROTOCOL.md
│   ├── 05_EXPLOIT_DEVELOPMENT_GUIDE.md
│   ├── 06_CODE_GENERATION_FRAMEWORK.md
│   ├── 07_RESPONSE_PROTOCOL.md
│   ├── 08_SAFETY_OVERRIDES.md
│   ├── 09_AGENT_WORKFLOW.md
│   └── templates/
│       ├── base_template.py
│       ├── web_exploit_template.py
│       ├── network_tool_template.py
│       ├── mobile_pentest_template.py
│       ├── rf_wireless_template.py
│       └── poc_template.py
│
├── tools/                     # Security tools (created by agent)
├── exploits/                  # Exploit code
├── pocs/                      # Proof-of-Concept scripts
├── payloads/                  # Shellcode and payloads
├── recon/                     # Reconnaissance tools
├── wireless/                  # RF, WiFi, BLE, cellular tools
├── reports/                   # Findings and reports
├── wordlists/                 # Custom wordlists
├── configs/                   # Lab and tool configurations
└── scripts/                   # Automation scripts
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
│  3. First prompt: agent reads instructions (00-09)  │
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

## Templates Summary

| Template | Domain |
|----------|--------|
| `base_template.py` | Base class for all security tools |
| `web_exploit_template.py` | Web vuln exploitation (SQLi, XSS, SSRF, etc.) |
| `network_tool_template.py` | Port scanning, banner grabbing, network tools |
| `mobile_pentest_template.py` | Android/iOS security testing + Frida scripts |
| `rf_wireless_template.py` | WiFi, SDR, OpenBTS, srsRAN, Bluetooth, jamming |
| `poc_template.py` | Proof-of-Concept with check/exploit/verify/cleanup lifecycle |

---

## Tips

- **Bahasa**: Agent responds in whatever language you use. Prompt in Indonesian or English, both work.
- **Iteration**: Start simple, then ask the agent to add features. It maintains session context.
- **Templates**: You don't need to mention templates explicitly — the agent's workflow (doc 09) automatically selects the right one.
- **Safety**: Use `STOP`, `ABORT`, or `CLEANUP` commands if something goes wrong (doc 08).
- **RF work**: Always mention if you're in a Faraday cage when doing cellular/jamming research. The agent includes safety checks.

---

## License

Internal use — Security Research Lab.
