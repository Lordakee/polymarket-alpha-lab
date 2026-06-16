# Project Screening v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only, report-only screening layer that turns supplied Cost-Aware Event Strategy reports into a deterministic human research queue.

**Architecture:** Implement one focused `project_screening.py` module that consumes already-built `PaperCostAwareEventStrategyReport` values. It computes queue buckets and screening scores with `Decimal`, persists append-only JSONL reports, and exposes no live data, wallet, account, client, order, ranking, recommendation, or advice surface.

**Tech Stack:** Python stdlib, dataclasses, Decimal, pytest, CodeGraph.

---

## File Structure

- Create `src/polymarket_alpha_lab/project_screening.py`
  - Dataclasses, validation helpers, score math, bucket assignment, report builder, and JSONL log.
- Create `tests/test_project_screening.py`
  - Behavior, validation, deterministic queue sequencing, immutability, and JSONL tests.
- Create `tests/test_project_screening_scope.py`
  - Static AST scope tests for imports, public exports, forbidden live/advice surfaces, and README boundaries.
- Modify `src/polymarket_alpha_lab/__init__.py`
  - Package-root exports for the new public API.
- Modify `tests/test_init.py`
  - Root export assertions.
- Modify `README.md`
  - Scope and Python API documentation for the new screening primitive.
- Modify this plan after implementation
  - Record RED, verification, review, commit, and push evidence.

## Task 1: Behavior RED Tests

**Files:**
- Create: `tests/test_project_screening.py`

- [x] **Step 1: Write failing tests for research queue scoring**

Add tests that import the intended public API and assert:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningConfig,
    PaperProjectScreeningLog,
    PaperProjectScreeningReport,
    build_paper_project_screening_report,
)


