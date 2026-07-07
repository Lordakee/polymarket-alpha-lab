"""Phase 1 paper-only contradiction-penalized EV candidate scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION = (
    "strategy-candidate-contradiction-penalized-ev-v2"
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MINUS_ONE = Decimal("-1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_REASON_CODE_SEQUENCE = (
    "candidate_input",
    "empty_candidate_set",
    "negative_penalized_ev",
    "contradiction_severity_block",
    "low_penalized_ev_watch",
    "contradiction_severity_watch",
    "source_contradiction_penalty",
    "official_source_conflict",
    "resolution_ambiguity_penalty",
    "execution_cost_penalty",
    "liquidity_risk_penalty",
    "contradiction_penalized_ev_pass",
)
_REPORT_REASON_CODE_SEQUENCE = tuple(
    reason
    for reason in _REASON_CODE_SEQUENCE
    if reason not in {"candidate_input", "empty_candidate_set"}
)


@dataclass(frozen=True)
class StrategyCandidateContradictionPenalizedEvV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION
    )
    watch_penalized_ev_floor: Decimal = Decimal("0.010000")
    pass_penalized_ev_floor: Decimal = Decimal("0.030000")
    watch_contradiction_severity: Decimal = Decimal("0.040000")
    block_contradiction_severity: Decimal = Decimal("0.120000")
    official_source_conflict_block: Decimal = Decimal("0.800000")
    source_contradiction_weight: Decimal = Decimal("0.200000")
    official_source_conflict_weight: Decimal = Decimal("0.300000")
    resolution_ambiguity_weight: Decimal = Decimal("0.100000")
    liquidity_risk_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateContradictionPenalizedEvV2Config:
            raise TypeError(
                "StrategyCandidateContradictionPenalizedEvV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateContradictionPenalizedEvV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyCandidateContradictionPenalizedEvV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_penalized_ev_floor",
            "pass_penalized_ev_floor",
            "watch_contradiction_severity",
            "block_contradiction_severity",
            "official_source_conflict_block",
            "source_contradiction_weight",
            "official_source_conflict_weight",
            "resolution_ambiguity_weight",
            "liquidity_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_penalized_ev_floor > self.pass_penalized_ev_floor:
            raise ValueError(
                "watch_penalized_ev_floor must not exceed pass_penalized_ev_floor",
            )
        if self.block_contradiction_severity < self.watch_contradiction_severity:
            raise ValueError(
                "block_contradiction_severity must be at least "
                "watch_contradiction_severity",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCandidateContradictionPenalizedEvV2Candidate:
    candidate_id: str
    market_id: str
    evaluated_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    confidence_score: Decimal
    source_contradiction: Decimal
    official_source_conflict: Decimal
    resolution_ambiguity: Decimal
    taker_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    liquidity_risk: Decimal
    reason_codes: tuple[str, ...] = ("candidate_input",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateContradictionPenalizedEvV2Candidate:
            raise TypeError(
                "StrategyCandidateContradictionPenalizedEvV2Candidate does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateContradictionPenalizedEvV2Candidate:
            raise ValueError(
                "candidate must be exactly "
                "StrategyCandidateContradictionPenalizedEvV2Candidate",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        _require_public_identifier("market_id", self.market_id)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in (
            "forecast_probability",
            "market_probability",
            "confidence_score",
            "source_contradiction",
            "official_source_conflict",
            "resolution_ambiguity",
            "taker_cost",
            "spread_cost",
            "slippage_cost",
            "liquidity_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateContradictionPenalizedEvV2Row:
    candidate_id: str
    market_id: str
    evaluated_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    raw_edge: Decimal
    confidence_score: Decimal
    confidence_adjusted_edge: Decimal
    source_contradiction: Decimal
    official_source_conflict: Decimal
    resolution_ambiguity: Decimal
    contradiction_severity: Decimal
    taker_cost: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    execution_cost: Decimal
    liquidity_risk: Decimal
    liquidity_risk_penalty: Decimal
    total_penalty: Decimal
    contradiction_penalized_ev: Decimal
    ev_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateContradictionPenalizedEvV2Row:
            raise TypeError(
                "StrategyCandidateContradictionPenalizedEvV2Row does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateContradictionPenalizedEvV2Row:
            raise ValueError(
                "row must be exactly StrategyCandidateContradictionPenalizedEvV2Row",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        _require_public_identifier("market_id", self.market_id)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        for field_name in (
            "forecast_probability",
            "market_probability",
            "confidence_score",
            "source_contradiction",
            "official_source_conflict",
            "resolution_ambiguity",
            "contradiction_severity",
            "taker_cost",
            "spread_cost",
            "slippage_cost",
            "execution_cost",
            "liquidity_risk",
            "liquidity_risk_penalty",
            "total_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "raw_edge",
            "confidence_adjusted_edge",
            "contradiction_penalized_ev",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_edge_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("ev_status", self.ev_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        return _row_payload(self, include_digest=True)


@dataclass(frozen=True)
class StrategyCandidateContradictionPenalizedEvV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_contradiction_penalized_ev: Decimal
    max_contradiction_severity: Decimal
    max_execution_cost: Decimal
    report_status: str
    rows: tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateContradictionPenalizedEvV2Report:
            raise TypeError(
                "StrategyCandidateContradictionPenalizedEvV2Report does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateContradictionPenalizedEvV2Report:
            raise ValueError(
                "report must be exactly StrategyCandidateContradictionPenalizedEvV2Report",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_contradiction_penalized_ev",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_edge_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_contradiction_severity",
            "max_execution_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        return strategy_candidate_contradiction_penalized_ev_v2_payload(self)


def build_strategy_candidate_contradiction_penalized_ev_v2(
    candidates: Sequence[StrategyCandidateContradictionPenalizedEvV2Candidate],
    *,
    config: StrategyCandidateContradictionPenalizedEvV2Config,
    generated_at: datetime,
) -> StrategyCandidateContradictionPenalizedEvV2Report:
    if type(config) is not StrategyCandidateContradictionPenalizedEvV2Config:
        raise ValueError(
            "config must be StrategyCandidateContradictionPenalizedEvV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for candidate in normalized_candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_candidate(candidate, config=config)
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyCandidateContradictionPenalizedEvV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_contradiction_penalized_ev=_average_edge(
            tuple(row.contradiction_penalized_ev for row in rows),
        ),
        max_contradiction_severity=max(
            (row.contradiction_severity for row in rows),
            default=_ZERO,
        ),
        max_execution_cost=max((row.execution_cost for row in rows), default=_ZERO),
        report_status=_report_status(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_candidate_contradiction_penalized_ev_v2_payload(
    value: StrategyCandidateContradictionPenalizedEvV2Report | dict[str, object],
) -> dict[str, object]:
    if type(value) is StrategyCandidateContradictionPenalizedEvV2Report:
        _require_hard_flags("report", value)
        _validate_report(value)
        payload = _report_payload(value, include_digest=True)
    elif type(value) is dict:
        payload = _copy_payload(value)
    else:
        raise ValueError(
            "value must be a StrategyCandidateContradictionPenalizedEvV2Report or dict",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _reject_json_numeric_payload(payload)
    _verify_payload_digests(payload)
    return payload


def _row_from_candidate(
    candidate: StrategyCandidateContradictionPenalizedEvV2Candidate,
    *,
    config: StrategyCandidateContradictionPenalizedEvV2Config,
) -> StrategyCandidateContradictionPenalizedEvV2Row:
    raw_edge = _subtract(candidate.forecast_probability, candidate.market_probability)
    confidence_adjusted_edge = _multiply(raw_edge, candidate.confidence_score)
    contradiction_severity = _clamp_ratio(
        _add(
            _multiply(candidate.source_contradiction, config.source_contradiction_weight),
            _multiply(
                candidate.official_source_conflict,
                config.official_source_conflict_weight,
            ),
            _multiply(
                candidate.resolution_ambiguity,
                config.resolution_ambiguity_weight,
            ),
        ),
    )
    execution_cost = _clamp_ratio(
        _add(candidate.taker_cost, candidate.spread_cost, candidate.slippage_cost),
    )
    liquidity_risk_penalty = _multiply(candidate.liquidity_risk, config.liquidity_risk_weight)
    total_penalty = _clamp_ratio(
        _add(contradiction_severity, execution_cost, liquidity_risk_penalty),
    )
    contradiction_penalized_ev = _subtract(confidence_adjusted_edge, total_penalty)
    ev_status = _row_status(
        contradiction_penalized_ev=contradiction_penalized_ev,
        contradiction_severity=contradiction_severity,
        official_source_conflict=candidate.official_source_conflict,
        config=config,
    )
    return StrategyCandidateContradictionPenalizedEvV2Row(
        candidate_id=candidate.candidate_id,
        market_id=candidate.market_id,
        evaluated_at=candidate.evaluated_at,
        forecast_probability=candidate.forecast_probability,
        market_probability=candidate.market_probability,
        raw_edge=raw_edge,
        confidence_score=candidate.confidence_score,
        confidence_adjusted_edge=confidence_adjusted_edge,
        source_contradiction=candidate.source_contradiction,
        official_source_conflict=candidate.official_source_conflict,
        resolution_ambiguity=candidate.resolution_ambiguity,
        contradiction_severity=contradiction_severity,
        taker_cost=candidate.taker_cost,
        spread_cost=candidate.spread_cost,
        slippage_cost=candidate.slippage_cost,
        execution_cost=execution_cost,
        liquidity_risk=candidate.liquidity_risk,
        liquidity_risk_penalty=liquidity_risk_penalty,
        total_penalty=total_penalty,
        contradiction_penalized_ev=contradiction_penalized_ev,
        ev_status=ev_status,
        reason_codes=_row_reason_codes(
            candidate.reason_codes,
            ev_status=ev_status,
            contradiction_penalized_ev=contradiction_penalized_ev,
            contradiction_severity=contradiction_severity,
            source_contradiction=candidate.source_contradiction,
            official_source_conflict=candidate.official_source_conflict,
            resolution_ambiguity=candidate.resolution_ambiguity,
            execution_cost=execution_cost,
            liquidity_risk_penalty=liquidity_risk_penalty,
            config=config,
        ),
    )


def _row_status(
    *,
    contradiction_penalized_ev: Decimal,
    contradiction_severity: Decimal,
    official_source_conflict: Decimal,
    config: StrategyCandidateContradictionPenalizedEvV2Config,
) -> str:
    if contradiction_penalized_ev < _ZERO:
        return "blocked"
    if contradiction_severity >= config.block_contradiction_severity:
        return "blocked"
    if official_source_conflict >= config.official_source_conflict_block:
        return "blocked"
    if contradiction_penalized_ev < config.pass_penalized_ev_floor:
        return "watch"
    if contradiction_severity >= config.watch_contradiction_severity:
        return "watch"
    return "pass"


def _row_reason_codes(
    input_reason_codes: tuple[str, ...],
    *,
    ev_status: str,
    contradiction_penalized_ev: Decimal,
    contradiction_severity: Decimal,
    source_contradiction: Decimal,
    official_source_conflict: Decimal,
    resolution_ambiguity: Decimal,
    execution_cost: Decimal,
    liquidity_risk_penalty: Decimal,
    config: StrategyCandidateContradictionPenalizedEvV2Config,
) -> tuple[str, ...]:
    reason_codes = list(input_reason_codes)
    if contradiction_penalized_ev < _ZERO:
        reason_codes.append("negative_penalized_ev")
    if (
        contradiction_severity >= config.block_contradiction_severity
        or official_source_conflict >= config.official_source_conflict_block
    ):
        reason_codes.append("contradiction_severity_block")
    if official_source_conflict > _ZERO:
        reason_codes.append("official_source_conflict")
    if (
        contradiction_penalized_ev < config.pass_penalized_ev_floor
        and contradiction_penalized_ev >= _ZERO
    ):
        reason_codes.append("low_penalized_ev_watch")
    if (
        contradiction_severity >= config.watch_contradiction_severity
        and contradiction_severity < config.block_contradiction_severity
    ):
        reason_codes.append("contradiction_severity_watch")
    if source_contradiction > _ZERO:
        reason_codes.append("source_contradiction_penalty")
    if resolution_ambiguity > _ZERO:
        reason_codes.append("resolution_ambiguity_penalty")
    if execution_cost > _ZERO:
        reason_codes.append("execution_cost_penalty")
    if liquidity_risk_penalty > _ZERO:
        reason_codes.append("liquidity_risk_penalty")
    if ev_status == "pass":
        reason_codes.append("contradiction_penalized_ev_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_candidate_set",)
    reason_codes = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in _REPORT_REASON_CODE_SEQUENCE if reason in reason_codes)


def _report_status(
    rows: tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...],
) -> str:
    if not rows:
        return "pass"
    if any(row.ev_status == "blocked" for row in rows):
        return "blocked"
    if any(row.ev_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.ev_status == status))


def _normalize_candidates(
    value: Sequence[StrategyCandidateContradictionPenalizedEvV2Candidate],
) -> tuple[StrategyCandidateContradictionPenalizedEvV2Candidate, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(value)
    seen_candidate_ids: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyCandidateContradictionPenalizedEvV2Candidate:
            raise ValueError(
                "candidates must contain StrategyCandidateContradictionPenalizedEvV2Candidate",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_id in seen_candidate_ids:
            raise ValueError("duplicate candidate_id")
        seen_candidate_ids.add(candidate.candidate_id)
    return normalized


def _normalize_rows(
    value: tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...],
) -> tuple[StrategyCandidateContradictionPenalizedEvV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(value)
    for row in normalized:
        if type(row) is not StrategyCandidateContradictionPenalizedEvV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateContradictionPenalizedEvV2Row",
            )
        _require_hard_flags("row", row)
    row_keys = tuple(_row_sort_key(row) for row in normalized)
    if row_keys != tuple(sorted(row_keys)):
        raise ValueError("rows must be sorted by candidate_id and market_id")
    candidate_ids = tuple(row.candidate_id for row in normalized)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("rows must have unique candidate_id values")
    return normalized


def _row_sort_key(row: StrategyCandidateContradictionPenalizedEvV2Row) -> tuple[str, str]:
    return (row.candidate_id, row.market_id)


def _validate_row(row: StrategyCandidateContradictionPenalizedEvV2Row) -> None:
    expected_raw_edge = _subtract(row.forecast_probability, row.market_probability)
    if row.raw_edge != expected_raw_edge:
        raise ValueError("raw_edge must match forecast_probability minus market_probability")
    expected_confidence_adjusted_edge = _multiply(row.raw_edge, row.confidence_score)
    if row.confidence_adjusted_edge != expected_confidence_adjusted_edge:
        raise ValueError("confidence_adjusted_edge must match raw_edge times confidence_score")
    expected_execution_cost = _clamp_ratio(
        _add(row.taker_cost, row.spread_cost, row.slippage_cost),
    )
    if row.execution_cost != expected_execution_cost:
        raise ValueError("execution_cost must match taker, spread, and slippage costs")
    expected_total_penalty = _clamp_ratio(
        _add(row.contradiction_severity, row.execution_cost, row.liquidity_risk_penalty),
    )
    if row.total_penalty != expected_total_penalty:
        raise ValueError("total_penalty must match severity, cost, and liquidity penalties")
    expected_ev = _subtract(row.confidence_adjusted_edge, row.total_penalty)
    if row.contradiction_penalized_ev != expected_ev:
        raise ValueError("contradiction_penalized_ev must match adjusted edge minus penalty")
    if row.ev_status != _status_from_row_values(row):
        raise ValueError("ev_status must match contradiction-penalized EV rules")
    if row.reason_codes != _reason_codes_from_row_values(row):
        raise ValueError("reason_codes must match contradiction-penalized EV rules")


def _status_from_row_values(row: StrategyCandidateContradictionPenalizedEvV2Row) -> str:
    if row.contradiction_penalized_ev < _ZERO:
        return "blocked"
    if "contradiction_severity_block" in row.reason_codes:
        return "blocked"
    if "low_penalized_ev_watch" in row.reason_codes:
        return "watch"
    if "contradiction_severity_watch" in row.reason_codes:
        return "watch"
    return "pass"


def _reason_codes_from_row_values(
    row: StrategyCandidateContradictionPenalizedEvV2Row,
) -> tuple[str, ...]:
    reason_codes = [
        reason
        for reason in row.reason_codes
        if reason
        in {
            "candidate_input",
            "negative_penalized_ev",
            "contradiction_severity_block",
            "official_source_conflict",
            "low_penalized_ev_watch",
            "contradiction_severity_watch",
            "source_contradiction_penalty",
            "resolution_ambiguity_penalty",
            "execution_cost_penalty",
            "liquidity_risk_penalty",
            "contradiction_penalized_ev_pass",
        }
    ]
    if row.contradiction_penalized_ev < _ZERO and "negative_penalized_ev" not in reason_codes:
        reason_codes.append("negative_penalized_ev")
    if row.official_source_conflict > _ZERO and "official_source_conflict" not in reason_codes:
        reason_codes.append("official_source_conflict")
    if row.source_contradiction > _ZERO and "source_contradiction_penalty" not in reason_codes:
        reason_codes.append("source_contradiction_penalty")
    if row.resolution_ambiguity > _ZERO and "resolution_ambiguity_penalty" not in reason_codes:
        reason_codes.append("resolution_ambiguity_penalty")
    if row.execution_cost > _ZERO and "execution_cost_penalty" not in reason_codes:
        reason_codes.append("execution_cost_penalty")
    if row.liquidity_risk_penalty > _ZERO and "liquidity_risk_penalty" not in reason_codes:
        reason_codes.append("liquidity_risk_penalty")
    if row.ev_status == "pass" and "contradiction_penalized_ev_pass" not in reason_codes:
        reason_codes.append("contradiction_penalized_ev_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _validate_report(report: StrategyCandidateContradictionPenalizedEvV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    expected_average = _average_edge(
        tuple(row.contradiction_penalized_ev for row in report.rows),
    )
    if report.average_contradiction_penalized_ev != expected_average:
        raise ValueError("average_contradiction_penalized_ev must match rows")
    expected_max_severity = max(
        (row.contradiction_severity for row in report.rows),
        default=_ZERO,
    )
    if report.max_contradiction_severity != expected_max_severity:
        raise ValueError("max_contradiction_severity must match rows")
    expected_max_execution_cost = max(
        (row.execution_cost for row in report.rows),
        default=_ZERO,
    )
    if report.max_execution_cost != expected_max_execution_cost:
        raise ValueError("max_execution_cost must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_edge_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _MINUS_ONE or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between minus one and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value.quantize(_COUNT_QUANT)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_public_identifier(field_name, reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must contain known reason codes")
    normalized = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )
    if len(normalized) != len(set(reason_codes)):
        raise ValueError(f"{field_name} must not contain duplicate reason codes")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANT)


def _average_edge(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _count(len(values)))


def _add(*values: Decimal) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _subtract(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left * right)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _row_payload(
    row: StrategyCandidateContradictionPenalizedEvV2Row,
    *,
    include_digest: bool,
) -> dict[str, object]:
    if type(row) is not StrategyCandidateContradictionPenalizedEvV2Row:
        raise ValueError("row must be StrategyCandidateContradictionPenalizedEvV2Row")
    payload = _dataclass_payload(row, include_digest=include_digest)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    return payload


def _report_payload(
    report: StrategyCandidateContradictionPenalizedEvV2Report,
    *,
    include_digest: bool,
) -> dict[str, object]:
    if type(report) is not StrategyCandidateContradictionPenalizedEvV2Report:
        raise ValueError("report must be StrategyCandidateContradictionPenalizedEvV2Report")
    payload = _dataclass_payload(report, include_digest=include_digest)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _dataclass_payload(value: object, *, include_digest: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, object] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            payload[field.name] = _json_ready(getattr(value, field.name))
        return payload
    return _json_ready(value)


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_payload(value, include_digest=True)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _row_digest(row: StrategyCandidateContradictionPenalizedEvV2Row) -> str:
    return _payload_digest(_row_payload(row, include_digest=False))


def _report_digest(report: StrategyCandidateContradictionPenalizedEvV2Report) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: dict[str, object]) -> str:
    _reject_unsafe_public_payload("derived validation digest payload", payload)
    _reject_json_numeric_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _copy_payload(value: dict[str, object]) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return {str(key): _copy_json_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("payload contains non-Decimal public numeric value")
    raise ValueError("payload contains unsupported value")


def _verify_payload_digests(payload: dict[str, object]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict payloads")
        supplied_row_digest = row.get("derived_validation_digest")
        _require_digest("derived_validation_digest", supplied_row_digest)
        expected_row_digest = _payload_digest(_without_digest(row))
        if supplied_row_digest != expected_row_digest:
            raise ValueError("derived_validation_digest mismatch")
    supplied_report_digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", supplied_report_digest)
    expected_report_digest = _payload_digest(_without_digest(payload))
    if supplied_report_digest != expected_report_digest:
        raise ValueError("derived_validation_digest mismatch")


def _without_digest(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def _reject_json_numeric_payload(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("payload contains non-Decimal public numeric value")
    if type(value) is dict:
        for item in value.values():
            _reject_json_numeric_payload(item)
    if type(value) is list:
        for item in value:
            _reject_json_numeric_payload(item)


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, field.name)
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} contains unsafe public payload")
            _reject_unsafe_public_payload(field_name, key)
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public payload")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION",
    "StrategyCandidateContradictionPenalizedEvV2Candidate",
    "StrategyCandidateContradictionPenalizedEvV2Config",
    "StrategyCandidateContradictionPenalizedEvV2Report",
    "StrategyCandidateContradictionPenalizedEvV2Row",
    "build_strategy_candidate_contradiction_penalized_ev_v2",
    "strategy_candidate_contradiction_penalized_ev_v2_payload",
)
