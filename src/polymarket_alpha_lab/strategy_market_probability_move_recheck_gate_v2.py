"""Pure in-memory Phase 1 market probability move recheck gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from typing import Any


DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION = (
    "strategy-market-probability-move-recheck-gate-v2"
)

GATE_STATUSES = ("clear", "watch", "recheck_required")
CLEAR_REASON_CODE = "probability_move_gate_clear"
EMPTY_REASON_CODE = "probability_move_gate_empty"
ROW_REASON_CODE_SEQUENCE = (
    "probability_move_velocity_above_recheck",
    "probability_move_velocity_above_watch",
    "probability_move_evidence_gap_above_recheck",
    "probability_move_evidence_gap_above_watch",
    "probability_move_official_update_below_recheck",
    "probability_move_official_update_below_watch",
    "probability_move_liquidity_movement_below_recheck",
    "probability_move_liquidity_movement_below_watch",
    "probability_move_specialist_confidence_below_recheck",
    "probability_move_specialist_confidence_below_watch",
    "probability_move_resolution_horizon_unjustified",
    "probability_move_resolution_horizon_watch",
    "probability_move_support_score_below_recheck",
    "probability_move_support_score_below_watch",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, CLEAR_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
RECHECK_REASON_CODES = frozenset(
    (
        "probability_move_velocity_above_recheck",
        "probability_move_evidence_gap_above_recheck",
        "probability_move_official_update_below_recheck",
        "probability_move_liquidity_movement_below_recheck",
        "probability_move_specialist_confidence_below_recheck",
        "probability_move_resolution_horizon_unjustified",
        "probability_move_support_score_below_recheck",
    ),
)

STATUS_RANK = {
    "recheck_required": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "clear": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIXTY = Decimal("60.000000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyMarketProbabilityMoveRecheckGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION
    )
    max_clear_probability_velocity_per_hour: Decimal = Decimal("0.060000")
    max_watch_probability_velocity_per_hour: Decimal = Decimal("0.120000")
    max_clear_evidence_gap_probability: Decimal = Decimal("0.030000")
    max_watch_evidence_gap_probability: Decimal = Decimal("0.070000")
    min_clear_official_source_update_score: Decimal = Decimal("0.700000")
    min_watch_official_source_update_score: Decimal = Decimal("0.400000")
    min_clear_liquidity_movement_score: Decimal = Decimal("0.700000")
    min_watch_liquidity_movement_score: Decimal = Decimal("0.400000")
    min_clear_specialist_confidence_score: Decimal = Decimal("0.750000")
    min_watch_specialist_confidence_score: Decimal = Decimal("0.500000")
    max_clear_resolution_horizon_hours: Decimal = Decimal("168.000000")
    max_watch_resolution_horizon_hours: Decimal = Decimal("720.000000")
    min_clear_support_score: Decimal = Decimal("0.700000")
    min_watch_support_score: Decimal = Decimal("0.450000")
    evidence_alignment_weight: Decimal = Decimal("0.250000")
    official_source_update_weight: Decimal = Decimal("0.200000")
    liquidity_movement_weight: Decimal = Decimal("0.200000")
    specialist_confidence_weight: Decimal = Decimal("0.200000")
    resolution_horizon_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityMoveRecheckGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityMoveRecheckGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_clear_probability_velocity_per_hour",
            "max_watch_probability_velocity_per_hour",
            "max_clear_resolution_horizon_hours",
            "max_watch_resolution_horizon_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_clear_evidence_gap_probability",
            "max_watch_evidence_gap_probability",
            "min_clear_official_source_update_score",
            "min_watch_official_source_update_score",
            "min_clear_liquidity_movement_score",
            "min_watch_liquidity_movement_score",
            "min_clear_specialist_confidence_score",
            "min_watch_specialist_confidence_score",
            "min_clear_support_score",
            "min_watch_support_score",
            "evidence_alignment_weight",
            "official_source_update_weight",
            "liquidity_movement_weight",
            "specialist_confidence_weight",
            "resolution_horizon_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityMoveRecheckGateV2Snapshot:
    market_slug: str
    condition_id: str
    observed_at: datetime
    previous_market_probability: Decimal
    current_market_probability: Decimal
    elapsed_minutes: Decimal
    evidence_probability_delta: Decimal
    official_source_update_score: Decimal
    liquidity_movement_score: Decimal
    specialist_confidence_score: Decimal
    resolution_horizon_hours: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityMoveRecheckGateV2Snapshot does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "previous_market_probability",
            "current_market_probability",
            "evidence_probability_delta",
            "official_source_update_score",
            "liquidity_movement_score",
            "specialist_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "elapsed_minutes",
            _normalize_positive_decimal("elapsed_minutes", self.elapsed_minutes),
        )
        object.__setattr__(
            self,
            "resolution_horizon_hours",
            _normalize_nonnegative_decimal(
                "resolution_horizon_hours",
                self.resolution_horizon_hours,
            ),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_ratio("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityMoveRecheckGateV2Row:
    market_slug: str
    condition_id: str
    observed_at: datetime
    previous_market_probability: Decimal
    current_market_probability: Decimal
    market_probability_delta: Decimal
    elapsed_minutes: Decimal
    probability_velocity_per_hour: Decimal
    evidence_probability_delta: Decimal
    evidence_alignment_score: Decimal
    evidence_gap_probability: Decimal
    official_source_update_score: Decimal
    liquidity_movement_score: Decimal
    specialist_confidence_score: Decimal
    resolution_horizon_hours: Decimal
    resolution_horizon_justification_score: Decimal
    support_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityMoveRecheckGateV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "previous_market_probability",
            "current_market_probability",
            "market_probability_delta",
            "probability_velocity_per_hour",
            "evidence_probability_delta",
            "evidence_alignment_score",
            "evidence_gap_probability",
            "official_source_update_score",
            "liquidity_movement_score",
            "specialist_confidence_score",
            "resolution_horizon_justification_score",
            "support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "elapsed_minutes",
            _normalize_positive_decimal("elapsed_minutes", self.elapsed_minutes),
        )
        object.__setattr__(
            self,
            "resolution_horizon_hours",
            _normalize_nonnegative_decimal(
                "resolution_horizon_hours",
                self.resolution_horizon_hours,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategyMarketProbabilityMoveRecheckGateV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    recheck_required_count: Decimal
    max_market_probability_delta: Decimal
    max_probability_velocity_per_hour: Decimal
    max_evidence_gap_probability: Decimal
    min_support_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityMoveRecheckGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityMoveRecheckGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "clear_count",
            "watch_count",
            "recheck_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_market_probability_delta",
            "max_probability_velocity_per_hour",
            "max_evidence_gap_probability",
            "min_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_market_probability_move_recheck_gate_v2_report(
    snapshots: list[StrategyMarketProbabilityMoveRecheckGateV2Snapshot]
    | tuple[StrategyMarketProbabilityMoveRecheckGateV2Snapshot, ...],
    *,
    config: StrategyMarketProbabilityMoveRecheckGateV2Config,
    generated_at: datetime,
) -> StrategyMarketProbabilityMoveRecheckGateV2Report:
    if type(config) is not StrategyMarketProbabilityMoveRecheckGateV2Config:
        raise ValueError(
            "config must be a StrategyMarketProbabilityMoveRecheckGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    _validate_unique_snapshots(normalized_snapshots)
    _validate_not_after_generated_at(normalized_snapshots, generated_at=generated_at_utc)

    rows = tuple(
        sorted(
            (_row_for_snapshot(snapshot, config=config) for snapshot in normalized_snapshots),
            key=_row_sort_key,
        ),
    )
    return StrategyMarketProbabilityMoveRecheckGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        recheck_required_count=_status_count(rows, "recheck_required"),
        max_market_probability_delta=max(
            (row.market_probability_delta for row in rows),
            default=ZERO,
        ),
        max_probability_velocity_per_hour=max(
            (row.probability_velocity_per_hour for row in rows),
            default=ZERO,
        ),
        max_evidence_gap_probability=max(
            (row.evidence_gap_probability for row in rows),
            default=ZERO,
        ),
        min_support_score=min((row.support_score for row in rows), default=ZERO),
        gate_status=_report_status(rows),
        recommended_next_step=_recommended_next_step(_report_status(rows)),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_market_probability_move_recheck_gate_v2_public_payload(
    report: StrategyMarketProbabilityMoveRecheckGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketProbabilityMoveRecheckGateV2Report:
        raise ValueError(
            "report must be a StrategyMarketProbabilityMoveRecheckGateV2Report",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_market_probability_move_recheck_gate_v2_public_payload(payload)
    return payload


def validate_strategy_market_probability_move_recheck_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy market probability move recheck payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_snapshot(
    snapshot: StrategyMarketProbabilityMoveRecheckGateV2Snapshot,
    *,
    config: StrategyMarketProbabilityMoveRecheckGateV2Config,
) -> StrategyMarketProbabilityMoveRecheckGateV2Row:
    market_probability_delta = abs(
        _subtract_decimal(
            snapshot.current_market_probability,
            snapshot.previous_market_probability,
        ),
    )
    probability_velocity_per_hour = _probability_velocity_per_hour(
        market_probability_delta,
        snapshot.elapsed_minutes,
    )
    evidence_gap_probability = max(
        _subtract_decimal(market_probability_delta, snapshot.evidence_probability_delta),
        ZERO,
    )
    evidence_alignment_score = _evidence_alignment_score(
        evidence_gap_probability,
        market_probability_delta,
    )
    resolution_horizon_justification_score = _resolution_horizon_justification_score(
        snapshot.resolution_horizon_hours,
        config,
    )
    support_score = _support_score(
        evidence_alignment_score=evidence_alignment_score,
        official_source_update_score=snapshot.official_source_update_score,
        liquidity_movement_score=snapshot.liquidity_movement_score,
        specialist_confidence_score=snapshot.specialist_confidence_score,
        resolution_horizon_justification_score=resolution_horizon_justification_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        probability_velocity_per_hour=probability_velocity_per_hour,
        evidence_gap_probability=evidence_gap_probability,
        official_source_update_score=snapshot.official_source_update_score,
        liquidity_movement_score=snapshot.liquidity_movement_score,
        specialist_confidence_score=snapshot.specialist_confidence_score,
        resolution_horizon_hours=snapshot.resolution_horizon_hours,
        support_score=support_score,
        config=config,
    )
    return StrategyMarketProbabilityMoveRecheckGateV2Row(
        market_slug=snapshot.market_slug,
        condition_id=snapshot.condition_id,
        observed_at=snapshot.observed_at,
        previous_market_probability=snapshot.previous_market_probability,
        current_market_probability=snapshot.current_market_probability,
        market_probability_delta=market_probability_delta,
        elapsed_minutes=snapshot.elapsed_minutes,
        probability_velocity_per_hour=probability_velocity_per_hour,
        evidence_probability_delta=snapshot.evidence_probability_delta,
        evidence_alignment_score=evidence_alignment_score,
        evidence_gap_probability=evidence_gap_probability,
        official_source_update_score=snapshot.official_source_update_score,
        liquidity_movement_score=snapshot.liquidity_movement_score,
        specialist_confidence_score=snapshot.specialist_confidence_score,
        resolution_horizon_hours=snapshot.resolution_horizon_hours,
        resolution_horizon_justification_score=resolution_horizon_justification_score,
        support_score=support_score,
        gate_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        source_config_version=snapshot.source_config_version,
    )


def _row_reason_codes(
    *,
    probability_velocity_per_hour: Decimal,
    evidence_gap_probability: Decimal,
    official_source_update_score: Decimal,
    liquidity_movement_score: Decimal,
    specialist_confidence_score: Decimal,
    resolution_horizon_hours: Decimal,
    support_score: Decimal,
    config: StrategyMarketProbabilityMoveRecheckGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if probability_velocity_per_hour > config.max_watch_probability_velocity_per_hour:
        reason_codes.append("probability_move_velocity_above_recheck")
    elif probability_velocity_per_hour > config.max_clear_probability_velocity_per_hour:
        reason_codes.append("probability_move_velocity_above_watch")
    if evidence_gap_probability > config.max_watch_evidence_gap_probability:
        reason_codes.append("probability_move_evidence_gap_above_recheck")
    elif evidence_gap_probability > config.max_clear_evidence_gap_probability:
        reason_codes.append("probability_move_evidence_gap_above_watch")
    if official_source_update_score < config.min_watch_official_source_update_score:
        reason_codes.append("probability_move_official_update_below_recheck")
    elif official_source_update_score < config.min_clear_official_source_update_score:
        reason_codes.append("probability_move_official_update_below_watch")
    if liquidity_movement_score < config.min_watch_liquidity_movement_score:
        reason_codes.append("probability_move_liquidity_movement_below_recheck")
    elif liquidity_movement_score < config.min_clear_liquidity_movement_score:
        reason_codes.append("probability_move_liquidity_movement_below_watch")
    if specialist_confidence_score < config.min_watch_specialist_confidence_score:
        reason_codes.append("probability_move_specialist_confidence_below_recheck")
    elif specialist_confidence_score < config.min_clear_specialist_confidence_score:
        reason_codes.append("probability_move_specialist_confidence_below_watch")
    if resolution_horizon_hours > config.max_watch_resolution_horizon_hours:
        reason_codes.append("probability_move_resolution_horizon_unjustified")
    elif resolution_horizon_hours > config.max_clear_resolution_horizon_hours:
        reason_codes.append("probability_move_resolution_horizon_watch")
    if support_score < config.min_watch_support_score:
        reason_codes.append("probability_move_support_score_below_recheck")
    elif support_score < config.min_clear_support_score:
        reason_codes.append("probability_move_support_score_below_watch")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in RECHECK_REASON_CODES for reason_code in reason_codes):
        return "recheck_required"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "clear"
    return "watch"


def _report_status(rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...]) -> str:
    statuses = tuple(row.gate_status for row in rows)
    if "recheck_required" in statuses:
        return "recheck_required"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "recheck_required":
        return "force_report_only_probability_move_recheck"
    if gate_status == "watch":
        return "review_report_only_probability_move_recheck"
    return "continue_report_only_probability_move_recheck"


def _report_reason_codes(
    rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    )
    if not present:
        return (CLEAR_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in present)


def _reason_code_counts(
    rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...],
) -> tuple[StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount, ...]:
    market_count = _count(len(rows))
    return tuple(
        StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            market_ratio=_ratio(_reason_count(rows, reason_code), market_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_snapshots(
    value: object,
) -> tuple[StrategyMarketProbabilityMoveRecheckGateV2Snapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    for item in snapshots:
        if type(item) is not StrategyMarketProbabilityMoveRecheckGateV2Snapshot:
            raise ValueError(
                "snapshots must contain StrategyMarketProbabilityMoveRecheckGateV2Snapshot "
                "values",
            )
        _require_hard_flags("snapshot", item)
    return snapshots


def _normalize_rows(
    value: object,
) -> tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyMarketProbabilityMoveRecheckGateV2Row:
            raise ValueError(
                "rows must contain StrategyMarketProbabilityMoveRecheckGateV2Row values",
            )
        _require_hard_flags("row", row)
        key = _market_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market probability snapshot")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODE_SEQUENCE
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: StrategyMarketProbabilityMoveRecheckGateV2Config) -> None:
    _require_less_or_equal(
        "max_clear_probability_velocity_per_hour",
        config.max_clear_probability_velocity_per_hour,
        config.max_watch_probability_velocity_per_hour,
    )
    _require_less_or_equal(
        "max_clear_evidence_gap_probability",
        config.max_clear_evidence_gap_probability,
        config.max_watch_evidence_gap_probability,
    )
    _require_less_or_equal(
        "min_watch_official_source_update_score",
        config.min_watch_official_source_update_score,
        config.min_clear_official_source_update_score,
    )
    _require_less_or_equal(
        "min_watch_liquidity_movement_score",
        config.min_watch_liquidity_movement_score,
        config.min_clear_liquidity_movement_score,
    )
    _require_less_or_equal(
        "min_watch_specialist_confidence_score",
        config.min_watch_specialist_confidence_score,
        config.min_clear_specialist_confidence_score,
    )
    _require_less_or_equal(
        "max_clear_resolution_horizon_hours",
        config.max_clear_resolution_horizon_hours,
        config.max_watch_resolution_horizon_hours,
    )
    _require_less_or_equal(
        "min_watch_support_score",
        config.min_watch_support_score,
        config.min_clear_support_score,
    )
    support_weight_sum = _add_decimal(
        config.evidence_alignment_weight,
        config.official_source_update_weight,
        config.liquidity_movement_weight,
        config.specialist_confidence_weight,
        config.resolution_horizon_weight,
    )
    if support_weight_sum != ONE:
        raise ValueError("support weights must sum to 1.000000")


def _validate_unique_snapshots(
    snapshots: tuple[StrategyMarketProbabilityMoveRecheckGateV2Snapshot, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for snapshot in snapshots:
        key = _market_key(snapshot)
        if key in seen:
            raise ValueError("snapshots contain duplicate market probability snapshot")
        seen.add(key)


def _validate_not_after_generated_at(
    snapshots: tuple[StrategyMarketProbabilityMoveRecheckGateV2Snapshot, ...],
    *,
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _validate_row(row: StrategyMarketProbabilityMoveRecheckGateV2Row) -> None:
    expected_delta = abs(
        _subtract_decimal(row.current_market_probability, row.previous_market_probability),
    )
    if row.market_probability_delta != expected_delta:
        raise ValueError("market_probability_delta must match market probabilities")
    if row.probability_velocity_per_hour != _probability_velocity_per_hour(
        row.market_probability_delta,
        row.elapsed_minutes,
    ):
        raise ValueError("probability_velocity_per_hour must match probability movement")
    expected_gap = max(
        _subtract_decimal(row.market_probability_delta, row.evidence_probability_delta),
        ZERO,
    )
    if row.evidence_gap_probability != expected_gap:
        raise ValueError("evidence_gap_probability must match market move and evidence")
    if row.evidence_alignment_score != _evidence_alignment_score(
        row.evidence_gap_probability,
        row.market_probability_delta,
    ):
        raise ValueError("evidence_alignment_score must match evidence gap")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyMarketProbabilityMoveRecheckGateV2Report) -> None:
    rows = report.rows
    market_count = _count(len(rows))
    if report.market_count != market_count:
        raise ValueError("market_count must match rows")
    for field_name, status in (
        ("clear_count", "clear"),
        ("watch_count", "watch"),
        ("recheck_required_count", "recheck_required"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.clear_count + report.watch_count + report.recheck_required_count != market_count:
        raise ValueError("status counts must match market_count")
    if report.max_market_probability_delta != max(
        (row.market_probability_delta for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_market_probability_delta must match rows")
    if report.max_probability_velocity_per_hour != max(
        (row.probability_velocity_per_hour for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_velocity_per_hour must match rows")
    if report.max_evidence_gap_probability != max(
        (row.evidence_gap_probability for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_gap_probability must match rows")
    if report.min_support_score != min((row.support_score for row in rows), default=ZERO):
        raise ValueError("min_support_score must match rows")
    for row in rows:
        _validate_row(row)
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _market_key(
    value: StrategyMarketProbabilityMoveRecheckGateV2Snapshot
    | StrategyMarketProbabilityMoveRecheckGateV2Row,
) -> tuple[str, str]:
    return (value.market_slug, value.condition_id)


def _row_sort_key(
    row: StrategyMarketProbabilityMoveRecheckGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.gate_status],
        row.support_score,
        -row.probability_velocity_per_hour,
        row.market_slug,
        row.condition_id,
    )


def _status_count(
    rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _reason_count(
    rows: tuple[StrategyMarketProbabilityMoveRecheckGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _probability_velocity_per_hour(
    probability_delta: Decimal,
    elapsed_minutes: Decimal,
) -> Decimal:
    return _ratio(_multiply_decimal(probability_delta, SIXTY), elapsed_minutes)


def _evidence_alignment_score(
    evidence_gap_probability: Decimal,
    market_probability_delta: Decimal,
) -> Decimal:
    if market_probability_delta == ZERO:
        return ONE
    return max(ONE - _ratio(evidence_gap_probability, market_probability_delta), ZERO)


def _resolution_horizon_justification_score(
    resolution_horizon_hours: Decimal,
    config: StrategyMarketProbabilityMoveRecheckGateV2Config,
) -> Decimal:
    if resolution_horizon_hours <= config.max_clear_resolution_horizon_hours:
        return ONE
    if resolution_horizon_hours >= config.max_watch_resolution_horizon_hours:
        return ZERO
    horizon_window = _subtract_decimal(
        config.max_watch_resolution_horizon_hours,
        config.max_clear_resolution_horizon_hours,
    )
    excess_horizon = _subtract_decimal(
        resolution_horizon_hours,
        config.max_clear_resolution_horizon_hours,
    )
    return max(ONE - _ratio(excess_horizon, horizon_window), ZERO)


def _support_score(
    *,
    evidence_alignment_score: Decimal,
    official_source_update_score: Decimal,
    liquidity_movement_score: Decimal,
    specialist_confidence_score: Decimal,
    resolution_horizon_justification_score: Decimal,
    config: StrategyMarketProbabilityMoveRecheckGateV2Config,
) -> Decimal:
    return _add_decimal(
        _multiply_decimal(evidence_alignment_score, config.evidence_alignment_weight),
        _multiply_decimal(
            official_source_update_score,
            config.official_source_update_weight,
        ),
        _multiply_decimal(liquidity_movement_score, config.liquidity_movement_weight),
        _multiply_decimal(
            specialist_confidence_score,
            config.specialist_confidence_weight,
        ),
        _multiply_decimal(
            resolution_horizon_justification_score,
            config.resolution_horizon_weight,
        ),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_count(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return normalized


def _require_public_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_less_or_equal(field_name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _row_derived_validation_digest(
    row: StrategyMarketProbabilityMoveRecheckGateV2Row,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: StrategyMarketProbabilityMoveRecheckGateV2Report,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: StrategyMarketProbabilityMoveRecheckGateV2Row,
) -> dict[str, Any]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: StrategyMarketProbabilityMoveRecheckGateV2Report,
) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_public_numeric_values(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError("public payload must use Decimal strings, not numeric values")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_STRATEGY_MARKET_PROBABILITY_MOVE_RECHECK_GATE_V2_CONFIG_VERSION",
    "StrategyMarketProbabilityMoveRecheckGateV2Config",
    "StrategyMarketProbabilityMoveRecheckGateV2ReasonCodeCount",
    "StrategyMarketProbabilityMoveRecheckGateV2Report",
    "StrategyMarketProbabilityMoveRecheckGateV2Row",
    "StrategyMarketProbabilityMoveRecheckGateV2Snapshot",
    "build_strategy_market_probability_move_recheck_gate_v2_report",
    "strategy_market_probability_move_recheck_gate_v2_public_payload",
    "validate_strategy_market_probability_move_recheck_gate_v2_public_payload",
)
