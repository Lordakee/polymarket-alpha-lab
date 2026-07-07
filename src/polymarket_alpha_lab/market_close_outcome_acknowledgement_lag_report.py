"""In-memory market close outcome acknowledgement lag report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_MARKET_CLOSE_OUTCOME_ACKNOWLEDGEMENT_LAG_CONFIG_VERSION = (
    "market-close-outcome-acknowledgement-lag-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DEFAULT_STALE_SOURCE_AFTER_SECONDS = Decimal("3600.000000")
_DEFAULT_LATE_ACKNOWLEDGEMENT_AFTER_SECONDS = Decimal("1800.000000")
_DEFAULT_UNRESOLVED_CLOSE_AFTER_SECONDS = Decimal("7200.000000")
_REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"

_LAG_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHTS = {"blocked": 0, "watch": 1, "pass": 2}
_CLEAR_REASON_CODE = "market_close_outcome_acknowledgement_lag_clear"
_REPORT_STATUS_REASON_CODES = {
    "blocked": "market_close_outcome_acknowledgement_lag_blocked",
    "watch": "market_close_outcome_acknowledgement_lag_watch",
    "pass": "market_close_outcome_acknowledgement_lag_clear",
}
_ROW_REASON_TO_REPORT_REASON = (
    ("outcome_source_contradiction", "outcome_source_contradiction_present"),
    ("missing_outcome_confirmation", "missing_outcome_confirmation_present"),
    ("stale_source_confirmation", "stale_source_confirmation_present"),
    ("late_team_acknowledgement", "late_team_acknowledgement_present"),
    ("unresolved_close_age_exceeds_threshold", "unresolved_close_age_present"),
)
_REASON_CODE_RANK = {
    "market_close_outcome_acknowledgement_lag_blocked": 0,
    "market_close_outcome_acknowledgement_lag_watch": 1,
    _CLEAR_REASON_CODE: 2,
    "no_closed_markets_to_assess": 3,
    "outcome_source_contradiction": 10,
    "missing_outcome_confirmation": 11,
    "stale_source_confirmation": 12,
    "late_team_acknowledgement": 13,
    "unresolved_close_age_exceeds_threshold": 14,
    "outcome_source_contradiction_present": 20,
    "missing_outcome_confirmation_present": 21,
    "stale_source_confirmation_present": 22,
    "late_team_acknowledgement_present": 23,
    "unresolved_close_age_present": 24,
}
_DIGEST_FIELD_NAME = "derived_validation_digest"
_SHA256_HEX_CHARS = frozenset("0123456789abcdef")
_UNSAFE_TEXT_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)


@dataclass(frozen=True)
class MarketCloseOutcomeAcknowledgementLagConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_OUTCOME_ACKNOWLEDGEMENT_LAG_CONFIG_VERSION
    stale_source_after_seconds: Decimal = _DEFAULT_STALE_SOURCE_AFTER_SECONDS
    late_acknowledgement_after_seconds: Decimal = (
        _DEFAULT_LATE_ACKNOWLEDGEMENT_AFTER_SECONDS
    )
    unresolved_close_after_seconds: Decimal = _DEFAULT_UNRESOLVED_CLOSE_AFTER_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_source_after_seconds",
            _normalize_seconds_decimal(
                "stale_source_after_seconds",
                self.stale_source_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "late_acknowledgement_after_seconds",
            _normalize_seconds_decimal(
                "late_acknowledgement_after_seconds",
                self.late_acknowledgement_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_close_after_seconds",
            _normalize_seconds_decimal(
                "unresolved_close_after_seconds",
                self.unresolved_close_after_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseOutcomeAcknowledgementLagInput:
    condition_id: str
    closed_at: datetime
    outcome_confirmed_at: datetime | None = None
    source_confirmed_at: datetime | None = None
    team_acknowledged_at: datetime | None = None
    outcome_value: Decimal | None = None
    source_outcome_value: Decimal | None = None
    source_reference: str = _REDACTED_SOURCE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        for field_name in (
            "outcome_confirmed_at",
            "source_confirmed_at",
            "team_acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_value",
            _normalize_probability_or_none("outcome_value", self.outcome_value),
        )
        object.__setattr__(
            self,
            "source_outcome_value",
            _normalize_probability_or_none(
                "source_outcome_value",
                self.source_outcome_value,
            ),
        )
        _validate_confirmation_pair(
            "outcome",
            self.outcome_confirmed_at,
            self.outcome_value,
        )
        _validate_confirmation_pair(
            "source",
            self.source_confirmed_at,
            self.source_outcome_value,
        )
        _require_canonical_string("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", _REDACTED_SOURCE_REFERENCE)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseOutcomeAcknowledgementLagRow:
    condition_id: str
    closed_at: datetime
    outcome_confirmed_at: datetime | None
    source_confirmed_at: datetime | None
    team_acknowledged_at: datetime | None
    outcome_value: Decimal | None
    source_outcome_value: Decimal | None
    source_reference: str
    close_age_seconds: Decimal
    close_to_outcome_seconds: Decimal | None
    close_to_source_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal | None
    unresolved_close_age_seconds: Decimal
    lag_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        object.__setattr__(self, "closed_at", _as_utc("closed_at", self.closed_at))
        for field_name in (
            "outcome_confirmed_at",
            "source_confirmed_at",
            "team_acknowledged_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_value",
            _normalize_probability_or_none("outcome_value", self.outcome_value),
        )
        object.__setattr__(
            self,
            "source_outcome_value",
            _normalize_probability_or_none(
                "source_outcome_value",
                self.source_outcome_value,
            ),
        )
        _require_canonical_string("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", _REDACTED_SOURCE_REFERENCE)
        for field_name in (
            "close_age_seconds",
            "unresolved_close_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "close_to_outcome_seconds",
            "close_to_source_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_seconds_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_status("lag_status", self.lag_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketCloseOutcomeAcknowledgementLagReport:
    generated_at: datetime
    config_version: str
    total_market_count: Decimal
    blocked_market_count: Decimal
    watch_market_count: Decimal
    pass_market_count: Decimal
    acknowledged_market_count: Decimal
    missing_outcome_count: Decimal
    stale_source_count: Decimal
    late_acknowledgement_count: Decimal
    contradiction_count: Decimal
    unresolved_close_age_count: Decimal
    acknowledgement_completion_ratio: Decimal
    lag_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketCloseOutcomeAcknowledgementLagRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "total_market_count",
            "blocked_market_count",
            "watch_market_count",
            "pass_market_count",
            "acknowledged_market_count",
            "missing_outcome_count",
            "stale_source_count",
            "late_acknowledgement_count",
            "contradiction_count",
            "unresolved_close_age_count",
            "acknowledgement_completion_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.acknowledgement_completion_ratio > _ONE:
            raise ValueError("acknowledgement_completion_ratio must be between 0 and 1")
        _require_status("lag_status", self.lag_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        _require_hard_flags(self)


def build_market_close_outcome_acknowledgement_lag_report(
    inputs: tuple[MarketCloseOutcomeAcknowledgementLagInput, ...]
    | list[MarketCloseOutcomeAcknowledgementLagInput],
    *,
    config: MarketCloseOutcomeAcknowledgementLagConfig,
    generated_at: datetime,
) -> MarketCloseOutcomeAcknowledgementLagReport:
    if type(config) is not MarketCloseOutcomeAcknowledgementLagConfig:
        raise ValueError("config must be a MarketCloseOutcomeAcknowledgementLagConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_inputs
            ),
            key=lambda row: (_STATUS_WEIGHTS[row.lag_status], row.condition_id),
        ),
    )
    lag_status = _report_status(rows)
    return MarketCloseOutcomeAcknowledgementLagReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        total_market_count=_count_decimal(rows),
        blocked_market_count=_count_decimal(
            row for row in rows if row.lag_status == "blocked"
        ),
        watch_market_count=_count_decimal(row for row in rows if row.lag_status == "watch"),
        pass_market_count=_count_decimal(row for row in rows if row.lag_status == "pass"),
        acknowledged_market_count=_count_decimal(
            row for row in rows if row.team_acknowledged_at is not None
        ),
        missing_outcome_count=_reason_count(rows, "missing_outcome_confirmation"),
        stale_source_count=_reason_count(rows, "stale_source_confirmation"),
        late_acknowledgement_count=_reason_count(rows, "late_team_acknowledgement"),
        contradiction_count=_reason_count(rows, "outcome_source_contradiction"),
        unresolved_close_age_count=_reason_count(
            rows,
            "unresolved_close_age_exceeds_threshold",
        ),
        acknowledgement_completion_ratio=_ratio(
            _count_decimal(row for row in rows if row.team_acknowledged_at is not None),
            _count_decimal(rows),
        ),
        lag_status=lag_status,
        reason_codes=_report_reason_codes(rows, lag_status),
        rows=rows,
    )


def market_close_outcome_acknowledgement_lag_report_payload(
    report: MarketCloseOutcomeAcknowledgementLagReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseOutcomeAcknowledgementLagReport:
        raise ValueError("report must be a MarketCloseOutcomeAcknowledgementLagReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload(
        "market close outcome acknowledgement lag report",
        report,
    )
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("market close outcome acknowledgement lag report must be an object")
    return payload


def _row_from_input(
    item: MarketCloseOutcomeAcknowledgementLagInput,
    *,
    config: MarketCloseOutcomeAcknowledgementLagConfig,
    generated_at: datetime,
) -> MarketCloseOutcomeAcknowledgementLagRow:
    if item.closed_at > generated_at:
        raise ValueError("closed_at must not be after generated_at")
    _validate_not_after_generated_at(
        "outcome_confirmed_at",
        item.outcome_confirmed_at,
        generated_at,
    )
    _validate_not_after_generated_at(
        "source_confirmed_at",
        item.source_confirmed_at,
        generated_at,
    )
    _validate_not_after_generated_at(
        "team_acknowledged_at",
        item.team_acknowledged_at,
        generated_at,
    )
    close_age_seconds = _elapsed_seconds(item.closed_at, generated_at)
    close_to_outcome_seconds = _elapsed_seconds_or_none(
        item.closed_at,
        item.outcome_confirmed_at,
    )
    close_to_source_seconds = _elapsed_seconds_or_none(
        item.closed_at,
        item.source_confirmed_at,
    )
    acknowledgement_lag_seconds = _acknowledgement_lag_seconds(item)
    reason_codes = _row_reason_codes(
        item,
        close_age_seconds=close_age_seconds,
        close_to_source_seconds=close_to_source_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
        generated_at=generated_at,
    )
    return MarketCloseOutcomeAcknowledgementLagRow(
        condition_id=item.condition_id,
        closed_at=item.closed_at,
        outcome_confirmed_at=item.outcome_confirmed_at,
        source_confirmed_at=item.source_confirmed_at,
        team_acknowledged_at=item.team_acknowledged_at,
        outcome_value=item.outcome_value,
        source_outcome_value=item.source_outcome_value,
        source_reference=item.source_reference,
        close_age_seconds=close_age_seconds,
        close_to_outcome_seconds=close_to_outcome_seconds,
        close_to_source_seconds=close_to_source_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        unresolved_close_age_seconds=(
            close_age_seconds if item.team_acknowledged_at is None else _ZERO
        ),
        lag_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketCloseOutcomeAcknowledgementLagInput,
    *,
    close_age_seconds: Decimal,
    close_to_source_seconds: Decimal | None,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketCloseOutcomeAcknowledgementLagConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    codes: list[str] = []
    if (
        item.outcome_value is not None
        and item.source_outcome_value is not None
        and item.outcome_value != item.source_outcome_value
    ):
        codes.append("outcome_source_contradiction")
    if item.outcome_confirmed_at is None:
        codes.append("missing_outcome_confirmation")
    if (
        item.source_confirmed_at is None
        or close_to_source_seconds is None
        or close_to_source_seconds > config.stale_source_after_seconds
    ):
        codes.append("stale_source_confirmation")
    if _late_acknowledgement(
        item,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
        generated_at=generated_at,
    ):
        codes.append("late_team_acknowledgement")
    if (
        item.team_acknowledged_at is None
        and close_age_seconds > config.unresolved_close_after_seconds
    ):
        codes.append("unresolved_close_age_exceeds_threshold")
    if not codes:
        return (_CLEAR_REASON_CODE,)
    return tuple(codes)


def _late_acknowledgement(
    item: MarketCloseOutcomeAcknowledgementLagInput,
    *,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketCloseOutcomeAcknowledgementLagConfig,
    generated_at: datetime,
) -> bool:
    if acknowledgement_lag_seconds is not None:
        return acknowledgement_lag_seconds > config.late_acknowledgement_after_seconds
    reference_at = _latest_confirmation_at(item)
    if reference_at is None:
        return _elapsed_seconds(item.closed_at, generated_at) > (
            config.late_acknowledgement_after_seconds
        )
    return _elapsed_seconds(reference_at, generated_at) > (
        config.late_acknowledgement_after_seconds
    )


def _acknowledgement_lag_seconds(
    item: MarketCloseOutcomeAcknowledgementLagInput,
) -> Decimal | None:
    if item.team_acknowledged_at is None:
        return None
    reference_at = _latest_confirmation_at(item)
    if reference_at is None:
        reference_at = item.closed_at
    return _elapsed_seconds(reference_at, item.team_acknowledged_at)


def _latest_confirmation_at(
    item: MarketCloseOutcomeAcknowledgementLagInput,
) -> datetime | None:
    values = tuple(
        value
        for value in (item.outcome_confirmed_at, item.source_confirmed_at)
        if value is not None
    )
    if not values:
        return None
    return max(values)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "outcome_source_contradiction" in reason_codes
        or "missing_outcome_confirmation" in reason_codes
    ):
        return "blocked"
    if reason_codes == (_CLEAR_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[MarketCloseOutcomeAcknowledgementLagRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.lag_status == "blocked" for row in rows):
        return "blocked"
    if any(row.lag_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketCloseOutcomeAcknowledgementLagRow, ...],
    lag_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("no_closed_markets_to_assess",)
    codes = [_REPORT_STATUS_REASON_CODES[lag_status]]
    row_reason_codes = tuple(code for row in rows for code in row.reason_codes)
    for row_code, report_code in _ROW_REASON_TO_REPORT_REASON:
        if row_code in row_reason_codes:
            codes.append(report_code)
    return tuple(codes)


def _normalize_inputs(
    value: tuple[MarketCloseOutcomeAcknowledgementLagInput, ...]
    | list[MarketCloseOutcomeAcknowledgementLagInput],
) -> tuple[MarketCloseOutcomeAcknowledgementLagInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(value)
    seen_condition_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketCloseOutcomeAcknowledgementLagInput:
            raise ValueError(
                "inputs must contain MarketCloseOutcomeAcknowledgementLagInput values",
            )
        _require_hard_flags(item)
        if item.condition_id in seen_condition_ids:
            raise ValueError("inputs must not contain duplicate condition_id values")
        seen_condition_ids.add(item.condition_id)
    return normalized


def _normalize_rows(value: object) -> tuple[MarketCloseOutcomeAcknowledgementLagRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain MarketCloseOutcomeAcknowledgementLagRow values")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketCloseOutcomeAcknowledgementLagRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketCloseOutcomeAcknowledgementLagRow:
            raise ValueError(
                "rows must contain MarketCloseOutcomeAcknowledgementLagRow values",
            )
        _require_hard_flags(row)
    if rows != tuple(
        sorted(rows, key=lambda row: (_STATUS_WEIGHTS[row.lag_status], row.condition_id)),
    ):
        raise ValueError("rows must use deterministic lag sort")
    return rows


def _validate_confirmation_pair(
    label: str,
    confirmed_at: datetime | None,
    value: Decimal | None,
) -> None:
    if confirmed_at is None and value is not None:
        raise ValueError(f"{label} value must include confirmation time")
    if confirmed_at is not None and value is None:
        raise ValueError(f"{label} confirmation must include value")


def _validate_not_after_generated_at(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row_consistency(row: MarketCloseOutcomeAcknowledgementLagRow) -> None:
    if row.lag_status != _row_status(row.reason_codes):
        raise ValueError("lag_status must match reason_codes")
    if row.close_to_outcome_seconds != _elapsed_seconds_or_none(
        row.closed_at,
        row.outcome_confirmed_at,
    ):
        raise ValueError("close_to_outcome_seconds must match outcome confirmation")
    if row.close_to_source_seconds != _elapsed_seconds_or_none(
        row.closed_at,
        row.source_confirmed_at,
    ):
        raise ValueError("close_to_source_seconds must match source confirmation")
    if row.acknowledgement_lag_seconds != _expected_acknowledgement_lag_seconds(row):
        raise ValueError("acknowledgement_lag_seconds must match acknowledgement time")
    if row.team_acknowledged_at is not None and row.unresolved_close_age_seconds != _ZERO:
        raise ValueError("acknowledged rows must have zero unresolved close age")
    if (
        row.team_acknowledged_at is None
        and row.unresolved_close_age_seconds != row.close_age_seconds
    ):
        raise ValueError("unresolved_close_age_seconds must match close_age_seconds")


def _expected_acknowledgement_lag_seconds(
    row: MarketCloseOutcomeAcknowledgementLagRow,
) -> Decimal | None:
    if row.team_acknowledged_at is None:
        return None
    reference_at = max(
        value
        for value in (
            row.closed_at,
            row.outcome_confirmed_at,
            row.source_confirmed_at,
        )
        if value is not None
    )
    return _elapsed_seconds(reference_at, row.team_acknowledged_at)


def _validate_report_consistency(report: MarketCloseOutcomeAcknowledgementLagReport) -> None:
    if report.total_market_count != _count_decimal(report.rows):
        raise ValueError("total_market_count must match rows")
    if report.blocked_market_count != _count_decimal(
        row for row in report.rows if row.lag_status == "blocked"
    ):
        raise ValueError("blocked_market_count must match rows")
    if report.watch_market_count != _count_decimal(
        row for row in report.rows if row.lag_status == "watch"
    ):
        raise ValueError("watch_market_count must match rows")
    if report.pass_market_count != _count_decimal(
        row for row in report.rows if row.lag_status == "pass"
    ):
        raise ValueError("pass_market_count must match rows")
    acknowledged_market_count = _count_decimal(
        row for row in report.rows if row.team_acknowledged_at is not None
    )
    if report.acknowledged_market_count != acknowledged_market_count:
        raise ValueError("acknowledged_market_count must match rows")
    if report.missing_outcome_count != _reason_count(
        report.rows,
        "missing_outcome_confirmation",
    ):
        raise ValueError("missing_outcome_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "stale_source_confirmation",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.late_acknowledgement_count != _reason_count(
        report.rows,
        "late_team_acknowledgement",
    ):
        raise ValueError("late_acknowledgement_count must match rows")
    if report.contradiction_count != _reason_count(
        report.rows,
        "outcome_source_contradiction",
    ):
        raise ValueError("contradiction_count must match rows")
    if report.unresolved_close_age_count != _reason_count(
        report.rows,
        "unresolved_close_age_exceeds_threshold",
    ):
        raise ValueError("unresolved_close_age_count must match rows")
    if report.acknowledgement_completion_ratio != _ratio(
        acknowledged_market_count,
        report.total_market_count,
    ):
        raise ValueError("acknowledgement_completion_ratio must match rows")
    if report.lag_status != _report_status(report.rows):
        raise ValueError("lag_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.lag_status):
        raise ValueError("reason_codes must match rows")


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("timestamps must not move backward")
    delta = end - start
    whole_seconds = delta.days * 86400 + delta.seconds
    with localcontext(_DECIMAL_CONTEXT):
        return (
            Decimal(whole_seconds) + (Decimal(delta.microseconds) / Decimal(1000000))
        ).quantize(_QUANTUM)


def _elapsed_seconds_or_none(start: datetime, end: datetime | None) -> Decimal | None:
    if end is None:
        return None
    return _elapsed_seconds(start, end)


def _count_decimal(values: object) -> Decimal:
    if isinstance(values, (str, bytes)):
        raise ValueError("values must be iterable")
    try:
        count = sum(1 for _ in values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("values must be iterable") from exc
    return Decimal(count).quantize(_QUANTUM)


def _reason_count(
    rows: tuple[MarketCloseOutcomeAcknowledgementLagRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(row for row in rows if reason_code in row.reason_codes)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANTUM)


def _normalize_optional_seconds_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_seconds_decimal(field_name, value)


def _normalize_seconds_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_or_none(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain canonical strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain canonical strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(
        sorted(
            reason_codes,
            key=lambda reason_code: (
                _REASON_CODE_RANK.get(reason_code, len(_REASON_CODE_RANK)),
                reason_code,
            ),
        ),
    )


def _require_status(field_name: str, value: object) -> None:
    if value not in _LAG_STATUSES:
        raise ValueError(f"{field_name} must be one of {_LAG_STATUSES!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in _SHA256_HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} contains unsafe public surface")
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _derived_validation_digest(
    report: MarketCloseOutcomeAcknowledgementLagReport,
) -> str:
    encoded = json.dumps(
        _digest_payload_value(report),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_payload_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD_NAME
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat().replace("+00:00", "Z")
    if type(value) is tuple:
        return [_digest_payload_value(item) for item in value]
    if type(value) is list:
        return [_digest_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _digest_payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("derived_validation_digest source contains unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            MarketCloseOutcomeAcknowledgementLagConfig,
            MarketCloseOutcomeAcknowledgementLagInput,
            MarketCloseOutcomeAcknowledgementLagRow,
            MarketCloseOutcomeAcknowledgementLagReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        if not value.same_quantum(_QUANTUM):
            raise ValueError(f"{current_path} must be quantized to six decimals")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{current_path} keys must be strings")
            _reject_unsafe_public_text(current_path, key)
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat().replace("+00:00", "Z")
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


__all__ = (
    "DEFAULT_MARKET_CLOSE_OUTCOME_ACKNOWLEDGEMENT_LAG_CONFIG_VERSION",
    "MarketCloseOutcomeAcknowledgementLagConfig",
    "MarketCloseOutcomeAcknowledgementLagInput",
    "MarketCloseOutcomeAcknowledgementLagReport",
    "MarketCloseOutcomeAcknowledgementLagRow",
    "build_market_close_outcome_acknowledgement_lag_report",
    "market_close_outcome_acknowledgement_lag_report_payload",
)
