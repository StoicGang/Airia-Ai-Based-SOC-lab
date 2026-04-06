#!/usr/bin/env python3
"""
scripts/soc_monitor_v2.py — Phase 2 pipeline.

Replaces soc_monitor.py. Adds:
  - YAML-driven detection rules
  - SQLite persistence
  - Session tracking
  - --rule flag to target a specific rule
  - --list flag to show available rules

Usage:
    sudo python scripts/soc_monitor_v2.py              # RULE-001 (default)
    sudo python scripts/soc_monitor_v2.py --rule RULE-002
    sudo python scripts/soc_monitor_v2.py --list
"""

import argparse
import json
import os
import socket
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Path Setup ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import init_db, save_alert, create_session, complete_session
from detection.rules import load_rules, get_rule_by_id, run_rule

load_dotenv(BASE_DIR / "config" / ".env")

# ── Config ────────────────────────────────────────────────────
AIRIA_API_URL = os.getenv("AIRIA_API_URL")
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY")
DESTINATION_IP = os.getenv("DESTINATION_IP", "192.168.56.20")
DESTINATION_HOST = os.getenv("DESTINATION_HOST", "Kali-SOC-Monitor")
INTERFACE = os.getenv("INTERFACE", "eth0")

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

PCAP_FILE = os.getenv("PCAP_FILE", str(LOG_DIR / "traffic.pcap"))
CSV_FILE = os.getenv("CSV_FILE", str(LOG_DIR / "traffic.csv"))


def validate_config() -> None:
    errors = []
    if not AIRIA_API_URL or "YOUR-PROJECT-ID" in AIRIA_API_URL:
        errors.append("AIRIA_API_URL not configured in config/.env")
    if not AIRIA_API_KEY or "YOUR-API-KEY" in AIRIA_API_KEY:
        errors.append("AIRIA_API_KEY not configured in config/.env")
    if errors:
        for e in errors:
            print(f"[!] {e}")
        raise SystemExit(1)


def resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Unknown"


def parse_airia_response(data: dict) -> dict:
    raw = data.get("result", "")
    if not raw:
        return data
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_result": raw}


def build_alert(rule: dict, src_ip: str, count: int) -> dict:
    return {
        "alert_id": f"SOC-{uuid.uuid4().hex[:8].upper()}",
        "alert_type": rule["alert_type"],
        "indicator_type": "ip",
        "indicator_value": src_ip,
        "source_host": resolve_hostname(src_ip),
        "destination_host": DESTINATION_HOST,
        "destination_ip": DESTINATION_IP,
        "protocol": rule["protocol"].upper(),
        "rule_id": rule["id"],
        "evidence": {
            "packet_count": count,
            "time_window_seconds": rule["time_window"],
            "threshold": rule["threshold"],
            "data_source": "traffic.pcap"
        },
        "analyst_question": "Is this expected activity or a genuine threat?"
    }


def send_to_airia(alert: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": AIRIA_API_KEY
    }
    payload = {
        "userInput": json.dumps(alert),
        "asyncOutput": False
    }
    print("\n[Airia] Sending alert...")
    response = requests.post(AIRIA_API_URL, headers=headers,
                             json=payload, timeout=100)
    response.raise_for_status()
    print(f"[Airia] HTTP {response.status_code}")
    return parse_airia_response(response.json())


def print_report(report: dict) -> None:
    ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    risk = report.get("risk_level", "Unknown")
    mitre = report.get("mitre_mapping", {})

    print("\n" + "=" * 60)
    print("  🛡️  AIRIA SOC ANALYSIS REPORT")
    print("=" * 60)
    print(f"  Alert ID   : {report.get('alert_id')}")
    print(f"  Risk Level : {ICONS.get(risk, '⚪')} {risk}")
    print(f"  Risk Score : {report.get('risk_score')}/100")
    print(f"  Confidence : {report.get('confidence_level')}")
    print(f"  Escalate   : {'⚠️  YES' if report.get('escalation_required') else '✅ No'}")
    if isinstance(mitre, dict):
        print(f"  MITRE      : {mitre.get('technique_id')} — {mitre.get('technique_name')}")
    print(f"\n  Summary: {report.get('executive_summary')}")
    actions = report.get("recommended_actions", [])
    if actions:
        print("\n  Actions:")
        for i, a in enumerate(actions, 1):
            print(f"    {i}. {a}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="SOC Monitor v2")
    parser.add_argument("--rule", default="RULE-001",
                        help="Rule ID to run (default: RULE-001)")
    parser.add_argument("--list", action="store_true",
                        help="List all available rules and exit")
    args = parser.parse_args()

    if args.list:
        for r in load_rules():
            status = "✅" if r.get("enabled") else "❌"
            print(f"  {status} {r['id']}: {r['name']} "
                  f"(threshold={r['threshold']}, window={r['time_window']}s)")
        return

    validate_config()
    init_db()

    rule = get_rule_by_id(args.rule)
    if not rule:
        print(f"[!] Rule not found: {args.rule}")
        print("[!] Use --list to see available rules")
        raise SystemExit(1)

    session_id = uuid.uuid4().hex[:8].upper()

    print(f"\n{'=' * 55}")
    print(f"  AIRIA SOC MONITOR v2")
    print(f"  Rule      : {rule['id']} — {rule['name']}")
    print(f"  Target    : {DESTINATION_IP}")
    print(f"  Interface : {INTERFACE}")
    print(f"  Window    : {rule['time_window']}s")
    print(f"  Threshold : {rule['threshold']}")
    print(f"  Session   : {session_id}")
    print(f"{'=' * 55}\n")

    create_session(session_id, INTERFACE, rule["time_window"], rule["id"])

    try:
        src_ip, count = run_rule(rule, PCAP_FILE, CSV_FILE)

        if src_ip:
            alert = build_alert(rule, src_ip, count)
            soc_report = send_to_airia(alert)
            print_report(soc_report)

            save_alert(alert, soc_report, session_id)
            complete_session(session_id, count, 1)

            report_path = LOG_DIR / f"{alert['alert_id']}_report.json"
            with open(report_path, "w") as f:
                json.dump(soc_report, f, indent=2)
            print(f"\n[+] Report saved: {report_path}")
        else:
            complete_session(session_id, 0, 0)
            print("[+] No alert. Session recorded.")

        print("\n[+] Workflow complete.")

    except RuntimeError as e:
        print(f"\n[!] {e}")
    except requests.exceptions.ConnectionError:
        print("\n[!] Cannot reach Airia API. Check internet connection.")
    except requests.exceptions.HTTPError as e:
        print(f"\n[!] Airia error: {e}")
    except KeyboardInterrupt:
        print("\n[!] Stopped.")


if __name__ == "__main__":
    main()
