#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "   Building repo-runner v0.2 Executable   "
echo "=========================================="

# 1. Cleanup old build files
echo "Cleaning old build files..."
rm -rf build dist repo-runner.spec

# 2. Check Python Environment
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python is not installed." >&2
        exit 1
    fi
fi

# 3. Compile Binary via PyInstaller
echo "Compiling macOS Mach-O executable..."
$PYTHON_CMD -m PyInstaller --noconfirm --onefile --console --clean \
    --name "repo-runner" \
    --paths "." \
    --hidden-import "tkinter" \
    --collect-all "src" \
    src/entry_point.py

# 4. Success Check
EXE_PATH="dist/repo-runner"
if [ -f "$EXE_PATH" ]; then
    echo -e "\nBuild Success!"
    echo "Executable is ready at:"
    echo "  $(pwd)/$EXE_PATH"
else
    echo "Error: Build failed. No output file generated." >&2
    exit 1
fi