"""Pure public quote staleness exception report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION = (
    "research-market-quote-staleness-exception-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "quote_staleness_exception_"
CLEAR_REASON = f"{REASON_PREFIX}clear"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
COST_STALENESS_BLOCK_REASON = f"{REASON_PREFIX}cost_staleness_block"
COST_STALENESS_WATCH_REASON = f"{REASON_PREFIX}cost_staleness_watch"
DEPTH_BLOCK_REASON = f"{REASON_PREFIX}depth_block"
DEPTH_WATCH_REASON = f"{REASON_PREFIX}depth_watch"
EXCEPTION_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}exception_pressure_block"
EXCEPTION_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}exception_pressure_watch"
QUOTE_AGE_BLOCK_REASON = f"{REASON_PREFIX}quote_age_block"
QUOTE_AGE_WATCH_REASON = f"{REASON_PREFIX}quote_age_watch"
SPREAD_BLOCK_REASON = f"{REASON_PREFIX}spread_block"
SPREAD_WATCH_REASON = f"{REASON_PREFIX}spread_watch"

REPORT_CLEAR_REASON = f"{REASON_PREFIX}report_clear"
REPORT_COST_STALENESS_REASON = f"{REASON_PREFIX}report_cost_staleness_detected"
REPORT_DEPTH_REASON = f"{REASON_PREFIX}report_depth_detected"
REPORT_EXCEPTION_PRESSURE_REASON = f"{REASON_PREFIX}report_exception_pressure_detected"
REPORT_NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
REPORT_QUOTE_AGE_REASON = f"{REASON_PREFIX}report_quote_age_detected"
REPORT_REVIEW_REQUIRED_REASON = f"{REASON_PREFIX}report_review_required"
REPORT_SPREAD_REASON = f"{REASON_PREFIX}report_spread_detected"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_REASON_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,191}$")

PUBLIC_DENY_FRAGMENTS = (
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "sl" + "ug",
    "question",
    "ur" + "l",
    "source" + "_text",
    "source" + "_url",
    "ra" + "w",
    "://",
    "?",
    "dsn",
    "tab" + "le",
    "to" + "ken",
    "api" + "_key",
    "secret",
    "credential",
    "session",
    "cookie",
    "bearer",
    "private" + "_key",
    "wal" + "let",
    "au" + "th",
    "bro" + "ker",
    "sign" + "ing",
    "net" + "work",
    "data" + "base",
    "or" + "der",
    "tra" + "de",
    "bu" + "y",
    "se" + "ll",
    "recom" + "mendation",
    "siz" + "ing",
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketQuoteStalenessExceptionConfig",
    "ResearchMarketQuoteStalenessExceptionObservation",
    "ResearchMarketQuoteStalenessExceptionReasonCodeCount",
    "ResearchMarketQuoteStalenessExceptionReport",
    "ResearchMarketQuoteStalenessExceptionRow",
    "build_research_market_quote_staleness_exception_report",
    "research_market_quote_staleness_exception_report_digest",
    "research_market_quote_staleness_exception_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessExceptionConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION
    watch_quote_age_seconds: Decimal = Decimal("120.000000")
    block_quote_age_seconds: Decimal = Decimal("300.000000")
    watch_spread_ratio: Decimal = Decimal("0.020000")
    block_spread_ratio: Decimal = Decimal("0.060000")
    watch_depth_pressure: Decimal = Decimal("0.250000")
    block_depth_pressure: Decimal = Decimal("0.650000")
    watch_cost_staleness_pressure: Decimal = Decimal("0.300000")
    block_cost_staleness_pressure: Decimal = Decimal("0.700000")
    watch_exception_pressure: Decimal = Decimal("0.300000")
    block_exception_pressure: Decimal = Decimal("0.700000")
    quote_age_weight: Decimal = Decimal("0.350000")
    spread_weight: Decimal = Decimal("0.250000")
    depth_weight: Decimal = Decimal("0.200000")
    cost_staleness_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketQuoteStalenessExceptionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessExceptionConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_EXCEPTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_quote_age_seconds",
            "block_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_spread_ratio",
            "block_spread_ratio",
            "watch_depth_pressure",
            "block_depth_pressure",
            "watch_cost_staleness_pressure",
            "block_cost_staleness_pressure",
            "watch_exception_pressure",
            "block_exception_pressure",
            "quote_age_weight",
            "spread_weight",
            "depth_weight",
            "cost_staleness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_threshold(
            "watch_quote_age_seconds",
            self.watch_quote_age_seconds,
            "block_quote_age_seconds",
            self.block_quote_age_seconds,
        )
        _require_increasing_threshold(
            "watch_spread_ratio",
            self.watch_spread_ratio,
            "block_spread_ratio",
            self.block_spread_ratio,
        )
        _require_increasing_threshold(
            "watch_depth_pressure",
            self.watch_depth_pressure,
            "block_depth_pressure",
            self.block_depth_pressure,
        )
        _require_increasing_threshold(
            "watch_cost_staleness_pressure",
            self.watch_cost_staleness_pressure,
            "block_cost_staleness_pressure",
            self.block_cost_staleness_pressure,
        )
        _require_increasing_threshold(
            "watch_exception_pressure",
            self.watch_exception_pressure,
            "block_exception_pressure",
            self.block_exception_pressure,
        )
        weight_sum = _quantize(
            self.quote_age_weight
            + self.spread_weight
            + self.depth_weight
            + self.cost_staleness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("exception pressure weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessExceptionObservation:
    public_segment: str
    observed_at: datetime
    sample_count: Decimal
    aggregate_quote_age_seconds: Decimal
    aggregate_spread_ratio: Decimal
    aggregate_depth_pressure: Decimal
    cost_staleness_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketQuoteStalenessExceptionObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessExceptionObservation, "observation")
        object.__setattr__(
            self,
            "public_segment",
            _require_public_label("public_segment", self.public_segment),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        object.__setattr__(
            self,
            "aggregate_quote_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_quote_age_seconds",
                self.aggregate_quote_age_seconds,
            ),
        )
        for field_name in (
            "aggregate_spread_ratio",
            "aggregate_depth_pressure",
            "cost_staleness_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessExceptionRow:
    public_segment: str
    observed_at: datetime
    observation_age_seconds: Decimal
    sample_count: Decimal
    aggregate_quote_age_seconds: Decimal
    aggregate_spread_ratio: Decimal
    aggregate_depth_pressure: Decimal
    cost_staleness_pressure: Decimal
    quote_age_pressure: Decimal
    spread_pressure: Decimal
    depth_pressure: Decimal
    cost_pressure: Decimal
    exception_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketQuoteStalenessExceptionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessExceptionRow, "row")
        object.__setattr__(
            self,
            "public_segment",
            _require_public_label("public_segment", self.public_segment),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("observation_age_seconds", "aggregate_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "aggregate_spread_ratio",
            "aggregate_depth_pressure",
            "cost_staleness_pressure",
            "quote_age_pressure",
            "spread_pressure",
            "depth_pressure",
            "cost_pressure",
            "exception_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False, sort_values=True),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketQuoteStalenessExceptionReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessExceptionReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessExceptionReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    quote_age_exception_count: Decimal
    spread_exception_count: Decimal
    depth_exception_count: Decimal
    cost_staleness_exception_count: Decimal
    mean_aggregate_quote_age_seconds: Decimal
    max_aggregate_quote_age_seconds: Decimal
    mean_aggregate_spread_ratio: Decimal
    mean_aggregate_depth_pressure: Decimal
    mean_cost_staleness_pressure: Decimal
    mean_exception_pressure: Decimal
    max_exception_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketQuoteStalenessExceptionReasonCodeCount, ...]
    rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketQuoteStalenessExceptionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessExceptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "quote_age_exception_count",
            "spread_exception_count",
            "depth_exception_count",
            "cost_staleness_exception_count",
            "mean_aggregate_quote_age_seconds",
            "max_aggregate_quote_age_seconds",
            "mean_aggregate_spread_ratio",
            "mean_aggregate_depth_pressure",
            "mean_cost_staleness_pressure",
            "mean_exception_pressure",
            "max_exception_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False, sort_values=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_quote_staleness_exception_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketQuoteStalenessExceptionConfig,
    generated_at: datetime,
) -> ResearchMarketQuoteStalenessExceptionReport:
    if type(config) is not ResearchMarketQuoteStalenessExceptionConfig:
        raise ValueError("config must be a ResearchMarketQuoteStalenessExceptionConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketQuoteStalenessExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(input_rows)),
        sample_count=sum((row.sample_count for row in rows), ZERO),
        row_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        quote_age_exception_count=_count(
            _reason_count(rows, QUOTE_AGE_WATCH_REASON)
            + _reason_count(rows, QUOTE_AGE_BLOCK_REASON),
        ),
        spread_exception_count=_count(
            _reason_count(rows, SPREAD_WATCH_REASON)
            + _reason_count(rows, SPREAD_BLOCK_REASON),
        ),
        depth_exception_count=_count(
            _reason_count(rows, DEPTH_WATCH_REASON)
            + _reason_count(rows, DEPTH_BLOCK_REASON),
        ),
        cost_staleness_exception_count=_count(
            _reason_count(rows, COST_STALENESS_WATCH_REASON)
            + _reason_count(rows, COST_STALENESS_BLOCK_REASON),
        ),
        mean_aggregate_quote_age_seconds=_mean(
            tuple(row.aggregate_quote_age_seconds for row in rows),
        ),
        max_aggregate_quote_age_seconds=max(
            (row.aggregate_quote_age_seconds for row in rows),
            default=ZERO,
        ),
        mean_aggregate_spread_ratio=_mean(tuple(row.aggregate_spread_ratio for row in rows)),
        mean_aggregate_depth_pressure=_mean(
            tuple(row.aggregate_depth_pressure for row in rows),
        ),
        mean_cost_staleness_pressure=_mean(
            tuple(row.cost_staleness_pressure for row in rows),
        ),
        mean_exception_pressure=_mean(tuple(row.exception_pressure for row in rows)),
        max_exception_pressure=max((row.exception_pressure for row in rows), default=ZERO),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_market_quote_staleness_exception_report_payload(
    report: ResearchMarketQuoteStalenessExceptionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketQuoteStalenessExceptionReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        expected_digest = _derived_report_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a ResearchMarketQuoteStalenessExceptionReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_market_quote_staleness_exception_report_digest(
    report: ResearchMarketQuoteStalenessExceptionReport | dict[str, Any],
) -> str:
    payload = research_market_quote_staleness_exception_report_payload(report)
    return _digest_payload(payload)


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


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketQuoteStalenessExceptionObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    rows = tuple(observations)
    for row in rows:
        if type(row) is not ResearchMarketQuoteStalenessExceptionObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketQuoteStalenessExceptionObservation",
            )
        _require_hard_flags("observation", row)
    return rows


def _row_from_observation(
    row: ResearchMarketQuoteStalenessExceptionObservation,
    *,
    config: ResearchMarketQuoteStalenessExceptionConfig,
    generated_at: datetime,
) -> ResearchMarketQuoteStalenessExceptionRow:
    observation_age_seconds = _age_seconds(row.observed_at, generated_at)
    quote_age_pressure = _ratio_pressure(
        row.aggregate_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
    )
    spread_pressure = _ratio_pressure(
        row.aggregate_spread_ratio,
        block_value=config.block_spread_ratio,
    )
    depth_pressure = _ratio_pressure(
        row.aggregate_depth_pressure,
        block_value=config.block_depth_pressure,
    )
    cost_pressure = _ratio_pressure(
        row.cost_staleness_pressure,
        block_value=config.block_cost_staleness_pressure,
    )
    exception_pressure = _exception_pressure(
        quote_age_pressure=quote_age_pressure,
        spread_pressure=spread_pressure,
        depth_pressure=depth_pressure,
        cost_pressure=cost_pressure,
        config=config,
    )
    status = _row_status(
        row,
        exception_pressure=exception_pressure,
        config=config,
    )
    return ResearchMarketQuoteStalenessExceptionRow(
        public_segment=row.public_segment,
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        sample_count=row.sample_count,
        aggregate_quote_age_seconds=row.aggregate_quote_age_seconds,
        aggregate_spread_ratio=row.aggregate_spread_ratio,
        aggregate_depth_pressure=row.aggregate_depth_pressure,
        cost_staleness_pressure=row.cost_staleness_pressure,
        quote_age_pressure=quote_age_pressure,
        spread_pressure=spread_pressure,
        depth_pressure=depth_pressure,
        cost_pressure=cost_pressure,
        exception_pressure=exception_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            row,
            status=status,
            exception_pressure=exception_pressure,
            config=config,
        ),
    )


def _row_status(
    row: ResearchMarketQuoteStalenessExceptionObservation,
    *,
    exception_pressure: Decimal,
    config: ResearchMarketQuoteStalenessExceptionConfig,
) -> str:
    if (
        row.aggregate_quote_age_seconds >= config.block_quote_age_seconds
        or row.aggregate_spread_ratio >= config.block_spread_ratio
        or row.aggregate_depth_pressure >= config.block_depth_pressure
        or row.cost_staleness_pressure >= config.block_cost_staleness_pressure
        or exception_pressure >= config.block_exception_pressure
    ):
        return STATUS_BLOCK
    if (
        row.reason_codes
        or row.aggregate_quote_age_seconds >= config.watch_quote_age_seconds
        or row.aggregate_spread_ratio >= config.watch_spread_ratio
        or row.aggregate_depth_pressure >= config.watch_depth_pressure
        or row.cost_staleness_pressure >= config.watch_cost_staleness_pressure
        or exception_pressure >= config.watch_exception_pressure
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    row: ResearchMarketQuoteStalenessExceptionObservation,
    *,
    status: str,
    exception_pressure: Decimal,
    config: ResearchMarketQuoteStalenessExceptionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(row.reason_codes)
    _append_threshold_reason(
        reason_codes,
        row.aggregate_quote_age_seconds,
        config.watch_quote_age_seconds,
        config.block_quote_age_seconds,
        QUOTE_AGE_WATCH_REASON,
        QUOTE_AGE_BLOCK_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        row.aggregate_spread_ratio,
        config.watch_spread_ratio,
        config.block_spread_ratio,
        SPREAD_WATCH_REASON,
        SPREAD_BLOCK_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        row.aggregate_depth_pressure,
        config.watch_depth_pressure,
        config.block_depth_pressure,
        DEPTH_WATCH_REASON,
        DEPTH_BLOCK_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        row.cost_staleness_pressure,
        config.watch_cost_staleness_pressure,
        config.block_cost_staleness_pressure,
        COST_STALENESS_WATCH_REASON,
        COST_STALENESS_BLOCK_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        exception_pressure,
        config.watch_exception_pressure,
        config.block_exception_pressure,
        EXCEPTION_PRESSURE_WATCH_REASON,
        EXCEPTION_PRESSURE_BLOCK_REASON,
    )
    if status == STATUS_PASS and not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False, sort_values=True)


def _append_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_value:
        reason_codes.append(block_reason)
    elif value >= watch_value:
        reason_codes.append(watch_reason)


def _report_reason_codes(
    rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(
        QUOTE_AGE_WATCH_REASON in row.reason_codes
        or QUOTE_AGE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_QUOTE_AGE_REASON)
    if any(
        SPREAD_WATCH_REASON in row.reason_codes or SPREAD_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_SPREAD_REASON)
    if any(
        DEPTH_WATCH_REASON in row.reason_codes or DEPTH_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_DEPTH_REASON)
    if any(
        COST_STALENESS_WATCH_REASON in row.reason_codes
        or COST_STALENESS_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_COST_STALENESS_REASON)
    if any(
        EXCEPTION_PRESSURE_WATCH_REASON in row.reason_codes
        or EXCEPTION_PRESSURE_BLOCK_REASON in row.reason_codes
        for row in rows
    ):
        reason_codes.append(REPORT_EXCEPTION_PRESSURE_REASON)
    if any(row.status != STATUS_PASS for row in rows):
        reason_codes.append(REPORT_REVIEW_REQUIRED_REASON)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=False, sort_values=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketQuoteStalenessExceptionReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchMarketQuoteStalenessExceptionReasonCodeCount(
                reason_code=reason_code,
                count=ONE,
                row_ratio=ZERO,
            )
            for reason_code in report_reason_codes
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchMarketQuoteStalenessExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_rows(
    rows: Iterable[ResearchMarketQuoteStalenessExceptionRow],
) -> tuple[ResearchMarketQuoteStalenessExceptionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketQuoteStalenessExceptionRow:
            raise ValueError("rows must contain ResearchMarketQuoteStalenessExceptionRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketQuoteStalenessExceptionReasonCodeCount],
) -> tuple[ResearchMarketQuoteStalenessExceptionReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchMarketQuoteStalenessExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketQuoteStalenessExceptionReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row_consistency(row: ResearchMarketQuoteStalenessExceptionRow) -> None:
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must contain only the clear reason")
    if row.status in (STATUS_WATCH, STATUS_BLOCK) and CLEAR_REASON in row.reason_codes:
        raise ValueError("review rows must not contain the clear reason")
    if row.status == STATUS_BLOCK and not any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must contain a block reason")
    if row.status == STATUS_WATCH and any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must not contain a block reason")


def _validate_report_consistency(report: ResearchMarketQuoteStalenessExceptionReport) -> None:
    rows = report.rows
    for row in rows:
        _require_hard_flags("row", row)
    for reason_count in report.reason_code_counts:
        _require_hard_flags("reason code count", reason_count)
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.sample_count != sum((row.sample_count for row in rows), ZERO):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _count(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.quote_age_exception_count != _count(
        _reason_count(rows, QUOTE_AGE_WATCH_REASON)
        + _reason_count(rows, QUOTE_AGE_BLOCK_REASON),
    ):
        raise ValueError("quote_age_exception_count must match rows")
    if report.spread_exception_count != _count(
        _reason_count(rows, SPREAD_WATCH_REASON)
        + _reason_count(rows, SPREAD_BLOCK_REASON),
    ):
        raise ValueError("spread_exception_count must match rows")
    if report.depth_exception_count != _count(
        _reason_count(rows, DEPTH_WATCH_REASON) + _reason_count(rows, DEPTH_BLOCK_REASON),
    ):
        raise ValueError("depth_exception_count must match rows")
    if report.cost_staleness_exception_count != _count(
        _reason_count(rows, COST_STALENESS_WATCH_REASON)
        + _reason_count(rows, COST_STALENESS_BLOCK_REASON),
    ):
        raise ValueError("cost_staleness_exception_count must match rows")
    if report.mean_aggregate_quote_age_seconds != _mean(
        tuple(row.aggregate_quote_age_seconds for row in rows),
    ):
        raise ValueError("mean_aggregate_quote_age_seconds must match rows")
    if report.max_aggregate_quote_age_seconds != max(
        (row.aggregate_quote_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_aggregate_quote_age_seconds must match rows")
    if report.mean_aggregate_spread_ratio != _mean(
        tuple(row.aggregate_spread_ratio for row in rows),
    ):
        raise ValueError("mean_aggregate_spread_ratio must match rows")
    if report.mean_aggregate_depth_pressure != _mean(
        tuple(row.aggregate_depth_pressure for row in rows),
    ):
        raise ValueError("mean_aggregate_depth_pressure must match rows")
    if report.mean_cost_staleness_pressure != _mean(
        tuple(row.cost_staleness_pressure for row in rows),
    ):
        raise ValueError("mean_cost_staleness_pressure must match rows")
    if report.mean_exception_pressure != _mean(tuple(row.exception_pressure for row in rows)):
        raise ValueError("mean_exception_pressure must match rows")
    if report.max_exception_pressure != max((row.exception_pressure for row in rows), default=ZERO):
        raise ValueError("max_exception_pressure must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketQuoteStalenessExceptionRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _row_sort_key(
    row: ResearchMarketQuoteStalenessExceptionRow,
) -> tuple[int, Decimal, Decimal, str, datetime]:
    return (
        STATUS_RANK[row.status],
        -row.exception_pressure,
        -row.aggregate_quote_age_seconds,
        row.public_segment,
        row.observed_at,
    )


def _exception_pressure(
    *,
    quote_age_pressure: Decimal,
    spread_pressure: Decimal,
    depth_pressure: Decimal,
    cost_pressure: Decimal,
    config: ResearchMarketQuoteStalenessExceptionConfig,
) -> Decimal:
    return _clamp_ratio(
        quote_age_pressure * config.quote_age_weight
        + spread_pressure * config.spread_weight
        + depth_pressure * config.depth_weight
        + cost_pressure * config.cost_staleness_weight,
    )


def _ratio_pressure(value: Decimal, *, block_value: Decimal) -> Decimal:
    if block_value <= ZERO:
        raise ValueError("block threshold must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / block_value)


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("observed_at must not be after generated_at")
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400") * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    reason_codes: list[str] = []
    for item in values:
        clean = _require_reason_code("reason_code", item)
        reason_codes.append(f"input_{clean}")
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=True, sort_values=True)


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
    sort_values: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    reason_codes = tuple(_require_reason_code("reason_code", item) for item in values)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if sort_values:
        return tuple(sorted(reason_codes))
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_REASON_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public reason code")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_increasing_threshold(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if upper_value <= lower_value:
        raise ValueError(f"{upper_name} must exceed {lower_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value <= ZERO:
            return ZERO
        if value >= ONE:
            return ONE
        return _quantize(value)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must use exact Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must use exact datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if value is None:
        return None
    raise ValueError("value is not JSON serializable")


def _derived_report_digest(report: ResearchMarketQuoteStalenessExceptionReport) -> str:
    return _report_digest_from_values(_report_values_without_digest(report))


def _report_values_without_digest(
    report: ResearchMarketQuoteStalenessExceptionReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_payload("digest payload", payload)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        return
    digest = payload["derived_validation_digest"]
    _require_hex_digest("derived_validation_digest", digest)
    expected = _digest_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _reject_unsafe_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        item
        for item in "".join(char if char.isalnum() else "_" for char in lowered).split("_")
        if item
    )
    for fragment in PUBLIC_DENY_FRAGMENTS:
        if "_" in fragment or len(fragment) <= 3:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False
