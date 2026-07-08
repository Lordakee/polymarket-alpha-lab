"""Pure public-safe research risk-gate summary report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION = (
    "research-strategy-risk-gate-summary-v0"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_SCORE_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6")
_HEX_CHARS = frozenset("0123456789abcdef")

_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON = "risk_gate_pass"
_EMPTY_REASON = "empty_candidate_set_block"
_REASON_PRIORITY = (
    "aggregate_uncertainty_block",
    "cost_pressure_block",
    "liquidity_quality_block",
    "settlement_risk_block",
    "information_freshness_block",
    "team_disagreement_block",
    "composite_risk_block",
    "aggregate_uncertainty_watch",
    "cost_pressure_watch",
    "liquidity_quality_watch",
    "settlement_risk_watch",
    "information_freshness_watch",
    "team_disagreement_watch",
    "composite_risk_watch",
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(reason for reason in _REASON_PRIORITY if reason.endswith("_block"))
_WATCH_REASONS = frozenset(reason for reason in _REASON_PRIORITY if reason.endswith("_watch"))

_HIGH_RISK_SPECS = (
    (
        "aggregate_uncertainty_score",
        "watch_aggregate_uncertainty_score",
        "block_aggregate_uncertainty_score",
        "aggregate_uncertainty_watch",
        "aggregate_uncertainty_block",
    ),
    (
        "cost_pressure_score",
        "watch_cost_pressure_score",
        "block_cost_pressure_score",
        "cost_pressure_watch",
        "cost_pressure_block",
    ),
    (
        "settlement_risk_score",
        "watch_settlement_risk_score",
        "block_settlement_risk_score",
        "settlement_risk_watch",
        "settlement_risk_block",
    ),
    (
        "team_disagreement_score",
        "watch_team_disagreement_score",
        "block_team_disagreement_score",
        "team_disagreement_watch",
        "team_disagreement_block",
    ),
)
_FLOOR_RISK_SPECS = (
    (
        "liquidity_quality_score",
        "watch_liquidity_quality_floor",
        "block_liquidity_quality_floor",
        "liquidity_quality_watch",
        "liquidity_quality_block",
    ),
    (
        "information_freshness_score",
        "watch_information_freshness_floor",
        "block_information_freshness_floor",
        "information_freshness_watch",
        "information_freshness_block",
    ),
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-",
    "event_id",
    "event-",
    "market_id",
    "market_slug",
    "market-",
    "source_id",
    "source_ref",
    "source_url",
    "source_text",
    "source-",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live execution",
    "live_execution",
    "buy",
    "sell",
    "recommend",
    "position",
    "sizing",
)


@dataclass(frozen=True)
class ResearchStrategyRiskGateSummaryConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION
    watch_aggregate_uncertainty_score: Decimal = Decimal("0.300000")
    block_aggregate_uncertainty_score: Decimal = Decimal("0.700000")
    watch_cost_pressure_score: Decimal = Decimal("0.300000")
    block_cost_pressure_score: Decimal = Decimal("0.700000")
    watch_liquidity_quality_floor: Decimal = Decimal("0.600000")
    block_liquidity_quality_floor: Decimal = Decimal("0.300000")
    watch_settlement_risk_score: Decimal = Decimal("0.300000")
    block_settlement_risk_score: Decimal = Decimal("0.700000")
    watch_information_freshness_floor: Decimal = Decimal("0.700000")
    block_information_freshness_floor: Decimal = Decimal("0.400000")
    watch_team_disagreement_score: Decimal = Decimal("0.300000")
    block_team_disagreement_score: Decimal = Decimal("0.700000")
    watch_composite_risk_score: Decimal = Decimal("0.250000")
    block_composite_risk_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskGateSummaryConfig:
            raise ValueError("config must be exactly ResearchStrategyRiskGateSummaryConfig")
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_aggregate_uncertainty_score",
            "block_aggregate_uncertainty_score",
            "watch_cost_pressure_score",
            "block_cost_pressure_score",
            "watch_liquidity_quality_floor",
            "block_liquidity_quality_floor",
            "watch_settlement_risk_score",
            "block_settlement_risk_score",
            "watch_information_freshness_floor",
            "block_information_freshness_floor",
            "watch_team_disagreement_score",
            "block_team_disagreement_score",
            "watch_composite_risk_score",
            "block_composite_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for risk_name, watch_name, block_name, _, _ in _HIGH_RISK_SPECS:
            _validate_high_risk_threshold_pair(
                risk_name,
                getattr(self, watch_name),
                getattr(self, block_name),
            )
        for _, watch_name, block_name, _, _ in _FLOOR_RISK_SPECS:
            _validate_floor_threshold_pair(
                block_name,
                getattr(self, watch_name),
                getattr(self, block_name),
            )
        _validate_high_risk_threshold_pair(
            "composite_risk_score",
            self.watch_composite_risk_score,
            self.block_composite_risk_score,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskGateSummaryConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskGateCandidate:
    anonymized_candidate_key: str
    aggregate_uncertainty_score: Decimal
    cost_pressure_score: Decimal
    liquidity_quality_score: Decimal
    settlement_risk_score: Decimal
    information_freshness_score: Decimal
    team_disagreement_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskGateCandidate:
            raise ValueError("candidate must be exactly ResearchStrategyRiskGateCandidate")
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "anonymized_candidate_key",
            _require_public_text("anonymized_candidate_key", self.anonymized_candidate_key),
        )
        for field_name in _candidate_score_fields():
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskGateCandidate",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskGateSummaryRow:
    anonymized_candidate_key: str
    aggregate_uncertainty_score: Decimal
    cost_pressure_score: Decimal
    liquidity_quality_score: Decimal
    settlement_risk_score: Decimal
    information_freshness_score: Decimal
    team_disagreement_score: Decimal
    composite_risk_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskGateSummaryRow:
            raise ValueError("row must be exactly ResearchStrategyRiskGateSummaryRow")
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "anonymized_candidate_key",
            _require_public_text("anonymized_candidate_key", self.anonymized_candidate_key),
        )
        for field_name in _candidate_score_fields():
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "composite_risk_score",
            _normalize_ratio("composite_risk_score", self.composite_risk_score),
        )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskGateSummaryRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyRiskGateSummaryReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_uncertainty_score: Decimal
    average_cost_pressure_score: Decimal
    average_liquidity_quality_score: Decimal
    average_settlement_risk_score: Decimal
    average_information_freshness_score: Decimal
    average_team_disagreement_score: Decimal
    average_composite_risk_score: Decimal
    min_liquidity_quality_score: Decimal
    min_information_freshness_score: Decimal
    max_composite_risk_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyRiskGateSummaryRow, ...]
    risk_gate_summary_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyRiskGateSummaryReport:
            raise ValueError("report must be exactly ResearchStrategyRiskGateSummaryReport")
        _require_hard_flags(self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_text("config_version", self.config_version),
        )
        _require_status("gate_status", self.gate_status)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_uncertainty_score",
            "average_cost_pressure_score",
            "average_liquidity_quality_score",
            "average_settlement_risk_score",
            "average_information_freshness_score",
            "average_team_disagreement_score",
            "average_composite_risk_score",
            "min_liquidity_quality_score",
            "min_information_freshness_score",
            "max_composite_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("risk_gate_summary_digest", self.risk_gate_summary_digest)
        _validate_report(self)
        _validate_digest(self)
        _reject_unsafe_public_payload(
            "ResearchStrategyRiskGateSummaryReport",
            self.payload,
        )

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_risk_gate_summary_report(
    candidates: Iterable[object],
    *,
    config: ResearchStrategyRiskGateSummaryConfig,
    generated_at: datetime,
) -> ResearchStrategyRiskGateSummaryReport:
    if type(config) is not ResearchStrategyRiskGateSummaryConfig:
        raise ValueError("config must be a ResearchStrategyRiskGateSummaryConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in _normalize_candidates(candidates)),
            key=_row_sort_key,
        ),
    )
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": _report_status(rows),
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_aggregate_uncertainty_score": _average(
            row.aggregate_uncertainty_score for row in rows
        ),
        "average_cost_pressure_score": _average(row.cost_pressure_score for row in rows),
        "average_liquidity_quality_score": _average(
            row.liquidity_quality_score for row in rows
        ),
        "average_settlement_risk_score": _average(row.settlement_risk_score for row in rows),
        "average_information_freshness_score": _average(
            row.information_freshness_score for row in rows
        ),
        "average_team_disagreement_score": _average(
            row.team_disagreement_score for row in rows
        ),
        "average_composite_risk_score": _average(row.composite_risk_score for row in rows),
        "min_liquidity_quality_score": _min_or_zero(
            row.liquidity_quality_score for row in rows
        ),
        "min_information_freshness_score": _min_or_zero(
            row.information_freshness_score for row in rows
        ),
        "max_composite_risk_score": _max_or_zero(row.composite_risk_score for row in rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["risk_gate_summary_digest"] = _digest_payload(_payload_value(values))
    return ResearchStrategyRiskGateSummaryReport(**values)


def research_strategy_risk_gate_summary_report_payload(
    report: ResearchStrategyRiskGateSummaryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyRiskGateSummaryReport:
        raise ValueError("report must be a ResearchStrategyRiskGateSummaryReport")
    _require_hard_flags(report)
    payload = report.payload
    _reject_unsafe_public_payload(
        "ResearchStrategyRiskGateSummaryReport.payload",
        payload,
    )
    return payload


def _row_from_candidate(
    candidate: ResearchStrategyRiskGateCandidate,
    *,
    config: ResearchStrategyRiskGateSummaryConfig,
) -> ResearchStrategyRiskGateSummaryRow:
    composite_score = _composite_risk_score(candidate)
    reason_codes = _candidate_reason_codes(candidate, config, composite_score)
    return ResearchStrategyRiskGateSummaryRow(
        anonymized_candidate_key=candidate.anonymized_candidate_key,
        aggregate_uncertainty_score=candidate.aggregate_uncertainty_score,
        cost_pressure_score=candidate.cost_pressure_score,
        liquidity_quality_score=candidate.liquidity_quality_score,
        settlement_risk_score=candidate.settlement_risk_score,
        information_freshness_score=candidate.information_freshness_score,
        team_disagreement_score=candidate.team_disagreement_score,
        composite_risk_score=composite_score,
        gate_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _candidate_reason_codes(
    candidate: ResearchStrategyRiskGateCandidate,
    config: ResearchStrategyRiskGateSummaryConfig,
    composite_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name, watch_name, block_name, watch_reason, block_reason in _HIGH_RISK_SPECS:
        value = getattr(candidate, field_name)
        if value >= getattr(config, block_name):
            reasons.append(block_reason)
        elif value >= getattr(config, watch_name):
            reasons.append(watch_reason)
    for field_name, watch_name, block_name, watch_reason, block_reason in _FLOOR_RISK_SPECS:
        value = getattr(candidate, field_name)
        if value <= getattr(config, block_name):
            reasons.append(block_reason)
        elif value < getattr(config, watch_name):
            reasons.append(watch_reason)
    if composite_score >= config.block_composite_risk_score:
        reasons.append("composite_risk_block")
    elif composite_score >= config.watch_composite_risk_score:
        reasons.append("composite_risk_watch")
    if not reasons:
        reasons.append(_PASS_REASON)
    return _ordered_reason_codes(reasons)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchStrategyRiskGateCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be iterable") from exc
    seen_keys: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyRiskGateCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyRiskGateCandidate values",
            )
        _require_hard_flags(item)
        if item.anonymized_candidate_key in seen_keys:
            raise ValueError("duplicate anonymized_candidate_key")
        seen_keys.add(item.anonymized_candidate_key)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyRiskGateSummaryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyRiskGateSummaryRow:
            raise ValueError("rows must contain ResearchStrategyRiskGateSummaryRow values")
        _require_hard_flags(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len({row.anonymized_candidate_key for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: ResearchStrategyRiskGateSummaryRow) -> None:
    if row.composite_risk_score != _composite_risk_score(row):
        raise ValueError("composite_risk_score must match row scores")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if row.gate_status == "pass" and row.reason_codes != (_PASS_REASON,):
        raise ValueError("pass rows must include only pass reason")
    if row.gate_status == "watch" and not any(
        reason_code in _WATCH_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must include watch reason")
    if row.gate_status == "block" and not any(
        reason_code in _BLOCK_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include block reason")


def _validate_report(report: ResearchStrategyRiskGateSummaryReport) -> None:
    rows = report.rows
    if report.config_version != DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    for report_field_name, row_field_name in (
        ("average_aggregate_uncertainty_score", "aggregate_uncertainty_score"),
        ("average_cost_pressure_score", "cost_pressure_score"),
        ("average_liquidity_quality_score", "liquidity_quality_score"),
        ("average_settlement_risk_score", "settlement_risk_score"),
        ("average_information_freshness_score", "information_freshness_score"),
        ("average_team_disagreement_score", "team_disagreement_score"),
        ("average_composite_risk_score", "composite_risk_score"),
    ):
        if getattr(report, report_field_name) != _average(
            getattr(row, row_field_name) for row in rows
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.min_liquidity_quality_score != _min_or_zero(
        row.liquidity_quality_score for row in rows
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.min_information_freshness_score != _min_or_zero(
        row.information_freshness_score for row in rows
    ):
        raise ValueError("min_information_freshness_score must match rows")
    if report.max_composite_risk_score != _max_or_zero(
        row.composite_risk_score for row in rows
    ):
        raise ValueError("max_composite_risk_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_digest(report: ResearchStrategyRiskGateSummaryReport) -> None:
    payload = report.payload
    payload_without_digest = dict(payload)
    payload_without_digest.pop("risk_gate_summary_digest")
    expected = _digest_payload(payload_without_digest)
    if report.risk_gate_summary_digest != expected:
        raise ValueError("risk_gate_summary_digest must match payload")


def _composite_risk_score(value: object) -> Decimal:
    return _quantize(
        (
            getattr(value, "aggregate_uncertainty_score")
            + getattr(value, "cost_pressure_score")
            + (_ONE - getattr(value, "liquidity_quality_score"))
            + getattr(value, "settlement_risk_score")
            + (_ONE - getattr(value, "information_freshness_score"))
            + getattr(value, "team_disagreement_score")
        )
        / _SIX,
    )


def _report_status(rows: tuple[ResearchStrategyRiskGateSummaryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchStrategyRiskGateSummaryRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchStrategyRiskGateSummaryRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.gate_status],
        -row.composite_risk_score,
        -row.aggregate_uncertainty_score,
        -row.cost_pressure_score,
        row.anonymized_candidate_key,
    )


def _candidate_score_fields() -> tuple[str, ...]:
    return (
        "aggregate_uncertainty_score",
        "cost_pressure_score",
        "liquidity_quality_score",
        "settlement_risk_score",
        "information_freshness_score",
        "team_disagreement_score",
    )


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _quantize(sum(items, _ZERO) / Decimal(len(items)))


def _min_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return min(items)


def _max_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _status_count(rows: tuple[ResearchStrategyRiskGateSummaryRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if not value.same_quantum(_SCORE_QUANT):
        raise ValueError(f"{field_name} must use six decimal places")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_high_risk_threshold_pair(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"block_{field_name} must be at least watch threshold")


def _validate_floor_threshold_pair(
    block_field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"{block_field_name} must be no greater than watch threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_text(field_name: str, value: object) -> str:
    text = _require_canonical_text(field_name, value)
    _reject_unsafe_text(field_name, text)
    return text


def _require_canonical_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_canonical_text(field_name, reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError(f"{field_name} must contain known reasons")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        reason_index = _REASON_PRIORITY.index(reason_code)
        if reason_index <= previous_index:
            raise ValueError(f"{field_name} must use priority order")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _ordered_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    observed = set(reason_codes)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed),
    )


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a hex digest")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a hex digest")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _digest_payload(payload: object) -> str:
    payload_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(payload_text.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RISK_GATE_SUMMARY_CONFIG_VERSION",
    "ResearchStrategyRiskGateCandidate",
    "ResearchStrategyRiskGateSummaryConfig",
    "ResearchStrategyRiskGateSummaryReport",
    "ResearchStrategyRiskGateSummaryRow",
    "build_research_strategy_risk_gate_summary_report",
    "research_strategy_risk_gate_summary_report_payload",
)
