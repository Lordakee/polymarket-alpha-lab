# Project-private native PostgreSQL

This is the current database deployment path. **No Docker, Supabase service,
cloud DB, Windows database service, or shared PostgreSQL instance is required.**
The project starts its own native PostgreSQL processes, owns a separate cluster,
and supplies generated project-only credentials. A PostgreSQL process is still
required; this is application-managed server software, not an in-process engine.


A clean Windows source + PostgreSQL distribution and automatic first-start check
are now available. See **[quickstart.md](quickstart.md)** for the two-command
setup, kit checksums, and the boundary that Python/dependencies remain required.

## Layout and one-time setup

```text
runtime/postgres/        # imported native bin/, lib/, share/, runtime.json
.local/postgres/         # private cluster, config, credentials, instance marker
.local/postgres.lock     # OS lifecycle lock; not a PID ownership assertion
database/migrations.lock.json
supabase/migrations/     # historical pathname ONLY; unchanged SQL identities
```

Only source/configuration templates and the migration lock enter Git. Runtime
binaries, generated passwords and PostgreSQL cluster files are ignored. Business
records remain in PostgreSQL, not in an extra JSON/file journal. Native server
logs/configuration and the cluster's own physical files are infrastructure.

Install the existing project environment including its Postgres driver:

```powershell
uv sync --locked --extra dev --extra postgres
```

A source checkout does not include hundreds of megabytes of platform binaries.
For Windows, obtain the official PostgreSQL binary ZIP from the PostgreSQL/EDB
channel and approve its SHA256 independently before import. The importer does
not silently download or execute software. Importing a trusted extracted prefix
is also supported; it must contain `bin`, `lib`, and `share`. Do NOT point at an
existing data directory. The importer copies only the runtime, never any source
cluster, service configuration, account or credential.

```powershell
# Official binary archive; replace both arguments with the approved local file/hash.
.\.venv\Scripts\python.exe scripts/project_database.py install-runtime --archive C:\Downloads\postgresql-binaries.zip --sha256 APPROVED_SHA256

# Alternative: explicitly trusted, already extracted portable native prefix.
.\.venv\Scripts\python.exe scripts/project_database.py install-runtime --from-directory C:\Downloads\pgsql

# Use ONE import method. No PostgreSQL system installation or service registration.
.\.venv\Scripts\python.exe scripts/project_database.py init
.\.venv\Scripts\python.exe scripts/project_database.py up
.\.venv\Scripts\python.exe scripts/project_database.py status
.\.venv\Scripts\python.exe scripts/project_database.py down
```

`init` creates a new cluster, installs all 62 locked historical migrations, then
stops the server. Default port is 55432; choose `init --port N` once if necessary.
A busy port blocks; the project will not connect to whatever occupies that port.
A repeated init refuses an existing directory rather than resetting its data.
`up` is repeatable and `down` preserves the entire cluster. There is no `reset`,
`destroy`, force-kill, automatic upgrade, or arbitrary executable/SQL command.

Native prefixes for PostgreSQL majors 16, 17 and 18 are accepted only when all
five required programs agree on an exact version. Acceptance tests, not this
allowlist, determine which OS/version combinations have actually been verified;
see the PR/CI record. Changing a runtime version on an initialized project is
not an upgrade procedure. Keep a supported patched release and perform planned
backup/restore or pg_upgrade outside this initial lifecycle implementation.
The underlying platform's C/C++ runtime dependencies still apply.

Paths containing spaces are included in the native proof. Windows ancestors
must be accessible to the owning non-elevated account: PostgreSQL deliberately
drops administrator privileges. The manager does not alter ancestor ACLs or
disable that restriction; use a project directory owned by your ordinary account. Shell
metacharacters and quotes in the project path are rejected. The project path is
bound to its instance: copying/moving an initialized project is not an automatic
migration procedure. Existing external/Supabase data is NEVER adopted or copied.

## Application integration (no caller DSN)

```python
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

# prepared_request: existing CapturedResearchRequest from approved market intake.
# model_factory: explicitly configured client; no default live provider is enabled.
db = ProjectPostgres(Path(project_root))
with db.session() as research:
    result = research.run_research(request=prepared_request, model_factory=model_factory)
    # inspect(record_id=...), retry_capture(request=..., run=...), and
    # capture_outcome(...) use the same private, restricted application identity.
    diagnostics = research.evaluate().to_dict()
```

The session starts the server when necessary and stops only the instance it
started. If `up` had already started it explicitly, the session leaves it running.
An OS-held exclusive lifecycle lease prevents another process from stopping or
migrating the instance during the session. A single session may run multiple
research calls concurrently in threads. Its close waits for in-flight calls to
finish; injected model clients must supply their own bounded I/O. A crashed
application releases the OS lease but may leave PostgreSQL running; the next
explicit start/status verifies and reuses only that exact private instance.
There is no claim of perfect parent-death cleanup or automatic incomplete-job
recovery. The existing at-most-once research claim rules remain unchanged.

