"""Pure Phase 1 candidate event-asymmetry gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_EVENT_ASYMMETRY_GATE_V2_CONFIG_VERSION = (
    "strategy-candidate-tail-risk-event-asymmetry-gate-v2"
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

_PASS_REASON = "tail_risk_event_asymmetry_gate_pass"
_EMPTY_REASON = "tail_risk_event_asymmetry_gate_empty"
_PENALTY_WATCH_REASON = "event_asymmetry_penalty_watch"
_PENALTY_BLOCK_REASON = "event_asymmetry_penalty_block"
_LIQUIDITY_WATCH_REASON = "low_liquidity_exit_watch"
_LIQUIDITY_BLOCK_REASON = "low_liquidity_exit_block"
_AMBIGUITY_WATCH_REASON = "high_ambiguity_watch"
_AMBIGUITY_BLOCK_REASON = "high_ambiguity_block"
_CATALYST_WATCH_REASON = "negative_catalyst_cluster_watch"
_CATALYST_BLOCK_REASON = "negative_catalyst_cluster_block"
_LAG_WATCH_REASON = "settlement_lag_watch"
_LAG_BLOCK_REASON = "settlement_lag_block"
_DISAGREEMENT_WATCH_REASON = "source_disagreement_watch"
_DISAGREEMENT_BLOCK_REASON = "source_disagreement_block"

_REASON_PRIORITY = (
    _LIQUIDITY_BLOCK_REASON,
    _AMBIGUITY_BLOCK_REASON,
    _CATALYST_BLOCK_REASON,
    _LAG_BLOCK_REASON,
    _DISAGREEMENT_BLOCK_REASON,
    _PENALTY_BLOCK_REASON,
    _LIQUIDITY_WATCH_REASON,
    _AMBIGUITY_WATCH_REASON,
    _CATALYST_WATCH_REASON,
    _LAG_WATCH_REASON,
    _DISAGREEMENT_WATCH_REASON,
    _PENALTY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(
    (
        _LIQUIDITY_BLOCK_REASON,
        _AMBIGUITY_BLOCK_REASON,
        _CATALYST_BLOCK_REASON,
        _LAG_BLOCK_REASON,
        _DISAGREEMENT_BLOCK_REASON,
        _PENALTY_BLOCK_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _LIQUIDITY_WATCH_REASON,
        _AMBIGUITY_WATCH_REASON,
        _CATALYST_WATCH_REASON,
        _LAG_WATCH_REASON,
        _DISAGREEMENT_WATCH_REASON,
        _PENALTY_WATCH_REASON,
    ),
)
_COMPONENT_SPECS = (
    ("liquidity_exit_risk_score", _LIQUIDITY_WATCH_REASON, _LIQUIDITY_BLOCK_REASON),
    ("ambiguity_risk_score", _AMBIGUITY_WATCH_REASON, _AMBIGUITY_BLOCK_REASON),
    (
        "negative_catalyst_cluster_score",
        _CATALYST_WATCH_REASON,
        _CATALYST_BLOCK_REASON,
    ),
    ("settlement_lag_risk_score", _LAG_WATCH_REASON, _LAG_BLOCK_REASON),
    (
        "source_disagreement_score",
        _DISAGREEMENT_WATCH_REASON,
        _DISAGREEMENT_BLOCK_REASON,
    ),
)
_WEIGHT_FIELDS = (
    "liquidity_exit_weight",
    "ambiguity_weight",
    "negative_catalyst_cluster_weight",
    "settlement_lag_weight",
    "source_disagreement_weight",
)


@dataclass(frozen=True)
class StrategyCandidateTailRiskEventAsymmetryGateConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_EVENT_ASYMMETRY_GATE_V2_CONFIG_VERSION
    )
    watch_component_score: Decimal = Decimal("0.350000")
    block_component_score: Decimal = Decimal("0.700000")
    watch_penalty_score: Decimal = Decimal("0.350000")
    block_penalty_score: Decimal = Decimal("0.700000")
    liquidity_exit_weight: Decimal = Decimal("0.250000")
    ambiguity_weight: Decimal = Decimal("0.200000")
    negative_catalyst_cluster_weight: Decimal = Decimal("0.250000")
    settlement_lag_weight: Decimal = Decimal("0.150000")
    source_disagreement_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateTailRiskEventAsymmetryGateConfig:
            raise TypeError(
                "StrategyCandidateTailRiskEventAsymmetryGateConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateTailRiskEventAsymmetryGateConfig:
            raise ValueError(
                "config must be exactly "
                "StrategyCandidateTailRiskEventAsymmetryGateConfig",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "watch_component_score",
            "block_component_score",
            "watch_penalty_score",
            "block_penalty_score",
            *_WEIGHT_FIELDS,
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "block_component_score",
            self.watch_component_score,
            self.block_component_score,
        )
        _require_threshold_sequence(
            "block_penalty_score",
            self.watch_penalty_score,
            self.block_penalty_score,
        )
        if _weight_total(self) <= _ZERO:
            raise ValueError("weight total must be positive")
        require_paper_only_flags("event asymmetry config", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskEventAsymmetryCandidate:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    base_candidate_score: Decimal
    liquidity_exit_risk_score: Decimal
    ambiguity_risk_score: Decimal
    negative_catalyst_cluster_score: Decimal
    settlement_lag_risk_score: Decimal
    source_disagreement_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateTailRiskEventAsymmetryCandidate:
            raise TypeError(
                "StrategyCandidateTailRiskEventAsymmetryCandidate "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateTailRiskEventAsymmetryCandidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyCandidateTailRiskEventAsymmetryCandidate",
            )
        _require_text("candidate_id", self.candidate_id)
        _require_text("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name, _, _ in _COMPONENT_SPECS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "base_candidate_score",
            _normalize_unit_decimal("base_candidate_score", self.base_candidate_score),
        )
        require_paper_only_flags("event asymmetry candidate", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskEventAsymmetryGateRow:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    base_candidate_score: Decimal
    liquidity_exit_risk_score: Decimal
    ambiguity_risk_score: Decimal
    negative_catalyst_cluster_score: Decimal
    settlement_lag_risk_score: Decimal
    source_disagreement_score: Decimal
    asymmetry_penalty_score: Decimal
    adjusted_candidate_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateTailRiskEventAsymmetryGateRow:
            raise TypeError(
                "StrategyCandidateTailRiskEventAsymmetryGateRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateTailRiskEventAsymmetryGateRow:
            raise ValueError(
                "row must be exactly StrategyCandidateTailRiskEventAsymmetryGateRow",
            )
        _require_text("candidate_id", self.candidate_id)
        _require_text("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name, _, _ in _COMPONENT_SPECS:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_candidate_score",
            "asymmetry_penalty_score",
            "adjusted_candidate_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("event asymmetry row", self)


@dataclass(frozen=True)
class StrategyCandidateTailRiskEventAsymmetryGateReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_asymmetry_penalty_score: Decimal
    min_adjusted_candidate_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateTailRiskEventAsymmetryGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateTailRiskEventAsymmetryGateReport:
            raise TypeError(
                "StrategyCandidateTailRiskEventAsymmetryGateReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateTailRiskEventAsymmetryGateReport:
            raise ValueError(
                "report must be exactly StrategyCandidateTailRiskEventAsymmetryGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_asymmetry_penalty_score",
            "min_adjusted_candidate_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("event asymmetry report", self)


def build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report(
    candidates: Iterable[object],
    *,
    config: StrategyCandidateTailRiskEventAsymmetryGateConfig,
    generated_at: datetime,
) -> StrategyCandidateTailRiskEventAsymmetryGateReport:
    if type(config) is not StrategyCandidateTailRiskEventAsymmetryGateConfig:
        raise ValueError("config must be a StrategyCandidateTailRiskEventAsymmetryGateConfig")
    require_paper_only_flags("event asymmetry config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in _normalize_candidates(candidates)
            ),
            key=_row_key,
        ),
    )
    return StrategyCandidateTailRiskEventAsymmetryGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.gate_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.gate_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.gate_status == "block")),
        max_asymmetry_penalty_score=_max_decimal(
            row.asymmetry_penalty_score for row in rows
        ),
        min_adjusted_candidate_score=_min_decimal(row.adjusted_candidate_score for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_tail_risk_event_asymmetry_gate_v2_payload(
    report: StrategyCandidateTailRiskEventAsymmetryGateReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateTailRiskEventAsymmetryGateReport:
        raise ValueError("report must be a StrategyCandidateTailRiskEventAsymmetryGateReport")
    require_paper_only_flags("event asymmetry report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    require_paper_only_flags("event asymmetry payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_candidate(
    candidate: StrategyCandidateTailRiskEventAsymmetryCandidate,
    *,
    config: StrategyCandidateTailRiskEventAsymmetryGateConfig,
    generated_at: datetime,
) -> StrategyCandidateTailRiskEventAsymmetryGateRow:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    penalty_score = _penalty_score(candidate, config)
    adjusted_score = _clamp_unit(candidate.base_candidate_score - penalty_score)
    reason_codes = _row_reason_codes(candidate, penalty_score=penalty_score, config=config)
    return StrategyCandidateTailRiskEventAsymmetryGateRow(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        observed_at=candidate.observed_at,
        base_candidate_score=candidate.base_candidate_score,
        liquidity_exit_risk_score=candidate.liquidity_exit_risk_score,
        ambiguity_risk_score=candidate.ambiguity_risk_score,
        negative_catalyst_cluster_score=candidate.negative_catalyst_cluster_score,
        settlement_lag_risk_score=candidate.settlement_lag_risk_score,
        source_disagreement_score=candidate.source_disagreement_score,
        asymmetry_penalty_score=penalty_score,
        adjusted_candidate_score=adjusted_score,
        gate_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    candidate: StrategyCandidateTailRiskEventAsymmetryCandidate,
    *,
    penalty_score: Decimal,
    config: StrategyCandidateTailRiskEventAsymmetryGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for field_name, watch_reason, block_reason in _COMPONENT_SPECS:
        score = getattr(candidate, field_name)
        if score >= config.block_component_score:
            reason_codes.append(block_reason)
        elif score >= config.watch_component_score:
            reason_codes.append(watch_reason)
    if penalty_score >= config.block_penalty_score:
        reason_codes.append(_PENALTY_BLOCK_REASON)
    elif penalty_score >= config.watch_penalty_score:
        reason_codes.append(_PENALTY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _penalty_score(
    candidate: StrategyCandidateTailRiskEventAsymmetryCandidate,
    config: StrategyCandidateTailRiskEventAsymmetryGateConfig,
) -> Decimal:
    total_weight = _weight_total(config)
    weighted_total = (
        candidate.liquidity_exit_risk_score * config.liquidity_exit_weight
        + candidate.ambiguity_risk_score * config.ambiguity_weight
        + candidate.negative_catalyst_cluster_score
        * config.negative_catalyst_cluster_weight
        + candidate.settlement_lag_risk_score * config.settlement_lag_weight
        + candidate.source_disagreement_score * config.source_disagreement_weight
    )
    return _clamp_unit(weighted_total / total_weight)


def _weight_total(config: StrategyCandidateTailRiskEventAsymmetryGateConfig) -> Decimal:
    return _quantize(sum((getattr(config, field_name) for field_name in _WEIGHT_FIELDS), _ZERO))


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyCandidateTailRiskEventAsymmetryCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be iterable") from exc
    seen_ids: set[str] = set()
    for item in items:
        if type(item) is not StrategyCandidateTailRiskEventAsymmetryCandidate:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateTailRiskEventAsymmetryCandidate values",
            )
        require_paper_only_flags("event asymmetry candidate", item)
        if item.candidate_id in seen_ids:
            raise ValueError("duplicate candidate_id")
        seen_ids.add(item.candidate_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCandidateTailRiskEventAsymmetryGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateTailRiskEventAsymmetryGateRow:
            raise ValueError(
                "rows must contain StrategyCandidateTailRiskEventAsymmetryGateRow values",
            )
        require_paper_only_flags("event asymmetry row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    if len({row.candidate_id for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: StrategyCandidateTailRiskEventAsymmetryGateRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    expected_adjusted_score = _clamp_unit(
        row.base_candidate_score - row.asymmetry_penalty_score,
    )
    if row.adjusted_candidate_score != expected_adjusted_score:
        raise ValueError("adjusted_candidate_score must match score less penalty")
    if row.gate_status == "pass" and _PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.gate_status == "watch" and not any(
        reason_code in _WATCH_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must include watch reason")
    if row.gate_status == "block" and not any(
        reason_code in _BLOCK_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must include block reason")


def _validate_report(report: StrategyCandidateTailRiskEventAsymmetryGateReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.gate_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.gate_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.gate_status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_asymmetry_penalty_score != _max_decimal(
        row.asymmetry_penalty_score for row in rows
    ):
        raise ValueError("max_asymmetry_penalty_score must match rows")
    if report.min_adjusted_candidate_score != _min_decimal(
        row.adjusted_candidate_score for row in rows
    ):
        raise ValueError("min_adjusted_candidate_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _report_status(
    rows: tuple[StrategyCandidateTailRiskEventAsymmetryGateRow, ...],
) -> str:
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateTailRiskEventAsymmetryGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _WATCH_REASONS or reason_code in _BLOCK_REASONS
    }
    if not observed:
        return (_PASS_REASON,)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_key(
    row: StrategyCandidateTailRiskEventAsymmetryGateRow,
) -> tuple[int, Decimal, Decimal, datetime, str, str]:
    return (
        _STATUS_WEIGHT[row.gate_status],
        -row.asymmetry_penalty_score,
        row.adjusted_candidate_score,
        row.observed_at,
        row.candidate_id,
        row.market_slug,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        reason_index = _REASON_PRIORITY.index(reason_code)
        if reason_code in seen or reason_index <= previous_index:
            raise ValueError("reason_codes must use priority sequence")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    observed: set[str] = set()
    for reason_code in value:
        _require_text("reason_codes", reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        observed.add(reason_code)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return min(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _clamp_unit(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_threshold_sequence(
    threshold_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{threshold_name} must be at least watch threshold")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be block, watch, or pass")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_TAIL_RISK_EVENT_ASYMMETRY_GATE_V2_CONFIG_VERSION",
    "StrategyCandidateTailRiskEventAsymmetryCandidate",
    "StrategyCandidateTailRiskEventAsymmetryGateConfig",
    "StrategyCandidateTailRiskEventAsymmetryGateReport",
    "StrategyCandidateTailRiskEventAsymmetryGateRow",
    "build_strategy_candidate_tail_risk_event_asymmetry_gate_v2_report",
    "strategy_candidate_tail_risk_event_asymmetry_gate_v2_payload",
)
