#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Wazuh Agent Installation Script
# SOC Lab Phase 3 — Multi-distro agent deployment
#
# Supports: Debian/Ubuntu, RHEL/CentOS/Fedora, Arch Linux
# Wazuh Version: 4.14.4
# Manager: 192.168.56.20 (Kali VM)
#
# Usage:
#   sudo ./install_agent.sh [OPTIONS]
#
# Options:
#   -m, --manager    Manager IP (default: 192.168.56.20)
#   -n, --name       Agent name (default: hostname)
#   -g, --group      Agent group (default: default)
#   -p, --protocol   Communication protocol (default: tcp)
#   -h, --help       Show this help
#
# Author: Zero (SOC Lab Phase 3)
# Version: 1.0.0
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ──────────────────────────────────────────────
# Defaults
# ──────────────────────────────────────────────
WAZUH_VERSION="4.14.4"
MANAGER_IP="192.168.56.20"
AGENT_NAME="$(hostname)"
AGENT_GROUP="default"
PROTOCOL="tcp"
WAZUH_DIR="/var/ossec"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ──────────────────────────────────────────────
# Functions
# ──────────────────────────────────────────────
log_info()  { echo -e "${GREEN}[+]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[-]${NC} $1"; }
log_step()  { echo -e "${CYAN}[*]${NC} $1"; }

show_help() {
    head -25 "$0" | tail -15
    exit 0
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID="${ID,,}"
        DISTRO_FAMILY=""
        
        case "$DISTRO_ID" in
            ubuntu|debian|kali|linuxmint|pop)
                DISTRO_FAMILY="debian"
                ;;
            rhel|centos|fedora|rocky|almalinux|amzn)
                DISTRO_FAMILY="rhel"
                ;;
            arch|manjaro|endeavouros|garuda)
                DISTRO_FAMILY="arch"
                ;;
            *)
                DISTRO_FAMILY="unknown"
                ;;
        esac
    elif [ -f /etc/debian_version ]; then
        DISTRO_FAMILY="debian"
        DISTRO_ID="debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO_FAMILY="rhel"
        DISTRO_ID="rhel"
    else
        DISTRO_FAMILY="unknown"
        DISTRO_ID="unknown"
    fi
    
    log_info "Detected: ${DISTRO_ID} (${DISTRO_FAMILY} family)"
}

check_connectivity() {
    log_step "Checking connectivity to manager ${MANAGER_IP}..."
    
    if ping -c 1 -W 3 "$MANAGER_IP" &>/dev/null; then
        log_info "Manager ${MANAGER_IP} is reachable"
    else
        log_error "Cannot reach manager at ${MANAGER_IP}"
        log_error "Check network configuration and firewall rules"
        exit 1
    fi
    
    # Check enrollment port
    if timeout 3 bash -c "echo >/dev/tcp/${MANAGER_IP}/1515" 2>/dev/null; then
        log_info "Enrollment port 1515 is open"
    else
        log_warn "Enrollment port 1515 may be blocked (agent may still connect)"
    fi
}

# ──────────────────────────────────────────────
# Debian/Ubuntu Installation
# ──────────────────────────────────────────────
install_debian() {
    log_step "Installing Wazuh agent via APT..."
    
    # Add Wazuh repository
    curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | \
        gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import 2>/dev/null && \
        chmod 644 /usr/share/keyrings/wazuh.gpg
    
    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | \
        tee /etc/apt/sources.list.d/wazuh.list
    
    apt-get update -qq
    
    WAZUH_MANAGER="$MANAGER_IP" \
    WAZUH_AGENT_NAME="$AGENT_NAME" \
    WAZUH_AGENT_GROUP="$AGENT_GROUP" \
    WAZUH_PROTOCOL="$PROTOCOL" \
        apt-get install -y wazuh-agent="${WAZUH_VERSION}-1"
    
    # Prevent auto-updates
    echo "wazuh-agent hold" | dpkg --set-selections
    
    log_info "APT installation complete"
}

