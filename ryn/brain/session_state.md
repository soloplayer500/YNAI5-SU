# Session State — RYN CORE v3
_Written: 2026-04-21 | Session: RYN CORE v3 System Lockdown + RAG Init_

---

## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| ynai5-dashboard | active (running) | enabled on VM |
| ynai5-gemini | active (running) | enabled on VM |
| ynai5-claude | active (running) | enabled on VM |
| ynai5-drive | active (running) | enabled on VM |
| nginx | active (running) | enabled on VM |
| Ollama | DISABLED | insufficient RAM on e2-micro (958MB/1GB used) |
| RAG Index | READY | 667 chunks, 49 files |

---

## Known Issues
- `ynai5-claude`: intermittent I/O errors on `/mnt/gdrive/SYNC/HEARTBEAT.json` — rclone flakiness, non-blocking
- Ollama: permanently disabled on YNAI5-VM due to RAM constraint — router bypasses via brain state

---

## Session Completed Tasks (RYN CORE v3)

- [x] Phase 0: System lockdown (local background scripts checked — none running)
- [x] Phase 1: ryn/ folder structure created (ryn-core/, ryn-vm/, ryn-local/, brain/, legacy/)
- [x] Phase 1: .gitignore updated with ryn/ runtime artifact exclusions
- [x] Phase 1: CLAUDE.md workspace map updated with full ryn/ tree
- [x] Phase 2: Security hardening — no hardcoded tokens found in tracked files
- [x] Phase 3: ryn/brain/state.json created (model availability, VM status)
- [x] Phase 3: ryn/brain/memory.md created (append-only brain notes)
- [x] Phase 3: ryn/brain/tasks.log created (append-only task log)
- [x] Phase 3: ryn/brain/communication.log created (inter-component log)
- [x] Phase 4: ryn/ryn-core/rag_indexer.py built (667 chunks, 49 files, keyword index)
- [x] Phase 4: RAG index built — rag_index_ready: true in state.json
- [x] Phase 5: router.py patched — reads brain/state.json, _model_available() guards on all _try_*()
- [x] Phase 6: This session_state.md written

---

## RAG Index Stats
- Files indexed: 49
- Total chunks: 667
- Built UTC: 2026-04-21T19:59:29Z
- Scan scope: CLAUDE.md, memory/, context/, docs/, projects/*/README.md, sessions/, playbooks/, ryn/brain/*.md

---

## Previous Session Context (Session 21)
- Ollama Docker image was downloading — likely done
- Open WebUI container was next (paused for this RYN CORE build)
- VM sessions: all 5 services enabled + active confirmed this session

---

## Next Session Startup
1. `python ryn/ryn-core/rag_indexer.py --query "your topic"` — RAG is live
2. Router brain awareness active — Ollama auto-skipped on VM
3. Continue Open WebUI / Ollama Docker setup if needed
4. Rebuild RAG index after adding new docs: `python ryn/ryn-core/rag_indexer.py --index`
