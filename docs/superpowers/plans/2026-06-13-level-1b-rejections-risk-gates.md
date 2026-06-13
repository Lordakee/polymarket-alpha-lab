# Level 1B Rejections And Risk Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first Level 1B paper-only control layer: configurable entry risk gates plus append-only rejected-candidate logs with explicit reason codes.

**Architecture:** Keep gate evaluation and rejection persistence separate. `risk.py` evaluates complete or incomplete `ResearchPacket` objects against a frozen `RiskGateConfig` and returns structured reasons. `rejections.py` persists rejected candidates as JSONL audit records only when a gate decision is rejected. No module may authenticate, place orders, cancel orders, open user WebSockets, send heartbeat requests, or touch private keys.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSONL files, existing `ResearchPacket`, `pytest`, CodeGraph.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1B Node 1 until Claude Code returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.
3. Before every node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - the node-specific pytest command for that node.
   - `.venv/bin/python -m pytest`.
   - `git diff --check`; after staging, also run `git diff --cached --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - Claude Code review with `claude-opus-4-8`, `--effort max`, covering the node diff, untracked files, verification output, and the next node plan when one exists.
4. Do not commit or push a node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
5. After the node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, and next step.

Level 1B Node 1 must not add:

- account authentication
- private-key handling
- live trading
- automated order placement
- order cancellation
- user WebSocket
- REST heartbeat
- trading SDK
- human approval proposal workflow
- compliance/legal/geographic-access analysis

## Level 1B Node 1 Scope

This node adds only the accept/reject control plane for paper candidates:

- configurable entry risk thresholds
- structured gate decisions and reason codes
- append-only rejected-candidate JSONL records
- public API exports and README status text

This node intentionally does not add paper position ledgers, executable NAV marks, exposure analytics, realized PnL, calibration, dashboards, or performance reports. Those depend on having accepted/rejected candidate decisions and are deferred to later Level 1B nodes.

## Target File Structure

- Create: `src/polymarket_alpha_lab/risk.py`
  - Frozen risk config, structured gate reasons, and deterministic `ResearchPacket` evaluation.
- Create: `src/polymarket_alpha_lab/rejections.py`
  - Rejected-candidate record factory and JSONL append-only log writer.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1B Node 1 public APIs.
- Create: `tests/test_risk_gates.py`
  - Config validation, accept/reject gate evaluation, and reason-code tests.
- Create: `tests/test_rejections.py`
  - Rejected-candidate JSONL persistence and validation tests.
- Modify: `tests/test_init.py`
  - Package-root export contract for risk/rejection APIs.
- Modify: `README.md`
  - Add Level 1B Node 1 paper-only status and Python API notes.
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-rejections-risk-gates.md`
  - Update gate results and handoff notes as the node is completed.

## Public API Contract

Create these names:

```python
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)
from polymarket_alpha_lab.rejections import (
    RejectedCandidateLog,
    RejectedCandidateRecord,
)
```

Export all six from `polymarket_alpha_lab.__init__`.

## Risk Gate Semantics

`RiskGateConfig` is frozen and finite-only:

```python
@dataclass(frozen=True)
class RiskGateConfig:
    config_version: str
    min_confidence: Decimal = Decimal("0.50")
    min_cost_adjusted_edge: Decimal = Decimal("0.00")
    max_spread: Decimal = Decimal("0.10")
    max_slippage_estimate: Decimal = Decimal("0.02")
    min_max_executable_size: Decimal = Decimal("1")
    allowed_strategy_types: tuple[str, ...] = ()
    blocked_risk_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "allowed_strategy_types",
            _normalize_string_sequence("allowed_strategy_types", self.allowed_strategy_types),
        )
        object.__setattr__(
            self,
            "blocked_risk_tags",
            _normalize_string_sequence("blocked_risk_tags", self.blocked_risk_tags),
        )
        _validate_config(self)
```

`evaluate_research_packet_risk(packet, config)` returns a frozen `RiskGateDecision`:

```python
@dataclass(frozen=True)
class RiskGateReason:
    code: str
    message: str
    field_name: str
    observed_value: Decimal | str | None = None
    threshold: Decimal | str | None = None

    def __post_init__(self) -> None:
        _validate_reason(self)


@dataclass(frozen=True)
class RiskGateDecision:
    accepted: bool
    config_version: str
    reasons: tuple[RiskGateReason, ...]

    def __post_init__(self) -> None:
        try:
            normalized_reasons = tuple(self.reasons)
        except TypeError as exc:
            raise ValueError("reasons must be a sequence of RiskGateReason values") from exc
        object.__setattr__(self, "reasons", normalized_reasons)
        if not isinstance(self.accepted, bool):
            raise ValueError("accepted must be a bool")
        if not isinstance(self.config_version, str) or not self.config_version.strip():
            raise ValueError("config_version is required")
        for reason in self.reasons:
            if not isinstance(reason, RiskGateReason):
                raise ValueError("reasons must contain RiskGateReason values")
        if self.accepted and self.reasons:
            raise ValueError("accepted decisions must not include reasons")
        if not self.accepted and not self.reasons:
            raise ValueError("rejected decisions must include at least one reason")
```

Reason codes are stable strings:

- `incomplete_packet`
- `low_confidence`
- `low_cost_adjusted_edge`
- `wide_spread`
- `high_slippage`
- `insufficient_executable_size`
- `strategy_not_allowed`
- `blocked_risk_tag`

Public APIs must raise controlled `ValueError` exceptions for invalid public inputs rather than leaking `AttributeError` or `TypeError`. `RiskGateConfig.config_version`, `RiskGateDecision.config_version`, and `RiskGateReason.code/message/field_name` must be strings. `RiskGateConfig.allowed_strategy_types` and `RiskGateConfig.blocked_risk_tags` may be non-string sequences, but not bare `str`/`bytes`, and every member must be a nonblank string. `RiskGateReason.observed_value` and `RiskGateReason.threshold`, when present, must be `Decimal` or `str`. `RiskGateReason` only validates observed/threshold value types; finite Decimal validation for rejection-log persistence occurs in `RejectedCandidateLog.append()` before the file is opened.

