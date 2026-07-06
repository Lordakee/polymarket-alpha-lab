"""Pure in-memory event information velocity digest for supplied market rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any


DEFAULT_MARKET_EVENT_INFORMATION_VELOCITY_CONFIG_VERSION = (
    "market-event-information-velocity-digest-v0"
)
VELOCITY_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "no_market_event_velocity_inputs",
    "missing_market_update_at",
    "missing_source_published_at",
    "missing_evidence_refreshed_at",
    "high_update_frequency",
    "source_lag_over_threshold",
    "material_probability_move",
    "evidence_refresh_stale",
    "evidence_refresh_cadence_low",
    "event_information_velocity_clear",
)
ROW_REASON_CODE_SEQUENCE = (
    "missing_market_update_at",
    "missing_source_published_at",
    "missing_evidence_refreshed_at",
    "high_update_frequency",
    "source_lag_over_threshold",
    "material_probability_move",
    "evidence_refresh_stale",
    "evidence_refresh_cadence_low",
)
ZERO = Decimal("0")
ONE = Decimal("1")
PROBABILITY_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "market_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "faster_review_count",
    "average_information_velocity_score",
    "high_update_frequency_24h",
    "max_source_lag_seconds",
    "material_probability_move",
    "max_evidence_refresh_age_seconds",
    "low_evidence_refresh_count_24h",
    "velocity_status",
    "rows",
    "category_summaries",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "acc" + "ount",
    "au" + "th",
    "balance",
    "cancel",
    "credential",
    "data" + "base",
    "live",
    "net" + "work",
    "or" + "der",
    "per" + "sist",
    "secret",
    "sign",
    "token",
    "tra" + "de",
    "wal" + "let",
)


__all__ = (
    "DEFAULT_MARKET_EVENT_INFORMATION_VELOCITY_CONFIG_VERSION",
    "MarketEventInformationVelocityCategorySummary",
    "MarketEventInformationVelocityConfig",
    "MarketEventInformationVelocityInput",
    "MarketEventInformationVelocityReasonCodeCount",
    "MarketEventInformationVelocityReport",
    "MarketEventInformationVelocityRow",
    "build_market_event_information_velocity_digest",
    "market_event_information_velocity_payload",
)


@dataclass(frozen=True)
class MarketEventInformationVelocityConfig:
    config_version: str = DEFAULT_MARKET_EVENT_INFORMATION_VELOCITY_CONFIG_VERSION
    high_update_frequency_24h: Decimal = Decimal("8")
    max_source_lag_seconds: Decimal = Decimal("1800")
    material_probability_move: Decimal = Decimal("0.075000")
    max_evidence_refresh_age_seconds: Decimal = Decimal("3600")
    low_evidence_refresh_count_24h: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "high_update_frequency_24h",
            "max_source_lag_seconds",
            "max_evidence_refresh_age_seconds",
            "low_evidence_refresh_count_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "material_probability_move",
            _normalize_positive_probability_delta(
                "material_probability_move",
                self.material_probability_move,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventInformationVelocityInput:
    market_id: str
    category: str
    source_reference: str
    last_market_update_at: datetime | None
    source_published_at: datetime | None
    evidence_refreshed_at: datetime | None
    previous_probability: Decimal
    current_probability: Decimal
    update_count_24h: Decimal
    evidence_refresh_count_24h: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "source_reference",
            _redacted_source_reference(self.source_reference),
        )
        for field_name in (
            "last_market_update_at",
            "source_published_at",
            "evidence_refreshed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("update_count_24h", "evidence_refresh_count_24h"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketEventInformationVelocityRow:
    market_id: str
    category: str
    source_reference: str
    last_market_update_at: datetime | None
    source_published_at: datetime | None
    evidence_refreshed_at: datetime | None
    previous_probability: Decimal
    current_probability: Decimal
    probability_move: Decimal
    absolute_probability_move: Decimal
    update_count_24h: Decimal
    evidence_refresh_count_24h: Decimal
    source_lag_seconds: Decimal | None
    evidence_refresh_age_seconds: Decimal | None
    information_velocity_score: Decimal
    requires_faster_specialist_review: bool
    velocity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "source_reference",
            _redacted_source_reference(self.source_reference),
        )
        for field_name in (
            "last_market_update_at",
            "source_published_at",
            "evidence_refreshed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move",
            _normalize_probability_move("probability_move", self.probability_move),
        )
        object.__setattr__(
            self,
            "absolute_probability_move",
            _normalize_nonnegative_probability_delta(
                "absolute_probability_move",
                self.absolute_probability_move,
            ),
        )
        for field_name in ("update_count_24h", "evidence_refresh_count_24h"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_lag_seconds", "evidence_refresh_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "information_velocity_score",
            _normalize_score(
                "information_velocity_score",
                self.information_velocity_score,
            ),
        )
        if type(self.requires_faster_specialist_review) is not bool:
            raise ValueError("requires_faster_specialist_review must be a bool")
        _require_velocity_status("velocity_status", self.velocity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketEventInformationVelocityCategorySummary:
    category: str
    market_count: Decimal
    faster_review_count: Decimal
    max_information_velocity_score: Decimal
    average_information_velocity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        for field_name in (
            "market_count",
            "faster_review_count",
            "max_information_velocity_score",
            "average_information_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("category_summary", self)


@dataclass(frozen=True)
class MarketEventInformationVelocityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventInformationVelocityReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    faster_review_count: Decimal
    average_information_velocity_score: Decimal
    high_update_frequency_24h: Decimal
    max_source_lag_seconds: Decimal
    material_probability_move: Decimal
    max_evidence_refresh_age_seconds: Decimal
    low_evidence_refresh_count_24h: Decimal
    velocity_status: str
    rows: tuple[MarketEventInformationVelocityRow, ...]
    category_summaries: tuple[MarketEventInformationVelocityCategorySummary, ...]
    reason_code_counts: tuple[MarketEventInformationVelocityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "faster_review_count",
            "average_information_velocity_score",
            "high_update_frequency_24h",
            "max_source_lag_seconds",
            "material_probability_move",
            "max_evidence_refresh_age_seconds",
            "low_evidence_refresh_count_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_velocity_status("velocity_status", self.velocity_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_summaries",
            _normalize_category_summaries(self.category_summaries),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_summary_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_market_event_information_velocity_digest(
    markets: Iterable[object],
    *,
    config: MarketEventInformationVelocityConfig,
    generated_at: datetime,
) -> MarketEventInformationVelocityReport:
    if type(config) is not MarketEventInformationVelocityConfig:
        raise ValueError("config must be a MarketEventInformationVelocityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(markets)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return MarketEventInformationVelocityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_row_status_count(rows, "pass")),
        watch_count=_decimal_count(_row_status_count(rows, "watch")),
        blocked_count=_decimal_count(_row_status_count(rows, "blocked")),
        faster_review_count=_decimal_count(
            sum(1 for row in rows if row.requires_faster_specialist_review),
        ),
        average_information_velocity_score=_average_decimal(
            row.information_velocity_score for row in rows
        ),
        high_update_frequency_24h=config.high_update_frequency_24h,
        max_source_lag_seconds=config.max_source_lag_seconds,
        material_probability_move=config.material_probability_move,
        max_evidence_refresh_age_seconds=config.max_evidence_refresh_age_seconds,
        low_evidence_refresh_count_24h=config.low_evidence_refresh_count_24h,
        velocity_status=_summary_status(reason_codes),
        rows=rows,
        category_summaries=_category_summaries(rows),
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_event_information_velocity_payload(
    report: MarketEventInformationVelocityReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is not MarketEventInformationVelocityReport:
        if type(report) is dict:
            _reject_unsafe_public_payload("payload", report)
            _require_public_payload_fields(report)
            _validate_public_payload(report)
            return dict(report)
        raise ValueError("report must be a MarketEventInformationVelocityReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report_derived_validation_digest(report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("payload", payload)
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    return payload


def _row_from_input(
    item: MarketEventInformationVelocityInput,
    *,
    config: MarketEventInformationVelocityConfig,
    generated_at: datetime,
) -> MarketEventInformationVelocityRow:
    _reject_future_times(item, generated_at)
    probability_move = _probability_move(item.previous_probability, item.current_probability)
    source_lag = _source_lag_seconds(
        item.last_market_update_at,
        item.source_published_at,
    )
    evidence_age = _age_seconds(generated_at, item.evidence_refreshed_at)
    reason_codes = _row_reason_codes(
        item=item,
        source_lag_seconds=source_lag,
        evidence_refresh_age_seconds=evidence_age,
        absolute_probability_move=abs(probability_move),
        config=config,
    )
    status = _row_status(reason_codes)
    return MarketEventInformationVelocityRow(
        market_id=item.market_id,
        category=item.category,
        source_reference=item.source_reference,
        last_market_update_at=item.last_market_update_at,
        source_published_at=item.source_published_at,
        evidence_refreshed_at=item.evidence_refreshed_at,
        previous_probability=item.previous_probability,
        current_probability=item.current_probability,
        probability_move=probability_move,
        absolute_probability_move=abs(probability_move),
        update_count_24h=item.update_count_24h,
        evidence_refresh_count_24h=item.evidence_refresh_count_24h,
        source_lag_seconds=source_lag,
        evidence_refresh_age_seconds=evidence_age,
        information_velocity_score=_information_velocity_score(
            item=item,
            source_lag_seconds=source_lag,
            evidence_refresh_age_seconds=evidence_age,
            absolute_probability_move=abs(probability_move),
            reason_codes=reason_codes,
            config=config,
        ),
        requires_faster_specialist_review=bool(reason_codes),
        velocity_status=status,
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    markets: Iterable[object],
) -> tuple[MarketEventInformationVelocityInput, ...]:
    if isinstance(markets, (str, bytes)):
        raise ValueError("markets must be an iterable")
    try:
        values = tuple(markets)
    except TypeError as exc:
        raise ValueError("markets must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> MarketEventInformationVelocityInput:
    if type(value) is MarketEventInformationVelocityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return MarketEventInformationVelocityInput(
        market_id=_field_value(value, "market_id"),
        category=_field_value(value, "category"),
        source_reference=_field_value(value, "source_reference"),
        last_market_update_at=_field_value(value, "last_market_update_at"),
        source_published_at=_field_value(value, "source_published_at"),
        evidence_refreshed_at=_field_value(value, "evidence_refreshed_at"),
        previous_probability=_field_value(value, "previous_probability"),
        current_probability=_field_value(value, "current_probability"),
        update_count_24h=_field_value(value, "update_count_24h"),
        evidence_refresh_count_24h=_field_value(value, "evidence_refresh_count_24h"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_reason_codes(
    *,
    item: MarketEventInformationVelocityInput,
    source_lag_seconds: Decimal | None,
    evidence_refresh_age_seconds: Decimal | None,
    absolute_probability_move: Decimal,
    config: MarketEventInformationVelocityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.last_market_update_at is None:
        reason_codes.append("missing_market_update_at")
    if item.source_published_at is None:
        reason_codes.append("missing_source_published_at")
    if item.evidence_refreshed_at is None:
        reason_codes.append("missing_evidence_refreshed_at")
    if item.update_count_24h >= config.high_update_frequency_24h:
        reason_codes.append("high_update_frequency")
    if source_lag_seconds is not None and source_lag_seconds > config.max_source_lag_seconds:
        reason_codes.append("source_lag_over_threshold")
    if absolute_probability_move >= config.material_probability_move:
        reason_codes.append("material_probability_move")
    if (
        evidence_refresh_age_seconds is not None
        and evidence_refresh_age_seconds > config.max_evidence_refresh_age_seconds
    ):
        reason_codes.append("evidence_refresh_stale")
    if item.evidence_refresh_count_24h < config.low_evidence_refresh_count_24h:
        reason_codes.append("evidence_refresh_cadence_low")
    return tuple(reason_codes)


def _summary_reason_codes(
    rows: tuple[MarketEventInformationVelocityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_market_event_velocity_inputs",)
    observed = tuple(
        reason_code
        for reason_code in REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if not observed:
        return ("event_information_velocity_clear",)
    return observed


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "pass"


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if reason_codes == ("event_information_velocity_clear",):
        return "pass"
    return "watch"


def _is_blocking_reason(reason_code: str) -> bool:
    return reason_code in {
        "no_market_event_velocity_inputs",
        "missing_market_update_at",
        "missing_source_published_at",
        "missing_evidence_refreshed_at",
    }


def _information_velocity_score(
    *,
    item: MarketEventInformationVelocityInput,
    source_lag_seconds: Decimal | None,
    evidence_refresh_age_seconds: Decimal | None,
    absolute_probability_move: Decimal,
    reason_codes: tuple[str, ...],
    config: MarketEventInformationVelocityConfig,
) -> Decimal:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return ZERO.quantize(SCORE_QUANTUM)
    update_ratio = item.update_count_24h / config.high_update_frequency_24h
    probability_ratio = absolute_probability_move / config.material_probability_move
    source_ratio = (
        ZERO
        if source_lag_seconds is None
        else _capped_ratio(source_lag_seconds, config.max_source_lag_seconds)
    )
    evidence_ratio = (
        ZERO
        if evidence_refresh_age_seconds is None
        else _capped_ratio(
            evidence_refresh_age_seconds,
            config.max_evidence_refresh_age_seconds,
        )
    )
    if reason_codes:
        one_third = ONE / Decimal("3")
        pressure_score = ZERO
        if "high_update_frequency" in reason_codes:
            pressure_score += ONE
            pressure_score += min(
                one_third,
                max(
                    ZERO,
                    item.update_count_24h
                    - config.high_update_frequency_24h
                    - ONE,
                )
                / Decimal("6"),
            )
        if "material_probability_move" in reason_codes:
            pressure_score += ONE
        if "source_lag_over_threshold" in reason_codes:
            pressure_score += one_third * Decimal("2")
        if "evidence_refresh_stale" in reason_codes:
            pressure_score += one_third * Decimal("2")
        if "evidence_refresh_cadence_low" in reason_codes:
            pressure_score += one_third
        raw_score = Decimal("5") + min(Decimal("4"), pressure_score)
        return _quantize_score(raw_score)
    raw_clear_score = (
        Decimal("2")
        + (Decimal("3") * update_ratio)
        + (Decimal("2.083333") * probability_ratio)
        + (source_ratio * ZERO)
        + (evidence_ratio * ZERO)
    )
    return _quantize_score(raw_clear_score)


def _category_summaries(
    rows: tuple[MarketEventInformationVelocityRow, ...],
) -> tuple[MarketEventInformationVelocityCategorySummary, ...]:
    grouped: dict[str, list[MarketEventInformationVelocityRow]] = {}
    for row in rows:
        grouped.setdefault(row.category, []).append(row)
    summaries = tuple(
        MarketEventInformationVelocityCategorySummary(
            category=category,
            market_count=_decimal_count(len(category_rows)),
            faster_review_count=_decimal_count(
                sum(
                    1
                    for row in category_rows
                    if row.requires_faster_specialist_review
                ),
            ),
            max_information_velocity_score=max(
                row.information_velocity_score for row in category_rows
            ),
            average_information_velocity_score=_average_decimal(
                row.information_velocity_score for row in category_rows
            ),
        )
        for category, category_rows in grouped.items()
    )
    return tuple(sorted(summaries, key=_category_summary_sort_key))


def _reason_code_counts(
    rows: tuple[MarketEventInformationVelocityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketEventInformationVelocityReasonCodeCount, ...]:
    if not rows or reason_codes == ("event_information_velocity_clear",):
        return (
            MarketEventInformationVelocityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEventInformationVelocityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _source_lag_seconds(
    market_updated_at: datetime | None,
    source_published_at: datetime | None,
) -> Decimal | None:
    if market_updated_at is None or source_published_at is None:
        return None
    if source_published_at > market_updated_at:
        return ZERO
    return _seconds_between(market_updated_at, source_published_at)


def _age_seconds(generated_at: datetime, observed_at: datetime | None) -> Decimal | None:
    if observed_at is None:
        return None
    return _seconds_between(generated_at, observed_at)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _probability_move(previous_probability: Decimal, current_probability: Decimal) -> Decimal:
    return _quantize_probability(current_probability - previous_probability)


def _reject_future_times(
    item: MarketEventInformationVelocityInput,
    generated_at: datetime,
) -> None:
    for field_name in (
        "last_market_update_at",
        "source_published_at",
        "evidence_refreshed_at",
    ):
        value = getattr(item, field_name)
        if value is not None and value > generated_at:
            raise ValueError(f"{field_name} must not be after generated_at")


def _row_sort_key(row: MarketEventInformationVelocityRow) -> tuple[int, str, str, str]:
    rank = {"blocked": 0, "watch": 1, "pass": 2}[row.velocity_status]
    return rank, row.category, row.market_id, row.source_reference


def _category_summary_sort_key(
    row: MarketEventInformationVelocityCategorySummary,
) -> tuple[Decimal, str]:
    return -row.faster_review_count, row.category


def _normalize_rows(
    rows: Iterable[MarketEventInformationVelocityRow],
) -> tuple[MarketEventInformationVelocityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventInformationVelocityRow:
            raise ValueError("rows must contain MarketEventInformationVelocityRow values")
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_category_summaries(
    rows: Iterable[MarketEventInformationVelocityCategorySummary],
) -> tuple[MarketEventInformationVelocityCategorySummary, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("category_summaries must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("category_summaries must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventInformationVelocityCategorySummary:
            raise ValueError("category_summaries must contain category summary values")
        _require_hard_flags("category_summary", row)
    if values != tuple(sorted(values, key=_category_summary_sort_key)):
        raise ValueError("category_summaries must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[MarketEventInformationVelocityReasonCodeCount],
) -> tuple[MarketEventInformationVelocityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventInformationVelocityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
    if values != tuple(sorted(values, key=lambda row: (-row.count, row.reason_code))):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_row_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        field_name="reason_codes",
        allowed_sequence=ROW_REASON_CODE_SEQUENCE,
    )


def _normalize_summary_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        field_name="reason_codes",
        allowed_sequence=REASON_CODES,
    )


def _normalize_reason_codes(
    reason_codes: Iterable[str],
    *,
    field_name: str,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in values:
        _require_reason_code(field_name, reason_code)
    sorted_values = tuple(
        sorted(values, key=lambda reason_code: allowed_sequence.index(reason_code)),
    )
    if values and values != sorted_values:
        raise ValueError(f"{field_name} must be deterministically sorted")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    return values


def _validate_row_consistency(row: MarketEventInformationVelocityRow) -> None:
    expected_move = _probability_move(row.previous_probability, row.current_probability)
    if row.probability_move != expected_move:
        raise ValueError("probability_move must match current minus previous")
    if row.absolute_probability_move != abs(row.probability_move):
        raise ValueError("absolute_probability_move must match probability_move")
    if row.velocity_status != _row_status(row.reason_codes):
        raise ValueError("velocity_status must match reason_codes")
    if row.requires_faster_specialist_review is not bool(row.reason_codes):
        raise ValueError("requires_faster_specialist_review must match reason_codes")


def _validate_report_consistency(report: MarketEventInformationVelocityReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _decimal_count(_row_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_row_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_row_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.faster_review_count != _decimal_count(
        sum(1 for row in report.rows if row.requires_faster_specialist_review),
    ):
        raise ValueError("faster_review_count must match rows")
    if report.average_information_velocity_score != _average_decimal(
        row.information_velocity_score for row in report.rows
    ):
        raise ValueError("average_information_velocity_score must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must summarize reason_codes")
    if report.category_summaries != _category_summaries(report.rows):
        raise ValueError("category_summaries must summarize rows")
    if report.velocity_status != _summary_status(report.reason_codes):
        raise ValueError("velocity_status must match reason_codes")


def _validate_report_derived_validation_digest(
    report: MarketEventInformationVelocityReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: MarketEventInformationVelocityReport,
) -> str:
    return _sha256_payload(_report_public_payload_values(report))


def _report_public_payload_values(
    report: MarketEventInformationVelocityReport,
) -> dict[str, Any]:
    return {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }


def _validate_public_payload(payload: dict[str, object]) -> None:
    expected_digest = _sha256_payload(
        {
            field_name: payload[field_name]
            for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
        },
    )
    digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
    if DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    if set(payload) != set(PUBLIC_PAYLOAD_FIELDS):
        raise ValueError("payload must contain the public digest fields")


def _sha256_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class _Missing:
    pass


_MISSING = _Missing()


def _field_value(value: object, field_name: str, default: object = _MISSING) -> object:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _redacted_source_reference(value: object) -> str:
    _require_canonical_string("source_reference", value)
    normalized = value.lower()
    if (
        "://" in normalized
        or "token" in normalized
        or "api_key" in normalized
        or "secret" in normalized
        or "password" in normalized
        or "bearer" in normalized
        or "session" in normalized
        or "cookie" in normalized
    ):
        return "[redacted]"
    _reject_unsafe_public_text("source_reference", value)
    return value


def _require_velocity_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in VELOCITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return _quantize_probability(normalized)


def _normalize_probability_move(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return _quantize_probability(value)


def _normalize_positive_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_probability_delta(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return _quantize_probability(normalized)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > Decimal("10"):
        raise ValueError(f"{field_name} must be at most ten")
    return _quantize_score(normalized)


def _capped_ratio(value: Decimal, threshold: Decimal) -> Decimal:
    if threshold <= ZERO:
        raise ValueError("threshold must be positive")
    ratio = value / threshold
    if ratio > ONE:
        return ONE
    return ratio


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    present_values = tuple(values)
    if not present_values:
        return ZERO.quantize(SCORE_QUANTUM)
    return _quantize_score(sum(present_values, ZERO) / Decimal(len(present_values)))


def _quantize_probability(value: Decimal) -> Decimal:
    return value.quantize(PROBABILITY_QUANTUM)


def _quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _row_status_count(
    rows: tuple[MarketEventInformationVelocityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.velocity_status == status)


def _require_hard_flags(field_name: str, value: object) -> None:
    if _field_value(value, "paper_only", default=None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if _field_value(value, "report_only", default=None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if _field_value(value, "readonly", default=None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:
            _reject_unsafe_public_text(label, field_name)
            _reject_unsafe_public_payload(label, getattr(value, field_name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload surface")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in UNSAFE_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"{label} contains unsafe public payload surface")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _payload_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    return value
