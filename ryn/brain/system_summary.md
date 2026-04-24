# YNAI5 System Summary
_Human-readable snapshot. Updated after major events._

Last Updated: 2026-04-24T00:46:49Z

---

## VM State

| Component | Status | Notes |
|-----------|--------|-------|
| GCP e2-micro | RUNNING | 34.45.31.188, Ubuntu 24 |
| Disk | 78% (6.6G free) | Rotated 30MB rclone log |
| RAM available | ~297MB | Swap: 778MB engaged |
| ynai5-dashboard | active | Port 8000, /api/status HTTP 200 |
| ynai5-gemini | active | Running 2+ weeks |
| ynai5-claude | active | Running 11+ days |
| ynai5-drive | active | rclone mount |
| ynai5-monitor | active | Crypto price alerts |
| nginx | active | Reverse proxy |
| **ynai5-heartbeat** | **active** | 60s loop, RAM/disk/load/service alerts |
| **ynai5-commander** | **active** | Telegram command handler |
| Ollama | DISABLED | Insufficient RAM (1 vCPU e2-micro) |

---

## Control Layer

| Channel | Purpose | Status |
|---------|---------|--------|
| Telegram @SoloClaude5_bot | Alerts + commands | LIVE |
| Heartbeat alerts | Service down / RAM / load / log size | Active |
| Commander bot | /status /logs /restart /snapshot | Active |
| GitHub (this repo) | Source of truth, snapshots | Active |
| Remote exec | /ynai5_runtime/scripts/remote_exec.sh | Ready |

---

## Telegram Commands

| Command | Response |
|---------|----------|
| `/status` | RAM, disk, load, all service states, last heartbeat |
| `/logs` | Last 20 lines of heartbeat.log |
| `/restart <svc>` | Restart: dashboard, gemini, nginx (safe list only) |
| `/snapshot` | Triggers GitHub brain update notice |

Security: responds ONLY to user ID 8569520396. All others silently ignored.

---

## Alert Conditions (Heartbeat)

| Condition | Threshold | Key |
|-----------|-----------|-----|
| dashboard down | != active | `dash` |
| nginx down | != active | `nginx` |
| RAM critical | < 100MB | `ram` |
| High CPU load | 1-min avg > 2.0 | `load` |
| Log oversized | any log > 20MB | `logsize_*` |

All alerts: fire once on breach, once on recovery. No spam.

---

## Log Rotation

| Log | Trigger | Versions kept |
|-----|---------|---------------|
| ~/ynai5-agent/heartbeat.log | 10MB | 3 |
| ~/ynai5-agent/command.log | 10MB | 3 |
| /ynai5_runtime/logs/*.log | 10MB | 3 |

Config: `/etc/logrotate.d/ynai5`

---

## System Model

```
[Telegram] ←→ [ynai5-commander] ← alerts ← [ynai5-heartbeat]
                     ↓
              [systemctl / shell]
                     ↓
              [VM services]

[GitHub repo] ← source of truth, snapshots, scripts
[Claude Code] ← execution engine (local or remote)
```

---

## Known Issues

- rclone-drive.log was 30MB — rotated (now 0B, .1 backup retained)
- RAM swap at 778MB — stable, monitor
- `.log.1` backfiles ~30MB+ (compress on next rotation cycle)
