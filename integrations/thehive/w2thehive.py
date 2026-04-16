#!/usr/bin/env python3
"""
w2thehive.py — Wazuh → TheHive alert forwarder
Deployed as a Wazuh custom integration. Fires on alerts level >= 7.

Deploy to Wazuh container:
  docker cp integrations/thehive/w2thehive.py \
    docker-wazuh.manager-1:/var/ossec/integrations/custom-w2thehive
  docker exec docker-wazuh.manager-1 chmod 750 /var/ossec/integrations/custom-w2thehive
  docker exec docker-wazuh.manager-1 chown root:wazuh /var/ossec/integrations/custom-w2thehive

ossec.conf entry:
  <integration>
    <name>custom-w2thehive</name>
    <level>7</level>
    <alert_format>json</alert_format>
  </integration>
"""

import json
import sys
import logging
import requests
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────────────────────────────────
THEHIVE_URL = "http://192.168.56.20:9000"
THEHIVE_API_KEY = "CHANGE_THIS_thehive_api_key"
LOG_FILE = "/var/ossec/logs/w2thehive.log"
TIMEOUT = 10

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("w2thehive")

# ─── Risk Register Asset Map (from Phase 3) ───────────────────────────────────
RISK_ASSETS = {
    "192.168.56.10": {
        "name": "arch-workstation",
        "type": "Attacker VM",
        "criticality": "HIGH",
        "risks": ["T1059", "T1204", "T1498"]
    },
    "192.168.56.20": {
        "name": "kali-soc-monitor",
        "type": "SOC Monitor Host",
        "criticality": "CRITICAL",
        "risks": ["T1190", "T1133"]
    }
}

# ─── Severity / TLP Mapping ───────────────────────────────────────────────────
def get_severity(level: int) -> int:
    """Wazuh level → TheHive severity (1=Low, 2=Medium, 3=High, 4=Critical)."""
    if level >= 12:
        return 4
    elif level >= 10:
        return 3
    elif level >= 7:
        return 2
    return 1


def get_tlp(level: int) -> int:
    """Severity → TLP (1=Green, 2=Amber, 3=Red)."""
    if level >= 12:
        return 3
    elif level >= 7:
        return 2
    return 1


# ─── Risk Register Context ────────────────────────────────────────────────────
def get_risk_context(data: dict) -> str:
    lines = []
    for key in ("srcip", "dstip", "src_ip", "dst_ip"):
        ip = data.get(key, "")
        if ip and ip in RISK_ASSETS:
            a = RISK_ASSETS[ip]
            lines.append(
                f"- **{a['name']}** (`{ip}`) — {a['type']} | "
                f"Criticality: `{a['criticality']}` | "
                f"Known risk techniques: {', '.join(a['risks'])}"
            )
    return "\n".join(lines) if lines else "_No matching assets in risk register._"


# ─── Observable Builder ───────────────────────────────────────────────────────
def build_observables(data: dict, level: int) -> list:
    observables = []
    tlp = get_tlp(level)

    for key, dtype, label in [
        ("srcip",   "ip",  "Source IP"),
        ("src_ip",  "ip",  "Source IP"),
        ("dstip",   "ip",  "Destination IP"),
        ("dst_ip",  "ip",  "Destination IP"),
        ("url",     "url", "URL"),
        ("md5",     "hash","MD5 hash"),
        ("sha1",    "hash","SHA1 hash"),
        ("sha256",  "hash","SHA256 hash"),
        ("hostname","fqdn","Hostname"),
    ]:
        val = data.get(key, "").strip()
        if val and val not in ("", "N/A", "unknown"):
            observables.append({
                "dataType": dtype,
                "data": val,
                "message": f"{label} from Wazuh alert",
                "tlp": tlp,
                "tags": ["wazuh", "auto-extracted"]
            })

    return observables


# ─── Alert Creator ────────────────────────────────────────────────────────────
def create_alert(raw: str) -> None:
    try:
        alert = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse alert JSON: {e}")
        return

    rule  = alert.get("rule", {})
    agent = alert.get("agent", {})
    data  = alert.get("data", {})

    level       = int(rule.get("level", 0))
    rule_id     = str(rule.get("id", "0"))
    description = rule.get("description", "Wazuh alert")
    timestamp   = alert.get("timestamp", datetime.now(timezone.utc).isoformat())
    alert_id    = alert.get("id", rule_id)

    # MITRE
    mitre = rule.get("mitre", {})
    mitre_ids     = mitre.get("id", [])     if isinstance(mitre.get("id"),     list) else [mitre.get("id",     "")]
    mitre_tactics = mitre.get("tactic", []) if isinstance(mitre.get("tactic"), list) else [mitre.get("tactic", "")]
    mitre_ids     = [m for m in mitre_ids if m]
    mitre_tactics = [t for t in mitre_tactics if t]

    # Build description markdown
    md = f"""## Wazuh Alert — Rule {rule_id}

| Field | Value |
|---|---|
| **Rule ID** | `{rule_id}` |
| **Level** | `{level}` |
| **Description** | {description} |
| **Agent** | {agent.get('name', 'N/A')} (`{agent.get('ip', agent.get('id', 'N/A'))}`) |
| **Timestamp** | {timestamp} |
| **Groups** | {', '.join(rule.get('groups', []))} |

### MITRE ATT&CK
- **Technique IDs:** {', '.join(mitre_ids) if mitre_ids else '_None mapped_'}
- **Tactics:** {', '.join(mitre_tactics) if mitre_tactics else '_None mapped_'}

### Risk Register Context
{get_risk_context(data)}

### Raw Event Data
```json
{json.dumps(data, indent=2)[:3000]}
```
"""

    # Deduplicate key: rule_id + alert_id
    source_ref = f"wazuh-{rule_id}-{alert_id}"

    tags = ["wazuh", "soc-lab", f"level-{level}"]
    tags += [f"mitre:{m}" for m in mitre_ids]
    tags += [f"group:{g}" for g in rule.get("groups", [])]

    payload = {
        "type":        "wazuh",
        "source":      "wazuh-siem",
        "sourceRef":   source_ref,
        "title":       f"[Wazuh L{level}] {description}",
        "description": md,
        "severity":    get_severity(level),
        "tlp":         get_tlp(level),
        "tags":        list(set(tags)),
        "observables": build_observables(data, level)
    }

    headers = {
        "Authorization": f"Bearer {THEHIVE_API_KEY}",
        "Content-Type":  "application/json"
    }

    try:
        resp = requests.post(
            f"{THEHIVE_URL}/api/v1/alert",
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        if resp.status_code in (200, 201):
            alert_obj = resp.json()
            log.info(f"Alert created: {alert_obj.get('_id', '?')} | {payload['title']}")
        elif resp.status_code == 207:
            # Duplicate sourceRef — already exists, skip silently
            log.info(f"Duplicate skipped: {source_ref}")
        else:
            log.error(f"TheHive returned {resp.status_code}: {resp.text[:500]}")
    except requests.exceptions.ConnectionError:
        log.error(f"Cannot reach TheHive at {THEHIVE_URL} — is it running?")
    except requests.exceptions.Timeout:
        log.error(f"TheHive request timed out after {TIMEOUT}s")
    except Exception as e:
        log.error(f"Unexpected error: {e}")


# ─── Entrypoint ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Wazuh passes alert as a file path argument
        alert_file = sys.argv[1]
        try:
            with open(alert_file, "r") as f:
                create_alert(f.read())
        except FileNotFoundError:
            log.error(f"Alert file not found: {alert_file}")
            sys.exit(1)
    else:
        # Fallback: read from stdin
        create_alert(sys.stdin.read())
