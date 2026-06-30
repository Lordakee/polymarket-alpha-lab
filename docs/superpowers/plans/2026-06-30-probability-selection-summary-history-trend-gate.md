# Probability Selection Summary History Trend Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Phase 1-safe gate that turns local Supabase/Postgres probability selection summary history trends into a pass/watch/blocked readiness evidence source.

**Architecture:** Follow the existing `probability_selection_scorer_agreement_trend_gate` pattern: a pure frozen dataclass reducer gates the already-existing `PaperProbabilitySelectionSummaryHistoryTrendReport`, a read-only CLI helper loads history rows from local Supabase/Postgres and builds the trend plus gate, and the readiness digest can optionally consume the new gate as evidence. This node is report-only and does not add live execution, auth, wallet, key, signing, order, or exchange mutation surfaces.

**Tech Stack:** Python 3.11+, `dataclasses`, `Decimal`, `datetime.UTC`, pytest, local Supabase/Postgres via existing psycopg config helpers.

## Global Constraints

- Codex subagents use model `gpt-5.5`, reasoning `xhigh`, and fast mode is forbidden.
- Reviews use local `opencode` with model `zhipuai-coding-plan/glm-5.2`, variant/thinking `max`.
- Durable project data must use local Supabase/Postgres only.
- No SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstraction, or new file-backed durable storage.
- Phase 1 boundary: no live trading, no auth/wallet/private keys, no order signing/submission/cancellation/replacement, no exchange mutation.
- All reducers remain paper-only, report-only, and readonly.
- Use `Decimal` for probability and share values; do not introduce floats.
- Do not edit applied migrations in place; this node should not need a migration.

---

## File Structure

- Create `src/polymarket_alpha_lab/paper_probability_selection_summary_history_trend_gate.py`: pure gate reducer over `PaperProbabilitySelectionSummaryHistoryTrendReport`.
- Create `tests/test_paper_probability_selection_summary_history_trend_gate.py`: reducer tests, direct-construction invariant tests, hard-flag tests, Decimal-only tests, and source type tests.
- Modify `src/polymarket_alpha_lab/cli.py`: add command `paper-probability-selection-summary-history-trend-gate`, default helper, parser wiring, output summary, and injection hook.
- Create `tests/test_cli_paper_probability_selection_summary_history_trend_gate.py`: CLI boundary, env config, local DB helper, redaction, and summary tests.
- Modify `src/polymarket_alpha_lab/paper_autonomous_readiness_digest.py`: add optional `selection_summary_trend_gate_report` evidence source after `agreement_trend_gate` and before `ledger`.
- Modify `tests/test_paper_autonomous_readiness_digest.py`: digest evidence order/status tests for the new optional source.
- Modify `tests/test_paper_autonomous_readiness_digest_db_row.py` if needed only to prove row codec round-trips the new source through payload JSON; do not add a migration in this node.
- Modify docs only after code is green: `docs/paper-autonomous-readiness-gate.md` or `docs/strategy-recommendation-layer.md` if they describe readiness digest evidence sources.

---

### Task 1: Pure Selection Summary Trend Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_probability_selection_summary_history_trend_gate.py`
- Create/Modify: `tests/test_paper_probability_selection_summary_history_trend_gate.py`

**Interfaces:**
- Consumes: `PaperProbabilitySelectionSummaryHistoryTrendReport` from `paper_probability_selection_summary_history_trend.py`.
- Produces:
  - `DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION`
  - `PaperProbabilitySelectionSummaryHistoryTrendGateConfig`
  - `PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount`
  - `PaperProbabilitySelectionSummaryHistoryTrendGateReport`
  - `build_paper_probability_selection_summary_history_trend_gate_report(source_report, *, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Add tests mirroring `tests/test_probability_selection_scorer_agreement_trend_gate.py`. Required behavior:

```python
def test_selection_summary_trend_gate_passes_stable_selection_trend() -> None:
    source = _trend_report(trend_status="stable", reason_codes=("history_trend_stable",))
    report = api.build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_probability_selection_summary_history_trend_review"
    assert report.reason_codes == ("paper_probability_selection_summary_history_trend_gate_passed",)
