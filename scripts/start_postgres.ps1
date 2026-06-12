# Start the local dev PostgreSQL server (portable install, no Windows service).
#
# PostgreSQL 17 was installed as a portable binary distribution under
# %LOCALAPPDATA%\PostgreSQL\17 (no admin rights, no installer, no service).
# Run this script to start it; use the -Stop switch to stop it.
#
# Usage:
#   .\scripts\start_postgres.ps1
#   .\scripts\start_postgres.ps1 -Stop

param(
    [switch]$Stop
)

$pgBin = "$env:LOCALAPPDATA\PostgreSQL\17\bin"
$dataDir = "$env:LOCALAPPDATA\PostgreSQL\17\data"
$logFile = "$env:LOCALAPPDATA\PostgreSQL\17\server.log"

if ($Stop) {
    & "$pgBin\pg_ctl.exe" -D $dataDir stop
} else {
    & "$pgBin\pg_ctl.exe" -D $dataDir -l $logFile -o "-p 5432" start
}
