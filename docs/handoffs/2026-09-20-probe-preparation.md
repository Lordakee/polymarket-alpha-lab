# WP-02 / WP-06: prepare the missing host, do not repeat the rejected probe

## Latest owner report, 2026-09-20

The supplied local-agent report (headed `B9G_AUTHORIZED_RECOVERY_AND_RESUME_v1`)
says **BLOCKED before A/B**, with 6/6 official scenarios unexecuted, no pytest exit
code and no log/XML. It describes the user's working machine as containing business
PostgreSQL, personal files and credentials, and uv0.12.13 rather than0.10.0.
Those are user-reported prior facts, not new remote measurements. Do not call this
a failed test, recreate nonexistent evidence or infer B9G's other work completed.

The previous handoff incorrectly made safe preparation conditional on already
having the environment it was meant to enable. This preparation handoff supersedes
that circular prerequisite **only for the narrow operations below**. It does not
waive real-image isolation, credential, vendor-download or business-data limits.

## What the coordinator delivers

- `scripts/inspect_claude_probe_host.ps1`: read-only, named OS/CIM queries for
  edition, Sandbox optional feature and virtualization. It may run on the working
  host; it never scans HOME, credentials, installed CLI or business paths. Unknown
  or denied reads stay unknown. It does not enable features, elevate, change
  firewall/ACL/execution policy, start Sandbox or execute any vendor program.
- `scripts/claude_probe_environment.py`: stdlib-only archive verification and
  new-directory staging. No uv, pip, Git, global change or download at the local
  stage. Existing reported Python3.12x64 suffices. It never overwrites/deletes an
  existing attempt. No real database, package installer or official CLI executes.
- A CI-built offline Windows Python3.12x64 runtime and exactly locked pytest/
  tzdata dependencies, original committed research source and the existing fixed
  probe module. CI's uv0.10.0 belongs to CI, **not a requirement to downgrade the
  user's uv0.12.13**. Python's redistribution licenses and dependency licenses
  travel with the runtime. No official Claude/Codex image, key, .local, .git,
  runtime database, personal configuration or borrowed virtual environment.
- A generated `preparation-smoke.wsb`: networking, clipboard, audio/video, printer
  and vGPU disabled, Protected Client requested. ONLY a newly created input dir
  (read-only) and an empty dedicated output dir (writable) are mapped. Never map
  a project root, HOME, Downloads, whole drive or business installation. The guest
  logon runs only the packaged Python/import/127.0.0.1 smoke, not the official
  six-case probe. The output JSON is untrusted data, never executable instructions.

A clean guest can coexist with personal data on the parent; the parent itself is
not reclassified as secret-free. The config requests OS isolation but this source
change and ordinary Windows CI do not prove the user's Sandbox works or its actual
network boundary. Local feature state and the observed guest are separate evidence.

## Local task and stopping points

The response supplies an immutable GitHub source commit, exact file hashes/bytes,
and a retained release-asset ZIP with SHA256/bytes. Do not use expired Actions
artifacts as the only download, floating main/latest, or a guessed release URL.
Download and verify first; review the scripts before execution. Do not use
ExecutionPolicy Bypass, Unblock-File, automatic elevation or an unsigned-script
policy workaround. A policy denial is a real stop, not permission to switch tools.

1. On the current working host run only the read-only host helper. Do not query
   uv again or rediscover facts already supplied. Return its redacted JSON even
   if Sandbox is absent/disabled/unknown; this is a preparation result, not a new
   A/B attempt or a demand to create an already-empty machine.
2. Verify the pinned offline ZIP with the existing Python using `-I -S -B` and
   stage it into one fresh explicitly chosen directory. It generates the .wsb
   but starts no process. No vendor image/path/hash is required for this step.
3. If Sandbox is not already enabled, **stop at preparation**, return the exact
   next action needing owner/admin approval (Windows feature enable/reboot, or
   another approved guest). Do not enable it, alter BIOS or firewall, or promise
   that edition/virtualization facts guarantee it can start. No global uv change.
4. If it is already enabled, the owner may explicitly authorize opening the
   generated .wsb for a preparation-only smoke. This is a new guest, not reuse of
   the business OS as a test host. No official program or key is mapped or run.
   Without this explicit local authorization do not open it automatically.
5. Return one `output/environment.json` when produced. A passing smoke means only
   bundled Python/dependencies/import origin/loopback worked. It retains
   official_cases_run=0, sandbox_isolation_verified=false, activation_authorized=false.
   Do not open the same attempt again, clear its output or retry to green.

Never run the previous A/B prompt against the working installation. No real CLI
request belongs to this handoff. The source does not fetch an official binary via
CI/mirror/package or decide its publisher identity. An already verified supplied
image is still required for later official-image work, after the host exists.
The owner's absent-image report is accepted; do not ask the agent to search for it.

## Return evidence

Report: preparation status; immutable helper/release hashes; host helper JSON;
staging exit/status; whether a guest was authorized/launched; redacted smoke JSON
or first preparation error; exact remaining owner/admin/image-provenance action.
No hostnames/usernames, command history, environment dump, secret-store content,
business paths or arbitrary raw logs. Keep first failure and partial new directory.
No pytest/full-suite/DB/market checks need repeating. Missing official binary does
not prevent preparation, but never counts as passed official acceptance.

## Scope and evidence

The new Windows workflow builds in a fresh CI-owned managed interpreter using the
existing lock, tests the helper (including real PS5.1 with synthetic CIM answers),
and verifies two independently relocated package paths. It does not launch a VM,
change a user's Windows feature, run official Claude or claim an isolation audit.
No production module, original test, 68SQL, lockfile or existing CI deadline changes.
Separate same-assistant review and final exact-source results go in the PR before
merge. This is a deployment/preparation gap repair, not another business report.

Primary references checked 2026-09-20:
- https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file
- https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install
- https://docs.astral.sh/uv/concepts/python-versions/
- https://docs.python.org/3.12/using/windows.html

The Microsoft configuration reference documents the dangerous defaults (network
and clipboard enabled; mappings writable unless explicitly read-only). All are
explicit here. The install reference distinguishes feature enablement/reboot from
opening an already enabled Sandbox. Old instructions banning any preparatory work
are not a requirement to block harmless read-only discovery forever; actual OS
changes remain an explicit owner/admin decision. G2–G6 stay open.
