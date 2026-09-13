# ASCII-only: compatible with Windows PowerShell 5.1 and PowerShell 7.
# Download engineering handoffs only. Never executes scripts or applies patches.
param(
    [string]$Repository,
    [string]$Commit,
    [string]$RelativeDirectory,
    [string]$ExpectedManifestSha256,
    [string]$OutputParent
)

function Receive-HandoffFile {
    param([string]$Uri, [string]$Destination, [long]$Limit)
    $Request = [System.Net.HttpWebRequest]::Create($Uri)
    $Request.Method = 'GET'
    $Request.AllowAutoRedirect = $false
    $Request.Proxy = $null
    $Request.UseDefaultCredentials = $false
    $Request.Credentials = $null
    $Request.Timeout = 15000
    $Request.ReadWriteTimeout = 15000
    $Request.AutomaticDecompression = [System.Net.DecompressionMethods]::None
    $Request.UserAgent = 'polymarket-alpha-lab-handoff/1'
    $Response = $null
    $InputStream = $null
    $OutputStream = $null
    try {
        $Response = $Request.GetResponse()
        if ([int]$Response.StatusCode -ne 200 -or $Response.ResponseUri.AbsoluteUri -ne $Uri -or
            $Response.ContentLength -gt $Limit) { throw 'unexpected_response' }
        $InputStream = $Response.GetResponseStream()
        $OutputStream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $Buffer = New-Object byte[] 65536
        [long]$Total = 0
        while (($Count = $InputStream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {
            $Total += $Count
            if ($Total -gt $Limit) { throw 'response_too_large' }
            $OutputStream.Write($Buffer, 0, $Count)
        }
        if ($Response.ContentLength -ge 0 -and $Total -ne $Response.ContentLength) {
            throw 'response_incomplete'
        }
        $OutputStream.Flush()
    } finally {
        if ($null -ne $OutputStream) { $OutputStream.Dispose() }
        if ($null -ne $InputStream) { $InputStream.Dispose() }
        if ($null -ne $Response) { $Response.Dispose() }
    }
}

function Invoke-HandoffDownload {
    param([string]$Repository, [string]$Commit, [string]$RelativeDirectory,
          [string]$ExpectedManifestSha256, [string]$OutputParent)
    $Stage = 'preflight'
    $Staging = $null
    try {
        if ($Repository -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$' -or
            $Commit -cnotmatch '^[0-9a-f]{40}$' -or
            $ExpectedManifestSha256 -cnotmatch '^[0-9a-f]{64}$' -or
            $RelativeDirectory -cnotmatch '^handoffs/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*$' -or
            -not (Test-Path -LiteralPath $OutputParent -PathType Container)) {
            throw 'invalid_parameters'
        }
        $Parent = (Get-Item -LiteralPath $OutputParent -ErrorAction Stop).FullName
        if ((Get-Item -LiteralPath $Parent).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'linked_parent'
        }
        $Nonce = [guid]::NewGuid().ToString('N')
        $Staging = Join-Path $Parent ('.pal-handoff-' + $Nonce + '.downloading')
        $Final = Join-Path $Parent ('pal-handoff-' + $Nonce)
        New-Item -ItemType Directory -Path $Staging -ErrorAction Stop | Out-Null
        $Base = "https://raw.githubusercontent.com/$Repository/$Commit/$RelativeDirectory"
        $Stage = 'manifest_download'
        $ManifestPart = Join-Path $Staging 'manifest.json.part'
        Receive-HandoffFile "$Base/manifest.json" $ManifestPart 65536
        $Stage = 'manifest_verification'
        if ((Get-FileHash -LiteralPath $ManifestPart -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ExpectedManifestSha256) {
            throw 'manifest_hash_mismatch'
        }
        $Utf8 = New-Object System.Text.UTF8Encoding($false, $true)
        $Manifest = $Utf8.GetString([IO.File]::ReadAllBytes($ManifestPart)) | ConvertFrom-Json -ErrorAction Stop
        $Names = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
        $Entries = @($Manifest.files)
        if ($Manifest.format -cne 'github-handoff-v2' -or $Entries.Count -lt 1 -or $Entries.Count -gt 20) {
            throw 'manifest_invalid'
        }
        [long]$Total = 0
        foreach ($Entry in $Entries) {
            if ($Entry.name -isnot [string] -or $Entry.name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$' -or
                $Entry.name -match '^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)' -or $Entry.name.EndsWith('.') -or
                $Entry.name -ieq 'manifest.json' -or ($Entry.name -imatch '\.part$') -or -not $Names.Add($Entry.name) -or
                ($Entry.bytes -isnot [int] -and $Entry.bytes -isnot [long]) -or
                $Entry.bytes -lt 1 -or $Entry.bytes -gt 1048576 -or
                $Entry.sha256 -isnot [string] -or $Entry.sha256 -cnotmatch '^[0-9a-f]{64}$') {
                throw 'manifest_entry_invalid'
            }
            $Total += $Entry.bytes
        }
        if ($Total -gt 5242880) { throw 'handoff_too_large' }
        [IO.File]::Move($ManifestPart, (Join-Path $Staging 'manifest.json'))
        foreach ($Entry in $Entries) {
            $Stage = 'file_download'
            $Part = Join-Path $Staging ($Entry.name + '.part')
            Receive-HandoffFile "$Base/$($Entry.name)" $Part $Entry.bytes
            $Stage = 'file_verification'
            if ((Get-Item -LiteralPath $Part).Length -ne $Entry.bytes -or
                (Get-FileHash -LiteralPath $Part -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Entry.sha256) {
                throw 'file_integrity_failed'
            }
            [IO.File]::Move($Part, (Join-Path $Staging $Entry.name))
        }
        $Stage = 'publication'
        # Directory.Move does not replace an existing directory. Preserve on failure.
        [IO.Directory]::Move($Staging, $Final)
        return [pscustomobject]@{status='verified'; directory=$Final; delivery_commit=$Commit;
            manifest_sha256=$ExpectedManifestSha256; files=$Entries.Count; executed=$false}
    } catch {
        return [pscustomobject]@{status='failed'; reason_code=('handoff_' + $Stage + '_failed');
            staging_directory=$Staging; executed=$false}
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    $ErrorActionPreference = 'Stop'
    $Result = Invoke-HandoffDownload $Repository $Commit $RelativeDirectory $ExpectedManifestSha256 $OutputParent
    $Result | ConvertTo-Json -Depth 5
    if ($Result.status -ne 'verified') { exit 1 }
}
