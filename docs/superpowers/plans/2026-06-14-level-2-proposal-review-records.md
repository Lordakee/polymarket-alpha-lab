# Level 2 Proposal Review Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 2 proposal-review record artifacts that capture an explicit human decision over a `TradeProposalPacket` without creating an approval workflow, broker handoff, execution request, or live-order surface.

**Architecture:** Add a new `proposal_review.py` derived-artifact layer. It consumes one caller-supplied `TradeProposalPacket`, caller-supplied human review fields, and caller-supplied review config, then emits frozen dataclasses and optional append-only JSONL. The module records a human review decision only; it does not fetch data, authenticate, handle credentials, build broker/order requests, import manual executions, manage approval queues, or place orders.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, deterministic SHA-256 ids, JSONL, pytest, CodeGraph, Claude Code reviews with `claude-opus-4-8` and effort `max`.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement until Claude returns `Proceed` or `Proceed with fixes` with zero Critical findings and zero Important findings.
3. Use TDD for implementation:
   - Write focused failing tests first.
   - Run the focused test and capture the expected failure.
   - Implement the minimum code.
   - Rerun the focused test and capture the pass.
4. Use parallel agents only with non-overlapping write ownership:
   - Functional-test worker owns `tests/test_proposal_review.py`.
   - Scope/export-test worker owns `tests/test_proposal_review_scope.py`, root-export migrations in existing scope tests, and `tests/test_init.py`.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_review.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
   - Codex subagents use model `gpt-5.5` with reasoning effort `xhigh`, matching `AGENTS.md`.
5. Do not let two agents edit the same file or same tightly coupled file batch at the same time.
6. Close completed subagents promptly, then redeploy only to a fresh independent task.
7. Before commit, run fresh verification and a self-contained Claude implementation review covering all modified and untracked files.
8. Resolve every Critical or Important implementation-review finding before staging for final commit.
9. Append a Handoff Summary to this plan before final commit.
10. Commit and push only after all gates pass.

## Plan Review Command Before Any Implementation

Run this exact self-contained command before implementation:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-review-records implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-review record boundary, explicit human decision semantics, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, source TradeProposalPacket validation, Gate 6 packet-review preservation, review attestation, deterministic ids, Decimal and UTC validation, JSONL validate-before-open behavior, public API/export surface, old root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
  printf '%s\n' 'Before the final verdict line, report finding counts exactly as:'
  printf '%s\n' 'Critical findings: <integer>'
  printf '%s\n' 'Important findings: <integer>'
  printf '%s\n' 'Minor findings: <integer>'
  printf '%s\n' 'Use 0 for empty categories; do not use "none" in count fields.'
  printf '%s\n' 'Finish with exactly one verdict line: Verdict: Proceed | Proceed with fixes | Blocked.'
  printf '%s\n' ''
  printf '%s\n' 'Repository instructions:'
  cat AGENTS.md
  printf '%s\n' ''
  printf '%s\n' 'Relevant Level 2 roadmap and validation gate context:'
  sed -n '70,115p' docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  sed -n '97,130p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current proposal packet source contract:'
  codegraph node src/polymarket_alpha_lab/proposal_packet.py
  codegraph node tests/test_proposal_packet.py
  printf '%s\n' ''
  printf '%s\n' 'Current package root and export tests:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Current scope tests that must be migrated safely:'
  codegraph node tests/test_proposal_packet_scope.py
  sed -n '1,340p' tests/test_analytics_scope.py
  sed -n '1,340p' tests/test_analytics_history_scope.py
  sed -n '1,340p' tests/test_forecast_evidence_scope.py
  sed -n '1,365p' tests/test_manual_review_queue_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6 and Gate 7 excerpts, fresh git status, the full `TradeProposalPacket` public contract, current package-root exports, current export tests, all root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 2 Scope

Level 2 Node 2 adds append-only proposal-review record artifacts over supplied `TradeProposalPacket` values. A proposal-review record captures a caller-supplied human review decision, reviewer label, rationale, reason codes, attestation, proposal identity, and proposal evidence snapshot for audit only. It is not a trade instruction, order instruction, broker request, order request, account action, approval workflow engine, approval queue, approval router, strategy-promotion signal, or live-execution signal.

The module must:

- Consume exactly one caller-supplied `TradeProposalPacket`.
- Reconstruct and validate the supplied proposal before deriving review fields.
- Require that the source proposal is proposal-only, requires human approval, is paper-review-ready, has no hard blocks, has no blocking reason codes, and has no failed history/forecast gates.
- Consume caller-supplied review values:
  - `decision`
  - `reviewer_label`
  - `review_rationale`
  - `review_reason_codes`
  - `human_attestation`
  - `config`
  - `recorded_at`
- Support exactly two review decisions:
  - `approved`
  - `rejected`
- Store `explicit_human_decision=True` to distinguish the artifact from automated scoring.
- Store `record_only=True`.
- Require `human_attestation` to equal the configured required attestation text.
- Copy enough Gate 6 and proposal audit fields to review the decision without opening the proposal packet log.
- Emit frozen `TradeProposalReviewRecord` values.
- Persist record snapshots through `TradeProposalReviewLog(path).append(record)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Add an approval workflow engine, approval queue, approval router, approver registry, role-based permissions, reviewer authentication, or identity verification.
- Convert approvals into order instructions, order requests, broker requests, execution decisions, order lifecycle states, or strategy-promotion signals.
- Import manual execution journals or manual execution results.
- Fetch market, order-book, price-history, outcome, account, credential, or identity data.
- Read JSONL logs or external history.
- Scrape websites, run browser automation, bypass anti-bot controls, or handle CAPTCHA.
- Authenticate, handle credentials, handle private keys, sign messages, use wallets, or use trading SDKs.
- Create broker clients, transport clients, request payloads, response objects, sessions, WebSockets, heartbeats, reconciliation, settlement, or account-state surfaces.
- Place, submit, sign, send, create, or cancel orders.
- Add CLI, UI, dashboard, scheduler, notification, compliance, legal, jurisdiction, geofence, KYC, AML, sanctions, or geographic-access analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/proposal_review.py`
- `tests/test_proposal_review.py`
- `tests/test_proposal_review_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
- `tests/test_init.py`
- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`
- `README.md`

