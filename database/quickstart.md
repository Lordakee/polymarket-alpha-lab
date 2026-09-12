# Native Windows project kit

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
