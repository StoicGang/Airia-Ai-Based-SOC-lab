#!/usr/bin/env python3
"""Unit tests for database module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from unittest.mock import patch

# Use temp DB for tests — never touch production DB
TEST_DB = tempfile.mktemp(suffix=".db")

with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
    from database.db_manager import init_db, save_alert, get_stats, get_recent_alerts

SAMPLE_ALERT = {
    "alert_id": "SOC-TEST0001",
    "alert_type": "ICMP Flood Detected",
    "indicator_value": "192.168.56.10",
    "destination_ip": "192.168.56.20",
    "protocol": "ICMP",
    "rule_id": "RULE-001",
    "evidence": {"packet_count": 85, "time_window_seconds": 100, "threshold": 40}
}

SAMPLE_REPORT = {
    "alert_id": "SOC-TEST0001",
    "risk_score": 65,
    "risk_level": "High",
    "threat_classification": "Suspicious Network Volume",
    "mitre_mapping": {"technique_id": "T1046", "technique_name": "Network Service Scanning", "tactic": "Discovery"},
    "escalation_required": False,
    "confidence_level": "High",
    "executive_summary": "Test summary.",
    "analysis_reasoning": "Test reasoning.",
    "recommended_actions": ["Monitor", "Investigate"]
}

def setup_function():
    with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
        init_db()

def test_save_alert():
    with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
        result = save_alert(SAMPLE_ALERT, SAMPLE_REPORT, "SESSION001")
    assert result is True

def test_duplicate_alert():
    with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
        save_alert(SAMPLE_ALERT, SAMPLE_REPORT, "SESSION001")
        result = save_alert(SAMPLE_ALERT, SAMPLE_REPORT, "SESSION001")
    assert result is False   # duplicate should return False

def test_get_stats():
    with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
        save_alert(SAMPLE_ALERT, SAMPLE_REPORT, "SESSION001")
        stats = get_stats()
    assert stats["total_alerts"] >= 1
    assert "by_risk_level" in stats

def test_get_recent_alerts():
    with patch.dict(os.environ, {"DB_PATH": TEST_DB}):
        save_alert(SAMPLE_ALERT, SAMPLE_REPORT, "SESSION001")
        alerts = get_recent_alerts(10)
    assert len(alerts) >= 1
    assert alerts[0]["alert_id"] == "SOC-TEST0001"