**Execution readiness is BLOCKED at `4bb734db24faf587c5270e8a79032bc8829d6c78`.** The two pending authorizations can unlock host preparation and the preparation smoke. The official six-scenario run also needs a published mechanism for supplying the image, recorded publisher provenance, and explicit authorization covering the image copy and official-binary execution. The existing preparation-only authorization does not cover those operations.

The conditional runbook below passed a fresh independent read-only review after corrections. I modified no files, ran no tests or probe, changed no policy, accessed no credentials, and opened no sandbox.

I reverified the following:

- HEAD matches the supplied revision; the worktree is clean.
- All **6,293** staged payload files match their manifest hashes and sizes.
- All **2,846** bundled source files match the corresponding Git blobs at HEAD. The older packaged source commit is absent from this clone, so this establishes byte equivalence of those files, not local ancestry.
- The ZIP’s embedded manifest matches the staged manifest.
- The local executable matches the supplied hash and size. I read the existing version receipt; I did not execute the installed image.
- The preparation output directory is empty.
- Windows PowerShell 5.1 currently reports effective policy `Restricted`, with `CurrentUser=Undefined`.

**1. Freeze the inputs and resolve the repository-side prerequisite.**

Use these pins throughout the execution record:

| Item | Revision or size | SHA256 / tree |
|---|---|---|
| Planning baseline | `4bb734db24faf587c5270e8a79032bc8829d6c78` | Tree `0241a5c247d5644261c6cad0f31cebc631d5d5a3` |
| Packaged source, declared by manifest | `21d888a0b4db49d92e3d73293ca7a71ec1087783` | Tree `5202e9a8422d99922eb60725b1384f48299d2257` |
| `claude-probe-environment.zip` | 35,497,151 bytes | `ac1ff95623ce9f20d7a2a6b876554242b277066c952ed9d62bda3b4747fddb57` |
| `input/environment-manifest.json` | 1,248,775 bytes | `913bd7d4fda8cad630bc0ff205998fee64d553d6e0911e550c6d7b9665932582` |
| Existing `preparation-smoke.wsb` | 918 bytes | `6fb0b9fb221e910e2fb3e0f8777f0ecd183182a989840a5b7dd1d6ce20ebf5fe` |
| Supplied `claude.exe` | 240,767,648 bytes | `39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c` |

The `.wsb` mechanism decision is to **preserve the existing preparation payload and generate a separate official-probe configuration through reviewed source code**.

The current [generator](/D:/Projects/polymarket-alpha-lab/scripts/claude_probe_environment.py:157) accepts only `input_dir` and `output_dir`. It always maps those two directories and runs `C:\pal-input\smoke.cmd`. It has no official-image mapping or alternate launcher interface.

Copying the payload and adding `claude.exe` inside the copy does not solve this:

- `verify()` requires an exact inventory and rejects additional files.
- The payload manifest requires `official_cli_included=false`.
- The preparation payload’s per-file limit is 150,000,000 bytes; the image is 240,767,648 bytes.

Use this official-run layout instead:

| Host directory | Guest mapping | Access |
|---|---|---|
| Existing `stage-attempt-1\input` | `C:\pal-input` | Read-only |
| New `official-attempt-1\image` | `C:\pal-claude-image` | Read-only |
| New `official-attempt-1\control` | `C:\pal-control` | Read-only |
| New `official-attempt-1\output` | `C:\pal-output` | Writable |

The `image` directory must contain **only** `claude.exe` and its small strict JSON manifest. The separate `control` mapping holds the published launcher/helper without changing either the payload inventory or the image-only directory.

The official configuration must preserve every existing hardening value:

```text
Networking=Disable
ClipboardRedirection=Disable
vGPU=Disable
AudioInput=Disable
VideoInput=Disable
PrinterRedirection=Disable
ProtectedClient=Enable
MemoryInMB=4096
```

Its `LogonCommand` should open a visible guest PowerShell console, with no automatic official-binary execution:

```text
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -NoExit
```

A minimal implementation can extend the existing environment helper with separate `official-stage`, `official-verify`, and `official-run` operations. Preserve the existing preparation commands and `sandbox_xml(input_dir, output_dir)` contract. The official generator may reuse that function and add the two mappings and alternate command **inside reviewed generator code**. Do not hand-edit the generated XML.

