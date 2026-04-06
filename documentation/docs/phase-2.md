# Phase 2 — Detection Engine + Dashboard

**Goal:** YAML-driven multi-attack detection, SQLite persistence, Flask dashboard.  
**Time:** ~2 hours | **Prereq:** Phase 1

---

## Step 1 — Add to .env

```env
DB_PATH=/home/kali/soc-lab/database/soc_lab.db
RULES_PATH=/home/kali/soc-lab/config/detection_rules.yaml
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
```

---

## Step 2 — Init Database

```bash
python database/db_manager.py
# Expected: [DB] Initialized | Total alerts: 0
```

---

## Step 3 — Check Rules

```bash
python scripts/soc_monitor_v2.py --list
```
```
RULE-001  ICMP Flood       (ICMP, threshold: 40, window: 100s)
RULE-002  TCP SYN Flood    (TCP, threshold: 80, window: 60s)
RULE-003  Port Scan        (TCP, threshold: 15, window: 30s)
```

---

## Step 4 — Test Each Attack

### ICMP Flood
**Kali:** `sudo python scripts/soc_monitor_v2.py --rule RULE-001`  
**Arch:** `ping 192.168.56.20 -c 200 -s 64`

### SYN Flood
**Kali:** `sudo python scripts/soc_monitor_v2.py --rule RULE-002`  
**Arch:** `sudo hping3 -S --flood -p 80 192.168.56.20` (stop after ~10s)

### Port Scan
**Kali:** `sudo python scripts/soc_monitor_v2.py --rule RULE-003`  
**Arch:** `nmap -sS 192.168.56.20 -p 1-100`

---

## Step 5 — Start Dashboard

```bash
python dashboard/app.py
```

Open `http://192.168.56.20:5000`:
- Stat cards: total alerts, avg risk, escalations, high+ severity
- Alert table with MITRE mappings
- Click any alert → full AI report

---

## Step 6 — API Endpoints

```bash
curl http://localhost:5000/api/alerts    # All alerts
curl http://localhost:5000/api/stats     # Summary stats
curl http://localhost:5000/api/iocs      # Extracted IOCs
curl http://localhost:5000/health        # Health check
```

---

## Adding New Rules

Edit `config/detection_rules.yaml` — no code changes needed:
```yaml
- id: "RULE-004"
  name: "DNS Tunneling"
  alert_type: "DNS Tunneling"
  protocol: "UDP"
  tshark_filter: "udp.port == 53"
  count_field: "packet_count"
  threshold: 100
  time_window: 60
  mitre_id: "T1071.004"
  mitre_tactic: "Command and Control"
```

---

## Verify

- [ ] Database initialised
- [ ] All 3 rules detected attacks
- [ ] Dashboard shows alerts at `:5000`
- [ ] API returns JSON
- [ ] `pytest tests/test_db.py -v` passes

→ [Phase 3](phase-3.md)