`RiskGateDecision` enforces decision invariants at construction: `accepted` must be a bool, accepted decisions must have `reasons == ()`, rejected decisions must contain one or more reasons, and every reason must be a `RiskGateReason`. `incomplete_packet` is intentionally terminal because downstream numeric gates may depend on missing fields. Complete packets use deterministic reason order:

1. strategy allowlist
2. blocked risk tags, in the packet tag order
3. confidence
4. cost-adjusted edge
5. spread
6. slippage
7. executable size

## Part 0: Existing Contract Check

**Goal:** Reconfirm current Level 1A APIs before implementing Level 1B Node 1.

**Files:**

- Inspect: `src/polymarket_alpha_lab/research.py`
- Inspect: `src/polymarket_alpha_lab/pipeline.py`
- Inspect: `src/polymarket_alpha_lab/__init__.py`
- Inspect: `tests/test_research.py`
- Inspect: `tests/test_journal.py`

- [x] **Step 1: Inspect current contracts with CodeGraph**

Run:

```bash
codegraph explore "ResearchPacket build_research_packet ScoredCandidate package exports"
codegraph node src/polymarket_alpha_lab/research.py
codegraph node src/polymarket_alpha_lab/__init__.py
```

Expected: confirm `ResearchPacket` exposes `packet_id`, `created_at`, `condition_id`, `token_id`, `market_slug`, `market_url`, `question`, `outcome_name`, `strategy_type`, `source_score`, `raw_archive_path`, `risk_tags`, `rule_text_hash`, `resolution_source`, `missing_required_fields()`, and finite-aware completeness checks.

Also explicitly confirm that every numeric field used by `evaluate_research_packet_risk()` is included in finite-aware completeness checks:

- `confidence`
- `cost_adjusted_edge`
- `spread`
- `slippage_estimate`
- `max_executable_size`

Regardless of the Level 1A result, implement a small runtime defensive check inside `evaluate_research_packet_risk()` for the exact Level 1B numeric fields above before numeric comparisons. The defensive check must return terminal `incomplete_packet` for `None`, non-`Decimal`, or non-finite values and must not rely on `assert` statements for runtime safety. Keep Level 1A completeness semantics for nonpositive executable size: `max_executable_size <= 0` is terminal incomplete packet data and should surface as `positive_max_executable_size` via `packet.missing_required_fields()`. The `insufficient_executable_size` risk reason is only for positive, finite executable sizes that are below `RiskGateConfig.min_max_executable_size`.

Part 0 is a blocking step before creating test files. If these contracts differ, update this plan before writing implementation tests. If `build_research_packet()` or `dataclasses.replace()` cannot construct an incomplete or invalid-type packet shape used by the planned tests, adapt the tests to a Level 1A-supported construction path before the RED run instead of weakening Level 1A invariants.

**Recorded result:** Completed before implementation. `codegraph explore "ResearchPacket build_research_packet ScoredCandidate package exports"`, `codegraph node src/polymarket_alpha_lab/research.py`, `codegraph node src/polymarket_alpha_lab/__init__.py`, and `codegraph node src/polymarket_alpha_lab/pipeline.py` confirmed the Level 1A contracts. `ResearchPacket` exposes the planned Level 1B inputs. `build_research_packet()` can construct the planned incomplete fixtures. `dataclasses.replace()` can construct the planned invalid numeric-type fixtures. `ResearchPacket.missing_required_fields()` reports `positive_max_executable_size` for invalid executable-size completeness and can raise `AttributeError` for non-`Decimal` `max_executable_size`, so Level 1B keeps the defensive numeric check before using Level 1A completeness results.

## Part 1: Risk Gates

**Goal:** Evaluate research packets against configurable paper-only entry gates and explain every rejection with stable reason codes.

**Files:**

- Create: `src/polymarket_alpha_lab/risk.py`
- Create: `tests/test_risk_gates.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`

- [x] **Step 1: Write failing risk-gate tests**

Create `tests/test_risk_gates.py`:

