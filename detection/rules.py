#!/usr/bin/env python3
"""
detection/rules.py — YAML-driven detection rule engine.
Phase: 2 | Status: Baseline locked

Loads rules from config/detection_rules.yaml.
Each rule specifies a tshark filter, threshold, and metadata.
"""

import yaml
import os
import subprocess
import csv
import tempfile
from pathlib import Path
from typing import Optional
from collections import Counter
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

RULES_PATH     = os.getenv("RULES_PATH",
                 str(Path(__file__).parent.parent / "config" / "detection_rules.yaml"))
DESTINATION_IP = os.getenv("DESTINATION_IP", "192.168.56.20")
INTERFACE      = os.getenv("INTERFACE", "eth0")


def load_rules() -> list[dict]:
    """
    Load all enabled detection rules from YAML file.

    Returns:
        List of rule dicts. Returns empty list if file not found.
    """
    if not os.path.exists(RULES_PATH):
        raise FileNotFoundError(f"Rules file not found: {RULES_PATH}")

    with open(RULES_PATH, "r") as f:
        data = yaml.safe_load(f)

    rules = [r for r in data.get("rules", []) if r.get("enabled", True)]
    print(f"[Rules] Loaded {len(rules)} enabled rules from {RULES_PATH}")
    return rules


def get_rule_by_id(rule_id: str) -> Optional[dict]:
    """Return a single rule by its ID."""
    for rule in load_rules():
        if rule["id"] == rule_id:
            return rule
    return None


def run_capture(rule: dict, pcap_path: str) -> bool:
    """
    Run tshark capture for a specific rule.

    Args:
        rule:      Rule dict from YAML
        pcap_path: Where to save the pcap file

    Returns:
        True if capture succeeded and file has data.
    """
    tshark_filter = rule["tshark_filter"].format(target_ip=DESTINATION_IP)
    duration      = rule["time_window"]

    print(f"[Capture] Rule: {rule['name']} | Filter: {tshark_filter}")
    print(f"[Capture] Interface: {INTERFACE} | Duration: {duration}s")
    print(f"[Capture] ⚡ Send your attack NOW — {duration} seconds to capture...")

    cmd = [
        "tshark", "-i", INTERFACE,
        "-f", tshark_filter,
        "-a", f"duration:{duration}",
        "-w", pcap_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"tshark failed (exit {result.returncode}): {result.stderr[:300]}\n"
            f"HINT: If dissector error — change INTERFACE to '2' in config/.env"
        )

    if not os.path.exists(pcap_path) or os.path.getsize(pcap_path) < 100:
        print("[Capture] Warning: PCAP very small — was attack traffic sent?")
        return False

    size = os.path.getsize(pcap_path)
    print(f"[Capture] Saved {size} bytes to {pcap_path}")
    return True


def parse_pcap_to_csv(pcap_path: str, csv_path: str) -> int:
    """
    Convert pcap to CSV and return number of data rows.

    Args:
        pcap_path: Input pcap file
        csv_path:  Output CSV file

    Returns:
        Number of packet rows (excluding header).
    """
    cmd = [
        "tshark", "-r", pcap_path, "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "ip.proto",
        "-e", "frame.len",
        "-e", "tcp.dstport",
        "-e", "udp.dstport",
        "-E", "header=y",
        "-E", "separator=,",
        "-E", "quote=d"
    ]

    with open(csv_path, "w", newline="") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"CSV conversion failed: {result.stderr.decode()[:200]}")

    with open(csv_path) as f:
        rows = sum(1 for _ in f) - 1   # subtract header row
    print(f"[Parse] {rows} packets parsed to {csv_path}")
    return rows


def analyze_csv(csv_path: str, rule: dict) -> tuple[Optional[str], int]:
    """
    Analyze the CSV against the rule threshold.

    ICMP/SYN rules: count packets per source IP.
    Port scan rules: count unique destination ports per source IP.

    Args:
        csv_path: Path to parsed CSV
        rule:     Rule dict with threshold and count_field

    Returns:
        (suspicious_ip, count) or (None, 0)
    """
    count_field = rule.get("count_field", "src_ip")
    threshold   = rule["threshold"]

    counter = Counter()

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src_ip = (row.get("ip.src") or "").strip().strip('"')
            if not src_ip:
                continue

            if count_field == "dst_port":
                # Port scan: count unique destination ports per source IP
                dst_port = (row.get("tcp.dstport") or
                            row.get("udp.dstport") or "").strip().strip('"')
                if dst_port:
                    counter[f"{src_ip}:{dst_port}"] += 1
            else:
                # Packet flood: count total packets per source IP
                counter[src_ip] += 1

    print(f"\n[Analyze] Traffic summary for rule: {rule['name']}")

    if count_field == "dst_port":
        # Collapse to: how many unique ports did each src IP scan?
        src_ports: dict[str, set] = {}
        for key in counter:
            src, port = key.split(":", 1)
            src_ports.setdefault(src, set()).add(port)

        for src, ports in sorted(src_ports.items(), key=lambda x: len(x[1]), reverse=True):
            bar  = "█" * min(len(ports) // 2, 40)
            flag = "  ← ALERT" if len(ports) > threshold else ""
            print(f"    {src:<20} {len(ports):>5} unique ports  {bar}{flag}")

        for src, ports in src_ports.items():
            if len(ports) > threshold:
                print(f"\n[!] Port scan detected: {src} ({len(ports)} unique ports > {threshold})")
                return src, len(ports)
    else:
        for ip, count in counter.most_common():
            bar  = "█" * min(count // 5, 40)
            flag = "  ← ALERT" if count > threshold else ""
            print(f"    {ip:<20} {count:>5} packets  {bar}{flag}")

        for ip, count in counter.most_common():
            if count > threshold:
                print(f"\n[!] Alert: {ip} ({count} > threshold {threshold})")
                return ip, count

    print(f"\n[Analyze] No suspicious activity. All below threshold ({threshold}).")
    return None, 0


def run_rule(rule: dict, pcap_path: str, csv_path: str) -> tuple[Optional[str], int]:
    """
    Full pipeline for one rule: capture → parse → analyze.

    Returns:
        (suspicious_ip, count) or (None, 0)
    """
    captured = run_capture(rule, pcap_path)
    if not captured:
        return None, 0

    parse_pcap_to_csv(pcap_path, csv_path)
    return analyze_csv(csv_path, rule)