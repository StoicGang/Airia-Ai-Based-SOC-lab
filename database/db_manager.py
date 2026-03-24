#!/usr/bin/env python3
"""
database/db_manager.py — SQLite persistence layer for SOC Lab.
Phase: 2 | Status: Baseline locked

All database operations go through this module.
Never write raw SQL in other modules — always call these functions.
"""

import sqlite3
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

DB_PATH     = os.getenv("DB_PATH", "/home/kali/soc-lab/database/soc_lab.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory for dict-like access."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # Better concurrent performance
    return conn


def init_db() -> None:
    """
    Create all tables if they do not exist.
    Safe to call on every startup — idempotent.
    """
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized at: {DB_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def create_session(session_id: str, interface: str,
                   duration: int, rule_used: str) -> None:
    """Create a new monitoring session record."""
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO sessions
            (session_id, started_at, interface, duration_seconds, rule_used)
        VALUES (?, datetime('now'), ?, ?, ?)
    """, (session_id, interface, duration, rule_used))
    conn.commit()
    conn.close()


def complete_session(session_id: str, total_packets: int,
                     alerts_generated: int) -> None:
    """Mark a session complete with final packet and alert counts."""
    conn = get_connection()
    conn.execute("""
        UPDATE sessions
        SET ended_at = datetime('now'),
            total_packets = ?,
            alerts_generated = ?,
            status = 'complete'
        WHERE session_id = ?
    """, (total_packets, alerts_generated, session_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# ALERT OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def save_alert(alert: dict, soc_report: dict, session_id: str) -> bool:
    """
    Persist a complete alert + AI SOC report to the database.

    Args:
        alert:      The JSON alert dict sent to Airia
        soc_report: The parsed AI analysis response from Airia
        session_id: ID of the current monitoring session

    Returns:
        True if saved successfully, False if alert_id already exists.
    """
    mitre = soc_report.get("mitre_mapping", {})
    actions = soc_report.get("recommended_actions", [])

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO alerts (
                alert_id, timestamp, src_ip, dst_ip,
                attack_type, protocol, packet_count, threshold,
                risk_score, risk_level, threat_classification,
                mitre_technique_id, mitre_technique_name, mitre_tactic,
                escalation_required, confidence_level,
                executive_summary, analysis_reasoning,
                recommended_actions, full_report_json,
                rule_id, session_id
            ) VALUES (
                ?, datetime('now'), ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )
        """, (
            alert.get("alert_id"),
            alert.get("indicator_value"),
            alert.get("destination_ip"),
            alert.get("alert_type"),
            alert.get("protocol"),
            alert["evidence"].get("packet_count"),
            alert["evidence"].get("threshold"),
            soc_report.get("risk_score"),
            soc_report.get("risk_level"),
            soc_report.get("threat_classification"),
            mitre.get("technique_id") if isinstance(mitre, dict) else None,
            mitre.get("technique_name") if isinstance(mitre, dict) else None,
            mitre.get("tactic") if isinstance(mitre, dict) else None,
            1 if soc_report.get("escalation_required") else 0,
            soc_report.get("confidence_level"),
            soc_report.get("executive_summary"),
            soc_report.get("analysis_reasoning"),
            json.dumps(actions),
            json.dumps(soc_report),
            alert.get("rule_id", "UNKNOWN"),
            session_id,
        ))
        conn.commit()
        _save_iocs(conn, alert)
        print(f"[DB] Alert saved: {alert.get('alert_id')}")
        return True

    except sqlite3.IntegrityError:
        print(f"[DB] Alert already exists: {alert.get('alert_id')} — skipped")
        return False
    finally:
        conn.close()


def _save_iocs(conn: sqlite3.Connection, alert: dict) -> None:
    """Extract and save IOCs from alert. Called internally by save_alert."""
    alert_id = alert.get("alert_id")
    now      = "datetime('now')"

    iocs = [
        ("ip",       alert.get("indicator_value")),
        ("ip",       alert.get("destination_ip")),
        ("protocol", alert.get("protocol")),
    ]

    for ioc_type, ioc_value in iocs:
        if not ioc_value:
            continue
        existing = conn.execute(
            "SELECT id, hit_count FROM iocs WHERE alert_id=? AND ioc_value=?",
            (alert_id, ioc_value)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE iocs SET hit_count=hit_count+1, last_seen=datetime('now') WHERE id=?",
                (existing["id"],)
            )
        else:
            conn.execute("""
                INSERT INTO iocs (alert_id, ioc_type, ioc_value, first_seen, last_seen)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """, (alert_id, ioc_type, ioc_value))


# ─────────────────────────────────────────────────────────────────────────────
# READ OPERATIONS (for dashboard)
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_alerts(limit: int = 20) -> list[dict]:
    """Return the most recent alerts, newest first."""
    conn  = get_connection()
    rows  = conn.execute("""
        SELECT alert_id, timestamp, src_ip, dst_ip, attack_type,
               risk_score, risk_level, mitre_technique_id,
               escalation_required, executive_summary, protocol
        FROM alerts
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alert_by_id(alert_id: str) -> dict | None:
    """Return full alert detail including AI report."""
    conn = get_connection()
    row  = conn.execute(
        "SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["recommended_actions"] = json.loads(result.get("recommended_actions") or "[]")
        result["full_report_json"]    = json.loads(result.get("full_report_json") or "{}")
        return result
    return None


def get_stats() -> dict:
    """Return aggregate statistics for the dashboard."""
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    by_risk = conn.execute("""
        SELECT risk_level, COUNT(*) as count
        FROM alerts GROUP BY risk_level
    """).fetchall()
    by_type = conn.execute("""
        SELECT attack_type, COUNT(*) as count
        FROM alerts GROUP BY attack_type ORDER BY count DESC
    """).fetchall()
    top_ips = conn.execute("""
        SELECT src_ip, COUNT(*) as count
        FROM alerts GROUP BY src_ip ORDER BY count DESC LIMIT 5
    """).fetchall()
    avg_risk = conn.execute(
        "SELECT AVG(risk_score) FROM alerts WHERE risk_score IS NOT NULL"
    ).fetchone()[0]
    escalations = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE escalation_required = 1"
    ).fetchone()[0]

    conn.close()
    return {
        "total_alerts":   total,
        "avg_risk_score": round(avg_risk or 0, 1),
        "escalations":    escalations,
        "by_risk_level":  {r["risk_level"]: r["count"] for r in by_risk},
        "by_attack_type": [dict(r) for r in by_type],
        "top_src_ips":    [dict(r) for r in top_ips],
    }


def get_all_iocs(limit: int = 50) -> list[dict]:
    """Return all IOCs across all alerts."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.ioc_type, i.ioc_value, i.hit_count,
               i.first_seen, i.last_seen, i.alert_id
        FROM iocs i
        ORDER BY i.hit_count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    stats = get_stats()
    print(f"[DB] Total alerts: {stats['total_alerts']}")
    print(f"[DB] Avg risk score: {stats['avg_risk_score']}")