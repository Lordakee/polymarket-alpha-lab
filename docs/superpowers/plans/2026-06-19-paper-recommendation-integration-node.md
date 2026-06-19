# Paper Recommendation Integration Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pure, paper-only integration reducers that turn existing recommendation reducer outputs into reportable pipeline, bundle, trend, cost, and audit artifacts without touching live trading paths.

**Architecture:** Keep all new modules as supplied-input reducers. Each reducer owns its validation helpers, uses frozen dataclasses, validates hard safety flags, normalizes datetimes to UTC, and quantizes Decimal math to `0.000001`. The CLI, API clients, auth, wallet, signing, and order execution surfaces remain outside this node.

**Tech Stack:** Python dataclasses, Decimal, pytest, CodeGraph, GitHub push after full verification.

---

## Scope

This node is limited to pure reducer/report code and documentation. The work may create independent modules under `src/polymarket_alpha_lab/` and matching tests under `tests/`, but it must not wire those modules into live execution, authenticated clients, or exchange mutation code.

The intended reducer family:

- `paper_recommendation_pipeline`: stage-level report status and count aggregation.
- `paper_recommendation_cycle_bundle`: immutable cycle artifact summary over supplied reports.
- `paper_recommendation_pipeline_trend`: trend summary across pipeline or bundle reports.
- `paper_external_cost_assumptions`: caller-supplied deposit, withdrawal, network, settlement, and opportunity-cost assumptions.
- `paper_fee_schedule`: caller-supplied protocol fee schedule assumptions.
- `paper_recommendation_decision_ledger`: row-level decision audit trail.
- `paper_recommendation_artifact_index`: canonical index over supplied report-like artifacts.
- `paper_recommendation_score_explanation`: supplied-input score component explanation.

## Invariants

- [ ] Every public dataclass is `@dataclass(frozen=True)`.
- [ ] Every report-like dataclass has `paper_only=True`, `report_only=True`, and `readonly=True` defaults.
- [ ] Every reducer validates hard flags with identity checks, not truthiness.
- [ ] Every Decimal input is a real `Decimal`, finite, and quantized or normalized to `0.000001`.
- [ ] Every `generated_at` is an exact `datetime`, normalized to UTC.
- [ ] Every status reducer uses explicit precedence: blocked first, watch second, pass last, unless the local reducer documents a stricter status vocabulary.
- [ ] No reducer imports CLI, live trading, auth, wallet, signing, real order, exchange mutation, network, or HTTP clients.

## Parallel Work Allocation

- [ ] **Worker A:** create `paper_recommendation_pipeline.py` and `tests/test_paper_recommendation_pipeline.py`.
- [ ] **Worker B:** create `paper_recommendation_cycle_bundle.py` and `tests/test_paper_recommendation_cycle_bundle.py`.
- [ ] **Worker C:** create `paper_recommendation_pipeline_trend.py` and `tests/test_paper_recommendation_pipeline_trend.py`.
- [ ] **Worker D:** create documentation for the pipeline and bundle stage.
- [ ] **Worker E:** create integration boundary/scope tests for the new modules.
- [ ] **Worker G:** create `paper_external_cost_assumptions.py` and matching tests.
- [ ] **Worker H:** create `paper_recommendation_decision_ledger.py` and matching tests.
- [ ] **Worker I:** create `paper_fee_schedule.py` and matching tests.
- [ ] **Worker J:** create `paper_recommendation_artifact_index.py` and matching tests.
- [ ] **Worker K:** create `paper_recommendation_score_explanation.py` and matching tests.

## Verification Gate

- [ ] Run focused tests for all newly added modules.
- [ ] Run `.venv/bin/python -m pytest -q`.
- [ ] Run `.venv/bin/python -m compileall -q src tests`.
- [ ] Run `git diff --check`.
- [ ] Run a source boundary scan over touched pure reducer modules for live/auth/wallet/signing/order/network/API mutation terms.
- [ ] Run `codegraph sync`.
- [ ] Request Claude Code audit with `claude-opus-4-8` and max thinking. If Claude fails twice, use OpenCode with `zhipuai-coding-plan/glm-5.2` and max thinking.
- [ ] Commit and push only after the verification gate is clean and the audit has no blocking findings.

## External Cost Notes

As of the current public Polymarket documentation check, the reducer layer should treat the following as supplied assumptions instead of fetched facts:

- Protocol taker fee rate and maker fee/rebate schedule.
- Deposit, withdrawal, bridge, network, and settlement-related costs.
- Opportunity cost for locked collateral and pending settlements.
- Any broker, exchange, or intermediary fees outside Polymarket itself.

These assumptions should feed the paper recommendation pipeline as explicit inputs so strategy comparisons can subtract fees and friction before allocating paper notional.
