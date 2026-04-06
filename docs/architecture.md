# Architecture

## Overview

The SOC lab pipeline has 5 automated stages plus an AI analysis stage:

```
Stage 1        Stage 2        Stage 3        Stage 4        Stage 5
tshark    →    PCAP      →    CSV       →    alert     →    Airia AI
capture        file           analysis       .json          response
```

---

## Network Layout

```
VirtualBox Host-Only Network: 192.168.56.0/24

┌─────────────────────┐         ┌──────────────────────┐
│   Arch Linux VM     │         │    Kali Linux VM      │
│   192.168.56.10     │ ──────► │    192.168.56.20      │
│                     │  ICMP   │                       │
│   Attacker          │  flood  │   SOC Monitor + Target│
│   ping -c 500       │         │   tshark on eth0      │
└─────────────────────┘         └──────────┬────────────┘
                                            │
                                            │ HTTPS POST
                                            ▼
                                 ┌──────────────────────┐
                                 │   Airia Cloud API    │
                                 │   GPT-4o mini        │
                                 │   SOC Playbook loaded│
                                 └──────────────────────┘
```

Both VMs have two network adapters:
- **Adapter 1 (NAT):** Internet access for the Kali VM to reach the Airia API
- **Adapter 2 (Host-Only):** Private VM-to-VM communication at `192.168.56.x`

---

## Stage-by-Stage Breakdown

### Stage 1: Traffic Capture (`capture_traffic`)

**Tool:** tshark (Wireshark CLI)

**Command equivalent:**
```bash
tshark -i eth0 -f "icmp and dst host 192.168.56.20" -a duration:100 -w traffic.pcap
```

**What it does:**
- Listens on the host-only interface (`eth0`)
- Applies a BPF filter — only captures ICMP packets going TO the target IP
- Runs for exactly `CAPTURE_DURATION` seconds then stops automatically
- Saves raw binary packet data to a `.pcap` file

**Why ICMP only?** The BPF filter reduces noise — we only want to see ping traffic, not all network activity on the interface.

---

### Stage 2: CSV Conversion (`convert_to_csv`)

**Tool:** tshark in read mode

**What it does:**
- Reads the `.pcap` file
- Extracts 5 fields per packet: timestamp, src IP, dst IP, protocol, length
- Writes them as a comma-separated CSV with headers

**CSV columns:**

| Column | Example | Meaning |
|--------|---------|---------|
| `frame.time_epoch` | `1705312822.123` | Unix timestamp |
| `ip.src` | `192.168.56.10` | Attacker IP |
| `ip.dst` | `192.168.56.20` | Target IP |
| `ip.proto` | `1` | Protocol (1 = ICMP) |
| `frame.len` | `98` | Packet size in bytes |

---

### Stage 3: Traffic Analysis (`analyze_traffic`)

**Tool:** Python `collections.Counter`

**What it does:**
- Reads the CSV row by row
- Counts packets per source IP using a Counter dictionary
- If any IP exceeds `THRESHOLD` packets → returns that IP and count as suspicious

**Why a simple counter?** For this use case (ping flood detection), packet count per source is the right metric. A real SOC tool would also analyse timing, ports, protocols, and payload content.

---

### Stage 4: Alert Generation (`generate_alert`)

**What it does:**
- Generates a unique `SOC-XXXXXXXX` alert ID using UUID
- Attempts a reverse DNS lookup on the suspicious IP for the `source_host` field
- Builds a structured JSON alert matching the SOC playbook's input requirements
- Saves it to `logs/alert.json`

**Alert JSON structure:**
```json
{
  "alert_id": "SOC-2E867F0A",
  "alert_type": "Suspicious Network Volume",
  "indicator_type": "ip",
  "indicator_value": "192.168.56.10",
  "source_host": "Unknown",
  "destination_host": "Kali-SOC-Monitor",
  "destination_ip": "192.168.56.20",
  "protocol": "ICMP",
  "evidence": {
    "packet_count": 85,
    "time_window_seconds": 100,
    "threshold": 40,
    "data_source": "traffic.pcap"
  }
}
```

---

### Stage 5: AI Analysis (`send_to_airia`)

**Tool:** Airia API (GPT-4o mini with SOC playbook)

**What it does:**
- POSTs the alert JSON to the Airia execution API
- The Airia agent processes it through 10 playbook sections
- Returns a structured JSON report
- The `parse_airia_response()` function extracts the inner JSON from Airia's wrapper

**Airia API request format:**
```json
{
  "userInput": "<alert JSON as string>",
  "asyncOutput": false
}
```

**Airia response wrapper:**
```json
{
  "$type": "string",
  "result": "{ ...actual SOC report JSON... }",
  "executionId": "...",
  "files": []
}
```

The `result` field contains the actual SOC analysis as a JSON string that needs to be parsed separately.

---

## Credential Security

All secrets are stored in `config/.env` which is excluded from version control via `.gitignore`.

```
config/
├── .env          ← Real credentials — never committed
└── .env.example  ← Placeholder template — safe to commit
```

The script uses `python-dotenv` to load variables at runtime:
```python
load_dotenv(dotenv_path=ENV_PATH)
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY")
```

If `.env` is missing or unconfigured, `validate_config()` exits with a clear error message before any network activity.
