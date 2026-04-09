# 🔮 Pre-Implementation Risk Plan — Phases 4, 5, and 6

> **Version:** 1.0  
> **Last Updated:** 2026-04-08  
> **Purpose:** Identify and plan for risks *before* implementation begins  
> **Methodology:** [risk_methodology.md](risk_methodology.md)

---

This document maps risks that **will be introduced** by Phases 4, 5, and 6. Each risk is assessed with a mitigation strategy so the engineering team can build defenses alongside the features, not as an afterthought.

---

## Phase 4 — TheHive + Cortex + MISP

**Scope:** Automated case management, observable enrichment, and threat intelligence sharing.

### P4-R1: Alert Ingestion Failure

| Field | Detail |
|-------|--------|
| **Description** | The Wazuh/Airia → TheHive bridge depends on API connectivity, correct auth tokens, and matching schemas. A TheHive API version change, expired API key, or network partition between Docker containers silently drops alerts. Cases are never created. Analysts have no visibility into the gap. |
| **Likelihood** | 3 — Possible. API changes are common across minor TheHive versions. Docker networking issues are frequent in multi-container stacks. |
| **Impact** | 4 — Major. Unprocessed alerts mean threats go uninvestigated. Compliance audit trail is broken. |
| **Risk Score** | 12 — 🟠 High |
| **Mitigation** | • Version-pin `thehive4py` and TheHive Docker image to tested versions<br>• Implement a pre-flight connectivity check on bridge startup<br>• Add retry logic with exponential backoff (3 attempts, max 60s)<br>• Queue failed alerts to `integrations/thehive/failed_alerts.jsonl` for manual replay<br>• Add ingestion success/failure count to the Flask dashboard stats page<br>• Create a Wazuh rule that fires when TheHive ingestion failure rate exceeds 10% in 5 minutes |

---

### P4-R2: Duplicate Alert Creation

| Field | Detail |
|-------|--------|
| **Description** | The same Wazuh alert or Airia report is forwarded to TheHive more than once — due to retry logic, script restart, or duplicate events from Wazuh. This creates duplicate cases that waste analyst time and skew metrics. |
| **Likelihood** | 3 — Possible. Retry logic without idempotency guarantees this will happen during error recovery. |
| **Impact** | 2 — Minor. No security impact, but operational noise reduces analyst efficiency. |
| **Risk Score** | 6 — 🟡 Medium |
| **Mitigation** | • Use `sourceRef` field in TheHive alerts for deduplication (TheHive rejects duplicates with same sourceRef)<br>• Generate `sourceRef` from a deterministic hash: `sha256(alert_id + timestamp + src_ip)`<br>• Before creating a case, query TheHive for existing alerts with the same sourceRef<br>• Log deduplicated alerts for metrics tracking |

---

### P4-R3: Incorrect Automated Response (Cortex)

| Field | Detail |
|-------|--------|
| **Description** | Cortex analyzers return enrichment data that is wrong (stale reputation DB, API errors returning partial data) or a Cortex responder takes an action based on incorrect enrichment. In the worst case, Cortex auto-blocks a legitimate service IP or marks a malicious domain as clean. |
| **Likelihood** | 2 — Unlikely. Cortex analyzers are well-tested, but free-tier APIs (VirusTotal, AbuseIPDB) have rate limits that can cause incomplete results. |
| **Impact** | 5 — Catastrophic. Wrong auto-response = legitimate service disrupted or malicious actor whitelisted. |
| **Risk Score** | 10 — 🟠 High |
| **Mitigation** | • Disable Cortex responders initially — use analyzers only for enrichment<br>• Validate analyzer output: check for error fields, empty results, low confidence scores<br>• Require human approval for any Cortex action with severity ≥ 3 (Medium+)<br>• Implement a "confidence floor" — ignore enrichment results with confidence < 0.6<br>• Log all Cortex analyzer invocations and results for audit<br>• Display Cortex enrichment quality score alongside results in the dashboard |

---

### P4-R4: Threat Intelligence Poisoning (MISP)

