"""Readonly Decimal strategy report blending specialist team signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_SPECIALIST_SIGNAL_CONFIDENCE_BLENDER_V2_CONFIG_VERSION = (
    "strategy-specialist-signal-confidence-blender-v2"
)

SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
PASS_NEXT_STEP = "allow_report_only_signal_confidence_review"
WATCH_NEXT_STEP = "monitor_report_only_signal_confidence_review"
BLOCKED_NEXT_STEP = "block_report_only_signal_confidence_review"

ROW_REASON_CODES = (
    "signal_confidence_row_pass",
    "signal_confidence_row_watch",
    "signal_confidence_row_blocked",
    "team_calibration_strong",
    "team_calibration_watch",
    "team_calibration_weak",
    "source_quality_strong",
    "source_quality_watch",
    "source_quality_weak",
    "evidence_fresh",
    "evidence_stale_watch",
    "evidence_stale_blocked",
    "conflict_severity_low",
    "conflict_severity_watch",
    "conflict_severity_high",
    "liquidity_exit_risk_low",
    "liquidity_exit_risk_watch",
    "liquidity_exit_risk_high",
    "resolution_rule_clear",
    "resolution_rule_watch",
    "resolution_rule_unclear",
)
REPORT_REASON_CODES = (
    "signal_confidence_recommendation_passed",
    "signal_confidence_watch_rows_present",
    "signal_confidence_blocked_rows_present",
    "signal_confidence_adjusted_probability_below_watch",
    "signal_confidence_adjusted_probability_watch",
    "signal_confidence_high_conflict_present",
    "signal_confidence_exit_risk_present",
    "signal_confidence_resolution_unclear",
    "signal_confidence_no_specialist_signals",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mut" + "ation",
    "b" + "uy",
    "se" + "ll",
    "tra" + "de",
)

REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "market_slug",
    "outcome_name",
    "signal_count",
    "pass_signal_count",
    "watch_signal_count",
    "blocked_signal_count",
    "blended_signal_probability",
    "average_specialist_confidence_score",
    "confidence_adjusted_probability",
    "max_conflict_severity_score",
    "max_liquidity_exit_risk_score",
    "min_resolution_rule_clarity_score",
    "recommendation_status",
    "recommended_next_step",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ROW_PAYLOAD_FIELDS = (
    "rank",
    "team_id",
    "market_slug",
    "outcome_name",
    "signal_probability",
    "team_calibration_score",
    "source_quality_score",
    "evidence_age_seconds",
    "evidence_freshness_score",
    "conflict_severity_score",
    "liquidity_exit_risk_score",
    "resolution_rule_clarity_score",
    "specialist_confidence_score",
    "confidence_weighted_signal",
    "row_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_STRATEGY_SPECIALIST_SIGNAL_CONFIDENCE_BLENDER_V2_CONFIG_VERSION",
    "StrategySpecialistSignalConfidenceBlenderV2Config",
    "StrategySpecialistSignalConfidenceBlenderV2Input",
    "StrategySpecialistSignalConfidenceBlenderV2Row",
    "StrategySpecialistSignalConfidenceBlenderV2Report",
    "build_strategy_specialist_signal_confidence_blender_v2",
    "strategy_specialist_signal_confidence_blender_v2_payload",
)


@dataclass(frozen=True)
class StrategySpecialistSignalConfidenceBlenderV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_SPECIALIST_SIGNAL_CONFIDENCE_BLENDER_V2_CONFIG_VERSION
    )
    team_calibration_weight: Decimal = Decimal("0.250000")
    source_quality_weight: Decimal = Decimal("0.200000")
    evidence_freshness_weight: Decimal = Decimal("0.171154")
    conflict_severity_weight: Decimal = Decimal("0.229808")
    liquidity_exit_risk_weight: Decimal = Decimal("0.072115")
    resolution_rule_clarity_weight: Decimal = Decimal("0.076923")
    max_evidence_age_seconds: Decimal = Decimal("86400.000000")
    pass_confidence_floor: Decimal = Decimal("0.850000")
    watch_confidence_floor: Decimal = Decimal("0.550000")
    min_confidence_adjusted_probability: Decimal = Decimal("0.550000")
    watch_confidence_adjusted_probability: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategySpecialistSignalConfidenceBlenderV2Config:
            raise TypeError(
                "StrategySpecialistSignalConfidenceBlenderV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategySpecialistSignalConfidenceBlenderV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategySpecialistSignalConfidenceBlenderV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "team_calibration_weight",
            "source_quality_weight",
            "evidence_freshness_weight",
            "conflict_severity_weight",
            "liquidity_exit_risk_weight",
            "resolution_rule_clarity_weight",
            "pass_confidence_floor",
            "watch_confidence_floor",
            "min_confidence_adjusted_probability",
            "watch_confidence_adjusted_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class StrategySpecialistSignalConfidenceBlenderV2Input:
    team_id: str
    market_slug: str
    outcome_name: str
    signal_probability: Decimal
    team_calibration_score: Decimal
    source_quality_score: Decimal
    evidence_age_seconds: Decimal
    conflict_severity_score: Decimal
    liquidity_exit_risk_score: Decimal
    resolution_rule_clarity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategySpecialistSignalConfidenceBlenderV2Input:
            raise TypeError(
                "StrategySpecialistSignalConfidenceBlenderV2Input "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategySpecialistSignalConfidenceBlenderV2Input:
            raise ValueError(
                "signal must be exactly StrategySpecialistSignalConfidenceBlenderV2Input",
            )
        for field_name in ("team_id", "market_slug", "outcome_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_probability",
            "team_calibration_score",
            "source_quality_score",
            "conflict_severity_score",
            "liquidity_exit_risk_score",
            "resolution_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=None,
            ),
        )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", _payload_value(asdict(self)))


@dataclass(frozen=True)
class StrategySpecialistSignalConfidenceBlenderV2Row:
    rank: Decimal
    team_id: str
    market_slug: str
    outcome_name: str
    signal_probability: Decimal
    team_calibration_score: Decimal
    source_quality_score: Decimal
    evidence_age_seconds: Decimal
    evidence_freshness_score: Decimal
    conflict_severity_score: Decimal
    liquidity_exit_risk_score: Decimal
    resolution_rule_clarity_score: Decimal
    specialist_confidence_score: Decimal
    confidence_weighted_signal: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategySpecialistSignalConfidenceBlenderV2Row:
            raise TypeError(
                "StrategySpecialistSignalConfidenceBlenderV2Row "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategySpecialistSignalConfidenceBlenderV2Row:
            raise ValueError(
                "row must be exactly StrategySpecialistSignalConfidenceBlenderV2Row",
            )
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("team_id", "market_slug", "outcome_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_probability",
            "team_calibration_score",
            "source_quality_score",
            "evidence_freshness_score",
            "conflict_severity_score",
            "liquidity_exit_risk_score",
            "resolution_rule_clarity_score",
            "specialist_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_seconds", "confidence_weighted_signal"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=None,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))


@dataclass(frozen=True)
class StrategySpecialistSignalConfidenceBlenderV2Report:
    generated_at: datetime
    config_version: str
    market_slug: str
    outcome_name: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    blended_signal_probability: Decimal
    average_specialist_confidence_score: Decimal
    confidence_adjusted_probability: Decimal
    max_conflict_severity_score: Decimal
    max_liquidity_exit_risk_score: Decimal
    min_resolution_rule_clarity_score: Decimal
    recommendation_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategySpecialistSignalConfidenceBlenderV2Report:
            raise TypeError(
                "StrategySpecialistSignalConfidenceBlenderV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategySpecialistSignalConfidenceBlenderV2Report:
            raise ValueError(
                "report must be exactly StrategySpecialistSignalConfidenceBlenderV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "market_slug", "outcome_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "blended_signal_probability",
            "average_specialist_confidence_score",
            "confidence_adjusted_probability",
            "max_conflict_severity_score",
            "max_liquidity_exit_risk_score",
            "min_resolution_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("recommendation_status", self.recommendation_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_non_empty_string("recommended_next_step", self.recommended_next_step),
        )
        if self.recommended_next_step not in (
            PASS_NEXT_STEP,
            WATCH_NEXT_STEP,
            BLOCKED_NEXT_STEP,
        ):
            raise ValueError("recommended_next_step must be a known report-only action")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            )
        _validate_report_consistency(self)


def build_strategy_specialist_signal_confidence_blender_v2(
    signals: object,
    *,
    config: StrategySpecialistSignalConfidenceBlenderV2Config | None = None,
    generated_at: datetime,
) -> StrategySpecialistSignalConfidenceBlenderV2Report:
    if config is None:
        config = StrategySpecialistSignalConfidenceBlenderV2Config()
    if type(config) is not StrategySpecialistSignalConfidenceBlenderV2Config:
        raise ValueError(
            "config must be a StrategySpecialistSignalConfidenceBlenderV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    market_slug, outcome_name = _report_market_and_outcome(normalized_signals)
    rows = _ranked_rows(normalized_signals, config)
    status = _report_status(rows, config)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "market_slug": market_slug,
        "outcome_name": outcome_name,
        "signal_count": _count_decimal(len(rows)),
        "pass_signal_count": _status_count(rows, "pass"),
        "watch_signal_count": _status_count(rows, "watch"),
        "blocked_signal_count": _status_count(rows, "blocked"),
        "blended_signal_probability": _blended_signal_probability(rows),
        "average_specialist_confidence_score": _average_confidence(rows),
        "confidence_adjusted_probability": ZERO,
        "max_conflict_severity_score": _max_conflict(rows),
        "max_liquidity_exit_risk_score": _max_liquidity_risk(rows),
        "min_resolution_rule_clarity_score": _min_resolution_clarity(rows),
        "recommendation_status": status,
        "recommended_next_step": _recommended_next_step(status),
        "reason_codes": _report_reason_codes(rows, status, config),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["confidence_adjusted_probability"] = _confidence_adjusted_probability(
        values["blended_signal_probability"],
        values["average_specialist_confidence_score"],
    )
    return StrategySpecialistSignalConfidenceBlenderV2Report(**values)


def strategy_specialist_signal_confidence_blender_v2_payload(
    report: StrategySpecialistSignalConfidenceBlenderV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategySpecialistSignalConfidenceBlenderV2Report:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a StrategySpecialistSignalConfidenceBlenderV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_scalars("payload", payload)
    _validate_public_payload(payload)
    return payload


def _ranked_rows(
    signals: tuple[StrategySpecialistSignalConfidenceBlenderV2Input, ...],
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...]:
    base_rows = tuple(_row_for_signal(signal, config) for signal in signals)
    ordered = tuple(sorted(base_rows, key=_row_sort_key))
    ranked_rows = tuple(
        _replace_row_rank(row, Decimal(index).quantize(COUNT_QUANT))
        for index, row in enumerate(ordered, start=1)
    )
    return ranked_rows


def _row_for_signal(
    signal: StrategySpecialistSignalConfidenceBlenderV2Input,
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> StrategySpecialistSignalConfidenceBlenderV2Row:
    freshness_score = _evidence_freshness_score(signal.evidence_age_seconds, config)
    confidence_score = _specialist_confidence_score(
        signal=signal,
        evidence_freshness_score=freshness_score,
        config=config,
    )
    row_status = _row_status(confidence_score, config)
    return StrategySpecialistSignalConfidenceBlenderV2Row(
        rank=ONE,
        team_id=signal.team_id,
        market_slug=signal.market_slug,
        outcome_name=signal.outcome_name,
        signal_probability=signal.signal_probability,
        team_calibration_score=signal.team_calibration_score,
        source_quality_score=signal.source_quality_score,
        evidence_age_seconds=signal.evidence_age_seconds,
        evidence_freshness_score=freshness_score,
        conflict_severity_score=signal.conflict_severity_score,
        liquidity_exit_risk_score=signal.liquidity_exit_risk_score,
        resolution_rule_clarity_score=signal.resolution_rule_clarity_score,
        specialist_confidence_score=confidence_score,
        confidence_weighted_signal=_confidence_weighted_signal(
            signal.signal_probability,
            confidence_score,
        ),
        row_status=row_status,
        reason_codes=_row_reason_codes(signal, freshness_score, row_status),
    )


def _replace_row_rank(
    row: StrategySpecialistSignalConfidenceBlenderV2Row,
    rank: Decimal,
) -> StrategySpecialistSignalConfidenceBlenderV2Row:
    return StrategySpecialistSignalConfidenceBlenderV2Row(
        rank=rank,
        team_id=row.team_id,
        market_slug=row.market_slug,
        outcome_name=row.outcome_name,
        signal_probability=row.signal_probability,
        team_calibration_score=row.team_calibration_score,
        source_quality_score=row.source_quality_score,
        evidence_age_seconds=row.evidence_age_seconds,
        evidence_freshness_score=row.evidence_freshness_score,
        conflict_severity_score=row.conflict_severity_score,
        liquidity_exit_risk_score=row.liquidity_exit_risk_score,
        resolution_rule_clarity_score=row.resolution_rule_clarity_score,
        specialist_confidence_score=row.specialist_confidence_score,
        confidence_weighted_signal=row.confidence_weighted_signal,
        row_status=row.row_status,
        reason_codes=row.reason_codes,
    )


def _specialist_confidence_score(
    *,
    signal: StrategySpecialistSignalConfidenceBlenderV2Input,
    evidence_freshness_score: Decimal,
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            signal.team_calibration_score * config.team_calibration_weight
            + signal.source_quality_score * config.source_quality_weight
            + evidence_freshness_score * config.evidence_freshness_weight
            + (ONE - signal.conflict_severity_score) * config.conflict_severity_weight
            + (ONE - signal.liquidity_exit_risk_score)
            * config.liquidity_exit_risk_weight
            + signal.resolution_rule_clarity_score
            * config.resolution_rule_clarity_weight
        )
    return _clamp_ratio(score)


def _evidence_freshness_score(
    evidence_age_seconds: Decimal,
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        full_credit_seconds = config.max_evidence_age_seconds / Decimal("24")
        decay_seconds = config.max_evidence_age_seconds * Decimal("5") / Decimal("6")
        if evidence_age_seconds <= full_credit_seconds:
            return ONE
        return _clamp_ratio(ONE - evidence_age_seconds / decay_seconds)


def _row_status(
    confidence_score: Decimal,
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> str:
    if confidence_score >= config.pass_confidence_floor:
        return "pass"
    if confidence_score >= config.watch_confidence_floor:
        return "watch"
    return "blocked"


def _row_reason_codes(
    signal: StrategySpecialistSignalConfidenceBlenderV2Input,
    evidence_freshness_score: Decimal,
    row_status: str,
) -> tuple[str, ...]:
    reasons = [
        f"signal_confidence_row_{row_status}",
        _tier_reason(
            signal.team_calibration_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="team_calibration_strong",
            watch_reason="team_calibration_watch",
            weak_reason="team_calibration_weak",
        ),
        _tier_reason(
            signal.source_quality_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.500000"),
            strong_reason="source_quality_strong",
            watch_reason="source_quality_watch",
            weak_reason="source_quality_weak",
        ),
        _freshness_reason(evidence_freshness_score),
        _risk_reason(
            signal.conflict_severity_score,
            low=Decimal("0.250000"),
            high=Decimal("0.700000"),
            low_reason="conflict_severity_low",
            watch_reason="conflict_severity_watch",
            high_reason="conflict_severity_high",
        ),
        _risk_reason(
            signal.liquidity_exit_risk_score,
            low=Decimal("0.300000"),
            high=Decimal("0.750000"),
            low_reason="liquidity_exit_risk_low",
            watch_reason="liquidity_exit_risk_watch",
            high_reason="liquidity_exit_risk_high",
        ),
        _tier_reason(
            signal.resolution_rule_clarity_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="resolution_rule_clear",
            watch_reason="resolution_rule_watch",
            weak_reason="resolution_rule_unclear",
        ),
        *signal.reason_codes,
    ]
    return tuple(dict.fromkeys(reasons))


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _risk_reason(
    value: Decimal,
    *,
    low: Decimal,
    high: Decimal,
    low_reason: str,
    watch_reason: str,
    high_reason: str,
) -> str:
    if value <= low:
        return low_reason
    if value < high:
        return watch_reason
    return high_reason


def _freshness_reason(value: Decimal) -> str:
    if value >= Decimal("0.750000"):
        return "evidence_fresh"
    if value >= Decimal("0.250000"):
        return "evidence_stale_watch"
    return "evidence_stale_blocked"


def _report_status(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    adjusted = _confidence_adjusted_probability(
        _blended_signal_probability(rows),
        _average_confidence(rows),
    )
    if adjusted >= config.min_confidence_adjusted_probability:
        return "pass"
    if adjusted >= config.watch_confidence_adjusted_probability:
        return "watch"
    return "blocked"


def _report_reason_codes(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
    status: str,
    config: StrategySpecialistSignalConfidenceBlenderV2Config,
) -> tuple[str, ...]:
    if not rows:
        return ("signal_confidence_no_specialist_signals",)
    reasons: list[str] = []
    if any(row.row_status == "blocked" for row in rows):
        reasons.append("signal_confidence_blocked_rows_present")
    elif any(row.row_status == "watch" for row in rows):
        reasons.append("signal_confidence_watch_rows_present")
    adjusted = _confidence_adjusted_probability(
        _blended_signal_probability(rows),
        _average_confidence(rows),
    )
    if adjusted < config.watch_confidence_adjusted_probability:
        reasons.append("signal_confidence_adjusted_probability_below_watch")
    elif adjusted < config.min_confidence_adjusted_probability:
        reasons.append("signal_confidence_adjusted_probability_watch")
    if _max_conflict(rows) >= Decimal("0.700000"):
        reasons.append("signal_confidence_high_conflict_present")
    if _max_liquidity_risk(rows) >= Decimal("0.750000"):
        reasons.append("signal_confidence_exit_risk_present")
    if _min_resolution_clarity(rows) < Decimal("0.500000"):
        reasons.append("signal_confidence_resolution_unclear")
    if not reasons and status == "pass":
        reasons.append("signal_confidence_recommendation_passed")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reasons)


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return PASS_NEXT_STEP
    if status == "watch":
        return WATCH_NEXT_STEP
    return BLOCKED_NEXT_STEP


def _confidence_weighted_signal(
    signal_probability: Decimal,
    confidence_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(signal_probability * confidence_score)


def _blended_signal_probability(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> Decimal:
    confidence_total = sum((row.specialist_confidence_score for row in rows), ZERO)
    if confidence_total == ZERO:
        return ZERO
    weighted_total = sum((row.confidence_weighted_signal for row in rows), ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(weighted_total / confidence_total)


def _average_confidence(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.specialist_confidence_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _confidence_adjusted_probability(
    blended_signal_probability: Decimal,
    average_specialist_confidence_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            blended_signal_probability * average_specialist_confidence_score,
        )


def _max_conflict(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> Decimal:
    return max((row.conflict_severity_score for row in rows), default=ZERO)


def _max_liquidity_risk(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> Decimal:
    return max((row.liquidity_exit_risk_score for row in rows), default=ZERO)


def _min_resolution_clarity(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> Decimal:
    return min((row.resolution_rule_clarity_score for row in rows), default=ZERO)


def _status_count(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _row_sort_key(
    row: StrategySpecialistSignalConfidenceBlenderV2Row,
) -> tuple[Decimal, str, str]:
    return (-row.specialist_confidence_score, row.team_id, row.market_slug)


def _report_market_and_outcome(
    signals: tuple[StrategySpecialistSignalConfidenceBlenderV2Input, ...],
) -> tuple[str, str]:
    if not signals:
        return "unassigned", "unassigned"
    market_slugs = {signal.market_slug for signal in signals}
    outcome_names = {signal.outcome_name for signal in signals}
    if len(market_slugs) != 1 or len(outcome_names) != 1:
        raise ValueError("signals must share the same market_slug and outcome_name")
    return signals[0].market_slug, signals[0].outcome_name


def _normalize_signals(
    value: object,
) -> tuple[StrategySpecialistSignalConfidenceBlenderV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("signals must be an iterable")
    signals = tuple(value)
    seen_team_ids: set[str] = set()
    for signal in signals:
        if type(signal) is not StrategySpecialistSignalConfidenceBlenderV2Input:
            raise ValueError(
                "signal items must be StrategySpecialistSignalConfidenceBlenderV2Input",
            )
        _require_hard_flags("signal", signal)
        if signal.team_id in seen_team_ids:
            raise ValueError("signals must not contain duplicate team_id values")
        seen_team_ids.add(signal.team_id)
    return signals


def _normalize_rows(value: object) -> tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen_team_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategySpecialistSignalConfidenceBlenderV2Row:
            raise ValueError(
                "rows must contain StrategySpecialistSignalConfidenceBlenderV2Row",
            )
        _require_hard_flags("row", row)
        if row.team_id in seen_team_ids:
            raise ValueError("rows must not contain duplicate team_id values")
        seen_team_ids.add(row.team_id)
    return rows


def _validate_config(config: StrategySpecialistSignalConfidenceBlenderV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.team_calibration_weight
            + config.source_quality_weight
            + config.evidence_freshness_weight
            + config.conflict_severity_weight
            + config.liquidity_exit_risk_weight
            + config.resolution_rule_clarity_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("weights must sum to 1.000000")
    if config.watch_confidence_floor > config.pass_confidence_floor:
        raise ValueError("watch_confidence_floor must not exceed pass_confidence_floor")
    if (
        config.watch_confidence_adjusted_probability
        > config.min_confidence_adjusted_probability
    ):
        raise ValueError(
            "watch_confidence_adjusted_probability must not exceed "
            "min_confidence_adjusted_probability",
        )


def _validate_row_consistency(
    row: StrategySpecialistSignalConfidenceBlenderV2Row,
) -> None:
    if row.confidence_weighted_signal != _confidence_weighted_signal(
        row.signal_probability,
        row.specialist_confidence_score,
    ):
        raise ValueError("confidence_weighted_signal must match row fields")
    if row.reason_codes[0] != f"signal_confidence_row_{row.row_status}":
        raise ValueError("reason_codes must start with row_status reason")


def _validate_report_consistency(
    report: StrategySpecialistSignalConfidenceBlenderV2Report,
) -> None:
    rows = report.rows
    if report.signal_count != _count_decimal(len(rows)):
        raise ValueError("signal_count must match rows")
    if (
        report.pass_signal_count != _status_count(rows, "pass")
        or report.watch_signal_count != _status_count(rows, "watch")
        or report.blocked_signal_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_signal_count
        + report.watch_signal_count
        + report.blocked_signal_count
        != report.signal_count
    ):
        raise ValueError("status counts must sum to signal_count")
    _validate_rows_sorted(rows)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    if report.blended_signal_probability != _blended_signal_probability(rows):
        raise ValueError("blended_signal_probability must match rows")
    if report.average_specialist_confidence_score != _average_confidence(rows):
        raise ValueError("average_specialist_confidence_score must match rows")
    if report.confidence_adjusted_probability != _confidence_adjusted_probability(
        report.blended_signal_probability,
        report.average_specialist_confidence_score,
    ):
        raise ValueError("confidence_adjusted_probability must match report fields")
    if report.max_conflict_severity_score != _max_conflict(rows):
        raise ValueError("max_conflict_severity_score must match rows")
    if report.max_liquidity_exit_risk_score != _max_liquidity_risk(rows):
        raise ValueError("max_liquidity_exit_risk_score must match rows")
    if report.min_resolution_rule_clarity_score != _min_resolution_clarity(rows):
        raise ValueError("min_resolution_rule_clarity_score must match rows")


def _validate_rows_sorted(
    rows: tuple[StrategySpecialistSignalConfidenceBlenderV2Row, ...],
) -> None:
    expected_rows = tuple(sorted(rows, key=_row_sort_key))
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected_rows or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by confidence and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        expected = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if allowed is not None and any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_decimal(field_name, normalized)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, _require_decimal(field_name, value))
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(SCORE_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {field_name}")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _report_derived_validation_digest(
    report: StrategySpecialistSignalConfidenceBlenderV2Report,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("derived validation payload", payload)
    _reject_public_numeric_scalars("derived validation payload", payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload_without_digest(
    report: StrategySpecialistSignalConfidenceBlenderV2Report,
) -> dict[str, Any]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _reject_public_numeric_scalars(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must use Decimal strings for numeric values")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_scalars(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numeric_scalars(label, item)


@dataclass(frozen=True)
class _DictFlags:
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


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_public_fields("payload", payload, REPORT_PAYLOAD_FIELDS)
    _require_hard_flags("payload", _DictFlags(payload))
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        _require_public_fields("payload row", row, ROW_PAYLOAD_FIELDS)
        _require_hard_flags("payload row", _DictFlags(row))
    digest = payload[DERIVED_VALIDATION_DIGEST_FIELD]
    _require_sha256_digest(DERIVED_VALIDATION_DIGEST_FIELD, digest)
    comparable = dict(payload)
    comparable.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if digest != _derived_validation_digest(comparable):
        raise ValueError("derived_validation_digest must match payload fields")


def _require_public_fields(
    label: str,
    value: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    for field_name in expected_fields:
        if field_name not in value:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(value) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")
