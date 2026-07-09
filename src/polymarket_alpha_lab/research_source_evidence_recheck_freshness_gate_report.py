"""Deterministic report-only freshness gate for caller-supplied evidence checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_RECHECK_FRESHNESS_GATE_CONFIG_VERSION",
    "ResearchSourceEvidenceRecheckFreshnessGateConfig",
    "ResearchSourceEvidenceRecheckFreshnessGateInput",
    "ResearchSourceEvidenceRecheckFreshnessGateReport",
    "ResearchSourceEvidenceRecheckFreshnessGateRow",
    "build_research_source_evidence_recheck_freshness_gate_report",
    "research_source_evidence_recheck_freshness_gate_report_payload",
)


DEFAULT_RESEARCH_SOURCE_EVIDENCE_RECHECK_FRESHNESS_GATE_CONFIG_VERSION = (
    "research-source-evidence-recheck-freshness-gate-v0"
)
GATE_STATUSES = ("pass", "watch", "block")
GATE_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PAYLOAD_SHA256_FIELD = "payload_sha256"
PASS_REASON_CODE = "evidence_recheck_freshness_pass"
WATCH_REASON_CODE = "evidence_recheck_freshness_watch"
BLOCK_REASON_CODE = "evidence_recheck_freshness_block"
NO_EVIDENCE_REASON_CODE = "no_source_evidence_rechecks"
PUBLIC_PAYLOAD_FORBIDDEN_FRAGMENTS = (
    "candidate",
    "market_id",
    "condition_id",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceEvidenceRecheckFreshnessGateConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_EVIDENCE_RECHECK_FRESHNESS_GATE_CONFIG_VERSION
    fresh_evidence_age_seconds: Decimal = Decimal("3600.000000")
    watch_evidence_age_seconds: Decimal = Decimal("7200.000000")
    block_evidence_age_seconds: Decimal = Decimal("172800.000000")
    source_confirmation_stale_after_seconds: Decimal = Decimal("5400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_evidence_age_seconds",
            "watch_evidence_age_seconds",
            "block_evidence_age_seconds",
            "source_confirmation_stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_evidence_age_seconds <= self.fresh_evidence_age_seconds:
            raise ValueError(
                "watch_evidence_age_seconds must exceed fresh_evidence_age_seconds",
            )
        if self.block_evidence_age_seconds <= self.watch_evidence_age_seconds:
            raise ValueError(
                "block_evidence_age_seconds must exceed watch_evidence_age_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRecheckFreshnessGateInput:
    evidence_ref: str
    observed_at: datetime
    last_rechecked_at: datetime | None
    next_recheck_due_at: datetime
    source_confirmed_at: datetime | None
    contradiction_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("evidence_ref", self.evidence_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "source_confirmed_at",
            _as_optional_utc("source_confirmed_at", self.source_confirmed_at),
        )
        _require_bool("contradiction_flag", self.contradiction_flag)
        if (
            self.last_rechecked_at is not None
            and self.last_rechecked_at < self.observed_at
        ):
            raise ValueError("last_rechecked_at must not precede observed_at")
        if self.next_recheck_due_at < self.observed_at:
            raise ValueError("next_recheck_due_at must not precede observed_at")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRecheckFreshnessGateRow:
    row_index: Decimal
    observed_at: datetime
    last_rechecked_at: datetime | None
    next_recheck_due_at: datetime
    source_confirmed_at: datetime | None
    evidence_age_seconds: Decimal
    recheck_age_seconds: Decimal | None
    recheck_overdue_seconds: Decimal
    source_confirmation_age_seconds: Decimal | None
    contradiction_flag: bool
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "row_index",
            _normalize_nonnegative_decimal("row_index", self.row_index),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_optional_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "next_recheck_due_at",
            _as_utc("next_recheck_due_at", self.next_recheck_due_at),
        )
        object.__setattr__(
            self,
            "source_confirmed_at",
            _as_optional_utc("source_confirmed_at", self.source_confirmed_at),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recheck_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "recheck_age_seconds",
                self.recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "recheck_overdue_seconds",
            _normalize_nonnegative_decimal(
                "recheck_overdue_seconds",
                self.recheck_overdue_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_confirmation_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_confirmation_age_seconds",
                self.source_confirmation_age_seconds,
            ),
        )
        _require_bool("contradiction_flag", self.contradiction_flag)
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceRecheckFreshnessGateReport:
    generated_at: datetime
    config_version: str
    fresh_evidence_age_seconds: Decimal
    watch_evidence_age_seconds: Decimal
    block_evidence_age_seconds: Decimal
    source_confirmation_stale_after_seconds: Decimal
    total_evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overdue_recheck_count: Decimal
    missing_recheck_count: Decimal
    stale_source_confirmation_count: Decimal
    contradiction_count: Decimal
    pass_ratio: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_evidence_age_seconds",
            "watch_evidence_age_seconds",
            "block_evidence_age_seconds",
            "source_confirmation_stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overdue_recheck_count",
            "missing_recheck_count",
            "stale_source_confirmation_count",
            "contradiction_count",
            "pass_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_ratio > ONE:
            raise ValueError("pass_ratio must be between 0 and 1")
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _require_or_set_payload_sha256(self)


def build_research_source_evidence_recheck_freshness_gate_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchSourceEvidenceRecheckFreshnessGateConfig,
    generated_at: datetime,
) -> ResearchSourceEvidenceRecheckFreshnessGateReport:
    if type(config) is not ResearchSourceEvidenceRecheckFreshnessGateConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceRecheckFreshnessGateConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_inputs(evidence_rows)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    row_index=index,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for index, item in enumerate(evidence_items, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceEvidenceRecheckFreshnessGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        fresh_evidence_age_seconds=config.fresh_evidence_age_seconds,
        watch_evidence_age_seconds=config.watch_evidence_age_seconds,
        block_evidence_age_seconds=config.block_evidence_age_seconds,
        source_confirmation_stale_after_seconds=(
            config.source_confirmation_stale_after_seconds
        ),
        total_evidence_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        overdue_recheck_count=_decimal_count(
            sum(1 for row in rows if "recheck_overdue" in row.reason_codes),
        ),
        missing_recheck_count=_decimal_count(
            sum(1 for row in rows if "missing_prior_recheck" in row.reason_codes),
        ),
        stale_source_confirmation_count=_decimal_count(
            sum(
                1
                for row in rows
                if "source_confirmation_stale" in row.reason_codes
                or "source_confirmation_missing" in row.reason_codes
            ),
        ),
        contradiction_count=_decimal_count(
            sum(1 for row in rows if row.contradiction_flag),
        ),
        pass_ratio=_ratio(_status_count(rows, "pass"), len(rows)),
        gate_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_evidence_recheck_freshness_gate_report_payload(
    report: ResearchSourceEvidenceRecheckFreshnessGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceEvidenceRecheckFreshnessGateReport:
        raise ValueError(
            "report must be a ResearchSourceEvidenceRecheckFreshnessGateReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_payload_sha256=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _row_from_input(
    item: ResearchSourceEvidenceRecheckFreshnessGateInput,
    *,
    row_index: int,
    config: ResearchSourceEvidenceRecheckFreshnessGateConfig,
    generated_at: datetime,
) -> ResearchSourceEvidenceRecheckFreshnessGateRow:
    _reject_future("observed_at", item.observed_at, generated_at)
    if item.last_rechecked_at is not None:
        _reject_future("last_rechecked_at", item.last_rechecked_at, generated_at)
    if item.source_confirmed_at is not None:
        _reject_future("source_confirmed_at", item.source_confirmed_at, generated_at)
    evidence_age_seconds = _elapsed_seconds(item.observed_at, generated_at)
    recheck_age_seconds = (
        None
        if item.last_rechecked_at is None
        else _elapsed_seconds(item.last_rechecked_at, generated_at)
    )
    recheck_overdue_seconds = (
        _elapsed_seconds(item.next_recheck_due_at, generated_at)
        if item.next_recheck_due_at < generated_at
        else ZERO
    )
    source_confirmation_age_seconds = (
        None
        if item.source_confirmed_at is None
        else _elapsed_seconds(item.source_confirmed_at, generated_at)
    )
    reason_codes = _row_reason_codes(
        item=item,
        evidence_age_seconds=evidence_age_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
        source_confirmation_age_seconds=source_confirmation_age_seconds,
        config=config,
    )
    return ResearchSourceEvidenceRecheckFreshnessGateRow(
        row_index=_decimal_count(row_index),
        observed_at=item.observed_at,
        last_rechecked_at=item.last_rechecked_at,
        next_recheck_due_at=item.next_recheck_due_at,
        source_confirmed_at=item.source_confirmed_at,
        evidence_age_seconds=evidence_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
        source_confirmation_age_seconds=source_confirmation_age_seconds,
        contradiction_flag=item.contradiction_flag,
        gate_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchSourceEvidenceRecheckFreshnessGateInput,
    evidence_age_seconds: Decimal,
    recheck_overdue_seconds: Decimal,
    source_confirmation_age_seconds: Decimal | None,
    config: ResearchSourceEvidenceRecheckFreshnessGateConfig,
) -> tuple[str, ...]:
    status = _freshness_status(
        item=item,
        evidence_age_seconds=evidence_age_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
        source_confirmation_age_seconds=source_confirmation_age_seconds,
        config=config,
    )
    if status == "pass":
        return (PASS_REASON_CODE,)

    reason_codes: set[str] = {
        BLOCK_REASON_CODE if status == "block" else WATCH_REASON_CODE,
    }
    if evidence_age_seconds >= config.watch_evidence_age_seconds:
        reason_codes.add("evidence_stale")
    if item.last_rechecked_at is None:
        reason_codes.add("missing_prior_recheck")
    if recheck_overdue_seconds > ZERO:
        reason_codes.add("recheck_overdue")
    if item.source_confirmed_at is None:
        reason_codes.add("source_confirmation_missing")
    elif (
        source_confirmation_age_seconds is not None
        and source_confirmation_age_seconds
        > config.source_confirmation_stale_after_seconds
    ):
        reason_codes.add("source_confirmation_stale")
    if item.contradiction_flag:
        reason_codes.add("contradiction_requires_recheck")
    return tuple(sorted(reason_codes))


def _freshness_status(
    *,
    item: ResearchSourceEvidenceRecheckFreshnessGateInput,
    evidence_age_seconds: Decimal,
    recheck_overdue_seconds: Decimal,
    source_confirmation_age_seconds: Decimal | None,
    config: ResearchSourceEvidenceRecheckFreshnessGateConfig,
) -> str:
    if item.contradiction_flag:
        return "block"
    if item.last_rechecked_at is None or item.source_confirmed_at is None:
        return "block"
    if evidence_age_seconds >= config.block_evidence_age_seconds:
        return "block"
    if evidence_age_seconds > config.fresh_evidence_age_seconds:
        return "watch"
    if recheck_overdue_seconds > ZERO:
        return "watch"
    if (
        source_confirmation_age_seconds is not None
        and source_confirmation_age_seconds
        > config.source_confirmation_stale_after_seconds
    ):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON_CODE in reason_codes:
        return "block"
    if WATCH_REASON_CODE in reason_codes:
        return "watch"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    raise ValueError("reason_codes do not determine gate_status")


def _report_status(
    rows: tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON_CODE,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    }
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(sorted(reason_codes))


def _normalize_inputs(
    evidence_rows: Iterable[object],
) -> tuple[ResearchSourceEvidenceRecheckFreshnessGateInput, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchSourceEvidenceRecheckFreshnessGateInput:
    if type(value) is ResearchSourceEvidenceRecheckFreshnessGateInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchSourceEvidenceRecheckFreshnessGateInput(
        evidence_ref=_field_value(value, "evidence_ref"),
        observed_at=_field_value(value, "observed_at"),
        last_rechecked_at=_field_value(value, "last_rechecked_at"),
        next_recheck_due_at=_field_value(value, "next_recheck_due_at"),
        source_confirmed_at=_field_value(value, "source_confirmed_at"),
        contradiction_flag=_field_value(value, "contradiction_flag", default=False),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _normalize_rows(
    rows: tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...],
) -> tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceEvidenceRecheckFreshnessGateRow:
            raise ValueError(
                "rows must contain ResearchSourceEvidenceRecheckFreshnessGateRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must use deterministic gate sort")
    return rows


def _row_sort_key(
    row: ResearchSourceEvidenceRecheckFreshnessGateRow,
) -> tuple[int, Decimal]:
    return (GATE_STATUS_WEIGHT[row.gate_status], row.row_index)


def _validate_row_consistency(
    row: ResearchSourceEvidenceRecheckFreshnessGateRow,
) -> None:
    if row.row_index <= ZERO:
        raise ValueError("row_index must be positive")
    if row.last_rechecked_at is None and row.recheck_age_seconds is not None:
        raise ValueError("recheck_age_seconds must be absent without last_rechecked_at")
    if row.last_rechecked_at is not None and row.recheck_age_seconds is None:
        raise ValueError("recheck_age_seconds is required with last_rechecked_at")
    if (
        row.source_confirmed_at is None
        and row.source_confirmation_age_seconds is not None
    ):
        raise ValueError(
            "source_confirmation_age_seconds must be absent without source_confirmed_at",
        )
    if (
        row.source_confirmed_at is not None
        and row.source_confirmation_age_seconds is None
    ):
        raise ValueError(
            "source_confirmation_age_seconds is required with source_confirmed_at",
        )
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchSourceEvidenceRecheckFreshnessGateReport,
) -> None:
    rows = report.rows
    if report.total_evidence_count != _decimal_count(len(rows)):
        raise ValueError("total_evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.overdue_recheck_count != _decimal_count(
        sum(1 for row in rows if "recheck_overdue" in row.reason_codes),
    ):
        raise ValueError("overdue_recheck_count must match rows")
    if report.missing_recheck_count != _decimal_count(
        sum(1 for row in rows if "missing_prior_recheck" in row.reason_codes),
    ):
        raise ValueError("missing_recheck_count must match rows")
    if report.stale_source_confirmation_count != _decimal_count(
        sum(
            1
            for row in rows
            if "source_confirmation_stale" in row.reason_codes
            or "source_confirmation_missing" in row.reason_codes
        ),
    ):
        raise ValueError("stale_source_confirmation_count must match rows")
    if report.contradiction_count != _decimal_count(
        sum(1 for row in rows if row.contradiction_flag),
    ):
        raise ValueError("contradiction_count must match rows")
    if report.pass_ratio != _ratio(_status_count(rows, "pass"), len(rows)):
        raise ValueError("pass_ratio must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchSourceEvidenceRecheckFreshnessGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    return (Decimal(numerator) / Decimal(denominator)).quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end must not precede start")
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    return (Decimal(microseconds) / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _reject_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_or_set_payload_sha256(
    report: ResearchSourceEvidenceRecheckFreshnessGateReport,
) -> None:
    expected = _payload_sha256(_report_payload_without_sha256(report))
    if report.payload_sha256 == "":
        object.__setattr__(report, PAYLOAD_SHA256_FIELD, expected)
        return
    if type(report.payload_sha256) is not str or report.payload_sha256 != expected:
        raise ValueError("payload_sha256 does not match report payload")


def _report_payload_without_sha256(
    report: ResearchSourceEvidenceRecheckFreshnessGateReport,
) -> dict[str, Any]:
    payload = _payload_value(report, include_payload_sha256=False)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, include_payload_sha256: bool) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [
            _payload_value(item, include_payload_sha256=include_payload_sha256)
            for item in value
        ]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(
                getattr(value, field.name),
                include_payload_sha256=include_payload_sha256,
            )
            for field in fields(value)
            if include_payload_sha256 or field.name != PAYLOAD_SHA256_FIELD
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{context} key", str(key))
            _reject_unsafe_public_payload(context, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(context, value)


def _reject_unsafe_public_text(context: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in PUBLIC_PAYLOAD_FORBIDDEN_FRAGMENTS):
        raise ValueError(f"{context} contains unsafe public value")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        normalized.append(reason_code)
    return tuple(sorted(set(normalized)))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANTUM)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be one of {GATE_STATUSES!r}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is str:
        _reject_unsafe_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
