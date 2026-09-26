# DRAFT -- WP-02 Host-Transfer Instructions (NOT YET APPROVED)

STATUS: DRAFT. Prepared 2026-09-26 on source host A by the WP-02 host-transfer
completion worker. Requires coordinator review before any publication or use.
This draft authorizes nothing by itself; the owner decides every step.
Run preflight-checklist.md on the target host FIRST; its stop conditions all
apply to this document.

## 1. What transfers

Payload -- exactly the two trees covered by manifest-sha256-full.txt, relative
to base D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify\
on host A:

- `official-attempt-1\` -- 4 files, 240,770,918 bytes:
  - `official-probe.wsb` (Windows Sandbox configuration; contains the four
    absolute host-path mappings listed in preflight-checklist.md P3)
  - `image\claude.exe` (official CLI image, 240,767,648 bytes, pinned by
    owner decision S49:
    SHA256 39be063c2512b43347fe7b0ab18c46f1596141701c9c5fc895ddfca9a051067c)
  - `image\image-manifest.json`
  - `control\official-probe.cmd` (launcher)
  - plus the EMPTY directory `output\` (0 files; the manifest records it as
    an empty-directory assertion, not data lines; recreate it empty on the
    target host).
- `stage-attempt-1\input\` -- 6,294 files, 149,477,161 bytes: the probe
  payload the .wsb maps read-only as C:\pal-input (embedded Python runtime,
  probe environment files including environment-manifest.json and
  probe-environment.py, and the packaged source snapshot under `source\`).

TOTAL payload: 6,298 files, 390,248,079 bytes (372.0 MiB).

Transfer package documents (travel with the payload; NOT covered by the
payload manifest):

- `manifest-sha256-full.txt` -- the integrity manifest
  (self SHA256 recorded on host A 2026-09-26:
  18a6d82495fa3da00213f5a3e45b9efab17d4bf2f7359002dbae0e0374321d9c)
- `preflight-checklist.md` -- target-host preflight (this package)
- `transfer-instructions-DRAFT.md` -- this file
- `codex-plan-probe-exec.md` -- the execution runbook, referenced not
  duplicated. On host A it lives at
  D:/Projects/.agent-artifacts/polymarket-alpha-lab/wp02-claude-verify/codex-plan-probe-exec.md
  (SHA256 recorded on host A 2026-09-26:
  a0dd13c1510eeea0f31ee6a290dfba4deaf5e834ff02fe09fe29740074a95e67).
  Record its hash at transfer time and confirm it on arrival.

CHANNEL RULE: OWNER-CONTROLLED CHANNEL ONLY. Never GitHub. The payload
includes a 240 MB official binary and a packaged source snapshot; neither is
published to any repository. GitHub publication, if any, happens only after
coordinator review and only for reviewed documents, never for the payload or
run evidence.

## 1a. Coordinator review note (2026-09-26): file-count reconciliation

The execution runbook states "All 6,293 staged payload files match their
manifest hashes and sizes" while this package's manifest records 6,294 files
under stage-attempt-1\input\. Both are correct and reconcile exactly:
environment-manifest.json (the staging payload manifest) contains 6,293 file
entries and does not list itself, so the runbook's 6,293 counts payload files
verified against that staging manifest; this transfer manifest additionally
includes environment-manifest.json itself, giving 6,294. Disk on host A holds
exactly 6,294 files under stage-attempt-1\input\ (all staged 2026-09-24
10:33, none added since). No drift; no anomaly.

## 2. Integrity verification on the target host

After staging (section 4), recompute the SHA256 of every file with
Get-FileHash and compare against the shipped manifest. Run in Windows
PowerShell 5.1:

    $base = 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify'
    $manifest = '<path-to>\manifest-sha256-full.txt'
    $data = @(Get-Content -LiteralPath $manifest | Where-Object { $_ -and -not $_.StartsWith('#') })
    if ($data.Count -ne 6298) { throw "expected 6298 data lines, got $($data.Count)" }
    $fail = @()
    foreach ($line in $data) {
        $sha, $rel = $line -split '  ', 2
        $p = Join-Path $base $rel
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { $fail += ('MISSING  ' + $rel); continue }
        $actual = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -cne $sha) { $fail += ('MISMATCH ' + $rel) }
    }
    $fail | ForEach-Object { Write-Output $_ }
    if ($fail.Count) { Write-Output ("FAIL: " + $fail.Count + " problem line(s)"); exit 1 }
    Write-Output 'OK: all 6298 files match manifest-sha256-full.txt'

Expected terminal output: `OK: all 6298 files match manifest-sha256-full.txt`.
Any MISSING or MISMATCH line, or a data-line count other than 6298, is a stop
condition. Also confirm the manifest itself arrived intact by comparing its
own SHA256 with the value recorded in section 1.

## 3. Manifest content statement (secret scan)

manifest-sha256-full.txt contains only SHA256 hex values, relative paths, and
comment lines; it embeds no file contents. It was scanned on host A on
2026-09-26 with the following results:

- Credential-pattern scan (password / passwd / secret / credential /
  api-key variants / Bearer / AKIA / AIza / sk- / ghp_ / gho_ / github_pat_ /
  xox- / PEM BEGIN / private key / .pem / .env): exactly 1 hit, the path
  `stage-attempt-1\input\python\Lib\secrets.py` -- the Python standard
  library module filename; false positive.
- Broad token/key word scan: 20 hits, all filenames of Python stdlib or
  packaged project source files (token.py, tokenize.py, keyword.py,
  has_key.py, config_key.py, pycore_token.h, _tokenizer.py, and names merely
  containing the letters "key" such as Turkey, monkeypatch.py, and the
  hockey digest modules); all false positives.
- Scan of path text for embedded high-entropy strings (32+ hex characters or
  40+ base64 characters): 0 hits.

Conclusion: no secret material is present in the manifest. The owner can
re-run the credential-pattern scan on arrival:

    Select-String -Path $manifest -Pattern 'sk-[a-zA-Z0-9]{8,}','ghp_','gho_','github_pat_','xox[baprs]-','AKIA[0-9A-Z]{16}','AIza[0-9A-Za-z_-]{20,}','-----BEGIN','[Bb]earer ','password','passwd','secret','api[_-]?key','credential','\.pem','\.env','private[_-]?key'

## 4. Staging steps (target host)

0. Complete preflight-checklist.md; every stop condition must be clear.
1. Collision check (preflight P5), then create the base directory:

        New-Item -ItemType Directory -Force -Path 'D:\Projects\.agent-artifacts\polymarket-alpha-lab\wp02-claude-verify'

2. Place the transferred payload so that every relative path in the manifest
   resolves under that base:
   - `official-attempt-1\official-probe.wsb`,
     `official-attempt-1\image\claude.exe`,
     `official-attempt-1\image\image-manifest.json`,
     `official-attempt-1\control\official-probe.cmd`
   - `stage-attempt-1\input\` (all 6,294 files)
   - `official-attempt-1\output\` recreated EMPTY if the transfer channel
     dropped the empty directory.
3. Re-run the in-place hash comparison (section 2). All 6,298 files must
   match before anything else happens.
4. Apply the staging permissions from preflight P5: input, image, and control
   marked read-only at the file level; output left writable and empty.
5. Run the claude.exe version preflight step (preflight P6) and confirm
   `2.1.278 (Claude Code)`.

## 5. Execution and evidence return

Execution itself follows the probe-exec runbook at
D:/Projects/.agent-artifacts/polymarket-alpha-lab/wp02-claude-verify/codex-plan-probe-exec.md
(six fixed scenarios: one success scenario plus five negative scenarios).
This file does not duplicate the runbook; the runbook governs the run.

After the six scenarios complete, or immediately at the first stop:

- Collect from the WRITABLE output directory
  (`official-attempt-1\output\`, guest `C:\pal-output`) ALL logs and outputs
  the run produced. Record a SHA256 for every collected file
  (Get-FileHash -Algorithm SHA256) so the returned evidence is itself
  verifiable.
- Preserve FIRST failures separately from any retry evidence. If anything is
  retried, keep the first attempt's artifacts untouched and label the retry
  explicitly; never overwrite a first failure with a later attempt.
- STOP-ON-FAILURE RULE: any scenario failure stops the whole run. Preserve
  all evidence as-is. No silent retry and no rerun without a new explicit
  owner decision. Isolation, integrity, or unsafe-output incidents abort
  immediately per the runbook.
- Return evidence through the same owner-controlled channel, never GitHub.

## 6. Boundaries

- Owner-controlled channel only; no GitHub publication of payload or
  evidence, ever.
- No credentials, no private account paths in any transferred material.
- The Phase 1 paper/report/readonly boundary is unchanged: no live trading,
  no account authentication, no order placement.
- claude.exe executes only inside the sandbox per the runbook; the only
  host-side execution is the --version preflight step (preflight P6).