**Those three operations do not exist at HEAD.** Before local official execution, their implementation must be tested, independently reviewed, committed, published to a retained GitHub ref, and read back with verified SHA256 and byte sizes. The delivery must include the helper, manifest, and complete instructions. No new delivery commit, retained ref, download URL, or checksum is available to claim in this read-only planning turn.

Required helper acceptance coverage includes:

- Exact four mappings, access modes, hardening fields and guest command.
- No launch during staging or verification.
- Fresh destinations; no overwrite, cleanup or automatic retry.
- Image-only inventory; bounded, identity-stable copy that rejects links and reparse points.
- Explicit image hash/size/version inputs and destination re-verification.
- Unchanged payload manifest and bytes.
- Path expansion, traversal, quoting and `%` refusal.
- Missing isolation assertion, malformed manifests and unsafe output refusal.
- Exact six-case evidence reconciliation described below.

That implementation PR must update `DELIVERY_PLAN.md` in the same PR with **WP-02**, this readiness gap, actual validation and delivery evidence, remaining blockers, and **official run: 0/6 unexecuted**. The later execution-evidence section is added only after execution.

**2. After the policy grant, apply only the authorized policy change and collect host facts.**

Run the following in a visible **64-bit Windows PowerShell 5.1** session started with `-NoProfile`. These commands are the future execution instructions; they were not run during this review.

```powershell
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$Repo = 'D:\Projects\polymarket-alpha-lab'
$TaskRoot = 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify'
$PrepRoot = Join-Path $TaskRoot 'stage-attempt-1'
$InputRoot = Join-Path $PrepRoot 'input'
$PrepOutput = Join-Path $PrepRoot 'output'
$PrepWsb = Join-Path $PrepRoot 'preparation-smoke.wsb'
$EvidenceRoot = Join-Path $TaskRoot 'host-attempt-1'
$PS51 = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$HostPython = 'D:\Programs\Python\Python312\python.exe'
$ImageSource = 'C:\Users\Administrator\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe'
$ImageSha = '39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c'

if ($PSVersionTable.PSVersion.Major -ne 5 -or
    $PSVersionTable.PSVersion.Minor -ne 1 -or
    -not [Environment]::Is64BitProcess) {
    throw 'BLOCKED: use 64-bit Windows PowerShell 5.1'
}

if (Test-Path -LiteralPath $EvidenceRoot) {
    throw 'BLOCKED: evidence attempt already exists'
}
New-Item -ItemType Directory -Path $EvidenceRoot | Out-Null

Get-ExecutionPolicy -Scope CurrentUser |
    Out-File -LiteralPath (Join-Path $EvidenceRoot 'policy-currentuser-before.txt') `
        -Encoding ascii -NoClobber

Get-ExecutionPolicy -List |
    Select-Object @{Name='Scope';Expression={$_.Scope.ToString()}},
                  @{Name='Policy';Expression={$_.ExecutionPolicy.ToString()}} |
    ConvertTo-Json |
    Out-File -LiteralPath (Join-Path $EvidenceRoot 'policy-before.json') `
        -Encoding ascii -NoClobber

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

if ((Get-ExecutionPolicy -Scope CurrentUser) -ne 'RemoteSigned' -or
    (Get-ExecutionPolicy) -ne 'RemoteSigned') {
    throw 'BLOCKED: authorized policy is not effective'
}
```

Record the actual authorization reference before the mutation. Do not use `Bypass`, `Unblock-File`, change another policy scope, or override Group Policy. `RemoteSigned` can still reject a downloaded unsigned script carrying a zone marker; retain that denial and stop.

Use a child PowerShell process for the host helper so that its process exit code is meaningful:

