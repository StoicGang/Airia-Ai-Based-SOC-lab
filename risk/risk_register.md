# 🛡️ Airia SOC Lab — Risk Register

> **Version:** 1.0  
> **Last Updated:** 2026-04-08  
> **Owner:** SOC Lab Engineering Team  
> **Review Cycle:** Every phase milestone or quarterly  
> **Methodology:** See [risk_methodology.md](risk_methodology.md)

---

## Risk Scoring Reference

| Likelihood | Impact | Score Range | Risk Level |
|:----------:|:------:|:-----------:|:----------:|
| 1 = Rare | 1 = Negligible | 1–4 | 🟢 Low |
| 2 = Unlikely | 2 = Minor | 5–9 | 🟡 Medium |
| 3 = Possible | 3 = Moderate | 10–15 | 🟠 High |
| 4 = Likely | 4 = Major | 16–20 | 🔴 Critical |
| 5 = Almost Certain | 5 = Catastrophic | 21–25 | 🔴 Critical |

**Formula:** Risk Score = Likelihood × Impact

---

## Active Risk Register

### Network Detection Pipeline (Phases 1–2)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-001 | tshark capture pipeline | Capture failure / packet loss | No health check on tshark subprocess; silent failure if interface goes down | 3 | 4 | 12 | 🟠 High | Mitigate | Implement process watchdog with auto-restart; add heartbeat logging every 60s; alert on zero-packet windows | Engineering | Open | Monitor tshark PID and packet-count delta | Low — watchdog covers most failure scenarios |
| R-002 | CSV parser | Malformed CSV injection | Parser does not sanitize tshark output; crafted packets could produce CSV fields that break parsing | 2 | 3 | 6 | 🟡 Medium | Mitigate | Validate CSV schema before processing; reject rows with unexpected column counts; log and quarantine malformed files | Engineering | Open | Schema validation errors in parse log | Low |
| R-003 | Detection rule engine | False negatives in detection | Static thresholds may miss low-and-slow attacks or attacks just below threshold | 4 | 4 | 16 | 🔴 Critical | Mitigate | Tune thresholds quarterly based on baseline traffic analysis; add ML anomaly detection in Phase 5; implement rule coverage reporting | Engineering | Open | Periodic detection gap analysis; red team exercises | Medium — threshold tuning helps but novel attacks remain a gap |
| R-004 | Detection rule engine | False positives / alert fatigue | Thresholds too sensitive for network conditions; operators ignore real alerts | 3 | 3 | 9 | 🟡 Medium | Mitigate | Implement adaptive baselines per-source-IP; add analyst feedback loop (Phase 6) to tune scores; provide alert suppression for known-good IPs | Engineering | Open | Track false positive rate per rule in dashboard stats | Low — feedback loop progressively reduces FPs |
| R-005 | Pipeline: tshark → CSV → AI → DB | End-to-end pipeline failure | No orchestration or retry logic; single component failure silently drops alerts | 3 | 5 | 15 | 🟠 High | Mitigate | Add pipeline health endpoint; implement dead-letter queue for failed AI calls; retry with exponential backoff; add `pipeline_status` table to SQLite | Engineering | Open | Pipeline health dashboard widget; dead-letter queue depth metric | Medium — retries help but prolonged AI outages still cause data loss |

---

### AI Analysis Engine (Phases 1–2)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-006 | Airia AI agent | AI hallucination / incorrect threat classification | LLM may generate plausible but wrong classifications, MITRE mappings, or risk scores | 4 | 4 | 16 | 🔴 Critical | Mitigate | Enforce structured JSON output with schema validation; cross-check MITRE IDs against known technique list; implement confidence thresholds — reject results below confidence=Medium; log all raw AI responses for audit | Engineering | Open | Schema validation failures; MITRE ID validation; analyst overrides tracked | Medium — structured output reduces hallucination but edge cases persist |
| R-007 | Airia AI agent | Prompt injection via logs | Crafted packet payloads or log content could manipulate AI behavior when included in the analysis prompt | 3 | 4 | 12 | 🟠 High | Mitigate | Sanitize all log/packet data before embedding in prompts; truncate payload fields to 256 chars; use a fixed system prompt that instructs the AI to ignore meta-instructions in data; validate output structure regardless of input | Engineering | Open | Output format deviation detection; prompt audit logging | Medium — sanitization reduces risk but novel injection vectors may emerge |
| R-008 | Airia API | API rate limiting / outage | External API dependency with no SLA in lab environment; Airia outage halts all analysis | 3 | 3 | 9 | 🟡 Medium | Mitigate | Implement API call retry with backoff; queue alerts during outage for later processing; add a local fallback rule-based scorer for critical alerts when AI is unavailable | Engineering | Open | API response time monitoring; error rate tracking | Low |

