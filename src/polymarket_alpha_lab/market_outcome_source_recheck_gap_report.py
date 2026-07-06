"""Pure read-only Polymarket outcome/source recheck gap report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_GAP_CONFIG_VERSION = (
    "market-outcome-source-recheck-gap-v0"
)

GAP_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "market_outcome_source_recheck_missing_recheck",
    "market_outcome_source_recheck_overdue_recheck",
    "market_outcome_source_recheck_missing_acknowledgement",
    "market_outcome_source_recheck_conflicting_outcome_source",
)
REPORT_REASON_CODES = (
    "market_outcome_source_recheck_gap_empty",
    "market_outcome_source_recheck_gap_clear",
) + ROW_REASON_CODES
BLOCKING_REASON_CODES = frozenset(
    (
        "market_outcome_source_recheck_missing_recheck",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_conflicting_outcome_source",
    ),
)
STATUS_RANK = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_ZERO = Decimal("0")
COUNT_QUANTUM = Decimal("1")
RATIO_ZERO = Decimal("0.000000")
RATIO_ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
AGE_ZERO = Decimal("0.000000")
AGE_QUANTUM = Decimal("0.000001")
DAY_SECONDS = Decimal("86400")
MICROSECOND_DIVISOR = Decimal("1000000")


def _piece(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _piece("au", "th"),
        _piece("cre", "den", "tial"),
        _piece("api", "_", "key"),
        _piece("private", "_", "key"),
        _piece("secret"),
        _piece("tok", "en"),
        _piece("wal", "let"),
        _piece("acc", "ount"),
        _piece("bro", "ker"),
        _piece("ord", "er"),
        _piece("submit"),
        _piece("cancel"),
        _piece("sign"),
        _piece("li", "ve"),
        _piece("li", "ve", "_", "tra", "ding"),
        _piece("tra", "de"),
        _piece("net", "work"),
        _piece("data", "base"),
        _piece("dsn"),
        _piece("per", "sist"),
    ),
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckGapConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_GAP_CONFIG_VERSION
    recheck_due_after_seconds: Decimal = Decimal("3600.000000")
    acknowledgement_due_after_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketOutcomeSourceRecheckGapConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "recheck_due_after_seconds",
            _normalize_positive_age_seconds(
                "recheck_due_after_seconds",
                self.recheck_due_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_due_after_seconds",
            _normalize_positive_age_seconds(
                "acknowledgement_due_after_seconds",
                self.acknowledgement_due_after_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckGapSource:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    final_outcome_at: datetime
    last_source_rechecked_at: datetime | None
    source_acknowledged_at: datetime | None
    expected_outcome: str | None
    source_outcome: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketOutcomeSourceRecheckGapSource does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "final_outcome_at",
            _as_utc("final_outcome_at", self.final_outcome_at),
        )
        object.__setattr__(
            self,
            "last_source_rechecked_at",
            _as_optional_utc(
                "last_source_rechecked_at",
                self.last_source_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        _validate_source(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckGapReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckGapRow:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    final_outcome_at: datetime
    last_source_rechecked_at: datetime | None
    source_acknowledged_at: datetime | None
    outcome_age_seconds: Decimal
    recheck_gap_seconds: Decimal
    acknowledgement_gap_seconds: Decimal
    expected_outcome: str | None
    source_outcome: str | None
    gap_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketOutcomeSourceRecheckGapRow does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "final_outcome_at",
            _as_utc("final_outcome_at", self.final_outcome_at),
        )
        object.__setattr__(
            self,
            "last_source_rechecked_at",
            _as_optional_utc(
                "last_source_rechecked_at",
                self.last_source_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        for field_name in (
            "outcome_age_seconds",
            "recheck_gap_seconds",
            "acknowledgement_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_age_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "source_outcome",
            _normalize_optional_public_string("source_outcome", self.source_outcome),
        )
        _require_member("gap_status", self.gap_status, GAP_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckGapReport:
    generated_at: datetime
    config_version: str
    status: str
    source_row_count: Decimal
    gap_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_recheck_count: Decimal
    overdue_recheck_count: Decimal
    missing_acknowledgement_count: Decimal
    source_outcome_conflict_count: Decimal
    gap_ratio: Decimal
    missing_recheck_ratio: Decimal
    overdue_recheck_ratio: Decimal
    max_recheck_gap_seconds: Decimal
    max_acknowledgement_gap_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketOutcomeSourceRecheckGapReasonCodeCount, ...]
    rows: tuple[MarketOutcomeSourceRecheckGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketOutcomeSourceRecheckGapReport does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "source_row_count",
            "gap_count",
            "clear_count",
            "watch_count",
            "blocked_count",
            "missing_recheck_count",
            "overdue_recheck_count",
            "missing_acknowledgement_count",
            "source_outcome_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gap_ratio",
            "missing_recheck_ratio",
            "overdue_recheck_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_recheck_gap_seconds",
            "max_acknowledgement_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_age_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
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


def build_market_outcome_source_recheck_gap_report(
    sources: list[MarketOutcomeSourceRecheckGapSource]
    | tuple[MarketOutcomeSourceRecheckGapSource, ...],
    *,
    config: MarketOutcomeSourceRecheckGapConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckGapReport:
    if type(config) is not MarketOutcomeSourceRecheckGapConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckGapConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    _validate_unique_sources(normalized_sources)
    _validate_no_later_than_generated_at(
        normalized_sources,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _build_row(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_sources
            ),
            key=_row_sort_key,
        ),
    )
    source_row_count = _count(len(rows))
    gap_count = _count(sum(1 for row in rows if row.gap_status != "pass"))
    missing_recheck_count = _reason_count(
        rows,
        "market_outcome_source_recheck_missing_recheck",
    )
    overdue_recheck_count = _reason_count(
        rows,
        "market_outcome_source_recheck_overdue_recheck",
    )

    return MarketOutcomeSourceRecheckGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        source_row_count=source_row_count,
        gap_count=gap_count,
        clear_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        missing_recheck_count=missing_recheck_count,
        overdue_recheck_count=overdue_recheck_count,
        missing_acknowledgement_count=_reason_count(
            rows,
            "market_outcome_source_recheck_missing_acknowledgement",
        ),
        source_outcome_conflict_count=_reason_count(
            rows,
            "market_outcome_source_recheck_conflicting_outcome_source",
        ),
        gap_ratio=_ratio(gap_count, source_row_count),
        missing_recheck_ratio=_ratio(missing_recheck_count, source_row_count),
        overdue_recheck_ratio=_ratio(overdue_recheck_count, source_row_count),
        max_recheck_gap_seconds=max(
            (row.recheck_gap_seconds for row in rows),
            default=AGE_ZERO,
        ),
        max_acknowledgement_gap_seconds=max(
            (row.acknowledgement_gap_seconds for row in rows),
            default=AGE_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_outcome_source_recheck_gap_report_payload(
    report: MarketOutcomeSourceRecheckGapReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckGapReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckGapReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_market_outcome_source_recheck_gap_public_payload(payload)
    return payload


def validate_market_outcome_source_recheck_gap_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market outcome source recheck gap payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    value: MarketOutcomeSourceRecheckGapSource,
    *,
    config: MarketOutcomeSourceRecheckGapConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckGapRow:
    outcome_age_seconds = _duration_seconds(value.final_outcome_at, generated_at)
    recheck_gap_seconds = (
        outcome_age_seconds
        if value.last_source_rechecked_at is None
        else _duration_seconds(value.last_source_rechecked_at, generated_at)
    )
    acknowledgement_gap_seconds = (
        outcome_age_seconds
        if value.source_acknowledged_at is None
        else _duration_seconds(value.final_outcome_at, value.source_acknowledged_at)
    )
    reason_codes = _row_reason_codes(
        missing_recheck=value.last_source_rechecked_at is None,
        overdue_recheck=recheck_gap_seconds >= config.recheck_due_after_seconds,
        missing_acknowledgement=value.source_acknowledged_at is None,
        source_outcome_conflict=_source_outcome_conflict(value),
    )

    return MarketOutcomeSourceRecheckGapRow(
        market_id=value.market_id,
        market_slug=value.market_slug,
        outcome_id=value.outcome_id,
        source_id=value.source_id,
        final_outcome_at=value.final_outcome_at,
        last_source_rechecked_at=value.last_source_rechecked_at,
        source_acknowledged_at=value.source_acknowledged_at,
        outcome_age_seconds=outcome_age_seconds,
        recheck_gap_seconds=recheck_gap_seconds,
        acknowledgement_gap_seconds=acknowledgement_gap_seconds,
        expected_outcome=value.expected_outcome,
        source_outcome=value.source_outcome,
        gap_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_recheck: bool,
    overdue_recheck: bool,
    missing_acknowledgement: bool,
    source_outcome_conflict: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_recheck:
        reason_codes.append("market_outcome_source_recheck_missing_recheck")
    if overdue_recheck:
        reason_codes.append("market_outcome_source_recheck_overdue_recheck")
    if missing_acknowledgement:
        reason_codes.append("market_outcome_source_recheck_missing_acknowledgement")
    if source_outcome_conflict:
        reason_codes.append("market_outcome_source_recheck_conflicting_outcome_source")
    return tuple(reason_codes)


def _source_outcome_conflict(value: MarketOutcomeSourceRecheckGapSource) -> bool:
    if value.expected_outcome is None or value.source_outcome is None:
        return False
    return value.expected_outcome.casefold() != value.source_outcome.casefold()


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        return "pass"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeSourceRecheckGapRow, ...]) -> str:
    statuses = tuple(row.gap_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_outcome_source_recheck_gap_empty",)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if not present:
        return ("market_outcome_source_recheck_gap_clear",)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[MarketOutcomeSourceRecheckGapRow, ...],
) -> tuple[MarketOutcomeSourceRecheckGapReasonCodeCount, ...]:
    return tuple(
        MarketOutcomeSourceRecheckGapReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > COUNT_ZERO
    )


def _normalize_sources(value: object) -> tuple[MarketOutcomeSourceRecheckGapSource, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    sources = tuple(value)
    for item in sources:
        if type(item) is not MarketOutcomeSourceRecheckGapSource:
            raise ValueError(
                "sources must contain MarketOutcomeSourceRecheckGapSource values",
            )
        _require_hard_flags(item)
    return sources


def _normalize_rows(value: object) -> tuple[MarketOutcomeSourceRecheckGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckGapRow:
            raise ValueError("rows must contain MarketOutcomeSourceRecheckGapRow values")
        _require_hard_flags(row)
        key = _item_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market outcome source recheck gap")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketOutcomeSourceRecheckGapReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketOutcomeSourceRecheckGapReasonCodeCount values",
            )
        _require_hard_flags(row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    expected = tuple(
        row
        for reason_code in ROW_REASON_CODES
        for row in rows
        if row.reason_code == reason_code
    )
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return rows


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


def _validate_source(value: MarketOutcomeSourceRecheckGapSource) -> None:
    if (
        value.last_source_rechecked_at is not None
        and value.last_source_rechecked_at < value.final_outcome_at
    ):
        raise ValueError("last_source_rechecked_at must not be before final_outcome_at")
    if (
        value.source_acknowledged_at is not None
        and value.source_acknowledged_at < value.final_outcome_at
    ):
        raise ValueError("source_acknowledged_at must not be before final_outcome_at")


def _validate_row(row: MarketOutcomeSourceRecheckGapRow) -> None:
    _validate_source_like_row(row)
    if row.gap_status != _row_status(row.reason_codes):
        raise ValueError("gap_status must match reason_codes")
    expected_recheck_gap = (
        row.outcome_age_seconds
        if row.last_source_rechecked_at is None
        else _duration_seconds(row.last_source_rechecked_at, _row_generated_anchor(row))
    )
    if row.recheck_gap_seconds != expected_recheck_gap:
        raise ValueError("recheck_gap_seconds must match source recheck timing")
    expected_acknowledgement_gap = (
        row.outcome_age_seconds
        if row.source_acknowledged_at is None
        else _duration_seconds(row.final_outcome_at, row.source_acknowledged_at)
    )
    if row.acknowledgement_gap_seconds != expected_acknowledgement_gap:
        raise ValueError("acknowledgement_gap_seconds must match source timing")
    expected_missing_recheck = row.last_source_rechecked_at is None
    if (
        "market_outcome_source_recheck_missing_recheck" in row.reason_codes
    ) != expected_missing_recheck:
        raise ValueError("reason_codes must match missing source recheck state")
    expected_missing_acknowledgement = row.source_acknowledged_at is None
    if (
        "market_outcome_source_recheck_missing_acknowledgement" in row.reason_codes
    ) != expected_missing_acknowledgement:
        raise ValueError("reason_codes must match acknowledgement state")
    expected_conflict = _row_source_outcome_conflict(row)
    if (
        "market_outcome_source_recheck_conflicting_outcome_source" in row.reason_codes
    ) != expected_conflict:
        raise ValueError("reason_codes must match outcome source state")


def _validate_report(report: MarketOutcomeSourceRecheckGapReport) -> None:
    _require_hard_flags(report)
    rows = report.rows
    expected_values = {
        "status": _report_status(rows),
        "source_row_count": _count(len(rows)),
        "gap_count": _count(sum(1 for row in rows if row.gap_status != "pass")),
        "clear_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "missing_recheck_count": _reason_count(
            rows,
            "market_outcome_source_recheck_missing_recheck",
        ),
        "overdue_recheck_count": _reason_count(
            rows,
            "market_outcome_source_recheck_overdue_recheck",
        ),
        "missing_acknowledgement_count": _reason_count(
            rows,
            "market_outcome_source_recheck_missing_acknowledgement",
        ),
        "source_outcome_conflict_count": _reason_count(
            rows,
            "market_outcome_source_recheck_conflicting_outcome_source",
        ),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    expected_values["gap_ratio"] = _ratio(
        expected_values["gap_count"],
        expected_values["source_row_count"],
    )
    expected_values["missing_recheck_ratio"] = _ratio(
        expected_values["missing_recheck_count"],
        expected_values["source_row_count"],
    )
    expected_values["overdue_recheck_ratio"] = _ratio(
        expected_values["overdue_recheck_count"],
        expected_values["source_row_count"],
    )
    expected_values["max_recheck_gap_seconds"] = max(
        (row.recheck_gap_seconds for row in rows),
        default=AGE_ZERO,
    )
    expected_values["max_acknowledgement_gap_seconds"] = max(
        (row.acknowledgement_gap_seconds for row in rows),
        default=AGE_ZERO,
    )

    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_source_like_row(row: MarketOutcomeSourceRecheckGapRow) -> None:
    if (
        row.last_source_rechecked_at is not None
        and row.last_source_rechecked_at < row.final_outcome_at
    ):
        raise ValueError("last_source_rechecked_at must not be before final_outcome_at")
    if (
        row.source_acknowledged_at is not None
        and row.source_acknowledged_at < row.final_outcome_at
    ):
        raise ValueError("source_acknowledged_at must not be before final_outcome_at")


def _validate_unique_sources(
    sources: tuple[MarketOutcomeSourceRecheckGapSource, ...],
) -> None:
    seen_keys: set[tuple[str, str, str]] = set()
    for item in sources:
        key = _item_key(item)
        if key in seen_keys:
            raise ValueError("sources must not contain duplicate market outcome source recheck gap")
        seen_keys.add(key)


def _validate_no_later_than_generated_at(
    sources: tuple[MarketOutcomeSourceRecheckGapSource, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in sources:
        if item.final_outcome_at > generated_at:
            raise ValueError("final_outcome_at must not be after generated_at")


def _row_generated_anchor(row: MarketOutcomeSourceRecheckGapRow) -> datetime:
    return row.final_outcome_at + _seconds_to_delta(row.outcome_age_seconds)


def _seconds_to_delta(value: Decimal) -> Any:
    from datetime import timedelta

    whole_seconds = int(value)
    microseconds = int((value - Decimal(whole_seconds)) * MICROSECOND_DIVISOR)
    return timedelta(seconds=whole_seconds, microseconds=microseconds)


def _item_key(
    value: MarketOutcomeSourceRecheckGapSource | MarketOutcomeSourceRecheckGapRow,
) -> tuple[str, str, str]:
    return (value.market_id, value.outcome_id, value.source_id)


def _row_sort_key(
    row: MarketOutcomeSourceRecheckGapRow,
) -> tuple[Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.gap_status],
        row.market_slug,
        row.market_id,
        row.outcome_id,
        row.source_id,
    )


def _status_count(rows: tuple[MarketOutcomeSourceRecheckGapRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckGapRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_source_outcome_conflict(row: MarketOutcomeSourceRecheckGapRow) -> bool:
    if row.expected_outcome is None or row.source_outcome is None:
        return False
    return row.expected_outcome.casefold() != row.source_outcome.casefold()


def _report_public_payload_for_digest(
    report: MarketOutcomeSourceRecheckGapReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_to_public_string(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "source_row_count": _decimal_to_public_string(report.source_row_count),
        "gap_count": _decimal_to_public_string(report.gap_count),
        "clear_count": _decimal_to_public_string(report.clear_count),
        "watch_count": _decimal_to_public_string(report.watch_count),
        "blocked_count": _decimal_to_public_string(report.blocked_count),
        "missing_recheck_count": _decimal_to_public_string(
            report.missing_recheck_count,
        ),
        "overdue_recheck_count": _decimal_to_public_string(
            report.overdue_recheck_count,
        ),
        "missing_acknowledgement_count": _decimal_to_public_string(
            report.missing_acknowledgement_count,
        ),
        "source_outcome_conflict_count": _decimal_to_public_string(
            report.source_outcome_conflict_count,
        ),
        "gap_ratio": _decimal_to_public_string(report.gap_ratio),
        "missing_recheck_ratio": _decimal_to_public_string(
            report.missing_recheck_ratio,
        ),
        "overdue_recheck_ratio": _decimal_to_public_string(
            report.overdue_recheck_ratio,
        ),
        "max_recheck_gap_seconds": _decimal_to_public_string(
            report.max_recheck_gap_seconds,
        ),
        "max_acknowledgement_gap_seconds": _decimal_to_public_string(
            report.max_acknowledgement_gap_seconds,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: MarketOutcomeSourceRecheckGapRow) -> dict[str, Any]:
    return {
        "market_id": row.market_id,
        "market_slug": row.market_slug,
        "outcome_id": row.outcome_id,
        "source_id": row.source_id,
        "final_outcome_at": _datetime_to_public_string(row.final_outcome_at),
        "last_source_rechecked_at": _optional_datetime_to_public_string(
            row.last_source_rechecked_at,
        ),
        "source_acknowledged_at": _optional_datetime_to_public_string(
            row.source_acknowledged_at,
        ),
        "outcome_age_seconds": _decimal_to_public_string(row.outcome_age_seconds),
        "recheck_gap_seconds": _decimal_to_public_string(row.recheck_gap_seconds),
        "acknowledgement_gap_seconds": _decimal_to_public_string(
            row.acknowledgement_gap_seconds,
        ),
        "expected_outcome": row.expected_outcome,
        "source_outcome": row.source_outcome,
        "gap_status": row.gap_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    row: MarketOutcomeSourceRecheckGapReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _decimal_to_public_string(row.count),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_derived_validation_digest(report: MarketOutcomeSourceRecheckGapReport) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload_for_digest(report),
    )


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be true")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _reject_public_numeric_values(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload Decimal strings required")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(context: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} keys must be strings")
            _reject_unsafe_text(context, key)
            _reject_unsafe_public_payload(context, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is str:
        _reject_unsafe_text(context, value)


def _reject_unsafe_text(context: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{context} contains unsafe public surface")


def _datetime_to_public_string(value: datetime) -> str:
    return value.isoformat()


def _optional_datetime_to_public_string(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_to_public_string(value)


def _decimal_to_public_string(value: Decimal) -> str:
    return format(value, "f")


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = decimal_value.quantize(COUNT_QUANTUM, context=DECIMAL_CONTEXT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_positive_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_age_seconds(field_name, value)
    if decimal_value <= AGE_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < AGE_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(AGE_QUANTUM, context=DECIMAL_CONTEXT)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < RATIO_ZERO or decimal_value > RATIO_ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(RATIO_QUANTUM, context=DECIMAL_CONTEXT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM, context=DECIMAL_CONTEXT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO:
        return RATIO_ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta.days < 0:
        raise ValueError("duration must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * DAY_SECONDS
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR)
        ).quantize(AGE_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_text(field_name, value)
    return value


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, getattr(value, field_name))
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be true")


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = [
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_GAP_CONFIG_VERSION",
    "GAP_STATUSES",
    "REPORT_STATUSES",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "MarketOutcomeSourceRecheckGapConfig",
    "MarketOutcomeSourceRecheckGapReasonCodeCount",
    "MarketOutcomeSourceRecheckGapReport",
    "MarketOutcomeSourceRecheckGapRow",
    "MarketOutcomeSourceRecheckGapSource",
    "build_market_outcome_source_recheck_gap_report",
    "market_outcome_source_recheck_gap_report_payload",
    "validate_market_outcome_source_recheck_gap_public_payload",
]
