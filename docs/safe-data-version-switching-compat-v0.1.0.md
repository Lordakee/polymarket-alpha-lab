# Safe data version switching: offline compatibility evidence for the pinned v0.1.0 pair

## 1. Status and evidence boundary

> Status: OFFLINE EVIDENCE ONLY (evidence class 2 of the section 48 design).
> This document records a read-only comparison of two pinned revisions. It is
> not a switch implementation, not an installation acceptance, and it does not
> close WP-06 or G6.

This is the second evidence class listed under "Evidence required for later
acceptance" in [the section 48 design](safe-data-version-switching-design.md):
offline compatibility evidence for the exact release pair, dependencies,
catalog and schema assumptions, and command/root selection. The later classes
(isolated native Windows evidence, operator-reported evidence, and
owner-authorized installation acceptance) remain outstanding.

Nothing in this node implements or executes a version switch, installs or
extracts any kit, starts or probes PostgreSQL, reads credentials, `.local`
state, a user database, or any private backup, or runs any program shipped in
either distribution. Phase 1 boundaries are retained exactly: `paper_only=True`,
`report_only=True`, and `readonly=True` where those flags exist.

The OLD kit ZIP was finally verified in this node. Every OLD-source finding in
the section 48 planning record that was tagged as describing the pinned Git
tree has now been corroborated against the verified ZIP contents (see
sections 3 to 8); no drift was found.

## 2. Pinned inputs and provenance

| Input | Pinned identity |
|---|---|
| Implementation repository / destination | `Lordakee/polymarket-alpha-lab`, remote `origin`, branch `main` |
| OLD release repository | `wmqfl861/polymarket-alpha-lab` |
| OLD release | `v0.1.0-native-preview.1`, release ID `387857161`, published `2026-09-13T10:02:19Z` |
| OLD tag commit | `2b20002c83ee33acb95fb2ca3de841f3e883ebbf` |
| OLD source tree | `d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4` |
| Declared bundle `source_commit` | `8ffb0e5f9d0874697fbc95dba5155d69b2903812`; the GitHub commit API independently confirmed the same OLD tree |
| NEW source / implementation base | `f9b2488303370e374a53b3b34094071bc8b8ef9d` |
| NEW tree | `a3120df9aefcf57acbe7771a453ae7e15461c393` |
| OLD ZIP asset | `polymarket-windows-native.zip`, asset ID `560975395` |
| Declared ZIP size | `66,596,016` bytes |
| Declared ZIP SHA256 | `c32647030e8d5cb2bab1ea3d6c93c6c253f80752390ea7240741f25b4022b705` |
| Checksum sidecar | Asset ID `560975028`, `96` bytes |
| Sidecar's own SHA256 | `26e81fafde01b119b02b53ca6e244cea13bb19396f93259c6e7a490a86a94b19` |

Declared versus observed:

- ZIP bytes: declared `66,596,016`, observed `66,596,016`. Match.
- ZIP SHA256: declared (release metadata and sidecar content)
  `c32647030e8d5cb2bab1ea3d6c93c6c253f80752390ea7240741f25b4022b705`,
  observed identical. Match. The 96-byte sidecar contains exactly
  `c32647030e8d5cb2bab1ea3d6c93c6c253f80752390ea7240741f25b4022b705  polymarket-windows-native.zip`.
- Bundle `source_commit` `8ffb0e5f...` differs from the tag commit
  `2b20002c...`. This is acceptable only because the GitHub commit API
  independently confirmed that the bundle commit resolves to the same OLD
  source tree `d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4` pinned by the tag
  tree, and because every shipped text member was byte-compared against that
  tree (section 3).
- The release reports `immutable=false`. The asset IDs, checksums, tag commit,
  and source tree above are pinned together; the tag name alone is not trusted.

Download-attempt history (both attempts preserved, neither discarded):

1. Planning-time first attempt: `gh api .../releases/assets/560975395` with
   `Accept: application/octet-stream`, host Python capturing stdout as bytes
   with a 150-second timeout. The attempt **timed out at 150 seconds**; no
   usable ZIP bytes were obtained, and the ZIP's contents and outer checksum
   remained unverified at that point.