```powershell
function Save-ProbeHostFacts {
    param([Parameter(Mandatory=$true)][string]$Label)

    $stdoutPath = Join-Path $EvidenceRoot ($Label + '.json')
    $stderrPath = Join-Path $EvidenceRoot ($Label + '.stderr.txt')

    if ((Test-Path -LiteralPath $stdoutPath) -or
        (Test-Path -LiteralPath $stderrPath)) {
        throw 'BLOCKED: host evidence file already exists'
    }

    $hostText = & $PS51 -NoLogo -NoProfile -NonInteractive `
        -File (Join-Path $Repo 'scripts\inspect_claude_probe_host.ps1') `
        2> $stderrPath
    $hostExit = $LASTEXITCODE

    $hostText | Out-File -LiteralPath $stdoutPath `
        -Encoding ascii -NoClobber

    if ($hostExit -ne 0) {
        throw 'BLOCKED: host helper failed; retain stdout and stderr'
    }

    $facts = ($hostText -join "`n") | ConvertFrom-Json
    if ($facts.schema -cne 'claude-probe-host-preparation-v1' -or
        $facts.vendor_executed -ne $false -or
        $facts.feature_changed -ne $false -or
        $facts.global_tools_changed -ne $false -or
        $facts.activation_authorized -ne $false) {
        throw 'BLOCKED: unexpected host helper receipt'
    }

    return $facts
}

$HostFacts = Save-ProbeHostFacts -Label 'host-before-feature'
$HostFacts | ConvertTo-Json -Depth 4
```

Branch on the exact `sandbox_feature` value:

| Value | Action |
|---|---|
| `enabled` | Proceed to preflight if `os_64bit=true`; successful launch remains unproven. |
| `disabled` / `absent` | Stop the launch sequence and report the feature enablement/reboot action. Execute step 3 only if that exact operation is covered by the owner’s grant. |
| `unknown`, unexpected value, malformed receipt | Stop. Do not reinterpret it as disabled or enabled. |

The helper recognizes a limited edition list. On Windows Server it may report `edition=unknown`; do not infer Sandbox support from an installed desktop shell or a server label.

**3. If required and explicitly approved, enable the feature, reboot, and repeat the host query.**

Use an administrator session deliberately opened by the operator. Do not automate elevation with `RunAs`.

```powershell
$featureResult = Enable-WindowsOptionalFeature `
    -Online `
    -FeatureName Containers-DisposableClientVM `
    -All `
    -NoRestart `
    -ErrorAction Stop

$featureResult | ConvertTo-Json -Depth 4 |
    Out-File -LiteralPath (Join-Path $EvidenceRoot 'feature-enable.json') `
        -Encoding ascii -NoClobber
```

Coordinate the reboot with the owner so other work can be saved. Once the reboot is authorized and scheduled:

```powershell
Restart-Computer
```

After reboot, reopen 64-bit PowerShell 5.1, restore the same path variables without recreating the attempt directory, verify effective policy, and run:

```powershell
$HostFacts = Save-ProbeHostFacts -Label 'host-after-reboot'

if ($HostFacts.sandbox_feature -cne 'enabled' -or
    $HostFacts.os_64bit -ne $true) {
    throw 'BLOCKED: prepared host is not ready for Sandbox launch'
}
```

An unsupported/unknown feature, enablement failure, pending reboot or missing launcher remains a blocker. Do not install another virtualization product, alter BIOS settings, change firewall/ACL settings, or use the working host as a substitute. If the pending grant already covers enablement and reboot, do not request that permission again.

**4. Complete preflight before opening the preparation `.wsb`.**

Use exact hashes, not the informal metadata note:

```powershell
function Assert-PinnedFile {
    param(
        [string]$Path,
        [long]$Bytes,
        [string]$Sha256
    )

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or
        (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw 'BLOCKED: expected a plain file'
    }

    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne $Bytes -or $actual -cne $Sha256) {
        throw 'BLOCKED: pinned file mismatch'
    }
}

Assert-PinnedFile `
    -Path (Join-Path $TaskRoot 'downloads\claude-probe-environment.zip') `
    -Bytes 35497151 `
    -Sha256 'ac1ff95623ce9f20d7a2a6b876554242b277066c952ed9d62bda3b4747fddb57'

Assert-PinnedFile `
    -Path (Join-Path $InputRoot 'environment-manifest.json') `
    -Bytes 1248775 `
    -Sha256 '913bd7d4fda8cad630bc0ff205998fee64d553d6e0911e550c6d7b9665932582'

Assert-PinnedFile `
    -Path $PrepWsb `
    -Bytes 918 `
    -Sha256 '6fb0b9fb221e910e2fb3e0f8777f0ecd183182a989840a5b7dd1d6ce20ebf5fe'

Assert-PinnedFile -Path $ImageSource -Bytes 240767648 -Sha256 $ImageSha

& $HostPython -I -S -B (Join-Path $InputRoot 'probe-environment.py') `
    verify --root $InputRoot

