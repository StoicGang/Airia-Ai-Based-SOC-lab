# Phase 3 — Wazuh SIEM Integration

**Goal:** Wazuh via Docker on Kali, Arch as agent, end-to-end: Wazuh → w2airia → Flask dashboard.  
**Time:** ~3–4 hours | **Prereq:** Phase 2, Docker installed

---

## Step 1 — Generate Certificates

```bash
cd ~/soc-lab/docker
docker compose -f generate-indexer-certs.yml run --rm generator
```

---

## Step 2 — Start Wazuh Stack

```bash
docker compose up -d
```

| Container | Port | Purpose |
|-----------|------|---------|
| wazuh.manager | 1514, 1515, 55000 | Agent comms + API |
| wazuh.indexer | 9200 | Alert storage |
| wazuh.dashboard | 443 | Web UI |

Wait ~60 seconds, then verify:
```bash
docker compose ps
curl -k -u admin:SecretPassword https://localhost:9200/_cluster/health?pretty
# status should be "green"
```

Dashboard: `https://192.168.56.20:443` — `admin` / `SecretPassword`

---

## Step 3 — Install Agent on Arch

```bash
# Use the multi-distro installer
sudo bash install_agent.sh
```

Or manually — configure `/var/ossec/etc/ossec.conf`:
```xml
<client>
  <server>
    <address>192.168.56.20</address>
    <port>1514</port>
    <protocol>tcp</protocol>
  </server>
</client>
```

```bash
sudo /var/ossec/bin/wazuh-control start
```

> If CDN is blocked, extract agent files from Docker image:  
> `docker pull wazuh/wazuh-agent:4.14.4` → `docker cp` → copy to `/var/ossec`

---

## Step 4 — Verify Agent

```bash
docker exec docker-wazuh.manager-1 /var/ossec/bin/manage_agents -l
# ID: 001, Name: arch-workstation, Status: Active
```

---

## Step 5 — Deploy Integration Script

```bash
# Copy into container
docker cp integrations/wazuh/custom-w2airia.py \
  docker-wazuh.manager-1:/var/ossec/integrations/custom-w2airia

# Permissions
docker exec docker-wazuh.manager-1 chmod 750 /var/ossec/integrations/custom-w2airia
docker exec docker-wazuh.manager-1 chown root:wazuh /var/ossec/integrations/custom-w2airia

# Install requests
docker exec docker-wazuh.manager-1 python3 -m ensurepip
docker exec docker-wazuh.manager-1 pip3 install requests
```

> `requests` is lost on container rebuild — reinstall after `docker compose down && up`.

---

## Step 6 — Enable Integration

```bash
docker exec docker-wazuh.manager-1 bash -c '
sed -i "/<\/ossec_config>/i\\
  <integration>\\
    <name>custom-w2airia</name>\\
    <level>3</level>\\
    <alert_format>json</alert_format>\\
  </integration>" /var/ossec/etc/ossec.conf
'
docker exec docker-wazuh.manager-1 /var/ossec/bin/wazuh-control restart
```

---

## Step 7 — Add Custom Rules

```bash
docker exec docker-wazuh.manager-1 bash -c 'cat > /var/ossec/etc/rules/local_rules.xml << EOF
<group name="custom,soc-lab">
  <rule id="100001" level="10">
    <if_group>syslog</if_group>
    <match>ICMP flood</match>
    <description>ICMP flood attack detected</description>
    <mitre><id>T1498</id></mitre>
  </rule>
</group>
EOF'
docker exec docker-wazuh.manager-1 /var/ossec/bin/wazuh-control restart
```

---

## Step 8 — Start Flask

```bash
cd ~/soc-lab && source venv/bin/activate
python dashboard/app.py
```

---

## Step 9 — Test End-to-End

On **Arch**:
```bash
sudo touch /etc/test-fim-trigger
```

On **Kali**:
```bash
# Force immediate scan
docker exec docker-wazuh.manager-1 /var/ossec/bin/agent_control -r -a
sleep 60

# Check alerts reached Wazuh
docker exec docker-wazuh.manager-1 tail -3 /var/ossec/logs/alerts/alerts.json

# Check integration forwarded
docker exec docker-wazuh.manager-1 cat /var/ossec/logs/w2airia.log

# Check Flask received
curl -s http://localhost:5000/api/alerts | python3 -m json.tool | head -20
```

`SOC-W-*` alerts should appear in both the Flask dashboard (`:5000`) and Wazuh dashboard (`:443`).

---

## Startup / Shutdown

**Start:**
```bash
cd ~/soc-lab/docker && docker compose up -d
sleep 60
docker exec docker-wazuh.manager-1 pip3 install requests 2>/dev/null
cd ~/soc-lab && source venv/bin/activate
nohup python dashboard/app.py > /tmp/flask-soc.log 2>&1 &
```

**Stop:**
```bash
pkill -f "dashboard/app.py"
cd ~/soc-lab/docker && docker compose down
```

---

## Severity Mapping

| Wazuh Level | Mapped Risk |
|-------------|------------|
| 0–3 | LOW |
| 4–6 | MEDIUM |
| 7–9 | HIGH |
| 10+ | CRITICAL |

---

## Verify

- [ ] Three containers running
- [ ] Indexer health "green"
- [ ] Agent Active
- [ ] FIM trigger → alert in Wazuh Dashboard
- [ ] Same alert forwarded to Flask Dashboard
- [ ] `SOC-W-*` alerts in `curl http://localhost:5000/api/alerts`

→ Phase 4 (coming soon)
