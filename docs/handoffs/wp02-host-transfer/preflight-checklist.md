# WP-02 Host Transfer -- Target-Host Preflight Checklist

- Status: prepared 2026-09-26 on source host A by the WP-02 host-transfer
  completion worker. Read-only preparation: no sandbox launch, no claude.exe
  execution, no network, no credentials touched.
- Audience: the owner, running this on the TARGET host BEFORE staging any
  transfer files. Every check here is a precondition for staging.
- Companion files in D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-host-transfer\
  on host A:
  - manifest-sha256-full.txt -- full SHA256 integrity manifest
    (self SHA256 recorded on host A 2026-09-26:
    18a6d82495fa3da00213f5a3e45b9efab17d4bf2f7359002dbae0e0374321d9c)
  - generate-manifest.ps1 -- the generator script (reference only; do not
    rerun on the target host)
  - transfer-instructions-DRAFT.md -- DRAFT owner instructions (staging,
    verification, evidence return)
- Execution runbook (referenced, not duplicated):
  D:/Projects/.agent-artifacts/polymarket-alpha-lab/wp02-claude-verify/codex-plan-probe-exec.md

## P1. Windows edition and Windows Sandbox feature

Windows Sandbox requires Windows 10/11 Pro/Enterprise/Education (AMD64) on a
stable/current servicing channel; it is not available on Home editions.
Virtualization must be enabled in firmware and the hypervisor must be running.

Run in an elevated Windows PowerShell 5.1 window:

    Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM

Expected: State must be `Enabled`.

    Test-Path 'C:\Windows\System32\WindowsSandbox.exe'

Expected: True.

    (Get-CimInstance Win32_ComputerSystem).HypervisorPresent

Expected: True. If False, enable virtualization in BIOS/UEFI and reboot before
continuing.

Note: `.wsb` files open with WindowsSandbox.exe (shell association). Checking
the association or the executable's presence is enough during preflight; do
not launch the sandbox yet.

STOP if: the feature is not Enabled, WindowsSandbox.exe is missing, or
HypervisorPresent is False.

## P2. PowerShell version and execution policy (owner decision S57)

Supported configuration (S57): execution policy `RemoteSigned` at
`CurrentUser` scope, on Windows PowerShell 5.1.

    $PSVersionTable.PSVersion        # expect major 5, minor 1
    Get-ExecutionPolicy -List        # expect CurrentUser : RemoteSigned

If CurrentUser is not RemoteSigned, the owner sets it on the target host
(host configuration change performed by the owner only):

    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

STOP if: the effective policy cannot be brought to the S57 configuration, or
PowerShell 5.1 is unavailable.

## P3. Exact host paths required by official-probe.wsb

The .wsb ships inside the transfer as
`official-attempt-1\official-probe.wsb`
(SHA256 eab52c0bfb34ee45233cf9ca09a557240f637293da1c9009f342879fecdf0a0a).
Its `<MappedFolder><HostFolder>` values are absolute host paths and the .wsb
itself is hash-pinned in the manifest: editing it on the target host would
break its manifest hash. The target host must therefore recreate these EXACT
absolute paths, verbatim from the .wsb:

| # | HostFolder (verbatim from official-probe.wsb) | SandboxFolder | ReadOnly |
|---|------------------------------------------------|---------------|----------|
| 1 | D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\stage-attempt-1\input | C:\pal-input | true |
| 2 | D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\official-attempt-1\image | C:\pal-claude-image | true |
| 3 | D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\official-attempt-1\control | C:\pal-control | true |
| 4 | D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\official-attempt-1\output | C:\pal-output | false (writable) |

Additional layout requirements carried by the manifest and the runbook:

- `official-attempt-1\image\` must contain ONLY `claude.exe` and
  `image-manifest.json` (2 files, no more).
- `official-attempt-1\output\` must exist and be EMPTY (0 files) before the
  run; the source manifest asserts it was empty at generation time.
- `official-attempt-1\control\` holds the launcher
  (`official-probe.cmd`, 1 file).
- `stage-attempt-1\input\` ships 6,294 files (embedded Python runtime, probe
  environment, source snapshot) and maps read-only as C:\pal-input.
- Sandbox hardening baked into the .wsb (do not weaken): Networking=Disable,
  ClipboardRedirection=Disable, vGPU=Disable, AudioInput=Disable,
  VideoInput=Disable, PrinterRedirection=Disable, ProtectedClient=Enable,
  MemoryInMB=4096.
- LogonCommand: `C:\Windows\System32\cmd.exe /d /c
  C:\pal-control\official-probe.cmd --isolated-host-attested`

Host sizing implication: MemoryInMB=4096 means the host must have at least
4096 MB RAM free for the sandbox in addition to normal OS headroom.

STOP if: the target host cannot provide the exact drive and path
`D:\Projects\...` (for example, no D: drive). Do not edit the .wsb to point
elsewhere; that breaks its pinned hash.

## P4. Required free disk space

Derived from manifest-sha256-full.txt (generated 2026-09-26T08:08:50Z):

- Section A, `official-attempt-1\`: 4 files, 240,770,918 bytes
  (claude.exe alone is 240,767,648 bytes).
- Section B, `stage-attempt-1\input\`: 6,294 files, 149,477,161 bytes.
- TOTAL payload: 6,298 files, 390,248,079 bytes (372.0 MiB).

Free-space floor on the staging drive (D:):

- staged payload: 390,248,079 bytes
- plus the retained transfer package if kept on the same drive (same order)
- plus the Windows Sandbox documented minimum of 1 GB free disk space

Recommended minimum before starting: 4 GB free on D:.

Mapped-folder startup brings the mapped content into the sandbox at launch;
with roughly 372 MiB mapped, allow several minutes for sandbox startup. Slow
startup alone is NOT a stop condition.

## P5. Path-collision check and permission expectations

Collision check BEFORE creating anything:

    Test-Path 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify'

If the base path (or any of the four P3 paths) already exists and contains
anything, STOP and report. Never merge, overwrite, or delete pre-existing
content.

Permission expectations at the NTFS level, where practical:

- `stage-attempt-1\input`, `official-attempt-1\image`,
  `official-attempt-1\control`: staged READ-ONLY. Practical measure after
  hash verification (defense in depth; the .wsb ReadOnly=true mapping is the
  primary control inside the guest):

        Get-ChildItem -LiteralPath '<dir>' -Recurse -File |
            ForEach-Object { $_.IsReadOnly = $true }

- `official-attempt-1\output`: writable, and EMPTY at run start.

## P6. claude.exe identity (owner decision S49 pinned value)

- Pinned SHA256: 39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c
- Pinned size: 240,767,648 bytes
- The full-tree hash comparison in transfer-instructions-DRAFT.md (step 2)
  verifies this automatically; the manifest summary also records
  `claude-exe-matches-pinned-values: True` at generation time.
- Version check (TARGET-HOST STEP ONLY; not performed during preparation on
  host A). After staging and hash verification, run from inside the image
  directory:

        Set-Location 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\official-attempt-1\image'
        .\claude.exe --version

  Expected output: `2.1.278 (Claude Code)`.

STOP if the reported version is anything other than 2.1.278.

## P7. Stop conditions (summary)

Any one of these stops the host transfer before or during staging:

1. Windows Sandbox feature not Enabled, or WindowsSandbox.exe missing.
2. Effective execution policy cannot be brought to S57 (CurrentUser
   RemoteSigned on Windows PowerShell 5.1).
3. The exact absolute host paths from P3 cannot be recreated (no D: drive).
4. Path collision: any target path already exists and is non-empty.
5. Free disk space below the P4 floor.
6. Any SHA256 mismatch against manifest-sha256-full.txt, before or after
   staging (including the manifest itself: compare its self hash recorded in
   this package).
7. `claude.exe --version` on the target host reports anything other than
   2.1.278.

## Appendix: manifest facts used above

- File: manifest-sha256-full.txt, 6,324 lines total, of which 6,298 data
  lines and 26 comment/blank lines; 933,769 bytes; ASCII; CRLF.
- Base for all relative paths (source host A):
  D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\
- Data-line format: lowercase 64-hex SHA256, two spaces, relative path with
  backslashes. All 6,298 data lines conform; 0 duplicate paths.
- Coverage verified: 4 lines under `official-attempt-1\`, 6,294 lines under
  `stage-attempt-1\input\`, 0 lines outside those two prefixes.
- Summary block: section-A 4 files / 240,770,918 bytes; section-B 6,294
  files / 149,477,161 bytes; total 6,298 files / 390,248,079 bytes;
  claude-exe-sha256 39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c;
  claude-exe-bytes 240,767,648; generated-utc 2026-09-26T08:08:50Z.
- Source repo revision recorded in the manifest header:
  main 4ed7cc189631688eb2c3cd144dbbc8bf0dc06e4c.
