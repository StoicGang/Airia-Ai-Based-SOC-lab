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

## [2.0.0] — 2026-03-24

### Added
- **SQLite persistence layer** — `database/schema.sql` + `database/db_manager.py`
  - Three tables: `alerts`, `sessions`, `iocs` with full indexing
  - `init_db()`, `save_alert()`, `get_recent_alerts()`, `get_alert_by_id()`, `get_stats()`, `get_all_iocs()` functions
  - WAL journal mode for improved concurrent performance
  - IOC extraction and deduplication on every alert save
- **YAML-driven detection rule engine** — `detection/rules.py` + `config/detection_rules.yaml`
  - RULE-001: ICMP Flood (threshold 40 packets / 100s window) — T1498
  - RULE-002: TCP SYN Flood (threshold 80 SYN packets / 60s window) — T1498.001
  - RULE-003: Port Scan (threshold 15 unique destination ports / 30s window) — T1046
  - Configurable `count_field` to support both packet-count and unique-port-count analysis
- **Updated monitoring pipeline** — `scripts/soc_monitor_v2.py`
  - Replaces Phase 1 `soc_monitor.py` (backward compatible — RULE-001 is the default)
  - `--rule <ID>` flag to target any specific detection rule
  - `--list` flag to enumerate all loaded rules
  - Session tracking: each run creates a session row with start/end time, packet count, alert count
  - Automatically persists every Airia SOC report to SQLite after analysis
- **Flask web dashboard** — `dashboard/app.py` + `dashboard/templates/`
  - Live feed at `http://192.168.56.20:5000` — auto-refreshes every 30 seconds
  - `index.html`: stat cards (total alerts, avg risk, escalations, high+ severity) + sortable alert table
  - `alert_detail.html`: full AI report per alert — risk, MITRE mapping, executive summary, recommended actions
  - JSON API endpoints: `/api/alerts`, `/api/stats`, `/api/iocs`, `/health`
  - Dark theme with risk-level colour coding (Critical / High / Medium / Low)
- **Unit test suite** — `tests/test_db.py`
  - Tests: `test_save_alert`, `test_duplicate_alert`, `test_get_stats`, `test_get_recent_alerts`
  - Uses isolated temp DB — never touches the production database
- **New `.env` variables**: `DB_PATH`, `RULES_PATH`, `FLASK_PORT`, `FLASK_HOST`
- **`requirements.txt`** updated with: `pyyaml`, `pytest`, `flask`

### Changed
- `AGENT_BRAIN.md` `CURRENT_STATE` updated — active phase set to Phase 3

---

## [Unreleased] — Planned

### Planned
- Wazuh SIEM integration (Phase 3) — Docker-based deployment, Windows agent, custom rules
- TheHive + Cortex + MISP case management stack (Phase 4)
- Multi-agent orchestration with RAG memory (Phase 5)
- ML-based anomaly detection with scikit-learn Isolation Forest (Phase 5)
- Email/Slack alerting when escalation is required
- Docker support for containerised deployment
