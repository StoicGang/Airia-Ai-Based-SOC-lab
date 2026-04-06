# AI-Powered SOC Analyst Lab

Step-by-step guide to build an AI-powered Security Operations Center from scratch.

---

## Sections

| Section | What you'll build | Time |
|---------|------------------|------|
| [Prerequisites](prerequisites.md) | VirtualBox + two VMs + networking | 1–2 hrs |
| [Phase 1](phase-1.md) | ICMP detection → Airia AI analysis | 1 hr |
| [Phase 2](phase-2.md) | Multi-attack rules + SQLite + Flask dashboard | 2 hrs |
| [Phase 3](phase-3.md) | Wazuh SIEM + agent + AIRIA integration | 3–4 hrs |
| [Troubleshooting](troubleshooting.md) | Common fixes | — |
| [FAQ](faq.md) | Frequently asked questions | — |

Complete them in order. Each phase builds on the previous one.

---

## Architecture

```
  Arch (Attacker)                    Kali (SOC Monitor)
  192.168.56.10                      192.168.56.20
       │                                  │
       │── ICMP/TCP/Scan ──────────────► tshark → rules → Airia AI ──┐
       │                                  │                           │
       │── Wazuh Agent (1514) ─────────► Wazuh Manager → w2airia ──┐ │
                                          │                         │ │
                                          │   Flask Dashboard :5000 ◄─┘
                                          │   Wazuh Dashboard :443
```

---

## Links

- [GitHub Repository](https://github.com/StoicGang/Airia-Ai-Based-SOC-lab)
- [Airia Platform](https://airia.com)
- [Wazuh Docs](https://documentation.wazuh.com)
