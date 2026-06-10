# LSB local CI — mirrors .github/workflows/ci.yml (Blueprint Part 15.3 step d)
# Usage: .\scripts\ci.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { Write-Error "No .venv found - run: python -m venv .venv; .venv\Scripts\pip install pytest hypothesis psycopg2-binary pandas" }

Write-Host '== Unit tests =='
& $python -m pytest -q (Join-Path $root 'tests')
# Exit code 5 = no tests collected, allowed until the first module session
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) { Write-Error 'CI FAILED: pytest red' }

Write-Host '== Golden-fixture replay =='
$golden = Get-ChildItem (Join-Path $root 'tests\fixtures\golden') -Exclude '.gitkeep' -ErrorAction SilentlyContinue
if ($golden) {
    # Wired in Session 17 (Gate G2): replay every fixture set, fail on any byte difference.
    Write-Error 'CI FAILED: golden fixtures exist but the replay runner is not wired yet'
} else {
    Write-Host 'No golden fixtures yet (expected before Session 17) - skipping.'
}

Write-Host 'CI GREEN'
