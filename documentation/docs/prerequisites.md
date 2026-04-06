# Prerequisites

Complete everything here before Phase 1.

---

## 1. Install VirtualBox

[Download VirtualBox](https://www.virtualbox.org/wiki/Downloads).

---

## 2. Create Host-Only Network

VirtualBox → **File → Host Network Manager** → Create:
- IPv4: `192.168.56.1` / `255.255.255.0`
- DHCP: **Disabled**

---

## 3. Kali Linux VM (SOC Monitor)

[Download Kali VM image](https://www.kali.org/get-kali/#kali-virtual-machines)

| Setting | Value |
|---------|-------|
| RAM | 3.5 GB |
| CPUs | 2 |
| Adapter 1 | NAT |
| Adapter 2 | Host-Only (`vboxnet0`) |

Set static IP on host-only interface:
```bash
sudo nano /etc/network/interfaces
```
```
auto eth1
iface eth1 inet static
    address 192.168.56.20
    netmask 255.255.255.0
```
```bash
sudo ifup eth1
```

---

## 4. Arch Linux VM (Attacker)

[Download Arch ISO](https://archlinux.org/download/)

| Setting | Value |
|---------|-------|
| RAM | 1.5 GB |
| CPUs | 1 |
| Adapter 1 | NAT |
| Adapter 2 | Host-Only (`vboxnet0`) |

Set static IP:
```bash
sudo nano /etc/systemd/network/20-host-only.network
```
```ini
[Match]
Name=enp0s8

[Network]
Address=192.168.56.10/24
```
```bash
sudo systemctl restart systemd-networkd
```

---

## 5. Verify

```bash
# From Arch
ping 192.168.56.20

# From Kali
ping 192.168.56.10
```

---

## 6. Install Packages on Kali

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip tshark git docker.io docker-compose-v2
sudo usermod -aG wireshark $USER
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in
```

---

## 7. Create Airia Account

1. Sign up at [airia.com](https://airia.com) (free)
2. Create a Project
3. Copy the **Project Execution URL** and **API Key**
4. Set the system prompt to the SOC playbook from [`docs/airia-playbook.md`](https://github.com/StoicGang/Airia-Ai-Based-SOC-lab/blob/main/docs/airia-playbook.md)

---

## Checklist

- [ ] VirtualBox + host-only network created
- [ ] Kali at `192.168.56.20`, Arch at `192.168.56.10`
- [ ] VMs can ping each other
- [ ] tshark, Docker, Python 3.9+ installed on Kali
- [ ] Airia account with project URL + API key

→ [Phase 1](phase-1.md)
