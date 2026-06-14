# Level 2 Proposal Packets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 2 Node 1 proposal-packet artifacts that turn a ready manual-review queue item into a self-contained, human-review trade proposal packet without approval workflow or execution behavior.

**Architecture:** Add a new `proposal_packet.py` derived-artifact layer. It consumes one caller-supplied `PaperManualReviewQueueItem`, caller-supplied proposal intent fields, and caller-supplied proposal config, then emits frozen dataclasses and optional append-only JSONL. The module does not fetch data, authenticate, handle credentials, build broker requests, run approval workflow, import manual executions, or place orders.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, UTC `datetime`, deterministic SHA-256 packet ids, JSONL, pytest, CodeGraph, Claude Code reviews with `claude-opus-4-8` and effort `max`.

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
   - Functional-test worker owns `tests/test_proposal_packet.py`.
   - Scope/export-test worker owns `tests/test_proposal_packet_scope.py`, the root-export checks in existing scope tests, and `tests/test_init.py`.
   - Main integrator owns `src/polymarket_alpha_lab/proposal_packet.py`, `src/polymarket_alpha_lab/__init__.py`, `README.md`, and this plan.
5. Do not let two agents edit the same file or same batch of files at the same time.
6. Close completed subagents promptly, then redeploy only to a fresh independent task.
7. Before commit, run fresh verification and a self-contained Claude implementation review covering all modified and untracked files.
8. Resolve every Critical or Important implementation-review finding before staging for final commit.
9. Append a Handoff Summary to this plan before final commit.
10. Commit and push only after all gates pass.

## Plan Review Command Before Any Implementation

Run this exact self-contained command before implementation:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-packets implementation plan for polymarket-alpha-lab before implementation.'
  printf '%s\n' 'This is a read-only, self-contained plan review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, existing tests, or plan text.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; plan is implementable as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or plan ambiguity that could cause incorrect implementation.'
  printf '%s\n' 'Review specifically: Level 2 proposal-packet boundary, no approval workflow in Node 1, no private-key handling, no automatic credential use, no account authentication, no unattended execution, no live order placement, no broker/request/client surfaces, no scraping/browser automation, no compliance/legal/geographic analysis, proposal semantics, Gate 6 packet completeness, source evidence and audit trail fields, sizing limits, exit-rule clarity, target files, public API/export surface, old root-export scope-test migration, TDD steps, CodeGraph usage, verification gates, implementation-review self-containment, untracked-file handling, Handoff Summary, and commit/push order.'
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
  sed -n '1,120p' docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  sed -n '90,130p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'CodeGraph status:'
  codegraph status .
  printf '%s\n' ''
  printf '%s\n' 'Current manual-review queue source contract:'
  codegraph node src/polymarket_alpha_lab/manual_review_queue.py
  printf '%s\n' ''
  printf '%s\n' 'Current public API root and export tests:'
  codegraph node src/polymarket_alpha_lab/__init__.py
  codegraph node tests/test_init.py
  printf '%s\n' ''
  printf '%s\n' 'Existing root-export scope tests that must be migrated safely:'
  sed -n '160,310p' tests/test_analytics_scope.py
  sed -n '160,310p' tests/test_analytics_history_scope.py
  sed -n '160,310p' tests/test_forecast_evidence_scope.py
  sed -n '170,325p' tests/test_manual_review_queue_scope.py
  printf '%s\n' ''
  printf '%s\n' 'Plan under review:'
  cat docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted plan-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing repository instructions, missing Level 2 context, missing plan text, or transport failure is treated as `Blocked`. After fixing any Critical or Important plan-review finding, rerun the same self-contained Claude plan-review prompt and do not implement until the rerun reaches an accepted terminal state.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes `AGENTS.md`, the Level 2 roadmap excerpt, Gate 6, fresh git status, the manual-review status constants, the `PaperManualReviewQueueItem` source contract, the current package-root exports, the current export tests, the root-export scope-test snippets, the full target plan text, and the same count/verdict policy.

## Level 2 Node 1 Scope

Level 2 Node 1 adds reviewable proposal-packet artifacts over supplied paper-trading, analytics, forecast-evidence, and manual-review artifacts. A proposal packet is for human review only; it is not an approval workflow, trade instruction, order instruction, broker request, strategy-promotion signal, or live-execution signal.

The module must:

- Consume exactly one caller-supplied `PaperManualReviewQueueItem`.
- Require that the queue item is `paper_review_ready`, paper-only, risk-gate-passed, hard-block-free, and free of blocking reason codes.
- Consume caller-supplied proposal intent values:
  - `side`
  - `intended_order_type`
  - `maximum_size`
  - `exposure_after_trade`
  - `exit_rule`
  - `reason_trade_could_be_wrong`
- Copy Gate 6 evidence fields from the queue item:
  - market URL and token id
  - executable price assumption
  - cost-adjusted edge
  - thesis
  - invalidating condition
  - resolution rule hash and resolution source
  - risk tags
- Store source evidence and audit-trail fields needed to review the packet without opening the source queue.
- Emit frozen `TradeProposalPacket` values with `proposal_only=True` and `human_approval_required=True`.
- Persist packet snapshots through `TradeProposalPacketLog(path).append(packet)` using append-only JSONL.
- Serialize `Decimal` values as exact strings and datetimes as UTC ISO strings.
- Validate before opening or writing JSONL files.

The module must not:

- Add approval workflow, approval queues, approval status, approver fields, or approved-at fields.
- Import manual execution journals or manual execution results.
- Fetch market, order-book, price-history, outcome, or account data.
- Read JSONL logs or external history.
- Scrape websites, run browser automation, bypass anti-bot controls, or handle CAPTCHA.
- Authenticate, handle credentials, handle private keys, sign messages, use wallets, or use trading SDKs.
- Create broker clients, transport clients, request payloads, response objects, sessions, WebSockets, heartbeats, reconciliation, settlement, or account-state surfaces.
- Place, submit, sign, send, create, or cancel orders.
- Add CLI, UI, dashboard, scheduler, notification, compliance, legal, jurisdiction, geofence, KYC, AML, sanctions, or geographic-access analysis surfaces.

## Target File Structure

Create:

- `src/polymarket_alpha_lab/proposal_packet.py`
- `tests/test_proposal_packet.py`
- `tests/test_proposal_packet_scope.py`
- `docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md`

Modify:

- `src/polymarket_alpha_lab/__init__.py`
- `tests/test_init.py`
- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`
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

## Public API Contract

`src/polymarket_alpha_lab/proposal_packet.py` must export exactly:

```python
__all__ = (
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
)
```

### Boundary Statement

`DEFAULT_PROPOSAL_BOUNDARY_STATEMENT` must be exactly:

```python
(
    "This is a proposal-only human-review packet, not an approval workflow, "
    "trade instruction, order instruction, broker request, strategy-promotion "
    "signal, or live-execution signal; no order may leave the system without "
    "explicit human approval."
)
```

Validation for boundary statements must require these lowercase substrings:

- `proposal-only`
- `human-review packet`
- `not an approval workflow`
- `trade instruction`
- `order instruction`
- `broker request`
- `live-execution signal`
- `explicit human approval`

### TradeProposalPacketConfig

Fields:

```python
@dataclass(frozen=True)
class TradeProposalPacketConfig:
    config_version: str
    allowed_sides: tuple[str, ...] = ("buy", "sell")
    allowed_intended_order_types: tuple[str, ...] = ("limit", "marketable_limit")
    min_cost_adjusted_edge: Decimal = Decimal("0.0000")
    max_proposal_size: Decimal | None = None
    max_exposure_after_trade: Decimal | None = None
    boundary_statement: str = DEFAULT_PROPOSAL_BOUNDARY_STATEMENT
```

Validation:

- `config_version` and `boundary_statement` must be canonical nonblank strings.
- `allowed_sides` must be a nonempty tuple of canonical strings, and every value must be in `("buy", "sell")`.
- `allowed_intended_order_types` must be a nonempty tuple of canonical strings.
- `min_cost_adjusted_edge` must be a finite `Decimal`.
- `max_proposal_size` must be `None` or a finite positive `Decimal`.
- `max_exposure_after_trade` must be `None` or a finite nonnegative `Decimal`.
- `boundary_statement` must satisfy the boundary statement contract above.

### TradeProposalPacket

Fields:

```python
@dataclass(frozen=True)
class TradeProposalPacket:
    proposal_packet_id: str
    generated_at: datetime
    proposal_config_version: str
    proposal_only: bool
    human_approval_required: bool
    boundary_statement: str
    source_queue_item_id: str
    source_queue_rank: int
    source_manual_review_status: str
    source_packet_id: str
    source_boundary_statement: str
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
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    risk_tags: tuple[str, ...]
    exposure_after_trade: Decimal
    exit_rule: str
    reason_trade_could_be_wrong: str
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    blocking_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    evidence_scope: str
    risk_gate_passed: bool
    hard_block_count: int
