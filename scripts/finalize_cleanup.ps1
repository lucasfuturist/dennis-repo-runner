<#
.SYNOPSIS
    Final cleanup script to remove temporary legacy test files
    after their content has been merged.
#>

$Root = Resolve-Path ".\tests"
$Unit = Join-Path $Root "unit"
$Integration = Join-Path $Root "integration"

$LegacyFiles = @(
    "unit/test_structure_legacy.py",
    "unit/test_graph_resolution_legacy.py",
    "unit/test_import_scanner_logic_legacy.py",
    "unit/test_normalizer_legacy.py",
    "unit/test_scanner_hardening_legacy.py",
    "integration/test_e2e_flow_legacy.py"
)

Write-Host ">>> Starting Final Cleanup..." -ForegroundColor Cyan

foreach ($file in $LegacyFiles) {
    $path = Join-Path $Root $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  Deleted: $file" -ForegroundColor Green
    } else {
        Write-Host "  Skipped: $file (Not found)" -ForegroundColor Gray
    }
}

Write-Host ">>> Cleanup Complete. Run 'python -m pytest' to verify." -ForegroundColor Cyan