#!/bin/bash
# =============================================================
# Wazuh SOC Lab — Phase 3 Setup Script
# Target: Kali Linux VM (192.168.56.20)
# Version: Wazuh 4.14.4 (Single-Node)
# =============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Wazuh SOC Lab — Phase 3 Setup            ${NC}"
echo -e "${GREEN}  Wazuh 4.14.4 | Single-Node | Docker      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""

# Step 1: Check Docker
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Install it first:${NC}"
    echo "  sudo apt update && sudo apt install -y docker.io docker-compose-plugin"
    echo "  sudo systemctl enable --now docker"
    echo "  sudo usermod -aG docker \$USER"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Docker daemon is not running. Start it:${NC}"
    echo "  sudo systemctl start docker"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Step 2: Check docker compose
echo -e "${YELLOW}[2/5] Checking Docker Compose...${NC}"
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Docker Compose not found. Install it:${NC}"
    echo "  sudo apt install -y docker-compose-plugin"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose available ($COMPOSE_CMD)${NC}"

# Step 3: Set vm.max_map_count
echo -e "${YELLOW}[3/5] Setting vm.max_map_count=262144...${NC}"
CURRENT_MAP=$(sysctl -n vm.max_map_count 2>/dev/null || echo "0")
if [ "$CURRENT_MAP" -lt 262144 ]; then
    sudo sysctl -w vm.max_map_count=262144
    # Make persistent
    if ! grep -q "vm.max_map_count" /etc/sysctl.conf 2>/dev/null; then
        echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf > /dev/null
    fi
    echo -e "${GREEN}✅ vm.max_map_count set to 262144 (persistent)${NC}"
else
    echo -e "${GREEN}✅ vm.max_map_count already set ($CURRENT_MAP)${NC}"
fi

# Step 4: Generate SSL certificates
echo -e "${YELLOW}[4/5] Generating SSL certificates...${NC}"
if [ -f "./config/wazuh_indexer_ssl_certs/root-ca.pem" ]; then
    echo -e "${GREEN}✅ Certificates already exist. Skipping.${NC}"
    echo "   (Delete config/wazuh_indexer_ssl_certs/ to regenerate)"
else
    $COMPOSE_CMD -f generate-indexer-certs.yml run --rm generator
    echo -e "${GREEN}✅ Certificates generated${NC}"
fi

# Step 5: Pull images
echo -e "${YELLOW}[5/5] Pulling Wazuh Docker images...${NC}"
$COMPOSE_CMD pull
echo -e "${GREEN}✅ Images pulled${NC}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup Complete!                           ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "Start Wazuh:"
echo -e "  ${YELLOW}$COMPOSE_CMD up -d${NC}"
echo ""
echo -e "Access Dashboard:"
echo -e "  ${YELLOW}https://192.168.56.20${NC}"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}SecretPassword${NC}"
echo ""
echo -e "Check status:"
echo -e "  ${YELLOW}$COMPOSE_CMD ps${NC}"
echo ""
echo -e "View logs:"
echo -e "  ${YELLOW}$COMPOSE_CMD logs -f${NC}"
echo ""
echo -e "Stop Wazuh:"
echo -e "  ${YELLOW}$COMPOSE_CMD down${NC}"
echo ""
echo -e "${YELLOW}⚠️  First startup takes 2-5 minutes.${NC}"
echo -e "${YELLOW}   Wait for all 3 containers to show 'healthy' before accessing dashboard.${NC}"
echo ""
echo -e "Connect Arch Linux agent (192.168.56.10):"
echo -e "  1. Install wazuh-agent on Arch"
echo -e "  2. Set WAZUH_MANAGER=192.168.56.20"
echo -e "  3. Start: sudo systemctl start wazuh-agent"
echo ""
