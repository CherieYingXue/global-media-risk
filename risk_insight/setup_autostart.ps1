$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptDir\start_server.bat`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "全球媒体风险洞察-开机启动服务" -Action $Action -Trigger $Trigger -Settings $Settings -Force
Write-Host "已注册：登录时自动启动 Web 服务"
