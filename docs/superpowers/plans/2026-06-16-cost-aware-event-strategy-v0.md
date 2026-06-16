# Cost-Aware Event Strategy v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only, report-only evaluator that computes cost-adjusted YES/NO event-contract edge from supplied Polymarket probability, executable prices, depth, and cost assumptions.

**Architecture:** Implement one focused module, `cost_aware_event_strategy.py`, with frozen dataclasses, Decimal-only arithmetic, deterministic gates, and optional append-only JSONL persistence. The module consumes caller-supplied snapshots and cost assumptions; it has no live data, wallet, account, SDK, browser, or order-placement surface.

**Tech Stack:** Python stdlib, dataclasses, Decimal, pytest, CodeGraph.

---

## File Structure

- Create `src/polymarket_alpha_lab/cost_aware_event_strategy.py`
  - Dataclasses, validation helpers, fee/cost math, report builder, and JSONL log.
- Create `tests/test_cost_aware_event_strategy.py`
  - Behavior, validation, immutability, and JSONL tests.
- Create `tests/test_cost_aware_event_strategy_scope.py`
  - Static AST scope tests for imports, public exports, forbidden live surfaces, and README boundaries.
- Modify `src/polymarket_alpha_lab/__init__.py`
  - Package-root exports for the new public API.
- Modify `tests/test_init.py`
  - Root export assertions.
- Modify `README.md`
  - Scope and Python API documentation for the new strategy primitive.
- Modify this plan after implementation
  - Record verification, review, commit, and push evidence.

## Task 1: Behavior RED Tests

**Files:**
- Create: `tests/test_cost_aware_event_strategy.py`

- [x] **Step 1: Write failing tests for core event-contract math**

Add tests that import the intended public API and assert:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventCostAssumptions,
    PaperCostAwareEventMarketSnapshot,
    PaperCostAwareEventStrategyConfig,
    build_paper_cost_aware_event_strategy_report,
)


def test_cost_aware_event_strategy_computes_yes_edge_from_yes_probability_and_yes_ask():
    report = build_paper_cost_aware_event_strategy_report(
        base_snapshot(fair_probability_yes=Decimal("0.6200"), yes_ask=Decimal("0.5500")),
        cost_assumptions=PaperCostAwareEventCostAssumptions(
            taker_fee_rate=Decimal("0.0200"),
            slippage_cost_per_share=Decimal("0.0010"),
            funding_cost_per_share=Decimal("0.0020"),
            finalization_cost_per_share=Decimal("0.0005"),
            time_cost_per_share=Decimal("0.0005"),
            risk_cost_per_share=Decimal("0.0010"),
        ),
        config=PaperCostAwareEventStrategyConfig(config_version="cost-aware-event-v1"),
        generated_at=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )

    assert report.yes_result.fair_probability == Decimal("0.6200")
    assert report.yes_result.executable_price == Decimal("0.5500")
    assert report.yes_result.gross_edge_per_share == Decimal("0.0700")
    assert report.yes_result.fee_cost_per_share == Decimal("0.004950")
    assert report.yes_result.total_cost_per_share == Decimal("0.009950")
    assert report.yes_result.net_edge_per_share == Decimal("0.060050")
    assert report.selected_side == "yes"
    assert report.status == "paper_review_ready"
```

Also add tests for NO complement math, net-edge side selection, cost-eroded `blocked_by_cost`, gate failures, validation, frozen dataclasses, and JSONL serialization.

- [x] **Step 2: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cost_aware_event_strategy.py -q
```

Expected: import failure because `polymarket_alpha_lab.cost_aware_event_strategy` does not exist yet.

## Task 2: Scope RED Tests

**Files:**
- Create: `tests/test_cost_aware_event_strategy_scope.py`
- Modify later: `README.md`

- [x] **Step 1: Write failing static scope tests**

The tests must parse `src/polymarket_alpha_lab/cost_aware_event_strategy.py` and assert:

- Imports are limited to `__future__`, `json`, `dataclasses`, `datetime`, `decimal`, `pathlib`, and `typing`.
- Forbidden imports include `requests`, `httpx`, `aiohttp`, `web3`, `eth_account`, `py_clob_client`, `polymarket`, `selenium`, `playwright`, `socket`, `ssl`, and first-party live/data modules.
- Public exports exactly match the eight API names in the design spec.
- Public names do not contain account, auth, wallet, credential, client, transport, browser, websocket, broker, execution, recommendation, ranking, order placement, or live surfaces.
- README contains a Cost-Aware Event Strategy section with paper-only/report-only boundaries.

