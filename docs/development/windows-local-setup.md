# Windows Local Development Setup

Use this guide to install the checked-in project and verify it in Windows
PowerShell or Git Bash. Verification is offline and keeps Phase 1 paper-only,
report-only, and readonly. It does not fetch market data or require a database.

## Prerequisites

- Git, uv, and Python 3.12 available on the workstation. The project supports
  Python 3.11 or newer; Python 3.12 is the reference for this setup.
- A checkout of this repository. The examples use
  `D:\Projects\polymarket-alpha-lab`; adjust that path for your checkout.
- The checked-in `pyproject.toml` and `uv.lock`. Dependency installation may need
  network access for packages or the interpreter when they are not cached.

The reference environment uses Python 3.12.10, uv 0.12.8, pytest 9.1.1, and
psycopg 3.3.4. The initial checkout was `4cb9a056`. Its bootstrap installation
used `uv sync --frozen --extra dev --extra postgres --python 3.12`; installation,
`uv lock --check`, `uv pip check`, CLI help/report discovery, and compilation of
`src` and `tests` passed. Those checks do not establish a full pytest or real
database result.
Use `--locked` below so setup also checks that the lock matches project metadata.

## Install and Verify

Both shells use the same Windows `.venv/Scripts` executables. Environment
activation and PowerShell execution-policy changes are unnecessary. Run each
command in order and stop on failure; in PowerShell, check `$LASTEXITCODE` after
native commands as shown.

### PowerShell

```powershell
Set-Location 'D:\Projects\polymarket-alpha-lab'
uv sync --locked --extra dev --extra postgres --python 3.12
if ($LASTEXITCODE -ne 0) { throw 'Locked installation failed' }
uv pip check --python .\.venv\Scripts\python.exe
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
& .\.venv\Scripts\python.exe .\scripts\verify_local.py --quick
if ($LASTEXITCODE -ne 0) { throw 'Quick verification failed' }
```

For a complete offline baseline:

```powershell
& .\.venv\Scripts\python.exe .\scripts\verify_local.py --full
if ($LASTEXITCODE -ne 0) { throw 'Full verification failed' }
```

### Git Bash

```bash
cd /d/Projects/polymarket-alpha-lab
uv sync --locked --extra dev --extra postgres --python 3.12
uv pip check --python .venv/Scripts/python.exe
.venv/Scripts/python.exe scripts/verify_local.py --quick
```

For a complete offline baseline:

```bash
.venv/Scripts/python.exe scripts/verify_local.py --full
```

The `dev` extra supplies test dependencies. The `postgres` extra supplies the
existing psycopg driver and is optional for offline setup: omit
`--extra postgres` if the driver is not needed. The reference environment
includes it. Installing the driver does not start or connect to Postgres.

## What Verification Covers

[`scripts/verify_local.py`](../../scripts/verify_local.py) accepts `--quick`
(the default when no mode is supplied) or `--full`. These are mutually exclusive;
there are no other task selectors.

Both modes require a virtual environment and its console executable, verify
installed distribution metadata, and check that the editable install points to
this checkout. They exercise both the module entrypoint with Python `-I` and the
virtual environment's console executable from a temporary directory
outside the repository. This checks installation independently of pytest's
configured `src` import path. If `TMPDIR` or `TEMP` points inside the checkout,
the verifier uses a temporary sibling directory instead and removes it after
the checks. It reports an error if no writable location outside the repository
is available. CLI smoke commands are limited to `--help` and
[`report-discovery`](../cli/phase1-report-discovery.md), which lists registered
report entrypoints without executing them.

- `--quick` runs focused tests and compiles `src`, `tests`, and `scripts`.
- `--full` runs the complete pytest suite instead of the focused selection,
  along with the same installation, CLI, and compilation checks. It does not
  separately rerun the focused tests.

The verifier derives the repository root from its own file, uses the invoking
Python interpreter for subprocesses, and reports failing steps with a nonzero
exit code. It does not install dependencies, change the lock, or start services.
Run full verification once at a time; record the revision, command, exit code,
actual pytest counts, warnings, and elapsed time when reporting a baseline.

