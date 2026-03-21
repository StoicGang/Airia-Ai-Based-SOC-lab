# 🛡️ AI-Powered SOC Analyst Lab (AIRIA-style)

An automated Security Operations Center (SOC) lab that simulates real-world attack detection and AI-driven threat analysis — built entirely on free tools.

> **Built for learning.** This lab demonstrates how modern SOC pipelines work: network capture → detection → AI analysis → structured threat report.

---

## 📸 Demo

```
=======================================================
  AIRIA SOC MONITOR — Starting
  Target:    192.168.56.20
  Interface: eth0
  Threshold: 40 packets
=======================================================
[+] Capturing on eth0 for 100s...

[+] Traffic volume per source IP:
    192.168.56.10        85 packets  █████████████████  ← ALERT

[!] Suspicious IP detected: 192.168.56.10 (85 packets > threshold 40)
[+] Sending alert to Airia SOC Agent...

══════════════════════════════════════════════════════════════
  🛡️  AIRIA SOC ANALYSIS REPORT
══════════════════════════════════════════════════════════════
  Alert ID         : SOC-2E867F0A
  Classification   : Suspicious Network Volume
  Risk Level       : 🟠 High
  Risk Score       : 65 / 100
  Confidence       : High
  Escalate Now     : ✅ No

  MITRE ATT&CK:
    Tactic     : Discovery
    Technique  : T1046 — Network Service Scanning

  Executive Summary:
    A notable ICMP traffic spike was detected from
    192.168.56.10 to 192.168.56.20. The volume exceeds
    policy thresholds and warrants analyst review.
══════════════════════════════════════════════════════════════
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              VirtualBox — Host-Only Network              │
│                      192.168.56.x                        │
│                                                          │
│  ┌──────────────────┐   ICMP    ┌──────────────────┐    │
│  │  Windows 10 VM   │ ────────► │  Kali Linux VM   │    │
│  │  192.168.56.10   │   flood   │  192.168.56.20   │    │
│  │  (Attacker)      │           │  (SOC Monitor)   │    │
│  └──────────────────┘           └────────┬─────────┘    │
└───────────────────────────────────────────┼──────────────┘
                                            │ HTTPS
                                            ▼
                                 ┌─────────────────────┐
                                 │   Airia Cloud AI    │
                                 │   (SOC Analyst)     │
                                 │                     │
                                 │  ► Classify threat  │
                                 │  ► Score risk 0-100 │
                                 │  ► MITRE mapping    │
                                 │  ► Response actions │
                                 │  ► Exec summary     │
                                 └─────────────────────┘
```

**Pipeline (5 steps):**
```
tshark capture → PCAP → CSV → packet analysis → alert.json → Airia AI → SOC report
```

---

