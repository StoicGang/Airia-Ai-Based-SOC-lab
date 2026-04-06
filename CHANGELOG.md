# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] — 2026-04-06

### Added
- **Wazuh SIEM deployment** — `docker/docker-compose.yml` updated
  - Wazuh Manager 4.14.4, Indexer 4.14.4, Dashboard 4.14.4 via Docker
  - Single-node stack with SSL certificates (auto-generated via `wazuh-certs-generator:0.0.4`)
  - Docker project name: `wazuh-soc`
  - Ports: 1514 (agent), 1515 (enrollment), 514/udp (syslog), 55000 (API), 443→5601 (dashboard), 9200 (indexer)
- **Wazuh agent enrollment** — Arch Linux (192.168.56.10) as `arch-workstation`
  - Agent installed via Docker image extraction method (CDN downloads blocked)
  - `integrations/wazuh/install_agent.sh` — multi-distro installer (Debian/RHEL/Arch) with `--uninstall` support
- **Wazuh → AIRIA integration pipeline** — end-to-end alert forwarding
  - `integrations/wazuh/custom-w2airia.py` — Wazuh integration script
    - Severity mapping: Wazuh levels 0-3→LOW, 4-6→MEDIUM, 7-9→HIGH, 10+→CRITICAL
    - MITRE ATT&CK enrichment, FIM data support, vulnerability data support
    - Fallback: writes to `.jsonl` if Flask dashboard is unreachable
  - `database/db_manager.py` — added `save_wazuh_alert()` function
    - Maps Wazuh normalized alerts to existing `alerts` table schema
    - IOC extraction: IPs, file paths (FIM), CVEs (vulnerability data)
  - `dashboard/app.py` — added `POST /api/alerts/ingest` endpoint
    - Receives JSON from Wazuh integration, validates, stores via `save_wazuh_alert()`
    - Returns alert ID on success (201), handles duplicates (409)
  - Dashboard version bumped to v3
- **Custom Wazuh detection rule** — `local_rules.xml`
  - Rule 100001: ICMP flood detection (level 10, MITRE T1498)
- **Phase 3 Development Guide** — `PHASE_3_DEV_GUIDE.md`
  - Architecture diagram, Docker image extraction method, all troubleshooting steps
  - Startup/shutdown procedures, credentials reference, verification checklist

### Changed
- `dashboard/app.py` — added `request` import, `save_wazuh_alert` import, health endpoint version v2→v3
- `database/db_manager.py` — added `uuid` import, Phase header updated to Phase 3
- `integrations/wazuh/custom-w2airia.py` — API URL changed from `localhost:5000/api/alerts` to `192.168.56.20:5000/api/alerts/ingest` (container→host networking)
- `AGENT_BRAIN.md` `CURRENT_STATE` — Phase 3 complete, Phase 4 ready

### Fixed
- Port 9200 conflict with old Docker stack — resolved by tearing down legacy containers
- Wazuh CDN `AccessDenied` — workaround via Docker image file extraction
- Agent permission errors — `chown -R root:wazuh /var/ossec` + `chmod -R 770`
- Duplicate agent registration — clean slate via `manage_agents -r` + DB wipe
- `requests` module missing in Wazuh container — installed via `ensurepip` + `pip3`

### Infrastructure
- Kali VM (192.168.56.20): Wazuh Manager + Indexer + Dashboard (Docker), Flask dashboard (port 5000)
- Arch VM (192.168.56.10): Wazuh agent (`arch-workstation`)
- Docker network: 172.19.0.0/16
- Disk cleanup: removed 10.2GB of unused Docker images

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
- TheHive + Cortex + MISP case management stack (Phase 4)
- Multi-agent orchestration with RAG memory (Phase 5)
- ML-based anomaly detection with scikit-learn Isolation Forest (Phase 5)
- Automated containment response engine with DRY_RUN mode (Phase 6)
- Analyst feedback loop updating ChromaDB memory (Phase 6)
- Scheduled threat hunting against AbuseIPDB (Phase 6)