```

Required watch behavior:

```python
def test_selection_summary_trend_gate_watches_source_watch_and_stale_reports() -> None:
    source = _trend_report(
        trend_status="watch",
        stale_history_count=1,
        reason_codes=("stale_history_reports_present",),
    )
    report = api.build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "watch"
    assert "latest_paper_probability_selection_summary_history_trend_watch" in report.reason_codes
```

Required blocked behavior:

```python
def test_selection_summary_trend_gate_blocks_insufficient_stale_or_deteriorating_source() -> None:
    source = _trend_report(
        source_history_count=2,
        trend_status="insufficient_history",
        reason_codes=("insufficient_history_count",),
    )
    report = api.build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(min_source_history_count=3),
        generated_at=GENERATED_AT,
    )
    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "insufficient_paper_probability_selection_summary_history_trend_samples",
    )
```

Also test `trend_status="deteriorating"` blocks, `trend_status="stale"` blocks when latest source is stale, repeated watch streaks remain watch, future source `generated_at` rejects, wrong source type rejects, config/report dataclasses are frozen, hard flags remain true, and direct report construction validates reason code consistency.

- [ ] **Step 2: Run reducer tests red**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_probability_selection_summary_history_trend_gate.py
```

Expected: fail because module or exported symbols do not exist.

- [ ] **Step 3: Implement minimal reducer**

Implement a pure module using the scorer agreement trend gate style. Required constants:

```python
DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION = (
    "paper-probability-selection-summary-history-trend-gate-v0"
)
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_GATE_STATUS = {
    "pass": "allow_probability_selection_summary_history_trend_review",
    "watch": "throttle_probability_selection_summary_history_trend_review",
    "blocked": "block_probability_selection_summary_history_trend_review",
}
PASS_REASON_CODE = "paper_probability_selection_summary_history_trend_gate_passed"
```

Required source fields copied into the gate report:

```python
source_history_count
source_trend_status
source_recommended_next_step
latest_history_status
latest_status_streak
latest_selected_share
average_selected_share
selected_share_delta
stale_history_count
thin_history_count
latest_source_reason_codes
recurring_source_reason_code_counts
```

Required blocked reason codes:

```python
"insufficient_paper_probability_selection_summary_history_trend_samples"
"stale_paper_probability_selection_summary_history_trend"
"deteriorating_paper_probability_selection_summary_history_trend"
```

Required watch reason codes:

```python
"latest_paper_probability_selection_summary_history_trend_watch"
"repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded"
"thin_paper_probability_selection_summary_history_trend_reports"
"recurring_paper_probability_selection_summary_history_trend_reason_codes"
"aged_paper_probability_selection_summary_history_trend_report"
```

The reducer must be exact-type validated, frozen, Decimal-only for share fields, timezone-aware, and hard-flag enforced.

- [ ] **Step 4: Run reducer tests green**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_probability_selection_summary_history_trend.py tests/test_paper_probability_selection_summary_history_trend_gate.py
```

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/paper_probability_selection_summary_history_trend_gate.py tests/test_paper_probability_selection_summary_history_trend_gate.py
git commit -m "feat: add probability selection summary trend gate"
```

---

### Task 2: CLI Command and Local Supabase Read Path

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create/Modify: `tests/test_cli_paper_probability_selection_summary_history_trend_gate.py`

**Interfaces:**
- Consumes Task 1 gate builder and config classes.
- Consumes existing `from_paper_probability_selection_summary_history_db_env`, existing history store loader, and existing `build_paper_probability_selection_summary_history_trend_report`.
- Produces CLI command `paper-probability-selection-summary-history-trend-gate` with a default read-only helper.

