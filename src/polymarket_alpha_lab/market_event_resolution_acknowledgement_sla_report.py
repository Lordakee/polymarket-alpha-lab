"""Phase 1 market event resolution acknowledgement SLA report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION = (
    "market-event-resolution-acknowledgement-sla-report-v0"
)

REPORT_STATUSES = ("clear", "watch", "breached")
ACKNOWLEDGEMENT_STATUSES = ("acknowledged", "pending", "breached")
CONFLICT_STATUSES = ("none", "resolved", "unresolved")

CLEAR_REASON = "market_event_resolution_acknowledgement_sla_clear"
BREACHED_REASON = "market_event_resolution_acknowledgement_sla_breached"
PENDING_REASON = "market_event_resolution_acknowledgement_sla_pending"
MISSING_ACKNOWLEDGEMENT_REASON = "market_event_resolution_acknowledgement_missing"
LATE_ACKNOWLEDGEMENT_REASON = "market_event_resolution_acknowledgement_late"
MISSING_OFFICIAL_CHECK_REASON = "market_event_resolution_official_check_missing"
STALE_OFFICIAL_CHECK_REASON = "market_event_resolution_official_check_stale"
UNRESOLVED_CONFLICT_REASON = "market_event_resolution_unresolved_conflict"
MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON = (
    "market_event_resolution_postmortem_acknowledgement_missing"
)
LATE_POSTMORTEM_ACKNOWLEDGEMENT_REASON = (
    "market_event_resolution_postmortem_acknowledgement_late"
)

REASON_CODES = (
    CLEAR_REASON,
    BREACHED_REASON,
    PENDING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    LATE_ACKNOWLEDGEMENT_REASON,
    MISSING_OFFICIAL_CHECK_REASON,
    STALE_OFFICIAL_CHECK_REASON,
    UNRESOLVED_CONFLICT_REASON,
    MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON,
    LATE_POSTMORTEM_ACKNOWLEDGEMENT_REASON,
)

STATUS_RANK = {"breached": 0, "pending": 1, "acknowledged": 2}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketEventResolutionAcknowledgementSlaConfig:
    config_version: str = (
        DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION
    )
    default_acknowledgement_sla_seconds: Decimal = Decimal("86400.000000")
    market_family_acknowledgement_sla_seconds: tuple[tuple[str, Decimal], ...] = ()
    official_check_stale_seconds: Decimal = Decimal("3600.000000")
    postmortem_acknowledgement_sla_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "default_acknowledgement_sla_seconds",
            _require_positive_decimal(
                "default_acknowledgement_sla_seconds",
                self.default_acknowledgement_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "market_family_acknowledgement_sla_seconds",
            _normalize_market_family_sla_seconds(
                self.market_family_acknowledgement_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "official_check_stale_seconds",
            _require_positive_decimal(
                "official_check_stale_seconds",
                self.official_check_stale_seconds,
            ),
        )
        object.__setattr__(
            self,
            "postmortem_acknowledgement_sla_seconds",
            _require_positive_decimal(
                "postmortem_acknowledgement_sla_seconds",
                self.postmortem_acknowledgement_sla_seconds,
            ),
        )
        require_paper_only_flags("market event resolution acknowledgement SLA config", self)


@dataclass(frozen=True)
class MarketEventResolutionAcknowledgementSlaInputRow:
    team_id: str
    category_id: str
    market_family: str
    event_id: str
    event_resolved_at: datetime
    official_checked_at: datetime | None
    resolution_acknowledged_at: datetime | None
    conflict_status: str
    conflict_detected_at: datetime | None
    postmortem_required: bool
    postmortem_acknowledged_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("market_family", self.market_family)
        _require_public_string("event_id", self.event_id)
        object.__setattr__(
            self,
            "event_resolved_at",
            _as_utc("event_resolved_at", self.event_resolved_at),
        )
        for field_name in _OPTIONAL_TIME_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                normalized = _as_utc(field_name, value)
                if normalized < self.event_resolved_at:
                    raise ValueError(f"{field_name} must not be before event_resolved_at")
                object.__setattr__(self, field_name, normalized)
        _require_conflict_status("conflict_status", self.conflict_status)
        if self.conflict_status == "none" and self.conflict_detected_at is not None:
            raise ValueError("conflict_detected_at requires a conflict")
        if self.conflict_status != "none" and self.conflict_detected_at is None:
            raise ValueError("conflict_detected_at is required for conflicts")
        if type(self.postmortem_required) is not bool:
            raise ValueError("postmortem_required must be a bool")
        require_paper_only_flags(
            "market event resolution acknowledgement SLA input row",
            self,
        )


@dataclass(frozen=True)
class MarketEventResolutionAcknowledgementSlaRow:
    team_id: str
    category_id: str
    market_family: str
    event_id: str
    event_resolved_at: datetime
    official_checked_at: datetime | None
    resolution_acknowledged_at: datetime | None
    conflict_status: str
    conflict_detected_at: datetime | None
    postmortem_required: bool
    postmortem_acknowledged_at: datetime | None
    acknowledgement_sla_seconds: Decimal
    official_check_stale_seconds: Decimal
    postmortem_acknowledgement_sla_seconds: Decimal
    resolution_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal
    official_check_age_seconds: Decimal | None
    postmortem_acknowledgement_age_seconds: Decimal | None
    breach_seconds: Decimal
    acknowledgement_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("market_family", self.market_family)
        _require_public_string("event_id", self.event_id)
        object.__setattr__(
            self,
            "event_resolved_at",
            _as_utc("event_resolved_at", self.event_resolved_at),
        )
        for field_name in _OPTIONAL_TIME_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                normalized = _as_utc(field_name, value)
                if normalized < self.event_resolved_at:
                    raise ValueError(f"{field_name} must not be before event_resolved_at")
                object.__setattr__(self, field_name, normalized)
        _require_conflict_status("conflict_status", self.conflict_status)
        if self.conflict_status == "none" and self.conflict_detected_at is not None:
            raise ValueError("conflict_detected_at requires a conflict")
        if self.conflict_status != "none" and self.conflict_detected_at is None:
            raise ValueError("conflict_detected_at is required for conflicts")
        if type(self.postmortem_required) is not bool:
            raise ValueError("postmortem_required must be a bool")
        for field_name in (
            "acknowledgement_sla_seconds",
            "official_check_stale_seconds",
            "postmortem_acknowledgement_sla_seconds",
            "resolution_age_seconds",
            "acknowledgement_age_seconds",
            "breach_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.acknowledgement_sla_seconds <= ZERO:
            raise ValueError("acknowledgement_sla_seconds must be positive")
        if self.official_check_stale_seconds <= ZERO:
            raise ValueError("official_check_stale_seconds must be positive")
        if self.postmortem_acknowledgement_sla_seconds <= ZERO:
            raise ValueError("postmortem_acknowledgement_sla_seconds must be positive")
        object.__setattr__(
            self,
            "official_check_age_seconds",
            _normalize_optional_decimal(
                "official_check_age_seconds",
                self.official_check_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "postmortem_acknowledgement_age_seconds",
            _normalize_optional_decimal(
                "postmortem_acknowledgement_age_seconds",
                self.postmortem_acknowledgement_age_seconds,
            ),
        )
        _require_acknowledgement_status(
            "acknowledgement_status",
            self.acknowledgement_status,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_event_row(self)
        require_paper_only_flags("market event resolution acknowledgement SLA row", self)


@dataclass(frozen=True)
class MarketEventResolutionAcknowledgementSlaSummaryRow:
    team_id: str
    category_id: str
    market_family: str
    report_status: str
    event_count: Decimal
    exception_count: Decimal
    sla_breach_count: Decimal
    stale_official_check_count: Decimal
    missing_official_check_count: Decimal
    unresolved_conflict_count: Decimal
    missing_postmortem_acknowledgement_count: Decimal
    exception_ratio: Decimal
    max_resolution_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("market_family", self.market_family)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "event_count",
            "exception_count",
            "sla_breach_count",
            "stale_official_check_count",
            "missing_official_check_count",
            "unresolved_conflict_count",
            "missing_postmortem_acknowledgement_count",
            "exception_ratio",
            "max_resolution_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_summary_row(self)
        require_paper_only_flags(
            "market event resolution acknowledgement SLA summary row",
            self,
        )


@dataclass(frozen=True)
class MarketEventResolutionAcknowledgementSlaReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    event_count: Decimal
    acknowledged_event_count: Decimal
    pending_event_count: Decimal
    breached_event_count: Decimal
    exception_count: Decimal
    sla_breach_count: Decimal
    missing_acknowledgement_count: Decimal
    stale_official_check_count: Decimal
    missing_official_check_count: Decimal
    unresolved_conflict_count: Decimal
    missing_postmortem_acknowledgement_count: Decimal
    exception_ratio: Decimal
    max_resolution_age_seconds: Decimal
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...]
    market_family_summary_rows: tuple[
        MarketEventResolutionAcknowledgementSlaSummaryRow,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "event_count",
            "acknowledged_event_count",
            "pending_event_count",
            "breached_event_count",
            "exception_count",
            "sla_breach_count",
            "missing_acknowledgement_count",
            "stale_official_check_count",
            "missing_official_check_count",
            "unresolved_conflict_count",
            "missing_postmortem_acknowledgement_count",
            "exception_ratio",
            "max_resolution_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "market_family_summary_rows",
            _normalize_summary_rows(self.market_family_summary_rows),
        )
        _validate_report(self)
        require_paper_only_flags("market event resolution acknowledgement SLA report", self)
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
            _require_report_validation_digest(self)


_OPTIONAL_TIME_FIELDS = (
    "official_checked_at",
    "resolution_acknowledged_at",
    "conflict_detected_at",
    "postmortem_acknowledged_at",
)


def build_market_event_resolution_acknowledgement_sla_report(
    input_rows: list[MarketEventResolutionAcknowledgementSlaInputRow]
    | tuple[MarketEventResolutionAcknowledgementSlaInputRow, ...],
    *,
    config: MarketEventResolutionAcknowledgementSlaConfig,
    generated_at: datetime,
) -> MarketEventResolutionAcknowledgementSlaReport:
    if type(config) is not MarketEventResolutionAcknowledgementSlaConfig:
        raise ValueError(
            "config must be a MarketEventResolutionAcknowledgementSlaConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    report_rows = _sort_rows(
        tuple(
            _event_row(row, config=config, generated_at=generated_at_utc)
            for row in rows
        ),
    )
    reason_codes = _report_reason_codes(report_rows)

    return MarketEventResolutionAcknowledgementSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        event_count=_decimal_count(len(report_rows)),
        acknowledged_event_count=_status_count(report_rows, "acknowledged"),
        pending_event_count=_status_count(report_rows, "pending"),
        breached_event_count=_status_count(report_rows, "breached"),
        exception_count=_exception_count(report_rows),
        sla_breach_count=_reason_count(report_rows, BREACHED_REASON),
        missing_acknowledgement_count=_missing_acknowledgement_count(report_rows),
        stale_official_check_count=_reason_count(report_rows, STALE_OFFICIAL_CHECK_REASON),
        missing_official_check_count=_reason_count(
            report_rows,
            MISSING_OFFICIAL_CHECK_REASON,
        ),
        unresolved_conflict_count=_reason_count(report_rows, UNRESOLVED_CONFLICT_REASON),
        missing_postmortem_acknowledgement_count=_reason_count(
            report_rows,
            MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON,
        ),
        exception_ratio=_ratio(_exception_count(report_rows), _decimal_count(len(report_rows))),
        max_resolution_age_seconds=_max_resolution_age_seconds(report_rows),
        rows=report_rows,
        market_family_summary_rows=_summary_rows(report_rows),
    )


def market_event_resolution_acknowledgement_sla_report_to_payload(
    report: MarketEventResolutionAcknowledgementSlaReport,
) -> dict[str, Any]:
    if type(report) is not MarketEventResolutionAcknowledgementSlaReport:
        raise ValueError("report must be a MarketEventResolutionAcknowledgementSlaReport")
    _validate_report_public_numeric_types(report)
    _require_report_validation_digest(report)
    require_paper_only_flags(
        "market event resolution acknowledgement SLA report",
        report,
    )
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    validate_market_event_resolution_acknowledgement_sla_public_payload(ready)
    return ready


def validate_market_event_resolution_acknowledgement_sla_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "market event resolution acknowledgement SLA payload",
        payload,
    )
    _require_public_payload_flags(payload, require_current=True)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketEventResolutionAcknowledgementSlaInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketEventResolutionAcknowledgementSlaInputRow:
            raise ValueError("input rows must contain SLA input rows")
        require_paper_only_flags(
            "market event resolution acknowledgement SLA input row",
            row,
        )
        if row.event_resolved_at > generated_at:
            raise ValueError("event_resolved_at must not be in the future")
        for field_name in _OPTIONAL_TIME_FIELDS:
            value_at = getattr(row, field_name)
            if value_at is None:
                continue
            if value_at > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
            if value_at < row.event_resolved_at:
                raise ValueError(f"{field_name} must not be before event_resolved_at")
        key = (row.team_id, row.event_id)
        if key in seen:
            raise ValueError("event_id values must be unique per team")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.team_id,
                row.category_id,
                row.market_family,
                row.event_id,
            ),
        ),
    )


def _event_row(
    row: MarketEventResolutionAcknowledgementSlaInputRow,
    *,
    config: MarketEventResolutionAcknowledgementSlaConfig,
    generated_at: datetime,
) -> MarketEventResolutionAcknowledgementSlaRow:
    resolution_age_seconds = _age_seconds(generated_at, row.event_resolved_at)
    acknowledgement_sla_seconds = _acknowledgement_sla_seconds(row.market_family, config)
    acknowledgement_age_seconds = (
        resolution_age_seconds
        if row.resolution_acknowledged_at is None
        else _age_seconds(row.resolution_acknowledged_at, row.event_resolved_at)
    )
    acknowledgement_breach_seconds = _seconds_over_sla(
        acknowledgement_age_seconds,
        acknowledgement_sla_seconds,
    )
    official_check_age_seconds = (
        None
        if row.official_checked_at is None
        else _age_seconds(generated_at, row.official_checked_at)
    )
    postmortem_age_seconds = _postmortem_age_seconds(
        row,
        resolution_age_seconds=resolution_age_seconds,
    )
    postmortem_breach_seconds = (
        ZERO
        if not row.postmortem_required or postmortem_age_seconds is None
        else _seconds_over_sla(
            postmortem_age_seconds,
            config.postmortem_acknowledgement_sla_seconds,
        )
    )
    breach_seconds = max(
        acknowledgement_breach_seconds,
        postmortem_breach_seconds,
    ).quantize(QUANT)
    reason_codes = _row_reason_codes(
        row,
        acknowledgement_breach_seconds=acknowledgement_breach_seconds,
        official_check_age_seconds=official_check_age_seconds,
        official_check_stale_seconds=config.official_check_stale_seconds,
        postmortem_breach_seconds=postmortem_breach_seconds,
    )

    return MarketEventResolutionAcknowledgementSlaRow(
        team_id=row.team_id,
        category_id=row.category_id,
        market_family=row.market_family,
        event_id=row.event_id,
        event_resolved_at=row.event_resolved_at,
        official_checked_at=row.official_checked_at,
        resolution_acknowledged_at=row.resolution_acknowledged_at,
        conflict_status=row.conflict_status,
        conflict_detected_at=row.conflict_detected_at,
        postmortem_required=row.postmortem_required,
        postmortem_acknowledged_at=row.postmortem_acknowledged_at,
        acknowledgement_sla_seconds=acknowledgement_sla_seconds,
        official_check_stale_seconds=config.official_check_stale_seconds,
        postmortem_acknowledgement_sla_seconds=(
            config.postmortem_acknowledgement_sla_seconds
        ),
        resolution_age_seconds=resolution_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        official_check_age_seconds=official_check_age_seconds,
        postmortem_acknowledgement_age_seconds=postmortem_age_seconds,
        breach_seconds=breach_seconds,
        acknowledgement_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _postmortem_age_seconds(
    row: MarketEventResolutionAcknowledgementSlaInputRow,
    *,
    resolution_age_seconds: Decimal,
) -> Decimal | None:
    if not row.postmortem_required and row.postmortem_acknowledged_at is None:
        return None
    if row.postmortem_acknowledged_at is None:
        return resolution_age_seconds
    return _age_seconds(row.postmortem_acknowledged_at, row.event_resolved_at)


def _row_reason_codes(
    row: MarketEventResolutionAcknowledgementSlaInputRow,
    *,
    acknowledgement_breach_seconds: Decimal,
    official_check_age_seconds: Decimal | None,
    official_check_stale_seconds: Decimal,
    postmortem_breach_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.resolution_acknowledged_at is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_breach_seconds > ZERO:
        reasons.append(LATE_ACKNOWLEDGEMENT_REASON)
    if row.official_checked_at is None:
        reasons.append(MISSING_OFFICIAL_CHECK_REASON)
    elif (
        official_check_age_seconds is not None
        and official_check_age_seconds > official_check_stale_seconds
    ):
        reasons.append(STALE_OFFICIAL_CHECK_REASON)
    if row.conflict_status == "unresolved":
        reasons.append(UNRESOLVED_CONFLICT_REASON)
    if row.postmortem_required and row.postmortem_acknowledged_at is None:
        reasons.append(MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON)
    elif row.postmortem_required and postmortem_breach_seconds > ZERO:
        reasons.append(LATE_POSTMORTEM_ACKNOWLEDGEMENT_REASON)

    if acknowledgement_breach_seconds > ZERO or postmortem_breach_seconds > ZERO:
        reasons.insert(0, BREACHED_REASON)
    elif reasons:
        reasons.insert(0, PENDING_REASON)
    else:
        reasons.append(CLEAR_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BREACHED_REASON in reason_codes:
        return "breached"
    if PENDING_REASON in reason_codes:
        return "pending"
    return "acknowledged"


def _summary_rows(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> tuple[MarketEventResolutionAcknowledgementSlaSummaryRow, ...]:
    grouped: dict[tuple[str, str, str], list[MarketEventResolutionAcknowledgementSlaRow]] = {}
    for row in rows:
        key = (row.team_id, row.category_id, row.market_family)
        grouped.setdefault(key, []).append(row)
    return tuple(
        _summary_row(team_id, category_id, market_family, tuple(group_rows))
        for (team_id, category_id, market_family), group_rows in sorted(grouped.items())
    )


def _summary_row(
    team_id: str,
    category_id: str,
    market_family: str,
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> MarketEventResolutionAcknowledgementSlaSummaryRow:
    reason_codes = _report_reason_codes(rows)
    return MarketEventResolutionAcknowledgementSlaSummaryRow(
        team_id=team_id,
        category_id=category_id,
        market_family=market_family,
        report_status=_status_from_reason_codes(reason_codes),
        event_count=_decimal_count(len(rows)),
        exception_count=_exception_count(rows),
        sla_breach_count=_reason_count(rows, BREACHED_REASON),
        stale_official_check_count=_reason_count(rows, STALE_OFFICIAL_CHECK_REASON),
        missing_official_check_count=_reason_count(rows, MISSING_OFFICIAL_CHECK_REASON),
        unresolved_conflict_count=_reason_count(rows, UNRESOLVED_CONFLICT_REASON),
        missing_postmortem_acknowledgement_count=_reason_count(
            rows,
            MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON,
        ),
        exception_ratio=_ratio(_exception_count(rows), _decimal_count(len(rows))),
        max_resolution_age_seconds=_max_resolution_age_seconds(rows),
        reason_codes=reason_codes,
    )


def _report_reason_codes(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BREACHED_REASON in reason_codes:
        return "breached"
    if PENDING_REASON in reason_codes:
        return "watch"
    return "clear"


def _normalize_market_family_sla_seconds(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("market_family_acknowledgement_sla_seconds must be a list or tuple")
    rows = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError(
                "market_family_acknowledgement_sla_seconds rows must contain family and SLA",
            )
        market_family, sla_seconds = row
        _require_public_string("market_family", market_family)
        if market_family in seen:
            raise ValueError("market_family_acknowledgement_sla_seconds must be unique")
        seen.add(market_family)
        normalized.append(
            (
                market_family,
                _require_positive_decimal(
                    "market_family_acknowledgement_sla_seconds",
                    sla_seconds,
                ),
            ),
        )
    return tuple(sorted(normalized, key=lambda row: row[0]))


def _normalize_rows(
    value: object,
) -> tuple[MarketEventResolutionAcknowledgementSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketEventResolutionAcknowledgementSlaRow:
            raise ValueError("rows must contain acknowledgement SLA rows")
        require_paper_only_flags("market event resolution acknowledgement SLA row", row)
        key = (row.team_id, row.event_id)
        if key in seen:
            raise ValueError("rows must be unique per team and event_id")
        seen.add(key)
    expected = _sort_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_summary_rows(
    value: object,
) -> tuple[MarketEventResolutionAcknowledgementSlaSummaryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("market_family_summary_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketEventResolutionAcknowledgementSlaSummaryRow:
            raise ValueError("market_family_summary_rows must contain summary rows")
        require_paper_only_flags(
            "market event resolution acknowledgement SLA summary row",
            row,
        )
        key = (row.team_id, row.category_id, row.market_family)
        if key in seen:
            raise ValueError("market_family_summary_rows must be unique")
        seen.add(key)
    expected = tuple(sorted(rows, key=lambda row: (row.team_id, row.category_id, row.market_family)))
    if rows != expected:
        raise ValueError("market_family_summary_rows must be sorted deterministically")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _sort_rows(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> tuple[MarketEventResolutionAcknowledgementSlaRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.acknowledgement_status],
                -row.breach_seconds,
                -row.resolution_age_seconds,
                row.team_id,
                row.category_id,
                row.market_family,
                row.event_id,
            ),
        ),
    )


def _acknowledgement_sla_seconds(
    market_family: str,
    config: MarketEventResolutionAcknowledgementSlaConfig,
) -> Decimal:
    family_slas = dict(config.market_family_acknowledgement_sla_seconds)
    return family_slas.get(market_family, config.default_acknowledgement_sla_seconds)


def _validate_event_row(row: MarketEventResolutionAcknowledgementSlaRow) -> None:
    if row.acknowledgement_age_seconds != (
        row.resolution_age_seconds
        if row.resolution_acknowledged_at is None
        else _age_seconds(row.resolution_acknowledged_at, row.event_resolved_at)
    ):
        raise ValueError("acknowledgement_age_seconds must match acknowledgement time")
    if row.official_checked_at is None:
        if row.official_check_age_seconds is not None:
            raise ValueError("official_check_age_seconds requires official_checked_at")
    else:
        expected_official_age = _age_seconds(
            _event_row_reference_now(row),
            row.official_checked_at,
        )
        if row.official_check_age_seconds != expected_official_age:
            raise ValueError("official_check_age_seconds must match official_checked_at")
    expected_postmortem_age = _expected_postmortem_age_seconds(row)
    if row.postmortem_acknowledgement_age_seconds != expected_postmortem_age:
        raise ValueError(
            "postmortem_acknowledgement_age_seconds must match postmortem state",
        )
    acknowledgement_breach_seconds = _seconds_over_sla(
        row.acknowledgement_age_seconds,
        row.acknowledgement_sla_seconds,
    )
    postmortem_breach_seconds = (
        ZERO
        if expected_postmortem_age is None or not row.postmortem_required
        else _seconds_over_sla(
            expected_postmortem_age,
            row.postmortem_acknowledgement_sla_seconds,
        )
    )
    if row.breach_seconds != max(
        acknowledgement_breach_seconds,
        postmortem_breach_seconds,
    ).quantize(QUANT):
        raise ValueError("breach_seconds must match SLA overage")
    expected_reason_codes = _expected_reason_codes_from_row(row)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row state")
    if row.acknowledgement_status != _row_status(row.reason_codes):
        raise ValueError("acknowledgement_status must match reason_codes")


def _event_row_reference_now(row: MarketEventResolutionAcknowledgementSlaRow) -> datetime:
    return row.event_resolved_at + _seconds_to_timedelta(row.resolution_age_seconds)


def _seconds_to_timedelta(value: Decimal) -> timedelta:
    seconds = int(value)
    microseconds = int((value - Decimal(seconds)) * MICROSECONDS_PER_SECOND)
    return timedelta(seconds=seconds, microseconds=microseconds)


def _expected_postmortem_age_seconds(
    row: MarketEventResolutionAcknowledgementSlaRow,
) -> Decimal | None:
    if not row.postmortem_required and row.postmortem_acknowledged_at is None:
        return None
    if row.postmortem_acknowledged_at is None:
        return row.resolution_age_seconds
    return _age_seconds(row.postmortem_acknowledged_at, row.event_resolved_at)


def _expected_reason_codes_from_row(
    row: MarketEventResolutionAcknowledgementSlaRow,
) -> tuple[str, ...]:
    acknowledgement_breach_seconds = _seconds_over_sla(
        row.acknowledgement_age_seconds,
        row.acknowledgement_sla_seconds,
    )
    postmortem_breach_seconds = (
        ZERO
        if not row.postmortem_required or row.postmortem_acknowledgement_age_seconds is None
        else _seconds_over_sla(
            row.postmortem_acknowledgement_age_seconds,
            row.postmortem_acknowledgement_sla_seconds,
        )
    )
    input_like = MarketEventResolutionAcknowledgementSlaInputRow(
        team_id=row.team_id,
        category_id=row.category_id,
        market_family=row.market_family,
        event_id=row.event_id,
        event_resolved_at=row.event_resolved_at,
        official_checked_at=row.official_checked_at,
        resolution_acknowledged_at=row.resolution_acknowledged_at,
        conflict_status=row.conflict_status,
        conflict_detected_at=row.conflict_detected_at,
        postmortem_required=row.postmortem_required,
        postmortem_acknowledged_at=row.postmortem_acknowledged_at,
    )
    return _row_reason_codes(
        input_like,
        acknowledgement_breach_seconds=acknowledgement_breach_seconds,
        official_check_age_seconds=row.official_check_age_seconds,
        official_check_stale_seconds=row.official_check_stale_seconds,
        postmortem_breach_seconds=postmortem_breach_seconds,
    )


def _validate_summary_row(row: MarketEventResolutionAcknowledgementSlaSummaryRow) -> None:
    if row.exception_count > row.event_count:
        raise ValueError("exception_count must not exceed event_count")
    if row.sla_breach_count > row.exception_count:
        raise ValueError("sla_breach_count must not exceed exception_count")
    if row.exception_ratio != _ratio(row.exception_count, row.event_count):
        raise ValueError("exception_ratio must match event_count")
    if row.report_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _validate_report(report: MarketEventResolutionAcknowledgementSlaReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.acknowledged_event_count != _status_count(report.rows, "acknowledged"):
        raise ValueError("acknowledged_event_count must match rows")
    if report.pending_event_count != _status_count(report.rows, "pending"):
        raise ValueError("pending_event_count must match rows")
    if report.breached_event_count != _status_count(report.rows, "breached"):
        raise ValueError("breached_event_count must match rows")
    if (
        report.acknowledged_event_count
        + report.pending_event_count
        + report.breached_event_count
        != report.event_count
    ):
        raise ValueError("status counts must sum to event_count")
    if report.exception_count != _exception_count(report.rows):
        raise ValueError("exception_count must match rows")
    if report.sla_breach_count != _reason_count(report.rows, BREACHED_REASON):
        raise ValueError("sla_breach_count must match rows")
    if report.missing_acknowledgement_count != _missing_acknowledgement_count(report.rows):
        raise ValueError("missing_acknowledgement_count must match rows")
    if report.stale_official_check_count != _reason_count(
        report.rows,
        STALE_OFFICIAL_CHECK_REASON,
    ):
        raise ValueError("stale_official_check_count must match rows")
    if report.missing_official_check_count != _reason_count(
        report.rows,
        MISSING_OFFICIAL_CHECK_REASON,
    ):
        raise ValueError("missing_official_check_count must match rows")
    if report.unresolved_conflict_count != _reason_count(
        report.rows,
        UNRESOLVED_CONFLICT_REASON,
    ):
        raise ValueError("unresolved_conflict_count must match rows")
    if report.missing_postmortem_acknowledgement_count != _reason_count(
        report.rows,
        MISSING_POSTMORTEM_ACKNOWLEDGEMENT_REASON,
    ):
        raise ValueError("missing_postmortem_acknowledgement_count must match rows")
    if report.exception_ratio != _ratio(report.exception_count, report.event_count):
        raise ValueError("exception_ratio must match rows")
    if report.max_resolution_age_seconds != _max_resolution_age_seconds(report.rows):
        raise ValueError("max_resolution_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.market_family_summary_rows != _summary_rows(report.rows):
        raise ValueError("market_family_summary_rows must match rows")


def _require_report_validation_digest(
    report: MarketEventResolutionAcknowledgementSlaReport,
) -> None:
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: MarketEventResolutionAcknowledgementSlaReport,
) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload_for_digest(report),
    )


def _report_public_payload_for_digest(
    report: MarketEventResolutionAcknowledgementSlaReport,
) -> dict[str, Any]:
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report JSON value must be an object")
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


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_payload_flags(
    value: object,
    *,
    require_current: bool = False,
) -> None:
    flag_names = ("paper_only", "report_only", "readonly")
    if isinstance(value, dict):
        has_flag = any(flag_name in value for flag_name in flag_names)
        if require_current or has_flag:
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _require_public_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_public_payload_flags(item)


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    reject_unsafe_surface_fields(label, value)
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public text in {label}")


def _status_count(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.acknowledgement_status == status))


def _exception_count(rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...]) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if row.acknowledgement_status != "acknowledged"),
    )


def _reason_count(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _missing_acknowledgement_count(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.resolution_acknowledged_at is None))


def _max_resolution_age_seconds(
    rows: tuple[MarketEventResolutionAcknowledgementSlaRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.resolution_age_seconds for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _seconds_over_sla(duration_seconds: Decimal, sla_seconds: Decimal) -> Decimal:
    if duration_seconds <= sla_seconds:
        return ZERO
    return (duration_seconds - sla_seconds).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _validate_report_public_numeric_types(
    report: MarketEventResolutionAcknowledgementSlaReport,
) -> None:
    for field_name in (
        "event_count",
        "acknowledged_event_count",
        "pending_event_count",
        "breached_event_count",
        "exception_count",
        "sla_breach_count",
        "missing_acknowledgement_count",
        "stale_official_check_count",
        "missing_official_check_count",
        "unresolved_conflict_count",
        "missing_postmortem_acknowledgement_count",
        "exception_ratio",
        "max_resolution_age_seconds",
    ):
        if type(getattr(report, field_name)) is not Decimal:
            raise ValueError(f"{field_name} must be a Decimal")
    for row in report.rows:
        for field_name in (
            "acknowledgement_sla_seconds",
            "official_check_stale_seconds",
            "postmortem_acknowledgement_sla_seconds",
            "resolution_age_seconds",
            "acknowledgement_age_seconds",
            "breach_seconds",
        ):
            if type(getattr(row, field_name)) is not Decimal:
                raise ValueError(f"{field_name} must be a Decimal")
        for field_name in (
            "official_check_age_seconds",
            "postmortem_acknowledgement_age_seconds",
        ):
            value = getattr(row, field_name)
            if value is not None and type(value) is not Decimal:
                raise ValueError(f"{field_name} must be a Decimal")
    for summary_row in report.market_family_summary_rows:
        for field_name in (
            "event_count",
            "exception_count",
            "sla_breach_count",
            "stale_official_check_count",
            "missing_official_check_count",
            "unresolved_conflict_count",
            "missing_postmortem_acknowledgement_count",
            "exception_ratio",
            "max_resolution_age_seconds",
        ):
            if type(getattr(summary_row, field_name)) is not Decimal:
                raise ValueError(f"{field_name} must be a Decimal")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or breached")


def _require_acknowledgement_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACKNOWLEDGEMENT_STATUSES:
        raise ValueError(f"{field_name} must be acknowledged, pending, or breached")


def _require_conflict_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CONFLICT_STATUSES:
        raise ValueError(f"{field_name} must be none, resolved, or unresolved")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


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
    "DEFAULT_MARKET_EVENT_RESOLUTION_ACKNOWLEDGEMENT_SLA_REPORT_CONFIG_VERSION",
    "MarketEventResolutionAcknowledgementSlaConfig",
    "MarketEventResolutionAcknowledgementSlaInputRow",
    "MarketEventResolutionAcknowledgementSlaReport",
    "MarketEventResolutionAcknowledgementSlaRow",
    "MarketEventResolutionAcknowledgementSlaSummaryRow",
    "build_market_event_resolution_acknowledgement_sla_report",
    "market_event_resolution_acknowledgement_sla_report_to_payload",
    "validate_market_event_resolution_acknowledgement_sla_public_payload",
)