# ──────────────────────────────────────────────
# RHEL/CentOS/Fedora Installation
# ──────────────────────────────────────────────
install_rhel() {
    log_step "Installing Wazuh agent via YUM/DNF..."
    
    rpm --import https://packages.wazuh.com/key/GPG-KEY-WAZUH 2>/dev/null
    
    cat > /etc/yum.repos.d/wazuh.repo << 'REPO'
[wazuh]
gpgcheck=1
gpgkey=https://packages.wazuh.com/key/GPG-KEY-WAZUH
enabled=1
name=Wazuh repository
baseurl=https://packages.wazuh.com/4.x/yum/
protect=1
REPO
    
    WAZUH_MANAGER="$MANAGER_IP" \
    WAZUH_AGENT_NAME="$AGENT_NAME" \
    WAZUH_AGENT_GROUP="$AGENT_GROUP" \
    WAZUH_PROTOCOL="$PROTOCOL" \
        yum install -y "wazuh-agent-${WAZUH_VERSION}-1"
    
    # Prevent auto-updates
    if command -v dnf &>/dev/null; then
        echo "exclude=wazuh-agent" >> /etc/dnf/dnf.conf
    else
        echo "exclude=wazuh-agent" >> /etc/yum.conf
    fi
    
    log_info "YUM/DNF installation complete"
}

# ──────────────────────────────────────────────
# Arch Linux Installation (from RPM extraction)
# ──────────────────────────────────────────────
install_arch() {
    log_step "Installing Wazuh agent on Arch Linux..."
    log_warn "No native Arch package — extracting from Docker image"
    
    # Check if Docker is available
    if ! command -v docker &>/dev/null; then
        log_error "Docker is required for Arch installation"
        log_error "Install Docker: sudo pacman -S docker && sudo systemctl start docker"
        exit 1
    fi
    
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running"
        log_error "Start Docker: sudo systemctl start docker"
        exit 1
    fi
    
    # Pull agent image and extract files
    log_step "Pulling Wazuh agent Docker image..."
    docker pull "wazuh/wazuh-agent:${WAZUH_VERSION}" 2>/dev/null
    
    log_step "Extracting agent files..."
    docker create --name wazuh-agent-extract "wazuh/wazuh-agent:${WAZUH_VERSION}" &>/dev/null
    docker cp wazuh-agent-extract:/var/ossec /var/ossec
    docker rm wazuh-agent-extract &>/dev/null
    
    # Create wazuh user/group
    groupadd -r wazuh 2>/dev/null || true
    useradd -r -g wazuh -d /var/ossec -s /usr/bin/nologin wazuh 2>/dev/null || true
    
    # Fix permissions
    chown -R root:wazuh /var/ossec
    chmod -R 770 /var/ossec
    
    # Create required directories
    mkdir -p /var/ossec/var/run
    mkdir -p /var/ossec/logs/integrations
    mkdir -p /var/ossec/queue/{alerts,diff,rids,sockets}
    mkdir -p /var/ossec/tmp
    
    touch /var/ossec/etc/client.keys
    chown root:wazuh /var/ossec/etc/client.keys
    chmod 660 /var/ossec/etc/client.keys
    
    # Configure manager connection
    configure_agent
    
    log_info "Arch installation complete"
}

# ──────────────────────────────────────────────
# Agent Configuration
# ──────────────────────────────────────────────
configure_agent() {
    log_step "Configuring agent..."
    
    local OSSEC_CONF="${WAZUH_DIR}/etc/ossec.conf"
    
    if [ ! -f "$OSSEC_CONF" ]; then
        log_error "ossec.conf not found at ${OSSEC_CONF}"
        exit 1
    fi
    
    # Set manager address
    sed -i "s|<address>.*</address>|<address>${MANAGER_IP}</address>|g" "$OSSEC_CONF"
    
    # Set protocol
    sed -i "s|<protocol>.*</protocol>|<protocol>${PROTOCOL}</protocol>|g" "$OSSEC_CONF"
    
    # Fix any placeholder values
    sed -i "s|MANAGER_IP|${MANAGER_IP}|g" "$OSSEC_CONF"
    sed -i "s|CHANGE_MANAGER_PORT|1514|g" "$OSSEC_CONF"
    sed -i "s|CHANGE_ENROLL_PORT|1515|g" "$OSSEC_CONF"
    sed -i "s|CHANGE_PROTOCOL|${PROTOCOL}|g" "$OSSEC_CONF"
    sed -i "s|CHANGE_[A-Z_]*||g" "$OSSEC_CONF"
    
    # Set enrollment manager address
    sed -i "s|<manager_address></manager_address>|<manager_address>${MANAGER_IP}</manager_address>|g" "$OSSEC_CONF"
    
    # Set agent name in enrollment
    if grep -q "<agent_name>" "$OSSEC_CONF"; then
        sed -i "s|<agent_name>.*</agent_name>|<agent_name>${AGENT_NAME}</agent_name>|g" "$OSSEC_CONF"
    fi
    
    log_info "Agent configured: manager=${MANAGER_IP}, name=${AGENT_NAME}, protocol=${PROTOCOL}"
}