if ($LASTEXITCODE -ne 0) {
    throw 'BLOCKED: payload verification failed'
}

if (@(Get-ChildItem -LiteralPath $PrepOutput -Force).Count -ne 0) {
    throw 'BLOCKED: preparation output is not empty'
}
```

Also verify the executable helper bytes against the frozen delivery. For this existing checkout, `scripts\inspect_claude_probe_host.ps1` is 2,990 bytes with SHA256 `705e0e0f4abf2aebebbf824d874ddf7d4278a8c33e2e6d11a5a5cf7056f478bb`. Its committed LF blob is different—2,929 bytes, SHA256 `5e8b827bba6a8b7e93f701b410d9a22ed983a019c135316c2eaaef1492c504b2`—so do not compare a raw GitHub download against the checkout’s CRLF hash.

The coordinator’s final launch checklist is:

- Required owner grant recorded; policy effective; host feature explicitly `enabled`.
- Payload manifest, complete inventory and all file hashes verified.
- Relevant source still matches the reviewed revision; no silent source refresh.
- Image identity reverified, without running the installed image.
- `.wsb` bytes match the expected generated configuration.
- Every hardening setting, mapping, access flag and `LogonCommand` checked.
- All mapped paths and ancestors are plain directories; no reparse-point substitution.
- Output is fresh and empty.
- Only explicitly inventoried `.wsb` files exist in the task directory.
- No unexplained untracked `.wsb` files exist in the repository.
- The official Windows Sandbox launcher exists.

These read-only inventory commands support the last checks:

```powershell
git -C $Repo status --porcelain=v1 --untracked-files=all
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED: git status failed' }

git -C $Repo ls-files --others -- '*.wsb'
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED: WSB inventory failed' }

Get-ChildItem -LiteralPath $TaskRoot -Filter '*.wsb' -Recurse -File |
    Select-Object FullName, Length

$SandboxExe = 'C:\Windows\System32\WindowsSandbox.exe'
if (-not (Test-Path -LiteralPath $SandboxExe -PathType Leaf)) {
    throw 'BLOCKED: official Windows Sandbox launcher unavailable'
}
```

At present, the expected task inventory contains only `stage-attempt-1\preparation-smoke.wsb`. Later it may also contain the generated official variant and separately recorded retained attempts. Unknown variants cause a stop; do not delete them to make the inventory pass.

**5. Open the preparation smoke once and validate its actual receipt.**

After the preparation-smoke authorization and successful preflight:

```powershell
$smokeClient = Start-Process `
    -FilePath $SandboxExe `
    -ArgumentList ('"{0}"' -f $PrepWsb) `
    -PassThru
```

This deliberately opens the visible Sandbox interface. Direct invocation of `WindowsSandbox.exe` avoids relying on an unknown `.wsb` association. Double-clicking the file is equivalent only when the association is known to invoke that official launcher.

The generated logon command runs:

```text
C:\pal-input\python\python.exe -I -S -B C:\pal-input\probe-environment.py selftest --root C:\pal-input --receipt C:\pal-output\environment.json
```

The guest receipt appears directly on the host at:

```text
D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\stage-attempt-1\output\environment.json
```

Wait for guest completion and a complete, parseable receipt. A Sandbox client exit, an open GUI, or mere file existence is not proof of smoke completion. Use a declared **15-minute operator observation window**, checking at short intervals. Do not extend it or relaunch automatically.

After the file is complete, validate its bounded plain-file form and these exact values:

```powershell
$receiptPath = Join-Path $PrepOutput 'environment.json'
$receiptItem = Get-Item -LiteralPath $receiptPath -Force

if ($receiptItem.PSIsContainer -or
    $receiptItem.Length -gt 65536 -or
    (($receiptItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
    throw 'BLOCKED: unsafe preparation receipt'
}

$smoke = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json

if ($smoke.status -cne 'preparation_smoke_passed' -or
    $smoke.source_commit -cne '21d888a0b4db49d92e3d73293ca7a71ec1087783' -or
    $smoke.python -cne '3.12.12' -or
    $smoke.official_cli_included -ne $false -or
    $smoke.official_cli_executed -ne $false -or
    $smoke.official_cases_run -ne 0 -or
    $smoke.loopback_checked -ne $true -or
    $smoke.sandbox_isolation_verified -ne $false -or
    $smoke.activation_authorized -ne $false) {
    throw 'BLOCKED: preparation smoke receipt did not pass'
}
```

