$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$PSScriptRoot\daily_update.bat`""
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:00"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "全球媒体风险洞察-每日更新" -Action $Action -Trigger $Trigger -Settings $Settings -Force
Write-Host "已注册 Windows 计划任务：每日 06:00 生成报告"