- [ ] **Step 1: Write failing CLI tests**

Add CLI tests mirroring `tests/test_cli_probability_selection_scorer_agreement_trend_gate.py`. Required tests:

```python
COMMAND = "paper-probability-selection-summary-history-trend-gate"

def test_parser_help_includes_selection_summary_history_trend_gate(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    assert COMMAND in capsys.readouterr().out
```

```python
def test_selection_summary_trend_gate_command_help_declares_readonly_report_only_boundary(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "read-only" in captured.out
    assert "report-only" in captured.out
    assert "--persist" not in captured.out
    assert "--dsn" not in captured.out
    assert "--table" not in captured.out
```

Also test forbidden flags: `--persist`, `--dsn`, `--db-dsn`, `--table`, `--db-table`, `--input`, `--output`, `--live`, `--wallet`, `--order`, `--execute`, `--auth`, `--private-key`, `--account`, `--fast`.

The helper test must assert read-only local DB behavior:

```python
helper = getattr(cli, "_run_paper_probability_selection_summary_history_trend_gate")
result = helper(dsn=dsn, table_name=table_name, limit=7, runner=None)
assert result is gate_report
assert connect_calls == [(dsn, True)]
assert load_calls == [{"connection": connection, "limit": 7, "table_name": table_name}]
assert reports == (oldest, newest)
assert connection.close_count == 1
```

- [ ] **Step 2: Run CLI tests red**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history_trend_gate.py
```

Expected: fail because CLI command/helper does not exist.

- [ ] **Step 3: Implement CLI wiring**

Add a main injection parameter named:

```python
paper_probability_selection_summary_history_trend_gate_runner: PaperProbabilitySelectionSummaryHistoryTrendGateRunner | None = None
```

Add a subparser:

```python
paper_probability_selection_summary_history_trend_gate = subparsers.add_parser(
    "paper-probability-selection-summary-history-trend-gate",
    allow_abbrev=False,
    description=(
        "Build a read-only, report-only gate from local Supabase/Postgres "
        "probability selection summary history."
    ),
)
paper_probability_selection_summary_history_trend_gate.add_argument(
    "--limit",
    type=int,
    default=25,
    dest="limit",
)
```

Implement `_run_paper_probability_selection_summary_history_trend_gate` by:
- connecting with `psycopg.connect(dsn, autocommit=True)`,
- loading `load_paper_probability_selection_summary_history_reports(connection, limit=limit, table_name=table_name)`,
- sorting loaded reports by `generated_at` ascending before building,
- building `PaperProbabilitySelectionSummaryHistoryTrendConfig()` and `PaperProbabilitySelectionSummaryHistoryTrendGateConfig()`,
- building trend then gate with the same `generated_at`,
- closing the connection in `finally`,
- never committing or rolling back.

Output summary should print only aggregate fields and sanitized reason code fields; do not print DSN, table name, payload JSON, market slug, question, hash, or source row details.

- [ ] **Step 4: Run CLI tests green**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli_paper_probability_selection_summary_history_trend_gate.py tests/test_cli_paper_probability_selection_summary_history_trend.py
```

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/cli.py tests/test_cli_paper_probability_selection_summary_history_trend_gate.py
git commit -m "feat: add probability selection summary trend gate cli"
```

---

### Task 3: Readiness Digest Optional Evidence Source

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_autonomous_readiness_digest.py`
- Modify: `tests/test_paper_autonomous_readiness_digest.py`
- Modify: `tests/test_paper_autonomous_readiness_digest_db_row.py` only if codec tests need an explicit new-source round trip.

**Interfaces:**
- Consumes any report exposing `gate_status`, `recommended_next_step`, `generated_at`, `config_version`, and `reason_codes`.
- Produces digest source name `selection_summary_trend_gate`.

- [ ] **Step 1: Write failing digest tests**

Update canonical order expectations to:

