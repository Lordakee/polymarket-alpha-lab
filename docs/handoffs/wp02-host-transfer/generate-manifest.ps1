# WP-02 host-transfer manifest generator (read-only against source trees).
# Writes manifest-sha256-full.txt next to this script. ASCII output only.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$Root = 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify'
$OutDir = 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-host-transfer'
$OutFile = Join-Path $OutDir 'manifest-sha256-full.txt'

$PinnedClaudeSha = '39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c'
$PinnedClaudeBytes = 240767648

function Get-TreeHashes {
    param([string]$SubPath)
    $abs = Join-Path $Root $SubPath
    if (-not (Test-Path -LiteralPath $abs -PathType Container)) {
        throw "missing container: $SubPath"
    }
    $rows = @()
    $files = @(Get-ChildItem -LiteralPath $abs -Recurse -Force -File)
    foreach ($f in $files) {
        if (($f.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "reparse point refused: $($f.FullName)"
        }
        $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $rel = $f.FullName.Substring($Root.Length + 1)
        $rows += [pscustomobject]@{ Rel = $rel; Sha = $h; Bytes = [int64]$f.Length }
    }
    return ,$rows
}

$sectionA = Get-TreeHashes -SubPath 'official-attempt-1'
$sectionB = Get-TreeHashes -SubPath 'stage-attempt-1\input'

# Empty-directory assertions (directories that must exist but hold no files).
$outDirA = Join-Path $Root 'official-attempt-1\output'
if (-not (Test-Path -LiteralPath $outDirA -PathType Container)) { throw 'official-attempt-1\output missing' }
$cntA = @(Get-ChildItem -LiteralPath $outDirA -Force).Count
if ($cntA -ne 0) { throw "official-attempt-1\output not empty: $cntA entries" }

$bytesA = ($sectionA | Measure-Object -Property Bytes -Sum).Sum
$bytesB = ($sectionB | Measure-Object -Property Bytes -Sum).Sum
$totalFiles = $sectionA.Count + $sectionB.Count
$totalBytes = [int64]$bytesA + [int64]$bytesB
$stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$claudeRow = $sectionA | Where-Object { $_.Rel -ceq 'official-attempt-1\image\claude.exe' }
if ($null -eq $claudeRow) { throw 'claude.exe row missing' }
$claudeOk = ($claudeRow.Sha -ceq $PinnedClaudeSha) -and ($claudeRow.Bytes -eq $PinnedClaudeBytes)

$lines = @()
$lines += '# WP-02 host-transfer integrity manifest (full SHA256 values)'
$lines += '# Source repo revision at generation: main 4ed7cc189631688eb2c3cd144dbbc8bf0dc06e4c'
$lines += '# Base directory for all relative paths (source host A):'
$lines += '#   D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\'
$lines += '# Line format: <sha256-hex-lowercase>  <relative\path\with\backslashes>'
$lines += '# Lines starting with ''#'' are comments or summary; every other line is a data line.'
$lines += '# Hash method: PowerShell Get-FileHash -Algorithm SHA256 (streaming read).'
$lines += '# Order is for readability only; verification is per-file, not order-sensitive.'
$lines += ''
$lines += '# --- Section A: official-attempt-1\ (official-probe.wsb, image, control; output is empty) ---'
foreach ($r in ($sectionA | Sort-Object -Property Rel)) { $lines += ($r.Sha + '  ' + $r.Rel) }
$lines += ''
$lines += '# --- Section B: stage-attempt-1\input\ (payload input mapped by the .wsb as C:\pal-input) ---'
foreach ($r in ($sectionB | Sort-Object -Property Rel)) { $lines += ($r.Sha + '  ' + $r.Rel) }
$lines += ''
$lines += '# SUMMARY'
$lines += ('# section-A-files (official-attempt-1): ' + $sectionA.Count)
$lines += ('# section-A-bytes (official-attempt-1): ' + [int64]$bytesA)
$lines += ('# section-B-files (stage-attempt-1\input): ' + $sectionB.Count)
$lines += ('# section-B-bytes (stage-attempt-1\input): ' + [int64]$bytesB)
$lines += ('# total-files: ' + $totalFiles)
$lines += ('# total-bytes: ' + $totalBytes)
$lines += ('# claude-exe-sha256: ' + $claudeRow.Sha)
$lines += ('# claude-exe-bytes: ' + $claudeRow.Bytes)
$lines += ('# claude-exe-matches-pinned-values: ' + $claudeOk)
$lines += '# note: official-attempt-1\output\ exists on the source host as an empty directory'
$lines += '#       (0 files); it produces no data line and must be recreated empty on the target host.'
$lines += ('# generated-utc: ' + $stamp)

$lines | Out-File -LiteralPath $OutFile -Encoding ascii -NoClobber

Write-Output ('WROTE: ' + $OutFile)
Write-Output ('total-files: ' + $totalFiles)
Write-Output ('total-bytes: ' + $totalBytes)
Write-Output ('claude-exe-sha256: ' + $claudeRow.Sha)
Write-Output ('claude-exe-bytes: ' + $claudeRow.Bytes)
Write-Output ('claude-exe-matches-pinned-values: ' + $claudeOk)
if (-not $claudeOk) { Write-Output 'WARNING: claude.exe does NOT match pinned identity' }
