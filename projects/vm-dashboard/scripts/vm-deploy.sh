#!/bin/bash
# YNAI5 VM Deploy — push dashboard changes from repo to VM
# Usage: ./vm-deploy.sh [VM_IP] [SSH_KEY_PATH]
# Run from YNAI5-SU repo root.

VM_IP="${1:-34.45.31.188}"
SSH_KEY="${2:-~/.ssh/google_compute_engine}"
LOCAL_DIR="$(dirname "$0")/../dashboard/"
REMOTE_DIR="shema@$VM_IP:~/YNAI5_AI_CORE/dashboard/"

echo "=== YNAI5 VM Deploy ==="
echo "Local:  $LOCAL_DIR"
echo "Remote: $REMOTE_DIR"
echo ""

# Sync files
rsync -avz --exclude="*.pyc" --exclude="__pycache__" \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
  "$LOCAL_DIR" "$REMOTE_DIR"

# Syntax check main.py before restarting
echo ""
echo "--- Syntax check ---"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "shema@$VM_IP" \
  "python3 -c 'import ast; ast.parse(open(\"/home/shema/YNAI5_AI_CORE/dashboard/main.py\").read()); print(\"main.py OK\")'"

# Restart dashboard
echo "--- Restarting ynai5-dashboard ---"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "shema@$VM_IP" \
  "sudo systemctl restart ynai5-dashboard && sleep 2 && curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8000"

echo ""
echo "Deploy complete."
