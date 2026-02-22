param(
    [string]$BasePath = "tests\fixtures",
    [switch]$SkipSnapshot = $false
)

$ErrorActionPreference = "Stop"

# Create unique timestamped name
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoName = "repo_$Timestamp"
$RepoPath = Join-Path $BasePath $RepoName

# Ensure absolute resolution for clickable links
$RepoRoot = (Resolve-Path ".").Path
$AbsRepoPath = Join-Path $RepoRoot $RepoPath

# Ensure directory exists
if (-not (Test-Path $AbsRepoPath)) {
    New-Item -ItemType Directory -Path $AbsRepoPath -Force | Out-Null
}

Write-Host "Generating random test repo at: $AbsRepoPath" -ForegroundColor Cyan

# Helper to write files
function New-File($RelPath, $Content) {
    $Full = Join-Path $AbsRepoPath $RelPath
    $Dir = Split-Path -Parent $Full
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
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

# 4. Nested Deep Logic
New-File "scripts\deploy.py" @"
import boto3
import json
"@

Write-Host "`nGeneration Done." -ForegroundColor Green

if (-not $SkipSnapshot) {
    Write-Host "`nRunning Snapshot Capture..." -ForegroundColor Yellow
    
    $OutputDir = Join-Path $AbsRepoPath "output"
    
    $ScriptDir = Split-Path -Parent $PSCommandPath
    $ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
    
    $Ignores = @(".git", "node_modules", "__pycache__", "dist", "build", ".next", ".expo", ".venv", "output")
    
    Push-Location $ProjectRoot
    try {
        # Note: The output format is now handled by src.cli.main directly, 
        # which will print the absolute paths for the folder and the export.
        python -m src.cli.main snapshot "$AbsRepoPath" --output-root "$OutputDir" --ignore $Ignores --export-flatten
        
        Write-Host "`nSnapshot Success!" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to run snapshot: $_"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "Skipping snapshot run." -ForegroundColor Gray
}