2. Later attempt (coordinator-run, recorded here for provenance): the same
   fixed asset ID via the same `gh api` byte path **succeeded after 21 minutes
   21 seconds** (21m21s wall clock). The resulting file is the
   66,596,016-byte ZIP whose observed SHA256 is recorded above.

The successful attempt's 21m21s duration is recorded as-is; no retry-limit or
timeout policy is derived from it. A checksum sidecar does not verify a missing
ZIP, so no ZIP claim below relies on the sidecar alone.

## 3. Offline archive inspection

All inspection was performed with the Python standard library `zipfile` module
reading the archive in memory. Nothing was extracted to disk, no member was
executed, and no program inside the nested engine archive was opened as
anything other than hashed/compared data.

Outer archive layout:

- `2,870` members total: `2,869` manifest inventory records plus
  `PROJECT-BUNDLE.json` itself (the manifest is not listed in its own
  inventory).
- Every member is under the single top prefix `polymarket-alpha-lab/`; zero
  members outside it, zero directory entries, zero duplicate names, zero
  absolute/traversal/backslash/colon path forms.
- Declared (header) sizes match actual read sizes for every member. Sum of
  declared uncompressed sizes is `143,286,252` bytes.

`PROJECT-BUNDLE.json` (415,976 bytes) has exactly the seven expected keys:
`files`, `format`, `postgres_version`, `python_requires`, `source_commit`,
`source_tree`, `target`, with values:

- `format`: `project-native-distribution-v1` (matches the NEW
  `PP/distribution.py` constant, which is the same contract).
- `source_commit`: `8ffb0e5f9d0874697fbc95dba5155d69b2903812` (declared).
- `source_tree`: `d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4` (matches the
  independently pinned OLD tree).
- `target`: `windows-x86_64`.
- `postgres_version`: `17.11` (engine seed declaration; see section 4 limits).
- `python_requires`: `>=3.11`.
- `files`: `2,869` records (name to SHA256). Composition: `2,796` Python
  modules under `src/polymarket_alpha_lab/`, `63` SQL files under
  `supabase/migrations/`, the 9 `FIXED` files (`pyproject.toml`, `uv.lock`,
  `.gitignore`, `.gitattributes`, `database/README.md`,
  `database/quickstart.md`, `database/migrations.lock.json`,
  `scripts/project_database.py`, `scripts/start_project.py`), and the single
  engine entry `database/postgres-runtime.zip`. No optional public
  entrypoints are shipped; the six managed entry scripts of section 6 are
  absent from this inventory, as expected for a kit built before they existed.

Inventory verification: **every one of the 2,869 listed member hashes was
verified in memory; 2,869 matched, 0 mismatched, 0 unreadable.** No ZIP member
exists that is not either inventory-listed or the manifest itself, so there
were **no unexpected private-data members to reject** and none were opened
beyond hashing and byte comparison.

Engine seed, kept as data: `database/postgres-runtime.zip` is `50,345,366`
bytes with SHA256
`6c156231aa20c58b0164e86c0b6b3a39c2d7baaf00e436f6d00516e69702c5d0`,
matching its manifest entry. Its own member list (read in memory from the
bytes, never extracted, never executed) contains `1,753` members, all under
the `pgsql/` prefix, with zero duplicates and zero unsafe path forms. One
hundred sixty members carry executable/archive suffixes (`.exe`, `.dll` and
similar), which is the expected shape of a PostgreSQL runtime tree; they were
counted only. The engine's declared `17.11` was not confirmed by running any
binary.

Byte comparison against the pinned OLD tree: all `2,868` non-engine members
were compared byte-for-byte against `git cat-file blob` output for the same
paths in tree `d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4`. **All 2,868 are
byte-identical; 0 drift; 0 missing.** Conversely, every path in the OLD tree
that the distribution's `selected_source` rule would ship is present in the
kit. The shipped kit is therefore the pinned OLD tree plus the manifest and
the nested engine archive, exactly as declared.

## 4. Python, dependencies, and runtime

- Both `pyproject.toml` files declare `requires-python = ">=3.11"`; the
  manifest `python_requires` is also `>=3.11`. Neither tree contains a
  `.python-version` file.