```

Validation:

- `generated_at` is normalized to UTC.
- `proposal_packet_id` must equal the deterministic id derived from packet fields.
- `proposal_only` must be `True`.
- `human_approval_required` must be `True`.
- `source_paper_only` must be `True`.
- `source_manual_review_status` must be `paper_review_ready`.
- `risk_gate_passed` must be `True`.
- `hard_block_count` must be zero.
- `blocking_reason_codes` must be empty.
- `source_queue_item_id` must match `condition_id:token_id:source_packet_id`.
- `side` must be `buy` or `sell`.
- `intended_order_type` must be canonical nonblank text.
- `executable_price_assumption`, `fair_value_estimate`, `model_probability`, and `confidence` values must be within the inclusive binary range from `0` to `1` when present.
- `executable_price_assumption` must be positive and less than `1`.
- `maximum_size` and `source_max_executable_size` must be finite positive `Decimal` values.
- `maximum_size` must be less than or equal to `source_max_executable_size`.
- `cost_adjusted_edge`, `theoretical_edge`, `source_score`, and `market_score_total` must be finite `Decimal` values when present.
- `source_score` must be nonnegative.
- `source_queue_rank` must be positive.
- `cost_adjusted_edge` must be nonnegative.
- `exposure_after_trade` must be a finite nonnegative `Decimal`.
- `market_url`, `thesis`, `invalidating_conditions`, `rule_text_hash`, `resolution_source`, `exit_rule`, and `reason_trade_could_be_wrong` must be canonical nonblank strings.
- `risk_tags` must be a nonempty tuple of canonical strings.
- `review_focus` must be a tuple of canonical strings.
- `supporting_reason_codes` must be a tuple of canonical strings.
- The boundary statement must satisfy the boundary statement contract.

### build_trade_proposal_packet

Signature:

```python
def build_trade_proposal_packet(
    queue_item: PaperManualReviewQueueItem,
    *,
    side: str,
    intended_order_type: str,
    maximum_size: Decimal,
    exposure_after_trade: Decimal,
    exit_rule: str,
    reason_trade_could_be_wrong: str,
    config: TradeProposalPacketConfig,
    generated_at: datetime,
) -> TradeProposalPacket:
```

Builder behavior:

- Validate `type(queue_item) is PaperManualReviewQueueItem`.
- Reconstruct a fresh `PaperManualReviewQueueItem` from the input fields before using it, so mutated frozen objects are caught.
- Validate `type(config) is TradeProposalPacketConfig`.
- Normalize `generated_at` to UTC.
- Reject any queue item that is not `paper_review_ready`.
- Reject any queue item that has `paper_only` not `True`.
- Reject any queue item that has `risk_gate_passed` not `True`.
- Reject any queue item that has `hard_block_count != 0`.
- Reject any queue item with nonempty `blocking_reason_codes`.
- Reject missing Gate 6 source fields:
  - `market_url`
  - `expected_entry_price`
  - `max_executable_size`
  - `cost_adjusted_edge`
  - `thesis`
  - `invalidating_conditions`
  - `rule_text_hash`
  - `resolution_source`
  - `risk_tags`
- Reject `side` values not in `config.allowed_sides`.
- Reject `intended_order_type` values not in `config.allowed_intended_order_types`.
- Reject `maximum_size > queue_item.max_executable_size`.
- Reject `maximum_size > config.max_proposal_size` when `config.max_proposal_size` is not `None`.
- Reject `cost_adjusted_edge < config.min_cost_adjusted_edge`.
- Reject `exposure_after_trade > config.max_exposure_after_trade` when `config.max_exposure_after_trade` is not `None`.
- Return a `TradeProposalPacket` that copies source fields and records caller intent fields.

### TradeProposalPacketLog

Fields and behavior:

```python
@dataclass(frozen=True)
class TradeProposalPacketLog:
    path: Path | str

    def append(self, packet: TradeProposalPacket) -> None:
        if not isinstance(packet, TradeProposalPacket):
            raise ValueError("packet must be a TradeProposalPacket")
        validated = _validate_packet_tree(packet)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
```

The implementation must:

- Normalize `path` using the existing path rules from `PaperManualReviewLog`.
- Reject a blank path.
- Reject an existing directory path.
- Reject a path whose nearest existing parent is a file.
- Reject non-`TradeProposalPacket` values before creating a file.
- Reconstruct and validate the full packet tree before JSON serialization.
- Serialize with `json.dumps(_json_ready(asdict(packet)), allow_nan=False, sort_keys=True) + "\n"`.
- Create parent directories only after packet validation and serialization succeed.
- Append without overwriting existing lines.

## Field Mapping

| Packet field | Source |
|---|---|
| `proposal_packet_id` | Deterministic hash of config version, UTC generated timestamp, source queue item id, side, intended order type, maximum size, and exposure after trade |
| `generated_at` | Caller-supplied clock, normalized UTC |
| `proposal_config_version` | `config.config_version` |
| `proposal_only` | Constant `True` |
| `human_approval_required` | Constant `True` |
| `boundary_statement` | `config.boundary_statement` |
| `source_queue_item_id` | `queue_item.queue_item_id` |
| `source_queue_rank` | `queue_item.rank` |
| `source_manual_review_status` | `queue_item.status` |
| `source_packet_id` | `queue_item.packet_id` |
| `source_boundary_statement` | `queue_item.boundary_statement` |
| `source_paper_only` | `queue_item.paper_only` |
| `condition_id` | `queue_item.condition_id` |
| `token_id` | `queue_item.token_id` |
| `market_slug` | `queue_item.market_slug` |
| `market_url` | `queue_item.market_url` |
| `question` | `queue_item.question` |
| `outcome_name` | `queue_item.outcome_name` |
| `strategy_type` | `queue_item.strategy_type` |
| `side` | Caller-supplied proposal intent |
| `intended_order_type` | Caller-supplied descriptive order-type label |
| `executable_price_assumption` | `queue_item.expected_entry_price` |
| `maximum_size` | Caller-supplied size, capped by queue item and config |
| `source_max_executable_size` | `queue_item.max_executable_size` |
| `cost_adjusted_edge` | `queue_item.cost_adjusted_edge` |
| `theoretical_edge` | `queue_item.theoretical_edge` |
| `fair_value_estimate` | `queue_item.fair_value_estimate` |
| `model_probability` | `queue_item.model_probability` |
| `confidence` | `queue_item.confidence` |
| `source_score` | `queue_item.source_score` |
| `market_score_total` | `queue_item.market_score_total` |
| `thesis` | `queue_item.thesis` |
| `invalidating_conditions` | `queue_item.invalidating_conditions` |
| `rule_text_hash` | `queue_item.rule_text_hash` |
| `resolution_source` | `queue_item.resolution_source` |
| `risk_tags` | `queue_item.risk_tags` |
| `exposure_after_trade` | Caller-supplied proposal scenario value |
| `exit_rule` | Caller-supplied proposal intent |
| `reason_trade_could_be_wrong` | Caller-supplied review text |
| `readiness_summary` | `queue_item.readiness_summary` |
| `risk_summary` | `queue_item.risk_summary` |
| `evidence_summary` | `queue_item.evidence_summary` |
| `why_in_queue` | `queue_item.why_in_queue` |
| `primary_reason_code` | `queue_item.primary_reason_code` |
| `supporting_reason_codes` | `queue_item.supporting_reason_codes` |
| `blocking_reason_codes` | `queue_item.blocking_reason_codes` |
| `review_focus` | `queue_item.review_focus` |
| `history_status` | `queue_item.history_status` |
| `forecast_status` | `queue_item.forecast_status` |
| `history_gate_pass_count` | `queue_item.history_gate_pass_count` |
| `forecast_gate_pass_count` | `queue_item.forecast_gate_pass_count` |
| `history_gate_fail_count` | `queue_item.history_gate_fail_count` |
| `forecast_gate_fail_count` | `queue_item.forecast_gate_fail_count` |
| `evidence_scope` | `queue_item.evidence_scope` |
| `risk_gate_passed` | `queue_item.risk_gate_passed` |
| `hard_block_count` | `queue_item.hard_block_count` |

## Task 0: Pre-Implementation Contract Check

**Files:**

- Read only.

- [ ] **Step 1: Inspect current contracts with CodeGraph**

Run before writing implementation tests:

```bash
codegraph status .
codegraph node src/polymarket_alpha_lab/manual_review_queue.py
codegraph node src/polymarket_alpha_lab/__init__.py
codegraph node tests/test_init.py
codegraph node tests/test_manual_review_queue_scope.py
```

Expected: CodeGraph is up to date, and the current source confirms `PaperManualReviewQueueItem`, existing package-root exports, and current forbidden root-export fragments.

## Task 1: Write Export And Scope Tests First

**Files:**

- Create: `tests/test_proposal_packet_scope.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_analytics_scope.py`
- Modify: `tests/test_analytics_history_scope.py`
- Modify: `tests/test_forecast_evidence_scope.py`
- Modify: `tests/test_manual_review_queue_scope.py`

- [ ] **Step 1: Add direct public API import block to `tests/test_init.py`**

Insert after the `manual_review_queue` import block:

```python
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacket,
    TradeProposalPacketConfig,
    TradeProposalPacketLog,
    build_trade_proposal_packet,
)
```

- [ ] **Step 2: Add Level 2 export test to `tests/test_init.py`**

Insert after `test_level_1b_node_6_public_api_exports`:

```python
def test_level_2_node_1_public_api_exports():
    expected_exports = {
        "TradeProposalPacket",
        "TradeProposalPacketConfig",
        "TradeProposalPacketLog",
        "build_trade_proposal_packet",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.TradeProposalPacket is TradeProposalPacket
    assert lab.TradeProposalPacketConfig is TradeProposalPacketConfig
    assert lab.TradeProposalPacketLog is TradeProposalPacketLog
    assert lab.build_trade_proposal_packet is build_trade_proposal_packet
```

- [ ] **Step 3: Create `tests/test_proposal_packet_scope.py`**

Use this full file:

```python
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PACKET_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "proposal_packet.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}

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
    "polymarket_alpha_lab.manual_review_queue",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.manual_review_queue": {"PaperManualReviewQueueItem"},
}

FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "polymarket_alpha_lab.scoring",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "websocket",
    "websockets",
    "requests",
    "httpx",
    "aiohttp",
    "importlib",
    "runpy",
    "subprocess",
    "py_clob_client",
    "clob_client",
    "web3",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "selenium",
    "playwright",
    "bs4",
    "scrapy",
    "requests_html",
    "mechanize",
    "cloudscraper",
    "curl_cffi",
    "csv",
    "sqlite3",
    "pandas",
    "polars",
    "duckdb",
    "os",
}

FORBIDDEN_NAME_FRAGMENTS = (
    "privatekey",
    "privkey",
    "apikey",
    "secret",
    "credential",
    "password",
    "mnemonic",
    "seedphrase",
    "auth",
    "authentication",
    "bearer",
    "jwt",
    "wallet",
    "signer",
    "signature",
    "signedorder",
    "signorder",
    "signmessage",
    "signtransaction",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "executiondecision",
    "liveexecution",
    "approvalworkflow",
    "approvalqueue",
    "approvalstatus",
    "approvedby",
    "approvedat",
    "approver",
    "client",
    "transport",
    "fetch",
    "request",
    "response",
    "session",
    "urlopen",
    "getjson",
    "websocket",
    "heartbeat",
    "broker",
    "reconciler",
    "reconciliation",
    "exchangeaccount",
    "accountstate",
    "accountposition",
    "accountbalance",
    "compliance",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
    "geoblock",
    "kyc",
    "aml",
    "sanction",
    "simulateorderbookfill",
    "clobclient",
    "tradesdk",
    "settlement",
    "settle",
    "resolvedoutcome",
    "promotionpacket",
    "strategypromotion",
    "dashboard",
    "historicalloader",
    "externalhistory",
    "pricehistoryapi",
    "backfill",
    "download",
    "readjsonl",
    "loadjsonl",
    "scrape",
    "crawler",
    "captcha",
    "antibot",
    "bypass",
    "browserautomation",
)

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = (
    "approval",
    "broker",
    "execution",
    "credential",
    "wallet",
    "reconciliation",
    "compliance",
    "auth",
    "privatekey",
    "apikey",
    "signer",
    "signature",
    "placeorder",
    "createorder",
    "cancelorder",
    "submitorder",
    "signedorder",
    "orderlifecycle",
    "ordermanager",
    "orderrouter",
    "client",
    "transport",
    "fetch",
    "request",
    "session",
    "websocket",
    "heartbeat",
    "settlement",
    "resolvedoutcome",
    "dashboard",
    "legal",
    "jurisdiction",
    "geofence",
    "geographic",
)


def parse_proposal_packet():
    return ast.parse(PROPOSAL_PACKET_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return modules


def imported_first_party_symbols(tree):
    symbols = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in EXPECTED_FIRST_PARTY_IMPORTS:
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return symbols


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_proposal_packet_module_imports_only_allowed_dependencies():
    tree = parse_proposal_packet()
    for module_name in imported_modules(tree):
        assert any(
            module_name == allowed or module_name.startswith(f"{allowed}.")
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_proposal_packet_module_does_not_import_forbidden_surfaces():
    tree = parse_proposal_packet()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_proposal_packet_module_uses_only_allowed_first_party_symbols():
    tree = parse_proposal_packet()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_proposal_packet_module_does_not_define_forbidden_live_or_workflow_names():
    tree = parse_proposal_packet()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(fragment in name for name in lowered), fragment


def test_trade_proposal_packet_public_exports_are_artifact_only():
    tree = parse_proposal_packet()
    assigned_exports = module_exports(tree)
    assert set(assigned_exports) == EXPECTED_PROPOSAL_PACKET_EXPORTS
    for name in assigned_exports:
        assert name.startswith("TradeProposalPacket") or name == "build_trade_proposal_packet"
        normalized_name = normalize_identifier(name)
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )


def test_package_root_exports_do_not_leak_forbidden_level_2_node_1_surfaces():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        if "proposal" in normalized_name or "tradeproposal" in normalized_name:
            assert name in EXPECTED_PROPOSAL_PACKET_EXPORTS
            continue
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )
```

- [ ] **Step 4: Migrate old package-root scope checks to exact Level 2 allowlists**

In each of these files, add the following constant after `FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS`:

- `tests/test_analytics_scope.py`
- `tests/test_analytics_history_scope.py`
- `tests/test_forecast_evidence_scope.py`
- `tests/test_manual_review_queue_scope.py`

```python
EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS = {
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
}
```

Replace each `test_package_root_exports_do_not_leak_forbidden_*_surfaces` function body with this exact pattern, preserving the original test function name:

```python
def test_package_root_exports_do_not_leak_forbidden_analytics_surfaces():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    assigned_exports = module_exports(tree)
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        if "proposal" in normalized_name or "tradeproposal" in normalized_name:
            assert name in EXPECTED_LEVEL_2_PROPOSAL_PACKET_EXPORTS
            continue
        assert not any(
            fragment in normalized_name for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
        )
```

Use the same body for the analytics-history, forecast-evidence, and manual-review function names.

- [ ] **Step 5: Run the export/scope red tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py::test_level_2_node_1_public_api_exports tests/test_proposal_packet_scope.py -q
```

Expected: FAIL because `polymarket_alpha_lab.proposal_packet` does not exist yet or because the package root does not export the new Level 2 API.

## Task 2: Add Minimal Public Surface

**Files:**

- Create: `src/polymarket_alpha_lab/proposal_packet.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`

- [ ] **Step 1: Add minimal `proposal_packet.py` public surface**

Create the file with the import boundary and public symbols. The initial implementation can raise `NotImplementedError` from the builder until Task 4, but dataclasses and `__all__` must exist for import tests:

```python
"""Proposal-only human-review packet artifacts for Level 2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.manual_review_queue import PaperManualReviewQueueItem


__all__ = (
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
)


DEFAULT_PROPOSAL_BOUNDARY_STATEMENT = (
    "This is a proposal-only human-review packet, not an approval workflow, "
    "trade instruction, order instruction, broker request, strategy-promotion "
    "signal, or live-execution signal; no order may leave the system without "
    "explicit human approval."
)
ZERO = Decimal("0")
ONE = Decimal("1")
PROPOSAL_SIDES = ("buy", "sell")


@dataclass(frozen=True)
class TradeProposalPacketConfig:
    config_version: str
    allowed_sides: tuple[str, ...] = PROPOSAL_SIDES
    allowed_intended_order_types: tuple[str, ...] = ("limit", "marketable_limit")
    min_cost_adjusted_edge: Decimal = Decimal("0.0000")
    max_proposal_size: Decimal | None = None
    max_exposure_after_trade: Decimal | None = None
    boundary_statement: str = DEFAULT_PROPOSAL_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True)
class TradeProposalPacket:
    proposal_packet_id: str
    generated_at: datetime
    proposal_config_version: str
    proposal_only: bool
    human_approval_required: bool
    boundary_statement: str
    source_queue_item_id: str
    source_queue_rank: int
    source_manual_review_status: str
    source_packet_id: str
    source_boundary_statement: str
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
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    risk_tags: tuple[str, ...]
    exposure_after_trade: Decimal
    exit_rule: str
    reason_trade_could_be_wrong: str
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    blocking_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    evidence_scope: str
    risk_gate_passed: bool
    hard_block_count: int

    def __post_init__(self) -> None:
        _validate_packet(self)


@dataclass(frozen=True)
class TradeProposalPacketLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, packet: TradeProposalPacket) -> None:
        raise NotImplementedError("TradeProposalPacketLog.append is implemented in Task 8")


def build_trade_proposal_packet(
    queue_item: PaperManualReviewQueueItem,
    *,
    side: str,
    intended_order_type: str,
    maximum_size: Decimal,
    exposure_after_trade: Decimal,
    exit_rule: str,
    reason_trade_could_be_wrong: str,
    config: TradeProposalPacketConfig,
    generated_at: datetime,
) -> TradeProposalPacket:
    raise NotImplementedError("build_trade_proposal_packet is implemented in Task 4")
```

- [ ] **Step 2: Add root exports to `src/polymarket_alpha_lab/__init__.py`**

Add this import block after the `manual_review_queue` import block and before `journal` imports:

```python
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacket,
    TradeProposalPacketConfig,
    TradeProposalPacketLog,
    build_trade_proposal_packet,
)
```

Add these strings to `__all__` after `PaperManualReviewQueueItem`:

```python
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
```

Add this builder string near the other `build_*` exports:

```python
    "build_trade_proposal_packet",
```

