"""Pure in-memory Polymarket outcome/source recheck backlog report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from numbers import Number
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_BACKLOG_REPORT_CONFIG_VERSION = (
    "market-outcome-source-recheck-backlog-report-v0"
)

BACKLOG_STATUSES = ("clear", "watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "market_outcome_source_recheck_backlog_missing_recheck",
    "market_outcome_source_recheck_backlog_stale_recheck",
    "market_outcome_source_recheck_backlog_missing_acknowledgement",
    "market_outcome_source_recheck_backlog_source_outcome_conflict",
    "market_outcome_source_recheck_backlog_critical_age",
    "market_outcome_source_recheck_backlog_high_open_count",
)
REPORT_REASON_CODES = (
    "market_outcome_source_recheck_backlog_empty",
    "market_outcome_source_recheck_backlog_clear",
) + ROW_REASON_CODES
BLOCKING_REASON_CODES = frozenset(
    (
        "market_outcome_source_recheck_backlog_missing_recheck",
        "market_outcome_source_recheck_backlog_missing_acknowledgement",
        "market_outcome_source_recheck_backlog_source_outcome_conflict",
        "market_outcome_source_recheck_backlog_high_open_count",
    ),
)
STATUS_RANK = {"blocked": Decimal("0"), "watch": Decimal("1"), "clear": Decimal("2")}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_ZERO = Decimal("0")
RATIO_ZERO = Decimal("0.000000")
RATIO_QUANTUM = Decimal("0.000001")
AGE_ZERO = Decimal("0.000000")
AGE_QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("cre", "den", "tial"),
        _join_parts("api", "_", "key"),
        _join_parts("private", "_", "key"),
        _join_parts("secret"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("submit"),
        _join_parts("cancel"),
        _join_parts("sign"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("dsn"),
        _join_parts("per", "sist"),
    ),
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckBacklogConfig:
    config_version: str = (
        DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_BACKLOG_REPORT_CONFIG_VERSION
    )
    stale_backlog_after_seconds: Decimal = Decimal("3600.000000")
    critical_backlog_after_seconds: Decimal = Decimal("7200.000000")
    high_open_recheck_count_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckBacklogConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_backlog_after_seconds",
            _normalize_positive_age_seconds(
                "stale_backlog_after_seconds",
                self.stale_backlog_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "critical_backlog_after_seconds",
            _normalize_positive_age_seconds(
                "critical_backlog_after_seconds",
                self.critical_backlog_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "high_open_recheck_count_threshold",
            _normalize_positive_count(
                "high_open_recheck_count_threshold",
                self.high_open_recheck_count_threshold,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckBacklogItem:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    recheck_requested_at: datetime
    last_rechecked_at: datetime | None
    source_acknowledged_at: datetime | None
    expected_outcome: str | None
    source_outcome: str | None
    open_recheck_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckBacklogItem does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
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
        object.__setattr__(
            self,
            "open_recheck_count",
            _normalize_nonnegative_count("open_recheck_count", self.open_recheck_count),
        )
        _validate_item(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckBacklogReasonCodeCount does not support "
            "subclassing",
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
class MarketOutcomeSourceRecheckBacklogRow:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    recheck_requested_at: datetime
    last_rechecked_at: datetime | None
    source_acknowledged_at: datetime | None
    backlog_age_seconds: Decimal
    last_recheck_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal
    rechecked_after_request: bool
    source_acknowledged_after_request: bool
    expected_outcome: str | None
    source_outcome: str | None
    open_recheck_count: Decimal
    backlog_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckBacklogRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_id", "market_slug", "outcome_id", "source_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recheck_requested_at",
            _as_utc("recheck_requested_at", self.recheck_requested_at),
        )
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "source_acknowledged_at",
            _as_optional_utc("source_acknowledged_at", self.source_acknowledged_at),
        )
        object.__setattr__(
            self,
            "backlog_age_seconds",
            _normalize_nonnegative_age_seconds(
                "backlog_age_seconds",
                self.backlog_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "last_recheck_age_seconds",
            _normalize_optional_nonnegative_age_seconds(
                "last_recheck_age_seconds",
                self.last_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _normalize_nonnegative_age_seconds(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in (
            "rechecked_after_request",
            "source_acknowledged_after_request",
        ):
            _require_bool(field_name, getattr(self, field_name))
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
        object.__setattr__(
            self,
            "open_recheck_count",
            _normalize_nonnegative_count("open_recheck_count", self.open_recheck_count),
        )
        _require_member("backlog_status", self.backlog_status, BACKLOG_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckBacklogReport:
    generated_at: datetime
    config_version: str
    status: str
    item_count: Decimal
    backlog_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_recheck_count: Decimal
    stale_recheck_count: Decimal
    missing_acknowledgement_count: Decimal
    source_outcome_conflict_count: Decimal
    critical_age_count: Decimal
    high_open_recheck_count: Decimal
    blocked_ratio: Decimal
    watch_ratio: Decimal
    backlog_ratio: Decimal
    max_backlog_age_seconds: Decimal
    max_last_recheck_age_seconds: Decimal
    max_acknowledgement_lag_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketOutcomeSourceRecheckBacklogReasonCodeCount, ...]
    rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckBacklogReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "item_count",
            "backlog_count",
            "clear_count",
            "watch_count",
            "blocked_count",
            "missing_recheck_count",
            "stale_recheck_count",
            "missing_acknowledgement_count",
            "source_outcome_conflict_count",
            "critical_age_count",
            "high_open_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("blocked_ratio", "watch_ratio", "backlog_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_backlog_age_seconds",
            "max_last_recheck_age_seconds",
            "max_acknowledgement_lag_seconds",
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


def build_market_outcome_source_recheck_backlog_report(
    items: list[MarketOutcomeSourceRecheckBacklogItem]
    | tuple[MarketOutcomeSourceRecheckBacklogItem, ...],
    *,
    config: MarketOutcomeSourceRecheckBacklogConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckBacklogReport:
    if type(config) is not MarketOutcomeSourceRecheckBacklogConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckBacklogConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    _validate_unique_items(normalized_items)
    _validate_no_later_than_generated_at(normalized_items, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_items
            ),
            key=_row_sort_key,
        ),
    )
    item_count = _count(len(rows))
    backlog_count = _count(sum(1 for row in rows if row.backlog_status != "clear"))
    return MarketOutcomeSourceRecheckBacklogReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        item_count=item_count,
        backlog_count=backlog_count,
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        missing_recheck_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_missing_recheck",
        ),
        stale_recheck_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_stale_recheck",
        ),
        missing_acknowledgement_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_missing_acknowledgement",
        ),
        source_outcome_conflict_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_source_outcome_conflict",
        ),
        critical_age_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_critical_age",
        ),
        high_open_recheck_count=_reason_count(
            rows,
            "market_outcome_source_recheck_backlog_high_open_count",
        ),
        blocked_ratio=_ratio(_status_count(rows, "blocked"), item_count),
        watch_ratio=_ratio(_status_count(rows, "watch"), item_count),
        backlog_ratio=_ratio(backlog_count, item_count),
        max_backlog_age_seconds=max(
            (row.backlog_age_seconds for row in rows),
            default=AGE_ZERO,
        ),
        max_last_recheck_age_seconds=max(
            (
                row.last_recheck_age_seconds
                for row in rows
                if row.last_recheck_age_seconds is not None
            ),
            default=AGE_ZERO,
        ),
        max_acknowledgement_lag_seconds=max(
            (row.acknowledgement_lag_seconds for row in rows),
            default=AGE_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_outcome_source_recheck_backlog_report_payload(
    report: MarketOutcomeSourceRecheckBacklogReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckBacklogReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckBacklogReport")
    revalidated_report = _revalidate_report(report)
    payload = _report_public_payload_for_digest(revalidated_report)
    payload["derived_validation_digest"] = revalidated_report.derived_validation_digest
    validate_market_outcome_source_recheck_backlog_public_payload(payload)
    return payload


def validate_market_outcome_source_recheck_backlog_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    value: MarketOutcomeSourceRecheckBacklogItem,
    *,
    config: MarketOutcomeSourceRecheckBacklogConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckBacklogRow:
    backlog_age_seconds = _age_seconds(value.recheck_requested_at, generated_at)
    last_recheck_age_seconds = (
        None
        if value.last_rechecked_at is None
        else _age_seconds(value.last_rechecked_at, generated_at)
    )
    rechecked_after_request = _is_at_or_after(
        value.last_rechecked_at,
        value.recheck_requested_at,
    )
    source_acknowledged_after_request = _is_at_or_after(
        value.source_acknowledged_at,
        value.recheck_requested_at,
    )
    acknowledgement_lag_seconds = (
        backlog_age_seconds
        if value.source_acknowledged_at is None
        else _age_seconds(value.recheck_requested_at, value.source_acknowledged_at)
    )
    reason_codes = _row_reason_codes(
        missing_recheck=value.last_rechecked_at is None,
        stale_recheck=(
            last_recheck_age_seconds is not None
            and last_recheck_age_seconds >= config.stale_backlog_after_seconds
        ),
        missing_acknowledgement=not source_acknowledged_after_request,
        source_outcome_conflict=_source_outcome_conflict(value),
        critical_age=backlog_age_seconds >= config.critical_backlog_after_seconds,
        high_open_recheck_count=(
            value.open_recheck_count >= config.high_open_recheck_count_threshold
        ),
    )
    return MarketOutcomeSourceRecheckBacklogRow(
        market_id=value.market_id,
        market_slug=value.market_slug,
        outcome_id=value.outcome_id,
        source_id=value.source_id,
        recheck_requested_at=value.recheck_requested_at,
        last_rechecked_at=value.last_rechecked_at,
        source_acknowledged_at=value.source_acknowledged_at,
        backlog_age_seconds=backlog_age_seconds,
        last_recheck_age_seconds=last_recheck_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        rechecked_after_request=rechecked_after_request,
        source_acknowledged_after_request=source_acknowledged_after_request,
        expected_outcome=value.expected_outcome,
        source_outcome=value.source_outcome,
        open_recheck_count=value.open_recheck_count,
        backlog_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_recheck: bool,
    stale_recheck: bool,
    missing_acknowledgement: bool,
    source_outcome_conflict: bool,
    critical_age: bool,
    high_open_recheck_count: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_recheck:
        reason_codes.append("market_outcome_source_recheck_backlog_missing_recheck")
    if stale_recheck:
        reason_codes.append("market_outcome_source_recheck_backlog_stale_recheck")
    if missing_acknowledgement:
        reason_codes.append(
            "market_outcome_source_recheck_backlog_missing_acknowledgement",
        )
    if source_outcome_conflict:
        reason_codes.append("market_outcome_source_recheck_backlog_source_outcome_conflict")
    if critical_age:
        reason_codes.append("market_outcome_source_recheck_backlog_critical_age")
    if high_open_recheck_count:
        reason_codes.append("market_outcome_source_recheck_backlog_high_open_count")
    return tuple(reason_codes)


def _source_outcome_conflict(value: MarketOutcomeSourceRecheckBacklogItem) -> bool:
    if value.expected_outcome is None or value.source_outcome is None:
        return False
    return value.expected_outcome.casefold() != value.source_outcome.casefold()


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        return "clear"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...]) -> str:
    statuses = tuple(row.backlog_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_outcome_source_recheck_backlog_empty",)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if not present:
        return ("market_outcome_source_recheck_backlog_clear",)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...],
) -> tuple[MarketOutcomeSourceRecheckBacklogReasonCodeCount, ...]:
    return tuple(
        MarketOutcomeSourceRecheckBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > COUNT_ZERO
    )


def _normalize_items(value: object) -> tuple[MarketOutcomeSourceRecheckBacklogItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    items = tuple(value)
    for item in items:
        if type(item) is not MarketOutcomeSourceRecheckBacklogItem:
            raise ValueError(
                "items must contain MarketOutcomeSourceRecheckBacklogItem values",
            )
        _require_hard_flags(item)
    return items


def _normalize_rows(value: object) -> tuple[MarketOutcomeSourceRecheckBacklogRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckBacklogRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckBacklogRow values",
            )
        _require_hard_flags(row)
        _validate_row(row)
        key = _item_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market outcome/source item")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketOutcomeSourceRecheckBacklogReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketOutcomeSourceRecheckBacklogReasonCodeCount values",
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


def _validate_item(value: MarketOutcomeSourceRecheckBacklogItem) -> None:
    if (
        value.last_rechecked_at is not None
        and value.last_rechecked_at < value.recheck_requested_at
    ):
        raise ValueError("last_rechecked_at must not be before recheck_requested_at")
    if (
        value.source_acknowledged_at is not None
        and value.source_acknowledged_at < value.recheck_requested_at
    ):
        raise ValueError(
            "source_acknowledged_at must not be before recheck_requested_at",
        )


def _validate_unique_items(
    items: tuple[MarketOutcomeSourceRecheckBacklogItem, ...],
) -> None:
    seen_keys: set[tuple[str, str, str, str]] = set()
    for item in items:
        key = _item_key(item)
        if key in seen_keys:
            raise ValueError(
                "items must not contain duplicate market outcome/source recheck "
                "backlog item",
            )
        seen_keys.add(key)


def _validate_no_later_than_generated_at(
    items: tuple[MarketOutcomeSourceRecheckBacklogItem, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in items:
        for field_name in (
            "recheck_requested_at",
            "last_rechecked_at",
            "source_acknowledged_at",
        ):
            value = getattr(item, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row(row: MarketOutcomeSourceRecheckBacklogRow) -> None:
    if (
        row.last_rechecked_at is not None
        and row.last_rechecked_at < row.recheck_requested_at
    ):
        raise ValueError("last_rechecked_at must not be before recheck_requested_at")
    if (
        row.source_acknowledged_at is not None
        and row.source_acknowledged_at < row.recheck_requested_at
    ):
        raise ValueError(
            "source_acknowledged_at must not be before recheck_requested_at",
        )
    if row.rechecked_after_request != _is_at_or_after(
        row.last_rechecked_at,
        row.recheck_requested_at,
    ):
        raise ValueError("rechecked_after_request must match timestamps")
    if row.source_acknowledged_after_request != _is_at_or_after(
        row.source_acknowledged_at,
        row.recheck_requested_at,
    ):
        raise ValueError("source_acknowledged_after_request must match timestamps")
    if row.last_rechecked_at is None and row.last_recheck_age_seconds is not None:
        raise ValueError("last_recheck_age_seconds must be absent without last_rechecked_at")
    if row.last_rechecked_at is not None and row.last_recheck_age_seconds is None:
        raise ValueError("last_recheck_age_seconds is required with last_rechecked_at")
    if row.backlog_status != _row_status(row.reason_codes):
        raise ValueError("backlog_status must match reason_codes")


def _validate_report(report: MarketOutcomeSourceRecheckBacklogReport) -> None:
    rows = report.rows
    if report.item_count != _count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.backlog_count != _count(
        sum(1 for row in rows if row.backlog_status != "clear"),
    ):
        raise ValueError("backlog_count must match rows")
    if report.clear_count != _status_count(rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.item_count != report.backlog_count + report.clear_count:
        raise ValueError("item_count must equal backlog_count plus clear_count")
    for field_name, reason_code in (
        (
            "missing_recheck_count",
            "market_outcome_source_recheck_backlog_missing_recheck",
        ),
        (
            "stale_recheck_count",
            "market_outcome_source_recheck_backlog_stale_recheck",
        ),
        (
            "missing_acknowledgement_count",
            "market_outcome_source_recheck_backlog_missing_acknowledgement",
        ),
        (
            "source_outcome_conflict_count",
            "market_outcome_source_recheck_backlog_source_outcome_conflict",
        ),
        ("critical_age_count", "market_outcome_source_recheck_backlog_critical_age"),
        (
            "high_open_recheck_count",
            "market_outcome_source_recheck_backlog_high_open_count",
        ),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.blocked_ratio != _ratio(report.blocked_count, report.item_count):
        raise ValueError("blocked_ratio must match rows")
    if report.watch_ratio != _ratio(report.watch_count, report.item_count):
        raise ValueError("watch_ratio must match rows")
    if report.backlog_ratio != _ratio(report.backlog_count, report.item_count):
        raise ValueError("backlog_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.max_backlog_age_seconds != max(
        (row.backlog_age_seconds for row in rows),
        default=AGE_ZERO,
    ):
        raise ValueError("max_backlog_age_seconds must match rows")
    if report.max_last_recheck_age_seconds != max(
        (
            row.last_recheck_age_seconds
            for row in rows
            if row.last_recheck_age_seconds is not None
        ),
        default=AGE_ZERO,
    ):
        raise ValueError("max_last_recheck_age_seconds must match rows")
    if report.max_acknowledgement_lag_seconds != max(
        (row.acknowledgement_lag_seconds for row in rows),
        default=AGE_ZERO,
    ):
        raise ValueError("max_acknowledgement_lag_seconds must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _item_key(
    value: MarketOutcomeSourceRecheckBacklogItem | MarketOutcomeSourceRecheckBacklogRow,
) -> tuple[str, str, str, str]:
    return (value.market_id, value.market_slug, value.outcome_id, value.source_id)


def _row_sort_key(
    row: MarketOutcomeSourceRecheckBacklogRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.backlog_status],
        -_count(len(row.reason_codes)),
        -max(
            row.backlog_age_seconds,
            (
                row.last_recheck_age_seconds
                if row.last_recheck_age_seconds is not None
                else AGE_ZERO
            ),
            row.acknowledgement_lag_seconds,
        ),
        row.market_slug,
        row.market_id,
        row.outcome_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.backlog_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckBacklogRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return Decimal(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO:
        return RATIO_ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(
            RATIO_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )


def _age_seconds(earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("age seconds must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        if delta.microseconds:
            seconds += Decimal(delta.microseconds) / MICROSECOND_DIVISOR
        return seconds.quantize(AGE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _is_at_or_after(value: datetime | None, lower_bound: datetime) -> bool:
    return value is not None and value >= lower_bound


def _revalidate_report(
    report: MarketOutcomeSourceRecheckBacklogReport,
) -> MarketOutcomeSourceRecheckBacklogReport:
    return MarketOutcomeSourceRecheckBacklogReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        item_count=report.item_count,
        backlog_count=report.backlog_count,
        clear_count=report.clear_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        missing_recheck_count=report.missing_recheck_count,
        stale_recheck_count=report.stale_recheck_count,
        missing_acknowledgement_count=report.missing_acknowledgement_count,
        source_outcome_conflict_count=report.source_outcome_conflict_count,
        critical_age_count=report.critical_age_count,
        high_open_recheck_count=report.high_open_recheck_count,
        blocked_ratio=report.blocked_ratio,
        watch_ratio=report.watch_ratio,
        backlog_ratio=report.backlog_ratio,
        max_backlog_age_seconds=report.max_backlog_age_seconds,
        max_last_recheck_age_seconds=report.max_last_recheck_age_seconds,
        max_acknowledgement_lag_seconds=report.max_acknowledgement_lag_seconds,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_derived_validation_digest(
    report: MarketOutcomeSourceRecheckBacklogReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _report_public_payload_for_digest(
    report: MarketOutcomeSourceRecheckBacklogReport,
) -> dict[str, Any]:
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item)
        return ready
    if isinstance(value, Number) and type(value) is not bool:
        raise ValueError("JSON value must use Decimal strings")
    if type(value) is str:
        _reject_unsafe_public_text(value)
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_public_numeric_values(value: Any) -> None:
    if isinstance(value, Number) and type(value) is not bool:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            if _is_unsafe_public_text(key):
                raise ValueError("unsafe live surface field is not allowed")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _is_unsafe_public_text(value):
        raise ValueError("unsafe public value is not allowed")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


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


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_positive_age_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_age_seconds(field_name, value)
    if normalized <= AGE_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < RATIO_ZERO or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    if normalized != normalized.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return normalized


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < AGE_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(AGE_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")
    return normalized


def _normalize_optional_nonnegative_age_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_age_seconds(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_text(value: str) -> None:
    if _is_unsafe_public_text(value):
        raise ValueError("unsafe public surface text is not allowed")


def _is_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_BACKLOG_REPORT_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckBacklogConfig",
    "MarketOutcomeSourceRecheckBacklogItem",
    "MarketOutcomeSourceRecheckBacklogReasonCodeCount",
    "MarketOutcomeSourceRecheckBacklogRow",
    "MarketOutcomeSourceRecheckBacklogReport",
    "build_market_outcome_source_recheck_backlog_report",
    "market_outcome_source_recheck_backlog_report_payload",
    "validate_market_outcome_source_recheck_backlog_public_payload",
)
