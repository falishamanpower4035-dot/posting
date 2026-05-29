Param(
    [switch]$InstallHourlyBot,
    [switch]$InstallScheduler
)

$ErrorActionPreference = 'Stop'

$root = "D:\posty\tripavail_ai"
$logs = Join-Path $root 'logs'
if (-not (Test-Path $logs)) { New-Item -ItemType Directory -Path $logs | Out-Null }

function New-TripAvailTask {
    param(
        [Parameter(Mandatory)] [string] $TaskName,
        [Parameter(Mandatory)] [string] $Cmd
    )
    $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/c $Cmd"
    $triggers = @(
        (New-ScheduledTaskTrigger -AtStartup),
        (New-ScheduledTaskTrigger -AtLogOn)
    )
$principal = New-ScheduledTaskPrincipal -UserId "${env:USERDOMAIN}\\${env:USERNAME}" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    $task = New-ScheduledTask -Action $action -Trigger $triggers -Principal $principal -Settings $settings
    try {
        Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
        Write-Host ("Installed Scheduled Task: {0}" -f $TaskName)
    } catch {
        Write-Warning ("Failed to install task {0}: {1}" -f $TaskName, $_.Exception.Message)
        throw
    }
}

## Default behavior: install Hourly Bot if no switches provided
$doHourly = $InstallHourlyBot.IsPresent -or (-not $PSBoundParameters.ContainsKey('InstallHourlyBot') -and -not $PSBoundParameters.ContainsKey('InstallScheduler'))

if ($doHourly) {
    $cmd = "cd /d $root && call venv\Scripts\activate.bat && python run_hourly_bot.py >> logs\tripavail_ai.log 2>&1"
    New-TripAvailTask -TaskName 'TripAvail Hourly Bot' -Cmd $cmd
}

if ($InstallScheduler) {
    $cmd = "cd /d $root && call venv\Scripts\activate.bat && python smart_scheduler.py --run >> logs\scheduler.log 2>&1"
    New-TripAvailTask -TaskName 'TripAvail Smart Scheduler' -Cmd $cmd
}

Write-Host 'Done. Tasks will start at startup and user logon. You can run them now from Task Scheduler.'

