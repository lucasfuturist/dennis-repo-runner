<#
.SYNOPSIS
    The "Definition of Done" script.
    Runs the full test suite and checks for strictly passing conditions.
#>

$ErrorActionPreference = "Stop"

Write-Host ">>> 1. Checking Environment..." -ForegroundColor Cyan
python --version

Write-Host "`n>>> 2. Running Test Suite (Pytest)..." -ForegroundColor Cyan
# -v: verbose
# -rsf: report skipped/failed reasons
# -W ignore::DeprecationWarning: suppress noise
python -m pytest -v -rsf -W ignore::DeprecationWarning

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>>> ✅ VERIFICATION PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n>>> ❌ VERIFICATION FAILED" -ForegroundColor Red
    exit 1
}