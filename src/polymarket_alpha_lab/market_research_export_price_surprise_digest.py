"""Pure Phase 1 export-price surprise research reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_EXPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-export-price-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
SURPRISE_DIRECTIONS = ("negative", "neutral", "positive")

REASON_PREFIX = "market_research_export_price_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"

REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_RELEASE_REASON,
    MATERIAL_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_export_price_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_export_price_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_export_price_surprise_digest",
}

VALUE_QUANT = Decimal("0.000001")
RATIO_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EXPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchExportPriceSurpriseDigestConfig",
    "MarketResearchExportPriceSurpriseDigestReport",
    "MarketResearchExportPriceSurpriseDigestRow",
    "MarketResearchExportPriceSurpriseInput",
    "MarketResearchExportPriceSurpriseReasonCodeCount",
    "build_market_research_export_price_surprise_digest",
    "market_research_export_price_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchExportPriceSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EXPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    material_surprise_threshold: Decimal = Decimal("0.020000")
    high_revision_threshold: Decimal = Decimal("0.015000")
    min_source_count: Decimal = Decimal("2")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchExportPriceSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchExportPriceSurpriseDigestConfig does not support "
                "subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EXPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _normalize_positive_count_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_surprise_threshold",
            "high_revision_threshold",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        if self.material_surprise_threshold == ZERO_RATIO:
            raise ValueError("material_surprise_threshold must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchExportPriceSurpriseInput:
    release_key: str
    country_code: str
    period: str
    observed_at: datetime
    expected_price_index: Decimal
    actual_price_index: Decimal
    prior_price_index: Decimal
    surprise_ratio: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchExportPriceSurpriseInput:
            raise TypeError(
                "MarketResearchExportPriceSurpriseInput does not support subclassing",
            )
        for field_name in (
            "release_key",
            "country_code",
            "period",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_price_index",
            "actual_price_index",
            "prior_price_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchExportPriceSurpriseDigestRow:
    release_key: str
    country_code: str
    period: str
    digest_status: str
    observed_at: datetime
    release_age_seconds: Decimal
    expected_price_index: Decimal
    actual_price_index: Decimal
    prior_price_index: Decimal
    surprise_delta: Decimal
    prior_revision_delta: Decimal
    surprise_ratio: Decimal
    surprise_direction: str
    source_count: Decimal
    revision_ratio: Decimal
    base_confidence: Decimal
    final_confidence: Decimal
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchExportPriceSurpriseDigestRow:
            raise TypeError(
                "MarketResearchExportPriceSurpriseDigestRow does not support "
                "subclassing",
            )
        for field_name in (
            "release_key",
            "country_code",
            "period",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_price_index",
            "actual_price_index",
            "prior_price_index",
            "surprise_delta",
            "prior_revision_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "release_age_seconds",
            _normalize_nonnegative_count_decimal(
                "release_age_seconds",
                self.release_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "surprise_ratio",
            _normalize_signed_ratio("surprise_ratio", self.surprise_ratio),
        )
        _require_member("surprise_direction", self.surprise_direction, SURPRISE_DIRECTIONS)
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "base_confidence", "final_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchExportPriceSurpriseReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchExportPriceSurpriseReasonCodeCount:
            raise TypeError(
                "MarketResearchExportPriceSurpriseReasonCodeCount does not support "
                "subclassing",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_nonnegative_ratio("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchExportPriceSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    material_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    average_abs_surprise_ratio: Decimal
    max_abs_surprise_ratio: Decimal
    max_release_age_seconds: Decimal
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...]
    reason_code_counts: tuple[MarketResearchExportPriceSurpriseReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchExportPriceSurpriseDigestReport:
            raise TypeError(
                "MarketResearchExportPriceSurpriseDigestReport does not support "
                "subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "material_surprise_count",
            "stale_release_count",
            "thin_source_count",
            "high_revision_count",
            "average_abs_surprise_ratio",
            "max_abs_surprise_ratio",
            "max_release_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_export_price_surprise_digest(
    inputs: list[MarketResearchExportPriceSurpriseInput]
    | tuple[MarketResearchExportPriceSurpriseInput, ...],
    *,
    config: MarketResearchExportPriceSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchExportPriceSurpriseDigestReport:
    if type(config) is not MarketResearchExportPriceSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchExportPriceSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(row, config=config, generated_at=generated_at_utc)
                for row in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    input_count = _decimal_count(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows)
    return MarketResearchExportPriceSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        input_count=input_count,
        ready_count=_status_count(rows, STATUS_READY),
        watch_count=_status_count(rows, STATUS_WATCH),
        blocked_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_release_count=_reason_count(rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        average_abs_surprise_ratio=_average_abs_surprise_ratio(rows),
        max_abs_surprise_ratio=_max_abs_surprise_ratio(rows),
        max_release_age_seconds=_max_release_age_seconds(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes, input_count),
        reason_codes=reason_codes,
    )


def market_research_export_price_surprise_digest_payload(
    report: MarketResearchExportPriceSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchExportPriceSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchExportPriceSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_value(asdict(report))


def _normalize_inputs(
    inputs: list[MarketResearchExportPriceSurpriseInput]
    | tuple[MarketResearchExportPriceSurpriseInput, ...],
) -> tuple[MarketResearchExportPriceSurpriseInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchExportPriceSurpriseInput:
            raise ValueError(
                "inputs must contain MarketResearchExportPriceSurpriseInput values",
            )
        _require_hard_flags("input", row)
        key = (row.release_key, row.country_code, row.period)
        if key in seen_keys:
            raise ValueError(
                "inputs must not contain duplicate release_key country_code period "
                "values",
            )
        seen_keys.add(key)
    return rows


def _build_row(
    row: MarketResearchExportPriceSurpriseInput,
    *,
    config: MarketResearchExportPriceSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchExportPriceSurpriseDigestRow:
    release_age_seconds = _datetime_delta_seconds(generated_at, row.observed_at)
    surprise_delta = _normalize_value(
        "surprise_delta",
        row.actual_price_index - row.expected_price_index,
    )
    prior_revision_delta = _normalize_value(
        "prior_revision_delta",
        row.actual_price_index - row.prior_price_index,
    )
    reason_codes = _row_reason_codes(row, release_age_seconds, config=config)
    direction = _surprise_direction(row.surprise_ratio, reason_codes)
    digest_status = _row_status(reason_codes, row.base_confidence, config=config)
    return MarketResearchExportPriceSurpriseDigestRow(
        release_key=row.release_key,
        country_code=row.country_code,
        period=row.period,
        digest_status=digest_status,
        observed_at=row.observed_at,
        release_age_seconds=release_age_seconds,
        expected_price_index=row.expected_price_index,
        actual_price_index=row.actual_price_index,
        prior_price_index=row.prior_price_index,
        surprise_delta=surprise_delta,
        prior_revision_delta=prior_revision_delta,
        surprise_ratio=row.surprise_ratio,
        surprise_direction=direction,
        source_count=row.source_count,
        revision_ratio=row.revision_ratio,
        base_confidence=row.base_confidence,
        final_confidence=_final_confidence(row.base_confidence, reason_codes),
        signal_config_version=row.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchExportPriceSurpriseInput,
    release_age_seconds: Decimal,
    *,
    config: MarketResearchExportPriceSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if release_age_seconds > config.max_release_age_seconds:
        codes.append(STALE_RELEASE_REASON)
    if abs(row.surprise_ratio) >= config.material_surprise_threshold:
        codes.append(MATERIAL_SURPRISE_REASON)
    if row.source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if row.revision_ratio > config.high_revision_threshold:
        codes.append(HIGH_REVISION_REASON)
    if not codes:
        codes.append(READY_REASON)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in codes)


def _row_status(
    reason_codes: tuple[str, ...],
    base_confidence: Decimal,
    *,
    config: MarketResearchExportPriceSurpriseDigestConfig,
) -> str:
    if STALE_RELEASE_REASON in reason_codes or HIGH_REVISION_REASON in reason_codes:
        return STATUS_BLOCKED
    if THIN_SOURCES_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if base_confidence < config.watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_WATCH


def _final_confidence(
    base_confidence: Decimal,
    reason_codes: tuple[str, ...],
) -> Decimal:
    penalty = ZERO_RATIO
    if STALE_RELEASE_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if MATERIAL_SURPRISE_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if THIN_SOURCES_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if HIGH_REVISION_REASON in reason_codes:
        penalty += Decimal("0.100000")
    factor = ONE_RATIO - penalty
    if factor < ZERO_RATIO:
        factor = ZERO_RATIO
    return _normalize_nonnegative_ratio("final_confidence", base_confidence * factor)


def _report_reason_codes(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODE_SEQUENCE if code in present)


def _report_status(rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
    reason_codes: tuple[str, ...],
    input_count: Decimal,
) -> tuple[MarketResearchExportPriceSurpriseReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchExportPriceSurpriseReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ZERO_COUNT,
                input_ratio=ZERO_RATIO,
            ),
        )
    return tuple(
        MarketResearchExportPriceSurpriseReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            input_ratio=_ratio(_reason_count(rows, reason_code), input_count),
        )
        for reason_code in reason_codes
    )


def _row_sort_key(row: MarketResearchExportPriceSurpriseDigestRow) -> tuple[Decimal, str, str]:
    return (-abs(row.surprise_ratio), row.release_key, row.period)


def _status_count(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_abs_surprise_ratio(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_nonnegative_ratio(
        "average_abs_surprise_ratio",
        sum((abs(row.surprise_ratio) for row in rows), ZERO_RATIO)
        / _decimal_count(len(rows)),
    )


def _max_abs_surprise_ratio(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_nonnegative_ratio(
        "max_abs_surprise_ratio",
        max(abs(row.surprise_ratio) for row in rows),
    )


def _max_release_age_seconds(
    rows: tuple[MarketResearchExportPriceSurpriseDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO_VALUE
    return _normalize_nonnegative_count_decimal(
        "max_release_age_seconds",
        max(row.release_age_seconds for row in rows),
    )


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    total = seconds + microseconds
    if total < ZERO_VALUE:
        total = ZERO_VALUE
    return _normalize_nonnegative_count_decimal("release_age_seconds", total)


def _surprise_direction(
    surprise_ratio: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if MATERIAL_SURPRISE_REASON not in reason_codes:
        return "neutral"
    if surprise_ratio > ZERO_RATIO:
        return "positive"
    if surprise_ratio < ZERO_RATIO:
        return "negative"
    return "neutral"


def _validate_row(row: MarketResearchExportPriceSurpriseDigestRow) -> None:
    if row.surprise_delta != _normalize_value(
        "surprise_delta",
        row.actual_price_index - row.expected_price_index,
    ):
        raise ValueError("surprise_delta must match actual less expected")
    if row.prior_revision_delta != _normalize_value(
        "prior_revision_delta",
        row.actual_price_index - row.prior_price_index,
    ):
        raise ValueError("prior_revision_delta must match actual less prior")
    if row.surprise_direction != _surprise_direction(
        row.surprise_ratio,
        row.reason_codes,
    ):
        raise ValueError("surprise_direction must match surprise_ratio")


def _validate_report(report: MarketResearchExportPriceSurpriseDigestReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    for field_name, status in (
        ("ready_count", STATUS_READY),
        ("watch_count", STATUS_WATCH),
        ("blocked_count", STATUS_BLOCKED),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for field_name, reason_code in (
        ("material_surprise_count", MATERIAL_SURPRISE_REASON),
        ("stale_release_count", STALE_RELEASE_REASON),
        ("thin_source_count", THIN_SOURCES_REASON),
        ("high_revision_count", HIGH_REVISION_REASON),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.reason_codes != tuple(
        row.reason_code for row in report.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_rows(value: object) -> tuple[MarketResearchExportPriceSurpriseDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchExportPriceSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchExportPriceSurpriseDigestRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchExportPriceSurpriseReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    for item in counts:
        if type(item) is not MarketResearchExportPriceSurpriseReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchExportPriceSurpriseReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(VALUE_QUANT)
    if quantized < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count_decimal(field_name, value)
    if normalized == ZERO_VALUE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANT)


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    ratio = _normalize_signed_ratio(field_name, value)
    if ratio < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return ratio


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_ratio("input_ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, DIGEST_STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        with localcontext(DECIMAL_CONTEXT):
            return format(value.quantize(VALUE_QUANT), "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError(f"unsupported value for JSON conversion: {type(value).__name__}")