Compare the dependency map exactly with the pinned manifest: pytest `9.1.1`, tzdata `2026.3`, colorama `0.4.6`, iniconfig `2.3.0`, packaging `26.2`, pluggy `1.6.0`, pygments `2.20.0`.

There is **no Boolean `preparation_smoke_passed` field**; the success indicator is `status="preparation_smoke_passed"`.

The current `smoke.cmd` does not redirect failure output to a durable log. If the smoke fails or produces no receipt, retain the attempt directory, launch time, timeout/exit observation, and any visible redacted error. Record the missing receipt explicitly. Do not manufacture a log, edit `smoke.cmd`, clear output, or reopen this attempt.

Close the preparation Sandbox through its UI and confirm its session is discarded.

**6. Supply the image through the published official staging mechanism.**

This step needs explicit owner scope for copying the named image and running the six official-binary scenarios in a fresh guest. Preparation-only permission is insufficient.

The local metadata note is not canonical machine input: it contains a leading backslash in its `sha256` value and records npm package version `2.1.281` alongside executable version `2.1.278`. Use the exact verified constants above, and require the harness’s in-guest version check. Neither a file path nor a matching hash establishes publisher provenance; retain the separate provenance reference before proceeding.

The proposed published interface should support this command:

```powershell
# Proposed interface. It does not exist at the current HEAD.
# OfficialHelper must be the downloaded, reviewed and hash-verified delivery file.

& $HostPython -I -S -B $OfficialHelper official-stage `
    --prepared-root $InputRoot `
    --manifest-sha256 '913bd7d4fda8cad630bc0ff205998fee64d553d6e0911e550c6d7b9665932582' `
    --image $ImageSource `
    --image-sha256 $ImageSha `
    --image-bytes 240767648 `
    --image-version '2.1.278' `
    --destination (Join-Path $TaskRoot 'official-attempt-1')

if ($LASTEXITCODE -ne 0) {
    throw 'BLOCKED: official staging failed; retain partial attempt'
}
```

The helper must perform a bounded plain-file copy, compare source identity before and after, verify both source and destination hashes, and create the destination exclusively. It must not execute the source image or copy the surrounding npm installation.

The resulting image manifest should contain the exact guest path, SHA256, byte count and expected executable version. Keep the original host installation path in private evidence; do not publish the username-bearing path.

Before opening the official `.wsb`, repeat the preflight checklist against its actual generated hash, four mappings, unchanged payload, image-only directory, published control files and empty output. The official preflight verifier must reject a configuration that could auto-start the binary.

After opening the new Sandbox, record all of the following before running the probe:

- The verified official `.wsb` hash and reviewed mappings.
- Successful launch of that configuration on the prepared host.
- The matching preparation receipt.
- The image provenance and official-run authorization references.
- An explicit operator assertion that the supported `Networking=Disable` boundary is in effect for this guest and numeric loopback is allowed.

**Do not infer this assertion from the smoke receipt.** If the boundary is unknown, unsupported or contradicted, stop. If empirical egress certification is required, this node remains blocked pending a separately reviewed mechanism; do not improvise external connectivity tests.

**7. Run precisely the six cases inside the official guest.**

The five opt-in values, as defined by [the harness](/D:/Projects/polymarket-alpha-lab/tests/claude_cli_probe.py:34), are:

| Environment variable | Exact value / meaning |
|---|---|
| `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE` | `1` |
| `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE` | `C:\pal-claude-image\claude.exe` |
| `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256` | `39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c` |
| `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES` | `240767648`, decimal string |
| `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST` | `1`, an explicit operator assertion of the required environment |

The last variable does not contain JSON or host-detail fields. Record those details separately. All five absent means skips; partial or invalid configuration means failure. Neither is acceptance.

After the operator assertion, manually invoke the proposed published runner in the guest console:

```powershell
# Proposed interface, available only after the helper delivery is published.
& 'C:\pal-input\python\python.exe' -I -S -B `
    'C:\pal-control\probe-environment.py' official-run `
    --root 'C:\pal-input' `
    --image-manifest 'C:\pal-claude-image\image-manifest.json' `
    --output 'C:\pal-output' `
    --isolated-host-attested
```

