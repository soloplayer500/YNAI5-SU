# Oracle Cloud Free Tier — YNAI5 Setup Guide
_Created: 2026-03-29 | Always Free — no expiry_

---

## Why Oracle Cloud

- **4 vCPU / 24GB RAM ARM VM** — free forever (not a trial)
- Runs all YNAI5 automation 24/7 without touching the laptop
- Shami is also investing in Oracle stock — aligned incentive
- Replaces GitHub Actions limits (2000 min/mo) with unlimited VM cron

---

## What You Get (Always Free, No Expiry)

| Resource | Amount |
|----------|--------|
| ARM Ampere A1 VM | 4 OCPUs + 24GB RAM (1 big VM) |
| AMD micro VMs | 2x (1/8 OCPU, 1GB RAM each) |
| Block storage | 200GB total |
| Object storage | 10GB |
| Outbound data | 10TB/month |
| Public IPs | 2 free |

---

## Step 1 — Sign Up

**URL:** https://www.oracle.com/cloud/free/

- Use personal email
- Credit card required for verification — **will NOT be charged**
- **Region is permanent — choose carefully:**
  - US East/West = often FULL for A1 ARM VMs
  - Best options for Aruba: **São Paulo (GRU)**, **Amsterdam**, **Frankfurt**, **Santiago**
  - Pick São Paulo first — closest, usually has A1 availability
- Save your: tenancy name, username, password (store securely)

---

## Step 2 — Create the ARM VM

1. Console → **Compute** → **Instances** → **Create Instance**
2. Click **Change Shape** → **Ampere** → **VM.Standard.A1.Flex**
3. Set: **OCPUs = 4**, **Memory = 24 GB**
4. Image: **Ubuntu 22.04** (Canonical)
5. SSH keys: click "Generate a key pair" → download both files → save to `~/.ssh/oracle_ynai5`
6. Boot volume: **50 GB** (leave default)
7. Networking: default VCN, check **Assign a public IPv4 address**
8. Click **Create**

> If you get "Out of capacity" — wait and retry, or try a different region. A1 is in high demand.

---

## Step 3 — Connect to the VM

```bash
# On your laptop (Git Bash or WSL):
chmod 400 ~/.ssh/oracle_ynai5
ssh -i ~/.ssh/oracle_ynai5 ubuntu@<YOUR_VM_PUBLIC_IP>
```

---

## Step 4 — Initial VM Setup

Run these commands on the Oracle VM after SSH:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python + Docker + Git
sudo apt install -y python3 python3-pip python3-venv git curl wget
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu && newgrp docker

# Install pip packages globally
pip3 install requests python-dotenv anthropic

# Clone YNAI5-SU workspace
cd ~
git clone https://github.com/soloplayer500/YNAI5-SU.git
cd YNAI5-SU

# Create .env.local (copy keys from your laptop)
nano .env.local
# Paste all keys from your local .env.local — same content
```

---

## Step 5 — Open Firewall Port (if needed)

Oracle's default security list blocks most ports. For any web-facing services:

```bash
# In Oracle Console: Networking → VCN → Security Lists → Add Ingress Rule
# For SSH only (already open by default): port 22
# For any web app: add port 8080 or your app port
```

---

## Step 6 — Run Scripts as Systemd Services (24/7)

### monitor-loop.py (price alerts — MAIN daemon)

```bash
sudo nano /etc/systemd/system/ynai5-monitor.service
```

```ini
[Unit]
Description=YNAI5 Monitor Loop — Crypto Price Alerts
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/YNAI5-SU
ExecStart=/usr/bin/python3 projects/crypto-monitoring/monitor-loop.py
Restart=always
RestartSec=30
EnvironmentFile=/home/ubuntu/YNAI5-SU/.env.local

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ynai5-monitor
sudo systemctl start ynai5-monitor
sudo systemctl status ynai5-monitor
```

### telegram-claude-bridge.py (interactive bot)

```bash
sudo nano /etc/systemd/system/ynai5-bridge.service
```

```ini
[Unit]
Description=YNAI5 Telegram Claude Bridge
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/YNAI5-SU
ExecStart=/usr/bin/python3 projects/personal-ai-infrastructure/telegram-claude-bridge.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/YNAI5-SU/.env.local

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ynai5-bridge
sudo systemctl start ynai5-bridge
```

---

## Step 7 — Replace GitHub Actions with VM Cron

Once Oracle VM is live, move scheduled scripts from GitHub Actions to VM cron:

```bash
crontab -e
```

Add:
```cron
# Market Report — 9AM + 3PM AST (UTC-4 = 13:00 + 19:00 UTC)
0 13 * * * cd /home/ubuntu/YNAI5-SU && python3 projects/crypto-monitoring/market-report.py >> /tmp/market-report.log 2>&1
0 19 * * * cd /home/ubuntu/YNAI5-SU && python3 projects/crypto-monitoring/market-report.py >> /tmp/market-report.log 2>&1

# Morning Briefing — 9AM AST
0 13 * * * cd /home/ubuntu/YNAI5-SU && python3 projects/crypto-monitoring/morning-briefing.py >> /tmp/briefing.log 2>&1

# Portfolio sync — pull latest Kraken data every 30min (no Telegram alert, just JSON update)
*/30 * * * * cd /home/ubuntu/YNAI5-SU && python3 projects/crypto-monitoring/kraken/portfolio_monitor.py >> /tmp/portfolio.log 2>&1

# Auto-pull latest workspace from GitHub every hour
0 * * * * cd /home/ubuntu/YNAI5-SU && git pull --ff-only >> /tmp/git-pull.log 2>&1
```

---

## Step 8 — Keep Workspace Synced

The VM pulls from GitHub automatically (see cron above). To push changes from laptop to VM:

```bash
# On laptop: push as normal
git push

# VM auto-pulls hourly — or trigger manually:
ssh -i ~/.ssh/oracle_ynai5 ubuntu@<VM_IP> "cd ~/YNAI5-SU && git pull"
```

---

## Services on Oracle VM (Final State)

| Service | Type | Runs |
|---------|------|------|
| monitor-loop.py | systemd daemon | 24/7, alerts on threshold crossing |
| telegram-claude-bridge.py | systemd daemon | 24/7, responds to Telegram messages |
| market-report.py | cron | 9AM + 3PM AST |
| morning-briefing.py | cron | 9AM AST |
| portfolio_monitor.py | cron | Every 30min (JSON only, no Telegram noise) |
| screener-channel-bot.py | GitHub Actions | 8AM AST (Block Syndicate — keep on GH Actions) |

---

## Telegram Alerts — New Policy (once Oracle is live)

Only `monitor-loop.py` sends personal Telegram alerts — and only on:
- Price threshold crossings (e.g. OPN below $0.18)
- Big moves (>5% in 15 min)
- Daily noon heartbeat (optional, can disable)

All other scheduled Telegram noise = eliminated.

---

## Status

- [ ] Oracle account created
- [ ] ARM VM launched (VM.Standard.A1.Flex, 4 OCPU / 24GB)
- [ ] SSH access confirmed
- [ ] Initial setup done (Python, Docker, Git, .env.local)
- [ ] ynai5-monitor.service running
- [ ] ynai5-bridge.service running
- [ ] Cron jobs set up
- [ ] GitHub Actions portfolio-sync.yml stays paused (VM handles it)
