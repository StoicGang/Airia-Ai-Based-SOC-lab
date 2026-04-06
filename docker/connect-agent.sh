#!/bin/bash
# =============================================================
# Connect Wazuh Agent — Run this on Arch Linux VM (192.168.56.10)
# Manager: 192.168.56.20
# =============================================================

set -e

MANAGER_IP="192.168.56.20"
WAZUH_VERSION="4.14.4"

echo "═══════════════════════════════════════════"
echo "  Wazuh Agent Setup — Arch Linux"
echo "  Manager: $MANAGER_IP"
echo "═══════════════════════════════════════════"
echo ""

# Check if already installed
if [ -d "/var/ossec" ]; then
    echo "Wazuh agent already installed at /var/ossec"
    echo "Current status:"
    sudo /var/ossec/bin/wazuh-control status 2>/dev/null || echo "Not running"
    echo ""
    read -p "Reinstall? (y/N): " REINSTALL
    if [ "$REINSTALL" != "y" ]; then
        echo "Skipping install. Starting agent..."
        sudo systemctl start wazuh-agent 2>/dev/null || sudo /var/ossec/bin/wazuh-control start
        exit 0
    fi
fi

# Detect package manager
if command -v pacman &> /dev/null; then
    PKG_MGR="pacman"
elif command -v apt &> /dev/null; then
    PKG_MGR="apt"
else
    PKG_MGR="unknown"
fi

echo "Detected package manager: $PKG_MGR"

if [ "$PKG_MGR" = "apt" ]; then
    # Debian/Ubuntu method
    curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import 2>/dev/null && sudo chmod 644 /usr/share/keyrings/wazuh.gpg
    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
    sudo apt update
    WAZUH_MANAGER="$MANAGER_IP" sudo apt install -y wazuh-agent
else
    # Fallback: RPM via tarball
    echo "Using RPM package method..."
    wget -q "https://packages.wazuh.com/4.x/yum/wazuh-agent-${WAZUH_VERSION}-1.x86_64.rpm" -O /tmp/wazuh-agent.rpm
    
    if command -v rpm &> /dev/null; then
        sudo WAZUH_MANAGER="$MANAGER_IP" rpm -ivh /tmp/wazuh-agent.rpm
    elif command -v alien &> /dev/null; then
        cd /tmp && sudo alien -i wazuh-agent.rpm
    else
        echo "Cannot install RPM. Please install 'alien' or use the Wazuh tarball installer."
        echo "Download: https://packages.wazuh.com/4.x/linux/"
        exit 1
    fi
fi

# Configure manager IP
echo "Configuring manager IP: $MANAGER_IP"
if [ -f "/var/ossec/etc/ossec.conf" ]; then
    sudo sed -i "s/<address>.*<\/address>/<address>$MANAGER_IP<\/address>/" /var/ossec/etc/ossec.conf
fi

# Enable and start
sudo systemctl daemon-reload 2>/dev/null
sudo systemctl enable wazuh-agent 2>/dev/null
sudo systemctl start wazuh-agent 2>/dev/null || sudo /var/ossec/bin/wazuh-control start

echo ""
echo "✅ Wazuh agent installed and started"
echo ""
echo "Verify connection:"
echo "  sudo /var/ossec/bin/wazuh-control status"
echo ""
echo "Check on Wazuh dashboard:"
echo "  https://$MANAGER_IP → Agents tab"
