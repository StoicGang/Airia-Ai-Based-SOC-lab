# Troubleshooting

All known errors with exact fixes.

---

## tshark Dissector Bug (exit code 8)

**Error:**
```
tshark: Dissector bug: Invalid leading, duplicated or trailing '.' found in filter name
Command returned non-zero exit status 8.
```

**Fix A — Reinstall:**
```bash
sudo apt remove --purge tshark wireshark-common -y
sudo apt install tshark wireshark-common -y
sudo usermod -aG wireshark $USER
newgrp wireshark
```

**Fix B — Use interface number instead of name:**
```bash
sudo tshark -D   # find the number next to your interface
```
In `config/.env` change:
```
INTERFACE=2      # use the number, not eth0
```

---

## PCAP File is 0 Bytes / Very Small

**Cause:** No pings arrived during the capture window, or wrong interface.

**Fix — Test capture manually:**
```bash
# Terminal 1: 15-second test capture
sudo tshark -i eth0 -f "icmp and dst host 192.168.56.20" -a duration:15

# Windows VM immediately: send test pings
ping 192.168.56.20 -n 5
```
If nothing appears → wrong interface. Try `eth1` or use interface number from `tshark -D`.

---

## No Internet From Kali Terminal

**Symptom:** `ping 8.8.8.8` returns "Destination Host Unreachable"

**Cause:** No default gateway route on the NAT adapter.

**Fix:**
```bash
# Get IP on NAT adapter
sudo dhclient eth1

# Add default gateway (VirtualBox NAT is always 10.0.2.2)
sudo ip route add default via 10.0.2.2 dev eth1

# Test
ping 8.8.8.8 -c 3
```

**Make permanent:**
```bash
sudo nano /etc/network/interfaces
```
Add under eth1 section:
```
post-up ip route add default via 10.0.2.2 dev eth1 || true
```

**If DNS also broken** (`Temporary failure in name resolution`):
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
sudo chattr +i /etc/resolv.conf   # prevent overwrite
```

---

## Airia API: HTTP 401 Unauthorized

**Fix:** API key is wrong or expired.
- Log into airia.com → Account Settings → API Keys
- Delete old key → Create new key
- Update `config/.env` with new key

---

## Airia API: HTTP 404 Not Found

**Fix:** API URL is wrong.
- Log into airia.com → your project → Integration tab
- Copy the Execution URL again
- Update `AIRIA_API_URL` in `config/.env`

---

## Airia Returns Plain Text (Not JSON)

**Symptom:** Response is conversational text instead of a JSON object.

**Fix:** System prompt was not saved in Airia.
1. Open your project in Airia
2. Find System Prompt / Instructions field
3. Verify the full playbook is there
4. Confirm the last line of Section 8 reads: `Do not add any text before or after the JSON.`
5. Click **Save**

---

## Config Not Loading / Still Placeholders

**Symptom:**
```
[!] AIRIA_API_URL is missing or still placeholder
[!] Expected .env at: /home/kali/soc-lab/config/.env
```

**Fix:**
```bash
# Check the file exists
ls -la ~/soc-lab/config/.env

# If missing — create it
cp ~/soc-lab/config/.env.example ~/soc-lab/config/.env
nano ~/soc-lab/config/.env   # fill in real values

# Check it loads correctly
cd ~/soc-lab
source venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv('config/.env')
print('URL:', os.getenv('AIRIA_API_URL', 'NOT FOUND'))
print('KEY:', 'SET' if os.getenv('AIRIA_API_KEY') else 'NOT FOUND')
"
```

---

## VMs Cannot Ping Each Other

**Windows can't receive pings from Kali:**
```cmd
rem Windows VM — CMD as Administrator
netsh advfirewall firewall add rule name="ICMP In" protocol=icmpv4:8,any dir=in action=allow
netsh advfirewall firewall add rule name="ICMP Out" protocol=icmpv4:8,any dir=out action=allow
```

**Kali not responding to pings:**
```bash
sudo ufw allow icmp
# or if ufw is causing issues:
sudo ufw disable
```

**Neither can reach each other:**
- Check both VMs have Host-Only Adapter 2 enabled in VirtualBox settings
- Confirm IPs: `ip a` on Kali, `ipconfig` on Windows

---

## ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Fix:** Virtual environment not activated.
```bash
cd ~/soc-lab
source venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Status Check

```bash
#!/bin/bash
echo "=== SOC Lab Status ==="
ip a show eth0 | grep "inet " && echo "✅ Kali IP set" || echo "❌ No IP on eth0"
ping -c1 -W1 192.168.56.10 >/dev/null && echo "✅ Windows reachable" || echo "❌ Windows unreachable"
ping -c1 -W2 8.8.8.8 >/dev/null && echo "✅ Internet working" || echo "❌ No internet"
tshark --version >/dev/null 2>&1 && echo "✅ tshark OK" || echo "❌ tshark missing"
[ -f ~/soc-lab/config/.env ] && echo "✅ .env exists" || echo "❌ .env missing"
grep -q "YOUR-PROJECT-ID" ~/soc-lab/config/.env 2>/dev/null && echo "❌ .env not configured" || echo "✅ .env configured"
```