---

### Database & Dashboard (Phase 2)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-009 | SQLite database | Data integrity issues | No input validation on DB writes; concurrent writes may corrupt WAL; no backup mechanism | 3 | 4 | 12 | 🟠 High | Mitigate | Enable WAL mode for concurrent reads; validate all dict fields before `save_alert()`; implement daily automated backup to `database/backups/`; add integrity check on startup (`PRAGMA integrity_check`) | Engineering | Open | Startup integrity check; backup job status monitoring | Low |
| R-010 | Flask dashboard | Authentication bypass | Dashboard runs on 0.0.0.0:5000 with no authentication; anyone on host-only network can view/modify data | 4 | 4 | 16 | 🔴 Critical | Mitigate | Add basic auth or token-based access control; bind to 127.0.0.1 unless explicitly exposed; add session management with timeout; implement CSRF tokens on forms | Engineering | Open | Access log review; unauthorized request monitoring | Medium — basic auth is a stopgap; full RBAC needed for production |
| R-011 | Flask dashboard | Cross-site scripting (XSS) | AI-generated report content rendered in templates without proper escaping; attacker-controlled IPs/payloads in alert data | 3 | 3 | 9 | 🟡 Medium | Mitigate | Use Jinja2 auto-escaping (enabled by default); explicitly sanitize all dynamic content in `alert_detail.html`; implement Content-Security-Policy headers; never use `| safe` filter on untrusted data | Engineering | Open | CSP violation reports; periodic manual XSS testing | Low |
| R-012 | Flask dashboard | Information exposure | Debug mode enabled in development; stack traces and config exposed on error | 2 | 3 | 6 | 🟡 Medium | Mitigate | Set `debug=False` in production; create separate dev/prod configs; implement custom error handlers (404, 500); never expose `.env` or API keys in error responses | Engineering | Open | Error page content review; config audit | Low |
| R-013 | SQLite database | Missing audit logging | No record of who accessed what data, when alerts were modified, or dashboard queries | 3 | 3 | 9 | 🟡 Medium | Mitigate | Add `audit_log` table (timestamp, action, user/system, details); log all write operations, configuration changes, and API access; implement log rotation | Engineering | Open | Audit log completeness review | Low |

---

### SIEM Integration (Phase 3)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-014 | Wazuh Manager | Agent communication failure | Agent may disconnect silently; alerts lost during network outage between VMs | 3 | 3 | 9 | 🟡 Medium | Mitigate | Configure agent keep-alive monitoring in Wazuh; set `notify_time` and `time-reconnect` in agent config; alert on agent disconnect via Wazuh rule 503 | Engineering | Open | Wazuh agent status dashboard; disconnected agent alerts | Low |
| R-015 | custom-w2airia.py | Wazuh-to-Airia forwarding failure | Script has no supervisor; crash silently loses host-based alerts | 3 | 4 | 12 | 🟠 High | Mitigate | Run as systemd service with restart policy; implement failed delivery journal (`w2airia-failed.jsonl`); add health check endpoint; queue alerts during Airia outage | Engineering | Open | Systemd service status; failed delivery file size monitoring | Medium |
| R-016 | Wazuh Docker stack | Container resource exhaustion | Docker containers may consume all disk (indexer data) or memory without limits | 2 | 4 | 8 | 🟡 Medium | Mitigate | Set Docker resource limits (`mem_limit`, `cpus`); configure index lifecycle management in Wazuh Indexer; monitor disk usage; set alerting at 80% capacity | Engineering | Open | Docker stats monitoring; disk utilization alerts | Low |
| R-017 | System infrastructure | Lack of monitoring of system failures | No centralized monitoring of pipeline components, services, or resource utilization | 4 | 3 | 12 | 🟠 High | Mitigate | Implement health check script that validates: tshark running, Flask up, Wazuh containers healthy, SQLite writable, API reachable; run every 5 minutes via cron; push status to dashboard `/health` endpoint | Engineering | Open | Health check cron output; dashboard health widget | Medium |

---

