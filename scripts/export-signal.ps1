[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$OutDir = "",

  [Parameter(Mandatory = $false)]
  [string[]]$IncludeGlobs = @(
    "README.md",
    ".gitignore",
    "documents\**\*.md",
    "src\**\*.py",
    "scripts\**\*.ps1",
    "tests\**\*",
    ".context-docs\**\*.md",
    ".context-docs\**\*.txt",
    ".context-docs\**\*.json"
  ),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeDirs = @(
    "__pycache__", ".git", "dist", "node_modules", ".next", ".expo", ".venv"
  ),

  [Parameter(Mandatory = $false)]
  [string[]]$ExcludeExts = @(
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".ttf", ".otf", ".woff", ".woff2",
    ".mp4", ".mov", ".zip"
  )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $scriptsDir = Split-Path -Parent $PSCommandPath
  (Resolve-Path (Join-Path $scriptsDir "..")).Path
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
  }
}

function RelPath([string]$RepoRoot, [string]$AbsPath) {
  [System.IO.Path]::GetRelativePath($RepoRoot, $AbsPath)
}

function ToForwardSlashes([string]$Path) {
  $Path.Replace('\', '/')
}

$RepoRoot = Resolve-RepoRoot

if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $RepoRoot "dist\signal"
} else {
  if (-not [System.IO.Path]::IsPathRooted($OutDir)) {
    $OutDir = Join-Path $RepoRoot $OutDir
  }
}

Ensure-Dir $OutDir

$FlattenOut = Join-Path $OutDir "flatten-signal.md"
$ZipOut     = Join-Path $OutDir "signal.zip"

Write-Host ("repo-root:  {0}" -f $RepoRoot)
Write-Host ("out-dir:    {0}" -f $OutDir)
Write-Host ("flatten:    {0}" -f $FlattenOut)
Write-Host ("zip:        {0}" -f $ZipOut)
Write-Host ""

$excludeDirRegex = ($ExcludeDirs | ForEach-Object { [Regex]::Escape($_) }) -join "|"

$excludeExtSet = New-Object "System.Collections.Generic.HashSet[string]"
foreach ($e in $ExcludeExts) { [void]$excludeExtSet.Add($e.ToLower()) }

# 1) expand include globs
$found = New-Object "System.Collections.Generic.List[string]"

foreach ($glob in $IncludeGlobs) {
  $pattern = Join-Path $RepoRoot $glob

  $items = Get-ChildItem -Path $pattern -Recurse -File -Force -ErrorAction SilentlyContinue

  foreach ($it in $items) {
    if ($it.FullName -match "\\($excludeDirRegex)\\") { continue }

    $ext = [System.IO.Path]::GetExtension($it.Name).ToLower()
    if ($excludeExtSet.Contains($ext)) { continue }

    $found.Add($it.FullName) | Out-Null
  }
}

# 2) de-dupe + deterministic sort by repo-relative lowercased key
$map = @{}
foreach ($abs in $found) {
  $rel = RelPath $RepoRoot $abs
  $key = $rel.ToLower()
  $map[$key] = $abs
}

$keys = $map.Keys | Sort-Object

if ($keys.Count -eq 0) {
  throw "No files matched include globs. Adjust IncludeGlobs."
}

# 3) write flatten markdown (list + contents)
$sb = New-Object System.Text.StringBuilder

[void]$sb.AppendLine("# signal flatten export")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("* repo_root: $RepoRoot")
[void]$sb.AppendLine("* file_count: $($keys.Count)")
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Files")
[void]$sb.AppendLine("")

# FIX: Use single quotes for markdown code blocks to avoid escape sequence errors
[void]$sb.AppendLine('```') 

foreach ($k in $keys) {
  $rel = RelPath $RepoRoot $map[$k]
  [void]$sb.AppendLine( (ToForwardSlashes $rel) )
}

# FIX: Use single quotes
[void]$sb.AppendLine('```')
[void]$sb.AppendLine("")

[void]$sb.AppendLine("## Contents")
[void]$sb.AppendLine("")

foreach ($k in $keys) {
  $abs = $map[$k]
  $rel = ToForwardSlashes (RelPath $RepoRoot $abs)

  [void]$sb.AppendLine("### $rel")
  [void]$sb.AppendLine("")

  try {
    $content = Get-Content -LiteralPath $abs -Raw -Encoding UTF8 -ErrorAction Stop
  } catch {
    $content = "[[ERROR: $($_.Exception.Message)]]"
  }

  # FIX: Use single quotes
  [void]$sb.AppendLine('```')

  # FIX: TrimEnd requires char[], or use default TrimEnd() to remove all trailing whitespace
  # Using [char[]] ensures explicit handling of CR/LF without parser ambiguity
  [void]$sb.AppendLine([string]$content.TrimEnd([char[]]@("`r", "`n")))

  # FIX: Use single quotes
  [void]$sb.AppendLine('```')
  [void]$sb.AppendLine("")
}

Set-Content -LiteralPath $FlattenOut -Value $sb.ToString() -Encoding UTF8
Write-Host ("wrote flatten: {0}" -f $FlattenOut)

# 4) zip the same exact set
if (Test-Path $ZipOut) {
  Remove-Item $ZipOut -Force
}

$absPaths = foreach ($k in $keys) { $map[$k] }
Compress-Archive -Path $absPaths -DestinationPath $ZipOut -CompressionLevel Optimal
Write-Host ("wrote zip:     {0}" -f $ZipOut)

Write-Host "DONE."