- [x] **Step 2: Run RED scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cost_aware_event_strategy_scope.py -q
```

Expected: failure because the module and README section do not exist yet.

## Task 3: Production Module

**Files:**
- Create: `src/polymarket_alpha_lab/cost_aware_event_strategy.py`

- [x] **Step 1: Implement frozen dataclasses and validation helpers**

Create:

- `PaperCostAwareEventStrategyConfig`
- `PaperCostAwareEventCostAssumptions`
- `PaperCostAwareEventMarketSnapshot`
- `PaperCostAwareEventStrategyGateResult`
- `PaperCostAwareEventSideResult`
- `PaperCostAwareEventStrategyReport`
- `PaperCostAwareEventStrategyLog`

Use `Decimal` only for numeric probability, price, size, ratio, and cost fields. Reject floats. Normalize datetimes to UTC. Enforce `paper_only is True` and `report_only is True`.

- [x] **Step 2: Implement cost and side math**

For each side:

```text
YES fair value = fair_probability_yes
NO fair value = 1 - fair_probability_yes
gross_edge = fair value - executable ask
fee_cost_per_share = taker_fee_rate * executable ask * (1 - executable ask)
total_cost_per_share = fee + slippage + funding + finalization + time + risk
net_edge_per_share = gross_edge - total_cost_per_share
```

Quantize fee/net values deterministically with a declared cost quantum. Use the ask and ask depth for buy-side paper evaluation. Do not use midpoint for entry math.

- [x] **Step 3: Implement gate/status selection**

Use stable gate order:

```text
data_integrity, confidence, spread, resolution_risk, yes_depth, no_depth, edge_threshold
```

Select the valid side with the highest net edge when it clears `min_net_edge`. Return `watch`, `blocked_by_inputs`, `blocked_by_risk`, `blocked_by_cost`, or `no_paper_edge` otherwise.

- [x] **Step 4: Implement JSONL append**

`PaperCostAwareEventStrategyLog.append(report)` must validate the report tree, serialize Decimals as strings, and append one JSON object per line without reading existing files.

- [x] **Step 5: Run behavior tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cost_aware_event_strategy.py -q
```

Expected: pass.

## Task 4: Exports And README

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [x] **Step 1: Add package-root imports and `__all__` entries**

Add all eight new public API names to `src/polymarket_alpha_lab/__init__.py`.

- [x] **Step 2: Add root export test**

Add a `test_cost_aware_event_strategy_public_api_exports` function to `tests/test_init.py` asserting each package-root export is the same object as the module-level import.

- [x] **Step 3: Add README section**

Add sections:

- `## Cost-Aware Event Strategy v0 Status`
- `## Cost-Aware Event Strategy v0 Python API`

The text must state that v0 is paper-only/report-only, consumes caller-supplied inputs, uses executable YES/NO ask prices, models taker fees and explicit non-fee costs, and does not fetch data, authenticate, handle wallets/private keys, use account automation, place orders, rank investments, recommend trades, or provide financial advice.

- [x] **Step 4: Run export/scope tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py tests/test_cost_aware_event_strategy_scope.py -q
```

Expected: pass.

## Task 5: Full Verification And Review

**Files:**
- Modify this plan with the final evidence.

- [x] **Step 1: Focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cost_aware_event_strategy.py tests/test_cost_aware_event_strategy_scope.py tests/test_init.py -q
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

Prompt Claude to report Critical, Important, Minor, and Proceed/Block for the cost-aware event strategy diff.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add README.md docs src tests
git commit -m "feat: add cost-aware event strategy v0"
git push origin main
git status --short --branch
git ls-remote origin main
```

Expected: working tree clean, remote `main` points at local `HEAD`.

## Verification Evidence

- Behavior tests were written before production implementation. Initial RED runs failed because `polymarket_alpha_lab.cost_aware_event_strategy` did not exist. Later RED review tests failed for unreachable `watch`, zero-depth handling, omitted non-fee costs, mixed watch/cost status priority, invalid-depth watch candidates, and missing bid audit fields before the implementation was updated.
- Focused verification: `.venv/bin/python -m pytest tests/test_cost_aware_event_strategy.py tests/test_cost_aware_event_strategy_scope.py tests/test_init.py -q` -> `64 passed`.
- Full verification: `.venv/bin/python -m pytest -q` -> `841 passed`.
- Static verification: `git diff --check` -> pass.
- Secret scan over `README.md docs src tests` for GitHub/OpenAI/AWS/private-key patterns -> no matches.
- CodeGraph verification: `codegraph sync && codegraph status .` -> index up to date.
- Subagent review found and the implementation fixed: `watch` status ordering, zero depth, explicit non-fee costs, aggregate `edge_threshold` spec wording, mixed watch/cost priority, invalid-depth watch candidates, and bid audit retention.
- Final Claude review with `claude-opus-4-8` and `--effort max` reported no Critical or Important findings and `Assessment: Proceed`.
