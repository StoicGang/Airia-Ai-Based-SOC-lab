# Phase 1 — Base Detection Pipeline

**Goal:** Detect ICMP flood from Arch → Kali, send to Airia AI, get a SOC report.  
**Time:** ~1 hour

---

## Step 1 — Clone & Setup

```bash
cd ~
git clone https://github.com/StoicGang/Airia-Ai-Based-SOC-lab.git soc-lab
cd soc-lab
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 2 — Configure

```bash
cp config/.env.example config/.env
nano config/.env
```
```env
AIRIA_API_URL=https://api.airia.ai/v2/PipelineExecution/YOUR-PROJECT-ID
AIRIA_API_KEY=ak-YOUR-API-KEY
DESTINATION_IP=192.168.56.20
DESTINATION_HOST=Kali-SOC-Monitor
INTERFACE=eth1
```

> Use `ip addr` to find your host-only interface name.

---

## Step 3 — Run Monitor

On **Kali**:
```bash
sudo python scripts/soc_monitor.py
```

---

## Step 4 — Attack

On **Arch** (while monitor is capturing):
```bash
ping 192.168.56.20 -c 200 -s 64
```

---

## Step 5 — Verify

You should see a SOC report with risk score, MITRE mapping (T1498), and recommended actions. Report saved to `logs/`.

- [ ] Monitor detected ICMP flood (count > 40)
- [ ] Airia returned structured SOC report
- [ ] Report saved to `logs/`

→ [Phase 2](phase-2.md)
