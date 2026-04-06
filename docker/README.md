# Wazuh SOC Lab — Phase 3

## Overview
Standalone Wazuh SIEM deployment via Docker for the AI-Powered SOC Lab.

- **Version:** Wazuh 4.14.4
- **Architecture:** Single-node (Manager + Indexer + Dashboard)
- **Target Host:** Kali Linux VM (192.168.56.20)
- **Agent:** Arch Linux VM (192.168.56.10)

## Requirements
- Docker Engine (latest stable)
- Docker Compose v2+
- Minimum 4 CPU cores, 8 GB RAM, 50 GB disk
- Internet access (to pull images on first run)

## Quick Start

```bash
# 1. Extract the zip
unzip wazuh-soc-phase3.zip
cd wazuh-soc-phase3

# 2. Run setup (generates certs, sets kernel params, pulls images)
chmod +x setup.sh
./setup.sh

# 3. Start Wazuh
docker compose up -d

# 4. Wait 2-5 minutes, then access dashboard
# https://192.168.56.20
# Username: admin
# Password: SecretPassword
```

## File Structure
```
wazuh-soc-phase3/
├── docker-compose.yml              # Main stack definition
├── generate-indexer-certs.yml      # Certificate generator compose file
├── setup.sh                        # One-click setup script
├── README.md                       # This file
├── connect-agent.sh                # Agent connection helper
└── config/
    ├── certs.yml                   # Certificate node definitions
    ├── wazuh_cluster/
    │   └── wazuh_manager.conf      # Manager configuration (ossec.conf)
    ├── wazuh_indexer/
    │   ├── wazuh.indexer.yml       # OpenSearch configuration
    │   └── internal_users.yml      # User database
    ├── wazuh_dashboard/
    │   ├── opensearch_dashboards.yml  # Dashboard configuration
    │   └── wazuh.yml               # API connection config
    └── wazuh_indexer_ssl_certs/    # Generated after setup.sh (empty initially)
```

## Credentials

| Service | Username | Password |
|---------|----------|----------|
| Dashboard | admin | SecretPassword |
| API | wazuh-wui | MyS3cr37P450r.*- |

⚠️ **Change these passwords in production.** For lab use, defaults are fine.

## Connecting the Arch Linux Agent (192.168.56.10)

Run the `connect-agent.sh` script on your Arch Linux VM, or manually:

```bash
# On Arch Linux VM (192.168.56.10):

# 1. Add Wazuh repo
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import && sudo chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list

# 2. Install agent
WAZUH_MANAGER="192.168.56.20" sudo apt install -y wazuh-agent

# For Arch (pacman), build from AUR or use the tarball:
# wget https://packages.wazuh.com/4.x/linux/wazuh-agent-4.14.4-1.x86_64.rpm
# sudo alien -i wazuh-agent-4.14.4-1.x86_64.rpm

# 3. Configure manager IP
sudo sed -i 's/MANAGER_IP/192.168.56.20/' /var/ossec/etc/ossec.conf

# 4. Start agent
sudo systemctl daemon-reload
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent

# 5. Verify
sudo /var/ossec/bin/wazuh-control status
```

## Troubleshooting

### Indexer won't start
```bash
# Check vm.max_map_count
sysctl vm.max_map_count
# Must be 262144. If not:
sudo sysctl -w vm.max_map_count=262144
```

### Dashboard shows "Wazuh not ready"
```bash
# Wait 2-5 minutes after first start
# Check all containers are running:
docker compose ps
# Check logs:
docker compose logs wazuh.manager
```

### Port conflicts
```bash
# Check if ports 443, 1514, 1515, 9200 are free:
sudo ss -tulpn | grep -E '443|1514|1515|9200'
```

### Reset everything
```bash
docker compose down -v  # Removes all volumes (data loss!)
rm -rf config/wazuh_indexer_ssl_certs/*
./setup.sh
docker compose up -d
```

## GRC Framing (for Resume/Portfolio)
- "Deployed Wazuh SIEM per ISO 27001 Annex A.8 (Asset Management) and A.12 (Operations Security)"
- "Implemented continuous security monitoring mapped to NIST CSF Detect function"
- "Configured file integrity monitoring, vulnerability detection, and log analysis in containerized SIEM environment"
