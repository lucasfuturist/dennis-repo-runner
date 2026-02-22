$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Building repo-runner v0.2 Executable   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Function to handle stubborn directories
function Force-Delete ($Path) {
    if (Test-Path $Path) {
        Write-Host "Removing $Path..." -ForegroundColor Gray
        try {
            # Try standard delete
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
        } catch {
            # Fallback to CMD for deep paths or locked files
            Write-Host "   Standard delete failed (likely deep path). Using cmd.exe..." -ForegroundColor Yellow
            cmd /c "rmdir /s /q ""$Path"""
        }
    }
}

# 1. Cleanup
Force-Delete "build"
Force-Delete "dist"
if (Test-Path "repo-runner.spec") { Remove-Item "repo-runner.spec" -Force }

# 2. Check for PyInstaller (Safety Check)
if (-not (Get-Command "pyinstaller" -ErrorAction SilentlyContinue)) {
    # If not in PATH, we rely on python -m PyInstaller, which is fine.
    Write-Host "PyInstaller not in PATH, will use 'python -m PyInstaller'..." -ForegroundColor Gray
}

# 3. Build Command
Write-Host "Compiling..." -ForegroundColor Yellow

# Using python -m PyInstaller to avoid PATH issues
# --collect-all src: Bundles all code in src/
# --noconfirm: Don't ask to overwrite
python -m PyInstaller --noconfirm --onefile --console --clean `
    --name "repo-runner" `
    --paths "." `
    --hidden-import "tkinter" `
    --collect-all "src" `
    src/entry_point.py

# 4. Success Check
$ExePath = Join-Path (Get-Location).Path "dist\repo-runner.exe"
if (Test-Path $ExePath) {
    Write-Host "`nBuild Success!" -ForegroundColor Green
    Write-Host "Executable is ready at:" -ForegroundColor White
    Write-Host "  $ExePath" -ForegroundColor Cyan
} else {
    Write-Error "Build failed. No EXE found in dist/."
}