| Field | Detail |
|-------|--------|
| **Description** | MISP feeds from external communities may contain deliberately or accidentally wrong indicators. Poisoned IOCs cause: (a) false positives — legitimate traffic flagged as malicious, or (b) false negatives — attacker-controlled indicators added to whitelist feeds. If we auto-upgrade risk scores by +20 on MISP hits (as planned), a bad IOC directly inflates severity. |
| **Likelihood** | 2 — Unlikely. Established MISP communities have vetting, but free/open feeds have minimal quality control. |
| **Impact** | 4 — Major. Poisoned intel corrupts the entire analysis chain — AI produces wrong reports, TheHive prioritizes wrong cases, analysts investigate ghosts. |
| **Risk Score** | 8 — 🟡 Medium |
| **Mitigation** | • Start with curated, high-reputation MISP feeds only (e.g., CIRCL, Botvrij)<br>• Tag all MISP-sourced IOCs with their feed origin and confidence level<br>• Do not auto-upgrade risk score until MISP IOC has ≥ 2 sightings from independent sources<br>• Implement an IOC aging policy — auto-expire indicators older than 90 days unless reconfirmed<br>• Provide a dashboard view showing MISP hit rate vs. analyst confirmation rate (quality metric)<br>• Maintain a local override list to suppress known-bad MISP indicators |

---

### P4-R5: Case Misclassification

| Field | Detail |
|-------|--------|
| **Description** | The AI risk level → TheHive severity mapping produces incorrect case priority. An AI-assessed "Medium" alert creates a low-priority TheHive case when it should be high (or vice versa). Analysts triage in priority order, so misclassification directly affects response time for real threats. |
| **Likelihood** | 3 — Possible. AI hallucination risk (R-006) directly feeds this. Severity mapping is a hard problem with no ground truth in a lab. |
| **Impact** | 3 — Moderate. Worst case: a genuine Critical threat sits in the Medium queue for hours. |
| **Risk Score** | 9 — 🟡 Medium |
| **Mitigation** | • Implement dual-signal classification: both AI risk level AND detection rule severity must agree<br>• If signals disagree, escalate to higher severity (fail-safe)<br>• Add "AI Confidence" field to TheHive case custom fields — low confidence triggers manual review<br>• Track case reclassification rate — if > 15% of cases are reclassified by analysts, retune the mapping<br>• Quarterly review of severity mapping accuracy using closed-case data |

---

## Phase 5 — Multi-Agent + RAG Memory + ML

**Scope:** Specialized AI agents, persistent memory for context-aware analysis, and ML-based anomaly detection.

### P5-R1: Model Drift

| Field | Detail |
|-------|--------|
| **Description** | The Isolation Forest anomaly detector is trained on a baseline of "normal" traffic. Over time, network patterns change (new services, different traffic volumes, topology changes). The model's definition of "normal" becomes stale. Detection accuracy degrades — more false positives (old-normal flagged as anomalous) and false negatives (new-attack patterns accepted as normal). |
| **Likelihood** | 4 — Likely. Network baselines shift constantly, even in a lab. Any new VM, service, or test introduces new traffic patterns. |
| **Impact** | 3 — Moderate. Degraded ML doesn't crash the system — rule-based detection still works — but the ML layer becomes noise instead of signal. |
| **Risk Score** | 12 — 🟠 High |
| **Mitigation** | • Schedule model retraining monthly using the most recent 30 days of confirmed-clean traffic<br>• Track model metrics after each retraining: precision, recall, F1, false positive rate<br>• Alert when false positive rate exceeds 20% or recall drops below 70%<br>• Maintain versioned model snapshots — enable rollback if new model performs worse<br>• Display model performance metrics on the dashboard stats page<br>• Never use ML output alone for Critical-severity decisions — always require rule confirmation |

---

### P5-R2: Data Poisoning

| Field | Detail |
|-------|--------|
| **Description** | An attacker (or a misconfigured simulation) injects specifically crafted traffic into the training set. The model learns to treat attack patterns as "normal." Since the Isolation Forest is unsupervised, it has no labels to contradict poisoned samples. ChromaDB memory is similarly vulnerable — if false-positive alerts are stored without correction, the RAG context gives the AI wrong historical precedents. |
| **Likelihood** | 2 — Unlikely. Requires either attacker access to the training pipeline or a sustained low-and-slow campaign that avoids rule-based detection. |
| **Impact** | 5 — Catastrophic. Poisoned model = systematic false negatives. The ML layer actively hides attacks. |
| **Risk Score** | 10 — 🟠 High |
| **Mitigation** | • Never auto-add traffic samples to the training set — require analyst confirmation<br>• Implement data provenance: tag every training sample with source, timestamp, and confirmation status<br>• Maintain a "golden" baseline dataset that is manually curated and never auto-updated<br>• Run anomaly detection on the training data itself — flag statistical outliers before training<br>• For ChromaDB: only store alerts with analyst-confirmed outcomes (Confirmed Threat / Confirmed FP)<br>• Periodic integrity audit: compare model predictions against golden baseline |

