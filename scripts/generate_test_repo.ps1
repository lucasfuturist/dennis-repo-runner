param(
    [string]$BasePath = "tests\fixtures",
    [switch]$SkipSnapshot = $false
)

$ErrorActionPreference = "Stop"

# Create unique timestamped name
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoName = "repo_$Timestamp"
$RepoPath = Join-Path $BasePath $RepoName

# Ensure directory exists
if (-not (Test-Path $RepoPath)) {
    New-Item -ItemType Directory -Path $RepoPath -Force | Out-Null
}

Write-Host "Generating random test repo at: $RepoPath" -ForegroundColor Cyan

# Helper to write files
function New-File($RelPath, $Content) {
    $Full = Join-Path $RepoPath $RelPath
    $Dir = Split-Path -Parent $Full
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
    # Note: PowerShell 5.1 'UTF8' adds BOM. This effectively tests our BOM stripping logic!
    Set-Content -Path $Full -Value $Content -Encoding UTF8
    Write-Host "  + $RelPath" -ForegroundColor Gray
}

# 1. Root Files
New-File "README.md" "# Test Repo $Timestamp`n`nGenerated for semantic import testing."
New-File "requirements.txt" "requests`nnumpy`npandas"

# 2. Python Source
New-File "src\main.py" @"
import os
import sys
from utils.logger import log_msg

def main():
    print(os.getcwd())
    log_msg('Start')
"@

New-File "src\utils\logger.py" @"
import datetime
# This is a comment
def log_msg(msg):
    print(f'{datetime.datetime.now()}: {msg}')
"@

New-File "src\utils\__init__.py" ""

# 3. TypeScript / JS Source
New-File "frontend\app.tsx" @"
import React from 'react';
import { Button } from './components/Button';
import './styles.css';

export const App = () => <Button />;
"@

New-File "frontend\components\Button.tsx" @"
import { useState } from 'react';
export const Button = () => <button>Click</button>;
"@

New-File "frontend\legacy.js" @"
const fs = require('fs');
const path = require('path');
// require('ignored');
"@

# 4. Nested Deep Logic (Ignored by default configs usually, but let's check imports)
New-File "scripts\deploy.py" @"
import boto3
import json
"@

Write-Host "`nGeneration Done." -ForegroundColor Green

if (-not $SkipSnapshot) {
    Write-Host "`nRunning Snapshot Capture..." -ForegroundColor Yellow
    
    # Define output folder inside the fixture
    $OutputDir = Join-Path $RepoPath "output"
    
    # Determine Project Root (parent of 'scripts') to run python module correctly
    $ScriptDir = Split-Path -Parent $PSCommandPath
    $ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
    
    # We must ignore the output directory so the scanner doesn't scan the results
    # Standard ignores + 'output'
    $Ignores = @(".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv", "output")
    
    Push-Location $ProjectRoot
    try {
        # Run src.cli.main with --export-flatten
        # We assume 'python' is in PATH.
        python -m src.cli.main snapshot "$RepoPath" --output-root "$OutputDir" --ignore $Ignores --export-flatten
        
        Write-Host "`nSnapshot Success!" -ForegroundColor Green
        Write-Host "Output located at: $OutputDir" -ForegroundColor Gray
        Write-Host "Flattened export:  $OutputDir\<SNAPSHOT_ID>\exports\flatten.md" -ForegroundColor Gray
    }
    catch {
        Write-Error "Failed to run snapshot: $_"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "Skipping snapshot run." -ForegroundColor Gray
    Write-Host "To run manually:" -ForegroundColor Yellow
    Write-Host "python -m src.cli.main snapshot $RepoPath --output-root $RepoPath/output --export-flatten" -ForegroundColor White
}