```python
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import pytest

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def test_risk_gate_accepts_packet_that_meets_config():
    decision = evaluate_research_packet_risk(
        complete_packet(),
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is True
    assert decision.config_version == "v1"
    assert decision.reasons == ()


def test_risk_gate_rejects_invalid_public_inputs():
    with pytest.raises(ValueError, match="packet"):
        evaluate_research_packet_risk(
            object(),
            RiskGateConfig(config_version="v1"),
        )
    with pytest.raises(ValueError, match="config"):
        evaluate_research_packet_risk(
            complete_packet(),
            object(),
        )


def test_risk_gate_rejects_with_deterministic_reason_codes():
    packet = complete_packet(
        strategy_type="experimental",
        confidence=Decimal("0.40"),
        cost_adjusted_edge=Decimal("-0.01"),
        spread=Decimal("0.20"),
        slippage_estimate=Decimal("0.05"),
        max_executable_size=Decimal("0.5"),
        risk_tags=("rules", "blocked-theme", "blocked-second"),
    )
    config = RiskGateConfig(
        config_version="v2",
        min_confidence=Decimal("0.55"),
        min_cost_adjusted_edge=Decimal("0.01"),
        max_spread=Decimal("0.05"),
        max_slippage_estimate=Decimal("0.01"),
        min_max_executable_size=Decimal("1"),
        allowed_strategy_types=("market_quality",),
        blocked_risk_tags=("blocked-theme", "blocked-second"),
    )

    decision = evaluate_research_packet_risk(packet, config)

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == [
        "strategy_not_allowed",
        "blocked_risk_tag",
        "blocked_risk_tag",
        "low_confidence",
        "low_cost_adjusted_edge",
        "wide_spread",
        "high_slippage",
        "insufficient_executable_size",
    ]
    assert decision.reasons[0].field_name == "strategy_type"
    assert decision.reasons[1].observed_value == "blocked-theme"
    assert decision.reasons[2].observed_value == "blocked-second"
    assert decision.reasons[3].observed_value == Decimal("0.40")
    assert decision.reasons[3].threshold == Decimal("0.55")


def test_risk_gate_reports_incomplete_packet_before_numeric_gates():
    packet = complete_packet(
        confidence=None,
        cost_adjusted_edge=Decimal("NaN"),
        risk_tags=(),
    )

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    assert decision.reasons[0].field_name == "missing_required_fields"
    assert "confidence" in str(decision.reasons[0].observed_value)
    assert "cost_adjusted_edge" in str(decision.reasons[0].observed_value)
    assert "risk_tags" in str(decision.reasons[0].observed_value)


@pytest.mark.parametrize(
    "field_name",
    [
        "confidence",
        "cost_adjusted_edge",
        "spread",
        "slippage_estimate",
        "max_executable_size",
    ],
)
def test_risk_gate_treats_non_decimal_numeric_gate_fields_as_incomplete(field_name):
    packet = replace(complete_packet(), **{field_name: cast(Any, "0.60")})

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    assert field_name in str(decision.reasons[0].observed_value)


def test_risk_gate_treats_nonpositive_executable_size_as_incomplete_packet():
    packet = complete_packet(max_executable_size=Decimal("0"))

    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    assert decision.accepted is False
    assert [reason.code for reason in decision.reasons] == ["incomplete_packet"]
    assert "positive_max_executable_size" in str(decision.reasons[0].observed_value)


def test_risk_gate_accepts_threshold_equal_values():
    config = RiskGateConfig(
        config_version="v1",
        min_confidence=Decimal("0.60"),
        min_cost_adjusted_edge=Decimal("0.026"),
        max_spread=Decimal("0.02"),
        max_slippage_estimate=Decimal("0.004"),
        min_max_executable_size=Decimal("100"),
    )

    decision = evaluate_research_packet_risk(complete_packet(), config)

    assert decision.accepted is True
    assert decision.reasons == ()


def test_risk_gate_config_normalizes_sequences_to_tuples():
    config = RiskGateConfig(
        config_version="v1",
        allowed_strategy_types=["market_quality"],
        blocked_risk_tags=["rules"],
    )

    assert config.allowed_strategy_types == ("market_quality",)
    assert config.blocked_risk_tags == ("rules",)


@pytest.mark.parametrize(
    "config_kwargs",
    [
        {"config_version": "v1", "min_confidence": Decimal("NaN")},
        {"config_version": "v1", "min_confidence": "0.50"},
        {"config_version": "v1", "min_confidence": Decimal("-0.01")},
        {"config_version": "v1", "min_confidence": Decimal("1.01")},
        {"config_version": "v1", "min_cost_adjusted_edge": Decimal("Infinity")},
        {"config_version": "v1", "max_spread": Decimal("NaN")},
        {"config_version": "v1", "max_spread": Decimal("0")},
        {"config_version": "v1", "max_slippage_estimate": Decimal("Infinity")},
        {"config_version": "v1", "max_slippage_estimate": Decimal("-0.01")},
        {"config_version": "v1", "min_max_executable_size": Decimal("-Infinity")},
        {"config_version": "v1", "min_max_executable_size": Decimal("0")},
        {"config_version": "v1", "allowed_strategy_types": "market_quality"},
        {"config_version": "v1", "allowed_strategy_types": b"market_quality"},
        {"config_version": "v1", "allowed_strategy_types": (123,)},
        {"config_version": "v1", "allowed_strategy_types": ("market_quality", " ")},
        {"config_version": "v1", "blocked_risk_tags": "liquidity"},
        {"config_version": "v1", "blocked_risk_tags": b"liquidity"},
        {"config_version": "v1", "blocked_risk_tags": (123,)},
        {"config_version": "v1", "blocked_risk_tags": ("liquidity", "")},
        {"config_version": " "},
        {"config_version": 123},
    ],
)
def test_risk_gate_config_rejects_invalid_values(config_kwargs):
    with pytest.raises(ValueError):
        RiskGateConfig(**config_kwargs)


def test_risk_gate_decision_rejects_invalid_states():
    reason = RiskGateReason(
        code="low_confidence",
        message="confidence is below minimum",
        field_name="confidence",
        observed_value=Decimal("0.40"),
        threshold=Decimal("0.55"),
    )

    with pytest.raises(ValueError, match="accepted"):
        RiskGateDecision(accepted=True, config_version="v1", reasons=(reason,))
    with pytest.raises(ValueError, match="rejected"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=())
    with pytest.raises(ValueError, match="reasons"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=("bad",))
    with pytest.raises(ValueError, match="reasons"):
        RiskGateDecision(accepted=False, config_version="v1", reasons=None)
    with pytest.raises(ValueError, match="config_version"):
        RiskGateDecision(accepted=False, config_version=123, reasons=(reason,))
    with pytest.raises(ValueError, match="accepted"):
        RiskGateDecision(accepted="yes", config_version="v1", reasons=())


@pytest.mark.parametrize(
    "reason_kwargs",
    [
        {
            "code": "unknown_code",
            "message": "message",
            "field_name": "confidence",
        },
        {
            "code": 123,
            "message": "message",
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": 123,
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": " ",
            "field_name": "confidence",
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": 123,
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": " ",
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": "confidence",
            "observed_value": object(),
        },
        {
            "code": "low_confidence",
            "message": "message",
            "field_name": "confidence",
            "threshold": object(),
        },
    ],
)
def test_risk_gate_reason_rejects_invalid_public_values(reason_kwargs):
    with pytest.raises(ValueError):
        RiskGateReason(**reason_kwargs)


def test_risk_gate_is_available_from_package_root():
    import polymarket_alpha_lab as lab

    assert lab.RiskGateConfig is RiskGateConfig
    assert lab.RiskGateDecision.__name__ == "RiskGateDecision"
    assert lab.RiskGateReason.__name__ == "RiskGateReason"
    assert lab.evaluate_research_packet_risk is evaluate_research_packet_risk
```

- [x] **Step 2: Run risk-gate tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_risk_gates.py -q
```

Expected: import failure because `polymarket_alpha_lab.risk` does not exist.

**Recorded RED result:** `.venv/bin/python -m pytest tests/test_risk_gates.py -q` failed during collection with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.risk'`, as expected.