### Case Management & Threat Intel (Phase 4)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-018 | TheHive | Alert ingestion failure | API connectivity issues or schema changes break alert-to-case pipeline | 3 | 3 | 9 | 🟡 Medium | Mitigate | Validate TheHive API connectivity before forwarding; implement retry with backoff; queue failed alerts; version-pin TheHive API client | Engineering | Open | Ingestion success rate metric; queued alert count | Low |
| R-019 | TheHive | Duplicate alert creation | Same Wazuh alert forwarded multiple times creates duplicate cases | 3 | 2 | 6 | 🟡 Medium | Mitigate | Use `sourceRef` deduplication in TheHive; check for existing case before creation; implement idempotent alert handling | Engineering | Open | Duplicate case detection query | Low |
| R-020 | Cortex | Incorrect automated response | Cortex analyzer returns wrong enrichment or triggers wrong responder action | 2 | 5 | 10 | 🟠 High | Mitigate | Validate analyzer output before acting; require human approval for responder actions above severity 3; log all Cortex decisions for audit; implement analyzer result confidence scoring | Engineering | Open | Cortex action audit log; analyst override rate | Medium |
| R-021 | MISP | Threat intelligence poisoning | Compromised or low-quality MISP feeds introduce bad IOCs, causing false positives or missed threats | 2 | 4 | 8 | 🟡 Medium | Mitigate | Vet MISP feeds before subscribing; implement IOC confidence scoring; require minimum sighting count before auto-action; regularly audit IOC quality | Engineering | Open | IOC false positive rate; feed quality metrics | Medium |
| R-022 | TheHive | Case misclassification | AI severity mapping produces wrong TheHive case priority; analysts work low-priority cases first | 3 | 3 | 9 | 🟡 Medium | Mitigate | Cross-validate AI risk level with rule severity before mapping; allow analyst override of case priority; track reclassification rate as quality metric | Engineering | Open | Case reclassification rate tracking | Low |

---

### Multi-Agent & ML System (Phase 5)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-023 | ML anomaly detector | Model drift | Detection model degrades as network baselines shift; false positive/negative rates increase over time | 4 | 3 | 12 | 🟠 High | Mitigate | Schedule monthly model retraining on latest confirmed-threat data; track precision/recall metrics per retraining cycle; alert when detection rate drops below threshold; maintain model version history | Engineering | Open | Model performance metrics dashboard; detection rate trending | Medium |
| R-024 | ChromaDB / training data | Data poisoning | Attacker manipulates traffic patterns to train the model on malicious baselines; false negatives increase | 2 | 5 | 10 | 🟠 High | Mitigate | Validate training data provenance; require analyst confirmation before data enters training set; implement anomaly detection on the training data itself; maintain clean baseline dataset | Engineering | Open | Training data audit; model prediction divergence analysis | Medium |
| R-025 | ChromaDB vector store | Memory corruption / data loss | ChromaDB persistence fails silently; vector store becomes inconsistent with SQLite | 2 | 3 | 6 | 🟡 Medium | Mitigate | Regular ChromaDB backups alongside SQLite; implement consistency check between ChromaDB and alerts table; add error handling on all vector store operations | Engineering | Open | Backup verification; consistency check script | Low |
| R-026 | Multi-agent orchestrator | Over-reliance on AI decisions | SOC team trusts AI output without verification; critical context missed by all agents | 3 | 4 | 12 | 🟠 High | Mitigate | Mandate human review for all Critical-severity alerts; display AI confidence prominently; implement "AI Disagree" workflow when agents conflict; track analyst override rate as a system health metric | Engineering | Open | Analyst override rate; AI-vs-human decision concordance tracking | Medium |

---

### Autonomous Response (Phase 6)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| R-027 | Auto-response engine | Wrong automated blocking | Legitimate IP blocked due to false positive; service disruption for real users | 3 | 5 | 15 | 🟠 High | Mitigate | Default to `DRY_RUN=true`; maintain IP whitelist for critical services; require dual-condition trigger (AI + rule match) for auto-block; implement auto-unblock after review period; log every action with undo command | Engineering | Open | Blocked IP audit; false block rate tracking; response action log review | Medium |
| R-028 | Auto-response engine | Automation misuse / abuse | Attacker triggers automated response against arbitrary targets; denial of service via defensive tools | 2 | 5 | 10 | 🟠 High | Mitigate | Rate-limit automated actions (max 5 blocks/hour); require human approval for actions affecting multiple IPs; validate source of trigger; implement action cooldown period per target | Engineering | Open | Action rate monitoring; manual approval queue depth | Medium |
| R-029 | Auto-response engine | Privilege escalation via response scripts | Response scripts run with sudo/root; compromised script = full system access | 2 | 5 | 10 | 🟠 High | Mitigate | Run response scripts with minimal privileges using dedicated service account; use capabilities instead of full root; validate all commands against allowlist before execution; audit script integrity on startup | Engineering | Open | Script integrity hash verification; privilege audit | Medium |
| R-030 | Autonomous response system | Lack of human oversight | Fully automated loop with no circuit breaker; cascading wrong actions | 2 | 5 | 10 | 🟠 High | Mitigate | Implement mandatory human-in-the-loop for severity >= Critical; add global kill switch on dashboard; cap automated actions per hour; send notification to SOC team for every automated action | Engineering | Open | Kill switch functionality test; notification delivery verification | Medium |
| R-031 | Alert pipeline | Alert fatigue / overload | High volume of low-value alerts overwhelms operators; critical alerts buried | 4 | 4 | 16 | 🔴 Critical | Mitigate | Implement alert aggregation (group similar alerts); add severity-based notification routing; provide alert summary digest instead of individual notifications; tune detection thresholds; create "Top 10 Critical" dashboard view | Engineering | Open | Alert volume trending; mean-time-to-acknowledge metric; analyst workload dashboard | Medium — volume reduction helps but high-activity periods remain challenging |

