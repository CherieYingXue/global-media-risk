$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptDir\deploy.bat`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "全球媒体风险洞察-开机部署" -Action $Action -Trigger $Trigger -Settings $Settings -Force
Write-Host "已注册开机自动部署任务"