- [x] **Step 3: Implement risk gates**

Create `src/polymarket_alpha_lab/risk.py`:

```python
"""Paper-only research-packet risk gates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.research import ResearchPacket

ALLOWED_REASON_CODES = {
    "incomplete_packet",
    "low_confidence",
    "low_cost_adjusted_edge",
    "wide_spread",
    "high_slippage",
    "insufficient_executable_size",
    "strategy_not_allowed",
    "blocked_risk_tag",
}

RISK_NUMERIC_FIELDS = (
    "confidence",
    "cost_adjusted_edge",
    "spread",
    "slippage_estimate",
    "max_executable_size",
)


@dataclass(frozen=True)
class RiskGateConfig:
    config_version: str
    min_confidence: Decimal = Decimal("0.50")
    min_cost_adjusted_edge: Decimal = Decimal("0.00")
    max_spread: Decimal = Decimal("0.10")
    max_slippage_estimate: Decimal = Decimal("0.02")
    min_max_executable_size: Decimal = Decimal("1")
    allowed_strategy_types: tuple[str, ...] = ()
    blocked_risk_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "allowed_strategy_types",
            _normalize_string_sequence("allowed_strategy_types", self.allowed_strategy_types),
        )
        object.__setattr__(
            self,
            "blocked_risk_tags",
            _normalize_string_sequence("blocked_risk_tags", self.blocked_risk_tags),
        )
        _validate_config(self)


@dataclass(frozen=True)
class RiskGateReason:
    code: str
    message: str
    field_name: str
    observed_value: Decimal | str | None = None
    threshold: Decimal | str | None = None

    def __post_init__(self) -> None:
        _validate_reason(self)


@dataclass(frozen=True)
class RiskGateDecision:
    accepted: bool
    config_version: str
    reasons: tuple[RiskGateReason, ...]

    def __post_init__(self) -> None:
        try:
            normalized_reasons = tuple(self.reasons)
        except TypeError as exc:
            raise ValueError("reasons must be a sequence of RiskGateReason values") from exc
        object.__setattr__(self, "reasons", normalized_reasons)
        if not isinstance(self.accepted, bool):
            raise ValueError("accepted must be a bool")
        if not isinstance(self.config_version, str) or not self.config_version.strip():
            raise ValueError("config_version is required")
        for reason in self.reasons:
            if not isinstance(reason, RiskGateReason):
                raise ValueError("reasons must contain RiskGateReason values")
        if self.accepted and self.reasons:
            raise ValueError("accepted decisions must not include reasons")
        if not self.accepted and not self.reasons:
            raise ValueError("rejected decisions must include at least one reason")


def evaluate_research_packet_risk(
    packet: ResearchPacket,
    config: RiskGateConfig,
) -> RiskGateDecision:
    if not isinstance(packet, ResearchPacket):
        raise ValueError("packet must be a ResearchPacket")
    if not isinstance(config, RiskGateConfig):
        raise ValueError("config must be a RiskGateConfig")

    reasons: list[RiskGateReason] = []

    missing = _missing_fields_for_risk(packet)
    if missing:
        reasons.append(
            RiskGateReason(
                code="incomplete_packet",
                message="research packet is incomplete",
                field_name="missing_required_fields",
                observed_value=",".join(missing),
            )
        )
        return RiskGateDecision(
            accepted=False,
            config_version=config.config_version,
            reasons=tuple(reasons),
        )

    if config.allowed_strategy_types and packet.strategy_type not in config.allowed_strategy_types:
        reasons.append(
            RiskGateReason(
                code="strategy_not_allowed",
                message="strategy type is not allowed by this gate config",
                field_name="strategy_type",
                observed_value=packet.strategy_type,
                threshold=",".join(config.allowed_strategy_types),
            )
        )

    blocked_tags = set(config.blocked_risk_tags)
    for tag in packet.risk_tags:
        if tag in blocked_tags:
            reasons.append(
                RiskGateReason(
                    code="blocked_risk_tag",
                    message="risk tag is blocked by this gate config",
                    field_name="risk_tags",
                    observed_value=tag,
                    threshold=",".join(config.blocked_risk_tags),
                )
            )

    if packet.confidence < config.min_confidence:
        reasons.append(
            RiskGateReason(
                code="low_confidence",
                message="confidence is below minimum",
                field_name="confidence",
                observed_value=packet.confidence,
                threshold=config.min_confidence,
            )
        )
    if packet.cost_adjusted_edge < config.min_cost_adjusted_edge:
        reasons.append(
            RiskGateReason(
                code="low_cost_adjusted_edge",
                message="cost-adjusted edge is below minimum",
                field_name="cost_adjusted_edge",
                observed_value=packet.cost_adjusted_edge,
                threshold=config.min_cost_adjusted_edge,
            )
        )
    if packet.spread > config.max_spread:
        reasons.append(
            RiskGateReason(
                code="wide_spread",
                message="spread is above maximum",
                field_name="spread",
                observed_value=packet.spread,
                threshold=config.max_spread,
            )
        )
    if packet.slippage_estimate > config.max_slippage_estimate:
        reasons.append(
            RiskGateReason(
                code="high_slippage",
                message="slippage estimate is above maximum",
                field_name="slippage_estimate",
                observed_value=packet.slippage_estimate,
                threshold=config.max_slippage_estimate,
            )
        )
    if packet.max_executable_size < config.min_max_executable_size:
        reasons.append(
            RiskGateReason(
                code="insufficient_executable_size",
                message="maximum executable size is below minimum",
                field_name="max_executable_size",
                observed_value=packet.max_executable_size,
                threshold=config.min_max_executable_size,
            )
        )

    return RiskGateDecision(
        accepted=not reasons,
        config_version=config.config_version,
        reasons=tuple(reasons),
    )


def _validate_config(config: RiskGateConfig) -> None:
    if not isinstance(config.config_version, str) or not config.config_version.strip():
        raise ValueError("config_version is required")
    for field_name, value in (
        ("min_confidence", config.min_confidence),
        ("min_cost_adjusted_edge", config.min_cost_adjusted_edge),
        ("max_spread", config.max_spread),
        ("max_slippage_estimate", config.max_slippage_estimate),
        ("min_max_executable_size", config.min_max_executable_size),
    ):
        if not isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
    if config.min_confidence < 0 or config.min_confidence > 1:
        raise ValueError("min_confidence must be in [0, 1]")
    if config.max_spread <= 0:
        raise ValueError("max_spread must be positive")
    if config.max_slippage_estimate < 0:
        raise ValueError("max_slippage_estimate must be nonnegative")
    if config.min_max_executable_size <= 0:
        raise ValueError("min_max_executable_size must be positive")


def _validate_reason(reason: RiskGateReason) -> None:
    if not isinstance(reason.code, str):
        raise ValueError("risk gate reason code must be a string")
    if reason.code not in ALLOWED_REASON_CODES:
        raise ValueError("risk gate reason code is not recognized")
    if not isinstance(reason.message, str) or not reason.message.strip():
        raise ValueError("risk gate reason message is required")
    if not isinstance(reason.field_name, str) or not reason.field_name.strip():
        raise ValueError("risk gate reason field_name is required")
    for field_name, value in (
        ("observed_value", reason.observed_value),
        ("threshold", reason.threshold),
    ):
        if value is not None and not isinstance(value, (Decimal, str)):
            raise ValueError(f"risk gate reason {field_name} must be a Decimal or string")


def _missing_fields_for_risk(packet: ResearchPacket) -> tuple[str, ...]:
    numeric_missing = _risk_numeric_missing_fields(packet)
    try:
        level_1a_missing = tuple(packet.missing_required_fields())
    except (AttributeError, TypeError, ValueError) as exc:
        if numeric_missing:
            return _ordered_unique(numeric_missing)
        raise ValueError("research packet completeness could not be evaluated") from exc
    if "max_executable_size" in numeric_missing:
        level_1a_missing = tuple(
            field_name
            for field_name in level_1a_missing
            if field_name != "positive_max_executable_size"
        )
    return _ordered_unique((*level_1a_missing, *numeric_missing))


def _risk_numeric_missing_fields(packet: ResearchPacket) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in RISK_NUMERIC_FIELDS:
        value = getattr(packet, field_name)
        if not isinstance(value, Decimal) or not value.is_finite():
            missing.append(field_name)
    return tuple(missing)


def _normalize_string_sequence(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    for item in normalized:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain nonblank strings")
    return normalized


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
```

