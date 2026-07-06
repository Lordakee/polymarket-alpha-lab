"""Pure report-only reducer for market probability regime-shift diagnostics."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION = (
    "market-probability-regime-shift-digest-v0"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
REDACTED_VALUE = "[REDACTED]"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
DIGEST_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
CATEGORY_STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

STABLE_BUCKET = "stable"
MEDIUM_BUCKET = "medium"
HIGH_BUCKET = "high"
EXTREME_BUCKET = "extreme"
VOLATILITY_BUCKETS = (STABLE_BUCKET, MEDIUM_BUCKET, HIGH_BUCKET, EXTREME_BUCKET)

FRESH_STATUS = "fresh"
STALE_STATUS = "stale"
SOURCE_FRESHNESS_STATUSES = (FRESH_STATUS, STALE_STATUS)

MEDIUM_MOVE_REASON = "probability_regime_shift_medium_move"
HIGH_MOVE_REASON = "probability_regime_shift_high_move"
EXTREME_MOVE_REASON = "probability_regime_shift_extreme_move"
LIQUIDITY_CONFIRMED_REASON = "probability_regime_shift_liquidity_confirmed"
UNCONFIRMED_LIQUIDITY_REASON = "probability_regime_shift_unconfirmed_liquidity"
SOURCE_STALE_REASON = "probability_regime_shift_source_stale"
STABLE_REASON = "probability_regime_shift_stable"
DIGEST_PASSED_REASON = "probability_regime_shift_digest_passed"
DIGEST_EMPTY_REASON = "probability_regime_shift_digest_empty"

ROW_REASON_CODES = (
    EXTREME_MOVE_REASON,
    HIGH_MOVE_REASON,
    LIQUIDITY_CONFIRMED_REASON,
    MEDIUM_MOVE_REASON,
    SOURCE_STALE_REASON,
    STABLE_REASON,
    UNCONFIRMED_LIQUIDITY_REASON,
)
DIGEST_REASON_CODES = (
    EXTREME_MOVE_REASON,
    HIGH_MOVE_REASON,
    LIQUIDITY_CONFIRMED_REASON,
    MEDIUM_MOVE_REASON,
    SOURCE_STALE_REASON,
    UNCONFIRMED_LIQUIDITY_REASON,
    DIGEST_PASSED_REASON,
    DIGEST_EMPTY_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))

NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_probability_regime_shift_monitoring",
    WATCH_STATUS: "review_probability_regime_shift_diagnostics",
    BLOCKED_STATUS: "review_probability_regime_shift_diagnostics",
}

SENSITIVE_REFERENCE_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "bearer",
    "data" + "base",
    "net" + "work",
    "ord" + "er",
    "per" + "sist",
    "private",
    "secret",
    "token",
    "wal" + "let",
)
RISKY_TEXT_FRAGMENTS = SENSITIVE_REFERENCE_FRAGMENTS

PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "digest_status",
    "recommended_next_step",
    "condition_count",
    "category_count",
    "shifted_condition_count",
    "liquidity_confirmed_shift_count",
    "unconfirmed_shift_count",
    "stale_source_condition_count",
    "max_recent_probability_move",
    "max_source_age_seconds",
    "rows",
    "category_rollups",
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

__all__ = (
    "DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION",
    "MarketProbabilityRegimeShiftCategoryRollup",
    "MarketProbabilityRegimeShiftDigestConfig",
    "MarketProbabilityRegimeShiftDigestReport",
    "MarketProbabilityRegimeShiftInput",
    "MarketProbabilityRegimeShiftReasonCodeCount",
    "MarketProbabilityRegimeShiftRow",
    "build_market_probability_regime_shift_digest",
    "market_probability_regime_shift_digest_json_payload",
)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftDigestConfig:
    config_version: str = DEFAULT_MARKET_PROBABILITY_REGIME_SHIFT_DIGEST_CONFIG_VERSION
    medium_move_threshold: Decimal = Decimal("0.030000")
    high_move_threshold: Decimal = Decimal("0.080000")
    extreme_move_threshold: Decimal = Decimal("0.150000")
    liquidity_confirmation_threshold: Decimal = Decimal("0.600000")
    stale_source_seconds_threshold: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftDigestConfig:
            raise TypeError(
                "MarketProbabilityRegimeShiftDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftDigestConfig:
            raise ValueError(
                "config must be exactly MarketProbabilityRegimeShiftDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "medium_move_threshold",
            "high_move_threshold",
            "extreme_move_threshold",
            "liquidity_confirmation_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_source_seconds_threshold",
            _normalize_nonnegative_decimal(
                "stale_source_seconds_threshold",
                self.stale_source_seconds_threshold,
            ),
        )
        if self.medium_move_threshold <= ZERO:
            raise ValueError("medium_move_threshold must be positive")
        if self.medium_move_threshold >= self.high_move_threshold:
            raise ValueError("medium_move_threshold must be below high_move_threshold")
        if self.high_move_threshold >= self.extreme_move_threshold:
            raise ValueError("high_move_threshold must be below extreme_move_threshold")
        require_paper_only_flags("MarketProbabilityRegimeShiftDigestConfig", self)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftInput:
    condition_id: str
    category: str
    probability_before: Decimal
    probability_after: Decimal
    liquidity_confirmation_score: Decimal
    observed_at: datetime
    source_observed_at: datetime
    source_config_version: str
    source_reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftInput:
            raise TypeError("MarketProbabilityRegimeShiftInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftInput:
            raise ValueError("input must be exactly MarketProbabilityRegimeShiftInput")
        _require_identifier("condition_id", self.condition_id)
        _require_identifier("category", self.category)
        for field_name in (
            "probability_before",
            "probability_after",
            "liquidity_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.source_reference is not None:
            _require_canonical_string("source_reference", self.source_reference)
        require_paper_only_flags("MarketProbabilityRegimeShiftInput", self)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftReasonCodeCount:
    reason_code: str
    condition_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftReasonCodeCount:
            raise TypeError(
                "MarketProbabilityRegimeShiftReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketProbabilityRegimeShiftReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "condition_count",
            _normalize_nonnegative_whole_decimal("condition_count", self.condition_count),
        )
        require_paper_only_flags("MarketProbabilityRegimeShiftReasonCodeCount", self)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftRow:
    condition_id: str
    category: str
    observed_at: datetime
    probability_before: Decimal
    probability_after: Decimal
    recent_probability_move: Decimal
    volatility_bucket: str
    liquidity_confirmation_score: Decimal
    liquidity_confirmed: bool
    source_observed_at: datetime
    source_age_seconds: Decimal
    source_freshness_status: str
    source_config_version: str
    redacted_source_reference: str | None
    regime_shift_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftRow:
            raise TypeError("MarketProbabilityRegimeShiftRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftRow:
            raise ValueError("row must be exactly MarketProbabilityRegimeShiftRow")
        _require_identifier("condition_id", self.condition_id)
        _require_identifier("category", self.category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_before",
            "probability_after",
            "recent_probability_move",
            "liquidity_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_bucket("volatility_bucket", self.volatility_bucket)
        if type(self.liquidity_confirmed) is not bool:
            raise ValueError("liquidity_confirmed must be a bool")
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_source_freshness_status(
            "source_freshness_status",
            self.source_freshness_status,
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.redacted_source_reference is not None:
            _require_canonical_string(
                "redacted_source_reference",
                self.redacted_source_reference,
            )
        _require_status("regime_shift_status", self.regime_shift_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("MarketProbabilityRegimeShiftRow", self)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftCategoryRollup:
    category: str
    condition_count: Decimal
    shifted_condition_count: Decimal
    liquidity_confirmed_shift_count: Decimal
    unconfirmed_shift_count: Decimal
    stale_source_condition_count: Decimal
    max_recent_probability_move: Decimal | None
    category_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftCategoryRollup:
            raise TypeError(
                "MarketProbabilityRegimeShiftCategoryRollup does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftCategoryRollup:
            raise ValueError(
                "category rollup must be exactly "
                "MarketProbabilityRegimeShiftCategoryRollup",
            )
        _require_identifier("category", self.category)
        for field_name in (
            "condition_count",
            "shifted_condition_count",
            "liquidity_confirmed_shift_count",
            "unconfirmed_shift_count",
            "stale_source_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recent_probability_move",
            _normalize_optional_probability(
                "max_recent_probability_move",
                self.max_recent_probability_move,
            ),
        )
        _require_category_status("category_status", self.category_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_category_rollup(self)
        require_paper_only_flags("MarketProbabilityRegimeShiftCategoryRollup", self)


@dataclass(frozen=True)
class MarketProbabilityRegimeShiftDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    condition_count: Decimal
    category_count: Decimal
    shifted_condition_count: Decimal
    liquidity_confirmed_shift_count: Decimal
    unconfirmed_shift_count: Decimal
    stale_source_condition_count: Decimal
    max_recent_probability_move: Decimal | None
    max_source_age_seconds: Decimal | None
    rows: tuple[MarketProbabilityRegimeShiftRow, ...]
    category_rollups: tuple[MarketProbabilityRegimeShiftCategoryRollup, ...]
    reason_code_counts: tuple[MarketProbabilityRegimeShiftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityRegimeShiftDigestReport:
            raise TypeError(
                "MarketProbabilityRegimeShiftDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityRegimeShiftDigestReport:
            raise ValueError("report must be exactly MarketProbabilityRegimeShiftDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "condition_count",
            "category_count",
            "shifted_condition_count",
            "liquidity_confirmed_shift_count",
            "unconfirmed_shift_count",
            "stale_source_condition_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recent_probability_move",
            _normalize_optional_probability(
                "max_recent_probability_move",
                self.max_recent_probability_move,
            ),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("MarketProbabilityRegimeShiftDigestReport", self)
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


def build_market_probability_regime_shift_digest(
    inputs: Iterable[MarketProbabilityRegimeShiftInput],
    *,
    config: MarketProbabilityRegimeShiftDigestConfig,
    generated_at: datetime,
) -> MarketProbabilityRegimeShiftDigestReport:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    if type(config) is not MarketProbabilityRegimeShiftDigestConfig:
        raise ValueError("config must be a MarketProbabilityRegimeShiftDigestConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    require_paper_only_flags("MarketProbabilityRegimeShiftDigestConfig", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    try:
        input_items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    _validate_inputs(input_items)

    rows = _build_rows(input_items, config=config, generated_at=generated_at_utc)
    category_rollups = _category_rollups_from_rows(rows)
    reason_codes = _digest_reason_codes(rows)
    digest_status = _digest_status(rows)
    return MarketProbabilityRegimeShiftDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        condition_count=Decimal(len(rows)),
        category_count=Decimal(len(category_rollups)),
        shifted_condition_count=_shifted_condition_count(rows),
        liquidity_confirmed_shift_count=_liquidity_confirmed_shift_count(rows),
        unconfirmed_shift_count=_unconfirmed_shift_count(rows),
        stale_source_condition_count=_stale_source_condition_count(rows),
        max_recent_probability_move=_max_optional_decimal(
            row.recent_probability_move for row in rows
        ),
        max_source_age_seconds=_max_optional_decimal(row.source_age_seconds for row in rows),
        rows=rows,
        category_rollups=category_rollups,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_probability_regime_shift_digest_json_payload(
    report: MarketProbabilityRegimeShiftDigestReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is MarketProbabilityRegimeShiftDigestReport:
        require_paper_only_flags("MarketProbabilityRegimeShiftDigestReport", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload("MarketProbabilityRegimeShiftDigestReport", payload)
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("market probability regime shift payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a MarketProbabilityRegimeShiftDigestReport")


def _report_payload_without_digest(
    report: MarketProbabilityRegimeShiftDigestReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "condition_count": _count_decimal_string(report.condition_count),
        "category_count": _count_decimal_string(report.category_count),
        "shifted_condition_count": _count_decimal_string(report.shifted_condition_count),
        "liquidity_confirmed_shift_count": _count_decimal_string(
            report.liquidity_confirmed_shift_count,
        ),
        "unconfirmed_shift_count": _count_decimal_string(report.unconfirmed_shift_count),
        "stale_source_condition_count": _count_decimal_string(
            report.stale_source_condition_count,
        ),
        "max_recent_probability_move": _optional_decimal_string(
            report.max_recent_probability_move,
        ),
        "max_source_age_seconds": _optional_decimal_string(report.max_source_age_seconds),
        "rows": [
            {
                "condition_id": row.condition_id,
                "category": row.category,
                "observed_at": row.observed_at.isoformat(),
                "probability_before": _decimal_string(row.probability_before),
                "probability_after": _decimal_string(row.probability_after),
                "recent_probability_move": _decimal_string(row.recent_probability_move),
                "volatility_bucket": row.volatility_bucket,
                "liquidity_confirmation_score": _decimal_string(
                    row.liquidity_confirmation_score,
                ),
                "liquidity_confirmed": row.liquidity_confirmed,
                "source_observed_at": row.source_observed_at.isoformat(),
                "source_age_seconds": _decimal_string(row.source_age_seconds),
                "source_freshness_status": row.source_freshness_status,
                "source_config_version": row.source_config_version,
                "redacted_source_reference": row.redacted_source_reference,
                "regime_shift_status": row.regime_shift_status,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "category_rollups": [
            {
                "category": rollup.category,
                "condition_count": _count_decimal_string(rollup.condition_count),
                "shifted_condition_count": _count_decimal_string(
                    rollup.shifted_condition_count,
                ),
                "liquidity_confirmed_shift_count": _count_decimal_string(
                    rollup.liquidity_confirmed_shift_count,
                ),
                "unconfirmed_shift_count": _count_decimal_string(
                    rollup.unconfirmed_shift_count,
                ),
                "stale_source_condition_count": _count_decimal_string(
                    rollup.stale_source_condition_count,
                ),
                "max_recent_probability_move": _optional_decimal_string(
                    rollup.max_recent_probability_move,
                ),
                "category_status": rollup.category_status,
                "reason_codes": list(rollup.reason_codes),
                "paper_only": rollup.paper_only,
                "report_only": rollup.report_only,
                "readonly": rollup.readonly,
            }
            for rollup in report.category_rollups
        ],
        "reason_code_counts": [
            {
                "reason_code": reason_count.reason_code,
                "condition_count": _count_decimal_string(reason_count.condition_count),
                "paper_only": reason_count.paper_only,
                "report_only": reason_count.report_only,
                "readonly": reason_count.readonly,
            }
            for reason_count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_report_derived_validation_digest(
    report: MarketProbabilityRegimeShiftDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: MarketProbabilityRegimeShiftDigestReport,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("market_probability_regime_shift_digest_derived", values)


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(item)}" for key, item in sorted(value.items())
        ) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("derived_validation_digest payload contains unsupported value")


def _sha256(namespace: str, values: tuple[str, ...]) -> str:
    material = "\n".join((namespace, *values)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    missing_fields = sorted(set(PUBLIC_PAYLOAD_FIELDS) - set(payload))
    if missing_fields:
        raise ValueError(f"public payload missing field: {missing_fields[0]}")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    generated_at = _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    _require_status("digest_status", payload["digest_status"])
    _require_canonical_string("recommended_next_step", payload["recommended_next_step"])
    condition_count = _require_count_payload_string(
        "condition_count",
        payload["condition_count"],
    )
    category_count = _require_count_payload_string("category_count", payload["category_count"])
    shifted_condition_count = _require_count_payload_string(
        "shifted_condition_count",
        payload["shifted_condition_count"],
    )
    liquidity_confirmed_shift_count = _require_count_payload_string(
        "liquidity_confirmed_shift_count",
        payload["liquidity_confirmed_shift_count"],
    )
    unconfirmed_shift_count = _require_count_payload_string(
        "unconfirmed_shift_count",
        payload["unconfirmed_shift_count"],
    )
    stale_source_condition_count = _require_count_payload_string(
        "stale_source_condition_count",
        payload["stale_source_condition_count"],
    )
    max_recent_probability_move = _require_optional_probability_payload_string(
        "max_recent_probability_move",
        payload["max_recent_probability_move"],
    )
    max_source_age_seconds = _require_optional_nonnegative_payload_string(
        "max_source_age_seconds",
        payload["max_source_age_seconds"],
    )
    rows = _require_public_rows(payload["rows"])
    category_rollups = _require_public_category_rollups(payload["category_rollups"])
    reason_code_counts = _require_public_reason_code_counts(payload["reason_code_counts"])
    reason_codes = _require_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("public payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    MarketProbabilityRegimeShiftDigestReport(
        generated_at=generated_at,
        config_version=payload["config_version"],
        digest_status=payload["digest_status"],
        recommended_next_step=payload["recommended_next_step"],
        condition_count=condition_count,
        category_count=category_count,
        shifted_condition_count=shifted_condition_count,
        liquidity_confirmed_shift_count=liquidity_confirmed_shift_count,
        unconfirmed_shift_count=unconfirmed_shift_count,
        stale_source_condition_count=stale_source_condition_count,
        max_recent_probability_move=max_recent_probability_move,
        max_source_age_seconds=max_source_age_seconds,
        rows=rows,
        category_rollups=category_rollups,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        derived_validation_digest=provided_digest,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _require_public_rows(value: object) -> tuple[MarketProbabilityRegimeShiftRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[MarketProbabilityRegimeShiftRow] = []
    row_fields = {
        "condition_id",
        "category",
        "observed_at",
        "probability_before",
        "probability_after",
        "recent_probability_move",
        "volatility_bucket",
        "liquidity_confirmation_score",
        "liquidity_confirmed",
        "source_observed_at",
        "source_age_seconds",
        "source_freshness_status",
        "source_config_version",
        "redacted_source_reference",
        "regime_shift_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    for item in value:
        item_dict = _require_public_object("rows", item, row_fields)
        redacted_source_reference = item_dict["redacted_source_reference"]
        if redacted_source_reference is not None:
            _require_canonical_string(
                "redacted_source_reference",
                redacted_source_reference,
            )
        rows.append(
            MarketProbabilityRegimeShiftRow(
                condition_id=item_dict["condition_id"],
                category=item_dict["category"],
                observed_at=_require_datetime_payload_string(
                    "rows observed_at",
                    item_dict["observed_at"],
                ),
                probability_before=_require_probability_payload_string(
                    "rows probability_before",
                    item_dict["probability_before"],
                ),
                probability_after=_require_probability_payload_string(
                    "rows probability_after",
                    item_dict["probability_after"],
                ),
                recent_probability_move=_require_probability_payload_string(
                    "rows recent_probability_move",
                    item_dict["recent_probability_move"],
                ),
                volatility_bucket=item_dict["volatility_bucket"],
                liquidity_confirmation_score=_require_probability_payload_string(
                    "rows liquidity_confirmation_score",
                    item_dict["liquidity_confirmation_score"],
                ),
                liquidity_confirmed=_require_bool_payload(
                    "rows liquidity_confirmed",
                    item_dict["liquidity_confirmed"],
                ),
                source_observed_at=_require_datetime_payload_string(
                    "rows source_observed_at",
                    item_dict["source_observed_at"],
                ),
                source_age_seconds=_require_nonnegative_payload_string(
                    "rows source_age_seconds",
                    item_dict["source_age_seconds"],
                ),
                source_freshness_status=item_dict["source_freshness_status"],
                source_config_version=item_dict["source_config_version"],
                redacted_source_reference=redacted_source_reference,
                regime_shift_status=item_dict["regime_shift_status"],
                reason_codes=_require_public_reason_codes(
                    "rows reason_codes",
                    item_dict["reason_codes"],
                ),
                paper_only=item_dict["paper_only"],
                report_only=item_dict["report_only"],
                readonly=item_dict["readonly"],
            ),
        )
    return tuple(rows)


def _require_public_category_rollups(
    value: object,
) -> tuple[MarketProbabilityRegimeShiftCategoryRollup, ...]:
    if type(value) is not list:
        raise ValueError("category_rollups must be a list")
    rollups: list[MarketProbabilityRegimeShiftCategoryRollup] = []
    rollup_fields = {
        "category",
        "condition_count",
        "shifted_condition_count",
        "liquidity_confirmed_shift_count",
        "unconfirmed_shift_count",
        "stale_source_condition_count",
        "max_recent_probability_move",
        "category_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    for item in value:
        item_dict = _require_public_object("category_rollups", item, rollup_fields)
        rollups.append(
            MarketProbabilityRegimeShiftCategoryRollup(
                category=item_dict["category"],
                condition_count=_require_count_payload_string(
                    "category_rollups condition_count",
                    item_dict["condition_count"],
                ),
                shifted_condition_count=_require_count_payload_string(
                    "category_rollups shifted_condition_count",
                    item_dict["shifted_condition_count"],
                ),
                liquidity_confirmed_shift_count=_require_count_payload_string(
                    "category_rollups liquidity_confirmed_shift_count",
                    item_dict["liquidity_confirmed_shift_count"],
                ),
                unconfirmed_shift_count=_require_count_payload_string(
                    "category_rollups unconfirmed_shift_count",
                    item_dict["unconfirmed_shift_count"],
                ),
                stale_source_condition_count=_require_count_payload_string(
                    "category_rollups stale_source_condition_count",
                    item_dict["stale_source_condition_count"],
                ),
                max_recent_probability_move=_require_optional_probability_payload_string(
                    "category_rollups max_recent_probability_move",
                    item_dict["max_recent_probability_move"],
                ),
                category_status=item_dict["category_status"],
                reason_codes=_require_public_reason_codes(
                    "category_rollups reason_codes",
                    item_dict["reason_codes"],
                ),
                paper_only=item_dict["paper_only"],
                report_only=item_dict["report_only"],
                readonly=item_dict["readonly"],
            ),
        )
    return tuple(rollups)


def _require_public_reason_code_counts(
    value: object,
) -> tuple[MarketProbabilityRegimeShiftReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    counts: list[MarketProbabilityRegimeShiftReasonCodeCount] = []
    count_fields = {
        "reason_code",
        "condition_count",
        "paper_only",
        "report_only",
        "readonly",
    }
    for item in value:
        item_dict = _require_public_object("reason_code_counts", item, count_fields)
        counts.append(
            MarketProbabilityRegimeShiftReasonCodeCount(
                reason_code=item_dict["reason_code"],
                condition_count=_require_count_payload_string(
                    "reason_code_counts condition_count",
                    item_dict["condition_count"],
                ),
                paper_only=item_dict["paper_only"],
                report_only=item_dict["report_only"],
                readonly=item_dict["readonly"],
            ),
        )
    return tuple(counts)


def _require_public_object(
    label: str,
    value: object,
    expected_fields: set[str],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must contain objects")
    missing_fields = sorted(expected_fields - set(value))
    if missing_fields:
        raise ValueError(f"{label} missing field: {missing_fields[0]}")
    extra_fields = sorted(set(value) - expected_fields)
    if extra_fields:
        raise ValueError(f"unexpected {label} field: {extra_fields[0]}")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _has_risky_text(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if type(value) is float:
        raise ValueError(f"{label} must not contain float values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_risky_text(key):
                raise ValueError(f"unsafe field in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_risky_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in RISKY_TEXT_FRAGMENTS)


def _require_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return reason_codes


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_optional_probability_payload_string(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_payload_string(field_name, value)


def _require_probability_payload_string(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_payload_string(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _require_optional_nonnegative_payload_string(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_payload_string(field_name, value)


def _require_count_payload_string(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_payload_string(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    return decimal_value


def _require_nonnegative_payload_string(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal_payload_string(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(decimal_value)


def _require_bool_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


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


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _validate_inputs(inputs: tuple[MarketProbabilityRegimeShiftInput, ...]) -> None:
    seen_condition_ids: set[str] = set()
    for input_row in inputs:
        if type(input_row) is not MarketProbabilityRegimeShiftInput:
            raise ValueError(
                "inputs must contain MarketProbabilityRegimeShiftInput values",
            )
        require_paper_only_flags("MarketProbabilityRegimeShiftInput", input_row)
        if input_row.condition_id in seen_condition_ids:
            raise ValueError("inputs must use unique condition_id values")
        seen_condition_ids.add(input_row.condition_id)


def _build_rows(
    inputs: tuple[MarketProbabilityRegimeShiftInput, ...],
    *,
    config: MarketProbabilityRegimeShiftDigestConfig,
    generated_at: datetime,
) -> tuple[MarketProbabilityRegimeShiftRow, ...]:
    rows: list[MarketProbabilityRegimeShiftRow] = []
    for input_row in sorted(inputs, key=lambda row: (row.category, row.condition_id)):
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if input_row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        recent_probability_move = _absolute_change(
            input_row.probability_before,
            input_row.probability_after,
        )
        volatility_bucket = _volatility_bucket(recent_probability_move, config)
        source_age_seconds = _normalize_nonnegative_decimal(
            "source_age_seconds",
            Decimal(str((generated_at - input_row.source_observed_at).total_seconds())),
        )
        source_freshness_status = (
            STALE_STATUS
            if source_age_seconds >= config.stale_source_seconds_threshold
            else FRESH_STATUS
        )
        liquidity_confirmed = (
            recent_probability_move >= config.medium_move_threshold
            and input_row.liquidity_confirmation_score
            >= config.liquidity_confirmation_threshold
        )
        reason_codes = _row_reason_codes(
            volatility_bucket=volatility_bucket,
            liquidity_confirmed=liquidity_confirmed,
            source_freshness_status=source_freshness_status,
        )
        rows.append(
            MarketProbabilityRegimeShiftRow(
                condition_id=input_row.condition_id,
                category=input_row.category,
                observed_at=input_row.observed_at,
                probability_before=input_row.probability_before,
                probability_after=input_row.probability_after,
                recent_probability_move=recent_probability_move,
                volatility_bucket=volatility_bucket,
                liquidity_confirmation_score=input_row.liquidity_confirmation_score,
                liquidity_confirmed=liquidity_confirmed,
                source_observed_at=input_row.source_observed_at,
                source_age_seconds=source_age_seconds,
                source_freshness_status=source_freshness_status,
                source_config_version=input_row.source_config_version,
                redacted_source_reference=_redacted_reference(input_row.source_reference),
                regime_shift_status=_row_status(
                    volatility_bucket=volatility_bucket,
                    source_freshness_status=source_freshness_status,
                ),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _volatility_bucket(
    recent_probability_move: Decimal,
    config: MarketProbabilityRegimeShiftDigestConfig,
) -> str:
    if recent_probability_move >= config.extreme_move_threshold:
        return EXTREME_BUCKET
    if recent_probability_move >= config.high_move_threshold:
        return HIGH_BUCKET
    if recent_probability_move >= config.medium_move_threshold:
        return MEDIUM_BUCKET
    return STABLE_BUCKET


def _row_reason_codes(
    *,
    volatility_bucket: str,
    liquidity_confirmed: bool,
    source_freshness_status: str,
) -> tuple[str, ...]:
    if volatility_bucket == STABLE_BUCKET and source_freshness_status == FRESH_STATUS:
        return (STABLE_REASON,)
    reason_codes: list[str] = []
    if volatility_bucket == EXTREME_BUCKET:
        reason_codes.append(EXTREME_MOVE_REASON)
    elif volatility_bucket == HIGH_BUCKET:
        reason_codes.append(HIGH_MOVE_REASON)
    elif volatility_bucket == MEDIUM_BUCKET:
        reason_codes.append(MEDIUM_MOVE_REASON)
    if volatility_bucket != STABLE_BUCKET:
        if liquidity_confirmed:
            reason_codes.append(LIQUIDITY_CONFIRMED_REASON)
        else:
            reason_codes.append(UNCONFIRMED_LIQUIDITY_REASON)
    if source_freshness_status == STALE_STATUS:
        reason_codes.append(SOURCE_STALE_REASON)
    return tuple(sorted(reason_codes))


def _row_status(*, volatility_bucket: str, source_freshness_status: str) -> str:
    if volatility_bucket == EXTREME_BUCKET:
        return BLOCKED_STATUS
    if volatility_bucket in (HIGH_BUCKET, MEDIUM_BUCKET):
        return WATCH_STATUS
    if source_freshness_status == STALE_STATUS:
        return WATCH_STATUS
    return PASS_STATUS


def _category_rollups_from_rows(
    rows: tuple[MarketProbabilityRegimeShiftRow, ...],
) -> tuple[MarketProbabilityRegimeShiftCategoryRollup, ...]:
    categories = sorted({row.category for row in rows})
    rollups: list[MarketProbabilityRegimeShiftCategoryRollup] = []
    for category in categories:
        category_rows = tuple(row for row in rows if row.category == category)
        reason_codes = tuple(
            reason_code
            for reason_code in DIGEST_REASON_CODES
            if reason_code
            in {
                row_reason_code
                for row in category_rows
                for row_reason_code in row.reason_codes
                if row_reason_code != STABLE_REASON
            }
        )
        if not reason_codes:
            reason_codes = (DIGEST_PASSED_REASON,)
        rollups.append(
            MarketProbabilityRegimeShiftCategoryRollup(
                category=category,
                condition_count=Decimal(len(category_rows)),
                shifted_condition_count=_shifted_condition_count(category_rows),
                liquidity_confirmed_shift_count=_liquidity_confirmed_shift_count(
                    category_rows,
                ),
                unconfirmed_shift_count=_unconfirmed_shift_count(category_rows),
                stale_source_condition_count=_stale_source_condition_count(category_rows),
                max_recent_probability_move=_max_optional_decimal(
                    row.recent_probability_move for row in category_rows
                ),
                category_status=_digest_status(category_rows),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rollups)


def _digest_reason_codes(rows: tuple[MarketProbabilityRegimeShiftRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in DIGEST_REASON_CODES
        if reason_code
        in {
            row_reason_code
            for row in rows
            for row_reason_code in row.reason_codes
            if row_reason_code != STABLE_REASON
        }
    )
    if not reason_codes:
        return (DIGEST_PASSED_REASON,)
    return reason_codes


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketProbabilityRegimeShiftRow, ...],
) -> tuple[MarketProbabilityRegimeShiftReasonCodeCount, ...]:
    counts: list[MarketProbabilityRegimeShiftReasonCodeCount] = []
    for reason_code in reason_codes:
        if reason_code == DIGEST_EMPTY_REASON:
            condition_count = ZERO
        elif reason_code == DIGEST_PASSED_REASON:
            condition_count = Decimal(len(rows))
        else:
            condition_count = Decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            )
        counts.append(
            MarketProbabilityRegimeShiftReasonCodeCount(
                reason_code=reason_code,
                condition_count=condition_count,
            ),
        )
    return tuple(counts)


def _validate_row(row: MarketProbabilityRegimeShiftRow) -> None:
    expected_move = _absolute_change(row.probability_before, row.probability_after)
    if row.recent_probability_move != expected_move:
        raise ValueError("recent_probability_move must match probability inputs")
    if row.volatility_bucket == STABLE_BUCKET:
        expected_status = (
            WATCH_STATUS if row.source_freshness_status == STALE_STATUS else PASS_STATUS
        )
        if row.regime_shift_status != expected_status:
            raise ValueError("stable row status must match source freshness")
        if row.liquidity_confirmed is not False:
            raise ValueError("stable rows must not be liquidity confirmed shifts")
        expected_reason_codes = (
            (SOURCE_STALE_REASON,)
            if row.source_freshness_status == STALE_STATUS
            else (STABLE_REASON,)
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("stable row reason_codes must match source freshness")
    elif row.reason_codes == (STABLE_REASON,):
        raise ValueError("shift rows must not use only the stable reason code")
    if row.source_freshness_status == STALE_STATUS and SOURCE_STALE_REASON not in row.reason_codes:
        raise ValueError("stale source rows must include stale source reason")
    if row.redacted_source_reference is not None:
        _reject_sensitive_reference(
            "redacted_source_reference",
            row.redacted_source_reference,
        )


def _validate_category_rollup(rollup: MarketProbabilityRegimeShiftCategoryRollup) -> None:
    if rollup.shifted_condition_count > rollup.condition_count:
        raise ValueError("shifted_condition_count must not exceed condition_count")
    if (
        rollup.liquidity_confirmed_shift_count + rollup.unconfirmed_shift_count
        != rollup.shifted_condition_count
    ):
        raise ValueError("liquidity counts must match shifted_condition_count")
    if rollup.stale_source_condition_count > rollup.condition_count:
        raise ValueError("stale_source_condition_count must not exceed condition_count")


def _validate_report(report: MarketProbabilityRegimeShiftDigestReport) -> None:
    if report.condition_count != Decimal(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.category_count != Decimal(len(report.category_rollups)):
        raise ValueError("category_count must match category_rollups")
    if report.shifted_condition_count != _shifted_condition_count(report.rows):
        raise ValueError("shifted_condition_count must match rows")
    if (
        report.liquidity_confirmed_shift_count
        != _liquidity_confirmed_shift_count(report.rows)
    ):
        raise ValueError("liquidity_confirmed_shift_count must match rows")
    if report.unconfirmed_shift_count != _unconfirmed_shift_count(report.rows):
        raise ValueError("unconfirmed_shift_count must match rows")
    if report.stale_source_condition_count != _stale_source_condition_count(report.rows):
        raise ValueError("stale_source_condition_count must match rows")
    if report.max_recent_probability_move != _max_optional_decimal(
        row.recent_probability_move for row in report.rows
    ):
        raise ValueError("max_recent_probability_move must match rows")
    if report.max_source_age_seconds != _max_optional_decimal(
        row.source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_rollups = _category_rollups_from_rows(report.rows)
    if report.category_rollups != expected_rollups:
        raise ValueError("category_rollups must match rows")
    expected_reason_codes = _digest_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(value: object) -> tuple[MarketProbabilityRegimeShiftRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketProbabilityRegimeShiftRow:
            raise ValueError("rows must contain MarketProbabilityRegimeShiftRow values")
        require_paper_only_flags("MarketProbabilityRegimeShiftRow", row)
    if tuple(sorted(rows, key=lambda row: (row.category, row.condition_id))) != rows:
        raise ValueError("rows must be sorted by category and condition_id")
    return rows


def _normalize_category_rollups(
    value: object,
) -> tuple[MarketProbabilityRegimeShiftCategoryRollup, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("category_rollups must be an iterable")
    try:
        rollups = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_rollups must be an iterable") from exc
    for rollup in rollups:
        if type(rollup) is not MarketProbabilityRegimeShiftCategoryRollup:
            raise ValueError("category_rollups must contain category rollups")
        require_paper_only_flags("MarketProbabilityRegimeShiftCategoryRollup", rollup)
    if tuple(sorted(rollups, key=lambda rollup: rollup.category)) != rollups:
        raise ValueError("category_rollups must be sorted by category")
    return rollups


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketProbabilityRegimeShiftReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not MarketProbabilityRegimeShiftReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason counts")
        require_paper_only_flags("MarketProbabilityRegimeShiftReasonCodeCount", count)
    if tuple(sorted(counts, key=lambda count: count.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError(f"{field_name} must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return reason_codes


def _digest_status(rows: tuple[MarketProbabilityRegimeShiftRow, ...]) -> str:
    if any(row.regime_shift_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.regime_shift_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _shifted_condition_count(rows: tuple[MarketProbabilityRegimeShiftRow, ...]) -> Decimal:
    return Decimal(sum(1 for row in rows if row.volatility_bucket != STABLE_BUCKET))


def _liquidity_confirmed_shift_count(
    rows: tuple[MarketProbabilityRegimeShiftRow, ...],
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.liquidity_confirmed))


def _unconfirmed_shift_count(rows: tuple[MarketProbabilityRegimeShiftRow, ...]) -> Decimal:
    return Decimal(
        sum(
            1
            for row in rows
            if row.volatility_bucket != STABLE_BUCKET and not row.liquidity_confirmed
        ),
    )


def _stale_source_condition_count(
    rows: tuple[MarketProbabilityRegimeShiftRow, ...],
) -> Decimal:
    return Decimal(
        sum(1 for row in rows if row.source_freshness_status == STALE_STATUS),
    )


def _max_optional_decimal(values: object) -> Decimal | None:
    decimal_values = tuple(value for value in values if value is not None)
    if not decimal_values:
        return None
    return _quantize_decimal(max(decimal_values))


def _absolute_change(before: Decimal, after: Decimal) -> Decimal:
    return _quantize_decimal(abs(after - before))


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_identifier(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if not all(char.islower() or char.isdigit() or char in ("_", "-", ".") for char in value):
        raise ValueError(f"{field_name} must use lowercase identifier characters")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_bucket(field_name: str, value: str) -> None:
    if value not in VOLATILITY_BUCKETS:
        raise ValueError(f"{field_name} must be a known volatility bucket")


def _require_source_freshness_status(field_name: str, value: str) -> None:
    if value not in SOURCE_FRESHNESS_STATUSES:
        raise ValueError(f"{field_name} must be a known source freshness status")


def _require_status(field_name: str, value: str) -> None:
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_category_status(field_name: str, value: str) -> None:
    if value not in CATEGORY_STATUSES:
        raise ValueError(f"{field_name} must be a known category status")


def _redacted_reference(value: str | None) -> str | None:
    if value is None:
        return None
    _require_canonical_string("source_reference", value)
    if _is_sensitive_reference(value):
        return REDACTED_VALUE
    return value


def _reject_sensitive_reference(field_name: str, value: str) -> None:
    if value == REDACTED_VALUE:
        return
    if _is_sensitive_reference(value):
        raise ValueError(f"{field_name} contains a disallowed value")


def _is_sensitive_reference(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_REFERENCE_FRAGMENTS)


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def _count_decimal_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return format(value, ".0f")
    return _decimal_string(value)


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)