---

### P5-R3: Memory Corruption

| Field | Detail |
|-------|--------|
| **Description** | ChromaDB vector store becomes corrupted or inconsistent with the SQLite alerts table. Possible causes: disk failure during write, interrupted embedding operation, version mismatch after ChromaDB upgrade. Result: RAG context returns wrong or empty historical data; AI loses institutional memory. |
| **Likelihood** | 2 — Unlikely. ChromaDB uses SQLite internally with WAL mode. But edge cases exist during crashes. |
| **Impact** | 3 — Moderate. System continues to function but without historical context. AI analysis quality degrades. |
| **Risk Score** | 6 — 🟡 Medium |
| **Mitigation** | • Schedule daily ChromaDB backup alongside SQLite backup<br>• Implement a consistency check: count ChromaDB documents vs. SQLite alerts — alert on mismatch<br>• Wrap all ChromaDB operations in try/except — log failures, don't crash the pipeline<br>• Document ChromaDB rebuild procedure from SQLite data (re-embed all historical alerts)<br>• Pin ChromaDB version and test upgrades in isolation before deploying |

---

### P5-R4: Over-Reliance on AI Decisions

| Field | Detail |
|-------|--------|
| **Description** | With four specialized agents (Triage, Enrichment, Threat Hunt, Response) all producing confident assessments, operators may trust the system without question. Confirmation bias increases — if all agents agree, the analyst assumes correctness even when all agents share the same blind spot (e.g., a novel attack type not in training data). This is the "automation complacency" problem. |
| **Likelihood** | 3 — Possible. Human nature: operators trust consistent confident output. Lab environments reinforce this because most alerts are simulated. |
| **Impact** | 4 — Major. A missed novel threat because all agents agreed it was benign. The system provides a false sense of security. |
| **Risk Score** | 12 — 🟠 High |
| **Mitigation** | • Display agent agreement/disagreement prominently — flag unanimous decisions with a "consensus warning"<br>• Mandate manual review for the first 100 alerts in production (calibration period)<br>• Implement a "devil's advocate" check: if all agents agree, the Response Agent is prompted to argue the opposite case<br>• Track and display "AI accuracy" metric based on analyst confirmation rate<br>• Schedule weekly "AI review" sessions where stored decisions are audited with fresh eyes<br>• Never suppress the "Uncertain" confidence level — low confidence must always surface to the analyst |

---

## Phase 6 — Autonomous Response

**Scope:** Automated containment actions (IP blocking, rate limiting, host isolation), analyst feedback loops, and scheduled threat hunting.

### P6-R1: Wrong Automated Blocking

| Field | Detail |
|-------|--------|
| **Description** | The auto-response engine blocks a legitimate IP based on a false positive. In a production SOC, this means a customer, partner, or internal service loses connectivity. In the lab, this could block the Wazuh agent, break inter-VM communication, or lock out the analyst from the dashboard. |
| **Likelihood** | 3 — Possible. False positives are inherent in any detection system. Automated action on false positives is the inevitable result. |
| **Impact** | 5 — Catastrophic. Service disruption. In a real SOC, this directly impacts business operations. |
| **Risk Score** | 15 — 🟠 High |
| **Mitigation** | • `DRY_RUN=true` is the default — must be explicitly overridden for live blocking<br>• Maintain an IP whitelist: `192.168.56.0/24` (lab network), Wazuh Manager IP, gateway IPs<br>• Require dual confirmation for auto-block: both detection rule trigger AND AI risk_score ≥ 80<br>• Implement auto-unblock after 15 minutes unless manually confirmed by analyst<br>• Every block action logged with timestamp, alert_id, source, and undo command<br>• Add "Undo Last Action" button to dashboard for rapid rollback<br>• Rate limit: max 3 IP blocks per 10 minutes |

---

### P6-R2: System Abuse