Do not modify:

- `src/polymarket_alpha_lab/api.py`
- `src/polymarket_alpha_lab/archive.py`
- `src/polymarket_alpha_lab/cli.py`
- `src/polymarket_alpha_lab/pipeline.py`
- `src/polymarket_alpha_lab/scoring.py`
- `src/polymarket_alpha_lab/research.py`
- `src/polymarket_alpha_lab/risk.py`
- `src/polymarket_alpha_lab/paper.py`
- `src/polymarket_alpha_lab/journal.py`
- `src/polymarket_alpha_lab/positions.py`
- `src/polymarket_alpha_lab/analytics.py`
- `src/polymarket_alpha_lab/analytics_history.py`
- `src/polymarket_alpha_lab/forecast_evidence.py`
- `src/polymarket_alpha_lab/manual_review_queue.py`
- `src/polymarket_alpha_lab/proposal_packet.py`

## Public API Contract

`src/polymarket_alpha_lab/proposal_review.py` must export exactly:

```python
__all__ = (
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
)
```

### Boundary And Attestation Text

`DEFAULT_REVIEW_ATTESTATION` must be exactly:

```python
(
    "I reviewed this proposal packet and understand this record is not a "
    "trade instruction, order instruction, broker request, order request, "
    "account action, account authentication, private-key handling, wallet "
    "signature, live-execution signal, manual execution import, credential "
    "request, or automatic order-placement authorization."
)
```

`DEFAULT_REVIEW_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a record-only human-review decision artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, or automatic order-placement authorization."
)
```

Boundary statement validation must require these lowercase substrings:

- `record-only`
- `human-review decision`
- `not an approval workflow`
- `trade instruction`
- `order instruction`
- `broker request`
- `order request`
- `account action`
- `account authentication`
- `private-key handling`
- `wallet signature`
- `live-execution signal`
- `credential workflow`
- `manual execution import`
- `automatic order-placement authorization`

Attestation validation must require exact equality with `TradeProposalReviewConfig.required_human_attestation`.

### TradeProposalReviewConfig

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewConfig:
    config_version: str
    allowed_decisions: tuple[str, ...] = ("approved", "rejected")
    required_human_attestation: str = DEFAULT_REVIEW_ATTESTATION
    boundary_statement: str = DEFAULT_REVIEW_BOUNDARY_STATEMENT
```

Validation:

- `config_version`, `required_human_attestation`, and `boundary_statement` must be canonical nonblank strings.
- `allowed_decisions` must be a tuple of canonical strings whose normalized set is exactly `{"approved", "rejected"}`.
- `boundary_statement` must satisfy the boundary statement contract above.

### TradeProposalReviewRecord

Fields:

```python
@dataclass(frozen=True)
class TradeProposalReviewRecord:
    review_record_id: str
    recorded_at: datetime
    review_config_version: str
    record_only: bool
    explicit_human_decision: bool
    boundary_statement: str
    source_proposal_packet_id: str
    source_proposal_generated_at: datetime
    source_proposal_config_version: str
    source_proposal_fingerprint: str
    source_proposal_boundary_statement: str
    source_queue_boundary_statement: str
    source_proposal_only: bool
    source_human_approval_required: bool
    source_queue_item_id: str
    source_queue_rank: int
    source_manual_review_status: str
    source_packet_id: str
    source_paper_only: bool
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    side: str
    intended_order_type: str
    executable_price_assumption: Decimal
    maximum_size: Decimal
    source_max_executable_size: Decimal
    cost_adjusted_edge: Decimal
    theoretical_edge: Decimal | None
    fair_value_estimate: Decimal | None
    model_probability: Decimal | None
    confidence: Decimal | None
    source_score: Decimal
    market_score_total: Decimal | None
    exposure_after_trade: Decimal
    exit_rule: str
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    risk_tags: tuple[str, ...]
    reason_trade_could_be_wrong: str
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    evidence_scope: str
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    risk_gate_passed: bool
    hard_block_count: int
    blocking_reason_codes: tuple[str, ...]
    decision: str
    reviewer_label: str
    review_rationale: str
    review_reason_codes: tuple[str, ...]
    human_attestation: str
```

Validation:

- `recorded_at` and `source_proposal_generated_at` are normalized to UTC.
- `review_record_id` must equal the deterministic id derived from record fields.
- `source_proposal_fingerprint` must equal the deterministic fingerprint derived from copied proposal fields.
- `record_only` must be `True`.
- `explicit_human_decision` must be `True`.
- `source_proposal_only` must be `True`.
- `source_human_approval_required` must be `True`.
- `source_paper_only` must be `True`.
- `source_proposal_boundary_statement` must be canonical nonblank text satisfying the proposal packet boundary contract; the builder must copy it from `proposal.boundary_statement`.
- `source_queue_boundary_statement` must be canonical nonblank text; the builder must copy it from `proposal.source_boundary_statement`.
- `source_manual_review_status` must be `paper_review_ready`.
- `risk_gate_passed` must be `True`.
- `hard_block_count` must be zero.
- `blocking_reason_codes` must be empty.
- `history_status` and `forecast_status` must be `paper_review_ready`.
- `history_gate_fail_count` and `forecast_gate_fail_count` must be zero.
- `decision` must be `approved` or `rejected`.
- `review_reason_codes` must be a nonempty tuple of canonical strings when `decision == "rejected"`.
- `review_reason_codes` must be empty when `decision == "approved"`.
- `human_attestation` must be canonical nonblank text and match the config during build.
- `reviewer_label` and `review_rationale` must be canonical nonblank text.
- `source_queue_item_id` must match `condition_id:token_id:source_packet_id`.
- `source_queue_rank` must be positive.
- `side` must be `buy` or `sell`.
- `intended_order_type` must be canonical nonblank text.
- `executable_price_assumption`, `fair_value_estimate`, `model_probability`, and `confidence` values must be within the inclusive binary range from `0` to `1` when present.
- `executable_price_assumption` must be positive and less than `1`.
- `maximum_size` and `source_max_executable_size` must be finite positive `Decimal` values.
- `source_score` must be a finite nonnegative `Decimal`.
- `maximum_size` must be less than or equal to `source_max_executable_size`.
- `cost_adjusted_edge`, `theoretical_edge`, `market_score_total`, and `exposure_after_trade` must be finite `Decimal` values when present.
- `cost_adjusted_edge` and `exposure_after_trade` must be nonnegative.
- Gate 6 strings `market_url`, `thesis`, `invalidating_conditions`, `rule_text_hash`, `resolution_source`, `exit_rule`, and `reason_trade_could_be_wrong` must be canonical nonblank strings.
- Copied source identity and market strings `condition_id`, `token_id`, `market_slug`, `question`, `outcome_name`, `strategy_type`, `source_packet_id`, and `source_manual_review_status` must be canonical nonblank strings.
- `risk_tags` must be a nonempty tuple of canonical strings.
- `review_focus` must be a nonempty tuple of canonical strings.
- `supporting_reason_codes` must be a tuple of canonical strings.
- `why_in_queue`, `primary_reason_code`, and `evidence_scope` must be canonical nonblank strings.
- `boundary_statement` must satisfy the boundary contract above.

### Builder Contract

```python
def build_trade_proposal_review_record(
    proposal: TradeProposalPacket,
    *,
    decision: str,
    reviewer_label: str,
    review_rationale: str,
    review_reason_codes: Iterable[str] = (),
    human_attestation: str,
    config: TradeProposalReviewConfig,
    recorded_at: datetime,
) -> TradeProposalReviewRecord:
    ...