The runner must record that explicit assertion and its evidence references. It must refuse to set `ISOLATED_HOST=1` without the flag and required recorded prerequisites.

Its exact underlying pytest invocation must be equivalent to this PowerShell 5.1-compatible guest command:

```powershell
$env:POLYMARKET_ALPHA_LAB_CLAUDE_PROBE = '1'
$env:POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE = 'C:\pal-claude-image\claude.exe'
$env:POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256 = '39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c'
$env:POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES = '240767648'
$env:POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:TMP = 'C:\pal-output\launcher-tmp'
$env:TEMP = 'C:\pal-output\launcher-tmp'

Set-Location -LiteralPath 'C:\pal-output'

$pytestBootstrap = @'
import sys
sys.path[:0] = [
    r"C:\pal-input\source",
    r"C:\pal-input\source\src",
    r"C:\pal-input\python\Lib\site-packages",
]
import pytest
raise SystemExit(pytest.main([
    "-q", "-s", "--tb=short",
    "-o", "junit_family=legacy",
    "-p", "no:cacheprovider",
    "--basetemp=C:\\pal-output\\pytest-tmp",
    "--junitxml=C:\\pal-output\\junit.xml",
    "C:\\pal-input\\source\\tests\\test_research_claude_profile_native.py",
]))
'@

& 'C:\pal-input\python\python.exe' -I -S -B -c $pytestBootstrap
$pytestExit = $LASTEXITCODE
```

This block documents the invocation that the reviewed runner must perform; do not run it a second time after the runner. Explicit path insertion is necessary because `-I -S` does not load the packaged site-packages automatically.

Before starting pytest, the runner must verify import origins and image bytes, create `launcher-tmp`, and refuse existing `pytest-tmp`, logs, JUnit, observations or exit receipts. Pytest can clear an existing `--basetemp`, so existence must be rejected before invocation.

The runner must capture, with bounded sizes and exclusive creation:

```text
C:\pal-output\launch.json
C:\pal-output\pytest.log
C:\pal-output\junit.xml
C:\pal-output\observations.json
C:\pal-output\exit.json
C:\pal-output\pytest-tmp\
C:\pal-output\launcher-tmp\
```

Do not add `-x`, rerun plugins, xdist, broader test selection, real credentials or an external endpoint. The harness itself sets its synthetic noncredential and the sole `ANTHROPIC_BASE_URL` override to `http://127.0.0.1:<allocated-port>` inside the test. Keep the production HTTPS profile unchanged.

Each case allows a version operation and one prompt operation, each with a 20-second process deadline and a 5-second cleanup budget. Across six cases, that is approximately 240 seconds of process deadlines plus up to 60 seconds of cleanup, server teardown and repeated image hashing. Use a declared **15-minute overall operator abort window**. This is an operating limit, not a guaranteed hard deadline: [process supervision](/D:/Projects/polymarket-alpha-lab/src/polymarket_alpha_lab/research_process.py:303) explicitly excludes uninterruptible OS operations from a universal wall-clock guarantee.

**8. Apply exact pass/fail and first-failure rules.**

Acceptance requires all six modes, once each:

```text
success
rate_limit
server_error
invalid_action
tool_use
truncated
```

Require pytest exit code `0`, exactly six expected test cases, and zero failures, errors or skips. Require **both** evidence channels:

- Six JUnit `claude_cli_probe` properties.
- Six exact `CLAUDE_CLI_PROBE ` console records.

Parse and canonicalize both, match them one-for-one by mode, and reject missing, duplicate, malformed or divergent records. Do not choose whichever channel appears successful.

For every observation, the existing `observation_passed()` predicate must return true. It is a function, not an existing JSON field; label any stored result as a derived value.

| Check | Required result |
|---|---|
| Executable version | Exact expected version matches |
| Requests and responses | `request_count=1`, `responses_sent=1` |
| Unexpected traffic / mock faults | Both `0` |
| Request contract | `request_contract_matches=true` |
| State snapshot | Complete; changed/unsafe/sentinel counts all `0`; no limit reached |
| Success scenario | Decoder accepts; exact synthetic response; total tokens `26` |
| Five negative scenarios | Correct mock exchange occurred, then process fails or decoder rejects |

Every original observation must retain:

```text
activation_authorized=false
vendor_provenance_verified=false
external_egress_verified=false
outside_root_verified=false
transient_writes_verified=false
```

