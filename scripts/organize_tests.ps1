<#
.SYNOPSIS
    Standardizes the tests/ directory structure.
    Safely moves, renames, and groups tests.
#>

$ErrorActionPreference = "Stop"

$Root = Resolve-Path ".\tests"
$Unit = Join-Path $Root "unit"
$Integration = Join-Path $Root "integration"
$Fixtures = Join-Path $Root "fixtures"

Write-Host ">>> Starting Test Reorganization..." -ForegroundColor Cyan

# 1. Ensure clean structure
if (-not (Test-Path $Unit)) { New-Item -ItemType Directory -Path $Unit | Out-Null }
if (-not (Test-Path $Integration)) { New-Item -ItemType Directory -Path $Integration | Out-Null }
if (-not (Test-Path $Fixtures)) { New-Item -ItemType Directory -Path $Fixtures | Out-Null }

# 2. Clean up timestamped debris
Write-Host "Cleaning up legacy fixtures..." -ForegroundColor Yellow
Get-ChildItem -Path $Fixtures -Directory | Where-Object { $_.Name -match "repo_\d+" } | Remove-Item -Recurse -Force
Get-ChildItem -Path (Join-Path $Root "temp-test-output") -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# 3. Move CLI Tests from Unit -> Integration
Write-Host "Moving CLI tests to integration..." -ForegroundColor Yellow
$CliTests = @("test_cli_diff.py", "test_cli_slice.py")
foreach ($file in $CliTests) {
    $src = Join-Path $Unit $file
    if (Test-Path $src) {
        Move-Item $src -Destination $Integration -Force
        Write-Host "  Moved $file -> integration/" -ForegroundColor Gray
    }
}

# 4. Standardize Unit Test Names (Module-based naming)
# We rename specific files to match their source module explicitly.

$Renames = @{
    "test_normalizer.py" = "test_path_normalizer.py"
    "test_scanner_hardening.py" = "test_filesystem_scanner.py"
    "test_fingerprint_hardening.py" = "test_file_fingerprint.py"
    "test_graph_resolution.py" = "test_graph_builder.py"
    "test_structure.py" = "test_structure_builder.py"
    "test_import_scanner_logic.py" = "test_import_scanner.py"
}

Write-Host "Consolidating Unit Tests..." -ForegroundColor Yellow

foreach ($key in $Renames.Keys) {
    $oldName = $key
    $targetName = $Renames[$key]
    
    $oldPath = Join-Path $Unit $oldName
    $targetPath = Join-Path $Unit $targetName

    if (Test-Path $oldPath) {
        if (Test-Path $targetPath) {
            # Target exists (Collision). Rename old file to _legacy for manual merge.
            $legacyName = $oldName.Replace(".py", "_legacy.py")
            $legacyPath = Join-Path $Unit $legacyName
            Rename-Item -Path $oldPath -NewName $legacyName
            Write-Host "  Collision: Renamed $oldName -> $legacyName (Please merge content manually into $targetName)" -ForegroundColor Magenta
        } else {
            # Safe to rename
            Rename-Item -Path $oldPath -NewName $targetName
            Write-Host "  Renamed $oldName -> $targetName" -ForegroundColor Green
        }
    }
}

# 5. Consolidate Integration Tests
# Merge full_snapshot and snapshot_flow conceptually by grouping them
$E2EMapping = @{
    "test_full_snapshot.py" = "test_e2e_snapshot.py"
    "test_snapshot_flow.py" = "test_e2e_flow_legacy.py"
}

foreach ($key in $E2EMapping.Keys) {
    $src = Join-Path $Integration $key
    $dest = Join-Path $Integration $E2EMapping[$key]
    if (Test-Path $src) {
        Rename-Item $src -NewName $dest
        Write-Host "  Renamed $key -> $($E2EMapping[$key])" -ForegroundColor Green
    }
}

# 6. Cleanup Root Scratchpads
$Scratchpads = @("clean_test.py", "drift_test.py")
foreach ($file in $Scratchpads) {
    if (Test-Path ".\$file") {
        Move-Item ".\$file" -Destination ".\scripts\" -Force
        Write-Host "  Moved root scratchpad $file -> scripts/" -ForegroundColor Gray
    }
}

Write-Host ">>> Reorganization Complete." -ForegroundColor Cyan
Write-Host "Next Steps:"
Write-Host "1. Run 'pytest' to ensure baseline passes."
Write-Host "2. Manually copy useful code from *_legacy.py files into their main counterparts."
Write-Host "3. Delete *_legacy.py files once merged."