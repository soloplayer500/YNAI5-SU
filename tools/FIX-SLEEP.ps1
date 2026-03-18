# FIX-SLEEP.ps1 — Prevent Windows sleep from killing Claude Code sessions
# Run as Administrator once. Keeps machine awake while plugged in.
# Run: Right-click → "Run with PowerShell" (as Admin)

Write-Host "=== YNAI5 Sleep Fix ===" -ForegroundColor Cyan
Write-Host "Disabling sleep/hibernate on AC power to prevent session crashes..." -ForegroundColor Yellow

# Disable sleep on AC power (plugged in)
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 0

# Disable sleep on DC (battery) — comment this out if you want battery sleep preserved
powercfg /change standby-timeout-dc 0
powercfg /change hibernate-timeout-dc 0

# Disable hibernation entirely
powercfg /hibernate off

Write-Host ""
Write-Host "Done. Settings applied:" -ForegroundColor Green
Write-Host "  AC Sleep: NEVER" -ForegroundColor Green
Write-Host "  AC Hibernate: NEVER" -ForegroundColor Green
Write-Host "  Monitor timeout: NEVER (AC)" -ForegroundColor Green
Write-Host "  Hibernate: DISABLED" -ForegroundColor Green
Write-Host ""
Write-Host "Claude Code sessions will no longer be killed by sleep/lock." -ForegroundColor Cyan
Write-Host "Screen may still lock (Ctrl+L) but processes stay alive." -ForegroundColor Gray
Write-Host ""
Write-Host "To restore defaults: powercfg /restoredefaultschemes" -ForegroundColor Gray