The probe does not certify those properties, even when the operator separately supplies provenance and isolation evidence.

Retain ordinary scenario failures and let the remaining cases in this one fixed batch finish. Abort immediately for an isolation, integrity or unsafe-output incident. Preserve:

- First attempt and first failure.
- Every case actually executed.
- Missing observations, skipped cases and unexecuted cases separately.
- Unexpected internal retries as failures.
- Partial logs/JUnit and missing completion receipts.
- Any later separately reviewed rerun as another attempt, without replacing the first.

A failed or incomplete batch remains **BLOCKED**. Do not change the version, extend deadlines, remove state files, relax assertions, whitelist writes, or retry to green.

**9. Read evidence safely, discard the guest, and record the result.**

Before interpreting official guest output on the host, the published verifier must treat the writable mapping as untrusted. It must perform a bounded walk without following links and refuse reparse points, symlinks, hardlinks, nonregular files, escaped paths, unexpected top-level names and count/size violations. JSON parsing must reject duplicate keys. XML parsing must reject malformed/oversized documents and DTD/entity declarations.

Only the named evidence files should be interpreted. The pytest working directories remain private retained evidence; do not execute or upload their contents. Unsafe output causes a stop while preserving the original attempt.

The verifier must also recheck the payload and copied image after execution. Do not automatically open logs or JUnit in associated applications.

After preserving the mapped evidence, close the **specific owned Sandbox session** through its UI and confirm discard. Do not terminate every process sharing a Sandbox process name. A discarded VM does not delete the host’s mapped evidence.

No automatic policy rollback or feature disablement is part of this node. If rollback of `CurrentUser` was included in the authorization, restore its recorded prior value; it is currently `Undefined`:

```powershell
# Only when rollback is covered by the owner authorization.
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Undefined -Force
```

Feature disablement and any associated reboot need their own approved maintenance action.

After execution, append a sanitized section to `DELIVERY_PLAN.md`, using the next available section number at that revision. Use this evidence format:

```text
WP-02 official Claude supplied-image probe
Evidence class: isolated official-binary synthetic-loopback observation

Planning baseline:
Packaged source commit/tree:
Helper implementation commit/tree:
Retained delivery ref and full commit:
Delivery manifest SHA256/bytes:
Generated WSB SHA256/bytes:
Payload manifest SHA256/bytes:

Owner policy authorization reference:
Owner feature/reboot/smoke authorization reference:
Owner image-copy/official-run authorization reference:
Publisher-provenance reference:
Operator isolation assertion and basis:
Empirical egress test performed: false

Preparation attempt:
Preparation receipt SHA256:
Preparation status:
Official cases during preparation: 0

Guest image path: C:\pal-claude-image\claude.exe
Image SHA256:
Image bytes: 240767648
Expected executable version: 2.1.278

Exact guest launcher command:
Exact underlying pytest command:
Attempt start/end UTC:
Pytest exit code:
Cases executed/passed/failed/errored/skipped/unexecuted:
Per-mode observation and derived observation_passed result:
JUnit/log observations match one-for-one:
First failure:
Unexpected internal retries:
Subsequent reruns:
Private evidence filenames, sizes and SHA256:
Post-run payload/image verification:
Guest discard observed:

activation_authorized: false
WP-02: PARTIAL
G2: OPEN
V1 completed gates: 1/6
Remaining acceptance gaps:
```

Keep raw results outside the repository initially. Publish only reviewed metadata and the guest image path, hash and size; omit the personal installation path, host/user names, environment dumps, credentials and arbitrary raw state.

Throughout this node, map no user profile, `.claude`, `.local`, `.git`, database/runtime directory, backup or broad parent directory. The installed executable is only the source of an explicitly approved byte copy. All deliberate guest test writes go to `C:\pal-output`; host-visible writes stay within the approved artifact directories and the explicitly authorized OS changes. Windows Sandbox and this harness do not establish that every transient guest OS or binary write stayed inside the test root.

A passing batch supplies limited binary write/context/tool/retry behavior evidence. It does not authorize activation, validate production TLS or a real provider, close G2, or change the existing Codex SQLite blocker.

**VERDICT: PASS — conditional plan only. Execution remains BLOCKED until the missing helper delivery, provenance evidence and stated authorizations are in place.**