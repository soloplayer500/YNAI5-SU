# YNAI5 — Market Report Scheduler Setup
# Runs market-report.py 3x daily: 8 AM, 6 PM, 9 PM
# Run this ONCE as Administrator to register all tasks.
# Right-click this file → Run with PowerShell (as Administrator)

$WorkDir = "C:\Users\shema\OneDrive\Desktop\YNAI5-SU"
$Python  = (Get-Command python).Source
$Script  = "projects\crypto-monitoring\market-report.py"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 3) `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable

# ── Helper: create one task ───────────────────────────────────────────────────
function Register-ReportTask($TaskName, $Time) {
    $Action = New-ScheduledTaskAction `
        -Execute $Python `
        -Argument $Script `
        -WorkingDirectory $WorkDir

    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time

    Register-ScheduledTask `
        -TaskName   $TaskName `
        -TaskPath   "\YNAI5\" `
        -Action     $Action `
        -Trigger    $Trigger `
        -Settings   $Settings `
        -RunLevel   Limited `
        -Force | Out-Null

    Write-Host "  ✓ $TaskName — $Time daily" -ForegroundColor Green
}

Write-Host ""
Write-Host "YNAI5 — Registering Market Report Tasks" -ForegroundColor Cyan
Write-Host ""

Register-ReportTask "YNAI5-Report-Morning" "08:00AM"
Register-ReportTask "YNAI5-Report-Evening" "06:00PM"
Register-ReportTask "YNAI5-Report-Night"   "09:00PM"

Write-Host ""
Write-Host "All 3 tasks registered. Open Task Scheduler > YNAI5 folder to verify." -ForegroundColor Cyan
Write-Host "Script: $WorkDir\$Script" -ForegroundColor Gray
Write-Host ""
