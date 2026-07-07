"""Readonly Phase 1 quality score for manual review packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-manual-review-quality-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MANUAL_REVIEW_QUALITY_SCORE_DIMENSIONS = (
    "rationale_completeness",
    "source_coverage",
    "risk_reason_completeness",
    "abstain_condition_clarity",
    "cost_estimate_completeness",
    "resolution_rule_coverage",
    "handoff_readiness",
)

SCORE_BANDS = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "manual_review_quality_row_passed",
    "manual_review_quality_rationale_incomplete",
    "manual_review_quality_rationale_missing",
    "manual_review_quality_source_coverage_incomplete",
    "manual_review_quality_source_coverage_missing",
    "manual_review_quality_risk_reasons_incomplete",
    "manual_review_quality_risk_reasons_missing",
    "manual_review_quality_abstain_conditions_incomplete",
    "manual_review_quality_abstain_conditions_missing",
    "manual_review_quality_cost_estimate_incomplete",
    "manual_review_quality_cost_estimate_missing",
    "manual_review_quality_resolution_rule_coverage_incomplete",
    "manual_review_quality_resolution_rule_coverage_missing",
    "manual_review_quality_handoff_readiness_incomplete",
    "manual_review_quality_handoff_readiness_missing",
    "manual_review_quality_score_below_watch",
    "manual_review_quality_score_below_pass",
)
REPORT_REASON_CODES = (
    "manual_review_quality_report_passed",
    "manual_review_quality_report_empty",
    "manual_review_quality_report_blocked_rows",
    "manual_review_quality_report_watch_rows",
    "manual_review_quality_report_average_below_watch",
    "manual_review_quality_report_average_below_pass",
)
DIMENSION_SCORE_FIELDS = (
    (
        "rationale_completeness_score",
        "manual_review_quality_rationale_incomplete",
        "manual_review_quality_rationale_missing",
    ),
    (
        "source_coverage_score",
        "manual_review_quality_source_coverage_incomplete",
        "manual_review_quality_source_coverage_missing",
    ),
    (
        "risk_reason_completeness_score",
        "manual_review_quality_risk_reasons_incomplete",
        "manual_review_quality_risk_reasons_missing",
    ),
    (
        "abstain_condition_clarity_score",
        "manual_review_quality_abstain_conditions_incomplete",
        "manual_review_quality_abstain_conditions_missing",
    ),
    (
        "cost_estimate_completeness_score",
        "manual_review_quality_cost_estimate_incomplete",
        "manual_review_quality_cost_estimate_missing",
    ),
    (
        "resolution_rule_coverage_score",
        "manual_review_quality_resolution_rule_coverage_incomplete",
        "manual_review_quality_resolution_rule_coverage_missing",
    ),
    (
        "handoff_readiness_score",
        "manual_review_quality_handoff_readiness_incomplete",
        "manual_review_quality_handoff_readiness_missing",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "ord" "er",
    "net" "work",
    "data" "base",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "tra" "de",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION",
    "MANUAL_REVIEW_QUALITY_SCORE_DIMENSIONS",
    "TeamSpecialistManualReviewQualityScoreV2Config",
    "TeamSpecialistManualReviewQualityScoreV2Packet",
    "TeamSpecialistManualReviewQualityScoreV2Row",
    "TeamSpecialistManualReviewQualityScoreV2Report",
    "build_team_specialist_manual_review_quality_score_v2",
    "team_specialist_manual_review_quality_score_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistManualReviewQualityScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_MANUAL_REVIEW_QUALITY_SCORE_V2_CONFIG_VERSION
    )
    min_pass_quality_score: Decimal = Decimal("0.850000")
    min_watch_quality_score: Decimal = Decimal("0.650000")
    min_pass_dimension_score: Decimal = Decimal("0.750000")
    min_watch_dimension_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_quality_score",
            "min_watch_quality_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistManualReviewQualityScoreV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistManualReviewQualityScoreV2Packet:
    packet_id: str
    specialist_id: str
    rationale_completeness_score: Decimal
    source_coverage_score: Decimal
    risk_reason_completeness_score: Decimal
    abstain_condition_clarity_score: Decimal
    cost_estimate_completeness_score: Decimal
    resolution_rule_coverage_score: Decimal
    handoff_readiness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "packet_id",
            _require_non_empty_string("packet_id", self.packet_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name, _, _ in DIMENSION_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Packet", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistManualReviewQualityScoreV2Packet",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistManualReviewQualityScoreV2Row:
    rank: Decimal
    packet_id: str
    specialist_id: str
    rationale_completeness_score: Decimal
    source_coverage_score: Decimal
    risk_reason_completeness_score: Decimal
    abstain_condition_clarity_score: Decimal
    cost_estimate_completeness_score: Decimal
    resolution_rule_coverage_score: Decimal
    handoff_readiness_score: Decimal
    quality_score: Decimal
    score_band: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "packet_id",
            _require_non_empty_string("packet_id", self.packet_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        for field_name, _, _ in DIMENSION_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quality_score",
            _normalize_ratio("quality_score", self.quality_score),
        )
        _require_score_band("score_band", self.score_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistManualReviewQualityScoreV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistManualReviewQualityScoreV2Report:
    generated_at: datetime
    config_version: str
    score_band: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    pass_ratio: Decimal
    watch_ratio: Decimal
    blocked_ratio: Decimal
    average_quality_score: Decimal
    min_pass_quality_score: Decimal
    min_watch_quality_score: Decimal
    min_pass_dimension_score: Decimal
    min_watch_dimension_score: Decimal
    rows: tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_score_band("score_band", self.score_band)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "blocked_count",
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
            "pass_ratio",
            "watch_ratio",
            "blocked_ratio",
            "average_quality_score",
            "min_pass_quality_score",
            "min_watch_quality_score",
            "min_pass_dimension_score",
            "min_watch_dimension_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistManualReviewQualityScoreV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)
        if self.derived_validation_digest != _derived_validation_digest(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistManualReviewQualityScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_manual_review_quality_score_v2(
    manual_review_packets: object,
    *,
    config: TeamSpecialistManualReviewQualityScoreV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistManualReviewQualityScoreV2Report:
    if config is None:
        config = TeamSpecialistManualReviewQualityScoreV2Config()
    if type(config) is not TeamSpecialistManualReviewQualityScoreV2Config:
        raise ValueError(
            "config must be a TeamSpecialistManualReviewQualityScoreV2Config",
        )
    _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    packets = _normalize_packets(manual_review_packets)
    rows = _rows_for_packets(packets, config)
    packet_count = Decimal(len(rows)).quantize(COUNT_QUANT)
    pass_count = _score_band_count(rows, "pass")
    watch_count = _score_band_count(rows, "watch")
    blocked_count = _score_band_count(rows, "blocked")
    average_quality_score = _average_quality_score(rows)
    reasons = _report_reason_codes(
        packet_count=packet_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_quality_score=average_quality_score,
        config=config,
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "score_band": _report_score_band(
            packet_count=packet_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
            average_quality_score=average_quality_score,
            config=config,
        ),
        "packet_count": packet_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "pass_ratio": _ratio_or_zero(pass_count, packet_count),
        "watch_ratio": _ratio_or_zero(watch_count, packet_count),
        "blocked_ratio": _ratio_or_zero(blocked_count, packet_count),
        "average_quality_score": average_quality_score,
        "min_pass_quality_score": config.min_pass_quality_score,
        "min_watch_quality_score": config.min_watch_quality_score,
        "min_pass_dimension_score": config.min_pass_dimension_score,
        "min_watch_dimension_score": config.min_watch_dimension_score,
        "rows": rows,
        "reason_codes": reasons,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistManualReviewQualityScoreV2Report(**values)


def team_specialist_manual_review_quality_score_v2_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is TeamSpecialistManualReviewQualityScoreV2Report:
        return value.payload
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload(
        "team_specialist_manual_review_quality_score_v2_payload",
        payload,
    )
    _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def _rows_for_packets(
    packets: tuple[TeamSpecialistManualReviewQualityScoreV2Packet, ...],
    config: TeamSpecialistManualReviewQualityScoreV2Config,
) -> tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...]:
    sorted_packets = tuple(sorted(packets, key=lambda item: (item.packet_id, item.specialist_id)))
    return tuple(
        _row_for_packet(rank=index, packet=item, config=config)
        for index, item in enumerate(sorted_packets, start=1)
    )


def _row_for_packet(
    *,
    rank: int,
    packet: TeamSpecialistManualReviewQualityScoreV2Packet,
    config: TeamSpecialistManualReviewQualityScoreV2Config,
) -> TeamSpecialistManualReviewQualityScoreV2Row:
    quality_score = _quality_score(packet)
    return TeamSpecialistManualReviewQualityScoreV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        packet_id=packet.packet_id,
        specialist_id=packet.specialist_id,
        rationale_completeness_score=packet.rationale_completeness_score,
        source_coverage_score=packet.source_coverage_score,
        risk_reason_completeness_score=packet.risk_reason_completeness_score,
        abstain_condition_clarity_score=packet.abstain_condition_clarity_score,
        cost_estimate_completeness_score=packet.cost_estimate_completeness_score,
        resolution_rule_coverage_score=packet.resolution_rule_coverage_score,
        handoff_readiness_score=packet.handoff_readiness_score,
        quality_score=quality_score,
        score_band=_row_score_band(packet, quality_score, config),
        reason_codes=_row_reason_codes(packet, quality_score, config),
    )


def _quality_score(
    value: TeamSpecialistManualReviewQualityScoreV2Packet
    | TeamSpecialistManualReviewQualityScoreV2Row,
) -> Decimal:
    scores = tuple(getattr(value, field_name) for field_name, _, _ in DIMENSION_SCORE_FIELDS)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(scores, ZERO) / Decimal(len(scores)))


def _row_score_band(
    value: TeamSpecialistManualReviewQualityScoreV2Packet
    | TeamSpecialistManualReviewQualityScoreV2Row,
    quality_score: Decimal,
    config: TeamSpecialistManualReviewQualityScoreV2Config
    | TeamSpecialistManualReviewQualityScoreV2Report,
) -> str:
    scores = tuple(getattr(value, field_name) for field_name, _, _ in DIMENSION_SCORE_FIELDS)
    if quality_score < config.min_watch_quality_score or any(
        score < config.min_watch_dimension_score for score in scores
    ):
        return "blocked"
    if quality_score < config.min_pass_quality_score or any(
        score < config.min_pass_dimension_score for score in scores
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    value: TeamSpecialistManualReviewQualityScoreV2Packet
    | TeamSpecialistManualReviewQualityScoreV2Row,
    quality_score: Decimal,
    config: TeamSpecialistManualReviewQualityScoreV2Config
    | TeamSpecialistManualReviewQualityScoreV2Report,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name, incomplete_reason, missing_reason in DIMENSION_SCORE_FIELDS:
        score = getattr(value, field_name)
        if score < config.min_watch_dimension_score:
            reasons.append(missing_reason)
        elif score < config.min_pass_dimension_score:
            reasons.append(incomplete_reason)
    if quality_score < config.min_watch_quality_score:
        reasons.append("manual_review_quality_score_below_watch")
    elif quality_score < config.min_pass_quality_score:
        reasons.append("manual_review_quality_score_below_pass")
    return tuple(reasons or ("manual_review_quality_row_passed",))


def _score_band_count(
    rows: tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...],
    score_band: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.score_band == score_band)).quantize(
        COUNT_QUANT,
    )


def _average_quality_score(
    rows: tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.quality_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _report_reason_codes(
    *,
    packet_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    average_quality_score: Decimal,
    config: TeamSpecialistManualReviewQualityScoreV2Config
    | TeamSpecialistManualReviewQualityScoreV2Report,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if packet_count == ZERO:
        reasons.append("manual_review_quality_report_empty")
    if blocked_count > ZERO:
        reasons.append("manual_review_quality_report_blocked_rows")
    if watch_count > ZERO:
        reasons.append("manual_review_quality_report_watch_rows")
    if average_quality_score < config.min_watch_quality_score:
        reasons.append("manual_review_quality_report_average_below_watch")
    elif average_quality_score < config.min_pass_quality_score:
        reasons.append("manual_review_quality_report_average_below_pass")
    return tuple(reasons or ("manual_review_quality_report_passed",))


def _report_score_band(
    *,
    packet_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    average_quality_score: Decimal,
    config: TeamSpecialistManualReviewQualityScoreV2Config
    | TeamSpecialistManualReviewQualityScoreV2Report,
) -> str:
    if (
        packet_count == ZERO
        or blocked_count > ZERO
        or average_quality_score < config.min_watch_quality_score
    ):
        return "blocked"
    if watch_count > ZERO or average_quality_score < config.min_pass_quality_score:
        return "watch"
    return "pass"


def _normalize_packets(
    value: object,
) -> tuple[TeamSpecialistManualReviewQualityScoreV2Packet, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("manual_review_packets must be an iterable")
    packets = tuple(value)
    for item in packets:
        if type(item) is not TeamSpecialistManualReviewQualityScoreV2Packet:
            raise ValueError(
                "manual review packet items must be "
                "TeamSpecialistManualReviewQualityScoreV2Packet",
            )
        _require_hard_flags("TeamSpecialistManualReviewQualityScoreV2Packet", item)
    keys = tuple((item.packet_id, item.specialist_id) for item in packets)
    if len(set(keys)) != len(keys):
        raise ValueError("manual review packet items must not contain duplicate keys")
    return packets


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistManualReviewQualityScoreV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistManualReviewQualityScoreV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistManualReviewQualityScoreV2Config) -> None:
    if config.min_watch_quality_score > config.min_pass_quality_score:
        raise ValueError("min_watch_quality_score must not exceed min_pass_quality_score")
    if config.min_watch_dimension_score > config.min_pass_dimension_score:
        raise ValueError(
            "min_watch_dimension_score must not exceed min_pass_dimension_score",
        )


def _validate_row_consistency(row: TeamSpecialistManualReviewQualityScoreV2Row) -> None:
    expected_score = _quality_score(row)
    if row.quality_score != expected_score:
        raise ValueError("quality_score must match row dimensions")


def _validate_report_consistency(
    report: TeamSpecialistManualReviewQualityScoreV2Report,
) -> None:
    rows = report.rows
    if report.packet_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _score_band_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _score_band_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _score_band_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.pass_ratio != _ratio_or_zero(report.pass_count, report.packet_count):
        raise ValueError("pass_ratio must match counts")
    if report.watch_ratio != _ratio_or_zero(report.watch_count, report.packet_count):
        raise ValueError("watch_ratio must match counts")
    if report.blocked_ratio != _ratio_or_zero(report.blocked_count, report.packet_count):
        raise ValueError("blocked_ratio must match counts")
    if report.average_quality_score != _average_quality_score(rows):
        raise ValueError("average_quality_score must match rows")
    _validate_rows_sorted(rows)
    _validate_rows_against_report(rows, report)
    expected_reasons = _report_reason_codes(
        packet_count=report.packet_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        average_quality_score=report.average_quality_score,
        config=report,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report fields")
    expected_band = _report_score_band(
        packet_count=report.packet_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        average_quality_score=report.average_quality_score,
        config=report,
    )
    if report.score_band != expected_band:
        raise ValueError("score_band must match report fields")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...],
) -> None:
    expected = tuple(sorted(rows, key=lambda row: (row.packet_id, row.specialist_id)))
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must use deterministic sorting and rank")


def _validate_rows_against_report(
    rows: tuple[TeamSpecialistManualReviewQualityScoreV2Row, ...],
    report: TeamSpecialistManualReviewQualityScoreV2Report,
) -> None:
    for row in rows:
        if row.quality_score != _quality_score(row):
            raise ValueError("row quality_score must match dimensions")
        if row.reason_codes != _row_reason_codes(row, row.quality_score, report):
            raise ValueError("row reason_codes must match report thresholds")
        if row.score_band != _row_score_band(row, row.quality_score, report):
            raise ValueError("row score_band must match report thresholds")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_score_band(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in SCORE_BANDS:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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
    if type(value) in (float, int) and type(value) is not bool:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
