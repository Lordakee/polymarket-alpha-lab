"""In-memory research queue event freshness sweep report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_EVENT_FRESHNESS_SWEEP_CONFIG_VERSION = (
    "research-event-freshness-sweep-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_DEFAULT_INFORMATION_REFRESH_WATCH_AFTER_SECONDS = Decimal("7200.000000")
_DEFAULT_INFORMATION_REFRESH_BLOCK_AFTER_SECONDS = Decimal("21600.000000")
_DEFAULT_EVIDENCE_WATCH_AFTER_SECONDS = Decimal("14400.000000")
_DEFAULT_EVIDENCE_BLOCK_AFTER_SECONDS = Decimal("43200.000000")
_DEFAULT_SETTLEMENT_WATCH_WITHIN_SECONDS = Decimal("86400.000000")
_DEFAULT_SETTLEMENT_BLOCK_WITHIN_SECONDS = Decimal("3600.000000")
_DEFAULT_MAX_SETTLEMENT_HORIZON_SECONDS = Decimal("31536000.000000")

_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHTS = {"block": 0, "watch": 1, "pass": 2}
_CLEAR_REASON_CODE = "freshness_sweep_pass"
_DIGEST_FIELD_NAME = "derived_validation_digest"
_SHA256_HEX_CHARS = frozenset("0123456789abcdef")

_BLOCK_REASON_CODES = frozenset(
    (
        "missing_information_refresh",
        "information_refresh_block_stale",
        "missing_evidence_observation",
        "evidence_block_stale",
        "settlement_due_or_past",
        "settlement_block_window",
        "domain_owner_missing",
    ),
)
_INFORMATION_REFRESH_REASON_CODES = frozenset(
    (
        "missing_information_refresh",
        "information_refresh_watch_stale",
        "information_refresh_block_stale",
    ),
)
_STALE_EVIDENCE_REASON_CODES = frozenset(
    (
        "missing_evidence_observation",
        "evidence_watch_stale",
        "evidence_block_stale",
    ),
)
_SETTLEMENT_WINDOW_REASON_CODES = frozenset(
    (
        "settlement_due_or_past",
        "settlement_block_window",
        "settlement_watch_window",
    ),
)
_SENSITIVE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "text",
)
_REPORT_STATUS_REASON_CODES = {
    "block": "freshness_sweep_block",
    "watch": "freshness_sweep_watch",
    "pass": _CLEAR_REASON_CODE,
}
_ROW_REASON_TO_REPORT_REASON = (
    (_INFORMATION_REFRESH_REASON_CODES, "information_refresh_needed_present"),
    (_STALE_EVIDENCE_REASON_CODES, "stale_evidence_present"),
    (_SETTLEMENT_WINDOW_REASON_CODES, "settlement_window_present"),
    (frozenset(("domain_owner_missing",)), "domain_owner_missing_present"),
    (frozenset(("review_required",)), "review_required_present"),
    (frozenset(("manual_review_pending",)), "pending_review_present"),
)
_REASON_CODE_RANK = {
    "freshness_sweep_block": 0,
    "freshness_sweep_watch": 1,
    _CLEAR_REASON_CODE: 2,
    "no_queue_events_to_sweep": 3,
    "missing_information_refresh": 10,
    "information_refresh_block_stale": 11,
    "information_refresh_watch_stale": 12,
    "missing_evidence_observation": 20,
    "evidence_block_stale": 21,
    "evidence_watch_stale": 22,
    "settlement_due_or_past": 30,
    "settlement_block_window": 31,
    "settlement_watch_window": 32,
    "missing_settlement_at": 33,
    "domain_owner_missing": 40,
    "manual_review_pending": 50,
    "review_required": 60,
    "information_refresh_needed_present": 100,
    "stale_evidence_present": 101,
    "settlement_window_present": 102,
    "domain_owner_missing_present": 103,
    "review_required_present": 104,
    "pending_review_present": 105,
}


__all__ = (
    "DEFAULT_RESEARCH_MARKET_EVENT_FRESHNESS_SWEEP_CONFIG_VERSION",
    "ResearchMarketEventFreshnessSweepConfig",
    "ResearchMarketEventFreshnessSweepInput",
    "ResearchMarketEventFreshnessSweepReport",
    "ResearchMarketEventFreshnessSweepRow",
    "build_research_market_event_freshness_sweep_report",
    "research_market_event_freshness_sweep_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketEventFreshnessSweepConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_EVENT_FRESHNESS_SWEEP_CONFIG_VERSION
    information_refresh_watch_after_seconds: Decimal = (
        _DEFAULT_INFORMATION_REFRESH_WATCH_AFTER_SECONDS
    )
    information_refresh_block_after_seconds: Decimal = (
        _DEFAULT_INFORMATION_REFRESH_BLOCK_AFTER_SECONDS
    )
    evidence_watch_after_seconds: Decimal = _DEFAULT_EVIDENCE_WATCH_AFTER_SECONDS
    evidence_block_after_seconds: Decimal = _DEFAULT_EVIDENCE_BLOCK_AFTER_SECONDS
    settlement_watch_within_seconds: Decimal = _DEFAULT_SETTLEMENT_WATCH_WITHIN_SECONDS
    settlement_block_within_seconds: Decimal = _DEFAULT_SETTLEMENT_BLOCK_WITHIN_SECONDS
    max_settlement_horizon_seconds: Decimal = _DEFAULT_MAX_SETTLEMENT_HORIZON_SECONDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "information_refresh_watch_after_seconds",
            "information_refresh_block_after_seconds",
            "evidence_watch_after_seconds",
            "evidence_block_after_seconds",
            "settlement_watch_within_seconds",
            "settlement_block_within_seconds",
            "max_settlement_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.information_refresh_block_after_seconds
            <= self.information_refresh_watch_after_seconds
        ):
            raise ValueError(
                "information_refresh_block_after_seconds must be greater than "
                "information_refresh_watch_after_seconds",
            )
        if self.evidence_block_after_seconds <= self.evidence_watch_after_seconds:
            raise ValueError(
                "evidence_block_after_seconds must be greater than "
                "evidence_watch_after_seconds",
            )
        if self.settlement_watch_within_seconds <= self.settlement_block_within_seconds:
            raise ValueError(
                "settlement_watch_within_seconds must be greater than "
                "settlement_block_within_seconds",
            )
        if self.max_settlement_horizon_seconds <= self.settlement_watch_within_seconds:
            raise ValueError(
                "max_settlement_horizon_seconds must be greater than "
                "settlement_watch_within_seconds",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketEventFreshnessSweepInput:
    queue_item_id: str
    last_information_refresh_at: datetime | None = None
    latest_evidence_observed_at: datetime | None = None
    settlement_at: datetime | None = None
    domain_owner_present: bool = False
    manual_review_requested: bool = False
    review_completed_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("queue_item_id", self.queue_item_id)
        for field_name in (
            "last_information_refresh_at",
            "latest_evidence_observed_at",
            "settlement_at",
            "review_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        _require_bool("domain_owner_present", self.domain_owner_present)
        _require_bool("manual_review_requested", self.manual_review_requested)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketEventFreshnessSweepRow:
    queue_item_id: str
    last_information_refresh_at: datetime | None
    latest_evidence_observed_at: datetime | None
    settlement_at: datetime | None
    information_refresh_age_seconds: Decimal | None
    evidence_age_seconds: Decimal | None
    settlement_seconds_remaining: Decimal | None
    domain_owner_present: bool
    manual_review_requested: bool
    review_completed_at: datetime | None
    review_required: bool
    sweep_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("queue_item_id", self.queue_item_id)
        for field_name in (
            "last_information_refresh_at",
            "latest_evidence_observed_at",
            "settlement_at",
            "review_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "information_refresh_age_seconds",
            "evidence_age_seconds",
            "settlement_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_bool("domain_owner_present", self.domain_owner_present)
        _require_bool("manual_review_requested", self.manual_review_requested)
        _require_bool("review_required", self.review_required)
        _require_status("sweep_status", self.sweep_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketEventFreshnessSweepReport:
    generated_at: datetime
    config_version: str
    queue_item_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    information_refresh_needed_count: Decimal
    stale_evidence_count: Decimal
    settlement_window_count: Decimal
    missing_domain_owner_count: Decimal
    review_required_count: Decimal
    pending_review_count: Decimal
    sweep_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketEventFreshnessSweepRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "queue_item_count",
            "block_count",
            "watch_count",
            "pass_count",
            "information_refresh_needed_count",
            "stale_evidence_count",
            "settlement_window_count",
            "missing_domain_owner_count",
            "review_required_count",
            "pending_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("sweep_status", self.sweep_status)
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
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_hard_flags(self)


def build_research_market_event_freshness_sweep_report(
    inputs: tuple[ResearchMarketEventFreshnessSweepInput, ...]
    | list[ResearchMarketEventFreshnessSweepInput],
    *,
    config: ResearchMarketEventFreshnessSweepConfig,
    generated_at: datetime,
) -> ResearchMarketEventFreshnessSweepReport:
    if type(config) is not ResearchMarketEventFreshnessSweepConfig:
        raise ValueError("config must be a ResearchMarketEventFreshnessSweepConfig")
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
            key=lambda row: (_STATUS_WEIGHTS[row.sweep_status], row.queue_item_id),
        ),
    )
    sweep_status = _report_status(rows)
    return ResearchMarketEventFreshnessSweepReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_item_count=_count_decimal(rows),
        block_count=_count_decimal(row for row in rows if row.sweep_status == "block"),
        watch_count=_count_decimal(row for row in rows if row.sweep_status == "watch"),
        pass_count=_count_decimal(row for row in rows if row.sweep_status == "pass"),
        information_refresh_needed_count=_reason_family_count(
            rows,
            _INFORMATION_REFRESH_REASON_CODES,
        ),
        stale_evidence_count=_reason_family_count(rows, _STALE_EVIDENCE_REASON_CODES),
        settlement_window_count=_reason_family_count(rows, _SETTLEMENT_WINDOW_REASON_CODES),
        missing_domain_owner_count=_reason_count(rows, "domain_owner_missing"),
        review_required_count=_count_decimal(row for row in rows if row.review_required),
        pending_review_count=_reason_count(rows, "manual_review_pending"),
        sweep_status=sweep_status,
        reason_codes=_report_reason_codes(rows, sweep_status),
        rows=rows,
    )


def research_market_event_freshness_sweep_report_payload(
    report: ResearchMarketEventFreshnessSweepReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketEventFreshnessSweepReport:
        raise ValueError("report must be a ResearchMarketEventFreshnessSweepReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("freshness sweep report", report)
    _validate_report_consistency(report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("freshness sweep report must be an object")
    return payload


def _row_from_input(
    item: ResearchMarketEventFreshnessSweepInput,
    *,
    config: ResearchMarketEventFreshnessSweepConfig,
    generated_at: datetime,
) -> ResearchMarketEventFreshnessSweepRow:
    _validate_not_after_generated_at(
        "last_information_refresh_at",
        item.last_information_refresh_at,
        generated_at,
    )
    _validate_not_after_generated_at(
        "latest_evidence_observed_at",
        item.latest_evidence_observed_at,
        generated_at,
    )
    _validate_not_after_generated_at(
        "review_completed_at",
        item.review_completed_at,
        generated_at,
    )
    _validate_settlement_horizon(item.settlement_at, generated_at, config)
    information_age_seconds = _age_seconds_or_none(
        item.last_information_refresh_at,
        generated_at,
    )
    evidence_age_seconds = _age_seconds_or_none(
        item.latest_evidence_observed_at,
        generated_at,
    )
    settlement_seconds_remaining = _settlement_seconds_remaining(
        item.settlement_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        item,
        information_age_seconds=information_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        settlement_seconds_remaining=settlement_seconds_remaining,
        config=config,
        generated_at=generated_at,
    )
    return ResearchMarketEventFreshnessSweepRow(
        queue_item_id=item.queue_item_id,
        last_information_refresh_at=item.last_information_refresh_at,
        latest_evidence_observed_at=item.latest_evidence_observed_at,
        settlement_at=item.settlement_at,
        information_refresh_age_seconds=information_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        settlement_seconds_remaining=settlement_seconds_remaining,
        domain_owner_present=item.domain_owner_present,
        manual_review_requested=item.manual_review_requested,
        review_completed_at=item.review_completed_at,
        review_required=reason_codes != (_CLEAR_REASON_CODE,),
        sweep_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketEventFreshnessSweepInput,
    *,
    information_age_seconds: Decimal | None,
    evidence_age_seconds: Decimal | None,
    settlement_seconds_remaining: Decimal | None,
    config: ResearchMarketEventFreshnessSweepConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    codes: list[str] = []
    if information_age_seconds is None:
        codes.append("missing_information_refresh")
    elif information_age_seconds >= config.information_refresh_block_after_seconds:
        codes.append("information_refresh_block_stale")
    elif information_age_seconds >= config.information_refresh_watch_after_seconds:
        codes.append("information_refresh_watch_stale")

    if evidence_age_seconds is None:
        codes.append("missing_evidence_observation")
    elif evidence_age_seconds >= config.evidence_block_after_seconds:
        codes.append("evidence_block_stale")
    elif evidence_age_seconds >= config.evidence_watch_after_seconds:
        codes.append("evidence_watch_stale")

    if item.settlement_at is None:
        codes.append("missing_settlement_at")
    elif settlement_seconds_remaining == _ZERO and item.settlement_at <= generated_at:
        codes.append("settlement_due_or_past")
    elif (
        settlement_seconds_remaining is not None
        and settlement_seconds_remaining <= config.settlement_block_within_seconds
    ):
        codes.append("settlement_block_window")
    elif (
        settlement_seconds_remaining is not None
        and settlement_seconds_remaining <= config.settlement_watch_within_seconds
    ):
        codes.append("settlement_watch_window")

    if not item.domain_owner_present:
        codes.append("domain_owner_missing")
    if item.manual_review_requested and item.review_completed_at is None:
        codes.append("manual_review_pending")

    if not codes:
        return (_CLEAR_REASON_CODE,)
    codes.append("review_required")
    return _normalize_reason_codes(tuple(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == (_CLEAR_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchMarketEventFreshnessSweepRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.sweep_status == "block" for row in rows):
        return "block"
    if any(row.sweep_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketEventFreshnessSweepRow, ...],
    sweep_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("no_queue_events_to_sweep",)
    codes = [_REPORT_STATUS_REASON_CODES[sweep_status]]
    row_reason_codes = frozenset(code for row in rows for code in row.reason_codes)
    for row_codes, report_code in _ROW_REASON_TO_REPORT_REASON:
        if row_reason_codes & row_codes:
            codes.append(report_code)
    return tuple(codes)


def _normalize_inputs(
    value: tuple[ResearchMarketEventFreshnessSweepInput, ...]
    | list[ResearchMarketEventFreshnessSweepInput],
) -> tuple[ResearchMarketEventFreshnessSweepInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(value)
    seen_ids: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketEventFreshnessSweepInput:
            raise ValueError(
                "inputs must contain ResearchMarketEventFreshnessSweepInput values",
            )
        _require_hard_flags(item)
        if item.queue_item_id in seen_ids:
            raise ValueError("duplicate queue_item_id")
        seen_ids.add(item.queue_item_id)
    return normalized


def _normalize_rows(value: object) -> tuple[ResearchMarketEventFreshnessSweepRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain ResearchMarketEventFreshnessSweepRow values")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchMarketEventFreshnessSweepRow values",
        ) from exc
    for row in rows:
        if type(row) is not ResearchMarketEventFreshnessSweepRow:
            raise ValueError(
                "rows must contain ResearchMarketEventFreshnessSweepRow values",
            )
        _require_hard_flags(row)
    if rows != tuple(
        sorted(rows, key=lambda row: (_STATUS_WEIGHTS[row.sweep_status], row.queue_item_id)),
    ):
        raise ValueError("rows must use deterministic freshness sort")
    return rows


def _validate_row_consistency(row: ResearchMarketEventFreshnessSweepRow) -> None:
    if row.sweep_status != _row_status(row.reason_codes):
        raise ValueError("sweep_status must match reason_codes")
    if row.review_required != (row.reason_codes != (_CLEAR_REASON_CODE,)):
        raise ValueError("review_required must match reason_codes")
    if row.sweep_status == "pass" and row.reason_codes != (_CLEAR_REASON_CODE,):
        raise ValueError("pass rows must use the freshness_sweep_pass reason")
    if row.sweep_status != "pass" and _CLEAR_REASON_CODE in row.reason_codes:
        raise ValueError("non-pass rows must not use the freshness_sweep_pass reason")
    if row.settlement_at is None and row.settlement_seconds_remaining is not None:
        raise ValueError("settlement_seconds_remaining must be None without settlement_at")
    if row.settlement_at is not None and row.settlement_seconds_remaining is None:
        raise ValueError("settlement_seconds_remaining must be present with settlement_at")
    if (
        row.manual_review_requested
        and row.review_completed_at is None
        and "manual_review_pending" not in row.reason_codes
    ):
        raise ValueError("manual_review_pending reason must match review fields")


def _validate_report_consistency(report: ResearchMarketEventFreshnessSweepReport) -> None:
    if report.queue_item_count != _count_decimal(report.rows):
        raise ValueError("queue_item_count must match rows")
    if report.block_count != _count_decimal(
        row for row in report.rows if row.sweep_status == "block"
    ):
        raise ValueError("block_count must match rows")
    if report.watch_count != _count_decimal(
        row for row in report.rows if row.sweep_status == "watch"
    ):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count_decimal(
        row for row in report.rows if row.sweep_status == "pass"
    ):
        raise ValueError("pass_count must match rows")
    if report.information_refresh_needed_count != _reason_family_count(
        report.rows,
        _INFORMATION_REFRESH_REASON_CODES,
    ):
        raise ValueError("information_refresh_needed_count must match rows")
    if report.stale_evidence_count != _reason_family_count(
        report.rows,
        _STALE_EVIDENCE_REASON_CODES,
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.settlement_window_count != _reason_family_count(
        report.rows,
        _SETTLEMENT_WINDOW_REASON_CODES,
    ):
        raise ValueError("settlement_window_count must match rows")
    if report.missing_domain_owner_count != _reason_count(
        report.rows,
        "domain_owner_missing",
    ):
        raise ValueError("missing_domain_owner_count must match rows")
    if report.review_required_count != _count_decimal(
        row for row in report.rows if row.review_required
    ):
        raise ValueError("review_required_count must match rows")
    if report.pending_review_count != _reason_count(report.rows, "manual_review_pending"):
        raise ValueError("pending_review_count must match rows")
    if report.sweep_status != _report_status(report.rows):
        raise ValueError("sweep_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.sweep_status):
        raise ValueError("reason_codes must match rows")


def _validate_not_after_generated_at(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _validate_settlement_horizon(
    settlement_at: datetime | None,
    generated_at: datetime,
    config: ResearchMarketEventFreshnessSweepConfig,
) -> None:
    if settlement_at is None or settlement_at <= generated_at:
        return
    if _elapsed_seconds(generated_at, settlement_at) > config.max_settlement_horizon_seconds:
        raise ValueError("settlement_at must not be after max horizon")


def _age_seconds_or_none(observed_at: datetime | None, generated_at: datetime) -> Decimal | None:
    if observed_at is None:
        return None
    return _elapsed_seconds(observed_at, generated_at)


def _settlement_seconds_remaining(
    settlement_at: datetime | None,
    generated_at: datetime,
) -> Decimal | None:
    if settlement_at is None:
        return None
    if settlement_at <= generated_at:
        return _ZERO
    return _elapsed_seconds(generated_at, settlement_at)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("timestamps must not move backward")
    delta = end - start
    whole_seconds = delta.days * 86400 + delta.seconds
    with localcontext(_DECIMAL_CONTEXT):
        return (
            Decimal(whole_seconds) + (Decimal(delta.microseconds) / Decimal(1000000))
        ).quantize(_QUANTUM)


def _reason_count(
    rows: tuple[ResearchMarketEventFreshnessSweepRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(row for row in rows if reason_code in row.reason_codes)


def _reason_family_count(
    rows: tuple[ResearchMarketEventFreshnessSweepRow, ...],
    reason_codes: frozenset[str],
) -> Decimal:
    return _count_decimal(
        row for row in rows if any(code in reason_codes for code in row.reason_codes)
    )


def _count_decimal(values: object) -> Decimal:
    if isinstance(values, (str, bytes)):
        raise ValueError("values must be iterable")
    try:
        count = sum(1 for _ in values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("values must be iterable") from exc
    return Decimal(count).quantize(_QUANTUM)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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
        raise ValueError("reason_codes must contain public reason strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain public reason strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
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
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES!r}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} contains unsafe public surface")
    if any(fragment in lowered for fragment in _SENSITIVE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in _SHA256_HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _derived_validation_digest(report: ResearchMarketEventFreshnessSweepReport) -> str:
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
    raise ValueError("derived_validation_digest contains unsupported value")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat().replace("+00:00", "Z")
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchMarketEventFreshnessSweepConfig,
            ResearchMarketEventFreshnessSweepInput,
            ResearchMarketEventFreshnessSweepRow,
            ResearchMarketEventFreshnessSweepReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public_key(f"{current_path}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            key_text = str(key)
            _reject_unsafe_public_key(f"{current_path}.{key_text}", key_text)
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}.{key_text}",
            )
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value)
        return
    if value is None or type(value) in (Decimal, datetime, bool):
        return
    raise ValueError(f"{current_path} contains unsupported public payload value")


def _reject_unsafe_public_key(path: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} contains unsafe public surface")