- Dependency resolution (locked declarations, not an installed environment):
  both `uv.lock` files resolve `psycopg` `3.3.4` and `tzdata` `2026.3`. The
  OLD kit has no direct `tzdata` entry in `pyproject.toml`; its prescribed
  Windows installation (`uv sync --locked --extra postgres` in both OLD and
  NEW `database/quickstart.md`) already resolves tzdata transitively through
  psycopg. NEW adds the direct dependency `tzdata>=2026.2` and the NEW-only
  module `APP/research_crypto_observation.py::_new_york`, which imports only
  the installed tzdata package and loads `America/New_York` from package
  resources rather than host `TZPATH` or environment variables. Pinned
  Windows resolution is therefore compatible for the locked set.
- **Limit**: no actual `.venv` or installed package state was inspected on
  either side. Compatibility above is a statement about the two lockfiles and
  manifests, not about any observed environment.
- Runtime support surface: `PP/runtime.py` is **byte-identical** between OLD
  and NEW, with `SUPPORTED_MAJORS = (16, 17, 18)`; the declared `17.11` is a
  supported major, and the OLD build path itself required PostgreSQL major 17.
  The exact runtime instance checks in `PP/server.py` and the version
  validation in `PP/distribution.py` accept the same 17.x shape.
  **Limit**: no engine binary was executed, so the actual executable version,
  the engine inventory on disk, and any installed instance binding remain
  unverified (section 10).

## 5. Migration catalog and effective digests

OLD ships `database/migrations.lock.json` with **63** entries; NEW at the
pinned base has **68**. Verified against both sides:

- The first 63 entries are unchanged in NEW: identical names, identical order,
  identical raw SHA256 values in the lock, identical raw SQL bytes, and
  identical `transaction_wrapper` flags. `PP/sql.py`,
  `PP/migration_compat.py`, and `PP/files.py` are byte-identical between OLD
  and NEW, so the catalog loader, validation, and digest rules are the same
  code.
- The five appended migrations (positions 64-68), with raw byte counts, raw
  hashes, effective hashes, and their concrete schema consumers:

| Ordinal | Migration under `supabase/migrations/` | Raw bytes | Raw SHA256 | Effective SHA256 | NEW consumer under `APP/` |
|---:|---|---:|---|---|---|
| 64 | `20260914000000_research_dispatch_batches.sql` | 4,576 | `afd50399909967d6b22633ad763f9e96c10fd2c1d360001f38b8c90e6c6c9c67` | same as raw | `research_dispatch_store.py::enqueue_research_batch_with_psycopg` |
| 65 | `20260915000000_research_dispatch_turns.sql` | 7,775 | `e2f377662c43f1894818d3064e91ff192966c3521d82bd305c8fd6fed117e5f0` | same as raw | `research_dispatch_rotation_store.py::_reserve` |
| 66 | `20260915010000_research_model_budgets.sql` | 7,940 | `1413e9479daf69e53bcadaed336d8ee28ff9e486b7319c7ed53a0b63c14f467e` | same as raw | `research_model_budget_store.py::{create_model_budget_with_psycopg,_reserve_call}` |
| 67 | `20260915020000_research_paper_simulations.sql` | 5,848 | `60ba1277e25caef5ba75f44f8c3974cee63a964f1c9b9c14ff72d68cf5c75d17` | same as raw | `research_paper_capture.py::capture_research_paper_with_psycopg`; `research_paper_settlement.py` |
| 68 | `20260919000000_research_uncapped_audit.sql` | 10,811 | `fabfe9b925de658ccd67b95b3de1fbbf372a21a7f9631fd0b5f7e2f161d2c06d` | same as raw | `research_uncapped_audit_store.py::{create_uncapped_authorization_with_psycopg,_begin_call,_finish_call}` |

All five store-level consumer functions exist in NEW at the pinned base, and
`PP/research.py::ProjectResearchSession` exposes the corresponding wrapper
methods (`enqueue_research_batch`, `create_model_budget`,
`create_uncapped_authorization`, and the paper-capture/settlement and rotation
paths). These are method-level missing-schema hazards when the underlying
tables do not exist; they do not prove that merely importing NEW must fail.