# ──────────────────────────────────────────────
# Start Agent
# ──────────────────────────────────────────────
start_agent() {
    log_step "Starting Wazuh agent..."
    
    if [ "$DISTRO_FAMILY" = "arch" ]; then
        ${WAZUH_DIR}/bin/wazuh-control start
    else
        systemctl daemon-reload
        systemctl enable wazuh-agent
        systemctl start wazuh-agent
    fi
    
    sleep 3
    
    # Verify
    if [ "$DISTRO_FAMILY" = "arch" ]; then
        ${WAZUH_DIR}/bin/wazuh-control status
    else
        systemctl status wazuh-agent --no-pager -l
    fi
}

# ──────────────────────────────────────────────
# Uninstall Agent
# ──────────────────────────────────────────────
uninstall_agent() {
    log_step "Uninstalling Wazuh agent..."
    
    # Stop agent
    if [ -f "${WAZUH_DIR}/bin/wazuh-control" ]; then
        ${WAZUH_DIR}/bin/wazuh-control stop 2>/dev/null || true
    fi
    systemctl stop wazuh-agent 2>/dev/null || true
    systemctl disable wazuh-agent 2>/dev/null || true
    
    case "$DISTRO_FAMILY" in
        debian)
            apt-get remove --purge -y wazuh-agent 2>/dev/null || true
            rm -f /etc/apt/sources.list.d/wazuh.list
            rm -f /usr/share/keyrings/wazuh.gpg
            apt-get autoremove -y
            ;;
        rhel)
            yum remove -y wazuh-agent 2>/dev/null || true
            rm -f /etc/yum.repos.d/wazuh.repo
            ;;
        arch)
            # Manual cleanup for Arch
            rm -rf /var/ossec
            userdel wazuh 2>/dev/null || true
            groupdel wazuh 2>/dev/null || true
            ;;
    esac
    
    # Clean residual files
    rm -rf /var/ossec 2>/dev/null || true
    
    log_info "Wazuh agent uninstalled"
}

# ──────────────────────────────────────────────
# Parse Arguments
# ──────────────────────────────────────────────
ACTION="install"

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--manager)   MANAGER_IP="$2"; shift 2 ;;
        -n|--name)      AGENT_NAME="$2"; shift 2 ;;
        -g|--group)     AGENT_GROUP="$2"; shift 2 ;;
        -p|--protocol)  PROTOCOL="$2"; shift 2 ;;
        -u|--uninstall) ACTION="uninstall"; shift ;;
        -h|--help)      show_help ;;
        *)              log_error "Unknown option: $1"; show_help ;;
    esac
done

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
echo " Wazuh Agent ${ACTION^} — v${WAZUH_VERSION}"
echo " SOC Lab Phase 3"
echo "═══════════════════════════════════════════════════"
echo ""

check_root
detect_distro

if [ "$ACTION" = "uninstall" ]; then
    uninstall_agent
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo " Wazuh Agent Uninstalled"
    echo "═══════════════════════════════════════════════════"
    exit 0
fi

check_connectivity

case "$DISTRO_FAMILY" in
    debian) install_debian ;;
    rhel)   install_rhel ;;
    arch)   install_arch ;;
    *)
        log_error "Unsupported distribution: ${DISTRO_ID}"
        log_error "Supported: Debian/Ubuntu, RHEL/CentOS/Fedora, Arch Linux"
        exit 1
        ;;
esac

# Configure (debian/rhel set vars during install, arch calls configure_agent directly)
if [ "$DISTRO_FAMILY" != "arch" ]; then
    configure_agent
fi

start_agent

echo ""
echo "═══════════════════════════════════════════════════"
echo " Wazuh Agent Installed Successfully"
echo "═══════════════════════════════════════════════════"
echo ""
echo " Manager:  ${MANAGER_IP}"
echo " Agent:    ${AGENT_NAME}"
echo " Group:    ${AGENT_GROUP}"
echo " Protocol: ${PROTOCOL}"
echo ""
echo " Dashboard: https://${MANAGER_IP}"
echo " Credentials: admin / SecretPassword"
echo ""
echo " Check agent in dashboard -> Agents tab"
echo "═══════════════════════════════════════════════════"
