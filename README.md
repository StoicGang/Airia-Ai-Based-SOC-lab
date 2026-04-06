# 🛡️ AI-Powered SOC Analyst Lab

Automated Security Operations Center — attack detection, AI-driven threat analysis, and SIEM integration. Built on free tools.

---

## Architecture

```
  Arch Linux (Attacker)              Kali Linux (SOC Monitor)
  192.168.56.10                      192.168.56.20
       │                                  │
       │── ICMP/TCP/Scan ───────────────►│── tshark → rules → Airia AI ──┐
       │                                  │                               │
       │── Wazuh Agent (TCP 1514) ──────►│── Wazuh Manager → w2airia ──┐ │
                                          │                             │ │
                                          │  ┌──────────────────────────▼─▼──┐
                                          │  │  Flask Dashboard :5000        │
                                          │  │  (network + host alerts)      │
                                          │  └───────────────────────────────┘
                                          │  ┌───────────────────────────────┐
                                          │  │  Wazuh Dashboard :443         │
                                          │  │  (SIEM-native views)          │
                                          │  └───────────────────────────────┘
```

**Detection Path 1 (Network):** tshark → PCAP → CSV → YAML rules → Airia AI → SQLite → Flask  
**Detection Path 2 (Host):** Wazuh Agent → Manager → custom-w2airia.py → Flask ingest → SQLite

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Network detection | tshark + Python + YAML rules |
| AI analysis | Airia (GPT-4o mini) |
| SIEM | Wazuh 4.14.4 (Docker) |
| Dashboard | Flask + Wazuh Dashboard |
| Database | SQLite 3 |
| Integration | custom-w2airia.py (Wazuh → Flask) |
| VMs | VirtualBox (Kali + Arch, host-only network) |

---

## Quick Start

```bash
# Clone
git clone https://github.com/StoicGang/Airia-Ai-Based-SOC-lab.git
cd Airia-Ai-Based-SOC-lab

# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env  # fill in Airia credentials

# Init DB
python database/db_manager.py

# Run network monitor
sudo python scripts/soc_monitor_v2.py              # ICMP flood (default)
sudo python scripts/soc_monitor_v2.py --rule RULE-002  # SYN flood
sudo python scripts/soc_monitor_v2.py --rule RULE-003  # Port scan

# Deploy Wazuh SIEM
cd docker && docker compose -f generate-indexer-certs.yml run --rm generator
docker compose up -d

# Start dashboard
python dashboard/app.py  # http://192.168.56.20:5000

# Attack from Arch
ping 192.168.56.20 -c 200 -s 64
```

---

## Detection Coverage

### Network (Phase 2)

| Rule | Attack | Threshold | MITRE |
|------|--------|-----------|-------|
| RULE-001 | ICMP Flood | 40 pkts / 100s | T1498 |
| RULE-002 | TCP SYN Flood | 80 SYN / 60s | T1498.001 |
| RULE-003 | Port Scan | 15 ports / 30s | T1046 |

### Host-Based (Phase 3 — Wazuh)

| Source | Detects | Level |
|--------|---------|-------|
| FIM (Syscheck) | File changes | 5–7 |
| Rootcheck | System anomalies | 7 |
| Log analysis | Auth failures | 3–12 |
| Custom 100001 | ICMP flood (syslog) | 10 |

---

## Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Base pipeline — ICMP → Airia AI | ✅ |
| 2 | Multi-attack + SQLite + Flask dashboard | ✅ |
| 3 | Wazuh SIEM + AIRIA integration | ✅ |
| 4 | TheHive + Cortex + MISP | 📋 |
| 5 | Multi-agent + RAG memory + ML | 📋 |
| 6 | Autonomous response | 📋 |

---

## Docs

- [Setup Guide](docs/setup-guide.md)
- [Architecture](docs/architecture.md)
- [AI Playbook](docs/airia-playbook.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Changelog](CHANGELOG.md)

---

## Credits

[Airia](https://airia.com) · [Wazuh](https://wazuh.com) · [tshark](https://wireshark.org) · [MITRE ATT&CK](https://attack.mitre.org) · [Royden Rahul Rebello](https://www.linkedin.com/in/roydensprofile/)
