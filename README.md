# 🛡️ AI-Powered SOC Analyst Lab

An automated Security Operations Center (SOC) lab that simulates real-world attack detection and AI-driven threat analysis — built entirely on free tools.

> **Built for learning.** This lab demonstrates how modern SOC pipelines work: network capture → multi-attack detection → AI analysis → persistent threat reporting with a live web dashboard.

---

## 📸 Demo

```
=======================================================
  AIRIA SOC MONITOR v2
  Rule      : RULE-001 — ICMP Flood
  Target    : 192.168.56.20
  Interface : eth0
  Window    : 100s  |  Threshold : 40
=======================================================

[Capture] ⚡ Send your attack NOW — 100 seconds to capture...

[Analyze] Traffic summary for rule: ICMP Flood
    192.168.56.10        85 packets  █████████████████  ← ALERT

[!] Alert: 192.168.56.10 (85 > threshold 40)

============================================================
  🛡️  AIRIA SOC ANALYSIS REPORT
============================================================
  Alert ID    : SOC-2E867F0A
  Risk Level  : 🟠 High
  Risk Score  : 65/100
  Confidence  : High
  Escalate    : ✅ No
  MITRE       : T1498 — Network Denial of Service

  Summary: A notable ICMP traffic spike was detected from
  192.168.56.10. Volume exceeds policy thresholds and
  warrants analyst review.
============================================================
[DB] Alert saved: SOC-2E867F0A
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              VirtualBox — Host-Only Network               │
│                        192.168.56.x                       │
│                                                           │
│  ┌──────────────────┐  ICMP/TCP/Scan  ┌────────────────┐ │
│  │  Windows 10 VM   │ ──────────────► │  Kali Linux VM │ │
│  │  192.168.56.10   │                 │  192.168.56.20 │ │
│  │  (Attacker)      │                 │  (SOC Monitor) │ │
│  └──────────────────┘                 └───────┬────────┘ │
└──────────────────────────────────────────────-┼──────────┘
                                                │ tshark → Python
                                                ▼
                                    ┌───────────────────┐
                                    │   SQLite DB       │
                                    │   alerts / iocs   │
                                    │   sessions        │
                                    └─────────┬─────────┘
                                              │
                            ┌─────────────────┴──────────────┐
                            │                                │
                    ┌───────▼──────┐              ┌──────────▼──────┐
                    │  Airia AI    │              │  Flask Dashboard │
                    │  SOC Analyst │              │  :5000 (live)   │
                    └──────────────┘              └─────────────────┘
```

**Pipeline:**
```
tshark (rule-filtered) → PCAP → CSV → threshold analysis
  → alert.json → Airia AI → SOC report → SQLite → Dashboard
```

---

## ⚙️ Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Attacker VM | Windows 10 | Generate ICMP / TCP / port-scan traffic |
| SOC Monitor | Kali Linux | tshark capture + Python pipeline |
| Packet capture | tshark | Capture and parse network packets |
| Detection engine | Python + YAML rules | Threshold-based multi-attack detection |
| AI Analysis | Airia (GPT-4o mini) | SOC triage with structured playbook |
| Persistence | SQLite 3 | Store every alert, session, and IOC |
| Dashboard | Flask | Live web UI at `http://192.168.56.20:5000` |
| Credentials | python-dotenv | Secure config management |
| Virtualisation | VirtualBox | Host both VMs |

---

## 🚀 Quick Start

