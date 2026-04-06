# FAQ

### Do I need paid tools?
No. Airia free tier, Wazuh open source, tshark open source, VirtualBox free.

### Minimum RAM?
8GB host. Kali gets 3.5GB, Arch gets 1.5GB.

### VMware instead of VirtualBox?
Yes. Create a private network on `192.168.56.x` with static IPs.

### Ubuntu instead of Kali?
Yes. Install `tshark`, `docker`, `python3` manually.

### Different attacker distro?
Yes. Need `ping`, `nmap`, optionally `hping3`. Agent installer supports Debian/RHEL/Arch.

### Why two detection systems?
tshark catches network attacks (floods, scans). Wazuh catches host events (file changes, misconfigs). Real SOCs use both.

### Single VM?
Possible but defeats the attacker/defender separation.

### Does AI need internet?
Yes. Airia API calls go to `api.airia.ai` over HTTPS via NAT.

### Where is data stored?
| Data | Location |
|------|----------|
| Alerts + IOCs | `database/soc_lab.db` |
| AI reports | `logs/SOC-*_report.json` |
| Wazuh alerts | Wazuh Indexer (OpenSearch) |
| Packet captures | `logs/traffic.pcap` |
