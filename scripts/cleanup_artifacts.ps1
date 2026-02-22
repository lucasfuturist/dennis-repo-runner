<#
.SYNOPSIS
    Removes redundant scripts and temporary output folders 
    following the Pytest migration.
#>

$ErrorActionPreference = "Stop"
$Root = Resolve-Path "."

# Files to delete
$Files = @(
    "scripts/clean_test.py",
    "scripts/drift_test.py",
    "scripts/generate_test_repo.ps1",
    "scripts/organize_tests.ps1",
    "scripts/finalize_cleanup.ps1"
)

# Folders to delete
$Folders = @(
    "temp-test-output",
    "out"
)

Write-Host ">>> Starting Post-Migration Cleanup..." -ForegroundColor Cyan

foreach ($file in $Files) {
    $path = Join-Path $Root $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  Deleted: $file" -ForegroundColor Green
    }
}

foreach ($folder in $Folders) {
    $path = Join-Path $Root $folder
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
        Write-Host "  Deleted Folder: $folder" -ForegroundColor Green
    }
}

Write-Host ">>> Cleanup Complete." -ForegroundColor Cyan