### Prerequisites
- VirtualBox installed
- Two VMs: Kali Linux + Windows 10 on Host-Only network `192.168.56.x`
- Free [Airia](https://airia.com) account with a project created
- Python 3.9+ on Kali

### 1. Clone the repository
```bash
git clone https://github.com/StoicGang/Airia-Ai-Based-SOC-lab.git
cd Airia-Ai-Based-SOC-lab
```

### 2. Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials
```bash
cp config/.env.example config/.env
nano config/.env
```

### 4. Install tshark
```bash
sudo apt install tshark -y
sudo usermod -aG wireshark $USER
# Log out and back in
```

### 5. Initialise the database
```bash
python database/db_manager.py
# Expected: [DB] Initialized | Total alerts: 0
```

### 6. Run the monitor
```bash
# Default — ICMP flood (RULE-001)
sudo python scripts/soc_monitor_v2.py

# Target a different attack type
sudo python scripts/soc_monitor_v2.py --rule RULE-002   # TCP SYN flood
sudo python scripts/soc_monitor_v2.py --rule RULE-003   # Port scan

# List all available rules
python scripts/soc_monitor_v2.py --list
```

### 7. Trigger an attack (Windows VM)
```cmd
rem ICMP flood
ping 192.168.56.20 -n 200 -l 64

rem Port scan (nmap)
nmap -sS 192.168.56.20 -p 1-100
```

### 8. Open the dashboard
```bash
python dashboard/app.py
```
Browse to `http://192.168.56.20:5000` from your host machine.

---

## 📁 Project Structure

```
soc-lab/
│
├── scripts/
│   ├── soc_monitor.py          # Phase 1 — base ICMP pipeline (retained)
│   └── soc_monitor_v2.py       # Phase 2 — active pipeline (multi-attack + DB)
│
├── detection/
│   └── rules.py                # YAML-driven detection rule engine
│
├── database/
│   ├── schema.sql              # SQLite schema (alerts, sessions, iocs)
│   └── db_manager.py           # All database operations
│
├── dashboard/
│   ├── app.py                  # Flask web server
│   └── templates/
│       ├── index.html          # Live alert feed + stat cards
│       └── alert_detail.html   # Full AI report for one alert
│
├── config/
│   ├── .env                    # Your credentials (never committed)
│   ├── .env.example            # Template — safe to commit
│   └── detection_rules.yaml    # Attack detection rules (YAML)
│
├── tests/
│   └── test_db.py              # Unit tests (pytest)
│
├── logs/                       # Generated at runtime (gitignored)
│   ├── traffic.pcap
│   ├── traffic.csv
│   └── <ALERT_ID>_report.json
│
├── docs/
│   ├── architecture.md
│   ├── setup-guide.md
│   ├── airia-playbook.md
│   └── troubleshooting.md
│
├── AGENT_BRAIN.md              # Master roadmap for AI/human developers
├── CHANGELOG.md
├── CONTRIBUTING.md
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🔧 Configuration

All configuration lives in `config/.env`. Copy the example and fill in your values:

```bash
cp config/.env.example config/.env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRIA_API_URL` | Airia project execution URL | `https://api.airia.ai/v2/PipelineExecution/xxx` |
| `AIRIA_API_KEY` | Airia API key | `ak-xxxxxxxxxxxx` |
| `DESTINATION_IP` | IP of the monitored machine | `192.168.56.20` |
| `DESTINATION_HOST` | Descriptive name for the target | `Kali-SOC-Monitor` |
| `INTERFACE` | Network interface to capture on | `eth0` |
| `DB_PATH` | Path to the SQLite database | `/home/kali/soc-lab/database/soc_lab.db` |
| `RULES_PATH` | Path to the detection rules YAML | `/home/kali/soc-lab/config/detection_rules.yaml` |
| `FLASK_PORT` | Dashboard port | `5000` |
| `FLASK_HOST` | Dashboard bind address | `0.0.0.0` |

> ⚠️ Never commit `config/.env` — it is blocked by `.gitignore`.

---

## 🎯 Detection Rules & MITRE ATT&CK Coverage

Rules are defined in `config/detection_rules.yaml` and loaded at runtime. No code changes needed to add new rules.

| Rule ID | Attack Type | Protocol | Threshold | MITRE ID | Tactic |
|---------|-------------|----------|-----------|----------|--------|
| RULE-001 | ICMP Flood | ICMP | 40 packets / 100s | T1498 | Impact |
| RULE-002 | TCP SYN Flood | TCP | 80 SYN packets / 60s | T1498.001 | Impact |
| RULE-003 | Port Scan | TCP | 15 unique ports / 30s | T1046 | Discovery |

---

## 🤖 AI SOC Playbook

The Airia agent uses a structured 10-section playbook that enforces:

| # | Section | What it does |
|---|---------|--------------|
| 1 | Input validation | Checks all required alert fields |
| 2 | Threat classification | One of 6 categories (DoS, Scanning, etc.) |
| 3 | Risk scoring | 0–100 weighted model |
| 4 | MITRE ATT&CK mapping | Tactic + technique ID |
| 5 | Action plan | Tier 1 analyst steps |
| 6 | Escalation logic | Auto-escalate at score ≥ 80 |
| 7 | Executive summary | Plain English, no jargon |
| 8 | Strict JSON output | Structured and parseable every time |
| 9 | Confidence level | Low / Medium / High |
| 10 | Guardrails | No fabrication, defensive only |

Full playbook: [`docs/airia-playbook.md`](docs/airia-playbook.md)

---

## 🗺️ Lab Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Base pipeline — ICMP detection → Airia AI | ✅ Complete |
| Phase 2 | Persistence + multi-attack + Flask dashboard | ✅ Complete |
| Phase 3 | Wazuh SIEM integration (Docker) | 📋 Planned |
| Phase 4 | TheHive + Cortex + MISP case management | 📋 Planned |
| Phase 5 | Multi-agent mesh + RAG memory | 📋 Planned |
| Phase 6 | Near-autonomous SOC response | 📋 Planned |

See [`AGENT_BRAIN.md`](AGENT_BRAIN.md) for the full technical roadmap.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output: 4 tests passing in `tests/test_db.py` (save, duplicate, stats, recent alerts).

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup-guide.md) | Complete VM and environment setup |
| [Architecture](docs/architecture.md) | Deep dive into each component |
| [Airia Playbook](docs/airia-playbook.md) | The full SOC playbook used by the AI |
| [Troubleshooting](docs/troubleshooting.md) | Known errors and exact fixes |
| [AGENT_BRAIN.md](AGENT_BRAIN.md) | Master roadmap for developers and AI agents |

---

## 🤝 Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🙏 Credits

- [Airia AI Platform](https://airia.com) — AI agent orchestration
- [Wireshark / tshark](https://wireshark.org) — Network packet capture
- [MITRE ATT&CK](https://attack.mitre.org) — Threat intelligence framework
- [Royden Rahul Rebello](https://www.linkedin.com/in/roydensprofile/) — YouTube guidance
