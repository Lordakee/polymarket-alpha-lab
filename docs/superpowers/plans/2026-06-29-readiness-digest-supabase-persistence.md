# Readiness Digest Supabase Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan one task at a time. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional local Supabase/Postgres persistence for `paper-autonomous-readiness-digest` reports so readiness digest history can be reviewed later without adding live trading or exchange mutation.

**Architecture:** Keep digest generation pure and unchanged. Add a row codec, DB-API store, psycopg adapter, and env-only Supabase config matching the existing readiness-gate persistence pattern. Wire CLI persistence only behind an explicit `--persist` flag after the digest report has been built.

**Tech Stack:** Python dataclasses, existing `json_recovery.from_jsonable`, DB-API, optional `psycopg`, local Supabase/Postgres via environment variables, pytest.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, JSONL durable stores, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstractions, or file-backed durable caches.
- Phase 1 boundary remains binding: paper-only/report-only/read-only report generation only.
- Do not add live trading, auth, private keys, wallets, account access, order construction/signing/submission/cancel/replacement, exchange mutation, or strategy/action mutation.
- The default `paper-autonomous-readiness-digest` command remains no-write unless `--persist` is explicitly passed.
- DB DSN and table selection stay env-only. Do not add CLI DSN/table/file flags.
- Local Postgres/Supabase DSNs must be validated before connecting.
- Redact DSNs, hosts, table names, payloads, market details, reason codes, account/wallet/order/auth/private-key-like fields, and report hashes in CLI errors.
- Use TDD: write failing tests before production code.
- Subagents may write code only in their assigned file sets and must not revert or overwrite other workers' changes.

---

### Task 1: Digest DB Row Codec

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_readiness_digest_db_row.py`
- Test: `tests/test_paper_autonomous_readiness_digest_db_row.py`

**Interfaces:**
- Consumes: `PaperAutonomousReadinessDigestReport`, `DIGEST_STATUSES`, `json_recovery.from_jsonable`.
- Produces:
  - `PaperAutonomousReadinessDigestDbRow`
  - `paper_autonomous_readiness_digest_report_to_db_row(report: PaperAutonomousReadinessDigestReport) -> PaperAutonomousReadinessDigestDbRow`
  - `paper_autonomous_readiness_digest_report_from_db_row(row: PaperAutonomousReadinessDigestDbRow) -> PaperAutonomousReadinessDigestReport`
  - aliases `to_db_row`, `from_db_row`, `paper_autonomous_readiness_digest_to_db_row`, `paper_autonomous_readiness_digest_from_db_row`

- [ ] **Step 1: Write failing row codec tests**

Create `tests/test_paper_autonomous_readiness_digest_db_row.py` with a canonical digest report fixture:

```python
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timezone, timedelta
import hashlib
import json
import re

import pytest

from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
    PaperAutonomousReadinessDigestEvidence,
    PaperAutonomousReadinessDigestReasonCodeCount,
    PaperAutonomousReadinessDigestReport,
)

GENERATED_AT = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_GENERATED_AT = datetime(2026, 6, 29, 8, 0, tzinfo=SOURCE_TZ)
CONFIG_VERSION = "paper-autonomous-readiness-digest-test-v0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _codec_module():
    import polymarket_alpha_lab.paper_autonomous_readiness_digest_db_row as codec

    return codec


def _evidence(
    source_name: str,
    status: str,
    *,
    required: bool,
) -> PaperAutonomousReadinessDigestEvidence:
    return PaperAutonomousReadinessDigestEvidence(
        source_name=source_name,
        status=status,
        recommended_next_step=f"review_{source_name}_{status}",
        generated_at=SOURCE_GENERATED_AT,
        config_version=f"{source_name}-config-v0",
        reason_codes=(f"{source_name}_{status}",),
        required=required,
    )


