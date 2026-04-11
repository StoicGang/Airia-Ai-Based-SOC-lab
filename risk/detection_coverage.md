# Detection Coverage Matrix
# AI-Powered SOC Lab — Risk Register × Detection Capability
# Methodology: ISO 27001:2022 | MITRE ATT&CK aligned
# Last updated: 2026-04-11 | Phase 3 complete

---

## Coverage Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully detected — Wazuh rule fires, alert forwarded to AI pipeline |
| ⚠️ | Partially detected — trigger exists but no enrichment or case created |
| ❌ | Gap — no detection coverage in current phase |
| 🔜 | Covered in planned phase (see Phase column) |

---

## Matrix

| Risk ID | Asset | Threat | MITRE Technique | ISO Control | Risk Level | Wazuh Detection | Coverage | Gap | Closes in |
|---------|-------|--------|-----------------|-------------|------------|-----------------|----------|-----|-----------|
| R-001 | kali-soc-monitor (192.168.56.20) | Unauthorized access | T1190 — Exploit Public App | A.9.1.1 | HIGH | SSH brute-force rule (5712) + FIM on /etc | ⚠️ | Alert fires but no case created — no analyst review loop | Phase 4 (TheHive) |
| R-002 | arch-workstation (192.168.56.10) | Malware execution | T1059 — Command & Scripting | A.12.2.1 | HIGH | Wazuh agent process monitoring + syscall watch | ⚠️ | Detected but no IOC enrichment — hash/domain not checked | Phase 4 (Cortex) |
| R-003 | wazuh-manager (192.168.56.20) | Log tampering | T1070 — Indicator Removal | A.12.4.2 | MEDIUM | FIM on /var/ossec/logs + integrity check | ✅ | None — alert + AI report generated | Phase 3 ✅ |
| R-004 | flask-dashboard (192.168.56.20) | Web application attack | T1190 — Exploit Public App | A.14.2.1 | MEDIUM | Wazuh web log rule (31103) | ⚠️ | Alert fires but no payload analysis or WAF correlation | Phase 4 (Cortex) |
| R-005 | docker-daemon (192.168.56.20) | Container escape | T1611 — Escape to Host | A.12.6.1 | HIGH | Wazuh Docker listener + namespace watch | ⚠️ | Detection partial — no automated response action defined | Phase 4 (Cortex responder) |
| R-006 | airia-api-client | API key exfiltration | T1552 — Credentials from Files | A.9.4.3 | HIGH | FIM on .env + secrets scan | ⚠️ | .env monitored but no alert-to-case escalation path | Phase 4 (TheHive) |
| R-007 | sqlite-db (alert.db) | Data tampering / deletion | T1485 — Data Destruction | A.12.3.1 | MEDIUM | FIM on alert.db path | ✅ | None — FIM alert + AI report on change | Phase 3 ✅ |
| R-008 | arch-workstation (192.168.56.10) | Lateral movement from attacker VM | T1021 — Remote Services | A.13.1.3 | HIGH | Network traffic anomaly (ICMP flood threshold) | ✅ | None — threshold engine fires, full AI report generated | Phase 3 ✅ |
| R-009 | wazuh-indexer | Index corruption / DoS | T1499 — Endpoint DoS | A.17.1.2 | MEDIUM | Wazuh self-monitoring (manager→indexer health) | ❌ | No rule for indexer resource exhaustion | Phase 5 (multi-agent monitor) |
| R-010 | thehive (planned) | Case data manipulation | T1565 — Data Manipulation | A.18.1.3 | HIGH | Not deployed yet | ❌ | Entire tool is Phase 4 — no coverage now | Phase 4 (TheHive deploy) |
| R-011 | cortex (planned) | Analyzer abuse / API flooding | T1499 — Resource Hijacking | A.12.1.3 | MEDIUM | Not deployed yet | ❌ | Phase 4 dependency | Phase 4 (Cortex deploy) |
| R-012 | misp (planned) | IOC feed poisoning | T1584 — Compromise Infrastructure | A.6.1.1 | HIGH | Not deployed yet | ❌ | Phase 4 dependency | Phase 4 (MISP deploy) |

---

## Coverage Summary (Phase 3 Baseline)

| Level | Count | Fully Covered ✅ | Partial ⚠️ | Gap ❌ |
|-------|-------|-----------------|------------|--------|
| HIGH | 7 | 1 (14%) | 4 (57%) | 2 (29%) |
| MEDIUM | 5 | 2 (40%) | 2 (40%) | 1 (20%) |
| **Total** | **12** | **3 (25%)** | **6 (50%)** | **3 (25%)** |

**Phase 3 detection coverage: 25% full, 75% partial or gap.**
Phase 4 target: close all partial gaps for HIGH risks via TheHive case creation + Cortex enrichment.

---

## Phase-by-Phase Coverage Roadmap

```
Phase 3 (complete) ─── Wazuh detection + AI reports + FIM
                         ↓ closes: R-003, R-007, R-008

Phase 4 (next)     ─── TheHive cases + Cortex enrichment + MISP IOC lookup
                         ↓ closes: R-001, R-002, R-004, R-005, R-006, R-010, R-011, R-012

Phase 5            ─── Multi-agent + RAG memory + automated response
                         ↓ closes: R-009 + all remaining partial detections
```

---

## How to Read This in an Interview

> "My risk register follows ISO 31000 methodology with 31 identified risks across Phases 1–6.
> I maintain a detection coverage matrix that maps each risk to its MITRE ATT&CK technique,
> current Wazuh detection status, and which phase closes the gap.
> At Phase 3 baseline: 25% full coverage, 50% partial. Phase 4 (TheHive + Cortex) targets
> closing all HIGH-severity partial gaps through automated case creation and IOC enrichment."

---
*Generated from Phase 3 risk register (risk_register.md/.csv) — ISO 27001:2022 Clause 6.1.2*
