"""Pure Phase 1 report-only reducer for market forecast confidence rechecks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any


DEFAULT_MARKET_FORECAST_CONFIDENCE_RECHECK_DIGEST_CONFIG_VERSION = (
    "market-forecast-confidence-recheck-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600")
SECONDS_PER_DAY = 86400
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

RECHECK_STATUSES = ("pass", "watch", "blocked")
STATUS_REASON_CODES = (
    "market_forecast_confidence_recheck_pass",
    "market_forecast_confidence_recheck_watch",
    "market_forecast_confidence_recheck_blocked",
)
EMPTY_REASON_CODE = "market_forecast_confidence_recheck_empty"
PASS_REASON_CODE = "confidence_recheck_passed"
LOW_CONFIDENCE_WATCH_REASON_CODE = "low_confidence_watch"
LOW_CONFIDENCE_BLOCKED_REASON_CODE = "low_confidence_blocked"
PROBABILITY_DELTA_WATCH_REASON_CODE = "probability_delta_watch"
PROBABILITY_DELTA_BLOCKED_REASON_CODE = "probability_delta_blocked"
FORECAST_STALE_REASON_CODE = "forecast_stale"
FORECAST_EXPIRED_REASON_CODE = "forecast_expired"
EVIDENCE_COUNT_BELOW_MINIMUM_REASON_CODE = "evidence_count_below_minimum"
ROW_REASON_CODE_PRIORITY = (
    PASS_REASON_CODE,
    LOW_CONFIDENCE_WATCH_REASON_CODE,
    LOW_CONFIDENCE_BLOCKED_REASON_CODE,
    PROBABILITY_DELTA_WATCH_REASON_CODE,
    PROBABILITY_DELTA_BLOCKED_REASON_CODE,
    FORECAST_STALE_REASON_CODE,
    FORECAST_EXPIRED_REASON_CODE,
    EVIDENCE_COUNT_BELOW_MINIMUM_REASON_CODE,
)
REPORT_REASON_CODE_PRIORITY = (
    STATUS_REASON_CODES[0],
    STATUS_REASON_CODES[1],
    STATUS_REASON_CODES[2],
    *ROW_REASON_CODE_PRIORITY,
    EMPTY_REASON_CODE,
)
ROW_REASON_CODE_SET = frozenset(ROW_REASON_CODE_PRIORITY)
REPORT_REASON_CODE_SET = frozenset(REPORT_REASON_CODE_PRIORITY)
SENSITIVE_REFERENCE_FRAGMENTS = (
    "private_key",
    "secret",
    "token",
    "credential",
    "password",
)
REDACTED_REFERENCE = "<redacted>"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "forecast_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "average_confidence_score",
    "max_probability_delta",
    "status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ROW_PAYLOAD_FIELDS = (
    "market_slug",
    "forecast_id",
    "redacted_reference",
    "forecasted_at",
    "forecast_probability",
    "current_probability",
    "confidence_score",
    "evidence_count",
    "probability_delta",
    "forecast_age_hours",
    "recheck_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "li" + "ve",
    "a" + "uth",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)

__all__ = (
    "DEFAULT_MARKET_FORECAST_CONFIDENCE_RECHECK_DIGEST_CONFIG_VERSION",
    "MarketForecastConfidenceRecheckDigestConfig",
    "MarketForecastConfidenceRecheckDigestReport",
    "MarketForecastConfidenceRecheckInput",
    "MarketForecastConfidenceRecheckRow",
    "build_market_forecast_confidence_recheck_digest",
    "market_forecast_confidence_recheck_digest_payload",
)


@dataclass(frozen=True)
class MarketForecastConfidenceRecheckDigestConfig:
    config_version: str = DEFAULT_MARKET_FORECAST_CONFIDENCE_RECHECK_DIGEST_CONFIG_VERSION
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    blocked_confidence_threshold: Decimal = Decimal("0.400000")
    watch_probability_delta: Decimal = Decimal("0.080000")
    blocked_probability_delta: Decimal = Decimal("0.200000")
    stale_forecast_age_hours: Decimal = Decimal("24.000000")
    expired_forecast_age_hours: Decimal = Decimal("72.000000")
    minimum_evidence_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketForecastConfidenceRecheckDigestConfig:
            raise TypeError(
                "MarketForecastConfidenceRecheckDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketForecastConfidenceRecheckDigestConfig:
            raise ValueError(
                "config must be exactly MarketForecastConfidenceRecheckDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_confidence_threshold",
            "blocked_confidence_threshold",
            "watch_probability_delta",
            "blocked_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_forecast_age_hours", "expired_forecast_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_evidence_count",
            _normalize_count("minimum_evidence_count", self.minimum_evidence_count),
        )
        if self.blocked_confidence_threshold > self.watch_confidence_threshold:
            raise ValueError(
                "blocked_confidence_threshold must be <= watch_confidence_threshold",
            )
        if self.watch_probability_delta > self.blocked_probability_delta:
            raise ValueError(
                "watch_probability_delta must be <= blocked_probability_delta",
            )
        if self.stale_forecast_age_hours > self.expired_forecast_age_hours:
            raise ValueError("stale_forecast_age_hours must be <= expired_forecast_age_hours")
        _require_hard_flags(self)
        _reject_unsafe_public_value("config", self)


@dataclass(frozen=True)
class MarketForecastConfidenceRecheckInput:
    market_slug: str
    forecast_id: str
    forecasted_at: datetime
    forecast_probability: Decimal
    current_probability: Decimal
    confidence_score: Decimal
    evidence_count: Decimal
    reason_codes: tuple[str, ...]
    reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketForecastConfidenceRecheckInput:
            raise TypeError(
                "MarketForecastConfidenceRecheckInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketForecastConfidenceRecheckInput:
            raise ValueError("input must be exactly MarketForecastConfidenceRecheckInput")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "forecasted_at",
            _as_utc("forecasted_at", self.forecasted_at),
        )
        for field_name in (
            "forecast_probability",
            "current_probability",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_count("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        _require_hard_flags(self)
        _reject_unsafe_public_value("input", self)


@dataclass(frozen=True)
class MarketForecastConfidenceRecheckRow:
    market_slug: str
    forecast_id: str
    redacted_reference: str | None
    forecasted_at: datetime
    forecast_probability: Decimal
    current_probability: Decimal
    confidence_score: Decimal
    evidence_count: Decimal
    probability_delta: Decimal
    forecast_age_hours: Decimal
    recheck_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketForecastConfidenceRecheckRow:
            raise TypeError(
                "MarketForecastConfidenceRecheckRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketForecastConfidenceRecheckRow:
            raise ValueError("row must be exactly MarketForecastConfidenceRecheckRow")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "redacted_reference",
            _redact_reference(self.redacted_reference),
        )
        object.__setattr__(
            self,
            "forecasted_at",
            _as_utc("forecasted_at", self.forecasted_at),
        )
        for field_name in (
            "forecast_probability",
            "current_probability",
            "confidence_score",
            "probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_count("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "forecast_age_hours",
            _normalize_nonnegative_decimal("forecast_age_hours", self.forecast_age_hours),
        )
        _require_status("recheck_status", self.recheck_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)
        _reject_unsafe_public_value("row", self)


@dataclass(frozen=True)
class MarketForecastConfidenceRecheckDigestReport:
    generated_at: datetime
    config_version: str
    forecast_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_confidence_score: Decimal
    max_probability_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketForecastConfidenceRecheckRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketForecastConfidenceRecheckDigestReport:
            raise TypeError(
                "MarketForecastConfidenceRecheckDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketForecastConfidenceRecheckDigestReport:
            raise ValueError(
                "report must be exactly MarketForecastConfidenceRecheckDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("forecast_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "max_probability_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags(self)
        _reject_unsafe_public_value("report", self)
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
                _normalize_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _require_report_derived_validation_digest(self)


def build_market_forecast_confidence_recheck_digest(
    forecasts: list[MarketForecastConfidenceRecheckInput]
    | tuple[MarketForecastConfidenceRecheckInput, ...],
    *,
    config: MarketForecastConfidenceRecheckDigestConfig,
    generated_at: datetime,
) -> MarketForecastConfidenceRecheckDigestReport:
    if type(config) is not MarketForecastConfidenceRecheckDigestConfig:
        raise ValueError(
            "config must be a MarketForecastConfidenceRecheckDigestConfig",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_forecasts(forecasts)
    rows = tuple(
        sorted(
            (
                _row_from_forecast(row, config=config, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    forecast_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.recheck_status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.recheck_status == "watch"))
    blocked_count = _count(sum(1 for row in rows if row.recheck_status == "blocked"))
    average_confidence = ZERO_RATIO
    max_probability_delta = ZERO_RATIO
    if rows:
        average_confidence = _ratio(
            sum((row.confidence_score for row in rows), ZERO) / forecast_count,
        )
        max_probability_delta = max(row.probability_delta for row in rows)

    return MarketForecastConfidenceRecheckDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        forecast_count=forecast_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_confidence_score=average_confidence,
        max_probability_delta=max_probability_delta,
        status=_status_rollup(tuple(row.recheck_status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_forecast_confidence_recheck_digest_payload(
    report: MarketForecastConfidenceRecheckDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not MarketForecastConfidenceRecheckDigestReport:
        if type(report) is dict:
            _validate_public_payload(report)
            return dict(report)
        raise ValueError("report must be a MarketForecastConfidenceRecheckDigestReport")
    _require_hard_flags(report)
    _validate_report(report)
    _require_report_derived_validation_digest(report)
    _reject_unsafe_public_value("report", report)
    payload = _report_payload_without_digest(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    report: MarketForecastConfidenceRecheckDigestReport,
) -> dict[str, Any]:
    return {
        "generated_at": _format_datetime(report.generated_at),
        "config_version": report.config_version,
        "forecast_count": str(report.forecast_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "blocked_count": str(report.blocked_count),
        "average_confidence_score": str(report.average_confidence_score),
        "max_probability_delta": str(report.max_probability_delta),
        "status": report.status,
        "reason_codes": tuple(report.reason_codes),
        "rows": tuple(_row_payload(row) for row in report.rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_from_forecast(
    forecast: MarketForecastConfidenceRecheckInput,
    *,
    config: MarketForecastConfidenceRecheckDigestConfig,
    generated_at: datetime,
) -> MarketForecastConfidenceRecheckRow:
    if forecast.forecasted_at > generated_at:
        raise ValueError("forecasted_at must not be after generated_at")
    age_hours = _ratio(_timedelta_seconds(generated_at - forecast.forecasted_at) / SECONDS_PER_HOUR)
    probability_delta = _ratio(_abs_decimal(forecast.current_probability - forecast.forecast_probability))
    reason_codes: list[str] = []

    if forecast.confidence_score < config.blocked_confidence_threshold:
        reason_codes.append(LOW_CONFIDENCE_BLOCKED_REASON_CODE)
    elif forecast.confidence_score <= config.watch_confidence_threshold:
        reason_codes.append(LOW_CONFIDENCE_WATCH_REASON_CODE)

    if probability_delta >= config.blocked_probability_delta:
        reason_codes.append(PROBABILITY_DELTA_BLOCKED_REASON_CODE)
    elif probability_delta >= config.watch_probability_delta:
        reason_codes.append(PROBABILITY_DELTA_WATCH_REASON_CODE)

    if age_hours >= config.expired_forecast_age_hours:
        reason_codes.append(FORECAST_EXPIRED_REASON_CODE)
    elif age_hours >= config.stale_forecast_age_hours:
        reason_codes.append(FORECAST_STALE_REASON_CODE)

    if forecast.evidence_count < config.minimum_evidence_count:
        reason_codes.append(EVIDENCE_COUNT_BELOW_MINIMUM_REASON_CODE)

    if _blocked_reason_present(reason_codes):
        status = "blocked"
    elif reason_codes:
        status = "watch"
    else:
        status = "pass"
        reason_codes.append(PASS_REASON_CODE)

    return MarketForecastConfidenceRecheckRow(
        market_slug=forecast.market_slug,
        forecast_id=forecast.forecast_id,
        redacted_reference=forecast.reference,
        forecasted_at=forecast.forecasted_at,
        forecast_probability=forecast.forecast_probability,
        current_probability=forecast.current_probability,
        confidence_score=forecast.confidence_score,
        evidence_count=forecast.evidence_count,
        probability_delta=probability_delta,
        forecast_age_hours=age_hours,
        recheck_status=status,
        reason_codes=_row_reason_codes_by_priority(reason_codes),
    )


def _row_payload(row: MarketForecastConfidenceRecheckRow) -> dict[str, Any]:
    return {
        "market_slug": row.market_slug,
        "forecast_id": row.forecast_id,
        "redacted_reference": row.redacted_reference,
        "forecasted_at": _format_datetime(row.forecasted_at),
        "forecast_probability": str(row.forecast_probability),
        "current_probability": str(row.current_probability),
        "confidence_score": str(row.confidence_score),
        "evidence_count": str(row.evidence_count),
        "probability_delta": str(row.probability_delta),
        "forecast_age_hours": str(row.forecast_age_hours),
        "recheck_status": row.recheck_status,
        "reason_codes": tuple(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_derived_validation_digest(
    report: MarketForecastConfidenceRecheckDigestReport,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _require_report_derived_validation_digest(
    report: MarketForecastConfidenceRecheckDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("market_forecast_confidence_recheck_digest_derived", values)


def _digest_payload_value(value: object) -> str:
    if type(value) is dict:
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}"
            for key in sorted(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    return str(value)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_public_payload_fields(payload)
    _reject_unsafe_public_value("payload", payload)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    _require_count_payload_string("forecast_count", payload["forecast_count"])
    _require_count_payload_string("pass_count", payload["pass_count"])
    _require_count_payload_string("watch_count", payload["watch_count"])
    _require_count_payload_string("blocked_count", payload["blocked_count"])
    _require_ratio_payload_string(
        "average_confidence_score",
        payload["average_confidence_score"],
    )
    _require_ratio_payload_string(
        "max_probability_delta",
        payload["max_probability_delta"],
    )
    _require_status("status", payload["status"])
    _normalize_report_reason_codes(payload["reason_codes"])
    _validate_public_rows(payload["rows"])
    _require_hard_flags(_DictFlags(payload))
    digest = _normalize_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _require_public_payload_fields(payload: dict[str, Any]) -> None:
    for field_name in REPORT_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(REPORT_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_rows(value: object) -> None:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a tuple or list")
    for row in value:
        _validate_public_row(row)


def _validate_public_row(row: object) -> None:
    if type(row) is not dict:
        raise ValueError("rows must contain public row objects")
    for field_name in ROW_PAYLOAD_FIELDS:
        if field_name not in row:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(row) - set(ROW_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public row field: {extra_fields[0]}")
    _require_canonical_string("market_slug", row["market_slug"])
    _require_canonical_string("forecast_id", row["forecast_id"])
    if row["redacted_reference"] is not None:
        _require_canonical_string("redacted_reference", row["redacted_reference"])
    _require_canonical_string("forecasted_at", row["forecasted_at"])
    _require_ratio_payload_string("forecast_probability", row["forecast_probability"])
    _require_ratio_payload_string("current_probability", row["current_probability"])
    _require_ratio_payload_string("confidence_score", row["confidence_score"])
    _require_count_payload_string("evidence_count", row["evidence_count"])
    _require_ratio_payload_string("probability_delta", row["probability_delta"])
    _require_nonnegative_payload_string("forecast_age_hours", row["forecast_age_hours"])
    _require_status("recheck_status", row["recheck_status"])
    _normalize_row_reason_codes(row["reason_codes"])
    _require_hard_flags(_DictFlags(row))


class _DictFlags:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.paper_only = payload.get("paper_only")
        self.report_only = payload.get("report_only")
        self.readonly = payload.get("readonly")


def _normalize_forecasts(value: object) -> tuple[MarketForecastConfidenceRecheckInput, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("forecasts must be a tuple or list")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketForecastConfidenceRecheckInput:
            raise ValueError("forecasts must contain exact input rows")
        _require_hard_flags(row)
        key = (row.market_slug, row.forecast_id)
        if key in seen:
            raise ValueError("forecasts must be unique")
        seen.add(key)
    return rows


def _normalize_rows(value: object) -> tuple[MarketForecastConfidenceRecheckRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    previous_key: tuple[int, Decimal, str, str] | None = None
    for row in rows:
        if type(row) is not MarketForecastConfidenceRecheckRow:
            raise ValueError("rows must contain exact recheck rows")
        _require_hard_flags(row)
        key = (row.market_slug, row.forecast_id)
        if key in seen:
            raise ValueError("rows must be unique")
        seen.add(key)
        current_key = _row_sort_key(row)
        if previous_key is not None and previous_key > current_key:
            raise ValueError("rows must use deterministic sequence")
        previous_key = current_key
    return rows


def _validate_row(row: MarketForecastConfidenceRecheckRow) -> None:
    if row.probability_delta != _ratio(
        _abs_decimal(row.current_probability - row.forecast_probability),
    ):
        raise ValueError("probability_delta must match probabilities")
    if row.recheck_status != _row_status(row.reason_codes):
        raise ValueError("recheck_status must match reason_codes")


def _validate_report(report: MarketForecastConfidenceRecheckDigestReport) -> None:
    if report.forecast_count != _count(len(report.rows)):
        raise ValueError("forecast_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.recheck_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.recheck_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(sum(1 for row in report.rows if row.recheck_status == "blocked")):
        raise ValueError("blocked_count must match rows")
    expected_average = ZERO_RATIO
    expected_max_delta = ZERO_RATIO
    if report.rows:
        expected_average = _ratio(
            sum((row.confidence_score for row in report.rows), ZERO)
            / report.forecast_count,
        )
        expected_max_delta = max(row.probability_delta for row in report.rows)
    if report.average_confidence_score != expected_average:
        raise ValueError("average_confidence_score must match rows")
    if report.max_probability_delta != expected_max_delta:
        raise ValueError("max_probability_delta must match rows")
    if report.status != _status_rollup(tuple(row.recheck_status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    if statuses:
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[MarketForecastConfidenceRecheckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: list[str] = []
    reason_codes.append(STATUS_REASON_CODES[RECHECK_STATUSES.index(_status_rollup(tuple(row.recheck_status for row in rows)))])
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _report_reason_codes_by_priority(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if _blocked_reason_present(list(reason_codes)):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _blocked_reason_present(reason_codes: list[str]) -> bool:
    return any(
        reason_code
        in (
            LOW_CONFIDENCE_BLOCKED_REASON_CODE,
            PROBABILITY_DELTA_BLOCKED_REASON_CODE,
            FORECAST_EXPIRED_REASON_CODE,
            EVIDENCE_COUNT_BELOW_MINIMUM_REASON_CODE,
        )
        for reason_code in reason_codes
    )


def _row_sort_key(
    row: MarketForecastConfidenceRecheckRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {"blocked": 0, "watch": 1, "pass": 2}[row.recheck_status]
    return (status_rank, -row.probability_delta, row.market_slug, row.forecast_id)


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    rows = tuple(value)
    for reason_code in rows:
        _require_canonical_string("reason_codes", reason_code)
    if len(rows) != len(set(rows)):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(rows))


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_known_reason_codes(
        value,
        allowed=ROW_REASON_CODE_SET,
        priority=ROW_REASON_CODE_PRIORITY,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_known_reason_codes(
        value,
        allowed=REPORT_REASON_CODE_SET,
        priority=REPORT_REASON_CODE_PRIORITY,
    )


def _normalize_known_reason_codes(
    value: object,
    *,
    allowed: frozenset[str],
    priority: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    previous_position = -1
    for reason_code in rows:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in allowed:
            raise ValueError("reason_codes must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        position = priority.index(reason_code)
        if position < previous_position:
            raise ValueError("reason_codes must use priority sequence")
        previous_position = position
        seen.add(reason_code)
    return rows


def _row_reason_codes_by_priority(values: list[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_PRIORITY if reason_code in present)


def _report_reason_codes_by_priority(values: list[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(reason_code for reason_code in REPORT_REASON_CODE_PRIORITY if reason_code in present)


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _ratio(decimal_value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _ratio(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _timedelta_seconds(value: object) -> Decimal:
    days = object.__getattribute__(value, "days")
    seconds = object.__getattribute__(value, "seconds")
    microseconds = object.__getattribute__(value, "microseconds")
    return (
        Decimal(days * SECONDS_PER_DAY)
        + Decimal(seconds)
        + (Decimal(microseconds) / MICROSECONDS_PER_SECOND)
    )


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return -value
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _format_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _require_count_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    normalized = _normalize_count(field_name, Decimal(value))
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_ratio_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    normalized = _normalize_ratio(field_name, Decimal(value))
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_nonnegative_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    normalized = _normalize_nonnegative_decimal(field_name, Decimal(value))
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _normalize_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECHECK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _redact_reference(value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string("reference", value)
    reference = str(value)
    visible_reference = reference.split("#", 1)[0].split("?", 1)[0]
    if not visible_reference:
        return REDACTED_REFERENCE
    if any(fragment in visible_reference.lower() for fragment in SENSITIVE_REFERENCE_FRAGMENTS):
        return REDACTED_REFERENCE
    return visible_reference


def _reject_unsafe_public_value(field_name: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(token in lowered for token in UNSAFE_PUBLIC_TEXT_TOKENS):
            raise ValueError(f"{field_name} contains unsafe public text")
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_value(str(key), key)
            _reject_unsafe_public_value(str(key), item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_value(field_name, item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for nested_field_name in value.__dataclass_fields__:
            _reject_unsafe_public_value(
                nested_field_name,
                getattr(value, nested_field_name),
            )


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")