def _report(
    *,
    config_version: str = CONFIG_VERSION,
    digest_status: str = "watch",
    recommended_next_review_action: str = (
        "review_watch_paper_autonomous_readiness_evidence"
    ),
    evidence: tuple[PaperAutonomousReadinessDigestEvidence, ...] | None = None,
    reason_codes: tuple[str, ...] = (
        "readiness_gate_pass",
        "screening_watch",
    ),
) -> PaperAutonomousReadinessDigestReport:
    if evidence is None:
        evidence = (
            _evidence("readiness_gate", "pass", required=True),
            _evidence("screening", "watch", required=False),
        )
    return PaperAutonomousReadinessDigestReport(
        generated_at=GENERATED_AT,
        config_version=config_version,
        digest_status=digest_status,
        recommended_next_review_action=recommended_next_review_action,
        evidence=evidence,
        source_config_versions=tuple(
            (row.source_name, row.config_version) for row in evidence
        ),
        reason_code_counts=tuple(
            PaperAutonomousReadinessDigestReasonCodeCount(reason_code, 1)
            for reason_code in reason_codes
        ),
        reason_codes=reason_codes,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("digest DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)
```

Add tests covering:

```python
def test_digest_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousReadinessDigestDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.digest_status == "watch"
    assert row.recommended_next_review_action == (
        "review_watch_paper_autonomous_readiness_evidence"
    )
    assert row.evidence_json == [
        {
            "source_name": "readiness_gate",
            "status": "pass",
            "recommended_next_step": "review_readiness_gate_pass",
            "generated_at": "2026-06-29T12:00:00+00:00",
            "config_version": "readiness_gate-config-v0",
            "reason_codes": ["readiness_gate_pass"],
            "required": True,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "source_name": "screening",
            "status": "watch",
            "recommended_next_step": "review_screening_watch",
            "generated_at": "2026-06-29T12:00:00+00:00",
            "config_version": "screening-config-v0",
            "reason_codes": ["screening_watch"],
            "required": False,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.source_config_versions_json == [
        ["readiness_gate", "readiness_gate-config-v0"],
        ["screening", "screening-config-v0"],
    ]
    assert row.reason_code_counts_json == [
        {
            "reason_code": "readiness_gate_pass",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "screening_watch",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.reason_codes_json == ["readiness_gate_pass", "screening_watch"]
    assert row.payload_json["evidence"] == row.evidence_json
    assert row.payload_json["source_config_versions"] == row.source_config_versions_json
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.evidence_json)
    _assert_no_floats(row.source_config_versions_json)
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_readiness_digest_report_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_digest_report_from_db_row(row) == report
    assert codec.paper_autonomous_readiness_digest_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_digest_from_db_row(row) == report
```

Also add tests matching the readiness-gate codec style for deterministic hashing, frozen row, wrong report/row type rejection, false top-level flags, false nested evidence flags, corrupted stored payload flags, hash mismatch, materialized field mismatch, recursive JSON float rejection, and invalid row shapes. Include `pass`, `watch`, and `blocked` digest fixtures that use `NEXT_REVIEW_ACTION_BY_STATUS[digest_status]` so persistence tests cover every source-of-truth action string.

- [ ] **Step 2: Run RED**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_db_row.py -q
```

Expected: fail because `polymarket_alpha_lab.paper_autonomous_readiness_digest_db_row` does not exist.

- [ ] **Step 3: Implement codec**

Create `src/polymarket_alpha_lab/paper_autonomous_readiness_digest_db_row.py` using the existing `paper_autonomous_readiness_gate_db_row.py` structure with digest-specific fields:

```python
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "digest_status",
    "recommended_next_review_action",
    "evidence_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)
```

The row dataclass fields are `report_sha256`, `generated_at`, `config_version`, `digest_status`, `recommended_next_review_action`, `evidence_json`, `source_config_versions_json`, `reason_code_counts_json`, `reason_codes_json`, `payload_json`, and hard flags. Use `_json_ready(asdict(report))`, reject floats, hash canonical `payload_json`, and reconstruct with `from_jsonable(PaperAutonomousReadinessDigestReport, row.payload_json)`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_db_row.py -q
```

Expected: pass.

---

### Task 2: Digest DB-API Store

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_readiness_digest_store.py`
- Test: `tests/test_paper_autonomous_readiness_digest_store.py`

**Interfaces:**
- Consumes Task 1 row codec.
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_REPORTS_TABLE = "paper_autonomous_readiness_digest_reports"`
  - `PaperAutonomousReadinessDigestInsertResult`
  - `insert_paper_autonomous_readiness_digest_report(connection, report, *, table_name=...) -> PaperAutonomousReadinessDigestDbRow`
  - `insert_paper_autonomous_readiness_digest_report_with_result(connection, report, *, table_name=...) -> PaperAutonomousReadinessDigestInsertResult`
  - `load_paper_autonomous_readiness_digest_reports(connection, *, config_version=None, digest_status=None, limit=None, table_name=...) -> tuple[PaperAutonomousReadinessDigestReport, ...]`

- [ ] **Step 1: Write failing store tests**

Create tests mirroring `tests/test_paper_autonomous_readiness_gate_store.py` with `SELECT_COLUMNS`:

```python
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "digest_status",
    "recommended_next_review_action",
    "evidence_json",
    "source_config_versions_json",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
```

Use fake cursor/connection classes with `execute`, `fetchall`, `rowcount`, `close`, `commit_count`, and `rollback_count`. Cover:

- parameterized insert into `paper_autonomous_readiness_digest_reports`
- `ON CONFLICT (report_sha256) DO NOTHING`
- inserted vs duplicate result from rowcount `1` and `0`
- unexpected rowcount rejection
- newest-first load with optional `config_version`, `digest_status`, and `limit`
- positional, dict, namedtuple-like, and row-object load inputs
- unsafe table names rejected before cursor creation
- valid lowercase table names accepted
- invalid query inputs rejected before cursor creation
- public exports include default table and store functions

- [ ] **Step 2: Run RED**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_store.py -q
```

Expected: fail because the store module does not exist.

- [ ] **Step 3: Implement store**

Implement the store with the readiness-gate store structure, using digest-specific columns and filters. The load SQL must order by:

```sql
ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
```

The table name validator remains a simple lowercase identifier validator:

```python
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")
_TABLE_NAME_ERROR = "table_name must be a simple lowercase identifier"
```

- [ ] **Step 4: Run GREEN**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_store.py -q
```

Expected: pass.

---

### Task 3: Digest Supabase Env Config

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_paper_autonomous_readiness_digest_config.py`
- Test: `tests/test_supabase_paper_autonomous_readiness_digest_config.py`

**Interfaces:**
- Consumes Task 2 default table.
- Produces:
  - `PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED"`
  - `PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN"`
  - `PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE_ENV_VAR = "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE"`
  - `DEFAULT_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE`
  - `SupabasePaperAutonomousReadinessDigestConfig`
  - `from_paper_autonomous_readiness_digest_db_env(env: Mapping[str, str | None] | None = None) -> SupabasePaperAutonomousReadinessDigestConfig`

- [ ] **Step 1: Write failing env config tests**

Create `tests/test_supabase_paper_autonomous_readiness_digest_config.py` by adapting `tests/test_supabase_paper_autonomous_readiness_gate_config.py` and replacing readiness-gate names with readiness-digest names. Cover:

- constants and default table match store
- disabled config accepts missing DSN/default table
- strict enabled values only
- enabled config reads explicit local DSN
- accepts `localhost`, `127.0.0.1`, `[::1]`, Unix-socket URI query, and keyword Unix-socket DSNs
- rejects remote Postgres hosts without echoing DSN, host, or secret
- rejects non-strict enabled values without echoing DSN
- enabled requires DSN without echoing unrelated secrets
- padded DSNs normalize to absent for disabled config and are rejected for enabled config
- frozen dataclass and redacted `repr`
- table name validator matches the store simple-lowercase identifier
- public `__all__` is limited to constants, dataclass, and loader

- [ ] **Step 2: Run RED**

Run:

```bash
pytest tests/test_supabase_paper_autonomous_readiness_digest_config.py -q
```

Expected: fail because the config module does not exist.

- [ ] **Step 3: Implement env config**

Implement by adapting `supabase_paper_autonomous_readiness_gate_config.py` with digest-specific env var names and messages. Validate DSNs in the dataclass before connection is possible. Do not echo DSN, host, or secret values in validation errors or `repr`.

- [ ] **Step 4: Run GREEN**

Run:

```bash
pytest tests/test_supabase_paper_autonomous_readiness_digest_config.py -q
```

Expected: pass.

---

### Task 4: Digest psycopg Adapter

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_readiness_digest_psycopg.py`
- Test: `tests/test_paper_autonomous_readiness_digest_psycopg.py`

**Interfaces:**
- Consumes Task 2 store functions.
- Produces:
  - `insert_paper_autonomous_readiness_digest_report_with_psycopg(dsn: str, report: Any, *, table_name=...) -> PaperAutonomousReadinessDigestInsertResult`
  - `load_paper_autonomous_readiness_digest_reports_with_psycopg(dsn: str, *, config_version=None, digest_status=None, limit=None, table_name=...) -> tuple[PaperAutonomousReadinessDigestReport, ...]`

- [ ] **Step 1: Write failing psycopg adapter tests**

Create `tests/test_paper_autonomous_readiness_digest_psycopg.py` by adapting `tests/test_paper_autonomous_readiness_gate_psycopg.py`. Cover:

- importing adapter does not import `psycopg`
- missing `psycopg` error mentions postgres extra and redacts DSN
- successful insert delegates to store, commits, closes
- successful load connects with `autocommit=True`, delegates to store, closes without commit
- write store failure rolls back and closes
- write commit failure rolls back and closes
- read failure closes without commit/rollback
- connect failure raises `"failed to connect to the paper autonomous readiness digest database"` without DSN/secret/host
- dict/list params are wrapped in `Jsonb`
- JSON cursor exposes `fetchall` and `rowcount`
- public exports and return annotations match the digest domain

- [ ] **Step 2: Run RED**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_psycopg.py -q
```

Expected: fail because the adapter module does not exist.

- [ ] **Step 3: Implement psycopg adapter**

Implement by adapting `paper_autonomous_readiness_gate_psycopg.py` with digest-specific store imports and error text. Use owned write connections with commit/rollback/close and owned read connections with `autocommit=True`. Keep JSONB wrapping for dict/list params.

- [ ] **Step 4: Run GREEN**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_psycopg.py -q
```

Expected: pass.

---

### Task 5: Digest Schema and Migration

**Files:**
- Create: `supabase/migrations/20260625000012_paper_autonomous_readiness_digest_reports.sql`
- Test: `tests/test_paper_autonomous_readiness_digest_schema.py`

**Interfaces:**
- Consumes Task 1 row shape and Task 2 default table.
- Produces local Supabase/Postgres table `public.paper_autonomous_readiness_digest_reports`.

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_paper_autonomous_readiness_digest_schema.py` by adapting `tests/test_paper_autonomous_readiness_gate_schema.py`.

Expected constants:

```python
EXPECTED_MIGRATION_NAME = (
    "20260625000012_paper_autonomous_readiness_digest_reports.sql"
)
PREVIOUS_MIGRATION_NAME = (
    "20260625000011_probability_selection_scorer_agreement_reports.sql"
)
DEFAULT_TABLE = "paper_autonomous_readiness_digest_reports"
```

Tests must import `DIGEST_STATUSES` and `NEXT_REVIEW_ACTION_BY_STATUS` from `polymarket_alpha_lab.paper_autonomous_readiness_digest` and cover:

- exactly one digest reports migration exists and it is the next unique migration after `20260625000011_probability_selection_scorer_agreement_reports.sql`
- table creates `public.paper_autonomous_readiness_digest_reports`
- columns:

```text
report_sha256 text primary key
generated_at timestamptz not null
config_version text not null
digest_status text not null
recommended_next_review_action text not null
evidence_json jsonb not null
source_config_versions_json jsonb not null
reason_code_counts_json jsonb not null
reason_codes_json jsonb not null
payload_json jsonb not null
paper_only boolean not null default true
report_only boolean not null default true
readonly boolean not null default true
inserted_at timestamptz not null default now()
```

- checks:

```text
check (report_sha256 ~ '^[a-f0-9]{64}$')
check (digest_status in (<exact values from DIGEST_STATUSES>))
check (recommended_next_review_action = case digest_status when 'pass' then '<NEXT_REVIEW_ACTION_BY_STATUS["pass"]>' when 'watch' then '<NEXT_REVIEW_ACTION_BY_STATUS["watch"]>' when 'blocked' then '<NEXT_REVIEW_ACTION_BY_STATUS["blocked"]>' end)
check (jsonb_typeof(evidence_json) = 'array')
check (jsonb_typeof(source_config_versions_json) = 'array')
check (jsonb_typeof(reason_code_counts_json) = 'array')
check (jsonb_typeof(reason_codes_json) = 'array')
check (jsonb_typeof(payload_json) = 'object')
check (jsonb_array_length(evidence_json) >= 1)
check (jsonb_array_length(source_config_versions_json) = jsonb_array_length(evidence_json))
check (paper_only is true)
check (report_only is true)
check (readonly is true)
```

- payload consistency checks for `generated_at`, `config_version`, `digest_status`, `recommended_next_review_action`, `evidence`, `source_config_versions`, `reason_code_counts`, `reason_codes`, and hard flags
- JSONB payload columns and no `float`, `real`, or `double precision`
- indexes:

```sql
create index if not exists pardr_generated_at_idx
    on public.paper_autonomous_readiness_digest_reports
    (generated_at desc);

create index if not exists pardr_status_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc);

create index if not exists pardr_config_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (config_version, generated_at desc);

create index if not exists pardr_source_versions_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (source_config_versions_json jsonb_path_ops);

create index if not exists pardr_reason_codes_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (reason_codes_json jsonb_path_ops);

create index if not exists pardr_payload_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (payload_json jsonb_path_ops);

create index if not exists pardr_status_sort_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc, inserted_at desc, report_sha256 desc);
```

- table and index names under 63 characters
- no functions, triggers, row-level security, policies, foreign keys, references, SQLite, live trading, auth, wallet, private key, or order surfaces

- [ ] **Step 2: Run RED**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_schema.py -q
```

Expected: fail because the migration does not exist.

- [ ] **Step 3: Add migration**

Create `supabase/migrations/20260625000012_paper_autonomous_readiness_digest_reports.sql` with:

```sql
create table if not exists public.paper_autonomous_readiness_digest_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    digest_status text not null,
    recommended_next_review_action text not null,
    evidence_json jsonb not null,
    source_config_versions_json jsonb not null,
    reason_code_counts_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (digest_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_review_action = case digest_status
            when 'pass' then 'continue_operator_review_of_paper_autonomous_readiness_digest'
            when 'watch' then 'review_watch_paper_autonomous_readiness_evidence'
            when 'blocked' then 'review_blocked_paper_autonomous_readiness_evidence'
        end
    ),
    check (jsonb_typeof(evidence_json) = 'array'),
    check (jsonb_typeof(source_config_versions_json) = 'array'),
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (jsonb_array_length(evidence_json) >= 1),
    check (jsonb_array_length(source_config_versions_json) = jsonb_array_length(evidence_json)),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'digest_status' and jsonb_typeof(payload_json -> 'digest_status') = 'string' and payload_json ->> 'digest_status' = digest_status),
    check (payload_json ? 'recommended_next_review_action' and jsonb_typeof(payload_json -> 'recommended_next_review_action') = 'string' and payload_json ->> 'recommended_next_review_action' = recommended_next_review_action),
    check (payload_json ? 'evidence' and jsonb_typeof(payload_json -> 'evidence') = 'array' and evidence_json = payload_json -> 'evidence'),
    check (payload_json ? 'source_config_versions' and jsonb_typeof(payload_json -> 'source_config_versions') = 'array' and source_config_versions_json = payload_json -> 'source_config_versions'),
    check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts'),
    check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes')
);

create index if not exists pardr_generated_at_idx
    on public.paper_autonomous_readiness_digest_reports
    (generated_at desc);

create index if not exists pardr_status_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc);

create index if not exists pardr_config_generated_idx
    on public.paper_autonomous_readiness_digest_reports
    (config_version, generated_at desc);

create index if not exists pardr_source_versions_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (source_config_versions_json jsonb_path_ops);

create index if not exists pardr_reason_codes_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (reason_codes_json jsonb_path_ops);

create index if not exists pardr_payload_idx
    on public.paper_autonomous_readiness_digest_reports using gin
    (payload_json jsonb_path_ops);

create index if not exists pardr_status_sort_idx
    on public.paper_autonomous_readiness_digest_reports
    (digest_status, generated_at desc, inserted_at desc, report_sha256 desc);
```

The migration sequence label `20260625` continues the existing migration series and is independent of this plan file's `2026-06-29` date.

- [ ] **Step 4: Run GREEN**

Run:

```bash
pytest tests/test_paper_autonomous_readiness_digest_schema.py -q
```

Expected: pass.

---

### Task 6: CLI Persistence Wiring, Scope Tests, and Docs

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli_paper_autonomous_readiness_digest.py`
- Modify: `tests/test_cli_paper_autonomous_readiness_digest_scope.py`
- Modify: `README.md`
- Create: `docs/paper-autonomous-readiness-digest-db-persistence.md`

**Interfaces:**
- Consumes Tasks 3 and 4.
- Adds parser flag `--persist`, `action="store_true"`, `dest="persist"`.
- Adds `from_paper_autonomous_readiness_digest_db_env` import.
- Adds `PaperAutonomousReadinessDigestDbSink = Callable[..., object]`.
- Adds optional `paper_autonomous_readiness_digest_db_sink: PaperAutonomousReadinessDigestDbSink | None = None` to `main`; when `None`, lazy-import `insert_paper_autonomous_readiness_digest_report_with_psycopg` only inside the `--persist` branch.
- The command prints the existing aggregate summary and only prints `persisted=True/False` when `--persist` is used.

- [ ] **Step 1: Write failing CLI tests**

Update `tests/test_cli_paper_autonomous_readiness_digest.py`:

- Remove `--persist` from forbidden flag parametrization.
- Add constants and helpers for digest DB env:

```python
DIGEST_DB_ENABLED_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED"
)
DIGEST_DB_DSN_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN"
)
DIGEST_DB_TABLE_ENV_VAR = (
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE"
)


def _set_digest_db_env(
    monkeypatch: pytest.MonkeyPatch,
    dsn: str,
    *,
    table_name: str = "paper_autonomous_readiness_digest_reports",
) -> None:
    monkeypatch.setenv(DIGEST_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(DIGEST_DB_DSN_ENV_VAR, dsn)
    monkeypatch.setenv(DIGEST_DB_TABLE_ENV_VAR, table_name)
```

Add tests:

- default command with no `--persist` does not load digest DB env, does not connect to digest DB, and does not print `persisted=`
- `--persist` with digest DB disabled fails before sink/connect and reports digest DB must be enabled
- `--persist` with digest DB enabled and missing DSN fails before sink/connect and redacts unrelated secrets
- `--persist` with remote digest DSN rejects before connecting and redacts DSN, secret, and host
- `--persist` writes the already-built digest report with digest env DSN/table and prints `persisted=True`
- duplicate insert result prints `persisted=False`
- sink failure redacts readiness DSN/table, agreement DSN/table when enabled, digest DSN/table, payloads, market details, reason codes, wallet/account/order/auth/private-key fields, and hashes. The existing redactor already handles readiness/agreement context; extend it to accept digest context and add a three-DSN CLI regression test.
- runner injection still receives no digest DB args and persistence happens after the report returns

- [ ] **Step 2: Write failing scope tests**

Update `tests/test_cli_paper_autonomous_readiness_digest_scope.py`:

- Parser surface expected values become `{"--limit", "limit", "--persist", "persist"}`.
- Command branch expected refs include `from_paper_autonomous_readiness_digest_db_env` and the digest insert sink.
- The branch may reference `persist` only as the explicit CLI gate.
- The helper remains read-only and still must not reference insert/commit/rollback/wallet/order/auth/private_key/fast.
- `_run_paper_autonomous_readiness_digest` must not accept DB sink parameters and must not accept digest persistence DSN/table parameters.
- Summary remains aggregate-only and must not reference DB internals.

- [ ] **Step 3: Run RED**

Run:

```bash
pytest tests/test_cli_paper_autonomous_readiness_digest.py tests/test_cli_paper_autonomous_readiness_digest_scope.py -q
```

Expected: fail because `--persist` and digest DB env wiring do not exist yet.

- [ ] **Step 4: Implement CLI wiring**

Modify `cli.py`:

- Import `from_paper_autonomous_readiness_digest_db_env`.
- Add `PaperAutonomousReadinessDigestDbSink = Callable[..., object]`.
- Add `paper_autonomous_readiness_digest_db_sink: PaperAutonomousReadinessDigestDbSink | None = None` to `main`.
- Add parser argument:

```python
paper_autonomous_readiness_digest.add_argument(
    "--persist",
    action="store_true",
    default=False,
    dest="persist",
)
```

- In the command branch, only read digest DB env if `args.persist` is true.
- If `args.persist` is true, require digest DB enabled and DSN present.
- Validate digest DSN through the new config before any sink connection.
- After `_print_paper_autonomous_readiness_digest_summary(report)`, call the injected digest DB sink if provided, otherwise lazy-import `insert_paper_autonomous_readiness_digest_report_with_psycopg`. Do this only when `args.persist` is true, then print:

```python
print(f"persisted={result.inserted}")
```

- Extend `_redacted_paper_readiness_digest_error` to accept optional `digest_dsn` and `digest_table_name` and redact all configured DSNs/tables: source readiness, optional agreement, and output digest.
- Do not modify `_run_paper_autonomous_readiness_digest` to write anything.

- [ ] **Step 5: Update README**

Update the Paper Autonomous Readiness Digest CLI/readback section to say:

- default command accepts `--limit` and writes nothing
- optional `--persist` stores only the final digest report in local Supabase/Postgres through `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_*`
- no DSN/table/file/live/auth/wallet/account/order/signing/execution flags
- persisted digest is observability history only, not trade permission, not financial advice, not order instruction, and not execution authorization
- add a pointer to `docs/paper-autonomous-readiness-digest-db-persistence.md`

Create `docs/paper-autonomous-readiness-digest-db-persistence.md` with:

```markdown
# Paper Autonomous Readiness Digest DB Persistence

This optional local Supabase/Postgres persistence-only surface stores
deterministic `PaperAutonomousReadinessDigestReport` snapshots for later
paper-only/report-only/readonly review.

`paper-autonomous-readiness-digest` writes nothing by default. Only
`paper-autonomous-readiness-digest --persist` reads the readiness digest DB
environment config and inserts the already-built digest report. There are no
DSN or table CLI flags.

Environment:

- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_READINESS_DIGEST_DB_TABLE`

The default table is `paper_autonomous_readiness_digest_reports`.

Do not put secrets, private keys, wallet credentials, account identifiers, or
API tokens in reports or docs. Persistence is observability history only. It is
not financial advice, investment ranking, permission to trade, an order
instruction, execution authorization, wallet access, auth handling, signing,
submission, cancellation, replacement, or exchange mutation.

All durable data for this surface remains local Supabase/Postgres only. There is
no JSONL/SQLite/file durable store, Redis, Mongo, SQLAlchemy, generic durable
store abstraction, hosted DB assumption, or file-backed cache.
```

- [ ] **Step 6: Run GREEN**

Run:

```bash
pytest tests/test_cli_paper_autonomous_readiness_digest.py tests/test_cli_paper_autonomous_readiness_digest_scope.py -q
```

Expected: pass.

---

### Task 7: Full Verification, Local Review, Commit, Push

**Files:**
- Modify: `.superpowers/sdd/progress.md`
- Git commit all files from Tasks 1-6.

**Interfaces:**
- Consumes all previous tasks.
- Produces pushed GitHub commit.

- [ ] **Step 1: Run focused tests**

Run:

```bash
pytest \
  tests/test_paper_autonomous_readiness_digest_db_row.py \
  tests/test_paper_autonomous_readiness_digest_store.py \
  tests/test_supabase_paper_autonomous_readiness_digest_config.py \
  tests/test_paper_autonomous_readiness_digest_psycopg.py \
  tests/test_paper_autonomous_readiness_digest_schema.py \
  tests/test_cli_paper_autonomous_readiness_digest.py \
  tests/test_cli_paper_autonomous_readiness_digest_scope.py \
  -q
```

Expected: all pass.

- [ ] **Step 2: Run full verification**

Run:

```bash
pytest -q
python -m compileall -q src tests
git diff --check
```

Expected: all pass with zero failures and no whitespace errors.

- [ ] **Step 3: Sync CodeGraph**

Run:

```bash
codegraph sync
```

Expected: sync succeeds or reports already up to date.

- [ ] **Step 4: Run opencode review**

Use the local review gate:

```bash
TMP=/tmp/opencode-review-state-polymarket-readiness-digest-persistence-final
rm -rf "$TMP"
mkdir -p "$TMP/opencode"
cp /home/ubuntu/.local/share/opencode/auth.json "$TMP/opencode/auth.json"
XDG_DATA_HOME="$TMP" opencode run --format json \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  'DO NOT modify/create/delete ANY file. Review the current diff for readiness digest local Supabase/Postgres persistence. Focus on Phase 1 paper-only boundary, local Supabase/Postgres-only durable data, no live trading/auth/wallet/order/signing/execution mutation, env-only DSN/table config, no file/SQLite/JSONL durable store, local DSN validation before connect, and redaction of DSN/table/payload/market/reason/wallet/account/order/auth/private-key/hash details. Return blockers first, then important findings, then minor findings.'
```

Expected: no blockers or important findings. Fix any blockers/important findings before proceeding.

- [ ] **Step 5: Secret scan changed diff**

Run a diff scan for token-like content and known leaked values:

```bash
git diff --cached --name-only
git diff --cached | rg -n "g[h]p[_]|s[k][-]|private[_]key|secret[-]token|super[-]secret|postgresql://.*example|wallet|order[_]id" || true
```

Expected: no real secret or credential material in staged diff. Test fixture strings are acceptable only when deliberately fake and redacted by tests.

- [ ] **Step 6: Commit and push**

Run:

```bash
git status --short
git add \
  src/polymarket_alpha_lab/paper_autonomous_readiness_digest_db_row.py \
  src/polymarket_alpha_lab/paper_autonomous_readiness_digest_store.py \
  src/polymarket_alpha_lab/supabase_paper_autonomous_readiness_digest_config.py \
  src/polymarket_alpha_lab/paper_autonomous_readiness_digest_psycopg.py \
  src/polymarket_alpha_lab/cli.py \
  supabase/migrations/20260625000012_paper_autonomous_readiness_digest_reports.sql \
  tests/test_paper_autonomous_readiness_digest_db_row.py \
  tests/test_paper_autonomous_readiness_digest_store.py \
  tests/test_supabase_paper_autonomous_readiness_digest_config.py \
  tests/test_paper_autonomous_readiness_digest_psycopg.py \
  tests/test_paper_autonomous_readiness_digest_schema.py \
  tests/test_cli_paper_autonomous_readiness_digest.py \
  tests/test_cli_paper_autonomous_readiness_digest_scope.py \
  README.md \
  docs/paper-autonomous-readiness-digest-db-persistence.md \
  docs/superpowers/plans/2026-06-29-readiness-digest-supabase-persistence.md \
  .superpowers/sdd/progress.md
git commit -m "feat: persist readiness digest reports"
git push origin main
```

Expected: commit succeeds and push updates `origin/main`. This push is included because the user explicitly instructed this project to push completed, verified nodes to GitHub.

- [ ] **Step 7: Write handoff summary**

Append a short handoff summary to the controller notes or final response with:

- repo status
- pushed commit hash
- verification commands and outcomes
- opencode review outcome
- uncommitted files, if any
- recommended next node
