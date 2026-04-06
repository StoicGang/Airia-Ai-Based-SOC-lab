#!/usr/bin/env python3
"""
dashboard/app.py — Flask web dashboard for SOC Lab.
Phase: 2 | 

Run: python dashboard/app.py
Access: http://192.168.56.20:5000
"""

import json
import os
import sys
from pathlib import Path

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_manager import get_recent_alerts, get_alert_by_id, get_stats, get_all_iocs, init_db, save_wazuh_alert

load_dotenv(Path(__file__).parent.parent / "config" / ".env")

app  = Flask(__name__)
PORT = int(os.getenv("FLASK_PORT", 5000))
HOST = os.getenv("FLASK_HOST", "0.0.0.0")


@app.route("/")
def index():
    alerts = get_recent_alerts(20)
    stats  = get_stats()
    return render_template("index.html", alerts=alerts, stats=stats)


@app.route("/alert/<alert_id>")
def alert_detail(alert_id: str):
    alert = get_alert_by_id(alert_id)
    if not alert:
        return "Alert not found", 404
    return render_template("alert_detail.html", alert=alert)


@app.route("/api/alerts")
def api_alerts():
    return jsonify(get_recent_alerts(50))


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/iocs")
def api_iocs():
    return jsonify(get_all_iocs(50))


@app.route("/api/alerts/ingest", methods=["POST"])
def ingest_alert():
    """Receive Wazuh alerts from custom-w2airia integration."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or empty JSON body"}), 400
    if "rule" not in data and "source" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    result = save_wazuh_alert(data)
    if result.get("ok"):
        return jsonify({"status": "ok", "alert_id": result["alert_id"]}), 201
    else:
        code = 409 if result.get("error") == "duplicate" else 500
        return jsonify({"status": "error", "error": result.get("error")}), code


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "SOC Lab Dashboard v3"})


if __name__ == "__main__":
    init_db()
    print(f"\n🛡️  SOC Lab Dashboard starting at http://{HOST}:{PORT}")
    print(f"  Access from host: http://<YOUR-KALI-IP>:{PORT}\n")
    app.run(host=HOST, port=PORT, debug=False)