Digest sequence (exact order, both versions):

1. Validate the raw SQL SHA256 against `database/migrations.lock.json`.
2. Apply `PP/migration_compat.py::native_migration_bytes` to the raw bytes.
3. Hash the effective bytes; this effective digest is the ledger identity in
   `project_private.migrations` and the backup catalog identity.
4. Only afterwards, strip declared outer `BEGIN;`/`COMMIT;` wrappers
   (`transaction_wrapper=true`) for execution.

The sole raw/effective difference in both catalogs remains
`20260622000007_paper_project_screening_rank_stability_reports.sql` (the
closed JSONPath repair). `transaction_wrapper=true` appears only at positions
61 and 62, and wrapper removal happens after ledger digest binding, so those
entries' ledger digests are unchanged from their SQL bytes as locked.

Effective catalog fingerprints (canonical JSON of `[name, effective digest]`
pairs, hashed exactly as `PP/backup_format.py::fingerprint` computes the
backup `migrations_sha256`):

```text
OLD 63: 3e8c813dcb7ce2389f11aa7aebba03819392f014e1208910c75d70bf709ccee5
NEW 68: 8b984158a7fda85b1f8a58583d0d20ac86cc9abae6acdf713bd7b5946a8fdd71
```

Both were recomputed in this node with the project's own
`native_migration_bytes` logic over the verified OLD kit bytes and the pinned
NEW blobs. The NEW first-63 prefix fingerprint equals the OLD fingerprint
exactly, confirming the change is append-only.

## 6. Command, source, and root selection

- `scripts/project_database.py` drift (OLD 304 bytes, NEW 544 bytes): NEW
  resolves `ROOT = Path(__file__).resolve().parents[1]`, inserts
  `ROOT / 'src'` at the front of `sys.path`, and exits with
  `project_entry_source_missing` if the adjacent
  `src/polymarket_alpha_lab/__init__.py` is absent. OLD imported
  `polymarket_alpha_lab` from the invoking environment, so an unrelated
  editable installation could satisfy it. NEW always uses its own adjacent
  source/kit.
- `--root` behavior is unchanged: `project_database.py` still passes its own
  parent directory as `--root` by default, and `--root` continues to select
  the data, runtime, configuration, and migration catalog location. Source
  selection and root selection remain independent.
- `scripts/start_project.py` is **byte-identical** between OLD and NEW; it
  remains tied to its own root and has no `--root` flag.
- The six NEW managed entry scripts
  (`scripts/manage_research_tasks.py`, `scripts/review_resolution_queue.py`,
  `scripts/list_project_research.py`, `scripts/inspect_project_research.py`,
  `scripts/inspect_project_resolution.py`,
  `scripts/evaluate_project_research.py`) all exist at the NEW pinned base and
  are all absent from the OLD kit inventory (the OLD kit ships only
  `scripts/project_database.py` and `scripts/start_project.py` from
  `scripts/`). Their intended cross-version invocation shape is
  `NEW_PYTHON -I NEW_SOURCE/scripts/<script> --root OLD_PHYSICAL_ROOT`;
  this node enumerates that shape only and **does not execute it**.
