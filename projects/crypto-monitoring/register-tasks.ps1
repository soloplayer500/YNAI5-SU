$WorkDir = "C:\Users\shema\OneDrive\Desktop\YNAI5-SU"
$Python = (Get-Command python).Source
$Script = "projects\crypto-monitoring\market-report.py"
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -RunOnlyIfNetworkAvailable -StartWhenAvailable

$Action1 = New-ScheduledTaskAction -Execute $Python -Argument $Script -WorkingDirectory $WorkDir
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00AM"
Register-ScheduledTask -TaskName "YNAI5-Report-Morning" -TaskPath "\YNAI5\" -Action $Action1 -Trigger $Trigger1 -Settings $Settings -RunLevel Limited -Force | Out-Null
Write-Host "Morning task registered: 08:00 AM"

$Action2 = New-ScheduledTaskAction -Execute $Python -Argument $Script -WorkingDirectory $WorkDir
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "06:00PM"
Register-ScheduledTask -TaskName "YNAI5-Report-Evening" -TaskPath "\YNAI5\" -Action $Action2 -Trigger $Trigger2 -Settings $Settings -RunLevel Limited -Force | Out-Null
Write-Host "Evening task registered: 06:00 PM"

$Action3 = New-ScheduledTaskAction -Execute $Python -Argument $Script -WorkingDirectory $WorkDir
$Trigger3 = New-ScheduledTaskTrigger -Daily -At "09:00PM"
Register-ScheduledTask -TaskName "YNAI5-Report-Night" -TaskPath "\YNAI5\" -Action $Action3 -Trigger $Trigger3 -Settings $Settings -RunLevel Limited -Force | Out-Null
Write-Host "Night task registered: 09:00 PM"

Write-Host "Done."