| Field | Detail |
|-------|--------|
| **Description** | An attacker who understands the auto-response logic crafts traffic that triggers blocking of specific target IPs. The attacker uses the SOC's own defenses as a weapon — a "self-inflicted DoS." Example: spoof the source IP of a critical service, flood the detector, and the auto-response blocks the service IP. |
| **Likelihood** | 2 — Unlikely. Requires knowledge of the response rules and ability to spoof IPs on the network. Feasible in a lab but harder in production. |
| **Impact** | 5 — Catastrophic. Attacker controls which IPs get blocked. Complete loss of defensive control. |
| **Risk Score** | 10 — 🟠 High |
| **Mitigation** | • Validate source IP against ARP/MAC tables before auto-response — reject spoofed sources<br>• Do not auto-block IPs in the local subnet (192.168.56.0/24) without human approval<br>• Rate-limit response actions globally: max 5 blocks per hour across all alerts<br>• Implement "cooldown" per target IP — cannot be blocked again within 30 minutes of an unblock<br>• Log all blocked IPs and analyze patterns — multiple blocks of the same critical-service IP = abuse indicator<br>• Add an "abuse detection" alert: if an external IP triggers blocks of more than 3 internal IPs in 1 hour, flag it |

---

### P6-R3: Privilege Escalation

| Field | Detail |
|-------|--------|
| **Description** | The `auto_response.py` script executes `sudo iptables` commands. If the script, its configuration, or the pipeline feeding it is compromised, an attacker gains root-level network control. This is the highest-privilege operation in the entire SOC lab. |
| **Likelihood** | 2 — Unlikely. Requires compromising the script or its input chain. But the attack surface is broad: Flask API → DB → response engine. |
| **Impact** | 5 — Catastrophic. Root access to the Kali SOC monitor. Full control of firewall. Ability to disable all detection. |
| **Risk Score** | 10 — 🟠 High |
| **Mitigation** | • Run response scripts under a dedicated `soc-response` user, not root<br>• Use `sudoers` to allow only specific iptables commands (allowlist, not blanket sudo)<br>• Verify script integrity on startup: compare SHA-256 hash against known-good value<br>• Command injection prevention: never pass unsanitized strings to shell commands — use subprocess with argument lists, not shell=True<br>• Audit trail: log every command executed with full argument list to a tamper-evident log<br>• Separate the response engine from the Flask dashboard process — different user, different permissions |

---

### P6-R4: Lack of Human Oversight

| Field | Detail |
|-------|--------|
| **Description** | The system reaches a state where it detects, analyzes, decides, and acts without any human seeing it. A bug in the feedback loop causes cascading wrong actions. No one notices until significant damage is done. This is the "Skynet scenario" at lab scale — not AI sentience, but a runaway automation loop. |
| **Likelihood** | 2 — Unlikely. The system is designed with human-in-the-loop, but bugs or misconfig could bypass it. |
| **Impact** | 5 — Catastrophic. Cascading wrong actions with no human to hit the brake. |
| **Risk Score** | 10 — 🟠 High |
| **Mitigation** | • **Global kill switch:** A dashboard button and CLI command that immediately halts all automated responses<br>• **Action budget:** Maximum 10 automated actions per hour; exceeding this triggers kill switch automatically<br>• **Notification on every action:** Every automated response sends a desktop/email/Slack notification to the SOC team<br>• **Daily digest:** Automated summary of all actions taken in the past 24 hours, emailed to project lead<br>• **Mandatory review period:** First 30 days of Phase 6 runs in DRY_RUN mode with daily review of what *would have* happened<br>• **Circuit breaker:** If more than 3 consecutive actions are overridden by an analyst, auto-response pauses until manually re-enabled |

---

## Risk Summary by Phase

| Phase | Risks | Critical | High | Medium |
|:-----:|:-----:|:--------:|:----:|:------:|
| 4 | 5 | 0 | 2 | 3 |
| 5 | 4 | 0 | 3 | 1 |
| 6 | 4 | 0 | 4 | 0 |
| **Total** | **13** | **0** | **9** | **4** |

---

## Next Steps

1. Review this document before starting Phase 4 implementation
2. For each risk, implement the mitigation alongside the feature
3. After implementation, update `/risk/risk_register.md` and `/risk/risk_register.csv` with actual status
4. Schedule a risk review at Phase 4 completion before proceeding to Phase 5
