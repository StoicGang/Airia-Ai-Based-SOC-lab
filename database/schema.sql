-- SOC Lab Database Schema

PRAGMA foreign_keys = ON;

-- Every alert that crosses the detection threshold
CREATE TABLE IF NOT EXISTS alerts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id              TEXT    UNIQUE NOT NULL,
    timestamp             TEXT    NOT NULL,
    src_ip                TEXT    NOT NULL,
    dst_ip                TEXT    NOT NULL,
    attack_type           TEXT    NOT NULL,
    protocol              TEXT    NOT NULL,
    packet_count          INTEGER NOT NULL,
    threshold             INTEGER NOT NULL,
    risk_score            INTEGER,
    risk_level            TEXT,
    threat_classification TEXT,
    mitre_technique_id    TEXT,
    mitre_technique_name  TEXT,
    mitre_tactic          TEXT,
    escalation_required   INTEGER DEFAULT 0,
    confidence_level      TEXT,
    executive_summary     TEXT,
    analysis_reasoning    TEXT,
    recommended_actions   TEXT,    -- JSON array stored as string
    full_report_json      TEXT,    -- Complete Airia response
    rule_id               TEXT,    -- Which detection rule fired
    session_id            TEXT,
    created_at            TEXT    DEFAULT (datetime('now'))
);

-- Each run of soc_monitor_v2.py is one session
CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT    UNIQUE NOT NULL,
    started_at       TEXT    NOT NULL,
    ended_at         TEXT,
    interface        TEXT    NOT NULL,
    duration_seconds INTEGER NOT NULL,
    total_packets    INTEGER DEFAULT 0,
    alerts_generated INTEGER DEFAULT 0,
    rule_used        TEXT,
    status           TEXT    DEFAULT 'running'   -- running | complete | error
);

-- Individual IOCs extracted from alerts
CREATE TABLE IF NOT EXISTS iocs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id    TEXT    NOT NULL,
    ioc_type    TEXT    NOT NULL,   -- ip | port | protocol
    ioc_value   TEXT    NOT NULL,
    first_seen  TEXT    NOT NULL,
    last_seen   TEXT    NOT NULL,
    hit_count   INTEGER DEFAULT 1,
    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
);

-- Indexes for dashboard query performance
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp   ON alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_src_ip      ON alerts(src_ip);
CREATE INDEX IF NOT EXISTS idx_alerts_risk_level  ON alerts(risk_level);
CREATE INDEX IF NOT EXISTS idx_iocs_alert_id      ON iocs(alert_id);
CREATE INDEX IF NOT EXISTS idx_iocs_value         ON iocs(ioc_value);