- `database/quickstart.md` drift: both versions prescribe
  `uv sync --locked --extra postgres` and forbid overlay extraction; NEW adds
  the source-selection/second-extraction verification workflow sections. The
  preservation wording ("do not extract over an existing project as an upgrade
  mechanism") is present in both.

## 7. Managed-session admission

- In NEW, `PP/server.py::ProjectPostgres.session` calls
  `_verify_session_bundles()` at entry, before any private lifecycle access.
  It checks both the source root (`parents[3]` of `server.py`) and the data
  root (`self.layout.root`): if either `PROJECT-BUNDLE.json` or
  `database/postgres-runtime.zip` exists at a root, `verify_distribution` runs
  for that root. A source checkout with neither marker keeps its existing
  path.
- **Drift**: OLD `PP/server.py` has no `_verify_session_bundles`; the
  session-bundle integrity gate is NEW behavior. This is a compatibility
  difference in admission mechanics, not in schema handling.
- `verify_distribution` checks kit integrity: manifest shape (the same seven
  keys, `format=project-native-distribution-v1`, `target=windows-x86_64`,
  `python_requires>=3.11`, `postgres_version` matching `17.x`), the
  `FIXED`-plus-engine required set, per-file SHA256s, and that no extra or
  unlisted selected file exists. The OLD manifest values verified in section
  3 satisfy the NEW required-file contract, and the NEW optional public
  entrypoints are exactly that, optional, so an intact OLD extraction remains
  verifiable by NEW code. This is source-level analysis corroborated by the
  existing entry-root and session-bundle tests as specifications; those tests
  were read, not newly executed.
- Adding a SQL file or editing the lock inside the immutable OLD kit breaks
  its inventory (any unlisted selected file or changed hash fails with
  `project_bundle_invalid_or_changed`); editing the kit is invalid anyway.
- Admission is integrity only. It does not prove cross-version schema
  coverage: with NEW source against a data root whose ledger has 63 applied
  entries, the pending check in `session` still refuses entry
  (`project_postgres_migrations_pending`) because five migrations are
  pending, while the feature families of section 5 would need those tables.

## 8. Cold-backup format and catalog compatibility

- `PP/backup_format.py` (v1 format, `fingerprint`, `parse_manifest`,
  `inspect_archive`) and `PP/backup_zip.py::validate_zip_layout` are
  **byte-identical** between OLD and NEW. The v1 archive format and parser
  are unchanged, so OLD-produced backups remain readable structures for NEW
  tooling.
- Default binding (both versions): `create/verify/restore` compare
  `_migrations(layout)`, the effective-catalog fingerprint of the current
  data root, against the backup's recorded `migrations_sha256`. With OLD 63
  versus NEW 68 this fails (`project_postgres_backup_migrations_mismatch`)
  by design; default equality is intentionally strict.
- Explicit catalog extension (NEW only; `allow_catalog_extension` opt-in,
  which OLD `PP/backup.py` lacks): after the opt-in flag is validated,
  `_catalog_binding` matches the backup fingerprint against **nonempty exact
  prefixes** of the fully validated current effective catalog, longest first.
  The OLD 63-entry fingerprint is an exact prefix of the NEW 68-entry
  catalog (section 5), so an OLD backup can be verified/considered bound
  under the explicit extension, reporting `match=append_only_extension`,
  backup/current entry counts, `additional_entries=5`, and
  `database_ledger_checked=false`. Root/platform identity
  (`root_sha256`, `platform`), runtime version and runtime fingerprint,
  archive SHA256, and the `trusted_backup` opt-in checks are all still
  enforced; extension does not relax them.
- The extension applies **no SQL** and does not inspect the snapshot's
  applied ledger; migration remains a separate, explicitly authorized step.
  Restore still requires an absent target and is not an upgrade or rollback
  tool.
- `database/README.md` changed between OLD and NEW (documentation drift
  covering the extension); no executable behavior depends on it.

## 9. Compatibility matrix

In this table `PP/` means `src/polymarket_alpha_lab/project_postgres/` and
`APP/` means `src/polymarket_alpha_lab/`.

| Surface | Compared basis | Finding for the pinned OLD -> NEW pair |
|---|---|---|
| Runtime | `PP/runtime.py::{SUPPORTED_MAJORS,runtime_version,verify_runtime}`; instance checks in `PP/server.py`; version validation in `PP/distribution.py` | Supported. `PP/runtime.py` byte-identical; `SUPPORTED_MAJORS=(16,17,18)`; declared `17.11` supported. Actual executable version, engine inventory, installed instance binding unverified (nothing executed). |
| Dependencies | `pyproject.toml`, `uv.lock`, OLD/NEW `database/quickstart.md`, manifest `python_requires`; `APP/research_crypto_observation.py::_new_york` | Compatible for the locked resolution: Python `>=3.11` both; psycopg `3.3.4` and tzdata `2026.3` in both locks; NEW makes `tzdata>=2026.2` direct. No actual installed `.venv` inspected. |
| Catalog and schema | `database/migrations.lock.json`; `supabase/migrations/*.sql`; `PP/sql.py`; `PP/migration_compat.py`; `PP/files.py`; `PP/server.py::{_pending,_migrate,session}` | Append-only: 63-entry prefix identical in names, order, raw hashes, effective hashes, and SQL bytes; five appended entries verified with digests. Effective fingerprints OLD 63 `3e8c813d...` / NEW 68 `8b984158...`. Complete NEW feature surface is incompatible with an unchanged 63-migration schema (missing tables for five feature families). |
| Command and root selection | `scripts/project_database.py`; `scripts/start_project.py`; `PP/cli.py::main`; quickstart source/root and preservation sections | `--root` semantics unchanged (data/runtime/configuration/catalog). NEW `project_database.py` pins its adjacent `src` and fails if missing; OLD could import from the invoking environment. `start_project.py` unchanged, still root-tied, no `--root`. Six managed entry scripts are NEW-only; not executed here. |
| Distribution format | `PP/distribution.py::{FORMAT,MANIFEST,ENGINE,FIXED,PUBLIC_ENTRYPOINTS,selected_source,verify_distribution}` | Compatible. Same format `project-native-distribution-v1`, same required-file contract; the verified OLD manifest satisfies the NEW required set; added public entrypoints are optional for old kits. Verified against the actual OLD ZIP in this node. |
| Managed admission | `PP/server.py::_verify_session_bundles`,`session`,`_pending`; `PP/files.py::Layout` | Integrity admission NEW-only at session entry (OLD lacks it); triggers on `PROJECT-BUNDLE.json` or the engine archive at source/data roots. Checks integrity, not cross-version schema coverage. Modifying the immutable OLD kit (adding SQL, changing the lock) breaks its inventory. |
| Backup binding | `PP/backup_format.py`; `PP/backup_zip.py`; `PP/backup.py::{_migrations,_catalog_binding,_catalog_opt_in,_bindings,create_cold_backup,verify_cold_backup,restore_cold_backup}`; `database/README.md` | Format/parser unchanged; OLD backups structurally readable. Default binding requires exact catalog equality (OLD 63 vs NEW 68 fails intentionally). Explicit extension (NEW only) accepts only an unchanged, nonempty effective-digest prefix, preserving root/platform/runtime/checksum/trust checks; applies no SQL; does not inspect the snapshot ledger (`database_ledger_checked=false`). |
| Rollback | Source selection versus ledger/catalog state | Selecting OLD source again does not undo applied schema; see scenario rows below for the 68-ledger state. |

The seven scenarios, classified exactly as planned:

| Hypothetical state | Classification | Meaning |
|---|---|---|
| OLD catalog 63 / ledger 63, running NEW source | **Incompatible for complete NEW functionality** | The pending check can be empty while the five NEW schema-dependent feature families remain unavailable. |
| NEW catalog 68 / ledger 63 | **Requires-migration-step** | Five migrations are pending; managed session admission refuses entry. Catalog adoption and migration require separate authorization. |
| NEW catalog 68 / ledger 68 | **Catalog condition satisfied only** | Other admission checks, installation compatibility, and feature behavior remain unproven. |
| OLD catalog 63 / ledger 68 | **Incompatible** | `project_postgres_migration_history_conflict`; selecting an old catalog does not undo schema changes. |
| OLD source with a valid 68-entry catalog | **Rollback compatibility unproven** | The unchanged loader could theoretically read it. Do not claim all OLD-source use must fail. Editing the retained immutable kit to supply that catalog is invalid. |
| OLD backup catalog versus NEW catalog, default mode | **Incompatible catalog binding** | Default equality is intentionally strict. |
| OLD backup catalog versus NEW catalog, explicit extension | **Compatible prefix contract; later migration still required where applicable** | No SQL is applied and `database_ledger_checked=false`. |

There is no sanctioned in-place catalog-adoption procedure for the immutable
OLD root delivered by this node. The negative compatibility findings above
are completed class 2 evidence; they do not require changing production code
and they do not authorize any operation.

## 10. Unknowns and later evidence

Preserved unknowns, none of which this node resolves:

- Actual installed Python packages (no `.venv` on either side was inspected;
  lockfile resolution is not an environment observation).
- The applied ledger of the real installation (which entries are actually
  recorded in `project_private.migrations` on the operator's data root).
- Runtime inventory on disk and the actual engine executable version
  (nothing was executed or probed; `17.11` remains a declaration).
- Physical-root identity (that the operator's `--root` is the original
  physical root that produced any given backup).
- Backup usability against real data volumes and restore behavior on the
  operator's machine.
- Windows lifecycle and ownership behavior (start/stop/restart, file locks)
  under source switching.
- Rollback behavior after schema changes (the 68-ledger state), which stays
  unproven by design in this node.
- Isolated native Windows evidence, operator acceptance, and
  owner-authorized installation work are separate later evidence classes
  (classes 3 to 5 of the section 48 design) and remain outstanding.

## 11. Bounded conclusion and reproducibility references

Bounded conclusion, for the pinned pair only:

1. The OLD release artifact is exactly what it declared: 66,596,016 bytes,
   SHA256 `c3264703...`, 2,869 verified inventory records, shipped source
   byte-identical to tree `d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4`,
   engine seed archived as data.
2. PostgreSQL 17 remains supported by NEW; the runtime support surface is
   unchanged code.
3. The migration catalog change is exactly append-only: an unchanged
   63-entry prefix plus five ordered additions; effective fingerprints
   OLD 63 `3e8c813dcb7ce2389f11aa7aebba03819392f014e1208910c75d70bf709ccee5`
   and NEW 68 `8b984158a7fda85b1f8a58583d0d20ac86cc9abae6acdf713bd7b5946a8fdd71`.
4. The complete NEW feature surface is **incompatible** with an unchanged
   OLD 63-migration schema; catalog adoption, database migration, and
   rollback acceptance remain separate, explicitly authorized work.
5. Default cold-backup binding across the pair is incompatible by design;
   the explicit extension path exists in NEW only and verifies an exact
   effective-digest prefix without applying SQL.

This evidence does not implement or authorize a version switch, does not
close WP-06 or G6, and does not substitute for isolated Windows, operator, or
owner-authorized acceptance evidence.

Reproducibility references (immutable where the host allows):

- OLD release: https://github.com/wmqfl861/polymarket-alpha-lab/releases/tag/v0.1.0-native-preview.1
  (release ID `387857161`; `immutable=false`, hence the pinned checksums above).
- OLD ZIP asset ID `560975395`; sidecar asset ID `560975028`.
- OLD tag commit: https://github.com/wmqfl861/polymarket-alpha-lab/commit/2b20002c83ee33acb95fb2ca3de841f3e883ebbf
- OLD bundle source commit: https://github.com/wmqfl861/polymarket-alpha-lab/commit/8ffb0e5f9d0874697fbc95dba5155d69b2903812
- OLD pinned tree: https://github.com/wmqfl861/polymarket-alpha-lab/tree/d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4
- NEW implementation base: commit `f9b2488303370e374a53b3b34094071bc8b8ef9d`,
  tree `a3120df9aefcf57acbe7771a453ae7e15461c393` in
  `Lordakee/polymarket-alpha-lab` (delivery commit recorded in section 51 of
  `DELIVERY_PLAN.md`, not self-referenced here).

Exact read-only inspection commands used (host Python from the repository
virtual environment; nothing below writes inside the repository or extracts
the archive):

```text
sha256sum old-kit.zip                      # outer hash: c32647030e8d5cb2bab1ea3d6c93c6c253f80752390ea7240741f25b4022b705
python -c "import zipfile; ..."            # in-memory member list, manifest read,
                                           # per-member sha256 verification, nested
                                           # engine member count; zipfile only
git cat-file blob d6f6750b1068a3c75ab6249d5ca4f1ef7e010ee4:<path>
                                           # per-path byte comparison, no checkout
git cat-file blob HEAD:<path>              # NEW-side pinned-base blobs
```

The inspection and verification scripts are preserved uncommitted outside the
repository under the WP-06 working artifacts directory
(`.agent-artifacts/polymarket-alpha-lab/wp06-version-compat/`, files
`f1_inspect_zip.py`, `f1_compare_tree.py`, `f1_verify_claims.py`) so the
numbers above can be re-derived independently.