```python
(
    "readiness_gate",
    "screening",
    "transition",
    "allocation",
    "agreement_trend_gate",
    "selection_summary_trend_gate",
    "ledger",
)
```

Add a digest construction test:

```python
report = api.build_paper_autonomous_readiness_digest_report(
    _readiness_report(),
    agreement_trend_gate_report=_source_report(
        status="pass",
        field_name="gate_status",
        config_version="agreement-trend-gate-v0",
        reason_codes=("agreement_trend_gate_passed",),
    ),
    selection_summary_trend_gate_report=_source_report(
        status="blocked",
        field_name="gate_status",
        config_version="selection-summary-trend-gate-v0",
        recommended_next_step="block_probability_selection_summary_history_trend_review",
        reason_codes=("deteriorating_paper_probability_selection_summary_history_trend",),
    ),
    config=api.PaperAutonomousReadinessDigestConfig(),
    generated_at=GENERATED_AT,
)
assert report.digest_status == "blocked"
assert "selection_summary_trend_gate_blocked" in report.reason_codes
```

If updating DB row tests, add a report with the new source and assert `to_db_row`/`from_db_row` round-trips without floats.

- [ ] **Step 2: Run digest tests red**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest_db_row.py
```

Expected: fail because `selection_summary_trend_gate_report` is not accepted and source name is unknown.

- [ ] **Step 3: Implement digest source**

In `paper_autonomous_readiness_digest.py`, add:

```python
SELECTION_SUMMARY_TREND_GATE_SOURCE_NAME = "selection_summary_trend_gate"
```

Insert it after `AGREEMENT_TREND_GATE_SOURCE_NAME` and before `LEDGER_SOURCE_NAME` in both `SOURCE_NAMES` and `OPTIONAL_SOURCE_NAMES`.

Add builder argument:

```python
selection_summary_trend_gate_report: object | None = None,
```

Add optional report tuple after agreement trend gate and before ledger:

```python
(
    SELECTION_SUMMARY_TREND_GATE_SOURCE_NAME,
    selection_summary_trend_gate_report,
    "selection_summary_trend_gate_report",
),
```

- [ ] **Step 4: Run digest tests green**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest_db_row.py tests/test_paper_autonomous_readiness_digest_store.py
```

- [ ] **Step 5: Commit**

```bash
git add src/polymarket_alpha_lab/paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest.py tests/test_paper_autonomous_readiness_digest_db_row.py
git commit -m "feat: add selection summary trend gate readiness digest source"
```

---

### Task 4: Docs, Review, Verification, Push

**Files:**
- Modify: `docs/paper-autonomous-readiness-gate.md`
- Modify: `docs/strategy-recommendation-layer.md` if it lists probability selection gates.

- [ ] **Step 1: Update docs**

Mention `paper-probability-selection-summary-history-trend-gate` as a read-only, report-only command that uses local Supabase/Postgres probability selection summary history and contributes optional readiness digest evidence.

- [ ] **Step 2: Run focused tests**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_paper_probability_selection_summary_history_trend.py \
  tests/test_paper_probability_selection_summary_history_trend_gate.py \
  tests/test_cli_paper_probability_selection_summary_history_trend.py \
  tests/test_cli_paper_probability_selection_summary_history_trend_gate.py \
  tests/test_paper_autonomous_readiness_digest.py \
  tests/test_paper_autonomous_readiness_digest_db_row.py \
  tests/test_paper_autonomous_readiness_digest_store.py
```

- [ ] **Step 3: Run full verification**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
codegraph sync
```

- [ ] **Step 4: Opencode review**

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
```

Prompt requirements: review `origin/main..HEAD` for the probability selection summary history trend gate node; verify Phase 1 boundary, local Supabase/Postgres-only durable data, Decimal-only probabilities, readonly/report-only hard flags, redaction, readiness digest source ordering, and no migration unless required.

- [ ] **Step 5: Push**

```bash
git push origin main
```
