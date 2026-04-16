#!/usr/bin/env python3
"""
test_w2thehive.py — Unit tests for the Wazuh→TheHive forwarder.
Run: python3 -m pytest integrations/thehive/test_w2thehive.py -v
Or:  python3 integrations/thehive/test_w2thehive.py
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent dir to path
sys.path.insert(0, ".")
from integrations.thehive.w2thehive import (
    get_severity, get_tlp, get_risk_context,
    build_observables, create_alert
)


# ─── Sample Wazuh Alerts ──────────────────────────────────────────────────────
ALERT_LEVEL_10 = {
    "id": "test-001",
    "timestamp": "2026-04-11T00:00:00.000Z",
    "rule": {
        "id": "100001",
        "level": 10,
        "description": "ICMP flood attack detected",
        "groups": ["syslog", "soc-lab"],
        "mitre": {
            "id": ["T1498"],
            "tactic": ["Impact"]
        }
    },
    "agent": {
        "id": "001",
        "name": "arch-workstation",
        "ip": "192.168.56.10"
    },
    "data": {
        "srcip": "192.168.56.10",
        "dstip": "192.168.56.20",
        "protocol": "ICMP"
    }
}

ALERT_LEVEL_7 = {
    "id": "test-002",
    "timestamp": "2026-04-11T00:01:00.000Z",
    "rule": {
        "id": "550",
        "level": 7,
        "description": "File integrity monitoring — file changed",
        "groups": ["ossec", "syscheck"],
        "mitre": {}
    },
    "agent": {"id": "001", "name": "arch-workstation", "ip": "192.168.56.10"},
    "data": {"file": "/etc/passwd"}
}

ALERT_MISSING_FIELDS = {
    "rule": {},
    "agent": {},
    "data": {}
}

ALERT_BAD_JSON = "this is not json {"


# ─── Tests ────────────────────────────────────────────────────────────────────
class TestSeverityMapping(unittest.TestCase):
    def test_level_12_critical(self):
        self.assertEqual(get_severity(12), 4)

    def test_level_10_high(self):
        self.assertEqual(get_severity(10), 3)

    def test_level_7_medium(self):
        self.assertEqual(get_severity(7), 2)

    def test_level_3_low(self):
        self.assertEqual(get_severity(3), 1)

    def test_boundary_level_9(self):
        self.assertEqual(get_severity(9), 2)

    def test_boundary_level_11(self):
        self.assertEqual(get_severity(11), 3)


class TestTLPMapping(unittest.TestCase):
    def test_tlp_red_level_12(self):
        self.assertEqual(get_tlp(12), 3)

    def test_tlp_amber_level_7(self):
        self.assertEqual(get_tlp(7), 2)

    def test_tlp_green_level_3(self):
        self.assertEqual(get_tlp(3), 1)


class TestRiskContext(unittest.TestCase):
    def test_known_ip_returns_context(self):
        data = {"srcip": "192.168.56.10"}
        ctx = get_risk_context(data)
        self.assertIn("arch-workstation", ctx)
        self.assertIn("192.168.56.10", ctx)

    def test_unknown_ip_returns_fallback(self):
        data = {"srcip": "10.0.0.1"}
        ctx = get_risk_context(data)
        self.assertIn("No matching assets", ctx)

    def test_empty_data_returns_fallback(self):
        ctx = get_risk_context({})
        self.assertIn("No matching assets", ctx)

    def test_both_ips_in_context(self):
        data = {"srcip": "192.168.56.10", "dstip": "192.168.56.20"}
        ctx = get_risk_context(data)
        self.assertIn("arch-workstation", ctx)
        self.assertIn("kali-soc-monitor", ctx)


class TestObservableBuilder(unittest.TestCase):
    def test_extracts_src_ip(self):
        data = {"srcip": "192.168.56.10"}
        obs = build_observables(data, 7)
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0]["dataType"], "ip")
        self.assertEqual(obs[0]["data"], "192.168.56.10")

    def test_extracts_url(self):
        data = {"url": "http://malicious.example.com/payload"}
        obs = build_observables(data, 7)
        self.assertTrue(any(o["dataType"] == "url" for o in obs))

    def test_extracts_hash(self):
        data = {"sha256": "abc123def456"}
        obs = build_observables(data, 10)
        self.assertTrue(any(o["dataType"] == "hash" for o in obs))

    def test_skips_empty_fields(self):
        data = {"srcip": "", "dstip": "N/A"}
        obs = build_observables(data, 7)
        self.assertEqual(len(obs), 0)

    def test_tlp_matches_level(self):
        data = {"srcip": "1.2.3.4"}
        obs = build_observables(data, 12)
        self.assertEqual(obs[0]["tlp"], 3)  # RED for critical


class TestCreateAlert(unittest.TestCase):
    @patch("integrations.thehive.w2thehive.requests.post")
    def test_successful_creation(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"_id": "~12345"}
        mock_post.return_value = mock_resp

        create_alert(json.dumps(ALERT_LEVEL_10))
        mock_post.assert_called_once()

        # Verify payload structure
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        self.assertEqual(payload["type"], "wazuh")
        self.assertEqual(payload["source"], "wazuh-siem")
        self.assertIn("T1498", " ".join(payload["tags"]))
        self.assertEqual(payload["severity"], 3)  # level 10 → HIGH

    @patch("integrations.thehive.w2thehive.requests.post")
    def test_duplicate_sourceref_skipped(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 207  # Duplicate
        mock_post.return_value = mock_resp

        # Should not raise
        create_alert(json.dumps(ALERT_LEVEL_7))
        mock_post.assert_called_once()

    def test_bad_json_does_not_raise(self):
        # Should log error and return gracefully
        create_alert(ALERT_BAD_JSON)  # Must not raise

    @patch("integrations.thehive.w2thehive.requests.post")
    def test_missing_fields_handled(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"_id": "~99999"}
        mock_post.return_value = mock_resp

        # Should not raise even with empty rule/agent/data
        create_alert(json.dumps(ALERT_MISSING_FIELDS))
        mock_post.assert_called_once()

    @patch("integrations.thehive.w2thehive.requests.post")
    def test_source_ref_format(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"_id": "~11111"}
        mock_post.return_value = mock_resp

        create_alert(json.dumps(ALERT_LEVEL_10))
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["sourceRef"], "wazuh-100001-test-001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