The verifier removes inherited `POLYMARKET_ALPHA_LAB_*`, `PYTEST_ADDOPTS`,
`PYTEST_PLUGINS`, `PYTHONPATH`, and `PYTHONHOME` overrides from its subprocess
environments, then sets `POLYMARKET_ALPHA_LAB_RUN_SUPABASE_SMOKE=0` and
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` there. It leaves the calling shell environment
unchanged, does not import `.env`, and requires no DSN. Keep the real database
smoke disabled for offline verification.

You can invoke the script from any working directory by using absolute paths to
both the repository's virtual environment Python and the script.

PowerShell:

```powershell
& 'D:\Projects\polymarket-alpha-lab\.venv\Scripts\python.exe' 'D:\Projects\polymarket-alpha-lab\scripts\verify_local.py' --quick
```

Git Bash:

```bash
/d/Projects/polymarket-alpha-lab/.venv/Scripts/python.exe /d/Projects/polymarket-alpha-lab/scripts/verify_local.py --quick
```

Use `--full` in either command for a full run. The legacy `scan` examples in the
README fetch public market data and use legacy file outputs; they are outside
this onboarding flow.

## Troubleshooting

- **uv or Python is unavailable:** make the prerequisite tools available through
  your normal development toolchain, then rerun the locked installation from
  the repository root. Use Python 3.12 and a uv version compatible with the
  checked-in lock; uv 0.12.8 is the reference version.
- **Locked installation fails:** inspect the reported interpreter, download, or
  metadata error. Keep `--locked`; do not regenerate `uv.lock` or upgrade all
  dependencies to hide the failure. Uncached installation needs package access,
  whereas verification itself is offline.
- **Module, console executable, or editable source is wrong:** use this
  checkout's `.venv/Scripts/python.exe`, not a global Python or a virtual
  environment copied from another checkout. Rerun the locked sync from this
  repository. A pytest pass alone does not prove the editable installation.
- **Verification fails:** inspect the first failing step and its output. Keep
  the failing command and result for diagnosis; do not suppress assertions or
  enable database smoke to make an offline run pass.

The CodeGraph CLI was unavailable on the reference workstation. The local
codebase-memory engineering index `polymarket-alpha-lab-local` was available;
that is not evidence that the original `.codegraph/` index was synchronized.

## Database Work Is Separate

Offline tests, fake database adapters, and an installed psycopg driver do not
prove real local Supabase/Postgres integration. At the reference workstation's
bootstrap, there were no listeners on ports 5432, 54321, or 54322. Docker and
Supabase CLI were absent from `PATH`; `psql` was present. The initial checkout
contained 59 files under [`supabase/migrations`](../../supabase/migrations/),
but no Supabase `config.toml` or Compose setup. This is a workstation snapshot,
not an instruction to create or start services or apply migrations.

[`.env.example`](../../.env.example) is a variable reference, not a configuration
file to import automatically. Do not copy or import it wholesale for onboarding.
Only configure the variables required for a specific later database task.

Read the [local Supabase operations guide](../supabase/local-supabase-operations.md)
and [cycle snapshot runbook](../supabase-cycle-snapshot-runbook.md) when planning
that task. Their existing commands assume an older Linux installation with a
running Supabase stack; they are not Windows bootstrap commands. Local
Supabase/Postgres remains the only durable project data store. Every raw DSN
must pass `validate_local_postgres_dsn` before a connection or persistence
adapter is constructed.

The existing real Supabase smoke test inserts, reads back, and deletes test
rows. It remains disabled by default. A later integration check needs a
confirmed existing local instance, the required schema, and an explicitly
agreed test-write and cleanup scope. Onboarding does not run that integration
check. Any later database evidence remains local paper evidence, with
`paper_only=True`, `report_only=True`, and `readonly=True` wherever those flags
exist.
