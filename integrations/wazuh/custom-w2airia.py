#!/usr/bin/env python3
"""
Wazuh-to-AIRIA Integration Script
Forwards Wazuh alerts to the SOC Lab dashboard (AIRIA) for centralized monitoring.

Usage:
  - Triggered by Wazuh integratord when alert level >= threshold
  - Configure in ossec.conf under <integration> block
  - Reads alert JSON from stdin, forwards to AIRIA dashboard API

Wazuh ossec.conf integration block:
  <integration>
    <name>custom-w2airia.py</name>
    <level>5</level>
    <alert_format>json</alert_format>
  </integration>

Author: Zero (SOC Lab Phase 3)
Version: 1.0.0
"""

import sys
import json
import os
import logging
import requests
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
AIRIA_API_URL = os.getenv("AIRIA_API_URL", "http://192.168.56.20:5000/api/alerts/ingest")
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY", "")
LOG_FILE = "/var/ossec/logs/integrations/w2airia.log"
MIN_ALERT_LEVEL = int(os.getenv("W2AIRIA_MIN_LEVEL", "5"))
TIMEOUT = int(os.getenv("W2AIRIA_TIMEOUT", "10"))

# Severity mapping: Wazuh level -> SOC priority
SEVERITY_MAP = {
    range(0, 4): "LOW",
    range(4, 7): "MEDIUM",
    range(7, 10): "HIGH",
    range(10, 13): "CRITICAL",
    range(13, 16): "CRITICAL",
}

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("w2airia")


def get_severity(level: int) -> str:
    """Map Wazuh alert level to SOC severity."""
    for level_range, severity in SEVERITY_MAP.items():
        if level in level_range:
            return severity
    return "MEDIUM"


def parse_alert(alert_data: dict) -> dict:
    """
    Transform Wazuh alert JSON into AIRIA-compatible format.
    
    Input:  Raw Wazuh alert from integratord
    Output: Normalized alert dict for AIRIA dashboard
    """
    rule = alert_data.get("rule", {})
    agent = alert_data.get("agent", {})
    data = alert_data.get("data", {})
    syscheck = alert_data.get("syscheck", {})
    
    level = rule.get("level", 0)
    
    normalized = {
        "source": "wazuh",
        "timestamp": alert_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "alert_id": alert_data.get("id", "unknown"),
        "rule": {
            "id": rule.get("id", "0"),
            "description": rule.get("description", "No description"),
            "level": level,
            "groups": rule.get("groups", []),
            "mitre": rule.get("mitre", {}),
        },
        "severity": get_severity(level),
        "agent": {
            "id": agent.get("id", "000"),
            "name": agent.get("name", "unknown"),
            "ip": agent.get("ip", "0.0.0.0"),
        },
        "source_ip": data.get("srcip", alert_data.get("srcip", "")),
        "destination_ip": data.get("dstip", alert_data.get("dstip", "")),
        "full_log": alert_data.get("full_log", ""),
        "decoder": alert_data.get("decoder", {}).get("name", ""),
        "location": alert_data.get("location", ""),
    }
    
    # Add file integrity monitoring data if present
    if syscheck:
        normalized["fim"] = {
            "path": syscheck.get("path", ""),
            "event": syscheck.get("event", ""),
            "md5_before": syscheck.get("md5_before", ""),
            "md5_after": syscheck.get("md5_after", ""),
            "sha256_before": syscheck.get("sha256_before", ""),
            "sha256_after": syscheck.get("sha256_after", ""),
            "size_before": syscheck.get("size_before", ""),
            "size_after": syscheck.get("size_after", ""),
            "perm_before": syscheck.get("perm_before", ""),
            "perm_after": syscheck.get("perm_after", ""),
            "uid_after": syscheck.get("uid_after", ""),
            "gid_after": syscheck.get("gid_after", ""),
        }
    
    # Add MITRE ATT&CK mapping if available
    mitre = rule.get("mitre", {})
    if mitre:
        normalized["mitre_attack"] = {
            "id": mitre.get("id", []),
            "tactic": mitre.get("tactic", []),
            "technique": mitre.get("technique", []),
        }
    
    # Add vulnerability data if present
    vuln = data.get("vulnerability", {})
    if vuln:
        normalized["vulnerability"] = {
            "cve": vuln.get("cve", ""),
            "severity": vuln.get("severity", ""),
            "package": vuln.get("package", {}).get("name", ""),
            "title": vuln.get("title", ""),
        }
    
    return normalized


def send_to_airia(alert: dict) -> bool:
    """Send normalized alert to AIRIA dashboard API."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Wazuh-AIRIA-Integration/1.0",
    }
    
    if AIRIA_API_KEY:
        headers["Authorization"] = f"Bearer {AIRIA_API_KEY}"
    
    try:
        response = requests.post(
            AIRIA_API_URL,
            json=alert,
            headers=headers,
            timeout=TIMEOUT,
            verify=False,  # Self-signed certs in lab
        )
        
        if response.status_code in (200, 201, 202):
            logger.info(
                f"Alert forwarded: rule={alert['rule']['id']} "
                f"level={alert['rule']['level']} "
                f"agent={alert['agent']['name']} "
                f"severity={alert['severity']}"
            )
            return True
        else:
            logger.error(
                f"AIRIA returned {response.status_code}: {response.text[:200]}"
            )
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to AIRIA at {AIRIA_API_URL}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to AIRIA ({TIMEOUT}s)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    """
    Entry point. Wazuh integratord calls this script with:
      - sys.argv[1]: alert file path
      - sys.argv[2]: API key (optional)
      - sys.argv[3]: hook URL (optional)
    """
    # Read alert file path from args
    if len(sys.argv) < 2:
        logger.error("No alert file provided")
        sys.exit(1)
    
    alert_file = sys.argv[1]
    
    try:
        with open(alert_file, "r") as f:
            alert_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to read alert file {alert_file}: {e}")
        sys.exit(1)
    
    # Filter by minimum level
    level = alert_data.get("rule", {}).get("level", 0)
    if level < MIN_ALERT_LEVEL:
        logger.debug(f"Alert level {level} below threshold {MIN_ALERT_LEVEL}, skipping")
        sys.exit(0)
    
    # Parse and forward
    normalized = parse_alert(alert_data)
    success = send_to_airia(normalized)
    
    if not success:
        # Write to fallback file for retry
        fallback = "/var/ossec/logs/integrations/w2airia-failed.jsonl"
        try:
            with open(fallback, "a") as f:
                json.dump(normalized, f)
                f.write("\n")
            logger.info(f"Failed alert written to {fallback} for retry")
        except Exception as e:
            logger.error(f"Could not write to fallback: {e}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

