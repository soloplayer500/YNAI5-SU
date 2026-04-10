# Next Session Startup — YNAI5 VM
_Written: 2026-04-10 (end of Session 21)_

## First Thing: Check VM Status
```bash
ssh -i ~/.ssh/google_compute_engine shema@34.45.31.188 "docker ps --format 'table {{.Names}}\t{{.Status}}' && free -m | grep -E 'Mem|Swap'"
```

---

## Resume: Ollama Docker Setup

### Step 1 — Check if Ollama image finished downloading
```bash
ssh -i ~/.ssh/google_compute_engine shema@34.45.31.188 "docker images | grep ollama"
```
- If image shows → go to Step 2
- If not → `cd ~/YNAI5_AI_CORE && docker compose up -d ollama` (triggers pull)

### Step 2 — Start Ollama container + pull phi3:mini into Docker volume
```bash
ssh shema@34.45.31.188 "cd ~/YNAI5_AI_CORE && docker compose up -d ollama && sleep 5 && docker exec ollama ollama pull phi3:mini"
```
(This takes ~3 min — model downloads into Docker volume, not systemd path)

### Step 3 — Test inference via REST API (no spinner)
```bash
ssh shema@34.45.31.188 "curl -s -X POST http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{\"model\":\"phi3:mini\",\"prompt\":\"Reply in one sentence: what is YNAI5?\",\"stream\":false}' \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d[\"response\"][:200]);print(\"tok/s:\",round(d[\"eval_count\"]/d[\"eval_duration\"]*1e9,1))'"
```

### Step 4 — Start Open WebUI
```bash
ssh shema@34.45.31.188 "cd ~/YNAI5_AI_CORE && docker compose up -d open-webui && sleep 5 && curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000"
# Expected: 200
```

### Step 5 — Add nginx proxy for Open WebUI (so you can access it via browser)
Add to `/etc/nginx/sites-enabled/ynai5` under the existing server block:
```nginx
location /webui/ {
    proxy_pass http://127.0.0.1:3000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```
Then: `sudo nginx -t && sudo systemctl reload nginx`
Access at: `http://34.45.31.188/webui/`

---

## End of Month — VM Upgrade Plan
When payday hits, upgrade from e2-micro → e2-small for real Phi-3 speed:
```bash
# Stop VM (do this from GCP console or:)
gcloud compute instances stop ynai5-vm --zone=us-central1-a
gcloud compute instances set-machine-type ynai5-vm --machine-type=e2-small --zone=us-central1-a
gcloud compute instances start ynai5-vm --zone=us-central1-a
```
Cost: ~$13/month. Phi-3 goes from 1-2 tok/s → 8-15 tok/s (usable for real-time chat).

---

## Other Things Queued (From Previous Sessions)
- Perplexity API key → generate at perplexity.ai/settings/api → paste in YNAI5-KEY-INPUT.txt → adds to .env.local
- Wire `research-mcp` + `perplexity-mcp` (waiting on key)
- n8n event bus — wire Gemini worker + Claude runner through n8n for proper agent orchestration
- Netdata → dashboard widget (future STATUS BOARD tab enhancement)
- Health check Telegram alert activates automatically at 9AM AST daily (first run tomorrow)

---

## VM Quick Reference
| Thing | Location |
|-------|----------|
| Dashboard source | `~/YNAI5_AI_CORE/dashboard/` |
| Start all services | `cd ~/YNAI5_AI_CORE && docker compose up -d` |
| Full health check | `curl -s http://127.0.0.1:8000/status.json` |
| Logs | `/ynai5_runtime/logs/` |
| YNAI5 event log | `~/YNAI5_AI_CORE/logs/ynai5logs.json` |
| Models config | `~/YNAI5_AI_CORE/dashboard/config/models.json` |
| Chat server | Flask on port 8001 (`chat_server.py`) |
| Dashboard API | FastAPI on port 8000 (`main.py`) |
| Ollama (Docker) | port 11434 |
| Open WebUI | port 3000 (after setup) |
| n8n | port 5678 |