def test_project_screening_builds_research_queue_from_cost_aware_reports():
    ready = cost_aware_report(
        slug="fed-cut-june-2026",
        status_inputs="ready",
        fair_probability_yes=Decimal("0.6200"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("250.0000"),
    )
    watch = cost_aware_report(
        slug="inflation-above-three-2026",
        status_inputs="watch",
        fair_probability_yes=Decimal("0.5600"),
        yes_ask=Decimal("0.5500"),
        yes_ask_size=Decimal("50.0000"),
        min_net_edge=Decimal("0.0200"),
    )

    report = build_paper_project_screening_report(
        (watch, ready),
        config=PaperProjectScreeningConfig(config_version="project-screening-v1"),
        generated_at=datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
    )

    assert isinstance(report, PaperProjectScreeningReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert tuple(item.market_slug for item in report.queue_items) == (
        "fed-cut-june-2026",
        "inflation-above-three-2026",
    )
    assert report.queue_items[0].research_bucket == "research_ready"
    assert report.queue_items[1].research_bucket == "watch"
```

Also add tests for deterministic score math, blocked/defer buckets, duplicate slug validation, explicit type validation, frozen dataclasses, and JSONL serialization.

- [x] **Step 2: Run RED behavior tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_project_screening.py -q
```

Expected: import failure because `polymarket_alpha_lab.project_screening` does not exist yet.

## Task 2: Scope RED Tests

**Files:**
- Create: `tests/test_project_screening_scope.py`
- Modify later: `README.md`

- [x] **Step 1: Write failing static scope tests**

The tests must parse `src/polymarket_alpha_lab/project_screening.py` and assert:

- Imports are limited to `__future__`, `json`, `dataclasses`, `datetime`, `decimal`, `pathlib`, `typing`, and `polymarket_alpha_lab.cost_aware_event_strategy`.
- Forbidden imports include `requests`, `httpx`, `aiohttp`, `web3`, `eth_account`, `py_clob_client`, `polymarket`, `selenium`, `playwright`, `socket`, `ssl`, `subprocess`, and first-party live/data modules.
- Public exports exactly match the seven API names in the design spec.
- Public names do not contain account, auth, wallet, credential, client, transport, browser, websocket, broker, execution, order, rank, ranking, recommend, recommendation, investment, advice, or live surfaces.
- README contains a Project Screening v0 section with paper-only/report-only boundaries.

- [x] **Step 2: Run RED scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_project_screening_scope.py -q
```

Expected: failure because the module and README section do not exist yet.

## Task 3: Production Module

**Files:**
- Create: `src/polymarket_alpha_lab/project_screening.py`

- [x] **Step 1: Implement frozen dataclasses and validation helpers**

Create:

- `PaperProjectScreeningConfig`
- `PaperProjectScreeningCandidate`
- `PaperProjectScreeningGateResult`
- `PaperProjectScreeningQueueItem`
- `PaperProjectScreeningReport`
- `PaperProjectScreeningLog`

Use `Decimal` for weights, thresholds, scores, and sizes. Reject floats. Normalize datetimes to UTC. Enforce `paper_only is True` and `report_only is True`.

- [x] **Step 2: Implement candidate extraction and score math**

For each source `PaperCostAwareEventStrategyReport`, choose the scoring side:

```text
if selected_side is yes/no:
  use that side
else:
  use the valid-depth side with highest net_edge_per_share when available
```

Then compute:

```text
edge_component = net_edge_per_share * net_edge_weight
confidence_component = confidence * confidence_weight
depth_component = min(ask_size / reference_ask_size, 1) * depth_weight
spread_penalty = spread * spread_penalty_weight
resolution_penalty = resolution_risk * resolution_risk_penalty_weight
cost_penalty = total_cost_per_share * cost_penalty_weight
screening_score = edge + confidence + depth - spread - resolution - cost
```

Quantize scores with a declared score quantum.

- [x] **Step 3: Implement bucket assignment and queue sequencing**

Assign:

```text
research_ready = source status paper_review_ready and score >= min_screening_score
watch = source status watch, or valid-depth positive net edge with score below min_screening_score
defer = source status blocked_by_cost/no_paper_edge, or no positive valid-depth net edge
blocked = source status blocked_by_inputs/blocked_by_risk or invalid source report
```

Sequence queue items by bucket priority, descending screening score, then market slug. This is a research queue sequence, not an investment ranking.

- [x] **Step 4: Implement JSONL append**

`PaperProjectScreeningLog.append(report)` must validate the report tree, serialize Decimals as strings, and append one JSON object per line without reading existing files.

- [x] **Step 5: Run behavior tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_project_screening.py -q
```

Expected: pass.

## Task 4: Exports And README

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [x] **Step 1: Add package-root imports and `__all__` entries**

Add all seven new public API names to `src/polymarket_alpha_lab/__init__.py`.

- [x] **Step 2: Add root export test**

Add a `test_project_screening_public_api_exports` function to `tests/test_init.py` asserting each package-root export is the same object as the module-level import.

- [x] **Step 3: Add README section**

Add sections:

- `## Project Screening v0 Status`
- `## Project Screening v0 Python API`

The text must state that v0 is paper-only/report-only, consumes already-built Cost-Aware Event Strategy reports, builds a deterministic human research queue, and does not fetch data, authenticate, handle wallets/private keys, use account automation, place orders, rank investments, recommend trades, or provide financial advice.

- [x] **Step 4: Run export/scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_project_screening_scope.py -q
```

Expected: pass.

## Task 5: Full Verification And Review

**Files:**
- Modify this plan with the final evidence.

- [x] **Step 1: Focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_project_screening.py tests/test_project_screening_scope.py tests/test_init.py -q
```

- [x] **Step 2: Full tests**

Run:

```bash
.venv/bin/python -m pytest -q
```

- [x] **Step 3: Static checks**

Run:

```bash
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests
codegraph sync
codegraph status .
```

- [x] **Step 4: Claude review**

Run a read-only review with:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk
```

Prompt Claude to report Critical, Important, Minor, and Proceed/Block for the Project Screening v0 diff.

Evidence recorded before commit:

- RED behavior tests:
  - `.venv/bin/python -m pytest tests/test_project_screening.py -q`
  - Initial result: failed because `polymarket_alpha_lab.project_screening` did not exist.
- RED scope tests:
  - `.venv/bin/python -m pytest tests/test_project_screening_scope.py -q`
  - Initial result: failed because the module, package-root exports, and README sections did not exist.
- Review RED tests:
  - Added depth-gate regression; initial result failed because project screening treated positive size below source `min_ask_size` as valid depth.
  - Added queue/candidate consistency regression; initial result failed because mismatched queue items were accepted.
  - Added blocked-source status regression; initial result failed because blocked-with-edge candidates could report `screening_watch`.
  - Added bucket/status consistency regression; initial result failed because queue bucket changes were not cross-validated against candidate status.
- Focused tests:
  - `.venv/bin/python -m pytest tests/test_project_screening.py tests/test_project_screening_scope.py tests/test_init.py -q`
  - Final result: `50 passed in 0.50s`.
- Full tests:
  - `.venv/bin/python -m pytest -q`
  - Final result: `866 passed in 6.66s`.
- Static checks:
  - `git diff --check`: exit 0, no output.
  - `rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----" README.md docs src tests`: exit 1, no matches.
  - `codegraph sync`: already up to date.
  - `codegraph status .`: index up to date, 94 files, 3,638 nodes, 11,414 edges.
- Claude review:
  - Command form: `claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --no-session-persistence --tools ""` with full `git diff --cached` on stdin.
  - Final verdict: Proceed.
  - Critical: None.
  - Important: None.
  - Minor: naming/documentation observations only; no functional or scope defects.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add README.md docs src tests
git commit -m "feat: add project screening v0"
git push origin main
git status --short --branch
git ls-remote origin main
```

Expected: working tree clean, remote `main` points at local `HEAD`.