- [ ] **Step 3: Run the export/scope green tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py::test_level_2_node_1_public_api_exports tests/test_proposal_packet_scope.py -q
```

Expected: PASS for imports and scope once helper stubs are present. If scope fails because helper names are missing, add only validation helper definitions needed by dataclass `__post_init__`, then rerun.

## Task 3: Write Functional Builder Tests

**Files:**

- Create or modify: `tests/test_proposal_packet.py`

- [ ] **Step 1: Add test imports and local fixtures**

Create `tests/test_proposal_packet.py` with local helpers copied and adapted from manual-review tests. Do not import helper functions from another test module.

The file must start with:

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
    STATUS_RANK,
    build_paper_manual_review_queue,
)
from polymarket_alpha_lab.proposal_packet import (
    TradeProposalPacketConfig,
    TradeProposalPacketLog,
    build_trade_proposal_packet,
)
```

Add helper functions:

```python
def market_score(token_id: str, total_bias: Decimal = Decimal("0")) -> MarketScore:
    return MarketScore(
        condition_id="condition-1",
        token_id=token_id,
        activity=Decimal("90") + total_bias,
        liquidity=Decimal("80"),
        spread_quality=Decimal("85"),
        time_structure=Decimal("70"),
        information_structure=Decimal("75"),
        price_behavior=Decimal("65"),
        duplicate_penalty=Decimal("0"),
    )


def ready_history_report() -> PaperAnalyticsHistoryReport:
    gate_results = tuple(
        PaperAnalyticsHistoryGateResult(
            gate_name=gate_name,
            status="pass",
            message=f"{gate_name} is ready for manual review.",
        )
        for gate_name in (
            "data_integrity",
            "sample_size",
            "execution_cost_reality",
            "forecast_edge_quality",
            "risk_drawdown",
        )
    )
    trend = PaperAnalyticsHistoryTrend(
        marked_at=datetime(2026, 9, 1, tzinfo=UTC),
        exit_nav=Decimal("10100"),
        total_exit_pnl=Decimal("100"),
        drawdown=Decimal("0"),
        drawdown_ratio=Decimal("0.0000"),
        exit_depth_shortfall_ratio=Decimal("0.0000"),
        no_exit_depth_cost_basis_ratio=Decimal("0.0000"),
        midpoint_nav_gap_ratio=Decimal("0.0000"),
        breach_count=0,
    )
    return PaperAnalyticsHistoryReport(
        generated_at=datetime(2026, 9, 2, tzinfo=UTC),
        config_version="history-ready",
        first_marked_at=trend.marked_at,
        last_marked_at=trend.marked_at,
        report_count=1,
        candidate_observation_count=250,
        simulated_trade_count=55,
        exited_trade_count=31,
        forward_window_days=28,
        unique_market_count=1,
        unique_strategy_count=1,
        unique_risk_tag_count=1,
        latest_exit_nav=trend.exit_nav,
        latest_total_exit_pnl=trend.total_exit_pnl,
        max_drawdown=trend.drawdown,
        max_drawdown_ratio=trend.drawdown_ratio,
        worst_exit_depth_shortfall_ratio=trend.exit_depth_shortfall_ratio,
        worst_no_exit_depth_cost_basis_ratio=trend.no_exit_depth_cost_basis_ratio,
        worst_midpoint_nav_gap_ratio=trend.midpoint_nav_gap_ratio,
        largest_market_cost_basis_ratio=Decimal("0.1000"),
        largest_risk_tag_cost_basis_ratio=Decimal("0.1000"),
        max_breach_count=0,
        status="paper_review_ready",
        gate_results=gate_results,
        trends=(trend,),
    )
```

Continue the helper block with `forecast_observation`, `ready_forecast_report`, and `candidate` using the exact same field values from `tests/test_manual_review_queue.py`, except keep the helper local to this file.

Add proposal-specific helpers:

```python
def ready_queue_item(
    *,
    analytics_history=None,
    forecast_evidence=None,
    config=None,
    **overrides,
) -> PaperManualReviewQueueItem:
    base_candidate = candidate(1)
    if overrides:
        base_candidate = replace(base_candidate, **overrides)
    queue = build_paper_manual_review_queue(
        [base_candidate],
        market_scores=(market_score("token-1"),),
        analytics_history=analytics_history or ready_history_report(),
        forecast_evidence=forecast_evidence or ready_forecast_report(),
        config=(
            config
            or PaperManualReviewConfig(
                config_version="node6-test",
                min_source_score=Decimal("80.0000"),
            )
        ),
        generated_at=datetime(2026, 9, 3, tzinfo=UTC),
    )
    return queue.items[0]


def proposal_packet(**overrides):
    values = {
        "queue_item": ready_queue_item(),
        "side": "buy",
        "intended_order_type": "limit",
        "maximum_size": Decimal("25"),
        "exposure_after_trade": Decimal("0.1200"),
        "exit_rule": "Exit if executable price reaches fair value or thesis invalidates.",
        "reason_trade_could_be_wrong": "Liquidity could disappear before exit or the resolution source could clarify against the thesis.",
        "config": TradeProposalPacketConfig(config_version="proposal-v1"),
        "generated_at": datetime(2026, 9, 3, 12, tzinfo=UTC),
    }
    values.update(overrides)
    return build_trade_proposal_packet(**values)
```

- [ ] **Step 2: Add required-field builder test**

Add:

```python
def test_build_trade_proposal_packet_records_required_human_review_fields():
    item = ready_queue_item()

    packet = proposal_packet(queue_item=item)

    assert packet.source_queue_item_id == item.queue_item_id
    assert packet.source_queue_rank == item.rank
    assert packet.source_manual_review_status == "paper_review_ready"
    assert packet.source_packet_id == item.packet_id
    assert packet.source_boundary_statement == item.boundary_statement
    assert packet.source_paper_only is True
    assert packet.condition_id == item.condition_id
    assert packet.token_id == item.token_id
    assert packet.market_slug == item.market_slug
    assert packet.market_url == item.market_url
    assert packet.question == item.question
    assert packet.outcome_name == item.outcome_name
    assert packet.strategy_type == item.strategy_type
    assert packet.side == "buy"
    assert packet.intended_order_type == "limit"
    assert packet.executable_price_assumption == item.expected_entry_price
    assert packet.maximum_size == Decimal("25")
    assert packet.source_max_executable_size == item.max_executable_size
    assert packet.cost_adjusted_edge == item.cost_adjusted_edge
    assert packet.thesis == item.thesis
    assert packet.invalidating_conditions == item.invalidating_conditions
    assert packet.rule_text_hash == item.rule_text_hash
    assert packet.resolution_source == item.resolution_source
    assert packet.risk_tags == item.risk_tags
    assert packet.exposure_after_trade == Decimal("0.1200")
    assert packet.exit_rule.startswith("Exit if executable price")
    assert "Liquidity could disappear" in packet.reason_trade_could_be_wrong
    assert packet.readiness_summary == item.readiness_summary
    assert packet.risk_summary == item.risk_summary
    assert packet.evidence_summary == item.evidence_summary
    assert packet.why_in_queue == item.why_in_queue
    assert packet.primary_reason_code == item.primary_reason_code
    assert packet.supporting_reason_codes == item.supporting_reason_codes
    assert packet.blocking_reason_codes == ()
    assert packet.review_focus == item.review_focus
    assert packet.history_status == item.history_status
    assert packet.forecast_status == item.forecast_status
    assert packet.history_gate_pass_count == item.history_gate_pass_count
    assert packet.forecast_gate_pass_count == item.forecast_gate_pass_count
    assert packet.history_gate_fail_count == item.history_gate_fail_count
    assert packet.forecast_gate_fail_count == item.forecast_gate_fail_count
    assert packet.evidence_scope == item.evidence_scope
    assert packet.risk_gate_passed is True
    assert packet.hard_block_count == 0
    assert packet.proposal_only is True
    assert packet.human_approval_required is True
    assert "not an approval workflow" in packet.boundary_statement
    assert "explicit human approval" in packet.boundary_statement
```