## ⚙️ Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Attacker VM | Windows 10 | Generates ICMP flood traffic |
| SOC Monitor | Kali Linux | tshark capture + Python pipeline |
| Packet capture | tshark | Capture and parse network traffic |
| Automation | Python 3 | Orchestrate the full pipeline |
| AI Analysis | Airia (GPT-4o mini) | SOC triage with playbook |
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
git clone https://github.com/YOUR-USERNAME/soc-lab.git
cd soc-lab
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
Fill in your Airia API URL and Key. See [Configuration](#configuration) below.

### 4. Install tshark
```bash
sudo apt install tshark -y
sudo usermod -aG wireshark $USER
# Log out and back in
```

### 5. Run the monitor
```bash
sudo python scripts/soc_monitor.py
```

### 6. Trigger the attack (Windows VM)
```cmd
ping 192.168.56.20 -n 200 -l 64
```

---

## 📁 Project Structure

```
soc-lab/
│
├── scripts/
│   └── soc_monitor.py        # Main pipeline script
│
├── config/
│   ├── .env                  # Your credentials (never committed)
│   └── .env.example          # Template — safe to commit
│
├── logs/                     # Generated at runtime (gitignored)
│   ├── traffic.pcap
│   ├── traffic.csv
│   ├── alert.json
│   └── soc_report.json
│
├── docs/
│   ├── architecture.md       # Detailed architecture notes
│   ├── setup-guide.md        # Full step-by-step setup
│   ├── airia-playbook.md     # The SOC playbook used by the AI
│   └── troubleshooting.md    # Known errors and fixes
│
├── .gitignore
├── requirements.txt
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md                 # This file
```

---

## 🔧 Configuration

All configuration is loaded from `config/.env`. Copy the example file and fill in your values:

```bash
cp config/.env.example config/.env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRIA_API_URL` | Your Airia project execution URL | `https://api.airia.ai/v2/PipelineExecution/xxx` |
| `AIRIA_API_KEY` | Your Airia API key | `ak-xxxxxxxxxxxx` |
| `DESTINATION_IP` | IP of the machine being monitored | `192.168.56.20` |
| `DESTINATION_HOST` | Descriptive name for the target | `Kali-SOC-Monitor` |
| `INTERFACE` | Network interface to capture on | `eth0` |
| `CAPTURE_DURATION` | How long to capture in seconds | `100` |
| `THRESHOLD` | Packets from one IP to trigger alert | `40` |

> ⚠️ Never commit `config/.env` — it is in `.gitignore` by default.

---

## 🤖 AI SOC Playbook

The Airia agent uses a structured 10-section playbook that enforces:

1. **Input validation** — checks all required alert fields
2. **Threat classification** — one of 6 categories (Brute Force, Scanning, etc.)
3. **Risk scoring** — 0–100 weighted model with clear calculation
4. **MITRE ATT&CK mapping** — tactic + technique ID
5. **Action plan** — Tier 1 analyst steps
6. **Escalation logic** — automatic at score ≥ 80
7. **Executive summary** — plain English, no jargon
8. **Strict JSON output** — structured, parseable every time
9. **Confidence level** — Low/Medium/High based on data completeness
10. **Guardrails** — no fabrication, no attack instructions, defensive only

Full playbook: [`docs/airia-playbook.md`](docs/airia-playbook.md)

---

## 🎯 MITRE ATT&CK Coverage

This lab currently detects and maps to:

| Technique | ID | Tactic |
|-----------|-----|--------|
| Network Denial of Service | T1498 | Impact |
| Network Service Scanning | T1046 | Discovery |
| Application Layer Protocol | T1071 | C&C |

---

## 🔬 Extending the Lab

This is a base lab designed to be extended. Ideas to try:

- **Different attack types** — replace ICMP with TCP SYN flood, UDP flood, or port scanning
- **Lower the threshold** — change `THRESHOLD=10` for high-sensitivity mode
- **Add Sysmon** — install Sysmon on Windows VM for process-level detection
- **Add a database** — store all alerts in SQLite for trend analysis
- **Add a dashboard** — build a Flask web UI to visualise results
- **Wazuh integration** — replace tshark with full SIEM agent forwarding
- **Email alerts** — send notification when escalation is required

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup-guide.md) | Complete VM and environment setup |
| [Architecture](docs/architecture.md) | Deep dive into how each component works |
| [Airia Playbook](docs/airia-playbook.md) | The full SOC playbook used by the AI |
| [Troubleshooting](docs/troubleshooting.md) | Known errors and exact fixes |

---

## 🤝 Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

---

## 🙏 Credits

- [Airia AI Platform](https://airia.com) — AI agent orchestration
- [Wireshark / tshark](https://wireshark.org) — Network packet capture
- [Royden Rahul Rebello](https://www.linkedin.com/in/roydensprofile/) — Youtube Guidance
- [MITRE ATT&CK](https://attack.mitre.org) — Threat framework
- [SwiftOnSecurity Sysmon Config](https://github.com/SwiftOnSecurity/sysmon-config) — Endpoint detection reference
