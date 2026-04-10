#!/bin/bash
# YNAI5 VM Health Check — run locally or via GitHub Actions
# Usage: ./vm-health-check.sh [VM_IP] [SSH_KEY_PATH]

VM_IP="${1:-34.45.31.188}"
SSH_KEY="${2:-~/.ssh/google_compute_engine}"

echo "=== YNAI5 VM Health Check ==="
echo "Target: $VM_IP"
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "shema@$VM_IP" "
  echo '--- FastAPI Endpoints (port 8000) ---'
  for ep in / /status.json /api/status /api/heartbeat /api/ynai5logs; do
    code=\$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000\$ep)
    echo \"\$ep → \$code\"
  done

  echo ''
  echo '--- Flask Endpoints (port 8001) ---'
  for ep in /health /api/env; do
    code=\$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001\$ep)
    echo \"\$ep → \$code\"
  done

  echo ''
  echo '--- Services ---'
  for svc in ynai5-dashboard ynai5-chat ynai5-drive nginx docker; do
    state=\$(systemctl is-active \$svc 2>/dev/null || echo 'unknown')
    echo \"\$svc → \$state\"
  done

  echo ''
  echo '--- System ---'
  free -m | grep Mem | awk '{print \"RAM: \" \$3 \"/\" \$2 \" MB used\"}'
  df -h / | tail -1 | awk '{print \"Disk: \" \$3 \"/\" \$2 \" used (\" \$5 \")\"}'
"
