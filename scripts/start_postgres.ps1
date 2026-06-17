# Start the local dev PostgreSQL server (portable install, no Windows service).
#
# PostgreSQL 17 was installed as a portable binary distribution under
# %LOCALAPPDATA%\PostgreSQL\17 (no admin rights, no installer, no service).
#
# The server is launched *detached* from the calling terminal. A portable
# Postgres started directly in an interactive console shares that console's
# process group, so a Ctrl+C, a window close, or a logoff broadcasts a console
# control event (CTRL_C_EVENT / CTRL_CLOSE_EVENT) to Postgres' background
# workers. They die with exception 0xC000013A (STATUS_CONTROL_C_EXIT), the
# postmaster then tears down all processes, and the database "shuts down
# unexpectedly". Running it via Start-Process in its own hidden window keeps it
# out of this terminal's console group so working-terminal Ctrl+C can't reach it.
#
# Usage:
#   .\scripts\start_postgres.ps1            # start (detached)
#   .\scripts\start_postgres.ps1 -Stop      # stop
#   .\scripts\start_postgres.ps1 -Status    # report running / stopped + PID

param(
    [switch]$Stop,
    [switch]$Status
)

$pgBin = "$env:LOCALAPPDATA\PostgreSQL\17\bin"
$dataDir = "$env:LOCALAPPDATA\PostgreSQL\17\data"
$logFile = "$env:LOCALAPPDATA\PostgreSQL\17\server.log"
$pgCtl = "$pgBin\pg_ctl.exe"

if ($Status) {
    & $pgCtl -D $dataDir status
    exit $LASTEXITCODE
}

if ($Stop) {
    & $pgCtl -D $dataDir stop
    exit $LASTEXITCODE
}

# Start detached: Start-Process gives pg_ctl its own hidden console, so the
# postmaster it spawns is never a member of *this* terminal's process group.
Start-Process -FilePath $pgCtl `
    -ArgumentList "-D `"$dataDir`" -l `"$logFile`" -o `"-p 5432`" start" `
    -WindowStyle Hidden

Write-Host "PostgreSQL start requested (detached). Verify with:"
Write-Host "  .\scripts\start_postgres.ps1 -Status"
