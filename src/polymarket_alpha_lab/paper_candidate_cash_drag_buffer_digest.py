"""Pure paper candidate cash drag buffer diagnostics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "PaperCandidateCashDragBufferDigestCandidate",
    "PaperCandidateCashDragBufferDigestConfig",
    "PaperCandidateCashDragBufferDigestReport",
    "PaperCandidateCashDragBufferDigestRow",
    "build_paper_candidate_cash_drag_buffer_digest",
    "paper_candidate_cash_drag_buffer_digest_payload",
)


_CONFIG_VERSION = "paper-candidate-cash-drag-buffer-digest-v0"
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIDES = ("yes", "no")
_STATUSES = ("pass", "watch", "blocked")
_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

_EMPTY_REASON = "cash_drag_buffer_digest_empty"
_PASSED_REASON = "cash_drag_buffer_passed"
_WATCH_REASON = "cash_drag_ratio_watch"
_BLOCKED_REASON = "cash_drag_ratio_blocked"
_PENDING_REASON = "pending_cash_drag_present"
_SHORTFALL_REASON = "cash_buffer_shortfall_present"
_MINIMUM_REASON = "minimum_buffer_coverage_watch"
_REPORT_REASON_SEQUENCE = (
    _BLOCKED_REASON,
    _WATCH_REASON,
    _PASSED_REASON,
    _PENDING_REASON,
    _SHORTFALL_REASON,
    _MINIMUM_REASON,
    _EMPTY_REASON,
)


@dataclass(frozen=True)
class PaperCandidateCashDragBufferDigestConfig:
    config_version: str = _CONFIG_VERSION
    watch_cash_drag_ratio: Decimal = Decimal("0.100000")
    blocked_cash_drag_ratio: Decimal = Decimal("0.200000")
    minimum_buffer_ratio: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "watch_cash_drag_ratio",
            "blocked_cash_drag_ratio",
            "minimum_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_cash_drag_ratio > self.blocked_cash_drag_ratio:
            raise ValueError("watch_cash_drag_ratio must not exceed blocked_cash_drag_ratio")
        _require_flags("config", self)


@dataclass(frozen=True)
class PaperCandidateCashDragBufferDigestCandidate:
    candidate_reference: str
    market_reference: str
    side: str
    evaluated_at: datetime
    proposed_notional: Decimal
    available_cash: Decimal
    pending_cash_drag: Decimal
    cash_buffer: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        _require_member("side", self.side, _SIDES)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in ("proposed_notional", "available_cash"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pending_cash_drag", "cash_buffer"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes),
        )
        _require_flags("candidate", self)


@dataclass(frozen=True)
class PaperCandidateCashDragBufferDigestRow:
    redacted_candidate_reference: str
    redacted_market_reference: str
    side: str
    evaluated_at: datetime
    proposed_notional: Decimal
    available_cash: Decimal
    pending_cash_drag: Decimal
    cash_buffer: Decimal
    required_cash_buffer: Decimal
    buffer_shortfall: Decimal
    cash_drag_ratio: Decimal
    buffer_coverage_ratio: Decimal
    cash_drag_buffer_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("redacted_candidate_reference", self.redacted_candidate_reference)
        _require_text("redacted_market_reference", self.redacted_market_reference)
        _require_member("side", self.side, _SIDES)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in ("proposed_notional", "available_cash"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pending_cash_drag",
            "cash_buffer",
            "required_cash_buffer",
            "buffer_shortfall",
            "cash_drag_ratio",
            "buffer_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("cash_drag_buffer_status", self.cash_drag_buffer_status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reasons(self.reason_codes))
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class PaperCandidateCashDragBufferDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_proposed_notional: Decimal
    total_pending_cash_drag: Decimal
    total_cash_buffer: Decimal
    max_cash_drag_ratio: Decimal
    min_buffer_coverage_ratio: Decimal
    max_buffer_shortfall: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperCandidateCashDragBufferDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_proposed_notional",
            "total_pending_cash_drag",
            "total_cash_buffer",
            "max_cash_drag_ratio",
            "min_buffer_coverage_ratio",
            "max_buffer_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reasons(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_flags("report", self)


def build_paper_candidate_cash_drag_buffer_digest(
    candidates: Iterable[PaperCandidateCashDragBufferDigestCandidate],
    *,
    config: PaperCandidateCashDragBufferDigestConfig,
    generated_at: datetime,
) -> PaperCandidateCashDragBufferDigestReport:
    if type(config) is not PaperCandidateCashDragBufferDigestConfig:
        raise ValueError("config must be PaperCandidateCashDragBufferDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    candidate_tuple = tuple(candidates)
    seen: set[str] = set()
    rows: list[PaperCandidateCashDragBufferDigestRow] = []
    for candidate in candidate_tuple:
        if type(candidate) is not PaperCandidateCashDragBufferDigestCandidate:
            raise ValueError("candidates must contain PaperCandidateCashDragBufferDigestCandidate")
        if candidate.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(candidate.candidate_reference)
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
        rows.append(_build_row(candidate, config))

    rows = tuple(sorted(rows, key=_row_sort_key))
    if not rows:
        return PaperCandidateCashDragBufferDigestReport(
            generated_at=generated_at,
            config_version=config.config_version,
            candidate_count=_count_decimal(0),
            pass_count=_count_decimal(0),
            watch_count=_count_decimal(0),
            blocked_count=_count_decimal(0),
            total_proposed_notional=_ZERO,
            total_pending_cash_drag=_ZERO,
            total_cash_buffer=_ZERO,
            max_cash_drag_ratio=_ZERO,
            min_buffer_coverage_ratio=_ZERO,
            max_buffer_shortfall=_ZERO,
            status="watch",
            reason_codes=(_EMPTY_REASON,),
            rows=(),
        )

    return PaperCandidateCashDragBufferDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_count_decimal(
            sum(1 for row in rows if row.cash_drag_buffer_status == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in rows if row.cash_drag_buffer_status == "watch"),
        ),
        blocked_count=_count_decimal(
            sum(1 for row in rows if row.cash_drag_buffer_status == "blocked"),
        ),
        total_proposed_notional=_q(sum((row.proposed_notional for row in rows), _ZERO)),
        total_pending_cash_drag=_q(sum((row.pending_cash_drag for row in rows), _ZERO)),
        total_cash_buffer=_q(sum((row.cash_buffer for row in rows), _ZERO)),
        max_cash_drag_ratio=max(row.cash_drag_ratio for row in rows),
        min_buffer_coverage_ratio=min(row.buffer_coverage_ratio for row in rows),
        max_buffer_shortfall=max(row.buffer_shortfall for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reasons(rows),
        rows=rows,
    )


def paper_candidate_cash_drag_buffer_digest_payload(
    report: PaperCandidateCashDragBufferDigestReport,
) -> dict[str, Any]:
    if type(report) is not PaperCandidateCashDragBufferDigestReport:
        raise ValueError("report must be PaperCandidateCashDragBufferDigestReport")
    _require_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_text(report.candidate_count),
        "pass_count": _decimal_text(report.pass_count),
        "watch_count": _decimal_text(report.watch_count),
        "blocked_count": _decimal_text(report.blocked_count),
        "total_proposed_notional": _decimal_text(report.total_proposed_notional),
        "total_pending_cash_drag": _decimal_text(report.total_pending_cash_drag),
        "total_cash_buffer": _decimal_text(report.total_cash_buffer),
        "max_cash_drag_ratio": _decimal_text(report.max_cash_drag_ratio),
        "min_buffer_coverage_ratio": _decimal_text(report.min_buffer_coverage_ratio),
        "max_buffer_shortfall": _decimal_text(report.max_buffer_shortfall),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [
            {
                "redacted_candidate_reference": row.redacted_candidate_reference,
                "redacted_market_reference": row.redacted_market_reference,
                "side": row.side,
                "evaluated_at": row.evaluated_at.isoformat(),
                "proposed_notional": _decimal_text(row.proposed_notional),
                "available_cash": _decimal_text(row.available_cash),
                "pending_cash_drag": _decimal_text(row.pending_cash_drag),
                "cash_buffer": _decimal_text(row.cash_buffer),
                "required_cash_buffer": _decimal_text(row.required_cash_buffer),
                "buffer_shortfall": _decimal_text(row.buffer_shortfall),
                "cash_drag_ratio": _decimal_text(row.cash_drag_ratio),
                "buffer_coverage_ratio": _decimal_text(row.buffer_coverage_ratio),
                "cash_drag_buffer_status": row.cash_drag_buffer_status,
                "reason_codes": list(row.reason_codes),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for row in report.rows
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _build_row(
    candidate: PaperCandidateCashDragBufferDigestCandidate,
    config: PaperCandidateCashDragBufferDigestConfig,
) -> PaperCandidateCashDragBufferDigestRow:
    required_cash_buffer = candidate.pending_cash_drag
    buffer_shortfall = max(required_cash_buffer - candidate.cash_buffer, _ZERO)
    cash_drag_ratio = _safe_ratio(candidate.pending_cash_drag, candidate.available_cash)
    buffer_coverage_ratio = _safe_ratio(candidate.cash_buffer, required_cash_buffer)
    cash_buffer_ratio = _safe_ratio(candidate.cash_buffer, candidate.available_cash)
    if cash_drag_ratio >= config.blocked_cash_drag_ratio:
        status = "blocked"
        status_reason = _BLOCKED_REASON
    elif cash_drag_ratio >= config.watch_cash_drag_ratio or buffer_shortfall > _ZERO:
        status = "watch"
        status_reason = _WATCH_REASON
    else:
        status = "pass"
        status_reason = _PASSED_REASON

    reasons = [
        reason
        for reason in candidate.reason_codes
        if reason not in _REPORT_REASON_SEQUENCE
    ]
    reasons.append(status_reason)
    if candidate.pending_cash_drag > _ZERO:
        reasons.append(_PENDING_REASON)
    if buffer_shortfall > _ZERO:
        reasons.append(_SHORTFALL_REASON)
    if buffer_shortfall > _ZERO and cash_buffer_ratio < config.minimum_buffer_ratio:
        reasons.append(_MINIMUM_REASON)

    return PaperCandidateCashDragBufferDigestRow(
        redacted_candidate_reference=_redacted(candidate.candidate_reference, "candidate_ref_"),
        redacted_market_reference=_redacted(candidate.market_reference, "market_ref_"),
        side=candidate.side,
        evaluated_at=candidate.evaluated_at,
        proposed_notional=candidate.proposed_notional,
        available_cash=candidate.available_cash,
        pending_cash_drag=candidate.pending_cash_drag,
        cash_buffer=candidate.cash_buffer,
        required_cash_buffer=required_cash_buffer,
        buffer_shortfall=buffer_shortfall,
        cash_drag_ratio=cash_drag_ratio,
        buffer_coverage_ratio=buffer_coverage_ratio,
        cash_drag_buffer_status=status,
        reason_codes=tuple(reasons),
    )


def _report_status(rows: tuple[PaperCandidateCashDragBufferDigestRow, ...]) -> str:
    if any(row.cash_drag_buffer_status == "blocked" for row in rows):
        return "blocked"
    if any(row.cash_drag_buffer_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reasons(rows: tuple[PaperCandidateCashDragBufferDigestRow, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    return tuple(reason for reason in _REPORT_REASON_SEQUENCE if reason in seen)


def _row_sort_key(row: PaperCandidateCashDragBufferDigestRow) -> tuple[int, Decimal, str, str]:
    return (
        _STATUS_RANK[row.cash_drag_buffer_status],
        -row.buffer_shortfall,
        row.redacted_candidate_reference,
        row.side,
    )


def _validate_row(row: PaperCandidateCashDragBufferDigestRow) -> None:
    if row.required_cash_buffer != row.pending_cash_drag:
        raise ValueError("required_cash_buffer must equal pending_cash_drag")
    if row.buffer_shortfall != max(row.required_cash_buffer - row.cash_buffer, _ZERO):
        raise ValueError("buffer_shortfall does not match cash_buffer")
    if row.cash_drag_ratio != _safe_ratio(row.pending_cash_drag, row.available_cash):
        raise ValueError("cash_drag_ratio does not match cash values")
    if row.buffer_coverage_ratio != _safe_ratio(row.cash_buffer, row.required_cash_buffer):
        raise ValueError("buffer_coverage_ratio does not match cash values")


def _validate_report(report: PaperCandidateCashDragBufferDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count does not match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.cash_drag_buffer_status == "pass"),
    ):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.cash_drag_buffer_status == "watch"),
    ):
        raise ValueError("watch_count does not match rows")
    if report.blocked_count != _count_decimal(
        sum(1 for row in report.rows if row.cash_drag_buffer_status == "blocked"),
    ):
        raise ValueError("blocked_count does not match rows")
    if report.total_proposed_notional != _sum_decimal(
        row.proposed_notional for row in report.rows
    ):
        raise ValueError("total_proposed_notional does not match rows")
    if report.total_pending_cash_drag != _sum_decimal(
        row.pending_cash_drag for row in report.rows
    ):
        raise ValueError("total_pending_cash_drag does not match rows")
    if report.total_cash_buffer != _sum_decimal(row.cash_buffer for row in report.rows):
        raise ValueError("total_cash_buffer does not match rows")
    if report.max_cash_drag_ratio != _max_decimal(
        row.cash_drag_ratio for row in report.rows
    ):
        raise ValueError("max_cash_drag_ratio does not match rows")
    if report.min_buffer_coverage_ratio != _min_decimal(
        row.buffer_coverage_ratio for row in report.rows
    ):
        raise ValueError("min_buffer_coverage_ratio does not match rows")
    if report.max_buffer_shortfall != _max_decimal(
        row.buffer_shortfall for row in report.rows
    ):
        raise ValueError("max_buffer_shortfall does not match rows")
    expected_status = "watch" if not report.rows else _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status does not match rows")
    expected_reasons = (_EMPTY_REASON,) if not report.rows else _report_reasons(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match rows")


def _normalize_rows(
    rows: tuple[PaperCandidateCashDragBufferDigestRow, ...],
) -> tuple[PaperCandidateCashDragBufferDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not PaperCandidateCashDragBufferDigestRow:
            raise ValueError("rows must contain PaperCandidateCashDragBufferDigestRow")
        _require_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reasons(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    normalized: list[str] = []
    for reason in value:
        _require_text("reason_code", reason)
        if reason not in normalized:
            normalized.append(reason)
    return tuple(normalized)


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    _require_text(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _q(_require_decimal(field_name, value))
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _q(sum(values, _ZERO))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return min(items)


def _count_decimal(value: int) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_text(value: Decimal) -> str:
    return str(value)


def _redacted(value: str, prefix: str) -> str:
    return prefix + sha256(value.encode("utf-8")).hexdigest()[:16]
