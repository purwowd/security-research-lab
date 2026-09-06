# POC-CLOUD-IAM-LAB — Cloud IAM Attack Path

Working **full-attack** cloud lab path (AWS-shaped): enum → IAM escalate → read secret marker → cleanup.

## Backends

| Backend | When |
|---------|------|
| `mock` (default fallback) | No Docker — in-process AWS-shaped lab |
| `localstack` | `docker compose up -d` then `--backend localstack` |
| `auto` | Prefer LocalStack if `:4566` is up, else mock |

## Bring up LocalStack (optional)

```bash
docker compose up -d
pip install -r requirements.txt
```

## Usage

```bash
# Always works offline
python poc.py --mode full --backend mock --output result.json

# Against LocalStack
python poc.py --mode full --backend localstack --endpoint-url http://127.0.0.1:4566

# Check only
python poc.py --mode check --backend mock
```

## Evidence marker

`LAB_CLOUD_TOKEN=srl-cloud-lab-7c2e`

## ATT&CK

T1580, T1526, T1078.004, T1098, T1530

## Notes

Template source of truth: `ai_agent_instructions/templates/cloud_lab_template.py` (copied here as `poc.py`).
