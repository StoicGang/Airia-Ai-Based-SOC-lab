#!/usr/bin/env python3
"""
attack_simulator/port_scanner.py — Port scan attack simulation.
Phase: 2 | Status: Complete
Run from: Arch Linux VM (192.168.56.10)
Target:   Kali Linux SOC Monitor (192.168.56.20)

Usage:
    python port_scanner.py
    python port_scanner.py --target 192.168.56.20 --start 1 --end 1024
"""

import argparse
import socket
from datetime import datetime


TARGET_DEFAULT    = "192.168.56.20"
PORT_START        = 1
PORT_END          = 1024
TIMEOUT_DEFAULT   = 0.1


def port_scan(target: str, start: int, end: int, timeout: float) -> list[int]:
    """
    Scan a range of TCP ports on the target using socket connect.

    Args:
        target:  Destination IP address (Kali SOC Monitor)
        start:   First port to scan (inclusive)
        end:     Last port to scan (inclusive)
        timeout: Per-port connection timeout in seconds

    Returns:
        List of open port numbers found.
    """
    open_ports = []
    total      = end - start + 1

    print(f"[*] Port Scan — Target: {target} | Range: {start}-{end} ({total} ports)")
    print(f"[*] Start: {datetime.now().isoformat()}")

    for port in range(start, end + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
                print(f"    [OPEN] {port}")
        except socket.error:
            pass

    print(f"\n[+] Scan complete — {len(open_ports)} open ports found out of {total} scanned")
    print(f"[+] Done: {datetime.now().isoformat()}")
    return open_ports


def main() -> None:
    parser = argparse.ArgumentParser(description="Port Scanner (Arch Linux attacker)")
    parser.add_argument("--target",  default=TARGET_DEFAULT,
                        help=f"Target IP (default: {TARGET_DEFAULT})")
    parser.add_argument("--start",   type=int, default=PORT_START,
                        help=f"First port (default: {PORT_START})")
    parser.add_argument("--end",     type=int, default=PORT_END,
                        help=f"Last port (default: {PORT_END})")
    parser.add_argument("--timeout", type=float, default=TIMEOUT_DEFAULT,
                        help=f"Per-port timeout seconds (default: {TIMEOUT_DEFAULT})")
    args = parser.parse_args()

    open_ports = port_scan(args.target, args.start, args.end, args.timeout)
    if open_ports:
        print(f"\n[*] Open ports: {open_ports}")


if __name__ == "__main__":
    main()
