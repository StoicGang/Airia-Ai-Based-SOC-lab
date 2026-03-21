# Contributing to SOC Lab

Thank you for your interest in contributing. This is a learning-focused project — all skill levels welcome.

---

## 🐛 Reporting Issues

When opening an issue, include:
- Your OS and Kali Linux version
- The exact error message (full output)
- What you were doing when the error occurred
- What you already tried

---

## 🔧 Making Changes

### 1. Fork and clone
```bash
git clone https://github.com/YOUR-USERNAME/soc-lab.git
cd soc-lab
```

### 2. Create a branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/the-bug-you-are-fixing
```

### 3. Set up environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env
# Fill in your real credentials in config/.env
```

### 4. Make your changes

Keep these rules in mind:
- No credentials or API keys in any committed file
- No real IP addresses in documentation (use `192.168.x.x` placeholders)
- No pcap files, CSV files, or log files committed
- Follow the existing code style (clear variable names, comments on non-obvious logic)

### 5. Test your changes
```bash
sudo python scripts/soc_monitor.py
```
Confirm the full pipeline runs without errors.

### 6. Commit and push
```bash
git add .
git commit -m "feat: short description of what you added"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request
- Target the `main` branch
- Describe what you changed and why
- Include before/after output if relevant

---

## 💡 Ideas for Contributions

| Area | Ideas |
|------|-------|
| Detection | Add TCP SYN flood, UDP flood, or ARP spoofing detection |
| Output | Add email or Slack alert when escalation is triggered |
| Storage | Add SQLite database for storing alert history |
| Dashboard | Build a Flask web UI for the logs |
| Docs | Improve setup guide, add screenshots, translate to other languages |
| Tests | Add unit tests for `analyze_traffic()` and `generate_alert()` |

---

## 📋 Commit Message Format

```
type: short description

Types:
  feat     — new feature
  fix      — bug fix
  docs     — documentation only
  refactor — code change, no new feature or bug fix
  security — security improvement
```

---

## ⚠️ Security Note

This project is for **educational use in isolated lab environments only**.
Never run attack simulation scripts on networks you do not own or have explicit permission to test.