- [x] **Step 4: Export risk APIs**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)
```

Add to `__all__`:

```python
"RiskGateConfig",
"RiskGateDecision",
"RiskGateReason",
"evaluate_research_packet_risk",
```

Update `tests/test_init.py` imports and export assertions:

```python
from polymarket_alpha_lab.risk import (
    RiskGateConfig,
    RiskGateDecision,
    RiskGateReason,
    evaluate_research_packet_risk,
)


def test_level_1b_node_1_public_api_exports():
    expected_exports = {
        "RiskGateConfig",
        "RiskGateDecision",
        "RiskGateReason",
        "evaluate_research_packet_risk",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.RiskGateConfig is RiskGateConfig
    assert lab.RiskGateDecision is RiskGateDecision
    assert lab.RiskGateReason is RiskGateReason
    assert lab.evaluate_research_packet_risk is evaluate_research_packet_risk
```

- [x] **Step 5: Run risk-gate tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_init.py -q
```

Expected: all selected tests pass.

**Recorded GREEN result:** `.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py -q` passed with `77 passed`.

## Part 2: Rejected-Candidate Logs

**Goal:** Persist rejected paper candidates with stable reason codes, source packet metadata, and gate config provenance.

**Files:**

- Create: `src/polymarket_alpha_lab/rejections.py`
- Create: `tests/test_rejections.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`

- [x] **Step 1: Write failing rejection-log tests**

Create `tests/test_rejections.py`:

```python
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.rejections import RejectedCandidateLog, RejectedCandidateRecord
from polymarket_alpha_lab.research import build_research_packet
from polymarket_alpha_lab.risk import RiskGateConfig, evaluate_research_packet_risk


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("-0.010"),
        "confidence": Decimal("0.40"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def rejected_decision(packet=None):
    return evaluate_research_packet_risk(
        packet or complete_packet(),
        RiskGateConfig(
            config_version="v1",
            min_confidence=Decimal("0.55"),
            min_cost_adjusted_edge=Decimal("0.00"),
        ),
    )


def test_rejected_candidate_log_appends_jsonl_record(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31),
        evidence_summary="Cost-adjusted edge and confidence failed.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected-candidates.jsonl")

    log.append(record)

    lines = log.path.read_text().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"condition_id"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["rejected_at"] == "2026-06-13T12:31:00+00:00"
    assert stored["packet_id"] == packet.packet_id
    assert stored["condition_id"] == "0xabc"
    assert stored["token_id"] == "111"
    assert stored["market_slug"] == "example-market"
    assert stored["market_url"] == "https://polymarket.com/event/example-market"
    assert stored["strategy_type"] == "market_quality"
    assert stored["market_raw_archive_path"] == "data/raw/gamma/markets.json"
    assert stored["rule_text_hash"] == packet.rule_text_hash
    assert stored["risk_tags"] == ["liquidity"]
    assert stored["gate_config_version"] == "v1"
    assert [reason["code"] for reason in stored["reasons"]] == [
        "low_confidence",
        "low_cost_adjusted_edge",
    ]
    assert stored["reasons"][0]["observed_value"] == "0.40"
    assert stored["evidence_summary"] == "Cost-adjusted edge and confidence failed."


def test_rejected_candidate_log_appends_without_overwriting(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    log = RejectedCandidateLog(path=str(tmp_path / "nested" / "rejected.jsonl"))
    first = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="First rejection.",
    )
    second = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 32, tzinfo=UTC),
        evidence_summary="Second rejection.",
    )

    log.append(first)
    log.append(second)

    lines = log.path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["evidence_summary"] == "First rejection."
    assert json.loads(lines[1])["evidence_summary"] == "Second rejection."


def test_rejected_candidate_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=object())
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path="")
    with pytest.raises(ValueError, match="path"):
        RejectedCandidateLog(path=tmp_path)


def test_rejected_candidate_log_supports_incomplete_packet_rejections(tmp_path):
    packet = complete_packet(
        market_url="",
        outcome_name="",
        strategy_type="",
        confidence=None,
        risk_tags=(),
    )
    decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=decision,
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Packet was missing fields required for review.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    log.append(record)

    stored = json.loads(log.path.read_text())
    assert stored["market_url"] == ""
    assert stored["outcome_name"] == ""
    assert stored["strategy_type"] == ""
    assert stored["risk_tags"] == []
    assert stored["reasons"][0]["code"] == "incomplete_packet"
    assert "confidence" in stored["reasons"][0]["observed_value"]


def test_rejected_candidate_record_normalizes_rejected_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        evidence_summary="Rejected.",
    )

    assert record.rejected_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)


def test_rejected_candidate_record_rejects_accepted_decision():
    packet = complete_packet(cost_adjusted_edge=Decimal("0.020"), confidence=Decimal("0.80"))
    accepted_decision = evaluate_research_packet_risk(
        packet,
        RiskGateConfig(config_version="v1"),
    )

    with pytest.raises(ValueError, match="accepted"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=accepted_decision,
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Should not reject.",
        )


def test_rejected_candidate_record_rejects_invalid_public_inputs():
    packet = complete_packet()
    decision = rejected_decision(packet)

    with pytest.raises(ValueError, match="packet"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=object(),
            decision=decision,
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Rejected.",
        )
    with pytest.raises(ValueError, match="decision"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=object(),
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary="Rejected.",
        )


@pytest.mark.parametrize("evidence_summary", ["", "   ", None, 123])
def test_rejected_candidate_record_rejects_blank_evidence_summary(evidence_summary):
    packet = complete_packet()

    with pytest.raises(ValueError, match="evidence_summary"):
        RejectedCandidateRecord.from_packet_and_decision(
            packet=packet,
            decision=rejected_decision(packet),
            rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            evidence_summary=evidence_summary,
        )


def test_rejected_candidate_record_rejects_invalid_direct_record_state():
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )

    with pytest.raises(ValueError, match="paper_only"):
        replace(record, paper_only=False)
    with pytest.raises(ValueError, match="risk_tags"):
        replace(record, risk_tags=(123,))
    with pytest.raises(ValueError, match="reasons"):
        replace(record, reasons=("bad",))
    with pytest.raises(ValueError, match="reasons"):
        replace(record, reasons=None)
    with pytest.raises(ValueError, match="evidence_summary"):
        replace(record, evidence_summary=123)


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("packet_id", 123),
        ("packet_id", ""),
        ("condition_id", ""),
        ("token_id", ""),
        ("market_slug", ""),
        ("question", ""),
        ("source_score", ""),
        ("market_raw_archive_path", ""),
        ("rule_text_hash", ""),
        ("resolution_source", ""),
        ("gate_config_version", None),
        ("market_url", object()),
        ("outcome_name", object()),
        ("strategy_type", object()),
    ],
)
def test_rejected_candidate_record_rejects_invalid_direct_scalar_fields(
    field_name,
    bad_value,
):
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )

    with pytest.raises(ValueError, match=field_name):
        replace(record, **{field_name: bad_value})


def test_rejected_candidate_record_direct_construction_normalizes_timestamps():
    packet = complete_packet()
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=rejected_decision(packet),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Rejected.",
    )
    eastern = timezone(timedelta(hours=-4))

    normalized = replace(
        record,
        rejected_at=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        packet_created_at=datetime(2026, 6, 13, 8, 30, tzinfo=eastern),
    )

    assert normalized.rejected_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert normalized.packet_created_at == datetime(2026, 6, 13, 12, 30, tzinfo=UTC)


def test_rejected_candidate_log_rejects_non_finite_reason_decimal(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=replace(
            decision,
            reasons=(
                replace(decision.reasons[0], observed_value=Decimal("NaN")),
            ),
        ),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Bad decimal.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(record)

    assert not log.path.exists()


def test_rejected_candidate_log_rejects_non_finite_reason_threshold(tmp_path):
    packet = complete_packet()
    decision = rejected_decision(packet)
    record = RejectedCandidateRecord.from_packet_and_decision(
        packet=packet,
        decision=replace(
            decision,
            reasons=(
                replace(decision.reasons[0], threshold=Decimal("Infinity")),
            ),
        ),
        rejected_at=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        evidence_summary="Bad threshold.",
    )
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(record)

    assert not log.path.exists()


def test_rejected_candidate_log_rejects_invalid_public_input(tmp_path):
    log = RejectedCandidateLog(path=tmp_path / "rejected.jsonl")

    with pytest.raises(ValueError, match="record"):
        log.append(object())

    assert not log.path.exists()
```

- [x] **Step 2: Run rejection-log tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_rejections.py -q
```

Expected: import failure because `polymarket_alpha_lab.rejections` does not exist.

**Recorded RED result:** `.venv/bin/python -m pytest tests/test_rejections.py -q` failed during collection with `ModuleNotFoundError: No module named 'polymarket_alpha_lab.rejections'`, as expected.

**Recorded hardening RED result:** after Jason's read-only review, `.venv/bin/python -m pytest tests/test_rejections.py -q` failed on parent-path-file validation and `risk_tags=None` handling before those fixes were applied.

- [x] **Step 3: Implement rejected-candidate records and JSONL log**

Create `src/polymarket_alpha_lab/rejections.py`:

```python
"""Rejected-candidate audit logs for paper-only risk gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite
from pathlib import Path
from typing import Any, Iterable

from polymarket_alpha_lab.research import ResearchPacket
from polymarket_alpha_lab.risk import RiskGateDecision, RiskGateReason


@dataclass(frozen=True)
class RejectedCandidateRecord:
    rejected_at: datetime
    packet_id: str
    packet_created_at: datetime
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    source_score: str
    market_raw_archive_path: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    gate_config_version: str
    reasons: tuple[RiskGateReason, ...]
    evidence_summary: str
    paper_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rejected_at", _as_utc(self.rejected_at))
        object.__setattr__(self, "packet_created_at", _as_utc(self.packet_created_at))
        object.__setattr__(self, "risk_tags", _normalize_string_tuple("risk_tags", self.risk_tags))
        object.__setattr__(self, "reasons", _normalize_reasons(self.reasons))
        _require_nonblank_string("packet_id", self.packet_id)
        _require_nonblank_string("condition_id", self.condition_id)
        _require_nonblank_string("token_id", self.token_id)
        _require_nonblank_string("market_slug", self.market_slug)
        _require_string("market_url", self.market_url)
        _require_nonblank_string("question", self.question)
        _require_string("outcome_name", self.outcome_name)
        _require_string("strategy_type", self.strategy_type)
        _require_nonblank_string("source_score", self.source_score)
        _require_nonblank_string("market_raw_archive_path", self.market_raw_archive_path)
        _require_nonblank_string("rule_text_hash", self.rule_text_hash)
        _require_nonblank_string("resolution_source", self.resolution_source)
        _require_nonblank_string("gate_config_version", self.gate_config_version)
        if not isinstance(self.evidence_summary, str) or not self.evidence_summary.strip():
            raise ValueError("evidence_summary is required")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")

    @classmethod
    def from_packet_and_decision(
        cls,
        *,
        packet: ResearchPacket,
        decision: RiskGateDecision,
        rejected_at: datetime,
        evidence_summary: str,
    ) -> "RejectedCandidateRecord":
        if not isinstance(packet, ResearchPacket):
            raise ValueError("packet must be a ResearchPacket")
        if not isinstance(decision, RiskGateDecision):
            raise ValueError("decision must be a RiskGateDecision")
        if decision.accepted:
            raise ValueError("accepted decisions cannot be logged as rejected candidates")
        if not decision.reasons:
            raise ValueError("rejected decisions must include at least one reason")
        if not isinstance(evidence_summary, str) or not evidence_summary.strip():
            raise ValueError("evidence_summary is required")

        return cls(
            rejected_at=_as_utc(rejected_at),
            packet_id=packet.packet_id,
            packet_created_at=_as_utc(packet.created_at),
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            market_url=packet.market_url,
            question=packet.question,
            outcome_name=packet.outcome_name,
            strategy_type=packet.strategy_type,
            source_score=packet.source_score,
            market_raw_archive_path=packet.raw_archive_path,
            risk_tags=tuple(packet.risk_tags),
            rule_text_hash=packet.rule_text_hash,
            resolution_source=packet.resolution_source,
            gate_config_version=decision.config_version,
            reasons=tuple(decision.reasons),
            evidence_summary=evidence_summary,
        )


@dataclass(frozen=True)
class RejectedCandidateLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, record: RejectedCandidateRecord) -> None:
        if not isinstance(record, RejectedCandidateRecord):
            raise ValueError("record must be a RejectedCandidateRecord")
        line = json.dumps(_json_ready(asdict(record)), allow_nan=False, sort_keys=True) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime values are required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_reasons(value: Iterable[RiskGateReason]) -> tuple[RiskGateReason, ...]:
    try:
        reasons = tuple(value)
    except TypeError as exc:
        raise ValueError("reasons must be a sequence of RiskGateReason values") from exc
    if not reasons:
        raise ValueError("reasons must include at least one RiskGateReason")
    for reason in reasons:
        if not isinstance(reason, RiskGateReason):
            raise ValueError("reasons must contain RiskGateReason values")
    return reasons


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain nonblank strings")
    return items


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    return path


def _require_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")


def _require_nonblank_string(field_name: str, value: str) -> None:
    _require_string(field_name, value)
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("rejection log Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("rejection log float values must be finite")
        return value
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("rejection log object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("rejection log values must be JSON serializable")
```

- [x] **Step 4: Export rejection APIs**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.rejections import RejectedCandidateLog, RejectedCandidateRecord
```

Add to `__all__`:

```python
"RejectedCandidateLog",
"RejectedCandidateRecord",
```

Update `tests/test_init.py` imports and export assertions:

```python
from polymarket_alpha_lab.rejections import RejectedCandidateLog, RejectedCandidateRecord


def test_level_1b_rejection_public_api_exports():
    expected_exports = {
        "RejectedCandidateLog",
        "RejectedCandidateRecord",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.RejectedCandidateLog is RejectedCandidateLog
    assert lab.RejectedCandidateRecord is RejectedCandidateRecord
```

- [x] **Step 5: Run rejection-log tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py -q
```

Expected: all selected tests pass.

**Recorded GREEN result:** `.venv/bin/python -m pytest tests/test_rejections.py -q` passed with `32 passed`; `.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py -q` passed with `77 passed`.

## Part 3: README And Plan Gate

**Goal:** Document the new paper-only Level 1B Node 1 APIs and verify all gates before commit.

**Files:**

- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-rejections-risk-gates.md`

- [x] **Step 1: Update README status**

Add after the Level 1A Python API section:

```markdown
## Level 1B Node 1 Status

Level 1B Node 1 adds configurable paper-only risk gates and append-only rejected-candidate logs. It does not place orders, authenticate, handle private keys, cancel orders, open user WebSockets, run heartbeat logic, or create live-trading proposals.

## Level 1B Node 1 Python API

Node 1 is exposed through Python APIs:

- Configure entry gates with `RiskGateConfig(...)`.
- Evaluate packets with `evaluate_research_packet_risk(packet, config)`.
- Persist rejected candidates with `RejectedCandidateRecord.from_packet_and_decision(...)` and `RejectedCandidateLog(path).append(record)`.
```

- [x] **Step 2: Run required pre-commit/pre-push gate for Level 1B Node 1**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py -q
.venv/bin/python -m pytest
git diff --check
codegraph status .
# If CodeGraph reports stale/out of date:
codegraph sync .
codegraph status .
# After staging in Step 4 and before commit:
git diff --cached --check
```

Expected:

- untracked files are explicitly listed or `none`
- node-specific pytest passes
- full pytest reports all tests passing
- `git diff --check` reports no whitespace errors
- CodeGraph index is up to date
- after staging, `git diff --cached --check` reports no whitespace errors
- only intentional files are modified or staged

**Recorded pre-review gate result:** before staging, `git status --short --branch --untracked-files=all` listed intentional Level 1B files only; `.venv/bin/python -m pytest tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py -q` passed with `77 passed`; `.venv/bin/python -m pytest -q` passed with `212 passed`; `git diff --check` reported no whitespace errors; `codegraph status .` reported stale Python changes, then `codegraph sync .` updated two files and the follow-up `codegraph status .` reported the index is up to date. After staging, `git diff --cached --check` reported no whitespace errors.

- [x] **Step 3: Request Claude Code review before commit/push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Level 1B Node 1 rejected-candidate log and risk-gate changes in /home/ubuntu/polymarket-alpha-lab before commit/push. First run git status --short --branch --untracked-files=all and review all staged, unstaged, and untracked files. Confirm the recorded Node 1 gate includes node-specific pytest, full pytest, git diff --check, CodeGraph status/sync-if-stale results, and that git diff --cached --check will be run after staging and before commit. Requirements: configurable finite-only paper risk gates, deterministic structured rejection reasons, accepted decisions have no reasons, incomplete packets produce an incomplete_packet reason, rejected candidates append as JSONL with packet provenance, rule hash, risk tags, gate config version, reason codes, evidence summary, UTC timestamps, finite Decimal persistence checks, no auth, no private keys, no order placement, no cancellation, no user WebSocket, no heartbeat, no live trading, no proposal workflow, and no compliance/legal/geographic-access analysis. Also review next-stage direction: Level 1B paper positions and daily executable NAV marks, still paper-only. Report Critical, Important, Minor findings only, and finish with an explicit verdict: Proceed, Proceed with fixes, or Blocked."
```

Do not run `git commit` or `git push` until Claude returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.

**Recorded Claude review result:** `claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""` reviewed the provided status, verification output, tracked diff, and full untracked file contents. Verdict: `Proceed`. Findings: no Critical, no Important, no Minor. The review confirmed paper-only scope, public API exports, JSONL rejection persistence, deterministic risk reasons, finite Decimal/float persistence checks, parent/ancestor path validation, and absence of live-trading/auth/order-placement behavior.

- [ ] **Step 4: Commit Level 1B Node 1**

Run:

```bash
git add src/polymarket_alpha_lab/risk.py src/polymarket_alpha_lab/rejections.py src/polymarket_alpha_lab/__init__.py README.md tests/test_risk_gates.py tests/test_rejections.py tests/test_init.py docs/superpowers/plans/2026-06-13-level-1b-rejections-risk-gates.md
git diff --cached --check
git commit -m "feat: add paper risk gates"
git push
```

## Level 1B Node 1 Completion Criteria

Node 1 is complete only when:

- `RiskGateConfig` rejects non-string or blank config versions, non-Decimal or non-finite Decimal thresholds, invalid probability thresholds, nonpositive spread limits, negative slippage limits, nonpositive executable-size floors, bare string/bytes allowlists or blocked-tag lists, non-string allowlist/tag members, blank allowlist values, and blank blocked tags.
- `evaluate_research_packet_risk()` returns accepted decisions with no reasons for packets that meet the config.
- `evaluate_research_packet_risk()` returns rejected decisions with deterministic structured reasons for incomplete packets, disallowed strategies, blocked tags in packet order, low confidence, low cost-adjusted edge, wide spread, high slippage, and insufficient executable size.
- `evaluate_research_packet_risk()` treats `max_executable_size <= 0` as terminal incomplete packet data with `positive_max_executable_size`, while `insufficient_executable_size` is reserved for positive, finite executable sizes below the configured minimum.
- `RiskGateReason` rejects unknown codes, non-string or blank scalar text fields, and non-`Decimal`/non-string observed values or thresholds.
- `RiskGateDecision` rejects non-bool accepted values, non-string or blank config versions, non-`RiskGateReason` reason members, accepted decisions with reasons, and rejected decisions without reasons.
- `evaluate_research_packet_risk()` rejects non-`ResearchPacket` packets and non-`RiskGateConfig` configs with controlled `ValueError`.
- `RejectedCandidateRecord.from_packet_and_decision()` rejects accepted decisions, normalizes timestamps to UTC, and requires string nonblank evidence summary.
- `RejectedCandidateRecord` direct construction normalizes timestamps to UTC, tuple-normalizes `risk_tags` and `reasons`, rejects invalid `risk_tags`/`reasons`, validates key scalar provenance fields, requires string nonblank evidence summary, and requires `paper_only is True`.
- `RejectedCandidateRecord.from_packet_and_decision()` handles malformed incomplete-packet shapes such as `risk_tags=None` with controlled `ValueError` rather than leaking `TypeError`.
- `RejectedCandidateLog` rejects invalid, blank, directory, or parent-is-file paths with controlled `ValueError`.
- `RejectedCandidateLog.append()` writes sorted-key JSONL, appends without overwriting, creates parent directories, serializes Decimal values as strings, rejects non-finite Decimal observed values, thresholds, and float values before opening the log file, and rejects unsupported JSON values with controlled `ValueError`.
- Public package-root exports include the risk and rejection APIs.
- README documents Level 1B Node 1 as paper-only.
- The required gate and Claude review have passed.
- GitHub `main` contains the verified commit.

## Handoff Summary Template

```text
Handoff Summary
- Repo status: branch, latest commit, clean/dirty state, pushed/not pushed, plus `git status --short --branch --untracked-files=all` output.
- Verified commands: exact node-specific pytest, `.venv/bin/python -m pytest`, `git diff --check`, `git diff --cached --check` if staged, `codegraph status .`, `codegraph sync .` if run, follow-up `codegraph status .`, and pass/fail result.
- Untracked files: list or "none".
- Uncommitted files: list or "none".
- Data-integrity checks: risk config version, finite Decimal thresholds, deterministic reason codes, nonblank evidence summary, UTC timestamps, JSONL append behavior.
- Claude review: exact model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Next step: one concrete next action.
```
