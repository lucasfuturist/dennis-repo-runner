[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$OutDir = "",

  [Parameter(Mandatory = $false)]
  [string]$CopyFolderName = "repo-copy",

  [Parameter(Mandatory = $false)]
  [string]$ZipFileName = "repo-runner.zip",

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeDirs = @("__pycache__", ".git", "dist"),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeFiles = @(),

  # If set, show robocopy output in console (progress / file listing).
  [Parameter(Mandatory = $false)]
  [switch]$VerboseCopy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $scriptsDir = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $scriptsDir "..")).Path
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function Start-Heartbeat([string]$Message) {
  $job = Start-Job -ScriptBlock {
    param($Msg)
    while ($true) {
      Start-Sleep -Seconds 3
      Write-Host $Msg
    }
  } -ArgumentList $Message
  return $job
}

function Stop-Heartbeat($job) {
  if ($null -ne $job) {
    Stop-Job $job -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $job -Force -ErrorAction SilentlyContinue | Out-Null
  }
}

$RepoRoot = Resolve-RepoRoot

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $RepoRoot "dist"
} else {
  if (-not [System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir = Join-Path $RepoRoot $OutDir
  }
}

Ensure-Dir $OutDir

# Ensure absolute paths
$OutDirAbs = (Resolve-Path $OutDir).Path
$CopyOut = Join-Path $OutDirAbs $CopyFolderName
$ZipOut  = Join-Path $OutDirAbs $ZipFileName
$RoboLog = Join-Path $OutDirAbs "robocopy.log"

Write-Host "repo-root: $RepoRoot"
Write-Host "out-dir:   $OutDirAbs"
Write-Host ""

# -------------------------
# 1) CLEAN COPY (robocopy)
# -------------------------
Write-Host "==> creating clean copy..." -ForegroundColor Yellow

Ensure-Dir $CopyOut

$robocopyArgs = @(
  "`"$RepoRoot`"",
  "`"$CopyOut`"",
  "/E",
  "/R:0",
  "/W:0",
  "/MT:1",          # deterministic + reduces weird multi-thread behavior
  "/LOG:`"$RoboLog`"",
  "/TEE",           # also write to console, unless we suppress below
  "/XD"
) + $ExcludeDirs

if ($ExcludeFiles.Count -gt 0) {
  $robocopyArgs += @("/XF") + $ExcludeFiles
}

if (-not $VerboseCopy) {
  $robocopyArgs += @("/NFL", "/NDL")
}

$hb = Start-Heartbeat "  ...still working (robocopy). check log for details."

try {
  & robocopy @robocopyArgs | Out-Host
  $rc = $LASTEXITCODE
  if ($rc -ge 8) {
    throw "robocopy failed with exit code $rc (see $RoboLog)"
  }
}
finally {
  Stop-Heartbeat $hb
}

Write-Host "clean copy done." -ForegroundColor Green
Write-Host ""

# -------------------------
# 2) CLEAN ZIP (Compress-Archive)
# -------------------------
Write-Host "==> creating clean zip..." -ForegroundColor Yellow

if (Test-Path $ZipOut) {
  Remove-Item $ZipOut -Force
}

$excludeRegex = ($ExcludeDirs | ForEach-Object { [Regex]::Escape($_) }) -join "|"

$files = Get-ChildItem -Path $RepoRoot -Recurse -File -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch "\\($excludeRegex)\\" }

if ($ExcludeFiles.Count -gt 0) {
  $files = $files | Where-Object {
    $name = $_.Name
    $ok = $true
    foreach ($pat in $ExcludeFiles) {
      if ($name -like $pat) { $ok = $false; break }
    }
    $ok
  }
}

if ($files.Count -eq 0) {
  throw "no files selected for zip; check exclusions"
}

Compress-Archive -Path ($files | Select-Object -ExpandProperty FullName) -DestinationPath $ZipOut -CompressionLevel Optimal

Write-Host "clean zip done." -ForegroundColor Green
Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host "copy: " -NoNewline; Write-Host $CopyOut -ForegroundColor Cyan
Write-Host "zip:  " -NoNewline; Write-Host $ZipOut -ForegroundColor Cyan
Write-Host "log:  " -NoNewline; Write-Host $RoboLog -ForegroundColor Cyan