```

Builder behavior:

- Reject non-`TradeProposalPacket` source values.
- Reconstruct and validate the source proposal before copying fields.
- Reject non-`TradeProposalReviewConfig` config values.
- Normalize `recorded_at` to UTC.
- Require `decision` to be in `config.allowed_decisions`.
- Require `human_attestation == config.required_human_attestation`.
- Copy source proposal fields exactly, except datetimes normalized to UTC and tuples normalized to tuples.
- Compute `source_proposal_fingerprint` from a canonical JSON representation of these exact copied source proposal fields:
  - `source_proposal_packet_id`
  - `source_proposal_generated_at`
  - `source_proposal_config_version`
  - `source_proposal_boundary_statement`
  - `source_queue_boundary_statement`
  - `source_proposal_only`
  - `source_human_approval_required`
  - `source_queue_item_id`
  - `source_queue_rank`
  - `source_manual_review_status`
  - `source_packet_id`
  - `source_paper_only`
  - `condition_id`
  - `token_id`
  - `market_slug`
  - `market_url`
  - `question`
  - `outcome_name`
  - `strategy_type`
  - `side`
  - `intended_order_type`
  - `executable_price_assumption`
  - `maximum_size`
  - `source_max_executable_size`
  - `cost_adjusted_edge`
  - `theoretical_edge`
  - `fair_value_estimate`
  - `model_probability`
  - `confidence`
  - `source_score`
  - `market_score_total`
  - `exposure_after_trade`
  - `exit_rule`
  - `thesis`
  - `invalidating_conditions`
  - `rule_text_hash`
  - `resolution_source`
  - `risk_tags`
  - `reason_trade_could_be_wrong`
  - `readiness_summary`
  - `risk_summary`
  - `evidence_summary`
  - `why_in_queue`
  - `primary_reason_code`
  - `supporting_reason_codes`
  - `review_focus`
  - `evidence_scope`
  - `history_status`
  - `forecast_status`
  - `history_gate_pass_count`
  - `forecast_gate_pass_count`
  - `history_gate_fail_count`
  - `forecast_gate_fail_count`
  - `risk_gate_passed`
  - `hard_block_count`
  - `blocking_reason_codes`
- Compute `review_record_id` from:
  - `review_config_version`
  - UTC `recorded_at`
  - `source_proposal_packet_id`
  - `source_proposal_fingerprint`
  - `decision`
  - `reviewer_label`
  - `review_rationale`
  - `review_reason_codes` as a JSON array, not a joined string
  - `human_attestation`
- Build both `source_proposal_fingerprint` and `review_record_id` from canonical JSON objects serialized with `_json_ready(...)`, `sort_keys=True`, and compact separators `(",", ":")`.

### Log Contract

`TradeProposalReviewLog(path).append(record)`:

- Accepts only `TradeProposalReviewRecord`.
- Reconstructs and validates the record tree before serialization.
- Serializes with `json.dumps(..., allow_nan=False, sort_keys=True) + "\n"`.
- Uses append-only mode.
- Creates missing parent directories only after validation and serialization have succeeded.
- Revalidates the nearest existing parent before opening the file.
- Does not expose a reader, loader, updater, deleter, importer, exporter, dispatcher, or replay API.

## Task 1: Functional Tests

**Files:**
- Create: `tests/test_proposal_review.py`

- [ ] **Step 1: Write source proposal factories**

Duplicate the minimal fixture stack from `tests/test_proposal_packet.py` inside `tests/test_proposal_review.py`. Do not import from another test module.

The new file starts with these imports:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.analytics_history import (
    PaperAnalyticsHistoryGateResult,
    PaperAnalyticsHistoryReport,
    PaperAnalyticsHistoryTrend,
)
from polymarket_alpha_lab.domain import MarketScore
from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.manual_review_queue import (
    PaperManualReviewCandidate,
    PaperManualReviewConfig,
    PaperManualReviewQueueItem,
    build_paper_manual_review_queue,
)
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacketConfig,
    build_trade_proposal_packet,
)
from polymarket_alpha_lab.proposal_review import (
    TradeProposalReviewConfig,
    TradeProposalReviewLog,
    build_trade_proposal_review_record,
)
```

Add the same local fixture helper functions as `tests/test_proposal_packet.py`:

- `market_score(...)`
- `ready_history_report()`
- `forecast_observation(...)`
- `ready_forecast_report()`
- `candidate(...)`
- `ready_queue_item(...)`
- `proposal_packet(...)`

Use the same canonical proposal defaults:

```python
def proposal_packet(**overrides):
    values = {
        "queue_item": ready_queue_item(),
        "side": "buy",
        "intended_order_type": "limit",
        "maximum_size": Decimal("25"),
        "exposure_after_trade": Decimal("0.1200"),
        "exit_rule": "Exit if executable price reaches fair value or thesis invalidates.",
        "reason_trade_could_be_wrong": (
            "Liquidity could disappear before exit or the resolution source could "
            "clarify against the thesis."
        ),
        "config": TradeProposalPacketConfig(config_version="proposal-v1"),
        "generated_at": datetime(2026, 9, 3, 12, tzinfo=UTC),
    }
    values.update(overrides)
    return build_trade_proposal_packet(**values)
```

- [ ] **Step 2: Write the first failing approval-record test**

Append:

```python
def review_record(**overrides):
    values = {
        "proposal": proposal_packet(),
        "decision": "approved",
        "reviewer_label": "human-reviewer-1",
        "review_rationale": (
            "Approved after checking the packet evidence and exit liquidity constraints."
        ),
        "review_reason_codes": (),
        "human_attestation": (
            "I reviewed this proposal packet and understand this record is not a "
            "trade instruction, order instruction, broker request, order request, "
            "account action, account authentication, private-key handling, wallet "
            "signature, live-execution signal, manual execution import, credential "
            "request, or automatic order-placement authorization."
        ),
        "config": TradeProposalReviewConfig(config_version="review-v1"),
        "recorded_at": datetime(2026, 9, 3, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_record(**values)


def test_build_trade_proposal_review_record_records_explicit_human_decision():
    packet = proposal_packet()

    record = review_record(proposal=packet)

    assert record.decision == "approved"
    assert record.record_only is True
    assert record.explicit_human_decision is True
    assert record.recorded_at == datetime(2026, 9, 3, 12, 30, tzinfo=UTC)
    assert record.source_proposal_packet_id == packet.proposal_packet_id
    assert record.source_proposal_generated_at == packet.generated_at
    assert record.source_proposal_config_version == packet.proposal_config_version
    assert record.source_proposal_boundary_statement == packet.boundary_statement
    assert record.source_queue_boundary_statement == packet.source_boundary_statement
    assert record.source_proposal_only is True
    assert record.source_human_approval_required is True
    assert record.source_queue_item_id == packet.source_queue_item_id
    assert record.source_queue_rank == packet.source_queue_rank
    assert record.source_manual_review_status == "paper_review_ready"
    assert record.source_packet_id == packet.source_packet_id
    assert record.source_paper_only is True
    assert record.condition_id == packet.condition_id
    assert record.token_id == packet.token_id
    assert record.market_slug == packet.market_slug
    assert record.market_url == packet.market_url
    assert record.question == packet.question
    assert record.outcome_name == packet.outcome_name
    assert record.strategy_type == packet.strategy_type
    assert record.side == packet.side
    assert record.intended_order_type == packet.intended_order_type
    assert record.executable_price_assumption == packet.executable_price_assumption
    assert record.maximum_size == packet.maximum_size
    assert record.source_max_executable_size == packet.source_max_executable_size
    assert record.cost_adjusted_edge == packet.cost_adjusted_edge
    assert record.theoretical_edge == packet.theoretical_edge
    assert record.fair_value_estimate == packet.fair_value_estimate
    assert record.model_probability == packet.model_probability
    assert record.confidence == packet.confidence
    assert record.source_score == packet.source_score
    assert record.market_score_total == packet.market_score_total
    assert record.exposure_after_trade == packet.exposure_after_trade
    assert record.exit_rule == packet.exit_rule
    assert record.thesis == packet.thesis
    assert record.invalidating_conditions == packet.invalidating_conditions
    assert record.rule_text_hash == packet.rule_text_hash
    assert record.resolution_source == packet.resolution_source
    assert record.risk_tags == packet.risk_tags
    assert record.reason_trade_could_be_wrong == packet.reason_trade_could_be_wrong
    assert record.readiness_summary == packet.readiness_summary
    assert record.risk_summary == packet.risk_summary
    assert record.evidence_summary == packet.evidence_summary
    assert record.why_in_queue == packet.why_in_queue
    assert record.primary_reason_code == packet.primary_reason_code
    assert record.supporting_reason_codes == packet.supporting_reason_codes
    assert record.review_focus == packet.review_focus
    assert record.evidence_scope == packet.evidence_scope
    assert record.history_status == packet.history_status
    assert record.forecast_status == packet.forecast_status
    assert record.history_gate_pass_count == packet.history_gate_pass_count
    assert record.forecast_gate_pass_count == packet.forecast_gate_pass_count
    assert record.history_gate_fail_count == packet.history_gate_fail_count
    assert record.forecast_gate_fail_count == packet.forecast_gate_fail_count
    assert record.risk_gate_passed == packet.risk_gate_passed
    assert record.hard_block_count == packet.hard_block_count
    assert record.blocking_reason_codes == packet.blocking_reason_codes
    assert record.review_reason_codes == ()
    assert "not an approval workflow" in record.boundary_statement
    assert "automatic order-placement authorization" in record.boundary_statement
```

- [ ] **Step 3: Run the first focused test and capture failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review.py::test_build_trade_proposal_review_record_records_explicit_human_decision -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.proposal_review'`.

- [ ] **Step 4: Add remaining functional tests**

Append focused tests covering:

- rejected review records with nonempty `review_reason_codes`
- deterministic and input-sensitive `review_record_id`
- deterministic and input-sensitive `source_proposal_fingerprint`
- invalid public inputs and config validation
- invalid source proposal packets mutated with `object.__setattr__`
- frozen dataclasses and invariant validation through `replace(...)`
- default boundary statement and weak boundary rejection
- source proposal boundary rejection and source queue boundary blank rejection through `replace(...)`
- UTC normalization
- JSONL append one row
- JSONL append twice without overwrite and nested parent creation
- invalid paths and invalid append inputs before file creation
- preserving an existing file when record validation fails
- rejecting non-finite Decimals before opening a new file

Use this deterministic approved canonical id expectation:

```python
assert record.review_record_id.startswith("review-")
assert len(record.review_record_id) == len("review-") + 24
```

