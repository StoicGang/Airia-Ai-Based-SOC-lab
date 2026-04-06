# Setup Guide

Complete step-by-step instructions to build this lab from scratch.

---

## Requirements

| Item | Minimum | Notes |
|------|---------|-------|
| Host RAM | 8 GB | 2 GB for each VM + host OS |
| Host disk | 60 GB free | ~20 GB per VM |
| Internet | Required | For Airia API calls from Kali |
| VirtualBox | 7.x | Free at virtualbox.org |

---

## Step 1: Create the VMs

### Host-Only Network (do this first)
VirtualBox → File → Tools → Network Manager
```
IPv4 Address:  192.168.56.1
Subnet mask:   255.255.255.0
DHCP: Enabled
```

### Kali Linux VM
- Download: https://kali.org/get-kali/#kali-virtual-machines (VirtualBox .ova)
- Import: VirtualBox → File → Import Appliance
- RAM: 2048 MB
- Network Adapter 1: NAT
- Network Adapter 2: Host-only Adapter

### Arch Linux VM
- Download ISO: https://archlinux.org/download/
- New VM: 2048 MB RAM, 40 GB disk
- Network Adapter 1: NAT
- Network Adapter 2: Host-only Adapter
- Install Arch Linux (base install is sufficient for the lab)

---

## Step 2: Assign Static IPs

### Kali — set eth0 (or your host-only interface) to 192.168.56.20
```bash
sudo nano /etc/network/interfaces
```
Add:
```
auto eth0
iface eth0 inet static
    address 192.168.56.20
    netmask 255.255.255.0
```
```bash
sudo systemctl restart networking
```

### Arch Linux — set enp0s3 (host-only adapter) to 192.168.56.10

Create the systemd-networkd config file:
```bash
sudo nano /etc/systemd/network/20-hostonly.network
```
Add:
```ini
[Match]
Name=enp0s3

[Network]
Address=192.168.56.10/24
```
```bash
sudo systemctl enable --now systemd-networkd
```

### Verify both VMs can reach each other
```bash
# From Kali:
ping 192.168.56.10 -c 4   # Should reach Arch Linux
```
```bash
# From Arch Linux:
ping 192.168.56.20 -c 4   # Should reach Kali
```

---

## Step 3: Kali Environment Setup

```bash
# Install tshark
sudo apt install tshark -y
# When asked: select YES for non-superusers
sudo usermod -aG wireshark $USER
newgrp wireshark

# Project folders
mkdir -p ~/soc-lab/{scripts,config,logs}

# Python environment
cd ~/soc-lab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 4: Airia Platform Setup

1. Create free account at https://airia.com
2. Create project: `SOC-Lab-Analyst`
3. Select model: GPT-4o mini
4. Paste the full SOC playbook from `docs/airia-playbook.md` as the system prompt
5. Test with a sample alert in the Airia chat (see playbook doc)
6. Copy your **API URL** and **API Key** from the Integration tab

---

## Step 5: Configure Credentials

```bash
cp config/.env.example config/.env
nano config/.env
```

Fill in:
```
AIRIA_API_URL=https://api.airia.ai/v2/PipelineExecution/YOUR-ID
AIRIA_API_KEY=ak-YOUR-KEY
DESTINATION_IP=192.168.56.20
INTERFACE=eth0
```

---

## Step 6: Run the Lab

### Terminal 1 — Kali (start monitor)
```bash
cd ~/soc-lab
source venv/bin/activate
sudo python scripts/soc_monitor.py
```

Wait for: `[+] Capturing on eth0 for 100s...`

### Immediately — Arch Linux VM (launch attack)
```bash
ping 192.168.56.20 -c 200 -s 64
```

### After 100 seconds — Kali shows the AI SOC report automatically.

---

## Common Issues

See [`docs/troubleshooting.md`](troubleshooting.md) for fixes to all known errors.

| Symptom | Quick fix |
|---------|-----------|
| tshark dissector bug / exit 8 | `sudo apt reinstall tshark wireshark-common` |
| 0 byte PCAP | Send pings immediately after "Capturing..." appears |
| No internet in terminal | `sudo ip route add default via 10.0.2.2 dev eth1` |
| Airia 401 error | Regenerate API key in Airia dashboard |
| Plain text from Airia | Re-save system prompt in Airia project |
