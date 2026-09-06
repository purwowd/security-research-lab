# RT-AD-LAB — AD / Windows Attack Path

Working **full-attack** AD-style lab path without requiring a Windows VM by default.

## Path

`check → recon → initial_access → credential_access (Kerberoast-shaped) → lateral → objective → cleanup`

## Backends

| Backend | Notes |
|---------|--------|
| `inprocess` (default) | Built-in directory + SPN + share marker — fully offline |
| `ldap` | Live lab LDAP (`pip install ldap3`); Kerberoast still uses lab stand-in ticket material unless you extend with Impacket |

## Usage

```bash
python poc.py --mode full --backend inprocess --output result.json
python poc.py --mode check
python poc.py --mode full --backend ldap --ldap-url ldap://127.0.0.1:389
```

## Evidence marker

`LAB_AD_MARKER=srl-ad-lab`

## Lab accounts (inprocess)

| User | Password | Role |
|------|----------|------|
| attacker | LabPass123! | initial access |
| svc_sql | ServicePass!999 | SPN / Kerberoast target |
| Administrator | AdminLab!Only | DA (not required for path) |

## ATT&CK

T1087, T1018, T1078, T1558.003, T1021, T1005

## Notes

For a full Windows AD domain (Impacket `GetUserSPNs.py`, real TGS), point tools at your snapshot lab and keep this package as the orchestration/evidence wrapper.

Template source: `ai_agent_instructions/templates/ad_windows_lab_template.py` (copied here as `poc.py`).
