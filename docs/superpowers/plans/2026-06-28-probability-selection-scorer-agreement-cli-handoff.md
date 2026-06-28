# Probability Selection Scorer Agreement CLI Handoff

> **For agentic workers:** Implement this handoff task-by-task with `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Keep this document updateable; check boxes only after fresh verification evidence exists.

## Goal

Add a readback/reporting CLI path for the probability-selection-scorer-agreement feature so an operator can load durable Supabase-backed probability-selection and scorer outputs, build the agreement report, and inspect the result without creating live trading side effects.

## Safety Boundary

- This work is readback/report-only. It must not place orders, cancel orders, mutate auth/session state, or call live trading endpoints.
- Durable data must be Supabase-only. Do not add file-backed durable stores, local JSONL history, SQLite, or ad hoc cache persistence for production data.
- Preserve hard safety flags: `paper_only=True`, `report_only=True`, and `readonly=True` through config, report construction, CLI output, and tests.
- Do not introduce credential prompts or auth flows. The CLI may read existing environment configuration but must not log secrets.
- Keep live-trading/auth/order mutation code out of scope even behind flags.

## Intended Files

- `src/polymarket_alpha_lab/probability_selection_scorer_agreement.py` - existing pure report builder and hard-flag model; unchanged in this node.
- `src/polymarket_alpha_lab/probability_selection_scorer_agreement_load.py` - added pure dependency-injected loader composition over existing Supabase/Postgres store loaders.
- `src/polymarket_alpha_lab/cli.py` - added the report-only `probability-selection-scorer-agreement` command, local DSN guard, redacted failure path, default read adapter, and aggregate-only summary printer.
- `tests/test_probability_selection_scorer_agreement_load.py` - added pure loader composition coverage.
- `tests/test_cli_probability_selection_scorer_agreement.py` - added CLI behavior, local DSN, redaction, cleanup, and summary coverage.
- `tests/test_cli_probability_selection_scorer_agreement_scope.py` - added AST/static phase-boundary checks for parser/helper/summary surfaces.
- `docs/superpowers/plans/2026-06-28-probability-selection-scorer-agreement-cli-handoff.md` - update this handoff as implementation status changes.

## Implementation Notes

- Start from `build_probability_selection_scorer_agreement_report` and the immutable `ProbabilitySelectionScorerAgreementConfig` / `ProbabilitySelectionScorerAgreementReport` safety fields.
- The CLI is deterministic and non-interactive: it reads configured local Supabase/Postgres-backed inputs, builds one agreement report, prints aggregate fields, and exits nonzero only for invalid config/input/runtime errors.
- The public parser surface is only `--limit`; there are no CLI DSN/table/file/sink/persist/live/auth/order flags.
- The default psycopg path uses `autocommit=True`, closes both connections, and does not call commit/rollback or any insert/sink helper.
- The command hard-rejects non-local DSNs before connection. Allowed DSNs are local Postgres/Supabase hosts (`localhost`, `127.0.0.1`, `::1`) or explicit Unix socket hosts.
- CLI output includes the hard safety flags and safe reason-code formatting, but does not print source rows, payloads, market identifiers, questions, table names, DSNs, or hashes.
- Keep all writes limited to tests and source files required by the CLI/readback implementation. README was intentionally left unchanged.

## Verification Checklist

- [x] Existing probability-selection-scorer-agreement coverage:
  - Command: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_probability_selection_scorer_agreement.py tests/test_probability_selection_scorer_agreement_scope.py tests/test_probability_selection_scorer_agreement_load.py tests/test_cli_probability_selection_scorer_agreement.py tests/test_cli_probability_selection_scorer_agreement_scope.py`
  - Evidence: `105 passed in 3.45s`.
- [x] Adjacent CLI/readback coverage:
  - Command: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history.py tests/test_cli_autonomous_market_scorer_history.py tests/test_cli_paper_autonomous_readiness_digest.py`
  - Evidence: `85 passed in 2.79s`.
- [x] Store/config adjacency coverage:
  - Command: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q tests/test_supabase_probability_selection_summary_config.py tests/test_supabase_autonomous_market_scorer_config.py tests/test_paper_probability_selection_summary_store.py tests/test_autonomous_market_scorer_db_store.py`
  - Evidence: `90 passed in 1.48s`.
- [x] Static/lint/syntax checks:
  - Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m compileall -q src tests`
  - Evidence: passed.
  - Command: `git diff --check`
  - Evidence: passed.
- [x] Full regression suite:
  - Command: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q`
  - Evidence: `10110 passed, 1 skipped in 73.13s`.
- [x] CodeGraph refresh:
  - Command: `codegraph sync`
  - Evidence: synced 3 changed files after final test/CLI changes.
- [x] Boundary audit confirms no live trading/auth/order mutation path was added:
  - Evidence: local subagent review found no live/auth/wallet/order/sink/persistence behavior; it found a `--limit` propagation issue, which was fixed by passing `limit` through as both `selection_limit` and `scorer_limit`.
- [x] Durable-data audit confirms production durable state remains Supabase-only:
  - Evidence: new durable reads use existing local Supabase/Postgres env configs and store loaders only; no SQLite/JSONL/Redis/Mongo/file durable store was added.
- [x] `opencode` review:
  - Command: `opencode run --format json --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab 'DO NOT modify/create/delete ANY file. Review the current uncommitted probability-selection-scorer-agreement CLI/readback node...'`
  - Evidence: approved with "No blocking findings." It verified local Supabase/Postgres-only durable data, no live/auth/wallet/order/sink/persistence behavior, DSN/table redaction, aggregate-only output, autocommit/cleanup/no commit-rollback behavior, `--limit` propagation, and test adequacy.

## Review Gate

- Before merge or handoff completion, request an `opencode` review focused on:
  - CLI/readback safety boundary.
  - Supabase-only durable-data rule.
  - Absence of live trading/auth/order mutation behavior.
  - Adequacy of CLI and report-builder tests.

Status: `opencode` review complete; no blocking findings.

## Next-Node Options

- **Review node:** run/finalize `opencode` review and fix any blocking findings.
- **Docs node:** add user-facing CLI documentation only if the owner explicitly expands write scope beyond this handoff.
- **Strategy node:** build the next report-only agreement trend or calibration view that uses this agreement signal to inform later autonomous recommendation gating without live trading.
