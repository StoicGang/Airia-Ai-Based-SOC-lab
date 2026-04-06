#!/usr/bin/env python3
"""
scripts/soc_monitor.py — Phase 1 pipeline.

Basic ICMP flood detection → Airia AI analysis → console report.
Kept for reference. Phase 2+ should use soc_monitor_v2.py.

Usage:
    sudo python scripts/soc_monitor.py
"""

import csv
import json
import os
import socket
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── Path Setup ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / "config" / ".env")

# ── Config ────────────────────────────────────────────────────
AIRIA_API_URL = os.getenv("AIRIA_API_URL")
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY")
DESTINATION_IP = os.getenv("DESTINATION_IP", "192.168.56.20")
DESTINATION_HOST = os.getenv("DESTINATION_HOST", "Kali-SOC-Monitor")
INTERFACE = os.getenv("INTERFACE", "eth0")
CAPTURE_DURATION = int(os.getenv("CAPTURE_DURATION", "100"))
THRESHOLD = int(os.getenv("THRESHOLD", "40"))

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

PCAP_FILE = os.getenv("PCAP_FILE", str(LOG_DIR / "traffic.pcap"))
CSV_FILE = os.getenv("CSV_FILE", str(LOG_DIR / "traffic.csv"))
ALERT_FILE = os.getenv("ALERT_FILE", str(LOG_DIR / "alert.json"))


# ── Helpers ───────────────────────────────────────────────────

def run_command(cmd, description):
    print(f"[+] {description}")
    subprocess.run(cmd, check=True)


def resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Unknown"


# ── Step 1: Capture ──────────────────────────────────────────

def capture_traffic():
    if os.path.exists(PCAP_FILE):
        os.remove(PCAP_FILE)

    capture_cmd = [
        "tshark",
        "-i", INTERFACE,
        "-f", f"icmp and dst host {DESTINATION_IP}",
        "-a", f"duration:{CAPTURE_DURATION}",
        "-w", PCAP_FILE
    ]

    run_command(capture_cmd,
                f"Capturing on {INTERFACE} for {CAPTURE_DURATION}s — waiting for ICMP traffic...")

    if not os.path.exists(PCAP_FILE):
        raise RuntimeError(
            "PCAP capture failed. Check: tshark installed? "
            "Interface name correct? Run with sudo?")

    print(f"[+] Capture saved to {PCAP_FILE} ({os.path.getsize(PCAP_FILE)} bytes)")


# ── Step 2: Convert ──────────────────────────────────────────

def convert_to_csv():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

    convert_cmd = [
        "tshark",
        "-r", PCAP_FILE,
        "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "ip.proto",
        "-e", "frame.len",
        "-E", "header=y",
        "-E", "separator=,",
        "-E", "quote=d"
    ]

    with open(CSV_FILE, "w", newline="") as outfile:
        subprocess.run(convert_cmd, stdout=outfile, check=True)

    print(f"[+] CSV created at {CSV_FILE}")


# ── Step 3: Analyze ──────────────────────────────────────────

def analyze_traffic():
    ip_counter = Counter()

    with open(CSV_FILE, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            src_ip = (row.get("ip.src") or "").strip().strip('"')
            if src_ip:
                ip_counter[src_ip] += 1

    print("\n[+] Traffic volume per source IP:\n")
    for ip, count in ip_counter.most_common():
        print(f"    {ip:<20} {count:>5} packets")

    for ip, count in ip_counter.most_common():
        if count > THRESHOLD:
            print(f"\n[!] Suspicious IP: {ip} ({count} packets > threshold {THRESHOLD})")
            return ip, count

    print(f"\n[+] No suspicious activity. All IPs under threshold ({THRESHOLD}).")
    return None, None


# ── Step 4: Alert ─────────────────────────────────────────────

def generate_alert(ip, count):
    alert_id = f"SOC-{uuid.uuid4().hex[:8].upper()}"

    alert = {
        "alert_id": alert_id,
        "alert_type": "Suspicious Network Volume",
        "indicator_type": "ip",
        "indicator_value": ip,
        "source_host": resolve_hostname(ip),
        "destination_host": DESTINATION_HOST,
        "destination_ip": DESTINATION_IP,
        "protocol": "ICMP",
        "evidence": {
            "packet_count": count,
            "time_window_seconds": CAPTURE_DURATION,
            "threshold": THRESHOLD,
            "data_source": os.path.basename(PCAP_FILE)
        },
        "analyst_question": "Is this expected activity or suspicious scanning/noise?"
    }

    with open(ALERT_FILE, "w") as f:
        json.dump(alert, f, indent=4)

    print(f"[+] Alert JSON written to {ALERT_FILE}")
    print(f"[+] Alert ID: {alert_id}")
    return alert


# ── Step 5: Airia ─────────────────────────────────────────────

def send_to_airia(alert):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": AIRIA_API_KEY
    }
    payload = {
        "userInput": json.dumps(alert),
        "asyncOutput": False
    }

    print("\n[+] Sending alert to Airia SOC Agent...")
    response = requests.post(AIRIA_API_URL, headers=headers,
                             json=payload, timeout=100)
    response.raise_for_status()
    print(f"[+] Airia responded with status {response.status_code}")

    try:
        data = response.json()
        print("\n[+] Airia Response JSON:")
        print(json.dumps(data, indent=2))
    except Exception:
        print("[+] Airia response (raw text):")
        print(response.text)


# ── Main ──────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f" AIRIA SOC MONITOR — Starting")
    print(f" Target:    {DESTINATION_IP}")
    print(f" Interface: {INTERFACE}")
    print(f" Threshold: {THRESHOLD} packets")
    print(f"{'='*55}\n")

    try:
        capture_traffic()
        convert_to_csv()
        ip, count = analyze_traffic()

        if ip:
            alert = generate_alert(ip, count)
            send_to_airia(alert)
        else:
            print("[+] No alert generated, nothing sent to Airia.")

        print("\n[+] Workflow complete.")

    except subprocess.CalledProcessError as e:
        print(f"\n[!] tshark command failed: {e}")
        print("[!] Try running with sudo: sudo python scripts/soc_monitor.py")
    except requests.exceptions.HTTPError as e:
        print(f"\n[!] Airia API error: {e}")
    except Exception as e:
        print(f"\n[!] Error: {e}")


if __name__ == "__main__":
    main()