- [ ] **Step 3: Run the builder red test**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py::test_build_trade_proposal_packet_records_required_human_review_fields -q
```

Expected: FAIL because `build_trade_proposal_packet` still raises `NotImplementedError`.

## Task 4: Implement Builder And Packet Validation

**Files:**

- Modify: `src/polymarket_alpha_lab/proposal_packet.py`

- [ ] **Step 1: Add validation helpers**

Add helper functions to `proposal_packet.py` following the names used by dataclass `__post_init__`:

```python
def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_probability(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_probability(field_name, value)


def _require_executable_price(value: Decimal) -> None:
    _require_probability("executable_price_assumption", value)
    if value == ZERO or value == ONE:
        raise ValueError("executable_price_assumption must be greater than 0 and less than 1")
```

- [ ] **Step 2: Add boundary, config, and id helpers**

Add:

```python
def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    lowered = value.lower()
    required_parts = (
        "proposal-only",
        "human-review packet",
        "not an approval workflow",
        "trade instruction",
        "order instruction",
        "broker request",
        "live-execution signal",
        "explicit human approval",
    )
    if any(part not in lowered for part in required_parts):
        raise ValueError("boundary_statement must describe proposal-only human review")


def _validate_config(config: TradeProposalPacketConfig) -> None:
    _require_canonical_string("config_version", config.config_version)
    allowed_sides = _normalize_string_tuple("allowed_sides", config.allowed_sides)
    if not allowed_sides:
        raise ValueError("allowed_sides must not be empty")
    if any(side not in PROPOSAL_SIDES for side in allowed_sides):
        raise ValueError("allowed_sides must contain supported proposal sides")
    object.__setattr__(config, "allowed_sides", allowed_sides)
    allowed_order_types = _normalize_string_tuple(
        "allowed_intended_order_types",
        config.allowed_intended_order_types,
    )
    if not allowed_order_types:
        raise ValueError("allowed_intended_order_types must not be empty")
    object.__setattr__(config, "allowed_intended_order_types", allowed_order_types)
    _require_decimal("min_cost_adjusted_edge", config.min_cost_adjusted_edge)
    if config.max_proposal_size is not None:
        _require_positive_decimal("max_proposal_size", config.max_proposal_size)
    if config.max_exposure_after_trade is not None:
        _require_nonnegative_decimal(
            "max_exposure_after_trade",
            config.max_exposure_after_trade,
        )
    _require_boundary_statement(config.boundary_statement)


def _proposal_packet_id(
    *,
    config_version: str,
    generated_at: datetime,
    source_queue_item_id: str,
    side: str,
    intended_order_type: str,
    maximum_size: Decimal,
    exposure_after_trade: Decimal,
) -> str:
    raw = "|".join(
        (
            config_version,
            _as_utc(generated_at).isoformat(),
            source_queue_item_id,
            side,
            intended_order_type,
            str(maximum_size),
            str(exposure_after_trade),
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"proposal-{digest}"
```

- [ ] **Step 3: Add packet validation and queue-item clone**

Add:

```python
def _clone_queue_item(item: PaperManualReviewQueueItem) -> PaperManualReviewQueueItem:
    if type(item) is not PaperManualReviewQueueItem:
        raise ValueError("queue_item must be a PaperManualReviewQueueItem")
    return PaperManualReviewQueueItem(
        queue_item_id=item.queue_item_id,
        rank=item.rank,
        status=item.status,
        status_rank=item.status_rank,
        hard_block_count=item.hard_block_count,
        evidence_pass_count=item.evidence_pass_count,
        source_score=item.source_score,
        market_score_total=item.market_score_total,
        queued_at=item.queued_at,
        packet_id=item.packet_id,
        condition_id=item.condition_id,
        token_id=item.token_id,
        market_slug=item.market_slug,
        market_url=item.market_url,
        question=item.question,
        outcome_name=item.outcome_name,
        strategy_type=item.strategy_type,
        risk_tags=item.risk_tags,
        thesis=item.thesis,
        invalidating_conditions=item.invalidating_conditions,
        rule_text_hash=item.rule_text_hash,
        resolution_source=item.resolution_source,
        model_probability=item.model_probability,
        expected_entry_price=item.expected_entry_price,
        fair_value_estimate=item.fair_value_estimate,
        theoretical_edge=item.theoretical_edge,
        cost_adjusted_edge=item.cost_adjusted_edge,
        confidence=item.confidence,
        max_executable_size=item.max_executable_size,
        risk_gate_passed=item.risk_gate_passed,
        risk_reason_codes=item.risk_reason_codes,
        history_status=item.history_status,
        forecast_status=item.forecast_status,
        history_gate_pass_count=item.history_gate_pass_count,
        forecast_gate_pass_count=item.forecast_gate_pass_count,
        history_gate_fail_count=item.history_gate_fail_count,
        forecast_gate_fail_count=item.forecast_gate_fail_count,
        readiness_summary=item.readiness_summary,
        risk_summary=item.risk_summary,
        evidence_summary=item.evidence_summary,
        why_in_queue=item.why_in_queue,
        primary_reason_code=item.primary_reason_code,
        supporting_reason_codes=item.supporting_reason_codes,
        blocking_reason_codes=item.blocking_reason_codes,
        review_focus=item.review_focus,
        evidence_scope=item.evidence_scope,
        boundary_statement=item.boundary_statement,
        paper_only=item.paper_only,
    )


def _validate_ready_queue_item(item: PaperManualReviewQueueItem) -> None:
    if item.status != "paper_review_ready":
        raise ValueError("queue_item must be paper_review_ready")
    if item.paper_only is not True:
        raise ValueError("queue_item must be paper-only")
    if item.risk_gate_passed is not True:
        raise ValueError("queue_item risk gate must have passed")
    if item.hard_block_count != 0:
        raise ValueError("queue_item must not have hard blocks")
    if item.blocking_reason_codes:
        raise ValueError("queue_item must not have blocking reason codes")
    if item.market_url == "":
        raise ValueError("market_url is required")
    if item.expected_entry_price is None:
        raise ValueError("expected_entry_price is required")
    if item.max_executable_size is None:
        raise ValueError("max_executable_size is required")
    if item.cost_adjusted_edge is None:
        raise ValueError("cost_adjusted_edge is required")
    if not item.risk_tags:
        raise ValueError("risk_tags are required")
```

Add `_validate_packet(packet)` using the Public API Contract rules, including deterministic id verification:

```python
def _validate_packet(packet: TradeProposalPacket) -> None:
    object.__setattr__(packet, "generated_at", _as_utc(packet.generated_at))
    for field_name in (
        "proposal_packet_id",
        "proposal_config_version",
        "source_queue_item_id",
        "source_manual_review_status",
        "source_packet_id",
        "source_boundary_statement",
        "condition_id",
        "token_id",
        "market_slug",
        "market_url",
        "question",
        "outcome_name",
        "strategy_type",
        "side",
        "intended_order_type",
        "thesis",
        "invalidating_conditions",
        "rule_text_hash",
        "resolution_source",
        "exit_rule",
        "reason_trade_could_be_wrong",
        "readiness_summary",
        "risk_summary",
        "evidence_summary",
        "why_in_queue",
        "primary_reason_code",
        "evidence_scope",
    ):
        _require_canonical_string(field_name, getattr(packet, field_name))
    _require_boundary_statement(packet.boundary_statement)
    if packet.proposal_only is not True:
        raise ValueError("proposal_only must be True")
    if packet.human_approval_required is not True:
        raise ValueError("human_approval_required must be True")
    if packet.source_paper_only is not True:
        raise ValueError("source_paper_only must be True")
    if packet.source_manual_review_status != "paper_review_ready":
        raise ValueError("source_manual_review_status must be paper_review_ready")
    if packet.risk_gate_passed is not True:
        raise ValueError("risk_gate_passed must be True")
    if packet.hard_block_count != 0:
        raise ValueError("hard_block_count must be zero")
    if packet.source_queue_item_id != (
        f"{packet.condition_id}:{packet.token_id}:{packet.source_packet_id}"
    ):
        raise ValueError("source_queue_item_id must match condition_id:token_id:source_packet_id")
    if packet.source_queue_rank <= 0:
        raise ValueError("source_queue_rank must be positive")
    if packet.side not in PROPOSAL_SIDES:
        raise ValueError("side must be buy or sell")
    _require_executable_price(packet.executable_price_assumption)
    _require_positive_decimal("maximum_size", packet.maximum_size)
    _require_positive_decimal("source_max_executable_size", packet.source_max_executable_size)
    if packet.maximum_size > packet.source_max_executable_size:
        raise ValueError("maximum_size must be less than or equal to source_max_executable_size")
    _require_nonnegative_decimal("cost_adjusted_edge", packet.cost_adjusted_edge)
    _require_optional_finite_decimal("theoretical_edge", packet.theoretical_edge)
    _require_optional_probability("fair_value_estimate", packet.fair_value_estimate)
    _require_optional_probability("model_probability", packet.model_probability)
    _require_optional_probability("confidence", packet.confidence)
    _require_nonnegative_decimal("source_score", packet.source_score)
    _require_optional_finite_decimal("market_score_total", packet.market_score_total)
    _require_nonnegative_decimal("exposure_after_trade", packet.exposure_after_trade)
    object.__setattr__(packet, "risk_tags", _normalize_string_tuple("risk_tags", packet.risk_tags))
    object.__setattr__(
        packet,
        "supporting_reason_codes",
        _normalize_string_tuple("supporting_reason_codes", packet.supporting_reason_codes),
    )
    object.__setattr__(
        packet,
        "blocking_reason_codes",
        _normalize_string_tuple("blocking_reason_codes", packet.blocking_reason_codes),
    )
    object.__setattr__(
        packet,
        "review_focus",
        _normalize_string_tuple("review_focus", packet.review_focus),
    )
    if not packet.risk_tags:
        raise ValueError("risk_tags are required")
    if packet.blocking_reason_codes:
        raise ValueError("blocking_reason_codes must be empty")
    expected_id = _proposal_packet_id(
        config_version=packet.proposal_config_version,
        generated_at=packet.generated_at,
        source_queue_item_id=packet.source_queue_item_id,
        side=packet.side,
        intended_order_type=packet.intended_order_type,
        maximum_size=packet.maximum_size,
        exposure_after_trade=packet.exposure_after_trade,
    )
    if packet.proposal_packet_id != expected_id:
        raise ValueError("proposal_packet_id must match packet fields")
```

- [ ] **Step 4: Implement `build_trade_proposal_packet`**

Replace the `NotImplementedError` body with:

```python
    item = _clone_queue_item(queue_item)
    _validate_ready_queue_item(item)
    if type(config) is not TradeProposalPacketConfig:
        raise ValueError("config must be a TradeProposalPacketConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    generated_at = _as_utc(generated_at)
    _require_canonical_string("side", side)
    _require_canonical_string("intended_order_type", intended_order_type)
    if side not in config.allowed_sides:
        raise ValueError("side is not allowed by config")
    if intended_order_type not in config.allowed_intended_order_types:
        raise ValueError("intended_order_type is not allowed by config")
    _require_positive_decimal("maximum_size", maximum_size)
    _require_nonnegative_decimal("exposure_after_trade", exposure_after_trade)
    _require_canonical_string("exit_rule", exit_rule)
    _require_canonical_string(
        "reason_trade_could_be_wrong",
        reason_trade_could_be_wrong,
    )
    if maximum_size > item.max_executable_size:
        raise ValueError("maximum_size must not exceed source max_executable_size")
    if config.max_proposal_size is not None and maximum_size > config.max_proposal_size:
        raise ValueError("maximum_size exceeds max_proposal_size")
    if item.cost_adjusted_edge < config.min_cost_adjusted_edge:
        raise ValueError("cost_adjusted_edge is below minimum")
    if (
        config.max_exposure_after_trade is not None
        and exposure_after_trade > config.max_exposure_after_trade
    ):
        raise ValueError("exposure_after_trade exceeds maximum")
    packet_id = _proposal_packet_id(
        config_version=config.config_version,
        generated_at=generated_at,
        source_queue_item_id=item.queue_item_id,
        side=side,
        intended_order_type=intended_order_type,
        maximum_size=maximum_size,
        exposure_after_trade=exposure_after_trade,
    )
    return TradeProposalPacket(
        proposal_packet_id=packet_id,
        generated_at=generated_at,
        proposal_config_version=config.config_version,
        proposal_only=True,
        human_approval_required=True,
        boundary_statement=config.boundary_statement,
        source_queue_item_id=item.queue_item_id,
        source_queue_rank=item.rank,
        source_manual_review_status=item.status,
        source_packet_id=item.packet_id,
        source_boundary_statement=item.boundary_statement,
        source_paper_only=item.paper_only,
        condition_id=item.condition_id,
        token_id=item.token_id,
        market_slug=item.market_slug,
        market_url=item.market_url,
        question=item.question,
        outcome_name=item.outcome_name,
        strategy_type=item.strategy_type,
        side=side,
        intended_order_type=intended_order_type,
        executable_price_assumption=item.expected_entry_price,
        maximum_size=maximum_size,
        source_max_executable_size=item.max_executable_size,
        cost_adjusted_edge=item.cost_adjusted_edge,
        theoretical_edge=item.theoretical_edge,
        fair_value_estimate=item.fair_value_estimate,
        model_probability=item.model_probability,
        confidence=item.confidence,
        source_score=item.source_score,
        market_score_total=item.market_score_total,
        thesis=item.thesis,
        invalidating_conditions=item.invalidating_conditions,
        rule_text_hash=item.rule_text_hash,
        resolution_source=item.resolution_source,
        risk_tags=item.risk_tags,
        exposure_after_trade=exposure_after_trade,
        exit_rule=exit_rule,
        reason_trade_could_be_wrong=reason_trade_could_be_wrong,
        readiness_summary=item.readiness_summary,
        risk_summary=item.risk_summary,
        evidence_summary=item.evidence_summary,
        why_in_queue=item.why_in_queue,
        primary_reason_code=item.primary_reason_code,
        supporting_reason_codes=item.supporting_reason_codes,
        blocking_reason_codes=item.blocking_reason_codes,
        review_focus=item.review_focus,
        history_status=item.history_status,
        forecast_status=item.forecast_status,
        history_gate_pass_count=item.history_gate_pass_count,
        forecast_gate_pass_count=item.forecast_gate_pass_count,
        history_gate_fail_count=item.history_gate_fail_count,
        forecast_gate_fail_count=item.forecast_gate_fail_count,
        evidence_scope=item.evidence_scope,
        risk_gate_passed=item.risk_gate_passed,
        hard_block_count=item.hard_block_count,
    )
```

- [ ] **Step 5: Run the builder green test**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py::test_build_trade_proposal_packet_records_required_human_review_fields -q
```

Expected: PASS.

## Task 5: Write Validation And Boundary Tests

**Files:**

- Modify: `tests/test_proposal_packet.py`

- [ ] **Step 1: Add non-ready source rejection test**

Add:

```python
def test_trade_proposal_packet_rejects_non_ready_manual_review_items():
    cases = (
        "insufficient_evidence",
        "blocked_by_risk",
        "blocked_by_quality",
        "incomplete_data",
    )

    for status in cases:
        with pytest.raises(ValueError, match="paper_review_ready|queue_item"):
            proposal_packet(
                queue_item=replace(
                    ready_queue_item(),
                    status=status,
                    status_rank=STATUS_RANK[status],
                )
            )
```

- [ ] **Step 2: Add invalid public input test**

Add:

```python
@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("side", "hold"),
        ("intended_order_type", " "),
        ("maximum_size", Decimal("0")),
        ("maximum_size", Decimal("NaN")),
        ("maximum_size", Decimal("101")),
        ("exposure_after_trade", Decimal("-0.0001")),
        ("exposure_after_trade", Decimal("NaN")),
        ("exit_rule", " "),
        ("reason_trade_could_be_wrong", " "),
        ("generated_at", "2026-09-03"),
    ),
)
def test_trade_proposal_packet_rejects_invalid_public_inputs_and_values(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        proposal_packet(**{field_name: bad_value})


def test_trade_proposal_packet_rejects_invalid_config_and_source_type():
    with pytest.raises(ValueError, match="queue_item"):
        proposal_packet(queue_item=object())
    with pytest.raises(ValueError, match="config"):
        proposal_packet(config=object())
    with pytest.raises(ValueError, match="allowed_sides"):
        TradeProposalPacketConfig(config_version="proposal-v1", allowed_sides=())
    with pytest.raises(ValueError, match="allowed_sides"):
        TradeProposalPacketConfig(config_version="proposal-v1", allowed_sides=("hold",))
    with pytest.raises(ValueError, match="allowed_intended_order_types"):
        TradeProposalPacketConfig(
            config_version="proposal-v1",
            allowed_intended_order_types=(),
        )
    with pytest.raises(ValueError, match="max_proposal_size"):
        TradeProposalPacketConfig(
            config_version="proposal-v1",
            max_proposal_size=Decimal("0"),
        )
```

- [ ] **Step 3: Add Gate 6 missing-field tests**

Add:

```python
@pytest.mark.parametrize(
    "field_name,bad_value",
    (
        ("market_url", ""),
        ("thesis", " "),
        ("invalidating_conditions", " "),
        ("rule_text_hash", " "),
        ("resolution_source", " "),
        ("risk_tags", ()),
        ("expected_entry_price", None),
        ("expected_entry_price", Decimal("0")),
        ("expected_entry_price", Decimal("1")),
        ("expected_entry_price", Decimal("NaN")),
        ("max_executable_size", None),
        ("max_executable_size", Decimal("0")),
        ("cost_adjusted_edge", None),
        ("cost_adjusted_edge", Decimal("-0.0001")),
    ),
)
def test_trade_proposal_packet_rejects_missing_gate_6_packet_fields(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        proposal_packet(queue_item=replace(ready_queue_item(), **{field_name: bad_value}))
```

- [ ] **Step 4: Add UTC, frozen, invariant, and boundary tests**

Add:

```python
def test_trade_proposal_packet_timestamps_normalize_to_utc():
    packet = proposal_packet(
        generated_at=datetime(2026, 9, 3, 8, 31, tzinfo=timezone(timedelta(hours=8))),
    )

    assert packet.generated_at == datetime(2026, 9, 3, 0, 31, tzinfo=UTC)


def test_trade_proposal_packet_dataclasses_are_frozen_and_validate_invariants():
    packet = proposal_packet()

    with pytest.raises(FrozenInstanceError):
        packet.maximum_size = Decimal("1")
    with pytest.raises(ValueError, match="proposal_packet_id"):
        replace(packet, proposal_packet_id="bad")
    with pytest.raises(ValueError, match="human_approval_required"):
        replace(packet, human_approval_required=False)
    with pytest.raises(ValueError, match="proposal_only"):
        replace(packet, proposal_only=False)
    with pytest.raises(ValueError, match="source_queue_item_id"):
        replace(packet, source_queue_item_id="condition-1:token-1:other-packet")
    with pytest.raises(ValueError, match="blocking_reason_codes"):
        replace(packet, blocking_reason_codes=("risk_gate:drawdown",))


def test_trade_proposal_packet_boundary_statement_contract():
    config = TradeProposalPacketConfig(config_version="proposal-v1")
    assert config.boundary_statement == (
        "This is a proposal-only human-review packet, not an approval workflow, "
        "trade instruction, order instruction, broker request, strategy-promotion "
        "signal, or live-execution signal; no order may leave the system without "
        "explicit human approval."
    )

    for boundary_statement in (
        "proposal-only human-review packet, not an approval workflow, trade instruction, order instruction.",
        "This is a human-review packet, not an approval workflow, trade instruction, order instruction, broker request, strategy-promotion signal, or live-execution signal; no order may leave the system without explicit human approval.",
        "This is a proposal-only human-review packet.",
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalPacketConfig(
                config_version="proposal-v1",
                boundary_statement=boundary_statement,
            )
```

- [ ] **Step 5: Run validation red tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py::test_trade_proposal_packet_rejects_non_ready_manual_review_items tests/test_proposal_packet.py::test_trade_proposal_packet_rejects_invalid_public_inputs_and_values tests/test_proposal_packet.py::test_trade_proposal_packet_rejects_invalid_config_and_source_type tests/test_proposal_packet.py::test_trade_proposal_packet_rejects_missing_gate_6_packet_fields tests/test_proposal_packet.py::test_trade_proposal_packet_timestamps_normalize_to_utc tests/test_proposal_packet.py::test_trade_proposal_packet_dataclasses_are_frozen_and_validate_invariants tests/test_proposal_packet.py::test_trade_proposal_packet_boundary_statement_contract -q
```

Expected: At least one test fails because validation is not complete yet.

## Task 6: Harden Validation To Pass Tests

**Files:**

- Modify: `src/polymarket_alpha_lab/proposal_packet.py`

- [ ] **Step 1: Complete validation gaps**

Update helper validation so every field in Task 5 is rejected by the named field. The required behavior is:

```python
if item.cost_adjusted_edge is None:
    raise ValueError("cost_adjusted_edge is required")
_require_nonnegative_decimal("cost_adjusted_edge", item.cost_adjusted_edge)
if item.expected_entry_price is None:
    raise ValueError("expected_entry_price is required")
_require_decimal("expected_entry_price", item.expected_entry_price)
if item.expected_entry_price <= ZERO or item.expected_entry_price >= ONE:
    raise ValueError("expected_entry_price must be greater than 0 and less than 1")
if item.max_executable_size is None:
    raise ValueError("max_executable_size is required")
_require_positive_decimal("max_executable_size", item.max_executable_size)
```

Add equivalent checks for `market_url`, `risk_tags`, and all caller-supplied fields listed in Task 5.

- [ ] **Step 2: Run validation green tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py -q
```

Expected: PASS except JSONL tests, if JSONL tests have not been added yet.

## Task 7: Write JSONL Persistence Tests

**Files:**

- Modify: `tests/test_proposal_packet.py`

- [ ] **Step 1: Add JSONL append test**

Add:

```python
def test_trade_proposal_packet_log_appends_jsonl_packet(tmp_path):
    packet = proposal_packet()
    log = TradeProposalPacketLog(path=tmp_path / "proposal-packets.jsonl")

    log.append(packet)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"blocking_reason_codes"')
    stored = json.loads(lines[0])
    assert stored["proposal_only"] is True
    assert stored["human_approval_required"] is True
    assert stored["generated_at"] == "2026-09-03T12:00:00+00:00"
    assert stored["proposal_config_version"] == "proposal-v1"
    assert stored["maximum_size"] == "25"
    assert stored["exposure_after_trade"] == "0.1200"
    assert stored["risk_tags"] == ["liquidity", "event-risk"]
    assert stored["boundary_statement"] == packet.boundary_statement
```

- [ ] **Step 2: Add append/no-overwrite and path tests**

Add:

```python
def test_trade_proposal_packet_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    packet = proposal_packet()
    log = TradeProposalPacketLog(path=str(tmp_path / "nested" / "proposal-packets.jsonl"))

    log.append(packet)
    log.append(packet)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["proposal_packet_id"] == packet.proposal_packet_id
    assert json.loads(lines[1])["proposal_packet_id"] == packet.proposal_packet_id


def test_trade_proposal_packet_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalPacketLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalPacketLog(path=existing_file / "proposal-packets.jsonl")

    path = tmp_path / "proposal-packets.jsonl"
    log = TradeProposalPacketLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalPacket"):
        log.append(object())
    assert not path.exists()
```

- [ ] **Step 3: Add validate-before-open failure tests**

Add:

```python
def test_trade_proposal_packet_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    packet = proposal_packet()
    object.__setattr__(packet, "maximum_size", Decimal("NaN"))
    path = tmp_path / "proposal-packets.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalPacketLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable|maximum_size"):
        log.append(packet)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_packet_log_rejects_non_finite_decimal_before_open(tmp_path):
    packet = proposal_packet()
    object.__setattr__(packet, "cost_adjusted_edge", Decimal("NaN"))
    log = TradeProposalPacketLog(path=tmp_path / "proposal-packets.jsonl")

    with pytest.raises(ValueError, match="finite|cost_adjusted_edge"):
        log.append(packet)

    assert not log.path.exists()
```

- [ ] **Step 4: Run JSONL red tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py::test_trade_proposal_packet_log_appends_jsonl_packet tests/test_proposal_packet.py::test_trade_proposal_packet_log_appends_without_overwriting_and_creates_parent_dirs tests/test_proposal_packet.py::test_trade_proposal_packet_log_rejects_invalid_paths_and_inputs tests/test_proposal_packet.py::test_trade_proposal_packet_log_preserves_existing_file_when_validation_fails tests/test_proposal_packet.py::test_trade_proposal_packet_log_rejects_non_finite_decimal_before_open -q
```

Expected: FAIL because `TradeProposalPacketLog.append` still raises `NotImplementedError`.

## Task 8: Implement JSONL Persistence

**Files:**

- Modify: `src/polymarket_alpha_lab/proposal_packet.py`

- [ ] **Step 1: Implement log path and JSON helpers**

Add:

```python
def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
```

- [ ] **Step 2: Add packet tree validator**

Add:

```python
def _validate_packet_tree(packet: TradeProposalPacket) -> TradeProposalPacket:
    return TradeProposalPacket(
        proposal_packet_id=packet.proposal_packet_id,
        generated_at=packet.generated_at,
        proposal_config_version=packet.proposal_config_version,
        proposal_only=packet.proposal_only,
        human_approval_required=packet.human_approval_required,
        boundary_statement=packet.boundary_statement,
        source_queue_item_id=packet.source_queue_item_id,
        source_queue_rank=packet.source_queue_rank,
        source_manual_review_status=packet.source_manual_review_status,
        source_packet_id=packet.source_packet_id,
        source_boundary_statement=packet.source_boundary_statement,
        source_paper_only=packet.source_paper_only,
        condition_id=packet.condition_id,
        token_id=packet.token_id,
        market_slug=packet.market_slug,
        market_url=packet.market_url,
        question=packet.question,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        side=packet.side,
        intended_order_type=packet.intended_order_type,
        executable_price_assumption=packet.executable_price_assumption,
        maximum_size=packet.maximum_size,
        source_max_executable_size=packet.source_max_executable_size,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        theoretical_edge=packet.theoretical_edge,
        fair_value_estimate=packet.fair_value_estimate,
        model_probability=packet.model_probability,
        confidence=packet.confidence,
        source_score=packet.source_score,
        market_score_total=packet.market_score_total,
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text_hash=packet.rule_text_hash,
        resolution_source=packet.resolution_source,
        risk_tags=packet.risk_tags,
        exposure_after_trade=packet.exposure_after_trade,
        exit_rule=packet.exit_rule,
        reason_trade_could_be_wrong=packet.reason_trade_could_be_wrong,
        readiness_summary=packet.readiness_summary,
        risk_summary=packet.risk_summary,
        evidence_summary=packet.evidence_summary,
        why_in_queue=packet.why_in_queue,
        primary_reason_code=packet.primary_reason_code,
        supporting_reason_codes=packet.supporting_reason_codes,
        blocking_reason_codes=packet.blocking_reason_codes,
        review_focus=packet.review_focus,
        history_status=packet.history_status,
        forecast_status=packet.forecast_status,
        history_gate_pass_count=packet.history_gate_pass_count,
        forecast_gate_pass_count=packet.forecast_gate_pass_count,
        history_gate_fail_count=packet.history_gate_fail_count,
        forecast_gate_fail_count=packet.forecast_gate_fail_count,
        evidence_scope=packet.evidence_scope,
        risk_gate_passed=packet.risk_gate_passed,
        hard_block_count=packet.hard_block_count,
    )
```

- [ ] **Step 3: Implement `TradeProposalPacketLog.append`**

Replace the `NotImplementedError` body with:

```python
    def append(self, packet: TradeProposalPacket) -> None:
        if not isinstance(packet, TradeProposalPacket):
            raise ValueError("packet must be a TradeProposalPacket")
        validated = _validate_packet_tree(packet)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
```

- [ ] **Step 4: Run JSONL green tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py -q
```

Expected: PASS.

## Task 9: Update README And Repository Layout

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Update Phase 1 contents sentence**

In `README.md`, update the Phase 1 sentence so it includes `human-review proposal packet artifacts` after the manual-review queue phrase. The sentence must not imply live execution.

- [ ] **Step 2: Add Level 2 Node 1 status section**

Insert after the `Level 1B Node 6 Python API` section and before `Automation Roadmap`:

```markdown
## Level 2 Node 1 Status

Level 2 Node 1 adds reviewable proposal-packet artifacts over supplied paper-trading, analytics, forecast-evidence, and manual-review artifacts. A proposal packet is for human review only; it is not an approval workflow, trade instruction, order instruction, broker request, strategy-promotion signal, or live-execution signal. No order may leave the system without explicit human approval.

It does not fetch market, order-book, price-history, outcome, or account data; scrape websites; authenticate; handle private keys or credentials; place, submit, sign, or cancel orders; open user WebSockets; run heartbeat logic; use a trading SDK, broker client, or execution client; reconcile exchange accounts; import manual executions; or perform compliance/legal/geographic analysis.

## Level 2 Node 1 Python API

Node 1 is exposed through Python APIs:

- Configure proposal packet limits and boundary text with `TradeProposalPacketConfig(config_version="proposal-v1")`.
- Build proposal packets with `build_trade_proposal_packet(queue_item, side="buy", intended_order_type="limit", maximum_size=Decimal("25"), exposure_after_trade=Decimal("0.1200"), exit_rule="Exit if executable price reaches fair value or thesis invalidates.", reason_trade_could_be_wrong="Liquidity could disappear before exit.", config=config, generated_at=datetime.now(UTC))`, which returns `TradeProposalPacket`.
- Inspect proposal-only review fields with `TradeProposalPacket`.
- Persist proposal packet snapshots with `TradeProposalPacketLog(path).append(packet)`.
```

- [ ] **Step 3: Update Repository Layout**

Add `2026-06-14-level-2-proposal-packets.md` directly after `2026-06-14-level-1b-paper-manual-review-queue.md`.

Add `proposal_packet.py` under `src/polymarket_alpha_lab`.

Add `test_proposal_packet.py` and `test_proposal_packet_scope.py` under `tests`.

- [ ] **Step 4: Run README text checks**

Run:

```bash
rg -n "Level 2 Node 1|TradeProposalPacket|proposal packet|explicit human approval|live-execution signal" README.md
```

Expected: output shows the new Level 2 sections and API symbols.

## Task 10: Run Focused And Full Verification

**Files:**

- Read only.

- [ ] **Step 1: Run proposal packet focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_proposal_packet.py tests/test_proposal_packet_scope.py tests/test_init.py -q
```

Expected: PASS.

- [ ] **Step 2: Run existing scope tests affected by root exports**

Run:

```bash
.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q
```

Expected: PASS. The old root-export checks now allow only the exact Level 2 proposal packet exports and continue rejecting all other forbidden surfaces.

- [ ] **Step 3: Run full test suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run whitespace and CodeGraph verification**

Run:

```bash
git diff --check
codegraph status .
```

Expected: no whitespace errors, and CodeGraph reports the index is up to date or indicates the exact command needed to refresh it. If CodeGraph is stale after source changes, run:

```bash
codegraph index .
codegraph status .
```

Expected: CodeGraph reports the index is up to date.

## Task 11: Claude Implementation Review

**Files:**

- Read only unless Claude finds Critical or Important issues.

- [ ] **Step 1: Capture changed files**

Run:

```bash
git status --short --branch --untracked-files=all
git diff -- src/polymarket_alpha_lab/proposal_packet.py src/polymarket_alpha_lab/__init__.py tests/test_proposal_packet.py tests/test_proposal_packet_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md
```

- [ ] **Step 2: Submit compact implementation review**

Run this command after full verification:

```bash
{
  printf '%s\n' 'Review this Level 2 proposal-packets implementation for polymarket-alpha-lab before commit.'
  printf '%s\n' 'This is a read-only, self-contained implementation review. Use only the material in this prompt. Do not edit files.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Classify findings as Critical, Important, or Minor.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the included repository instructions, roadmap/spec material, validation gates, implementation files, tests, docs, or verification output.'
  printf '%s\n' 'Verdict policy:'
  printf '%s\n' '- Proceed: zero Critical/Important findings; implementation is safe to commit as written.'
  printf '%s\n' '- Proceed with fixes: zero Critical/Important findings; only Minor follow-up remains.'
  printf '%s\n' '- Blocked: any Critical/Important finding, missing required review material, unsafe scope, or ambiguity that could cause incorrect behavior.'
  printf '%s\n' 'Review specifically: proposal-only artifact semantics, no approval workflow, no live execution, no credential/account/order placement surfaces, Gate 6 completeness, Decimal and UTC validation, JSONL validate-before-open behavior, root-export allowlist migration, README wording, tests, verification evidence, Handoff Summary requirement, and commit/push readiness.'
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
  printf '%s\n' 'Level 2 roadmap and Gate 6 context:'
  sed -n '76,96p' docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md
  sed -n '97,113p' docs/research/validation-gates.md
  printf '%s\n' ''
  printf '%s\n' 'Fresh verification output:'
  printf '%s\n' 'Include the exact focused pytest, full pytest, git diff --check, and CodeGraph status outputs captured immediately before this review.'
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Changed file contents:'
  for path in \
    src/polymarket_alpha_lab/proposal_packet.py \
    src/polymarket_alpha_lab/__init__.py \
    tests/test_proposal_packet.py \
    tests/test_proposal_packet_scope.py \
    tests/test_init.py \
    tests/test_analytics_scope.py \
    tests/test_analytics_history_scope.py \
    tests/test_forecast_evidence_scope.py \
    tests/test_manual_review_queue_scope.py \
    README.md \
    docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md
  do
    printf '%s\n' "===== ${path} ====="
    cat "$path"
  done
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Accepted implementation-review terminal state: a fresh Claude review response that explicitly reports `Critical findings: 0`, `Important findings: 0`, and a verdict of `Proceed` or `Proceed with fixes`. Any Critical finding, Important finding, missing count line, ambiguous verdict, unsafe scope, missing implementation material, missing verification output, or transport failure is treated as `Blocked`.

If the full prompt is blocked by transport size, rerun a compact prompt that still includes relevant `AGENTS.md` instructions, the Level 2 roadmap/Gate 6 excerpt, fresh verification output, fresh git status, full content of every modified or untracked file, and the same count/verdict policy.

## Task 12: Handoff Summary, Commit, And Push

**Files:**

- Modify: `docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md`

- [ ] **Step 1: Append Handoff Summary**

Append a short section with this shape, replacing each description with the actual values from fresh command output:

```markdown
## Handoff Summary

- Repo status: branch name plus clean or dirty status from `git status --short --branch`.
- Verified commands: focused pytest command and result, scope pytest command and result, full pytest command and result, `git diff --check`, and `codegraph status .`.
- Claude reviews: plan-review verdict and counts, implementation-review verdict and counts.
- Uncommitted files before commit: short list from `git status --short`.
- Next step: next node recommendation.
```

- [ ] **Step 2: Final pre-commit checks**

Run:

```bash
git diff --check
git status --short --branch --untracked-files=all
```

Expected: no whitespace errors, and only intended files are modified or untracked.

- [ ] **Step 3: Commit**

Run:

```bash
git add src/polymarket_alpha_lab/proposal_packet.py src/polymarket_alpha_lab/__init__.py tests/test_proposal_packet.py tests/test_proposal_packet_scope.py tests/test_init.py tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py README.md docs/superpowers/plans/2026-06-14-level-2-proposal-packets.md
git commit -m "feat: add level 2 proposal packets"
```

Expected: commit succeeds.

- [ ] **Step 4: Push**

Run:

```bash
git push
```

Expected: push succeeds.

- [ ] **Step 5: Final status**

Run:

```bash
git status --short --branch
```

Expected: clean worktree on `main` tracking `origin/main`.

## Handoff Summary

- Repo status: `main` tracking `origin/main`; working tree contains intended Level 2 Node 1 changes before final staging.
- Verified commands: baseline `.venv/bin/python -m pytest -q` passed with `375 passed`; post-review focused proposal verification `.venv/bin/python -m pytest tests/test_proposal_packet.py -q` passed with `45 passed`; post-review focused proposal/init verification `.venv/bin/python -m pytest tests/test_proposal_packet.py tests/test_proposal_packet_scope.py tests/test_init.py -q` passed with `59 passed`; migrated scope verification `.venv/bin/python -m pytest tests/test_analytics_scope.py tests/test_analytics_history_scope.py tests/test_forecast_evidence_scope.py tests/test_manual_review_queue_scope.py -q` passed with `21 passed`; post-review full verification `.venv/bin/python -m pytest -q` passed with `427 passed`; `git diff --check` passed; `codegraph status .` reports the index is up to date.
- Claude reviews: plan review `Critical findings: 0`, `Important findings: 0`, `Minor findings: 0`, `Verdict: Proceed`; implementation review `Critical findings: 0`, `Important findings: 0`, `Minor findings: 3`, `Verdict: Proceed with fixes`.
- Post-review fixes: corrected stale boundary wording in this plan to `order instruction`; added builder rejection coverage for source queue safety gates; added black-box proposal id deterministic and input-sensitive coverage.
- Uncommitted files before commit: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `src/polymarket_alpha_lab/proposal_packet.py`, `tests/test_proposal_packet.py`, `tests/test_proposal_packet_scope.py`, `tests/test_init.py`, `tests/test_analytics_scope.py`, `tests/test_analytics_history_scope.py`, `tests/test_forecast_evidence_scope.py`, `tests/test_manual_review_queue_scope.py`, and this plan file.
- Next step: commit and push this node, then start a separate Claude-reviewed Level 2 Node 2 plan for explicit human-approval record artifacts while continuing to exclude broker, credential, account, and live-order behavior.
