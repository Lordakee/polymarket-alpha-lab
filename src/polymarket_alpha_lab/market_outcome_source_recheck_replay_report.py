"""Pure in-memory Polymarket outcome/source recheck replay report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from numbers import Number
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION = (
    "market-outcome-source-recheck-replay-report-v0"
)

REPLAY_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
ROW_REASON_CODES = (
    "market_outcome_source_recheck_replay_missing_replay",
    "market_outcome_source_recheck_replay_lag_breach",
    "market_outcome_source_recheck_replay_outcome_mismatch",
    "market_outcome_source_recheck_replay_outcome_age_priority",
)
REPORT_REASON_CODES = (
    "market_outcome_source_recheck_replay_empty",
    "market_outcome_source_recheck_replay_clear",
) + ROW_REASON_CODES
BLOCKING_REASON_CODES = frozenset(
    (
        "market_outcome_source_recheck_replay_missing_replay",
        "market_outcome_source_recheck_replay_outcome_mismatch",
    ),
)
STATUS_RANK = {"blocked": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}

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
        _join_parts("ord", "er"),
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
class MarketOutcomeSourceRecheckReplayConfig:
    config_version: str = DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION
    max_replay_lag_seconds: Decimal = Decimal("3600.000000")
    priority_outcome_age_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckReplayConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_replay_lag_seconds",
            _normalize_positive_age_seconds(
                "max_replay_lag_seconds",
                self.max_replay_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "priority_outcome_age_seconds",
            _normalize_nonnegative_age_seconds(
                "priority_outcome_age_seconds",
                self.priority_outcome_age_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReplayRecord:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    final_outcome_at: datetime
    replayed_at: datetime | None
    expected_outcome: str | None
    replayed_outcome: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckReplayRecord does not support subclassing",
        )

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
            "replayed_at",
            _as_optional_utc("replayed_at", self.replayed_at),
        )
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "replayed_outcome",
            _normalize_optional_public_string("replayed_outcome", self.replayed_outcome),
        )
        _validate_record(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReplayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckReplayReasonCodeCount does not support "
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
class MarketOutcomeSourceRecheckReplayRow:
    market_id: str
    market_slug: str
    outcome_id: str
    source_id: str
    final_outcome_at: datetime
    replayed_at: datetime | None
    outcome_age_seconds: Decimal
    replay_lag_seconds: Decimal
    replayed_after_outcome: bool
    expected_outcome: str | None
    replayed_outcome: str | None
    outcome_match: bool
    replay_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckReplayRow does not support subclassing",
        )

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
            "replayed_at",
            _as_optional_utc("replayed_at", self.replayed_at),
        )
        object.__setattr__(
            self,
            "outcome_age_seconds",
            _normalize_nonnegative_age_seconds(
                "outcome_age_seconds",
                self.outcome_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "replay_lag_seconds",
            _normalize_nonnegative_age_seconds(
                "replay_lag_seconds",
                self.replay_lag_seconds,
            ),
        )
        _require_bool("replayed_after_outcome", self.replayed_after_outcome)
        object.__setattr__(
            self,
            "expected_outcome",
            _normalize_optional_public_string("expected_outcome", self.expected_outcome),
        )
        object.__setattr__(
            self,
            "replayed_outcome",
            _normalize_optional_public_string("replayed_outcome", self.replayed_outcome),
        )
        _require_bool("outcome_match", self.outcome_match)
        _require_member("replay_status", self.replay_status, REPLAY_STATUSES)
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
class MarketOutcomeSourceRecheckReplayReport:
    generated_at: datetime
    config_version: str
    status: str
    record_count: Decimal
    replayed_count: Decimal
    missing_replay_count: Decimal
    replay_lag_breach_count: Decimal
    outcome_mismatch_count: Decimal
    outcome_age_priority_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    replayed_ratio: Decimal
    missing_replay_ratio: Decimal
    outcome_mismatch_ratio: Decimal
    max_outcome_age_seconds: Decimal
    max_replay_lag_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketOutcomeSourceRecheckReplayReasonCodeCount, ...]
    rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketOutcomeSourceRecheckReplayReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "record_count",
            "replayed_count",
            "missing_replay_count",
            "replay_lag_breach_count",
            "outcome_mismatch_count",
            "outcome_age_priority_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "replayed_ratio",
            "missing_replay_ratio",
            "outcome_mismatch_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_outcome_age_seconds", "max_replay_lag_seconds"):
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


def build_market_outcome_source_recheck_replay_report(
    records: list[MarketOutcomeSourceRecheckReplayRecord]
    | tuple[MarketOutcomeSourceRecheckReplayRecord, ...],
    *,
    config: MarketOutcomeSourceRecheckReplayConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckReplayReport:
    if type(config) is not MarketOutcomeSourceRecheckReplayConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckReplayConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_records = _normalize_records(records)
    _validate_unique_records(normalized_records)
    _validate_no_later_than_generated_at(normalized_records, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_records
            ),
            key=_row_sort_key,
        ),
    )
    record_count = _count(len(rows))
    replayed_count = _count(sum(1 for row in rows if row.replayed_at is not None))
    missing_replay_count = _reason_count(
        rows,
        "market_outcome_source_recheck_replay_missing_replay",
    )
    outcome_mismatch_count = _reason_count(
        rows,
        "market_outcome_source_recheck_replay_outcome_mismatch",
    )

    return MarketOutcomeSourceRecheckReplayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        record_count=record_count,
        replayed_count=replayed_count,
        missing_replay_count=missing_replay_count,
        replay_lag_breach_count=_reason_count(
            rows,
            "market_outcome_source_recheck_replay_lag_breach",
        ),
        outcome_mismatch_count=outcome_mismatch_count,
        outcome_age_priority_count=_reason_count(
            rows,
            "market_outcome_source_recheck_replay_outcome_age_priority",
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        replayed_ratio=_ratio(replayed_count, record_count),
        missing_replay_ratio=_ratio(missing_replay_count, record_count),
        outcome_mismatch_ratio=_ratio(outcome_mismatch_count, record_count),
        max_outcome_age_seconds=max(
            (row.outcome_age_seconds for row in rows),
            default=AGE_ZERO,
        ),
        max_replay_lag_seconds=max(
            (row.replay_lag_seconds for row in rows),
            default=AGE_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_outcome_source_recheck_replay_report_payload(
    report: MarketOutcomeSourceRecheckReplayReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckReplayReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckReplayReport")
    revalidated_report = _revalidate_report(report)
    payload = _report_public_payload_for_digest(revalidated_report)
    payload["derived_validation_digest"] = revalidated_report.derived_validation_digest
    validate_market_outcome_source_recheck_replay_public_payload(payload)
    return payload


def validate_market_outcome_source_recheck_replay_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("market outcome source recheck replay payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    value: MarketOutcomeSourceRecheckReplayRecord,
    *,
    config: MarketOutcomeSourceRecheckReplayConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckReplayRow:
    outcome_age_seconds = _age_seconds(value.final_outcome_at, generated_at)
    replay_lag_seconds = (
        outcome_age_seconds
        if value.replayed_at is None
        else _age_seconds(value.final_outcome_at, value.replayed_at)
    )
    outcome_match = _outcome_match(value)
    reason_codes = _row_reason_codes(
        missing_replay=value.replayed_at is None,
        replay_lag_breach=replay_lag_seconds >= config.max_replay_lag_seconds,
        outcome_mismatch=not outcome_match,
        outcome_age_priority=outcome_age_seconds >= config.priority_outcome_age_seconds,
    )
    return MarketOutcomeSourceRecheckReplayRow(
        market_id=value.market_id,
        market_slug=value.market_slug,
        outcome_id=value.outcome_id,
        source_id=value.source_id,
        final_outcome_at=value.final_outcome_at,
        replayed_at=value.replayed_at,
        outcome_age_seconds=outcome_age_seconds,
        replay_lag_seconds=replay_lag_seconds,
        replayed_after_outcome=_is_at_or_after(value.replayed_at, value.final_outcome_at),
        expected_outcome=value.expected_outcome,
        replayed_outcome=value.replayed_outcome,
        outcome_match=outcome_match,
        replay_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_replay: bool,
    replay_lag_breach: bool,
    outcome_mismatch: bool,
    outcome_age_priority: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if missing_replay:
        reason_codes.append("market_outcome_source_recheck_replay_missing_replay")
    if replay_lag_breach:
        reason_codes.append("market_outcome_source_recheck_replay_lag_breach")
    if outcome_mismatch:
        reason_codes.append("market_outcome_source_recheck_replay_outcome_mismatch")
    if outcome_age_priority:
        reason_codes.append("market_outcome_source_recheck_replay_outcome_age_priority")
    return tuple(reason_codes)


def _outcome_match(value: MarketOutcomeSourceRecheckReplayRecord) -> bool:
    if value.expected_outcome is None or value.replayed_outcome is None:
        return False
    return value.expected_outcome.casefold() == value.replayed_outcome.casefold()


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        return "pass"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...]) -> str:
    statuses = tuple(row.replay_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_outcome_source_recheck_replay_empty",)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if not present:
        return ("market_outcome_source_recheck_replay_clear",)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...],
) -> tuple[MarketOutcomeSourceRecheckReplayReasonCodeCount, ...]:
    return tuple(
        MarketOutcomeSourceRecheckReplayReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > COUNT_ZERO
    )


def _normalize_records(value: object) -> tuple[MarketOutcomeSourceRecheckReplayRecord, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("records must be a list or tuple")
    records = tuple(value)
    for item in records:
        if type(item) is not MarketOutcomeSourceRecheckReplayRecord:
            raise ValueError(
                "records must contain MarketOutcomeSourceRecheckReplayRecord values",
            )
        _require_hard_flags(item)
    return records


def _normalize_rows(value: object) -> tuple[MarketOutcomeSourceRecheckReplayRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckReplayRow:
            raise ValueError(
                "rows must contain MarketOutcomeSourceRecheckReplayRow values",
            )
        _require_hard_flags(row)
        key = _item_key(row)
        if key in seen_keys:
            raise ValueError(
                "rows must not contain duplicate market outcome/source recheck replay",
            )
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketOutcomeSourceRecheckReplayReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckReplayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketOutcomeSourceRecheckReplayReasonCodeCount values",
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


def _validate_record(value: MarketOutcomeSourceRecheckReplayRecord) -> None:
    if value.replayed_at is not None and value.replayed_at < value.final_outcome_at:
        raise ValueError("replayed_at must not be before final_outcome_at")


def _validate_unique_records(
    records: tuple[MarketOutcomeSourceRecheckReplayRecord, ...],
) -> None:
    seen_keys: set[tuple[str, str, str, str]] = set()
    for item in records:
        key = _item_key(item)
        if key in seen_keys:
            raise ValueError(
                "records must not contain duplicate market outcome/source recheck replay",
            )
        seen_keys.add(key)


def _validate_no_later_than_generated_at(
    records: tuple[MarketOutcomeSourceRecheckReplayRecord, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in records:
        for field_name in ("final_outcome_at", "replayed_at"):
            value = getattr(item, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row(row: MarketOutcomeSourceRecheckReplayRow) -> None:
    if row.replayed_at is not None and row.replayed_at < row.final_outcome_at:
        raise ValueError("replayed_at must not be before final_outcome_at")
    if row.replayed_after_outcome != _is_at_or_after(
        row.replayed_at,
        row.final_outcome_at,
    ):
        raise ValueError("replayed_after_outcome must match timestamps")
    if row.outcome_match != (
        row.expected_outcome is not None
        and row.replayed_outcome is not None
        and row.expected_outcome.casefold() == row.replayed_outcome.casefold()
    ):
        raise ValueError("outcome_match must match outcomes")
    if row.replay_status != _row_status(row.reason_codes):
        raise ValueError("replay_status must match reason_codes")


def _validate_report(report: MarketOutcomeSourceRecheckReplayReport) -> None:
    rows = report.rows
    if report.record_count != _count(len(rows)):
        raise ValueError("record_count must match rows")
    if report.replayed_count != _count(sum(1 for row in rows if row.replayed_at is not None)):
        raise ValueError("replayed_count must match rows")
    for field_name, reason_code in (
        (
            "missing_replay_count",
            "market_outcome_source_recheck_replay_missing_replay",
        ),
        (
            "replay_lag_breach_count",
            "market_outcome_source_recheck_replay_lag_breach",
        ),
        (
            "outcome_mismatch_count",
            "market_outcome_source_recheck_replay_outcome_mismatch",
        ),
        (
            "outcome_age_priority_count",
            "market_outcome_source_recheck_replay_outcome_age_priority",
        ),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.replayed_ratio != _ratio(report.replayed_count, report.record_count):
        raise ValueError("replayed_ratio must match counts")
    if report.missing_replay_ratio != _ratio(
        report.missing_replay_count,
        report.record_count,
    ):
        raise ValueError("missing_replay_ratio must match counts")
    if report.outcome_mismatch_ratio != _ratio(
        report.outcome_mismatch_count,
        report.record_count,
    ):
        raise ValueError("outcome_mismatch_ratio must match counts")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.max_outcome_age_seconds != max(
        (row.outcome_age_seconds for row in rows),
        default=AGE_ZERO,
    ):
        raise ValueError("max_outcome_age_seconds must match rows")
    if report.max_replay_lag_seconds != max(
        (row.replay_lag_seconds for row in rows),
        default=AGE_ZERO,
    ):
        raise ValueError("max_replay_lag_seconds must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _item_key(
    value: MarketOutcomeSourceRecheckReplayRecord | MarketOutcomeSourceRecheckReplayRow,
) -> tuple[str, str, str, str]:
    return (value.market_id, value.market_slug, value.outcome_id, value.source_id)


def _row_sort_key(
    row: MarketOutcomeSourceRecheckReplayRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.replay_status],
        -_count(len(row.reason_codes)),
        -max(row.outcome_age_seconds, row.replay_lag_seconds),
        row.market_slug,
        row.market_id,
        row.outcome_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.replay_status == status))


def _reason_count(
    rows: tuple[MarketOutcomeSourceRecheckReplayRow, ...],
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
    report: MarketOutcomeSourceRecheckReplayReport,
) -> MarketOutcomeSourceRecheckReplayReport:
    return MarketOutcomeSourceRecheckReplayReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        record_count=report.record_count,
        replayed_count=report.replayed_count,
        missing_replay_count=report.missing_replay_count,
        replay_lag_breach_count=report.replay_lag_breach_count,
        outcome_mismatch_count=report.outcome_mismatch_count,
        outcome_age_priority_count=report.outcome_age_priority_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        replayed_ratio=report.replayed_ratio,
        missing_replay_ratio=report.missing_replay_ratio,
        outcome_mismatch_ratio=report.outcome_mismatch_ratio,
        max_outcome_age_seconds=report.max_outcome_age_seconds,
        max_replay_lag_seconds=report.max_replay_lag_seconds,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_derived_validation_digest(
    report: MarketOutcomeSourceRecheckReplayReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _report_public_payload_for_digest(
    report: MarketOutcomeSourceRecheckReplayReport,
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


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    for public_text in _public_payload_strings(value):
        try:
            _reject_unsafe_public_text(public_text)
        except ValueError as exc:
            raise ValueError(f"unsafe public surface in {label}") from exc


def _public_payload_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            texts.append(key)
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(_public_payload_strings(item))
        return tuple(texts)
    if type(value) is str:
        return (value,)
    return ()


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


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < AGE_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(AGE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < RATIO_ZERO or normalized > Decimal("1.000000"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError("unsafe public text is not allowed")


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckReplayConfig",
    "MarketOutcomeSourceRecheckReplayRecord",
    "MarketOutcomeSourceRecheckReplayReasonCodeCount",
    "MarketOutcomeSourceRecheckReplayRow",
    "MarketOutcomeSourceRecheckReplayReport",
    "build_market_outcome_source_recheck_replay_report",
    "market_outcome_source_recheck_replay_report_payload",
    "validate_market_outcome_source_recheck_replay_public_payload",
)
