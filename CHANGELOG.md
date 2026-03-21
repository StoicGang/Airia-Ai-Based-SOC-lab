# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2025

### Added
- End-to-end SOC pipeline: tshark capture → CSV analysis → JSON alert → Airia AI
- `soc_monitor.py` — 5-step automation script
- `python-dotenv` credential management — no hardcoded secrets
- `.env.example` template for safe credential sharing
- SOC playbook with 10 sections: validation, classification, risk scoring,
  MITRE mapping, action plan, escalation logic, executive summary
- Clean formatted SOC report output with risk icons and word-wrapped text
- Automatic `soc_report.json` saved to `logs/` on each run
- `validate_config()` — fails clearly if `.env` is missing or unconfigured
- ICMP flood detection using packet count threshold
- MITRE ATT&CK technique mapping in AI response
- Reverse DNS hostname resolution for source IPs

### Security
- All credentials moved from source code to `.env` file
- `.gitignore` blocks `.env`, `logs/`, and all pcap/csv files from being committed

---

## [Unreleased] — Planned

### Planned
- SQLite database for storing historical alerts and trend analysis
- Flask web dashboard for visualising results
- Support for TCP SYN flood and UDP flood detection
- Sysmon integration for process-level endpoint detection
- Email/Slack alerting when escalation is required
- Multi-source IP detection (distributed attack pattern)
- Docker support for containerised deployment