New managed sessions reject inherited `PG*` overrides, accept no external DSN,
and check the protected instance record on each actual research connection
before business SQL. The shared local DSN validator remains unchanged. The new
`local_postgres_dsn` import refers to the same audited validator as the historical
`supabase_local_dsn` module; there is no alternate weaker validator. Older explicit
DSN APIs and serialized `supabase` labels remain compatibility surfaces. Using
those old APIs directly does not establish project-instance binding.

The manager performs administration through the project's absolute `psql` path,
with `-X`, no prompts, sanitized PostgreSQL environment, short timeouts and SQL
on stdin. Child output is suppressed on errors. The pg_ctl launcher uses DEVNULL instead
of inherited PIPE handles, avoiding waits for its long-lived Windows descendants.
Passwords travel through private
passfiles, not command-line arguments or PGPASSWORD. Public command output contains
status/port/version/instance ID only, never a password or DSN.

## Ownership, permissions and limits

First initialization generates separate random 256-bit owner and application
passwords. Windows protects the private root with an owner/SYSTEM-only inherited
ACL; POSIX requires owner-only permissions. Symlinks and Windows reparse points
are rejected. Permissions and deterministic connection/authentication configs
are checked instead of silently repairing possibly foreign infrastructure.

PostgreSQL listens only on 127.0.0.1. Unix sockets are disabled. HBA allows only
the two project roles and the project database using SCRAM; the owner may also
connect to the administration database. Other database/user/address combinations
are rejected. The application role is not superuser and cannot create databases,
roles or schemas, read password catalogs, or mutate instance/migration metadata.
It receives SELECT/INSERT on project evidence tables, not UPDATE/DELETE/TRUNCATE.
The existing RLS-enabled assignment table keeps RLS, with exact application-only
SELECT/INSERT policies instead of BYPASSRLS. Conflicting policy definitions block.

Both disk and live server identities are checked (data directory, native cluster
system ID, project-path hash, random project instance ID and database identity).
Do not treat an obscure port, source hash, or application_name as authentication.
A native DB authenticates credentials, not the caller's source code. Another
program running as the same OS user may read these credentials; a local admin
can alter files, disable guards or inspect processes. This is a dedicated,
non-shared project instance, NOT a security sandbox against the owning user or
administrator. Stronger isolation needs a separate OS account/sandbox.

## Migrations and failure handling

The 62 existing SQLs are retained byte-for-byte under their historical pathname;
none uses Supabase auth/storage/REST services. A checked-in manifest binds the
entire ordered set and records the two existing outer transaction wrappers.
A closed native bootstrap compatibility repair fixes the invalid historical
`type(@.reason_codes)` JSONPath syntax in migration 20260622000007 to the
PostgreSQL item method `@.reason_codes.type()`. Both the exact original and
effective SQL hashes are pinned in `project_postgres/migration_compat.py`; the
original file stays unchanged. The database ledger records the EFFECTIVE native
SQL hash, not a false claim that the unmodified invalid expression was executed.
Missing-field and non-array rejection remain, with real-engine negative probes.
No other migration receives a rewrite.

Initialization strips only those explicitly declared, hash-checked wrappers,
then applies each migration and its PostgreSQL ledger receipt in ONE transaction.
Applied history must be an exact unchanged prefix; unknown, reordered, missing,
or modified migrations block. The application cannot change the ledger.

For an existing managed instance, `up` reports pending migrations and a research
session refuses to run until explicitly upgraded:

```powershell
.\.venv\Scripts\python.exe scripts/project_database.py migrate
```

Review migration changes first. Adding a migration requires updating the manifest.
A failed migration rolls back its own DDL and ledger insertion; earlier committed
migrations and project records are retained. Native instance initialization that
fails leaves its private directory for diagnosis. There is no destructive retry.
Do not delete a cluster to make a check green. Backup/restore commands, automatic
major upgrades, existing-instance import, OS services and cloud targets are NOT
implemented. A local data directory is not a backup; retain a separately verified
PostgreSQL backup/recovery procedure before real long-term data collection.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_project_postgres.py
.\.venv\Scripts\python.exe scripts/verify_local.py --full
```

The native integration test is separately opt-in and writes only to a new
temporary project (an explicitly protected unique RUNNER_TEMP child on Windows,
not pytest's potentially administrator-only ancestor). Its explicit prefix is a trusted binary source, not the database
being tested. It exercises initialization of all migrations, private authentication,
limited privileges, concurrent research capture, persisted readback after restart,
instance mismatch rejection, port conflicts, config tampering and DDL rollback.
It does not touch a user's installed DB or call a live model. The GitHub native
workflow uses runner-provided Windows binaries solely as this source and never
starts its installed Windows service. Default offline tests do not start servers.

Official deployment references:
- https://www.postgresql.org/download/windows/
- https://www.postgresql.org/docs/16/app-initdb.html
- https://www.postgresql.org/docs/16/app-pg-ctl.html
- https://www.postgresql.org/docs/16/auth-pg-hba-conf.html
- https://www.postgresql.org/docs/16/libpq-pgpass.html
