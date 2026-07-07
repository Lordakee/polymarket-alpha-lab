from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_REVIEW_QUALITY_SCORE_CONFIG_VERSION = (
    "team-specialist-review-quality-score"
)
SPECIALIST_REVIEW_QUALITY_SCORE_FACTORS = (
    "evidence_completeness",
    "calibration",
    "correction_rate",
    "fresh_review",
    "gap_resolution",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_REVIEW_QUALITY_SCORE_CONFIG_VERSION",
    "SPECIALIST_REVIEW_QUALITY_SCORE_FACTORS",
    "TeamSpecialistReviewQualityScoreConfig",
    "TeamSpecialistReviewQualityInput",
    "TeamSpecialistReviewQualityRow",
    "TeamSpecialistReviewQualityReport",
    "build_team_specialist_review_quality_score",
    "team_specialist_review_quality_score_payload",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")

DECIMAL_CONTEXT = decimal_context = __import__("decimal").Context(
    prec=28,
    rounding=__import__("decimal").ROUND_HALF_EVEN,
)

STATUS_VALUES = ("pass", "watch", "block")

ROW_REASON_CODES = (
    "specialist_review_quality_row_pass",
    "specialist_review_quality_insufficient_review_volume",
    "specialist_review_quality_score_below_watch",
    "specialist_review_quality_score_below_pass",
    "specialist_review_quality_stale_review_ratio_above_watch",
    "specialist_review_quality_stale_review_ratio_above_pass",
    "specialist_review_quality_unresolved_gap_ratio_above_watch",
    "specialist_review_quality_unresolved_gap_ratio_above_pass",
)

REPORT_REASON_CODES = (
    "specialist_review_quality_report_pass",
    "specialist_review_quality_report_empty",
    "specialist_review_quality_report_block_rows",
    "specialist_review_quality_report_watch_rows",
    "specialist_review_quality_report_average_below_watch",
    "specialist_review_quality_report_average_below_pass",
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "market_id",
    "candidate_id",
    "market_slug",
    "market_question",
    "question",
    "http://",
    "https://",
    "url",
    "source",
    "source_ref",
    "source_refs",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "position-sizing",
    "position_sizing",
)


@dataclass(frozen=True)
class TeamSpecialistReviewQualityScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_REVIEW_QUALITY_SCORE_CONFIG_VERSION
    evidence_completeness_weight: Decimal = Decimal("0.300000")
    calibration_weight: Decimal = Decimal("0.300000")
    correction_rate_weight: Decimal = Decimal("0.200000")
    fresh_review_weight: Decimal = Decimal("0.100000")
    gap_resolution_weight: Decimal = Decimal("0.100000")
    min_pass_quality_score: Decimal = Decimal("0.850000")
    min_watch_quality_score: Decimal = Decimal("0.650000")
    min_reviewed_case_count: Decimal = Decimal("3")
    max_pass_stale_review_ratio: Decimal = Decimal("0.200000")
    max_watch_stale_review_ratio: Decimal = Decimal("0.400000")
    max_pass_unresolved_gap_ratio: Decimal = Decimal("0.150000")
    max_watch_unresolved_gap_ratio: Decimal = Decimal("0.350000")
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
            "evidence_completeness_weight",
            "calibration_weight",
            "correction_rate_weight",
            "fresh_review_weight",
            "gap_resolution_weight",
            "min_pass_quality_score",
            "min_watch_quality_score",
            "max_pass_stale_review_ratio",
            "max_watch_stale_review_ratio",
            "max_pass_unresolved_gap_ratio",
            "max_watch_unresolved_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reviewed_case_count",
            _normalize_positive_integral_decimal(
                "min_reviewed_case_count",
                self.min_reviewed_case_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistReviewQualityScoreConfig", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewQualityScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewQualityInput:
    team_id: str
    specialist_id: str
    reviewed_case_count: Decimal
    evidence_completeness_score: Decimal
    calibration_score: Decimal
    correction_rate_score: Decimal
    stale_review_ratio: Decimal
    unresolved_gap_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _require_non_empty_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "reviewed_case_count",
            _normalize_nonnegative_integral_decimal(
                "reviewed_case_count",
                self.reviewed_case_count,
            ),
        )
        for field_name in (
            "evidence_completeness_score",
            "calibration_score",
            "correction_rate_score",
            "stale_review_ratio",
            "unresolved_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("TeamSpecialistReviewQualityInput", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewQualityInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewQualityRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    reviewed_case_count: Decimal
    evidence_completeness_score: Decimal
    calibration_score: Decimal
    correction_rate_score: Decimal
    stale_review_ratio: Decimal
    unresolved_gap_ratio: Decimal
    fresh_review_score: Decimal
    gap_resolution_score: Decimal
    specialist_review_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_integral_decimal("rank", self.rank))
        object.__setattr__(self, "team_id", _require_non_empty_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "reviewed_case_count",
            _normalize_nonnegative_integral_decimal(
                "reviewed_case_count",
                self.reviewed_case_count,
            ),
        )
        for field_name in (
            "evidence_completeness_score",
            "calibration_score",
            "correction_rate_score",
            "stale_review_ratio",
            "unresolved_gap_ratio",
            "fresh_review_score",
            "gap_resolution_score",
            "specialist_review_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags("TeamSpecialistReviewQualityRow", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewQualityRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    average_specialist_review_quality_score: Decimal
    min_pass_quality_score: Decimal
    min_watch_quality_score: Decimal
    min_reviewed_case_count: Decimal
    max_pass_stale_review_ratio: Decimal
    max_watch_stale_review_ratio: Decimal
    max_pass_unresolved_gap_ratio: Decimal
    max_watch_unresolved_gap_ratio: Decimal
    rows: tuple[TeamSpecialistReviewQualityRow, ...]
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
        _require_status("report_status", self.report_status)
        for field_name in (
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
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
            "block_ratio",
            "average_specialist_review_quality_score",
            "min_pass_quality_score",
            "min_watch_quality_score",
            "max_pass_stale_review_ratio",
            "max_watch_stale_review_ratio",
            "max_pass_unresolved_gap_ratio",
            "max_watch_unresolved_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reviewed_case_count",
            _normalize_positive_integral_decimal(
                "min_reviewed_case_count",
                self.min_reviewed_case_count,
            ),
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("TeamSpecialistReviewQualityReport", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistReviewQualityReport",
            _payload_value(asdict(self)),
        )
        if self.derived_validation_digest != _derived_validation_digest(asdict(self)):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("TeamSpecialistReviewQualityReport.payload", payload)
        return payload


def build_team_specialist_review_quality_score(
    specialist_reviews: object,
    *,
    config: TeamSpecialistReviewQualityScoreConfig | None = None,
    generated_at: datetime,
) -> TeamSpecialistReviewQualityReport:
    if config is None:
        config = TeamSpecialistReviewQualityScoreConfig()
    if type(config) is not TeamSpecialistReviewQualityScoreConfig:
        raise ValueError("config must be a TeamSpecialistReviewQualityScoreConfig")
    _require_hard_flags("TeamSpecialistReviewQualityScoreConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reviews = _normalize_inputs(specialist_reviews)
    rows = _rows_for_inputs(reviews, config)
    specialist_count = Decimal(len(rows)).quantize(COUNT_QUANT)
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    average_score = _average_quality_score(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(
            specialist_count=specialist_count,
            watch_count=watch_count,
            block_count=block_count,
            average_score=average_score,
            config=config,
        ),
        "specialist_count": specialist_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "pass_ratio": _ratio_or_zero(pass_count, specialist_count),
        "watch_ratio": _ratio_or_zero(watch_count, specialist_count),
        "block_ratio": _ratio_or_zero(block_count, specialist_count),
        "average_specialist_review_quality_score": average_score,
        "min_pass_quality_score": config.min_pass_quality_score,
        "min_watch_quality_score": config.min_watch_quality_score,
        "min_reviewed_case_count": config.min_reviewed_case_count,
        "max_pass_stale_review_ratio": config.max_pass_stale_review_ratio,
        "max_watch_stale_review_ratio": config.max_watch_stale_review_ratio,
        "max_pass_unresolved_gap_ratio": config.max_pass_unresolved_gap_ratio,
        "max_watch_unresolved_gap_ratio": config.max_watch_unresolved_gap_ratio,
        "rows": rows,
        "reason_codes": _report_reason_codes(
            specialist_count=specialist_count,
            watch_count=watch_count,
            block_count=block_count,
            average_score=average_score,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistReviewQualityReport(**values)


def team_specialist_review_quality_score_payload(value: object) -> dict[str, object]:
    if type(value) is TeamSpecialistReviewQualityReport:
        return value.payload
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("team_specialist_review_quality_score_payload", payload)
    _require_sha256_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    return payload


def _rows_for_inputs(
    reviews: tuple[TeamSpecialistReviewQualityInput, ...],
    config: TeamSpecialistReviewQualityScoreConfig,
) -> tuple[TeamSpecialistReviewQualityRow, ...]:
    sorted_reviews = tuple(sorted(reviews, key=lambda item: (item.team_id, item.specialist_id)))
    return tuple(
        _row_for_input(rank=index, item=item, config=config)
        for index, item in enumerate(sorted_reviews, start=1)
    )


def _row_for_input(
    *,
    rank: int,
    item: TeamSpecialistReviewQualityInput,
    config: TeamSpecialistReviewQualityScoreConfig,
) -> TeamSpecialistReviewQualityRow:
    fresh_review_score = _inverse_ratio(item.stale_review_ratio)
    gap_resolution_score = _inverse_ratio(item.unresolved_gap_ratio)
    quality_score = _quality_score(
        evidence_completeness_score=item.evidence_completeness_score,
        calibration_score=item.calibration_score,
        correction_rate_score=item.correction_rate_score,
        fresh_review_score=fresh_review_score,
        gap_resolution_score=gap_resolution_score,
        config=config,
    )
    return TeamSpecialistReviewQualityRow(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        reviewed_case_count=item.reviewed_case_count,
        evidence_completeness_score=item.evidence_completeness_score,
        calibration_score=item.calibration_score,
        correction_rate_score=item.correction_rate_score,
        stale_review_ratio=item.stale_review_ratio,
        unresolved_gap_ratio=item.unresolved_gap_ratio,
        fresh_review_score=fresh_review_score,
        gap_resolution_score=gap_resolution_score,
        specialist_review_quality_score=quality_score,
        status=_row_status(item, quality_score, config),
        reason_codes=_row_reason_codes(item, quality_score, config),
    )


def _quality_score(
    *,
    evidence_completeness_score: Decimal,
    calibration_score: Decimal,
    correction_rate_score: Decimal,
    fresh_review_score: Decimal,
    gap_resolution_score: Decimal,
    config: TeamSpecialistReviewQualityScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            evidence_completeness_score * config.evidence_completeness_weight
            + calibration_score * config.calibration_weight
            + correction_rate_score * config.correction_rate_weight
            + fresh_review_score * config.fresh_review_weight
            + gap_resolution_score * config.gap_resolution_weight
        )
    return _clamp_ratio(raw_score)


def _row_status(
    value: TeamSpecialistReviewQualityInput | TeamSpecialistReviewQualityRow,
    quality_score: Decimal,
    config: TeamSpecialistReviewQualityScoreConfig | TeamSpecialistReviewQualityReport,
) -> str:
    if (
        value.reviewed_case_count < config.min_reviewed_case_count
        or quality_score < config.min_watch_quality_score
        or value.stale_review_ratio > config.max_watch_stale_review_ratio
        or value.unresolved_gap_ratio > config.max_watch_unresolved_gap_ratio
    ):
        return "block"
    if (
        quality_score < config.min_pass_quality_score
        or value.stale_review_ratio > config.max_pass_stale_review_ratio
        or value.unresolved_gap_ratio > config.max_pass_unresolved_gap_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    value: TeamSpecialistReviewQualityInput | TeamSpecialistReviewQualityRow,
    quality_score: Decimal,
    config: TeamSpecialistReviewQualityScoreConfig | TeamSpecialistReviewQualityReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.reviewed_case_count < config.min_reviewed_case_count:
        reasons.append("specialist_review_quality_insufficient_review_volume")
    if quality_score < config.min_watch_quality_score:
        reasons.append("specialist_review_quality_score_below_watch")
    elif quality_score < config.min_pass_quality_score:
        reasons.append("specialist_review_quality_score_below_pass")
    if value.stale_review_ratio > config.max_watch_stale_review_ratio:
        reasons.append("specialist_review_quality_stale_review_ratio_above_watch")
    elif value.stale_review_ratio > config.max_pass_stale_review_ratio:
        reasons.append("specialist_review_quality_stale_review_ratio_above_pass")
    if value.unresolved_gap_ratio > config.max_watch_unresolved_gap_ratio:
        reasons.append("specialist_review_quality_unresolved_gap_ratio_above_watch")
    elif value.unresolved_gap_ratio > config.max_pass_unresolved_gap_ratio:
        reasons.append("specialist_review_quality_unresolved_gap_ratio_above_pass")
    return tuple(reasons or ("specialist_review_quality_row_pass",))


def _status_count(rows: tuple[TeamSpecialistReviewQualityRow, ...], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status)).quantize(COUNT_QUANT)


def _average_quality_score(rows: tuple[TeamSpecialistReviewQualityRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.specialist_review_quality_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _report_status(
    *,
    specialist_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_score: Decimal,
    config: TeamSpecialistReviewQualityScoreConfig | TeamSpecialistReviewQualityReport,
) -> str:
    if (
        specialist_count == ZERO
        or block_count > ZERO
        or average_score < config.min_watch_quality_score
    ):
        return "block"
    if watch_count > ZERO or average_score < config.min_pass_quality_score:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    specialist_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_score: Decimal,
    config: TeamSpecialistReviewQualityScoreConfig | TeamSpecialistReviewQualityReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if specialist_count == ZERO:
        reasons.append("specialist_review_quality_report_empty")
    if block_count > ZERO:
        reasons.append("specialist_review_quality_report_block_rows")
    if watch_count > ZERO:
        reasons.append("specialist_review_quality_report_watch_rows")
    if average_score < config.min_watch_quality_score:
        reasons.append("specialist_review_quality_report_average_below_watch")
    elif average_score < config.min_pass_quality_score:
        reasons.append("specialist_review_quality_report_average_below_pass")
    return tuple(reasons or ("specialist_review_quality_report_pass",))


def _normalize_inputs(value: object) -> tuple[TeamSpecialistReviewQualityInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("specialist_reviews must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistReviewQualityInput:
            raise ValueError(
                "specialist review items must be TeamSpecialistReviewQualityInput",
            )
        _require_hard_flags("TeamSpecialistReviewQualityInput", item)
    keys = tuple((item.team_id, item.specialist_id) for item in items)
    if len(set(keys)) != len(keys):
        raise ValueError("specialist review items must not contain duplicate keys")
    return items


def _normalize_rows(value: object) -> tuple[TeamSpecialistReviewQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistReviewQualityRow:
            raise ValueError("rows must contain TeamSpecialistReviewQualityRow")
    return value


def _validate_config(config: TeamSpecialistReviewQualityScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.evidence_completeness_weight
            + config.calibration_weight
            + config.correction_rate_weight
            + config.fresh_review_weight
            + config.gap_resolution_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("specialist review quality weights must sum to 1.000000")
    if config.min_watch_quality_score > config.min_pass_quality_score:
        raise ValueError("min_watch_quality_score must not exceed min_pass_quality_score")
    if config.max_pass_stale_review_ratio > config.max_watch_stale_review_ratio:
        raise ValueError(
            "max_pass_stale_review_ratio must not exceed max_watch_stale_review_ratio",
        )
    if config.max_pass_unresolved_gap_ratio > config.max_watch_unresolved_gap_ratio:
        raise ValueError(
            "max_pass_unresolved_gap_ratio must not exceed max_watch_unresolved_gap_ratio",
        )


def _validate_row_consistency(row: TeamSpecialistReviewQualityRow) -> None:
    expected_fresh_review_score = _inverse_ratio(row.stale_review_ratio)
    if row.fresh_review_score != expected_fresh_review_score:
        raise ValueError("fresh_review_score must match stale_review_ratio")
    expected_gap_resolution_score = _inverse_ratio(row.unresolved_gap_ratio)
    if row.gap_resolution_score != expected_gap_resolution_score:
        raise ValueError("gap_resolution_score must match unresolved_gap_ratio")


def _validate_report_consistency(report: TeamSpecialistReviewQualityReport) -> None:
    rows = report.rows
    if report.specialist_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("specialist_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _ratio_or_zero(report.pass_count, report.specialist_count):
        raise ValueError("pass_ratio must match counts")
    if report.watch_ratio != _ratio_or_zero(report.watch_count, report.specialist_count):
        raise ValueError("watch_ratio must match counts")
    if report.block_ratio != _ratio_or_zero(report.block_count, report.specialist_count):
        raise ValueError("block_ratio must match counts")
    if report.average_specialist_review_quality_score != _average_quality_score(rows):
        raise ValueError("average_specialist_review_quality_score must match rows")
    if report.report_status != _report_status(
        specialist_count=report.specialist_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_score=report.average_specialist_review_quality_score,
        config=report,
    ):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(
        specialist_count=report.specialist_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_score=report.average_specialist_review_quality_score,
        config=report,
    ):
        raise ValueError("reason_codes must match rows")


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
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_public_text(field_name, normalized)
    return normalized


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_exact_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    quantized = value.quantize(SCORE_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_exact_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be > 0")
    return value


def _inverse_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            value = ZERO
        if value > ONE:
            value = ONE
        return value.quantize(SCORE_QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        item = _require_non_empty_string(field_name, item)
        if item not in allowed_values:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        normalized.append(item)
    return tuple(normalized)


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
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
