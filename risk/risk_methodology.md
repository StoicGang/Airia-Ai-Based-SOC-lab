# 📋 Airia SOC Lab — Risk Management Methodology

> **Version:** 1.0  
> **Last Updated:** 2026-04-08  
> **Standard Alignment:** ISO 31000:2018 — Risk Management Guidelines  
> **Scope:** All components within the Airia AI-Based SOC Lab

---

## 1. Purpose

This document defines the risk management methodology used across the Airia SOC Lab project. It establishes how risks are identified, scored, treated, and tracked throughout the system lifecycle — from the initial tshark capture pipeline through to autonomous response capabilities.

Risk management in a SOC lab is not academic. A missed risk in the detection pipeline means attacks go unnoticed. A poorly mitigated risk in the AI engine means analysts waste time on hallucinated threats. This methodology exists to keep the system reliable, the detection pipeline trustworthy, and the response mechanisms safe.

---

## 2. Risk Scoring Formula

### Calculation

```
Risk Score = Likelihood × Impact
```

Both **Likelihood** and **Impact** are rated on a 1–5 integer scale.

### Likelihood Scale

| Rating | Label | Description |
|:------:|:-----:|-------------|
| 1 | Rare | Could occur in exceptional circumstances only. May happen once in the project lifetime. |
| 2 | Unlikely | Not expected but possible. Could occur once per phase. |
| 3 | Possible | Reasonable chance of occurring. Could happen during normal operations. |
| 4 | Likely | Expected to occur. Will probably happen at least once per deployment cycle. |
| 5 | Almost Certain | Will happen unless actively prevented. Multiple occurrences expected. |

### Impact Scale

| Rating | Label | Description |
|:------:|:-----:|-------------|
| 1 | Negligible | No operational impact. Minor inconvenience. Self-correcting. |
| 2 | Minor | Slight degradation. Single alert missed or delayed. Easy to fix. |
| 3 | Moderate | Partial system functionality affected. Multiple alerts impacted. Manual intervention required. |
| 4 | Major | Significant functionality loss. Detection pipeline output unreliable. Investigation required. |
| 5 | Catastrophic | Complete pipeline failure, data loss, or security breach. System integrity compromised. |

### Risk Level Classification

| Score Range | Risk Level | Color | Required Response |
|:-----------:|:----------:|:-----:|-------------------|
| 1–4 | Low | 🟢 | Accept or monitor. Document and review quarterly. |
| 5–9 | Medium | 🟡 | Mitigate within current phase. Assign owner. |
| 10–15 | High | 🟠 | Mitigate before production use. Escalate to project lead. |
| 16–25 | Critical | 🔴 | Immediate action required. Block phase completion until addressed. |

---

## 3. Risk Treatment Strategies

Every identified risk must have one of the following treatment designations:

### Avoid

**Eliminate the risk entirely by removing the source.**

- Remove the feature, component, or integration that introduces the risk
- Applicable when the risk outweighs the value of the capability
- Example: Not enabling autonomous IP blocking in Phase 6 if the false positive rate is too high

### Mitigate

**Reduce the likelihood and/or impact through controls.**

- Implement preventive controls (input validation, access control, monitoring)
- Implement detective controls (logging, alerting, health checks)
- Implement corrective controls (auto-recovery, rollback, backups)
- Example: Adding schema validation on AI output to reduce hallucination impact

### Transfer

**Shift the risk to a third party.**

- Use an external service with SLA guarantees
- Shift accountability to a team with appropriate expertise
- Example: Using a managed MISP feed provider instead of self-curating threat intel

### Accept

**Acknowledge the risk and take no further action.**

- Only valid for Low-rated risks where mitigation cost exceeds impact
- Must be explicitly documented with justification
- Must be reviewed on schedule — acceptance does not mean forgotten
- Example: Accepting the risk of tshark packet loss under extreme volume in a lab environment

---

## 4. Risk Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  IDENTIFY   │───▶│   ASSESS    │───▶│    TREAT    │───▶│   MONITOR   │───▶│   REVIEW    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                                    │
                                                         ◀─────────────────────────┘
                                                           (continuous cycle)
