"""Pure in-memory market close acknowledgement recheck coverage report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.market_close_acknowledgement_recheck_report import (
    MarketCloseAcknowledgementRecheckRow,
)
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_COVERAGE_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-coverage-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STALE_ACKNOWLEDGEMENT_REASON = (
    "market_close_acknowledgement_recheck_stale_acknowledgement"
)

CLEAR_REASON = "market_close_acknowledgement_recheck_coverage_clear"
CLOSE_TIME_BUCKET_GAP_REASON = "close_time_bucket_coverage_gap"
ACK_COVERAGE_GAP_REASON = "acknowledgement_coverage_gap"
MISSING_ACK_COVERAGE_GAP_REASON = "missing_acknowledgement_coverage_gap"
STALE_RECHECK_COVERAGE_GAP_REASON = "stale_recheck_coverage_gap"
REASON_CODE_SEQUENCE = (
    CLOSE_TIME_BUCKET_GAP_REASON,
    ACK_COVERAGE_GAP_REASON,
    MISSING_ACK_COVERAGE_GAP_REASON,
    STALE_RECHECK_COVERAGE_GAP_REASON,
    CLEAR_REASON,
)

REPORT_STATUSES = ("ready", "watch", "blocked")
BUCKET_STATUSES = ("ready", "watch", "blocked")
ACK_COVERAGE_STATUSES = ("not_covered", "covered")
MISSING_ACK_STATUSES = ("missing", "present")
STALE_RECHECK_STATUSES = ("stale", "fresh")

ACK_COVERAGE_RANK = {"not_covered": 0, "covered": 1}
MISSING_ACK_RANK = {"missing": 0, "present": 1}
STALE_RECHECK_RANK = {"stale": 0, "fresh": 1}


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckCoverageConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_COVERAGE_CONFIG_VERSION
    close_time_bucket_bounds_seconds: tuple[Decimal, ...] = (
        Decimal("3600.000000"),
        Decimal("7200.000000"),
        Decimal("14400.000000"),
    )
    min_ack_coverage_ratio: Decimal = Decimal("0.750000")
    max_missing_ack_ratio: Decimal = Decimal("0.000000")
    max_stale_recheck_ratio: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "close_time_bucket_bounds_seconds",
            _normalize_bucket_bounds(self.close_time_bucket_bounds_seconds),
        )
        for field_name in (
            "min_ack_coverage_ratio",
            "max_missing_ack_ratio",
            "max_stale_recheck_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("coverage config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow:
    close_time_bucket_label: str
    bucket_status: str
    source_row_count: Decimal
    coverage_ratio: Decimal
    ack_covered_count: Decimal
    missing_ack_count: Decimal
    stale_recheck_count: Decimal
    max_market_close_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "close_time_bucket_label",
            self.close_time_bucket_label,
        )
        _require_member("bucket_status", self.bucket_status, BUCKET_STATUSES)
        for field_name in (
            "source_row_count",
            "ack_covered_count",
            "missing_ack_count",
            "stale_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "max_market_close_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_close_time_bucket_row(self)
        require_paper_only_flags("close time bucket coverage row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckAckCoverageRow:
    ack_coverage_status: str
    source_row_count: Decimal
    coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member(
            "ack_coverage_status",
            self.ack_coverage_status,
            ACK_COVERAGE_STATUSES,
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_count_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio_decimal("coverage_ratio", self.coverage_ratio),
        )
        require_paper_only_flags("ack coverage row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckMissingAckCoverageRow:
    missing_ack_status: str
    source_row_count: Decimal
    coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member(
            "missing_ack_status",
            self.missing_ack_status,
            MISSING_ACK_STATUSES,
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_count_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio_decimal("coverage_ratio", self.coverage_ratio),
        )
        require_paper_only_flags("missing ack coverage row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckStaleCoverageRow:
    stale_recheck_status: str
    source_row_count: Decimal
    coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member(
            "stale_recheck_status",
            self.stale_recheck_status,
            STALE_RECHECK_STATUSES,
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_count_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio_decimal("coverage_ratio", self.coverage_ratio),
        )
        require_paper_only_flags("stale recheck coverage row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckCoverageReport:
    generated_at: datetime
    config_version: str
    config_close_time_bucket_bounds_seconds: tuple[Decimal, ...]
    min_ack_coverage_ratio: Decimal
    max_missing_ack_ratio: Decimal
    max_stale_recheck_ratio: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    source_row_count: Decimal
    close_time_bucket_count: Decimal
    covered_close_time_bucket_count: Decimal
    close_time_bucket_coverage_ratio: Decimal
    ack_covered_count: Decimal
    ack_coverage_ratio: Decimal
    missing_ack_count: Decimal
    missing_ack_ratio: Decimal
    stale_recheck_count: Decimal
    stale_recheck_ratio: Decimal
    max_market_close_age_seconds: Decimal
    max_acknowledgement_age_seconds: Decimal
    close_time_bucket_rows: tuple[
        MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow,
        ...,
    ]
    ack_coverage_rows: tuple[MarketCloseAcknowledgementRecheckAckCoverageRow, ...]
    missing_ack_coverage_rows: tuple[
        MarketCloseAcknowledgementRecheckMissingAckCoverageRow,
        ...,
    ]
    stale_recheck_rows: tuple[MarketCloseAcknowledgementRecheckStaleCoverageRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "config_close_time_bucket_bounds_seconds",
            _normalize_bucket_bounds(self.config_close_time_bucket_bounds_seconds),
        )
        for field_name in (
            "min_ack_coverage_ratio",
            "max_missing_ack_ratio",
            "max_stale_recheck_ratio",
            "close_time_bucket_coverage_ratio",
            "ack_coverage_ratio",
            "missing_ack_ratio",
            "stale_recheck_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in (
            "source_row_count",
            "close_time_bucket_count",
            "covered_close_time_bucket_count",
            "ack_covered_count",
            "missing_ack_count",
            "stale_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_market_close_age_seconds",
            "max_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "close_time_bucket_rows",
            _normalize_close_time_bucket_rows(self.close_time_bucket_rows),
        )
        object.__setattr__(
            self,
            "ack_coverage_rows",
            _normalize_ack_coverage_rows(self.ack_coverage_rows),
        )
        object.__setattr__(
            self,
            "missing_ack_coverage_rows",
            _normalize_missing_ack_coverage_rows(self.missing_ack_coverage_rows),
        )
        object.__setattr__(
            self,
            "stale_recheck_rows",
            _normalize_stale_recheck_rows(self.stale_recheck_rows),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("market close ack coverage report", self)
        require_paper_only_flags("market close ack coverage report", self)


def build_market_close_acknowledgement_recheck_coverage_report(
    source_rows: Iterable[MarketCloseAcknowledgementRecheckRow],
    *,
    config: MarketCloseAcknowledgementRecheckCoverageConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckCoverageReport:
    if type(config) is not MarketCloseAcknowledgementRecheckCoverageConfig:
        raise ValueError(
            "config must be a MarketCloseAcknowledgementRecheckCoverageConfig",
        )
    require_paper_only_flags("coverage config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_source_rows(source_rows, generated_at=generated_at_utc)
    source_row_count = _decimal_count(len(rows))
    bucket_count = _decimal_count(len(config.close_time_bucket_bounds_seconds) + 1)
    close_time_bucket_rows = _close_time_bucket_rows(
        rows,
        bounds=config.close_time_bucket_bounds_seconds,
    )
    ack_coverage_rows = _ack_coverage_rows(rows)
    missing_ack_coverage_rows = _missing_ack_coverage_rows(rows)
    stale_recheck_rows = _stale_recheck_rows(rows)
    ack_covered_count = _decimal_count(sum(1 for row in rows if _ack_is_covered(row)))
    missing_ack_count = _decimal_count(sum(1 for row in rows if _ack_is_missing(row)))
    stale_recheck_count = _decimal_count(sum(1 for row in rows if _row_is_stale(row)))
    covered_close_time_bucket_count = _decimal_count(len(close_time_bucket_rows))
    close_time_bucket_coverage_ratio = _ratio(
        covered_close_time_bucket_count,
        bucket_count,
    )
    ack_coverage_ratio = _ratio(ack_covered_count, source_row_count)
    missing_ack_ratio = _ratio(missing_ack_count, source_row_count)
    stale_recheck_ratio = _ratio(stale_recheck_count, source_row_count)
    reason_codes = _report_reason_codes(
        source_row_count=source_row_count,
        close_time_bucket_count=bucket_count,
        covered_close_time_bucket_count=covered_close_time_bucket_count,
        ack_coverage_ratio=ack_coverage_ratio,
        min_ack_coverage_ratio=config.min_ack_coverage_ratio,
        missing_ack_ratio=missing_ack_ratio,
        max_missing_ack_ratio=config.max_missing_ack_ratio,
        stale_recheck_ratio=stale_recheck_ratio,
        max_stale_recheck_ratio=config.max_stale_recheck_ratio,
    )
    return MarketCloseAcknowledgementRecheckCoverageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config_close_time_bucket_bounds_seconds=config.close_time_bucket_bounds_seconds,
        min_ack_coverage_ratio=config.min_ack_coverage_ratio,
        max_missing_ack_ratio=config.max_missing_ack_ratio,
        max_stale_recheck_ratio=config.max_stale_recheck_ratio,
        report_status=_report_status(reason_codes),
        reason_codes=reason_codes,
        source_row_count=source_row_count,
        close_time_bucket_count=bucket_count,
        covered_close_time_bucket_count=covered_close_time_bucket_count,
        close_time_bucket_coverage_ratio=close_time_bucket_coverage_ratio,
        ack_covered_count=ack_covered_count,
        ack_coverage_ratio=ack_coverage_ratio,
        missing_ack_count=missing_ack_count,
        missing_ack_ratio=missing_ack_ratio,
        stale_recheck_count=stale_recheck_count,
        stale_recheck_ratio=stale_recheck_ratio,
        max_market_close_age_seconds=_max_row_decimal(rows, "market_close_age_seconds"),
        max_acknowledgement_age_seconds=_max_optional_row_decimal(
            rows,
            "acknowledgement_age_seconds",
        ),
        close_time_bucket_rows=close_time_bucket_rows,
        ack_coverage_rows=ack_coverage_rows,
        missing_ack_coverage_rows=missing_ack_coverage_rows,
        stale_recheck_rows=stale_recheck_rows,
    )


def market_close_acknowledgement_recheck_coverage_report_payload(
    report: MarketCloseAcknowledgementRecheckCoverageReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckCoverageReport:
        raise ValueError(
            "report must be a MarketCloseAcknowledgementRecheckCoverageReport",
        )
    require_paper_only_flags("market close ack coverage report", report)
    reject_unsafe_surface_fields("market close ack coverage report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


@dataclass(frozen=True)
class _BucketSignal:
    bucket_index: int
    label: str
    row: MarketCloseAcknowledgementRecheckRow


def _normalize_source_rows(
    value: Iterable[MarketCloseAcknowledgementRecheckRow],
    *,
    generated_at: datetime,
) -> tuple[MarketCloseAcknowledgementRecheckRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "source_rows must contain MarketCloseAcknowledgementRecheckRow values",
        )
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError(
            "source_rows must contain MarketCloseAcknowledgementRecheckRow values",
        ) from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckRow:
            raise ValueError(
                "source_rows must contain MarketCloseAcknowledgementRecheckRow values",
            )
        require_paper_only_flags("source row", row)
        _validate_source_row_times(row, generated_at=generated_at)
        key = (row.market_id, row.latest_update_id, row.source_id)
        if key in seen_keys:
            raise ValueError(
                "source_rows must be unique by market_id, latest_update_id, and source_id",
            )
        seen_keys.add(key)
    return tuple(sorted(rows, key=_source_row_sort_key))


def _validate_source_row_times(
    row: MarketCloseAcknowledgementRecheckRow,
    *,
    generated_at: datetime,
) -> None:
    if row.market_close_age_seconds != _seconds_between(row.market_closed_at, generated_at):
        raise ValueError("source_rows market_close_age_seconds must match generated_at")
    if row.update_age_seconds != _seconds_between(row.latest_update_at, generated_at):
        raise ValueError("source_rows update_age_seconds must match generated_at")
    if row.acknowledgement_at is None:
        if row.acknowledgement_age_seconds is not None:
            raise ValueError("source_rows acknowledgement_age_seconds requires ack time")
    elif row.acknowledgement_age_seconds != _seconds_between(
        row.acknowledgement_at,
        generated_at,
    ):
        raise ValueError("source_rows acknowledgement_age_seconds must match generated_at")


def _source_row_sort_key(
    row: MarketCloseAcknowledgementRecheckRow,
) -> tuple[str, str, str]:
    return (row.market_id, row.latest_update_id, row.source_id)


def _close_time_bucket_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
    *,
    bounds: tuple[Decimal, ...],
) -> tuple[MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow, ...]:
    grouped: dict[int, list[_BucketSignal]] = {}
    for row in rows:
        bucket_index = _bucket_index(row.market_close_age_seconds, bounds)
        grouped.setdefault(bucket_index, []).append(
            _BucketSignal(
                bucket_index=bucket_index,
                label=_bucket_label(bucket_index, bounds),
                row=row,
            ),
        )
    return tuple(
        _close_time_bucket_row(tuple(grouped[index]))
        for index in sorted(grouped)
    )


def _close_time_bucket_row(
    signals: tuple[_BucketSignal, ...],
) -> MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow:
    if not signals:
        raise ValueError("signals must not be empty")
    rows = tuple(signal.row for signal in signals)
    source_row_count = _decimal_count(len(rows))
    ack_covered_count = _decimal_count(sum(1 for row in rows if _ack_is_covered(row)))
    missing_ack_count = _decimal_count(sum(1 for row in rows if _ack_is_missing(row)))
    stale_recheck_count = _decimal_count(sum(1 for row in rows if _row_is_stale(row)))
    reason_codes = _bucket_reason_codes(
        source_row_count=source_row_count,
        ack_covered_count=ack_covered_count,
        missing_ack_count=missing_ack_count,
        stale_recheck_count=stale_recheck_count,
    )
    return MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow(
        close_time_bucket_label=signals[0].label,
        bucket_status=_bucket_status(reason_codes),
        source_row_count=source_row_count,
        coverage_ratio=_ratio(source_row_count, _decimal_count(len(rows))),
        ack_covered_count=ack_covered_count,
        missing_ack_count=missing_ack_count,
        stale_recheck_count=stale_recheck_count,
        max_market_close_age_seconds=_max_row_decimal(
            rows,
            "market_close_age_seconds",
        ),
        reason_codes=reason_codes,
    )


def _ack_coverage_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckAckCoverageRow, ...]:
    source_row_count = _decimal_count(len(rows))
    counts = {
        "not_covered": sum(1 for row in rows if not _ack_is_covered(row)),
        "covered": sum(1 for row in rows if _ack_is_covered(row)),
    }
    return tuple(
        MarketCloseAcknowledgementRecheckAckCoverageRow(
            ack_coverage_status=status,
            source_row_count=_decimal_count(count),
            coverage_ratio=_ratio(_decimal_count(count), source_row_count),
        )
        for status, count in sorted(
            counts.items(),
            key=lambda item: ACK_COVERAGE_RANK[item[0]],
        )
        if count > 0
    )


def _missing_ack_coverage_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckMissingAckCoverageRow, ...]:
    source_row_count = _decimal_count(len(rows))
    counts = {
        "missing": sum(1 for row in rows if _ack_is_missing(row)),
        "present": sum(1 for row in rows if not _ack_is_missing(row)),
    }
    return tuple(
        MarketCloseAcknowledgementRecheckMissingAckCoverageRow(
            missing_ack_status=status,
            source_row_count=_decimal_count(count),
            coverage_ratio=_ratio(_decimal_count(count), source_row_count),
        )
        for status, count in sorted(
            counts.items(),
            key=lambda item: MISSING_ACK_RANK[item[0]],
        )
        if count > 0
    )


def _stale_recheck_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckStaleCoverageRow, ...]:
    source_row_count = _decimal_count(len(rows))
    counts = {
        "stale": sum(1 for row in rows if _row_is_stale(row)),
        "fresh": sum(1 for row in rows if not _row_is_stale(row)),
    }
    return tuple(
        MarketCloseAcknowledgementRecheckStaleCoverageRow(
            stale_recheck_status=status,
            source_row_count=_decimal_count(count),
            coverage_ratio=_ratio(_decimal_count(count), source_row_count),
        )
        for status, count in sorted(
            counts.items(),
            key=lambda item: STALE_RECHECK_RANK[item[0]],
        )
        if count > 0
    )


def _ack_is_covered(row: MarketCloseAcknowledgementRecheckRow) -> bool:
    return (
        row.acknowledgement_at is not None
        and row.acknowledged_update_id == row.latest_update_id
        and row.acknowledgement_lag_seconds is not None
    )


def _ack_is_missing(row: MarketCloseAcknowledgementRecheckRow) -> bool:
    return row.acknowledgement_at is None


def _row_is_stale(row: MarketCloseAcknowledgementRecheckRow) -> bool:
    return STALE_ACKNOWLEDGEMENT_REASON in row.reason_codes


def _bucket_reason_codes(
    *,
    source_row_count: Decimal,
    ack_covered_count: Decimal,
    missing_ack_count: Decimal,
    stale_recheck_count: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if ack_covered_count == ZERO and source_row_count > ZERO:
        reasons.append(ACK_COVERAGE_GAP_REASON)
    if missing_ack_count > ZERO:
        reasons.append(MISSING_ACK_COVERAGE_GAP_REASON)
    if stale_recheck_count > ZERO:
        reasons.append(STALE_RECHECK_COVERAGE_GAP_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _bucket_status(reason_codes: tuple[str, ...]) -> str:
    if (
        MISSING_ACK_COVERAGE_GAP_REASON in reason_codes
        or ACK_COVERAGE_GAP_REASON in reason_codes
    ):
        return "blocked"
    if STALE_RECHECK_COVERAGE_GAP_REASON in reason_codes:
        return "watch"
    return "ready"


def _report_reason_codes(
    *,
    source_row_count: Decimal,
    close_time_bucket_count: Decimal,
    covered_close_time_bucket_count: Decimal,
    ack_coverage_ratio: Decimal,
    min_ack_coverage_ratio: Decimal,
    missing_ack_ratio: Decimal,
    max_missing_ack_ratio: Decimal,
    stale_recheck_ratio: Decimal,
    max_stale_recheck_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_row_count > ZERO:
        if covered_close_time_bucket_count < close_time_bucket_count:
            reasons.append(CLOSE_TIME_BUCKET_GAP_REASON)
        if ack_coverage_ratio < min_ack_coverage_ratio:
            reasons.append(ACK_COVERAGE_GAP_REASON)
        if missing_ack_ratio > max_missing_ack_ratio:
            reasons.append(MISSING_ACK_COVERAGE_GAP_REASON)
        if stale_recheck_ratio > max_stale_recheck_ratio:
            reasons.append(STALE_RECHECK_COVERAGE_GAP_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if (
        ACK_COVERAGE_GAP_REASON in reason_codes
        or MISSING_ACK_COVERAGE_GAP_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "ready"
    return "watch"


def _validate_close_time_bucket_row(
    row: MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow,
) -> None:
    if row.ack_covered_count + row.missing_ack_count > row.source_row_count:
        raise ValueError("ack counts must not exceed source_row_count")
    if row.stale_recheck_count > row.source_row_count:
        raise ValueError("stale_recheck_count must not exceed source_row_count")
    if row.coverage_ratio != ONE:
        raise ValueError("coverage_ratio must be one for represented buckets")
    if row.bucket_status != _bucket_status(row.reason_codes):
        raise ValueError("bucket_status must match reason_codes")


def _validate_report(report: MarketCloseAcknowledgementRecheckCoverageReport) -> None:
    if report.close_time_bucket_count != _decimal_count(
        len(report.config_close_time_bucket_bounds_seconds) + 1,
    ):
        raise ValueError("close_time_bucket_count must match config")
    if report.covered_close_time_bucket_count != _decimal_count(
        len(report.close_time_bucket_rows),
    ):
        raise ValueError("covered_close_time_bucket_count must match rows")
    if report.close_time_bucket_coverage_ratio != _ratio(
        report.covered_close_time_bucket_count,
        report.close_time_bucket_count,
    ):
        raise ValueError("close_time_bucket_coverage_ratio must match counts")
    if report.ack_covered_count != _sum_status_count(
        report.ack_coverage_rows,
        "covered",
        "ack_coverage_status",
    ):
        raise ValueError("ack_covered_count must match rows")
    if report.missing_ack_count != _sum_status_count(
        report.missing_ack_coverage_rows,
        "missing",
        "missing_ack_status",
    ):
        raise ValueError("missing_ack_count must match rows")
    if report.stale_recheck_count != _sum_status_count(
        report.stale_recheck_rows,
        "stale",
        "stale_recheck_status",
    ):
        raise ValueError("stale_recheck_count must match rows")
    if report.source_row_count != _sum_row_count(report.ack_coverage_rows):
        raise ValueError("source_row_count must match ack coverage rows")
    if report.source_row_count != _sum_row_count(report.missing_ack_coverage_rows):
        raise ValueError("source_row_count must match missing ack rows")
    if report.source_row_count != _sum_row_count(report.stale_recheck_rows):
        raise ValueError("source_row_count must match stale recheck rows")
    if report.ack_coverage_ratio != _ratio(
        report.ack_covered_count,
        report.source_row_count,
    ):
        raise ValueError("ack_coverage_ratio must match counts")
    if report.missing_ack_ratio != _ratio(
        report.missing_ack_count,
        report.source_row_count,
    ):
        raise ValueError("missing_ack_ratio must match counts")
    if report.stale_recheck_ratio != _ratio(
        report.stale_recheck_count,
        report.source_row_count,
    ):
        raise ValueError("stale_recheck_ratio must match counts")
    expected_reason_codes = _report_reason_codes(
        source_row_count=report.source_row_count,
        close_time_bucket_count=report.close_time_bucket_count,
        covered_close_time_bucket_count=report.covered_close_time_bucket_count,
        ack_coverage_ratio=report.ack_coverage_ratio,
        min_ack_coverage_ratio=report.min_ack_coverage_ratio,
        missing_ack_ratio=report.missing_ack_ratio,
        max_missing_ack_ratio=report.max_missing_ack_ratio,
        stale_recheck_ratio=report.stale_recheck_ratio,
        max_stale_recheck_ratio=report.max_stale_recheck_ratio,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match coverage state")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _normalize_close_time_bucket_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("close_time_bucket_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow:
            raise ValueError(
                "close_time_bucket_rows must contain close time bucket rows",
            )
        require_paper_only_flags("close time bucket coverage row", row)
        if row.close_time_bucket_label in seen:
            raise ValueError("close_time_bucket_rows must be unique")
        seen.add(row.close_time_bucket_label)
    if rows != tuple(sorted(rows, key=_close_time_bucket_row_sort_key)):
        raise ValueError("close_time_bucket_rows must be deterministic")
    return rows


def _normalize_ack_coverage_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckAckCoverageRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("ack_coverage_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckAckCoverageRow:
            raise ValueError("ack_coverage_rows must contain ack coverage rows")
        require_paper_only_flags("ack coverage row", row)
        if row.ack_coverage_status in seen:
            raise ValueError("ack_coverage_rows must be unique")
        seen.add(row.ack_coverage_status)
    if rows != tuple(sorted(rows, key=lambda row: ACK_COVERAGE_RANK[row.ack_coverage_status])):
        raise ValueError("ack_coverage_rows must be deterministic")
    return rows


def _normalize_missing_ack_coverage_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckMissingAckCoverageRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("missing_ack_coverage_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckMissingAckCoverageRow:
            raise ValueError(
                "missing_ack_coverage_rows must contain missing ack coverage rows",
            )
        require_paper_only_flags("missing ack coverage row", row)
        if row.missing_ack_status in seen:
            raise ValueError("missing_ack_coverage_rows must be unique")
        seen.add(row.missing_ack_status)
    if rows != tuple(sorted(rows, key=lambda row: MISSING_ACK_RANK[row.missing_ack_status])):
        raise ValueError("missing_ack_coverage_rows must be deterministic")
    return rows


def _normalize_stale_recheck_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckStaleCoverageRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("stale_recheck_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckStaleCoverageRow:
            raise ValueError("stale_recheck_rows must contain stale recheck rows")
        require_paper_only_flags("stale recheck coverage row", row)
        if row.stale_recheck_status in seen:
            raise ValueError("stale_recheck_rows must be unique")
        seen.add(row.stale_recheck_status)
    if rows != tuple(sorted(rows, key=lambda row: STALE_RECHECK_RANK[row.stale_recheck_status])):
        raise ValueError("stale_recheck_rows must be deterministic")
    return rows


def _close_time_bucket_row_sort_key(
    row: MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow,
) -> tuple[int, str]:
    return (_label_index(row.close_time_bucket_label), row.close_time_bucket_label)


def _label_index(label: str) -> int:
    if label.startswith("0_to_"):
        return 0
    if label.endswith("_plus_seconds"):
        return 1000000
    parts = label.split("_to_", maxsplit=1)
    if len(parts) == 2:
        return int(parts[0])
    return 1000001


def _sum_row_count(rows: Iterable[Any]) -> Decimal:
    return _decimal_count(sum(int(row.source_row_count) for row in rows))


def _sum_status_count(
    rows: Iterable[Any],
    status: str,
    status_field_name: str,
) -> Decimal:
    return _decimal_count(
        sum(
            int(row.source_row_count)
            for row in rows
            if getattr(row, status_field_name) == status
        ),
    )


def _bucket_index(age_seconds: Decimal, bounds: tuple[Decimal, ...]) -> int:
    for index, bound in enumerate(bounds):
        if age_seconds < bound:
            return index
    return len(bounds)


def _bucket_label(index: int, bounds: tuple[Decimal, ...]) -> str:
    if index == 0:
        return f"0_to_{_decimal_label(bounds[0])}_seconds"
    if index == len(bounds):
        return f"{_decimal_label(bounds[-1])}_plus_seconds"
    return f"{_decimal_label(bounds[index - 1])}_to_{_decimal_label(bounds[index])}_seconds"


def _decimal_label(value: Decimal) -> str:
    integral = value.to_integral_value()
    if value == integral:
        return str(int(integral))
    return str(value.normalize()).replace(".", "_")


def _max_row_decimal(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
    field_name: str,
) -> Decimal:
    values = tuple(getattr(row, field_name) for row in rows)
    if not values:
        return ZERO
    return max(values)


def _max_optional_row_decimal(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
    field_name: str,
) -> Decimal:
    values = tuple(getattr(row, field_name) for row in rows if getattr(row, field_name) is not None)
    if not values:
        return ZERO
    return max(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    if end_utc < start_utc:
        raise ValueError("end must be greater than or equal to start")
    delta = end_utc - start_utc
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _normalize_bucket_bounds(value: object) -> tuple[Decimal, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("close_time_bucket_bounds_seconds must be a list or tuple")
    bounds = tuple(
        _normalize_positive_decimal("close_time_bucket_bounds_seconds", item)
        for item in value
    )
    if not bounds:
        raise ValueError("close_time_bucket_bounds_seconds must not be empty")
    if any(bound != bound.to_integral_value() for bound in bounds):
        raise ValueError("close_time_bucket_bounds_seconds must be integral seconds")
    if tuple(sorted(bounds)) != bounds or len(set(bounds)) != len(bounds):
        raise ValueError("close_time_bucket_bounds_seconds must be ascending and unique")
    return bounds


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_COVERAGE_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckAckCoverageRow",
    "MarketCloseAcknowledgementRecheckCloseTimeBucketCoverageRow",
    "MarketCloseAcknowledgementRecheckCoverageConfig",
    "MarketCloseAcknowledgementRecheckCoverageReport",
    "MarketCloseAcknowledgementRecheckMissingAckCoverageRow",
    "MarketCloseAcknowledgementRecheckStaleCoverageRow",
    "build_market_close_acknowledgement_recheck_coverage_report",
    "market_close_acknowledgement_recheck_coverage_report_payload",
)
