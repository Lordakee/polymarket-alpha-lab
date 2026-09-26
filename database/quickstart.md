# Native Windows project kit and operating guide

Read [the operating path](#one-operating-path-discovery-to-retained-simulation-and-settlement)
for discovery, approvals, tasks, simulation, settlement and restart.
[Version changes](#preserving-data-while-selecting-another-version) have separate
limits: do not treat this guide as an approved upgrade of an existing kit.

This kit carries the project source, locked Python dependency metadata, all
historical SQL migrations, and an approved PostgreSQL 17 engine archive. No
Docker, Supabase service, shared database installation or Windows database
service is needed. The engine is imported automatically on first explicit run.

**Python is still required.** This is a source + native database distribution,
not a standalone executable, Python installer, prebuilt venv, or offline wheel
collection. With an existing Python/uv environment, install the locked dependency
set in the extracted project directory:

```powershell
uv sync --locked --extra postgres
.\.venv\Scripts\python.exe scripts/start_project.py
```

Startup imports the installed PostgreSQL driver before touching native runtime or
database state. A missing package or a native-library loading error returns
`project_start_postgres_extra_required` without initializing a database. Reinstall
the locked `postgres` extra in this project's environment; do not delete database
data to repair a Python dependency failure.

The dependency installation may download Python packages. Database preparation
itself makes no public network request and invokes no model. The startup command
checks the kit's code/engine checksums, imports the engine, creates a **new**
private database when none exists, applies its locked migrations, verifies the
restricted application account and complete-history evaluation, then exits.
A database it starts is stopped after the check. Existing explicitly running
project instances are borrowed and left running. `status=ready` is infrastructure
readiness, not measured model accuracy or a running trading service.

An optional `--port 55433` chooses a different port only on first creation.
Repeating the command reuses the same database and credentials. A partial
initialization, changed package, foreign instance, missing runtime for existing
data, pending migration or incomplete research history blocks. Nothing is reset,
reinstalled over existing data, silently migrated, or automatically recovered.
Use the existing explicit `scripts/project_database.py migrate` only after review.

For application use, retain `ProjectPostgres(root).session()` as described in
`database/README.md`. This gives existing research/capture/outcome/evaluation APIs
a private instance without passing arbitrary DSNs. Live research still needs
explicit input, model configuration and provider authorization.

## Obtain and verify a kit

Use the outer ZIP SHA256 from a trusted build record before extracting into a
**new directory owned by your normal Windows account**. The internal
`PROJECT-BUNDLE.json` binds every selected code/migration file and the engine
archive, but cannot authenticate a publisher or make malicious Python safe.
Never run an untrusted archive merely because its internal hashes agree.

The archive contains no `.local`, generated credentials, old cluster, `.env`,
`.venv`, Git metadata, logs, captured evidence or test datasets. Each extraction
creates its own credentials/instance. Do not copy an initialized project to
another location; initialized instances remain bound to their original path.
Do not extract over an existing project as an upgrade mechanism. Keep backups
before long-term collection; this kit is NOT a database backup/restore tool.

The compressed engine seed `database/postgres-runtime.zip` stays in the kit;
first startup also creates a private expanded `runtime/postgres`. That consumes
space for both the seed and active engine. The importer still refuses execution
of changed runtime bytes and does not fall back to a system service or PATH.
Windows/C-runtime platform dependencies still apply. Actual platform/version
acceptance belongs in the build's test record; the kit targets Windows x64 and
PostgreSQL 17 only. It is not a verified Linux/macOS release.

## Maintainer build

Build on Windows x64 from a committed source checkout, with a trusted native
PostgreSQL 17 prefix and a new destination path:

```powershell
.\.venv\Scripts\python.exe scripts/build_project_bundle.py --native-prefix C:\Approved\pgsql --output C:\Builds\polymarket-native.zip
```

The builder reads only explicitly selected **committed Git blobs**, not arbitrary
working-directory files. Dirty tracked source blocks a build; untracked files
are not included. It copies only native bin/lib/share and supplied license
notices, never the prefix's data, service settings or credentials. Bundled program
files are not stored in Git. Checksums and version probes establish byte/version
consistency, not a supply-chain security audit; the maintainer must approve the
prefix and included source. Available upstream notices are retained in the seed.

A build writes a `.building` file and publishes a completed ZIP without overwrite.
An interrupted/failed build can leave its owned partial file; it does not publish
that partial as a valid kit or delete a prior output. The manifest identifies the
source commit/tree, target, engine version and file digests. Neither a kit nor a
passing synthetic test establishes real model forecasting performance.

## One operating path: discovery to retained simulation and settlement

This is the shared operator route for the existing commands, not a new scheduler
or a claim that V1 is released. **Only G1 is complete.** The three direction
decisions are already accepted: D1 permits the named local-agent choices (Codex,
Claude Code, OpenCode, Grok CLI, ZCode CLI), D2 permits sending all needed
research data, and D3 sets no first-round business-scale or monetary cap. Still
pending and separate from those decisions: the exact executable/version/model
configuration, an accepted isolation host and official binary probe, an approved
finite in-memory key supplier with its concurrency conditions, and the concrete
execution authorization for a real run.
A ChatGPT/Codex login does not configure this application. Do not search for keys,
copy an example into `.env`, or treat a synthetic test client as a real provider.

### 1. Select one code version and one physical project

After verifying and extracting a trusted kit as described above, select its
existing absolute directory. Replace the illustrative path; do not paste it as
an instruction to create or adopt another database. In PowerShell:

```powershell
$Project = 'C:\Research\polymarket-alpha-lab'
$Python = Join-Path $Project '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Install this version first' }
```

Use this Python environment and these absolute script paths even when your shell
is in another directory. The database and resolution-queue scripts, like the
other managed entrypoints, select their own adjacent `src` before importing the
project. A missing package in these two entrypoints returns
`project_entry_source_missing` rather than falling back to an unrelated editable
installation. This is source selection, not authentication of Python, a sandbox
against already-running code, or a substitute for outer ZIP verification.

`--root` selects **data/runtime/configuration and the migration catalog**, not the
version of Python source. Put it before task subcommands. The startup script is
different: `start_project.py` always uses its own root and has **no `--root` option**.
Do not mix code and data versions merely because a command accepts that flag.

Inspect configuration without creating a database:

```powershell
& $Python -I "$Project/scripts/project_database.py" --root $Project status
if ($LASTEXITCODE -ne 0) { throw 'Status failed; stop and preserve the error' }
& $Python -I "$Project/scripts/discover_crypto_research.py" --team crypto_btc --team crypto_eth --select-supported --max-candidates 5 --attempts 1
if ($LASTEXITCODE -ne 0) { throw 'Disabled discovery check failed' }
```

`not_initialized` from status is not an empty research history. Discovery without
`--allow-public-fetch` returns `disabled`, with no HTTP, model or database work.
Only after authorizing creation of a NEW project, run the startup command from the
installation section using this exact script. `ready` means infrastructure checks
passed, not that a model was configured or a research service was started.

### 2. Discover, review and stop at the authorization boundary

An explicitly permitted public-input fetch uses the same command with one added
permission. This performs network reads but no model call, research write or
research approval:

```powershell
& $Python -I "$Project/scripts/discover_crypto_research.py" --team crypto_btc --team crypto_eth --select-supported --max-candidates 5 --attempts 1 --allow-public-fetch
if ($LASTEXITCODE -ne 0) { throw 'Discovery incomplete or rejected; retain its status, do not retry silently' }
```

Read each team's result, rejection/failed-check trace, unchecked candidates and
fresh cutoff. `ready_for_operator_review` and `pending_spec` are NOT approval.
Review the complete current question/rules, supported terminal contract, actual
observation minute and source suitability before a new forecast. Coinbase/Kraken
USD hourly references do not establish Binance USDT minute settlement. A later
attempt must not recycle an old cutoff or relabel an old snapshot as fresh.

The discovery console does not retain the typed source objects needed for live
execution. JSON output is not an executable task specification. The authorized
application must prepare fresh reviewed requests using the existing
[crypto launch](../docs/research-crypto-launch.md),
[contract](../docs/research-crypto-contract-scope.md) and
[observation](../docs/research-crypto-observation-time.md) paths. No file queue or
new loader is provided here. What gates live execution is no longer a D1-D3
decision: the remaining prerequisites are the exact executable/version/model
configuration, an accepted isolation host and official binary probe, an approved
finite in-memory key supplier, and the concrete execution authorization recorded
in the [local-agent integration](../docs/research-local-agent.md) contract.

### 3. Admit reviewed work, run one turn, then inspect

The accepted first-round route is uncapped and runs through the delivered typed
assembly `run_claude_research_rotation` in
`src/polymarket_alpha_lab/research_claude_operator.py`, which composes the stored
authorization, two reviewed single-request BTC/ETH batches, the lazy Claude
factory, the durable call audit and one bounded rotation. Its exact supplied
inputs and side effects are stated in the
[local-agent integration](../docs/research-local-agent.md) guide. Importing that
module is inert; invoking the function is NOT a harmless readiness check: it
writes the typed uncapped authorization, enqueues both batches and can enter the
real model path, with each step committing separately. It is application
assembly for an authorized application, not a standalone command, and the
remaining activation prerequisites above still apply before any real call.

The capped-budget alternative remains supported. Admit the reviewed batch and
budget through the existing task command's
`enqueue-batch --allow-queue-write` and `create-budget --allow-budget-write`, or
through the original typed session APIs. Each command also requires its original
ID, `--input-sha256` and canonical binary stdin; it never runs research or reserves
a model call. Use the [task guide](../docs/research-dispatch.md) for the exact input
transport and the [budget contract](../docs/research-model-budget.md) for reviewed
request hashes and an independently checked per-call charge bound. These are two
separate explicit writes, not an atomic pair: inspect the original IDs after any
failure, and only explicitly replay the same approved input. Creation does not
reset a used budget. Do not use the older unbudgeted API default for the real V1
workflow or count response token totals as a hard monetary ceiling. An inspection
command creates neither a batch nor an allowance.

The standalone `run-turn` script intentionally has **no model factory**. Even with
`--allow-model-calls`, it returns exit 2 before opening a managed session. These
commands are for reading the existing approved identifiers, not for enrolling them:

```powershell
& $Python -I "$Project/scripts/manage_research_tasks.py" --root $Project inspect-batch --batch-id approved-btc-batch
if ($LASTEXITCODE -ne 0) { throw 'Batch unavailable; inspect the error before proceeding' }
& $Python -I "$Project/scripts/manage_research_tasks.py" --root $Project inspect-budget --budget-id approved-budget
if ($LASTEXITCODE -ne 0) { throw 'Budget unavailable; do not run research' }
& $Python -I "$Project/scripts/manage_research_tasks.py" --root $Project inspect-turn --rotation-id approved-roster --turn-id turn-1
if ($LASTEXITCODE -ne 0) { throw 'Turn unavailable; do not infer that it never ran' }
```

The application may invoke `research_dispatch_cli.main` with its approved
`model_factory`, explicit `--budget-id` and `--allow-model-calls`; its parser and
original budgeted runner are the same as the console. The complete assembly is in
the task guide. This quickstart does not provide a default or dynamically loaded
client. Exit 0 for a replay/no-work turn is not proof all research completed.

After any run or interruption, list the ORIGINAL claims and results:

```powershell
& $Python -I "$Project/scripts/list_project_research.py" --root $Project --max-records 1000
if ($LASTEXITCODE -ne 0) { throw 'Inventory failed; do not assume an empty or complete history' }
& $Python -I "$Project/scripts/inspect_project_research.py" --root $Project --record-id original-record
if ($LASTEXITCODE -ne 0) { throw 'Original record unavailable; do not create a replacement' }
```

`captured` includes failed/blocked research, not only completed forecasts.
`incomplete` means a claim without a saved result; worker liveness is unknown.
Never age-reclaim, change task IDs, replenish a budget or call the model again to
replace that result. Capture-only recovery requires the still-held ORIGINAL
result through the existing typed API; a console receipt cannot reconstruct it.

### 4. Save the reviewed simulation before its original cutoff

Use the existing [simulation contract](../docs/research-paper.md) to construct a
`ResearchPaperScenario` from a saved forecast, current raw market/YES/NO books,
explicit quantity, all six costs, risk gates and the original record hash. Review
the canonical input and its SHA256 before the write. A digest is a byte binding,
not proof of source authenticity, approval or real exchange fees.

The existing `capture-paper` subcommand needs the original record ID,
`--input-sha256` and `--allow-paper-write`, plus one canonical UTF-8 input on binary
stdin. Do not use `Get-Content`, PowerShell's text pipeline, JSON reformatting or a
new business file journal to transport it. An approved application can send the
already-reviewed in-memory bytes directly (names below are supplied values, not
file paths or discovered credentials):

```python
from hashlib import sha256
from pathlib import Path
import subprocess

project = Path(actual_project_root)
assert type(reviewed_payload) is bytes
assert sha256(reviewed_payload).hexdigest() == reviewed_input_sha256
result = subprocess.run([
    str(project / '.venv/Scripts/python.exe'), '-I',
    str(project / 'scripts/manage_research_tasks.py'), '--root', str(project),
    'capture-paper', '--record-id', original_record_id,
    '--input-sha256', reviewed_input_sha256, '--allow-paper-write',
], input=reviewed_payload, capture_output=True, shell=False, check=False)
# Examine returncode AND the existing JSON receipt; do not automatically retry.
```

This is an explicitly authorized database write, never an exchange order. One
original record has one immutable input/result. Identical replay returns the
first receipt; changed input conflicts. Exit 0 with `paper_receipt_returned` can
mean a SAVED REJECTION or `not_simulated`, not a trade approval. Invalid binding,
missing research, incomplete history or expired admission cannot fabricate a
saved rejection. If the command errors or output is lost, a commit may already
have happened: inspect the SAME record first, then only explicitly replay the
SAME reviewed input. The console will not refresh timestamps or costs.

```powershell
& $Python -I "$Project/scripts/manage_research_tasks.py" --root $Project inspect-paper --record-id original-record
if ($LASTEXITCODE -ne 0) { throw 'Simulation receipt unavailable; inspect original state before any replay' }
```

### 5. Collect unconfirmed evidence, independently confirm, then evaluate

Start with a read-only resolution worklist:

```powershell
& $Python -I "$Project/scripts/review_resolution_queue.py" --root $Project --max-markets 1000
if ($LASTEXITCODE -ne 0) { throw 'Resolution listing failed; do not infer settlement' }
```

Only when public collection AND unconfirmed-evidence storage are authorized, add
`--collect --allow-public-fetch --max-requests 2` to that command. This can WRITE
unconfirmed candidates; it is not a read-only fetch, outcome confirmation or model
call. Review the exact retained candidate and original prediction privately.

```powershell
& $Python -I "$Project/scripts/inspect_project_resolution.py" --root $Project --review-id retained-candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate unavailable; stop before confirmation' }
```

Independent human verification must match the original venue, pair, minute and
Close with the actual YES/NO result. Missing, disputed, mismatched or unverifiable
evidence stays unresolved. The existing confirmation mode is
`review_resolution_queue.py --confirm --allow-resolution-write`, consuming one
reviewed bounded stdin object defined in the
[resolution guide](../docs/research-resolution-queue.md). It forbids collection
flags, binds original/candidate hashes and stores review/outcome atomically. Use
authorized binary transport as above; do not copy a historical example as actual
evidence, auto-approve a candidate, or substitute a legacy direct outcome write.

Read probability diagnostics first, then the retained cost-aware settlement view:

```powershell
& $Python -I "$Project/scripts/evaluate_project_research.py" --root $Project
if ($LASTEXITCODE -ne 0) { throw 'History evaluation blocked; retain incomplete and failed attempts' }
& $Python -I "$Project/scripts/evaluate_project_research.py" --root $Project --settled-paper
if ($LASTEXITCODE -ne 0) { throw 'Settled-paper evaluation blocked; do not use a partial substitute' }
```

Both reads may start/stop the private engine, but do not write business records.
`--include-decisions` explicitly adds per-record details; identifiers/hashes are
still business metadata, not anonymous public data. `--at` is a historical cutoff,
not a request to alter data. An empty view or zero scored events can be a valid
operation result, not strategy success. `incomplete` blocks strict evaluation.
The settled view keeps failed/later/rejected/missing/unresolved attempts, and
subtracts the ORIGINAL saved cost upper bound from reviewed settlement payment.
It reports an assumption-dependent simulated lower bound, **not account P&L**.
No after-the-fact side selection, verified tariff, actual fill or statistical
promotion follows from it. See the [settlement contract](../docs/research-paper-settlement.md).

### 6. Stop and restart without erasing history

There is no standalone `stop-turn` subcommand or automatic background service.
An authorized application requests `ResearchDispatchStop.request_stop()` or handles
Ctrl+C through the original cooperative drain. Previously admitted work can finish;
a hung client can delay completion, so bounded client I/O remains required.
Inspect the original batch/turn/budget after an uncertain stop. The SAME turn ID
only replays its selection receipt; a NEW explicitly chosen turn continues the
cursor, but never restarts captured or incomplete tasks.

After all managed sessions and admitted work have finished, explicit engine stop
is available; it does not cancel research:

```powershell
& $Python -I "$Project/scripts/project_database.py" --root $Project down
if ($LASTEXITCODE -ne 0) { throw 'Stop blocked; do not force-kill or delete lock/state files' }
& $Python -I "$Project/scripts/project_database.py" --root $Project status
if ($LASTEXITCODE -ne 0) { throw 'Could not verify stopped state' }
```

A managed command stops an engine it started and leaves an explicitly running
borrowed instance running. `up` alone starts infrastructure, not a dispatcher.
On restart, query saved state before deciding the next operation. Startup may
refuse an incomplete history even while metadata inspection remains available;
never delete the incomplete claim just to make startup return `ready`.

### Errors: read the exit code and the operation's own JSON

| Result | Required action |
| --- | --- |
| Exit 0 | Read the operation status. Disabled discovery, no work, saved rejection or unscored history is not business success. |
| Exit 1 | Operation/cleanup/output failure. Possible writes or admitted work are not rolled back merely because output failed. Inspect original IDs. |
| Exit 2 | Arguments or permission/client prerequisite failed. Read that command's fixed error/help, not a fallback execution path. |
| Exit 3 on an inspection | That identifier was not found, not evidence the whole database is empty or no prior action committed. |
| Exit 130 where supported | Interrupted/cooperatively stopped; inspect admitted work before proceeding. Other commands may propagate interruption differently. |

Do not send raw inputs, model outputs, credentials, database files or backups to
GitHub/chat. Keep the actual business evidence only in the project database;
share only an explicitly reviewed, sanitized engineering summary when requested.

## Preserving data while selecting another version

**No general old-kit upgrade or rollback is delivered here.** The source-root
fix selects Python code; it does not move the database or install new schema.
Every command using `--root` still reads runtime, private identity and migration
catalog from that physical root. New code pointing to an old kit cannot create
missing tables just because its own source checkout contains newer migrations.

For an existing immutable kit, keep its complete old directory and database in
place. Do not overlay a new ZIP, edit `PROJECT-BUNDLE.json`, copy `.local`, rename
the initialized root or alter the engine. A new extraction is an independent
empty instance, NOT migration of old history. `start_project.py` verifies its own
kit; other commands must not be used to bypass a failed kit verification.

For an explicitly authorized SOURCE installation (not an immutable old kit), a
version-change plan must pin current/candidate commits and the original physical
root, review dependencies and the complete migration prefix, and retain a private
cold backup before any change. The existing backup/migrate/restore commands are
specified in [database/README.md](README.md); they are not automatic upgrade steps.
Backup archives include private credentials and require private storage outside
the project; never upload them as engineering evidence. Migration is append-only,
explicit and uses the catalog at the selected data root. A schema change is not
undone by checking out old code. Restore refuses existing data; do not delete a
working cluster to force it through. Cross-path restore/adoption is not promised.

### Ordered source-switch procedure for a separately authorized release

The steps below make that boundary operational. They add no switch command,
persistent selector or approval record; every executable line is an existing
entrypoint already documented in this guide. The procedure stays
release-gated: the paths below are illustrative placeholders, and the
retained historical offline/native evidence for the pinned version pair is
evidence, not deployment approval. A missing release-specific value (a pinned
commit or tree, environment, archive hash or size) blocks use of the
procedure instead of silently defaulting.

**1. Pin the intended operation.** Record both versions' source commits and
trees, their Python environments, the trusted outer archive SHA256 values and
byte sizes, the unchanged original physical root, the runtime version and
instance identity, and reviewed compatibility evidence covering EVERY
feature you intend to operate, not only the migration counts in step 3. Keep
the complete OLD kit and its environment in place as the rollback baseline.
Pin the values from the reviewed release record, replacing every illustrative
path:

```powershell
$OriginalRoot = 'C:\Example\Existing\polymarket-alpha-lab'
$CandidateSource = 'C:\Example\NewKit\polymarket-alpha-lab'
$CandidatePython = Join-Path $CandidateSource '.venv\Scripts\python.exe'
$OldSource = 'C:\Example\RetainedOld\polymarket-alpha-lab'
$OldPython = Join-Path $OldSource '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $OriginalRoot -PathType Container)) { throw 'Pin the reviewed original root; an illustrative path is not deployment approval' }
if (-not (Test-Path -LiteralPath $CandidatePython -PathType Leaf)) { throw 'Reviewed candidate kit is not installed in its own directory; do not proceed' }
if (-not (Test-Path -LiteralPath $OldPython -PathType Leaf)) { throw 'Complete retained old kit missing; there is no rollback baseline' }
```

When the original installation's own code is the reviewed OLD source, pin
`$OldSource` to that same absolute path as `$OriginalRoot`; the two values are
still pinned and reviewed separately.

**2. Prepare the candidate source separately.** Verify the candidate's OUTER
archive SHA256 and byte size against the trusted build record BEFORE using
any code from it, then extract it into a NEW side-by-side directory as
described under [obtain and verify a kit](#obtain-and-verify-a-kit).
Preparing candidate source does not initialize a replacement database. A
declared kit's extracted inventory is checked by the existing
`verify_distribution` API at managed-session entry, for both the source
directory and the selected data root; this procedure adds no separate
verifier command. NEVER run `start_project.py` for this purpose: it has no
`--root` option and verifies and initializes its own installation instead of
selecting this root.

**3. Make schema compatibility a hard precondition.** The original root keeps
its effective migration catalog (`database/migrations.lock.json` plus
`supabase/migrations`) and its applied migration ledger exactly as they are;
establish both from reviewed evidence of the actual installation, not from
assumption. The counts below name the pinned historical pair (an OLD
63-entry catalog and a 68-entry candidate catalog) only, not a general rule
for other version pairs:

| Effective catalog / applied ledger | Required decision before selection |
| --- | --- |
| 63 entries / 63 applied | The candidate's complete NEW functionality is unsupported on the unchanged schema; only the specifically evidenced common operations may be considered. |
| 68 entries / 63 applied | Migrations are pending; managed sessions refuse entry with `project_postgres_migrations_pending`. Stop. Catalog adoption and migration are separately authorized, never implied by new source. |
| 63 entries / 68 applied | Conflicting history; refusal is `project_postgres_migration_history_conflict`, and selecting an old catalog does not undo schema changes. Stop. |
| 68 entries / 68 applied | The catalog condition is satisfied only; candidate-feature compatibility and installation evidence are still required. Counts alone are insufficient. |

Unknown requirements, a missing intended feature, pending or conflicting
history, missing compatibility evidence, a failed kit check, or runtime or
identity drift stops the procedure BEFORE any source selection.

**4. Drain before stopping.** Under the already-authorized maintenance window,
stop admitting new work and let previously admitted work finish through the
existing cooperative controls described under [stop and restart without
erasing history](#6-stop-and-restart-without-erasing-history); there is no
`stop-turn` CLI to invent or invoke. Preserve admitted, failed and incomplete
work exactly as recorded. Only after the drain, stop the engine and verify
the stopped state with the currently selected reviewed source (illustratively
the retained OLD kit):

```powershell
& $OldPython -I "$OldSource/scripts/project_database.py" --root $OriginalRoot down
if ($LASTEXITCODE -ne 0) { throw 'Stop blocked; do not force-kill or delete lock/state files' }
& $OldPython -I "$OldSource/scripts/project_database.py" --root $OriginalRoot status
if ($LASTEXITCODE -ne 0) { throw 'Could not verify stopped state' }
```

A busy engine or an active-connection failure never permits force-killing
processes or deleting lock or state files; retain the failure and stop the
procedure.

**5. Require verified private recovery material.** This step exists only
under the later, separate installation and backup authorization; the switch
itself does not authorize a backup. With the engine stopped, use the existing
cold-backup commands from a specifically pinned management-tool revision
whose flags that revision's own documentation confirms; do not assume a
historical OLD kit supports current flags. The destination must be a NEW
directory OUTSIDE the project under an already existing parent. Backups
contain private credentials: keep the directory private, never publish it,
and retain the SHA256 independently of the backup media:

```powershell
& $OldPython -I "$OldSource/scripts/project_database.py" --root $OriginalRoot backup --destination 'D:\Example\Backups\PreSwitch'
if ($LASTEXITCODE -ne 0) { throw 'Backup failed or was refused; the switch is blocked' }
& $OldPython -I "$OldSource/scripts/project_database.py" --root $OriginalRoot verify-backup --archive 'D:\Example\Backups\PreSwitch\snapshot.palpg.zip' --sha256 YOUR_RETAINED_SHA256 --trusted-backup
if ($LASTEXITCODE -ne 0) { throw 'Backup verification failed; the switch is blocked' }
```

`--trusted-backup` approves a backup of your own trusted database; it is not
a compatibility or upgrade check, and `--allow-catalog-extension` is not part
of this procedure. Any backup or verification failure blocks the switch.
Restore stays a separate disaster-recovery operation with an absent-target
requirement; it is never wired into this switch.

**6. Bind an explicit operator approval point.** Before any invocation
changes, the operator's existing approval process must explicitly bind both
source versions with their commits, trees and environments, the unchanged
`$OriginalRoot`, the compatibility evidence covering every intended
operation, the verified recovery material, and the switch and rollback
window. This guide adds no approval database, file journal or selector; the
approval lives in that existing process. No approval, no switch.

**7. Select source and environment.** The switch is only which absolute
entrypoint subsequent commands invoke. Keep `--root` on `$OriginalRoot`, in
its existing position before the subcommand: the invoked script still selects
its own adjacent source, and the explicit `--root` selects the data target,
overriding the script's adjacent default. Selection alone must not alter
catalogs, runtime, identity, credentials or business records:

```powershell
& $CandidatePython -I "$CandidateSource/scripts/project_database.py" --root $OriginalRoot status
if ($LASTEXITCODE -ne 0) { throw 'Candidate status failed; retain the error, do not force anything' }
```

Routine rollback selects the retained OLD kit and environment again with the
same root:

```powershell
& $OldPython -I "$OldSource/scripts/project_database.py" --root $OriginalRoot status
if ($LASTEXITCODE -ne 0) { throw 'Old-source status failed; retain the error' }
```

The direct OLD form above applies only when the retained OLD kit ships
`scripts/project_database.py` with today's adjacent-source behavior; the
retained historical pair needed an explicit adjacent-source runner, so pin
the OLD kit's actual entrypoint form from its own reviewed evidence instead
of assuming today's wrapper.

**8. Keep subsequent operations separately authorized.** Engine start and
managed reads are later, separately authorized operations: a session may
start PostgreSQL and change WAL, control and log state even when the business
operation is read-only, so physical byte equality of cluster files is not
promised after the engine starts. Source rollback remains valid only while
the original schema and storage contract stay compatible; it cannot undo
written records or schema changes, and any such requirement stops for a
separate design and authorization.

A release-specific reviewed procedure and final Windows end-to-end acceptance
are still required before deploying a changed version to an existing user's data.
This guide authorizes none of those user-machine writes. The known intermittent
PS5.1 first-invocation problem is still open; its test observations do not prove a
runtime fix. WP-06/G6 remain open, as do real forecast/input/fee acceptance and
the still-pending exact executable/version/model configuration and concrete
execution authorization; the D1-D3 decisions themselves are accepted.

## Maintainer acceptance: one packaged research-to-settlement route

The native distribution test now continues inside its fresh second extraction,
using that kit's Python and project modules, not checkout application code. A
reviewed test-only recipe supplies synthetic BTC/ETH requests and clients; it is
NOT shipped as an application, a model adapter or an operator command.

The proof creates a seven-call allowance, executes two bounded turns separated
by a database restart, and checks that replay consumes no extra allowance. It
saves two ready simulations, one rejected simulation and one failed research
result through the actual task command. After the declared UTC minute really
closes, the confirmation command stores synthetic independently-reviewed YES
outcomes; the actual evaluation command must reproduce the original cost-bound
results (BTC 2.971 and ETH -3.029 payout units) and retain both excluded attempts.
Historical and current exports must agree with the same packaged API after restart.

A separate synthetic child then exits abruptly after committing its claim and
one call reservation. The saved claim stays incomplete, its allowance is not
refunded, replay never constructs another client, and current strict evaluation
blocks while a pre-interruption historical view remains unchanged. The recipe
also checks all loaded project modules and the unchanged kit manifest.

This is isolated engineering evidence, not real source/fee verification, actual
human review, real model use or account P&L. It does not close G2-G6, the old
PS5.1 issue or release-specific upgrade acceptance; D1-D3 are accepted, and the
exact executable/version/model configuration and concrete execution authorization
under them remain pending. Existing component tests
remain in place. The new recipe has its own bounded child execution; no existing
process/job timeout, assertion, provider permission or user data is changed.

The combined PR44/PR45 proof also creates one real synthetic confirmation through
that kit's command with a deliberately short output sink. It first proves the
review is absent, requires a success-status output prefix and nonzero exit, then
reads back the committed review/outcome and explicitly replays the SAME input.
The original receipt and timestamps must match. No database/transaction mock is
used for this step; no new model call, alternate review ID or automatic retry is
permitted. It verifies this simulated failure, not real source/human acceptance.


### Cold backup across an appended migration catalog

The existing backup verifier/restorer offers an explicit `--allow-catalog-extension`
for reviewed SOURCE installations at the original physical root. Default behavior
still requires identical catalogs. The option accepts only the backup's unchanged
nonempty historical prefix of the fully validated current catalog, keeps exact
engine/root/trust/hash checks and NEVER overwrites an existing database or applies
SQL. It does not upgrade an immutable old kit. Its reported catalog counts are NOT
the snapshot's applied ledger; managed sessions still refuse pending migrations.
See [the backup contract](README.md#explicit-backupcatalog-extension-compatibility-not-an-upgrade)
for the separate permissions and private recovery procedure. This is not an
instruction to modify a user's existing installation or delete its original data.


## Maintainer acceptance: recover the complete packaged evidence

The same disposable second kit now also passes through its EXISTING `backup`,
`verify-backup` and `restore` commands in a separate test-only process. Before
backup it has four captured attempts, four simulation receipts, two settlements,
two batches/two turns, eight nonrefundable reservations and one incomplete claim.
The test requires a stopped instance, the known fixture identity and the complete
expected roster before the simulated recovery. It is not a general operator tool.

The proof checks the actual archive checksum, refusal to overwrite existing data,
and refusal of a bad checksum before staging. It then makes the original fixture
files unavailable by retaining them in another private directory, NEVER deleting
them. Restore goes to the SAME original physical project path and uses the SAME
runtime and migration catalog. Before restart, every restored byte is compared
with the cold source inventory, including the generated test credentials, WAL
and transaction state. The preserved original must also remain byte-identical.

After restart, the original requests/results, accepted/rejected simulations,
unconfirmed candidates/confirmed reviews, batches/turns, stored budget policies
and reserved amounts, and the explicitly fixed historical evaluation must match.
Only fresh budget observation times and batch `generated_at` query times are
excluded. Every original batch payload/enqueue time and execution claim/result is
compared; each batch snapshot is revalidated before projecting those stored fields.
Explicit original-request and original-simulation replays must make no model call,
refund no reservation and change no history. Strict current evaluation must still
refuse the incomplete claim. The recovered instance is left stopped.

This adds a separate 180-second test child and leaves all previous test/process/job
limits unchanged. The backup and preserved cluster contain PRIVATE synthetic
credentials and stay inside the disposable runner directory; they are not uploaded
with logs, source, or the kit. Only fixed engineering outcomes are emitted.

This is same-version, same-path cold recovery of synthetic data, not a version
upgrade, rollback, cross-machine/path adoption, real disaster recovery or actual
human/market acceptance. Existing cold-backup implementation and its component
regressions are unchanged. No recipe or recovery archive is shipped in the kit.
G2-G6, release-specific upgrade decisions and the PS5.1 issue remain open; D1-D3
are accepted, and the exact executable/version/model configuration and concrete
execution authorization under them remain pending.

PostgreSQL's file-system backup restrictions are documented at
https://www.postgresql.org/docs/17/backup-file.html (checked 2026-09-16): this test
uses a cleanly stopped WHOLE cluster, not isolated table copies or a live tar.


The integrated recovery comparison explicitly checks the current batch-snapshot
field inventory: a future additional field requires review rather than silently
being omitted. An invalid observation clock is still rejected by the original
snapshot constructor. This fixes the old test's comparison of two different
query times, not a change to the database backup format or stored timestamps.
The original failed Windows proof is preserved; a controlled reproduction proves
this comparison defect but does not identify every possible cause of that older
generic mismatch. The final combined-tree CI result is recorded in PR #46.


### Managed research also checks declared kit integrity

Every new `ProjectPostgres(root).session()` reuses the existing bundle verifier
BEFORE taking the lifecycle lease, reading private state, or starting/borrowing
an engine. It checks both the source/kit directory containing the imported server
module and the selected data root (once if they are the same). Either
`PROJECT-BUNDLE.json` or `database/postgres-runtime.zip` identifies a declared kit;
a missing companion, changed payload, extra selected code/SQL, reparse point or
unreadable marker refuses entry. There is no cached success between sessions.
This covers existing managed research, task, simulation and confirmation paths,
not only `start_project.py`. Console commands retain their existing fixed failure
responses and must not be retried against another root to bypass the rejection.

This is an entry-time integrity check, NOT source authentication, an atomic
filesystem snapshot or a sandbox against Python code already imported/executed.
Both markers absent remains the explicit SOURCE-installation path; removing both
markers maliciously is not detected as a previously installed kit. Check the
trusted outer archive before execution. Mid-session file changes are not monitored;
admitted work still uses its original cleanup, and the next entry rechecks bytes.
No new schema/version compatibility is inferred when code and data roots differ.

The separate `status`/`down` infrastructure controls are unchanged, so a rejected
research entry does not itself stop a borrowed running engine or block an operator
from its existing safe-stop procedure. This does not authorize an old-kit overlay,
file repair, deletion of state/markers, user database migration or real model call.


The mainline integration retains managed-session draining and cold-recovery
semantics. Integrity admission happens before the private lifecycle lease; after
admission, existing work drains even when close is interrupted. An already-running
borrowed engine stays owned by its caller. A later bundle change is rejected at
the next entry, not used to drop the lease during admitted work. The combined
tests use real Python Conditions/threads with synthetic lifecycle for unit checks;
the existing packaged drain and cold-recovery scenarios provide separate real
PostgreSQL coverage. All previous limits and failed-run evidence are retained.
This integration is not a diagnosis or repair of the intermittent PS5.1 first run.
Python Condition semantics reference checked 2026-09-18:
https://docs.python.org/3.12/library/threading.html#condition-objects


## Before selecting a real provider or changing an existing installation

The [approved-client assembly contract](../docs/research-model-budget.md#approved-client-assembly-contract-wp-02-design-only)
is the pending adapter's design and acceptance boundary, not a delivered provider
or a command that enables one. D1-D3 are already accepted as non-secret
decisions: D1 permits the named local-agent choices, D2 permits all needed
research data, and D3 sets no first-round business-scale or monetary cap. Do not
re-ask them; the remaining decisions are the exact executable/version/model
configuration and the concrete execution authorization for a real run. Do not
paste a key or ask a local agent to find credentials. Generic allowance tests do
not certify a provider's invoice or SDK retry behavior.

Cold backup verification/restoration remains bound to the ORIGINAL physical
project path, platform and engine. `--allow-catalog-extension` does not authorize
restoring into a sibling directory, changing instance identity or moving `.local`.
A second unpacked kit is a separate empty installation, not a migrated copy of
old history. Do not delete or rename a working database to satisfy restore's
absent-target requirement. The same-root cold-recovery tests are not a general
version-switch or cross-path restore procedure. No such user-data operation is
performed or authorized by this documentation update.