```

### 4.1 Identification

**When:** At the start of each phase, when adding new components, and during incident post-mortems.

**How:**
- Review the architecture and data flow for new failure modes
- Analyze threat model: What could an attacker (or a bug) break?
- Check each integration point (tshark → CSV → AI → DB → Dashboard)
- Review CVEs for dependencies (Flask, Wazuh, Docker images, Python packages)
- Capture risks from red team exercises and detection gap analysis

**Output:** New entries in `/risk/risk_register.md` with status `Open`

### 4.2 Assessment

**When:** Immediately after identification.

**How:**
- Assign Likelihood (1–5) based on operating environment and existing controls
- Assign Impact (1–5) based on worst-case outcome if the risk materializes
- Calculate Risk Score (L × I)
- Determine Risk Level from the classification table
- Differentiate clearly between the **threat** (the attacker action or event) and the **vulnerability** (the weakness that enables it)

**Key rule:** Score risks based on the system as it exists now, not how it will look after mitigation. Residual risk is scored separately.

### 4.3 Treatment

**When:** Immediately after assessment for High and Critical risks. Within the current phase for Medium risks.

**How:**
- Select treatment strategy (Avoid / Mitigate / Transfer / Accept)
- Define specific, actionable controls — not generic statements like "improve security"
- Assign a Risk Owner responsible for implementation
- Set a target date aligned with the relevant phase milestone
- Document the expected residual risk after treatment

### 4.4 Monitoring

**When:** Continuously during operation.

**How:**
- Implement the Detection Method specified in the risk register
- Track Key Risk Indicators (KRIs):
  - Alert volume and false positive rate
  - Pipeline health and uptime
  - AI output validation failure rate
  - Mean-time-to-detect and mean-time-to-respond
- Surface KRIs in the Flask dashboard where applicable

### 4.5 Review

**When:** At every phase completion milestone, or quarterly — whichever comes first. Also triggered by:
- Security incidents or near-misses
- Major architecture changes
- Addition of new integrations or external dependencies

**How:**
- Review all Open and In Progress risks
- Update Likelihood and Impact scores based on current evidence
- Verify that mitigations are implemented and effective
- Reassess residual risk levels
- Close risks that are fully mitigated or no longer applicable
- Identify new risks introduced since last review

---

## 5. Application to the SOC Lab

### Phase-Specific Risk Focus

| Phase | Primary Risk Domain | Key Concern |
|:-----:|---------------------|-------------|
| 1 | Network capture | Pipeline reliability — does tshark actually capture everything? |
| 2 | AI + Database + Dashboard | AI hallucination, data integrity, unauthenticated dashboard |
| 3 | SIEM Integration | Agent stability, alert forwarding, Docker resource management |
| 4 | Case Management | Alert ingestion, automated response accuracy, threat intel quality |
| 5 | Multi-Agent + ML | Model drift, data poisoning, over-reliance on AI |
| 6 | Autonomous Response | Wrong blocking, privilege escalation, lack of oversight |

### Integration with Development Workflow

1. **Before starting a phase:** Review `phase4_risk_plan.md` (or equivalent) to understand risks before writing code
2. **During development:** When adding a new component, check if it introduces risks not yet registered
3. **Before merging:** Verify that mitigations for the current phase's risks are implemented or explicitly deferred
4. **Post-deployment:** Validate detection methods are active and generating data

### Risk Register Ownership

- The risk register (`risk_register.md` & `risk_register.csv`) is a living document
- Every team member can propose new risks via PR
- The project lead reviews and approves risk assessments
- Risk register updates are tracked in `CHANGELOG.md`

---

## 6. Residual Risk

After mitigations are applied, the **residual risk** is the remaining exposure. This is documented in the risk register's `Residual Risk` column.

Residual risk should be:
- **Low:** Mitigation effectively addresses the root cause
- **Medium:** Mitigation reduces but does not eliminate the risk; ongoing monitoring required
- **High:** Mitigation is partial or not yet implemented; risk remains significant

If residual risk is **High**, the risk must be escalated and reassessed. Additional controls or a different treatment strategy may be needed.

---

## 7. Document Control

| Field | Value |
|-------|-------|
| Classification | Internal |
| Review Frequency | Per-phase or quarterly |
| Approved By | SOC Lab Project Lead |
| Related Documents | [risk_register.md](risk_register.md), [risk_register.csv](risk_register.csv), [phase4_risk_plan.md](phase4_risk_plan.md) |