Then assert black-box sensitivity without depending on a private helper:

```python
same_record = review_record()

assert same_record.review_record_id == record.review_record_id
assert same_record.source_proposal_fingerprint == record.source_proposal_fingerprint

same_instant_record = review_record(
    recorded_at=datetime(2026, 9, 3, 13, 30, tzinfo=timezone(timedelta(hours=1))),
)

assert same_instant_record.review_record_id == record.review_record_id
assert same_instant_record.source_proposal_fingerprint == record.source_proposal_fingerprint

variants = (
    review_record(config=TradeProposalReviewConfig(config_version="review-v2")),
    review_record(recorded_at=datetime(2026, 9, 3, 12, 31, tzinfo=UTC)),
    review_record(decision="rejected", review_reason_codes=("liquidity_exit_risk",)),
    review_record(reviewer_label="human-reviewer-2"),
    review_record(review_rationale="Approved after a separate human review pass."),
)
proposal_variants = (
    review_record(proposal=proposal_packet(generated_at=datetime(2026, 9, 3, 12, 1, tzinfo=UTC))),
    review_record(proposal=proposal_packet(maximum_size=Decimal("20"))),
)

assert {variant.review_record_id for variant in variants}.isdisjoint(
    {record.review_record_id},
)
assert {variant.source_proposal_fingerprint for variant in variants} == {
    record.source_proposal_fingerprint,
}
assert {variant.review_record_id for variant in proposal_variants}.isdisjoint(
    {record.review_record_id},
)
assert {variant.source_proposal_fingerprint for variant in proposal_variants}.isdisjoint(
    {record.source_proposal_fingerprint},
)
```