---

### Infrastructure & Governance (Cross-Phase)

| ID | Asset | Threat | Vulnerability | L | I | Score | Level | Treatment | Control / Mitigation | Owner | Status | Detection Method | Residual Risk |
|----|-------|--------|---------------|:-:|:-:|:-----:|:-----:|-----------|----------------------|-------|--------|------------------|---------------|
| ID-001 | Host Machine (Lab Environment) | Malicious actor exploiting VM internet exposure | Manual configuration leading to VM escape vulnerabilities | 1 | 5 | 5 | 🟡 Medium | Tolerate | Cost/benefit analysis favours acceptance for a solo lab; VMs run on host-only networking with no bridged internet access; VirtualBox updated to latest stable release | Engineering | Open | VirtualBox version audit; VM network adapter config review | Low — lab-only scope limits exposure |
| ID-002 | AI API Tokens | Accidental leak (GitHub) or local malicious actor | Hardcoded secrets in configuration files | 4 | 5 | 20 | 🔴 Critical | Mitigate | Secrets management via `.env` isolation and `.gitignore`; pre-commit hook scanning for leaked tokens; rotate keys quarterly; never log API keys in plaintext | Engineering | In Progress | `.gitignore` coverage audit; `git log` secret scan (`trufflehog` / `gitleaks`) | Medium — `.env` pattern works but key rotation discipline required |
| ID-003 | SQLite 3 Database | External entity with low-privilege access | Weak file permissions / missing least privilege | 1 | 2 | 2 | 🟢 Low | Mitigate | Scripted access control and file ownership restriction (`chmod 640`); DB file owned by dedicated `soc-lab` user; no world-readable permissions | Engineering | Open | File permission audit script; `ls -la` check on DB path | Low |
| ID-004 | Flask Dashboard (Port 5000) | Unauthorized device on the local network | Missing network restrictions / no authentication | 3 | 2 | 6 | 🟡 Medium | Mitigate | Network security management — IP whitelisting via iptables; bind to `127.0.0.1` for local-only access or whitelist `192.168.56.0/24`; port firewall rules on Kali | Engineering | Open | Port scan of Kali from external interface; firewall rule audit | Low |
| ID-005 | Airia AI Pipeline (OpenAPI) | Compromised internal host causing an alert flood | Missing outbound API rate limiting / payload filtering | 4 | 5 | 20 | 🔴 Critical | Mitigate | Secure system architecture — implement rate limits in `soc_monitor_v2.py` (max 10 API calls/min); payload size cap (4 KB per request); input validation before API submission; alert on anomalous call volume | Engineering | Open | API call rate dashboard metric; payload size logging | Medium — rate limits cap abuse but compromised host may still exhaust quota |
| ID-006 | Kali VM Storage | Unmanaged log generation (resource exhaustion) | Missing log rotation / no data retention limits | 3 | 2 | 6 | 🟡 Medium | Mitigate | Capacity management and log retention policies — `logrotate` config for `/home/kali/soc-lab/logs/`; cron job to purge files older than 30 days; disk usage alert at 80% | Engineering | Open | `df -h` monitoring; cron job execution log | Low |
| ID-007 | custom-w2airia.py | Malformed log data causing an unhandled exception | Lack of code exception handling / no service monitoring | 3 | 3 | 9 | 🟡 Medium | Mitigate | Secure system engineering — wrap all parsing in `try/except` blocks with structured error logging; run as systemd service with `Restart=on-failure`; add health check endpoint | Engineering | Open | systemd service status; error log monitoring; restart count tracking | Low |
| ID-008 | Wazuh Dashboard | Unauthorized user on the local Wi-Fi | Default administrator credentials left in deployment config | 5 | 4 | 20 | 🔴 Critical | Mitigate | Secure authentication — change default `admin`/`SecretPassword` credentials immediately post-deploy; store credentials in `.env`; enforce password complexity; rotate credentials quarterly; document credential change procedure in setup guide | Engineering | Open | Credential audit; login attempt monitoring via Wazuh Dashboard logs | Medium — credentials changed but no MFA available on Wazuh Dashboard |
| ID-009 | YAML Detection Rules | Accidental developer misconfiguration | Improper threshold tuning causing false positive floods | 3 | 4 | 12 | 🟠 High | Mitigate | Change management — test rules in isolated environment before live deployment; peer review for rule changes; maintain rule changelog; implement rule validation script that checks threshold ranges | Engineering | Open | Rule change diff review; false positive rate per rule post-deployment | Low |
| ID-010 | Wazuh Agent | External attacker with local access | Missing least privilege / no service tamper protection | 3 | 5 | 15 | 🟠 High | Mitigate | Privileged access management and endpoint tamper protection — run agent as dedicated `ossec` user; restrict write access to agent config; enable Wazuh agent self-monitoring; alert on agent binary modification | Engineering | Open | Agent file integrity monitoring (FIM on agent binaries); service status alerts | Medium — tamper protection helps but local root access bypasses it |
| ID-011 | Host-Only Network | Compromised internal VM (Attacker) | ARP protocol lacks authentication (stateless) | 3 | 4 | 12 | 🟠 High | Mitigate | Network security management — implement static ARP entries for critical hosts (`192.168.56.20`, gateway); enable ARP spoofing detection via Wazuh RULE-005; monitor for duplicate MAC addresses | Engineering | Open | ARP table monitoring; Wazuh ARP spoof alerts (RULE-005) | Medium — static ARP helps but adds maintenance overhead |
| ID-012 | OpenAI API (via Airia) | Vendor outage or adverse policy change | Single point of failure / vendor lock-in | 3 | 4 | 12 | 🟠 High | Mitigate | Supplier relationship management and business continuity — review Airia/OpenAI ToS quarterly; abstract AI calls behind interface layer for easy provider swap; document fallback to local LLM (Ollama/llama.cpp) as contingency; monitor vendor status page | Engineering | Open | Vendor status page monitoring; API error rate trending | Medium — abstraction layer planned but not yet implemented |
| ID-013 | Python Dependencies | Malicious actor on PyPI | Blindly pulling unpinned/unverified package versions | 4 | 5 | 20 | 🔴 Critical | Mitigate | Technical vulnerability management — pin all versions in `requirements.txt`; run `pip-audit` before each phase deployment; use hash verification (`--require-hashes`); review dependency changelogs on updates; subscribe to security advisories for critical packages (Flask, requests) | Engineering | In Progress | `pip-audit` CI check; dependency version drift monitoring | Medium — pinning helps but transitive dependency attacks remain a gap |
| ID-014 | Lab Documentation | Unauthorized access to internal SOC playbooks | Lack of encryption or access control for documentation files | 2 | 3 | 6 | 🟡 Medium | Mitigate | Information classification and handling — store sensitive playbooks in private repo or encrypted vault; classify documents (Public / Internal / Confidential); never commit credentials or internal IPs to public-facing docs | Engineering | Open | Repository visibility audit; document classification review | Low |
| ID-015 | Compliance (Data Privacy) | Accidental upload of PII to AI model | Lack of automated data masking/anonymization | 3 | 4 | 12 | 🟠 High | Mitigate | Data masking and privacy — implement regex-based PII scrubber (IPs, hostnames, usernames) in the pre-processing pipeline before AI submission; log what data is sent to the API; review Airia data retention policy; add PII detection unit test | Engineering | Open | PII detection test suite; API payload audit sampling | Medium — regex catches known patterns but novel PII formats may slip through |

---

## Summary Statistics

| Risk Level | Count | Percentage |
|:----------:|:-----:|:----------:|
| 🔴 Critical | 8 | 17% |
| 🟠 High | 17 | 37% |
| 🟡 Medium | 17 | 37% |
| 🟢 Low | 4 | 9% |
| **Total** | **46** | **100%** |

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-04-08 | 1.0 | SOC Lab Team | Initial comprehensive risk register covering Phases 1–6 |
| 2026-04-08 | 1.1 | SOC Lab Team | Added 15 infrastructure & governance risks (ID-001 through ID-015) covering host security, API tokens, credentials, supply chain, vendor dependencies, and data privacy |
