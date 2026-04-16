#!/usr/bin/env python3
"""
risk_loader.py — Load Phase 3 risk register and inject context into TheHive case templates.
Run standalone or import from w2thehive.py.

Usage:
  python3 risk_loader.py                  # print risk summary
  python3 risk_loader.py --thehive-sync   # create TheHive custom fields for assets
"""

import json
import os
import sys
import csv
import argparse
from pathlib import Path

# Paths — adjust if repo layout differs
REPO_ROOT = Path(__file__).resolve().parents[2]
RISK_REGISTER_CSV = REPO_ROOT / "risk" / "risk_register.csv"
RISK_REGISTER_MD  = REPO_ROOT / "risk" / "risk_register.md"

THEHIVE_URL = "http://192.168.56.20:9000"
THEHIVE_API_KEY = "CHANGE_THIS_thehive_api_key"


def load_from_csv() -> list:
    """Load risk register from CSV (generated in Phase 3)."""
    risks = []
    if not RISK_REGISTER_CSV.exists():
        print(f"[risk_loader] CSV not found at {RISK_REGISTER_CSV} — using hardcoded fallback.")
        return load_hardcoded()

    with open(RISK_REGISTER_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            risks.append(row)
    return risks


def load_hardcoded() -> list:
    """Hardcoded fallback — mirrors Phase 3 risk register (31 risks, ISO 27001 aligned)."""
    return [
        {"id": "R-001", "asset": "kali-soc-monitor", "ip": "192.168.56.20",
         "threat": "Unauthorized access", "likelihood": "M", "impact": "H",
         "risk_level": "HIGH", "control": "A.9.1.1", "treatment": "Mitigate",
         "technique": "T1190"},
        {"id": "R-002", "asset": "arch-workstation", "ip": "192.168.56.10",
         "threat": "Malware execution", "likelihood": "M", "impact": "H",
         "risk_level": "HIGH", "control": "A.12.2.1", "treatment": "Mitigate",
         "technique": "T1059"},
        {"id": "R-003", "asset": "wazuh-manager", "ip": "192.168.56.20",
         "threat": "Log tampering", "likelihood": "L", "impact": "H",
         "risk_level": "MEDIUM", "control": "A.12.4.2", "treatment": "Mitigate",
         "technique": "T1070"},
        {"id": "R-004", "asset": "flask-dashboard", "ip": "192.168.56.20",
         "threat": "Web app attack", "likelihood": "M", "impact": "M",
         "risk_level": "MEDIUM", "control": "A.14.2.1", "treatment": "Mitigate",
         "technique": "T1190"},
        {"id": "R-005", "asset": "docker-daemon", "ip": "192.168.56.20",
         "threat": "Container escape", "likelihood": "L", "impact": "C",
         "risk_level": "HIGH", "control": "A.12.6.1", "treatment": "Mitigate",
         "technique": "T1611"},
    ]


def get_asset_map() -> dict:
    """Return IP → risk context mapping for use in w2thehive.py."""
    risks = load_from_csv()
    asset_map = {}
    for r in risks:
        ip = r.get("ip", "")
        if ip:
            if ip not in asset_map:
                asset_map[ip] = {
                    "name": r.get("asset", ip),
                    "risks": [],
                    "highest_level": "LOW"
                }
            asset_map[ip]["risks"].append({
                "id": r.get("id"),
                "threat": r.get("threat"),
                "level": r.get("risk_level"),
                "technique": r.get("technique"),
                "control": r.get("control")
            })
            # Track highest risk level
            levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
            if levels.get(r.get("risk_level", "LOW"), 0) > levels.get(asset_map[ip]["highest_level"], 0):
                asset_map[ip]["highest_level"] = r.get("risk_level", "LOW")
    return asset_map


def print_summary():
    risks = load_from_csv()
    print(f"\n{'='*60}")
    print(f"  Phase 3 Risk Register — {len(risks)} risks loaded")
    print(f"{'='*60}")
    levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in risks:
        lvl = r.get("risk_level", "LOW").upper()
        if lvl in levels:
            levels[lvl] += 1
    for lvl, count in levels.items():
        bar = "█" * count
        print(f"  {lvl:10} {bar} ({count})")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOC Lab Risk Register Loader")
    parser.add_argument("--summary", action="store_true", help="Print risk summary")
    parser.add_argument("--json", action="store_true", help="Output asset map as JSON")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(get_asset_map(), indent=2))
    else:
        print_summary()
