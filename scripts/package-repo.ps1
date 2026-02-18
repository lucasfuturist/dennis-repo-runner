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

$CopyOut = Join-Path $OutDir $CopyFolderName
$ZipOut  = Join-Path $OutDir $ZipFileName
$RoboLog = Join-Path $OutDir "robocopy.log"

Write-Host "repo-root: $RepoRoot"
Write-Host "out-dir:   $OutDir"
Write-Host "copy-out:  $CopyOut"
Write-Host "zip-out:   $ZipOut"
Write-Host "log:       $RoboLog"
Write-Host ""

# -------------------------
# 1) CLEAN COPY (robocopy)
# -------------------------
Write-Host "==> creating clean copy..."

# Make sure destination exists (robocopy can create it, but this keeps things predictable)
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

# If not verbose, suppress noisy per-file lines but still show summary + progress
if (-not $VerboseCopy) {
  # /NP removes progress percentage; we actually *want* some progress signal, so keep it.
  # Instead, just reduce file/directory listing noise:
  $robocopyArgs += @("/NFL", "/NDL")
}

$hb = Start-Heartbeat "  ...still working (robocopy). check $RoboLog for details."

try {
  # robocopy returns non-zero even on success; only >=8 is failure.
  & robocopy @robocopyArgs | Out-Host
  $rc = $LASTEXITCODE
  if ($rc -ge 8) {
    throw "robocopy failed with exit code $rc (see $RoboLog)"
  }
}
finally {
  Stop-Heartbeat $hb
}

Write-Host "clean copy done."
Write-Host ""

# -------------------------
# 2) CLEAN ZIP (Compress-Archive)
# -------------------------
Write-Host "==> creating clean zip..."

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

Write-Host "clean zip done."
Write-Host ""
Write-Host "DONE."
Write-Host "copy: $CopyOut"
Write-Host "zip:  $ZipOut"
Write-Host "log:  $RoboLog"