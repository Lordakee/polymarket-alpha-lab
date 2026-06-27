# 2026-06-27 Paper Probability Selection Summary History CLI Handoff

## Node Summary

Implemented the `paper-probability-selection-summary-history` CLI command.

The command reads persisted `PaperProbabilitySelectionSummaryReport` rows from
local Supabase/Postgres through env-only source DB configuration, builds a
`PaperProbabilitySelectionSummaryHistoryReport`, prints aggregate-only history
metrics, and writes nothing by default. With `--persist`, it writes the derived
history report through the existing local Supabase/Postgres history DB env
configuration.

This node stays inside the current Phase boundary:

- Paper-only/report-only/readonly by default.
- No live trading.
- No auth, wallet, account, private-key, signing, order submission, cancel, or
  exchange mutation surface.
- All durable project data remains local Supabase/Postgres only.
- No SQLite, JSONL durable persistence, Redis, Mongo, SQLAlchemy, generic DB
  abstraction, hosted DB assumption, or file-backed durable store was added.

## Changed Files

- `src/polymarket_alpha_lab/cli.py`
  - Added parser surface for `paper-probability-selection-summary-history`.
  - Supported flags are exactly `--limit` and `--persist`.
  - Added dependency-injection hooks for runner and optional DB sink.
  - Added source read helper using `psycopg.connect(..., autocommit=True)`.
  - Loads source summaries newest-first from DB and reverses them before the
    reducer so history is built chronologically.
  - Added dedicated redaction helpers for read and persistence errors.
  - Added aggregate-only summary printer.
- `tests/test_cli_paper_probability_selection_summary_history.py`
  - Added behavioral tests for parser help, forbidden flags, disabled source
    config, limit validation, source env use, output redaction, no-write default,
    optional persistence, persistence error redaction, helper validation, and
    chronological reducer input.
- `tests/test_cli_paper_probability_selection_summary_history_scope.py`
  - Added AST guard tests for exact parser surface, `allow_abbrev=False`, source
    env/history env separation, helper import scope, redaction helper usage, and
    aggregate-only summary references.
- `README.md`
  - Documented the new command, env-only source DB read behavior, no-write
    default, optional history persistence, chronological reduction, aggregate
    output, and no-live-trading boundary.

## Verification

Focused CLI tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py
```

Result: `34 passed`.

After parallel coverage review identified that `--persist` sink-failure
redaction had only static coverage, an additional runtime test was added:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py::test_history_cli_persistence_errors_redact_source_history_payload_and_hash
```

Result: `1 passed`.

The focused CLI tests were re-run after the additional coverage:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py
```

Result: `35 passed`.

Related probability DB/config/reducer/store tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_supabase_probability_selection_summary_config.py tests/test_supabase_paper_probability_selection_summary_history_config.py tests/test_paper_probability_selection_summary_store.py tests/test_paper_probability_selection_summary_history.py tests/test_paper_probability_selection_summary_history_store.py tests/test_paper_probability_selection_summary_history_psycopg.py tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py
```

Result after additional persistence-failure redaction coverage: `150 passed`.

CLI slice:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_paper_probability_selection_summary_history_scope.py
```

Result after additional persistence-failure redaction coverage: `218 passed`.

Full suite:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
```

Result after additional persistence-failure redaction coverage:
`9794 passed, 1 skipped in 61.20s`.

Compile:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests
```

Result: passed.

Additional checks:

- `git diff --check`: passed.
- `codegraph sync`: synced the changed test file after adding the persistence
  failure redaction test; a final repeat sync returned `Already up to date`.
- Node diff secret scan: clean.
- Forbidden production persistence/trading scan: no blocking production hits.
  Test-only hits are forbidden literal guards.

## Review

Opencode review was run read-only with:

```bash
opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
```

Artifacts:

- `/tmp/polymarket-alpha-lab-review/selection-summary-history-cli-review-package-v2.md`
- `/tmp/polymarket-alpha-lab-review/selection-summary-history-cli-opencode-review-v2.jsonl`

Verdict: `APPROVED`.

Non-blocking notes from review:

- The `jsonl` carve-out in branch scope tests is harmless test asymmetry.
- The `persisted` output fallback of `True` when a sink result lacks `inserted`
  is semantically defensible; the default sink currently returns an object with
  `inserted`.

## Operational Notes

The command intentionally has no CLI DSN/table flags. Source DB configuration is
only read from:

- `POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_DB_*`

Persistence configuration is only read when `--persist` is present, from:

- `POLYMARKET_ALPHA_LAB_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_DB_*`

Default execution is a pure read/reduce/print path. It should be safe to run in
analysis loops without creating new durable rows unless `--persist` is explicit.

## Recommended Next Node

Next recommended development is a persisted history viewer/health trend layer
on top of this new history report. It should remain local Supabase/Postgres-only
and paper/report-only, and can be split into parallel modules:

- Store/query helper for history trend reads.
- CLI read-only aggregate viewer.
- Readiness/health reducer that converts history into allocation-readiness
  signals.
- Scope tests guarding no live trading and no file-backed durable persistence.