- [ ] **Step 5: Run the full functional test file and capture failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review.py -q
```

Expected: FAIL because implementation does not exist.

## Task 2: Core Implementation

**Files:**
- Create: `src/polymarket_alpha_lab/proposal_review.py`

- [ ] **Step 1: Add public dataclasses and builder skeleton**

Create `src/polymarket_alpha_lab/proposal_review.py` with:

```python
"""Record-only human-review decision artifacts for Level 2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_packet import TradeProposalPacket


__all__ = (
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
)
```

Add the two default strings exactly as specified in the public API contract.

- [ ] **Step 2: Implement dataclasses**

Add:

```python
@dataclass(frozen=True)
class TradeProposalReviewConfig:
    config_version: str
    allowed_decisions: tuple[str, ...] = ("approved", "rejected")
    required_human_attestation: str = DEFAULT_REVIEW_ATTESTATION
    boundary_statement: str = DEFAULT_REVIEW_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True)
class TradeProposalReviewRecord:
    # all fields listed in the Public API Contract

    def __post_init__(self) -> None:
        _validate_record(self)


@dataclass(frozen=True)
class TradeProposalReviewLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, record: TradeProposalReviewRecord) -> None:
        if not isinstance(record, TradeProposalReviewRecord):
            raise ValueError("record must be a TradeProposalReviewRecord")
        validated = _validate_record_tree(record)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
```

- [ ] **Step 3: Implement builder and source proposal cloning**

Add:

```python
def build_trade_proposal_review_record(
    proposal: TradeProposalPacket,
    *,
    decision: str,
    reviewer_label: str,
    review_rationale: str,
    review_reason_codes: Iterable[str] = (),
    human_attestation: str,
    config: TradeProposalReviewConfig,
    recorded_at: datetime,
) -> TradeProposalReviewRecord:
    source = _clone_proposal_packet(proposal)
    _validate_source_proposal(source)
    if type(config) is not TradeProposalReviewConfig:
        raise ValueError("config must be a TradeProposalReviewConfig")
    if not isinstance(recorded_at, datetime):
        raise ValueError("recorded_at must be a datetime")
    recorded_at = _as_utc(recorded_at)
    _require_canonical_string("decision", decision)
    if decision not in config.allowed_decisions:
        raise ValueError("decision is not allowed by config")
    _require_canonical_string("reviewer_label", reviewer_label)
    _require_canonical_string("review_rationale", review_rationale)
    _require_canonical_string("human_attestation", human_attestation)
    if human_attestation != config.required_human_attestation:
        raise ValueError("human_attestation must match required_human_attestation")
    reason_codes = _normalize_string_tuple("review_reason_codes", review_reason_codes)
    if decision == "approved" and reason_codes:
        raise ValueError("review_reason_codes must be empty when decision is approved")
    if decision == "rejected" and not reason_codes:
        raise ValueError("review_reason_codes are required when decision is rejected")
    fingerprint = _source_proposal_fingerprint(source)
    record_id = _review_record_id(
        config_version=config.config_version,
        recorded_at=recorded_at,
        source_proposal_packet_id=source.proposal_packet_id,
        source_proposal_fingerprint=fingerprint,
        decision=decision,
        reviewer_label=reviewer_label,
        review_rationale=review_rationale,
        review_reason_codes=reason_codes,
        human_attestation=human_attestation,
    )
    return TradeProposalReviewRecord(
        review_record_id=record_id,
        recorded_at=recorded_at,
        review_config_version=config.config_version,
        record_only=True,
        explicit_human_decision=True,
        boundary_statement=config.boundary_statement,
        # copy all source proposal fields listed in the contract
        decision=decision,
        reviewer_label=reviewer_label,
        review_rationale=review_rationale,
        review_reason_codes=reason_codes,
        human_attestation=human_attestation,
    )
```

The implementation must fill the omitted source-copy fields explicitly. Do not use dynamic `setattr` or dictionary unpacking for the public dataclass constructor.

- [ ] **Step 4: Implement validators and JSONL helpers**

Implement local helpers matching `proposal_packet.py` conventions:

- `_clone_proposal_packet`
- `_validate_source_proposal`
- `_validate_config`
- `_validate_record`
- `_validate_record_tree`
- `_source_proposal_fingerprint`
- `_review_record_id`
- `_json_ready`
- `_normalize_log_path`
- `_validate_log_parent`
- `_as_utc`
- `_require_canonical_string`
- `_require_boundary_statement`
- `_require_source_proposal_boundary_statement`
- `_normalize_string_tuple`
- `_require_positive_int`
- `_require_nonnegative_int`
- `_require_decimal`
- `_require_positive_decimal`
- `_require_nonnegative_decimal`
- `_require_optional_finite_decimal`
- `_require_probability`
- `_require_optional_probability`
- `_require_executable_price`

The source clone must reconstruct `TradeProposalPacket(...)` with every field copied explicitly so mutated frozen instances are revalidated before use.

- [ ] **Step 5: Run functional tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review.py -q
```

Expected: PASS.

## Task 3: Scope And Public Export Tests

**Files:**
- Create: `tests/test_proposal_review_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`
- Modify: `tests/test_proposal_packet_scope.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Add proposal-review scope tests**

Create `tests/test_proposal_review_scope.py` using the AST pattern from `tests/test_proposal_packet_scope.py`. Required constants:

```python
EXPECTED_PROPOSAL_REVIEW_EXPORTS = {
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
}
EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS | EXPECTED_PROPOSAL_REVIEW_EXPORTS
)
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.proposal_packet",
}
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.proposal_packet": {"TradeProposalPacket"},
}
```

Forbidden imports must include first-party modules other than `proposal_packet`, network libraries, browser/scraping libraries, account/signing libraries, storage/query libraries, and execution-like standard modules such as `subprocess`, `socket`, `urllib`, `http`, and `os`.

Do not use import aliases in `src/polymarket_alpha_lab/proposal_review.py`. The existing AST scope helpers treat `alias.asname` as an imported module candidate, so `from polymarket_alpha_lab.proposal_packet import TradeProposalPacket as SourceProposal` must fail. Import exactly `TradeProposalPacket` from `polymarket_alpha_lab.proposal_packet`, and do not import `TradeProposalPacketConfig`, `TradeProposalPacketLog`, or `build_trade_proposal_packet`.

Forbidden name fragments must allow exact source-audit and inert-review names such as `source_human_approval_required`, `required_human_attestation`, `intended_order_type`, and `explicit_human_decision`, but must forbid workflow, routing, automation, execution, account, credential, and broker surfaces:

- `approvalworkflow`
- `approvalqueue`
- `approvalrouter`
- `approvalbroker`
- `autoapproval`
- `autoapprove`
- `automaticapproval`
- `unattendedapproval`
- all broker, client, request, transport, credential, account, signing, order lifecycle, `liveexecution`, `executiondecision`, settlement, reconciliation, scraping, browser automation, compliance, and geographic fragments listed in the planning research.
- Do not include bare `approval`, bare `review`, bare `execution`, bare `request`, bare `order`, or bare `decision` when that would reject intentional source-audit or review-artifact names; use the specific forbidden compound fragments listed above and in the scope test constants.

Package-root leakage test must permit only exact Level 2 artifact exports when a root export name contains `proposal` or `tradeproposal`:

```python
if any(fragment in normalized_name for fragment in ("proposal", "tradeproposal")):
    assert name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS
    continue
```

- [ ] **Step 2: Add root export identity test**

In `tests/test_init.py`, import:

```python
from polymarket_alpha_lab.proposal_review import (
    TradeProposalReviewConfig,
    TradeProposalReviewLog,
    TradeProposalReviewRecord,
    build_trade_proposal_review_record,
)
```

Append:

```python
def test_level_2_node_2_public_api_exports():
    expected_exports = {
        "TradeProposalReviewConfig",
        "TradeProposalReviewLog",
        "TradeProposalReviewRecord",
        "build_trade_proposal_review_record",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalReviewConfig is TradeProposalReviewConfig
    assert lab.TradeProposalReviewLog is TradeProposalReviewLog
    assert lab.TradeProposalReviewRecord is TradeProposalReviewRecord
    assert (
        lab.build_trade_proposal_review_record
        is build_trade_proposal_review_record
    )
```

- [ ] **Step 3: Run scope/export red checks before package-root exports**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_scope.py -q
.venv/bin/python -m pytest tests/test_init.py::test_level_2_node_2_public_api_exports -q
```

Expected: `tests/test_proposal_review_scope.py` is a guard and may pass after `src/polymarket_alpha_lab/proposal_review.py` exists because it parses source files directly. `tests/test_init.py::test_level_2_node_2_public_api_exports` must fail before `src/polymarket_alpha_lab/__init__.py` exports the Node 2 API.

- [ ] **Step 4: Migrate existing package-root scope tests**

In these files, update the Level 2 allowlist to include both Node 1 and Node 2 exact exports:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
- `tests/test_proposal_packet_scope.py`

For `tests/test_analytics_scope.py`, `tests/test_analytics_history_scope.py`, `tests/test_forecast_evidence_scope.py`, and `tests/test_manual_review_queue_scope.py`, replace the current packet-only allowlist:

```python
EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}
```

with:

```python
EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}
EXPECTED_PROPOSAL_REVIEW_EXPORTS = {
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
}
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS | EXPECTED_PROPOSAL_REVIEW_EXPORTS
)
```

Then change each file's package-root leakage assertion to check `EXPECTED_LEVEL_2_ARTIFACT_EXPORTS`.

For `tests/test_proposal_packet_scope.py`, rename `EXPECTED_PROPOSAL_PACKET_EXPORTS` to stay local and add:

```python
EXPECTED_PROPOSAL_REVIEW_EXPORTS = {
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
}
EXPECTED_LEVEL_2_ARTIFACT_EXPORTS = (
    EXPECTED_PROPOSAL_PACKET_EXPORTS | EXPECTED_PROPOSAL_REVIEW_EXPORTS
)
```

Then change the root leakage exception:

```python
if any(fragment in normalized_name for fragment in ("proposal", "tradeproposal")):
    assert name in EXPECTED_LEVEL_2_ARTIFACT_EXPORTS
    continue
```

Do not add generic `review` to this trigger because it would incorrectly route existing `PaperManualReview*` exports into the Level 2 artifact allowlist. Do not broadly exempt `approval`, `request`, `broker`, or `execution`.

- [ ] **Step 5: Add package root exports**

In `src/polymarket_alpha_lab/__init__.py`, add:

```python
from polymarket_alpha_lab.proposal_review import (
    TradeProposalReviewConfig,
    TradeProposalReviewLog,
    TradeProposalReviewRecord,
    build_trade_proposal_review_record,
)
```

Add these names to `__all__`:

```python
    "TradeProposalReviewConfig",
    "TradeProposalReviewLog",
    "TradeProposalReviewRecord",
    "build_trade_proposal_review_record",
```

- [ ] **Step 6: Run scope/export green tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_review_scope.py tests/test_proposal_packet_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
```

Expected: PASS.

## Task 4: README And Repository Layout Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 0: Confirm README anchors before editing**

Run:

```bash
rg -n '^## Level 2 Node 1 Python API$|^## Automation Roadmap$|paper-only manual-review queues, and human-review proposal packet artifacts\\.' README.md
```

Expected: all three anchors are present. If an anchor is missing, inspect the surrounding README text and use the semantically equivalent current heading/sentence before editing.

- [ ] **Step 1: Update Phase 1 scope sentence**

Change the current scope sentence ending from:

```markdown
paper-only manual-review queues, and human-review proposal packet artifacts.
```

to:

```markdown
paper-only manual-review queues, human-review proposal packet artifacts, and append-only proposal-review record artifacts.
```

- [ ] **Step 2: Add Level 2 Node 2 README sections**

Insert after `Level 2 Node 1 Python API` and before `Automation Roadmap`:

```markdown
## Level 2 Node 2 Status

Level 2 Node 2 adds append-only proposal-review record artifacts over supplied `TradeProposalPacket` values. A proposal-review record captures a reviewer decision, rationale, reviewed packet identity, attestation, and boundary text for audit only; it is not an approval workflow, trade instruction, order instruction, broker request, order request, account action, strategy-promotion signal, or live-execution signal.

It does not fetch market, order-book, price-history, outcome, account, credential, or identity data; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, send, create, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, execution client, or transport client; build broker or order request payloads; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 2 Python API

Node 2 is exposed through Python APIs:

- Configure proposal-review boundaries with `TradeProposalReviewConfig(config_version="review-v1")`.
- Build proposal-review records with `build_trade_proposal_review_record(packet, decision="approved", reviewer_label="human-reviewer", review_rationale="Reviewed packet fields and supporting evidence.", review_reason_codes=(), human_attestation=config.required_human_attestation, config=config, recorded_at=datetime.now(UTC))`, which returns `TradeProposalReviewRecord`.
- Inspect review-only audit fields with `TradeProposalReviewRecord`.
- Persist proposal-review snapshots with `TradeProposalReviewLog(path).append(record)`.
```

- [ ] **Step 3: Update repository layout**

Add entries preserving the existing tree indentation and nearby context:

```text
│       │   ├── 2026-06-14-level-2-proposal-packets.md
│       │   ├── 2026-06-14-level-2-proposal-review-records.md
...
│       ├── proposal_packet.py
│       ├── proposal_review.py
...
    ├── test_proposal_packet_scope.py
    ├── test_proposal_review.py
    ├── test_proposal_review_scope.py
```

- [ ] **Step 4: Run README text checks**

Run:

```bash
rg -n "Level 2 Node 2|proposal-review|order request|approval workflow" README.md
rg -n "2026-06-14-level-2-proposal-review-records.md|proposal_review.py|test_proposal_review.py|test_proposal_review_scope.py" README.md
awk '
  /^## Level 2 Node 1 Python API$/ { node1_api = NR }
  /^## Level 2 Node 2 Status$/ { node2_status = NR }
  /^## Level 2 Node 2 Python API$/ { node2_api = NR }
  /^## Automation Roadmap$/ { automation = NR }
  END {
    if (!(node1_api && node2_status && node2_api && automation && node1_api < node2_status && node2_status < node2_api && node2_api < automation)) {
      exit 1
    }
  }
' README.md
```

Expected: all matches are explanatory boundary/API text or exact repository-layout entries, and the `awk` command exits zero only when the Node 2 sections are inserted after `Level 2 Node 1 Python API` and before `Automation Roadmap`.

## Task 5: Full Verification

**Files:** no edits.

- [ ] **Step 1: Run focused functional tests**

```bash
.venv/bin/python -m pytest tests/test_proposal_review.py -q
```

Expected: PASS.

- [ ] **Step 2: Run scope and export tests**

```bash
.venv/bin/python -m pytest tests/test_proposal_review_scope.py tests/test_proposal_packet_scope.py tests/test_init.py -q
.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

```bash
.venv/bin/python -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run whitespace and CodeGraph checks**

```bash
git diff --check
codegraph status .
```

If CodeGraph reports pending changes:

```bash
codegraph sync
codegraph status .
```

Expected: no whitespace errors and CodeGraph index up to date.

## Task 6: Handoff Summary And Claude Implementation Review

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md`

- [ ] **Step 1: Append preliminary Handoff Summary before implementation review**

Append this section before running Claude implementation review so the self-contained review includes the final plan-file content intended for commit:

```markdown
## Handoff Summary

- Repo status: <branch/status before final staging>.
- Verified commands: <fresh command outputs and pass counts>.
- Claude reviews: plan-review verdict and counts; implementation-review pending.
- Review fixes: <Critical/Important fixes, or none>.
- Uncommitted files before commit: <exact intended files>.
- Next step: <next staged node>.
```

After Claude implementation review returns an accepted terminal state, update this Handoff Summary with the implementation-review verdict and counts, then rerun Task 6 Step 2 once so the final reviewed file set includes the final Handoff Summary. If implementation-review fixes change code, tests, README, scope tests, verification output, or this Handoff Summary, update the Handoff Summary and rerun Task 6 Step 2 before commit.

- [ ] **Step 2: Run self-contained Claude implementation review**

Run this only after all verification in Task 5 passes:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-review-records implementation for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only, self-contained implementation review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, plan text, implementation, tests, or verification output.'
  printf '%s\n' 'Review specifically: proposal-review record-only semantics, explicit human decision fields, no approval workflow engine, no approval queue/router, no broker/request/client surfaces, no account/credential/private-key/signing surfaces, no live execution/order placement/order lifecycle/reconciliation/settlement surfaces, no manual execution import, no scraping/browser automation, no compliance/legal/geographic analysis, source TradeProposalPacket revalidation, deterministic record id and source fingerprint, Gate 6 field preservation, Decimal and UTC validation, JSONL validate-before-open behavior, exact public exports, scope-test allowlists, README wording, verification evidence, Handoff Summary requirement, and commit/push readiness.'
  printf '%s\n' 'Before the final verdict line, report finding counts exactly as:'
  printf '%s\n' 'Critical findings: <integer>'
  printf '%s\n' 'Important findings: <integer>'
  printf '%s\n' 'Minor findings: <integer>'
  printf '%s\n' 'Use 0 for empty categories; do not use "none" in count fields.'
  printf '%s\n' 'Finish with exactly one verdict line: Verdict: Proceed | Proceed with fixes | Blocked.'
  printf '%s\n' ''
  printf '%s\n' 'Repository instructions:'
  cat AGENTS.md
  printf '%s\n' ''
  printf '%s\n' 'Roadmap and validation gates:'
  sed -n '70,115p' docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  sed -n '97,130p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Plan text:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md
  printf '%s\n' ''
  printf '%s\n' 'Current proposal packet source contract:'
  codegraph node src/polymarket_alpha_lab/proposal_packet.py
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Verification output:'
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_proposal_review.py -q'
  .venv/bin/python -m pytest tests/test_proposal_review.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_proposal_review_scope.py tests/test_proposal_packet_scope.py tests/test_init.py -q'
  .venv/bin/python -m pytest tests/test_proposal_review_scope.py tests/test_proposal_packet_scope.py tests/test_init.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q'
  .venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
  printf '%s\n' '$ .venv/bin/python -m pytest -q'
  .venv/bin/python -m pytest -q
  printf '%s\n' '$ git diff --check'
  git diff --check && printf '%s\n' 'git diff --check passed'
  printf '%s\n' '$ codegraph status .'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Changed and untracked files:'
  cat README.md
  cat src/polymarket_alpha_lab/__init__.py
  cat src/polymarket_alpha_lab/proposal_review.py
  cat tests/test_proposal_review.py
  cat tests/test_proposal_review_scope.py
  cat tests/test_init.py
  cat tests/test_analytics_scope.py
  cat tests/test_analytics_history_scope.py
  cat tests/test_forecast_evidence_scope.py
  cat tests/test_manual_review_queue_scope.py
  cat tests/test_proposal_packet_scope.py
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Implementation review accepted terminal state: `Critical findings: 0`, `Important findings: 0`, and verdict `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing changed file contents, missing verification output, or transport failure is treated as `Blocked`.

- [ ] **Step 3: Fix review findings if needed**

For every Critical or Important finding:

1. Verify the finding against the codebase.
2. Apply the smallest scoped fix.
3. Rerun affected focused tests.
4. Rerun full verification as needed.
5. Rerun the Claude implementation review until accepted.

## Task 7: Commit And Push

**Files:**
- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md`

- [ ] **Step 1: Confirm Handoff Summary is current**

Confirm the Handoff Summary appended in Task 6 includes the final verification outputs, Claude review counts/verdicts, review fixes, and exact uncommitted files. If it needs any change, update it and rerun Task 6 Step 2 before staging.

- [ ] **Step 2: Final pre-commit checks**

Run:

```bash
git diff --check
git status --short --branch --untracked-files=all
```

Expected: only intended Node 2 files are modified or untracked.

- [ ] **Step 3: Stage exact files**

```bash
git add \
  README.md \
  src/polymarket_alpha_lab/__init__.py \
  src/polymarket_alpha_lab/proposal_review.py \
  tests/test_proposal_review.py \
  tests/test_proposal_review_scope.py \
  tests/test_init.py \
  tests/test_analytics_scope.py \
  tests/test_analytics_history_scope.py \
  tests/test_forecast_evidence_scope.py \
  tests/test_manual_review_queue_scope.py \
  tests/test_proposal_packet_scope.py \
  docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md
```

- [ ] **Step 4: Verify staged diff and commit**

```bash
git diff --cached --check
git status --short --branch --untracked-files=all
git commit -m "feat: add level 2 proposal review records"
```

- [ ] **Step 5: Push and verify clean state**

```bash
git push
git status --short --branch
codegraph status .
```

Expected: clean worktree on `main` tracking `origin/main`, CodeGraph index up to date.

## Handoff Summary

- Repo status: `main...origin/main` with intended Node 2 modified/untracked files before final staging.
- Verified commands:
  - `.venv/bin/python -m pytest tests/test_proposal_review.py -q` -> `29 passed`
  - `.venv/bin/python -m pytest tests/test_proposal_review_scope.py tests/test_proposal_packet_scope.py tests/test_init.py -q` -> `21 passed`
  - `.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q` -> `21 passed`
  - `.venv/bin/python -m pytest -q` -> `463 passed`
  - `git diff --check` -> passed
  - `codegraph sync && codegraph status .` -> synced 2 changed files; index up to date
- Claude reviews: plan-review `Critical findings: 0`, `Important findings: 0`, `Minor findings: 4`, `Verdict: Proceed with fixes`; implementation-review pass 1 `Critical findings: 0`, `Important findings: 0`, `Minor findings: 3`, `Verdict: Proceed with fixes`; implementation-review Handoff rerun `Critical findings: 0`, `Important findings: 0`, `Minor findings: 2`, `Verdict: Proceed with fixes`.
- Review fixes: plan-review minor fixes applied before implementation; implementation-review minor findings were non-blocking maintainability notes and did not require code changes.
- Uncommitted files before commit: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `src/polymarket_alpha_lab/proposal_review.py`, `tests/test_proposal_review.py`, `tests/test_proposal_review_scope.py`, `tests/test_init.py`, `tests/test_analytics_scope.py`, `tests/test_analytics_history_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_manual_review_queue_scope.py`, `tests/test_proposal_packet_scope.py`, `docs/superpowers/plans/2026-06-14-level-2-proposal-review-records.md`.
- Next step: run final pre-commit checks, commit, and push Node 2.
