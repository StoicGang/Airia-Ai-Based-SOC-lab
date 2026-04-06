# Troubleshooting

---

## General

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | `source venv/bin/activate && pip install -r requirements.txt` |
| tshark permission denied | `sudo usermod -aG wireshark $USER` → log out/in |
| No packets captured | Wrong interface — check with `ip addr`, update `INTERFACE` in `.env` |
| Airia empty response | Verify API key and project URL in `.env` |

## Wazuh (Phase 3)

| Problem | Fix |
|---------|-----|
| `Pool overlaps` on compose up | `docker network prune` then retry |
| Indexer "red" status | Disk full — `docker system prune -af && docker volume prune` |
| Agent "Never connected" | Check manager IP in agent `ossec.conf`, verify port 1514 reachable |
| `No module named 'requests'` | `docker exec docker-wazuh.manager-1 pip3 install requests` |
| w2airia.log empty | Check `<integration>` in ossec.conf, check integratord running, force scan |
| Port 5000 in use | `pkill -f "dashboard/app.py"` then restart |
| Wazuh CDN AccessDenied | Extract from Docker image: `docker pull wazuh/wazuh-agent:4.14.4` → `docker cp` |

## Log Locations

| Log | Command |
|-----|---------|
| Flask | `cat /tmp/flask-soc.log` |
| Wazuh Manager | `docker exec docker-wazuh.manager-1 tail -50 /var/ossec/logs/ossec.log` |
| Integration | `docker exec docker-wazuh.manager-1 cat /var/ossec/logs/w2airia.log` |
| Wazuh Agent | `sudo tail -50 /var/ossec/logs/ossec.log` (on Arch) |
