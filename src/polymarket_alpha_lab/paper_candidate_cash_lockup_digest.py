"""Pure paper candidate cash lockup diagnostics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256


__all__ = (
    "DEFAULT_PAPER_CANDIDATE_CASH_LOCKUP_DIGEST_CONFIG_VERSION",
    "PaperCandidateCashLockupDigestCandidate",
    "PaperCandidateCashLockupDigestConfig",
    "PaperCandidateCashLockupDigestReport",
    "PaperCandidateCashLockupDigestRow",
    "build_paper_candidate_cash_lockup_digest",
    "paper_candidate_cash_lockup_digest_payload",
)


DEFAULT_PAPER_CANDIDATE_CASH_LOCKUP_DIGEST_CONFIG_VERSION = (
    "paper-candidate-cash-lockup-digest-v0"
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DAYS_PER_YEAR = Decimal("365.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_SIDES = ("yes", "no")
_ROW_STATUSES = ("pass", "watch", "blocked")
_REPORT_STATUSES = ("pass", "watch", "blocked")
_ROW_STATUS_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}

_EMPTY_REASON_CODE = "cash_lockup_digest_empty"
_PASS_REASON_CODE = "cash_lockup_passed"
_WATCH_RATIO_REASON_CODE = "cash_lockup_ratio_watch"
_BLOCKED_RATIO_REASON_CODE = "cash_lockup_ratio_blocked"
_PENDING_CASH_DRAG_REASON_CODE = "pending_cash_drag_present"
_OPPORTUNITY_COST_WATCH_REASON_CODE = "opportunity_cost_watch"
_REPORT_REASON_PRIORITY = (
    _BLOCKED_RATIO_REASON_CODE,
    _WATCH_RATIO_REASON_CODE,
    _PASS_REASON_CODE,
    _PENDING_CASH_DRAG_REASON_CODE,
    _OPPORTUNITY_COST_WATCH_REASON_CODE,
    _EMPTY_REASON_CODE,
)
_UNSAFE_FIELD_FRAGMENTS = (
    "private_key",
    "exchange_mutation",
    "cancel",
    "replace",
    "sign",
)


@dataclass(frozen=True)
class PaperCandidateCashLockupDigestConfig:
    config_version: str = DEFAULT_PAPER_CANDIDATE_CASH_LOCKUP_DIGEST_CONFIG_VERSION
    watch_lockup_ratio: Decimal = Decimal("0.250000")
    blocked_lockup_ratio: Decimal = Decimal("0.500000")
    watch_opportunity_cost: Decimal = Decimal("1.000000")
    annualized_opportunity_cost_proxy: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_lockup_ratio",
            "blocked_lockup_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_opportunity_cost",
            "annualized_opportunity_cost_proxy",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_lockup_ratio > self.blocked_lockup_ratio:
            raise ValueError("watch_lockup_ratio must not exceed blocked_lockup_ratio")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperCandidateCashLockupDigestCandidate:
    candidate_reference: str
    market_reference: str
    side: str
    evaluated_at: datetime
    proposed_notional: Decimal
    available_cash: Decimal
    pending_cash_drag: Decimal
    expected_days_to_close: Decimal
    settlement_lag_days: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("market_reference", self.market_reference)
        _require_member("side", self.side, _SIDES)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in ("proposed_notional", "available_cash"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pending_cash_drag",
            "expected_days_to_close",
            "settlement_lag_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class PaperCandidateCashLockupDigestRow:
    redacted_candidate_reference: str
    redacted_market_reference: str
    side: str
    evaluated_at: datetime
    proposed_notional: Decimal
    available_cash: Decimal
    pending_cash_drag: Decimal
    expected_days_to_close: Decimal
    settlement_lag_days: Decimal
    cash_lockup_days: Decimal
    lockup_ratio: Decimal
    annualized_opportunity_cost_proxy: Decimal
    opportunity_cost: Decimal
    cash_lockup_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_canonical_string(
            "redacted_market_reference",
            self.redacted_market_reference,
        )
        _require_member("side", self.side, _SIDES)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in ("proposed_notional", "available_cash"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pending_cash_drag",
            "expected_days_to_close",
            "settlement_lag_days",
            "cash_lockup_days",
            "annualized_opportunity_cost_proxy",
            "opportunity_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "lockup_ratio",
            _normalize_nonnegative_decimal("lockup_ratio", self.lockup_ratio),
        )
        _require_member("cash_lockup_status", self.cash_lockup_status, _ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class PaperCandidateCashLockupDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_proposed_notional: Decimal
    total_pending_cash_drag: Decimal
    total_opportunity_cost: Decimal
    max_lockup_ratio: Decimal
    max_cash_lockup_days: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperCandidateCashLockupDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_proposed_notional",
            "total_pending_cash_drag",
            "total_opportunity_cost",
            "max_lockup_ratio",
            "max_cash_lockup_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_paper_candidate_cash_lockup_digest(
    candidates: Iterable[object],
    *,
    config: PaperCandidateCashLockupDigestConfig,
    generated_at: datetime,
) -> PaperCandidateCashLockupDigestReport:
    if type(config) is not PaperCandidateCashLockupDigestConfig:
        raise ValueError("config must be a PaperCandidateCashLockupDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(candidate, config=config, generated_at=generated_at)
                for candidate in source_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return PaperCandidateCashLockupDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_proposed_notional=_sum_decimal(row.proposed_notional for row in rows),
        total_pending_cash_drag=_sum_decimal(row.pending_cash_drag for row in rows),
        total_opportunity_cost=_sum_decimal(row.opportunity_cost for row in rows),
        max_lockup_ratio=_max_lockup_ratio(rows),
        max_cash_lockup_days=_max_cash_lockup_days(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def paper_candidate_cash_lockup_digest_payload(
    report: PaperCandidateCashLockupDigestReport,
) -> dict[str, object]:
    if type(report) is not PaperCandidateCashLockupDigestReport:
        raise ValueError("report must be a PaperCandidateCashLockupDigestReport")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "blocked_count": _count_payload(report.blocked_count),
        "total_proposed_notional": _decimal_payload(report.total_proposed_notional),
        "total_pending_cash_drag": _decimal_payload(report.total_pending_cash_drag),
        "total_opportunity_cost": _decimal_payload(report.total_opportunity_cost),
        "max_lockup_ratio": _decimal_payload(report.max_lockup_ratio),
        "max_cash_lockup_days": _decimal_payload(report.max_cash_lockup_days),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: PaperCandidateCashLockupDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "redacted_market_reference": row.redacted_market_reference,
        "side": row.side,
        "evaluated_at": row.evaluated_at.isoformat(),
        "proposed_notional": _decimal_payload(row.proposed_notional),
        "available_cash": _decimal_payload(row.available_cash),
        "pending_cash_drag": _decimal_payload(row.pending_cash_drag),
        "expected_days_to_close": _decimal_payload(row.expected_days_to_close),
        "settlement_lag_days": _decimal_payload(row.settlement_lag_days),
        "cash_lockup_days": _decimal_payload(row.cash_lockup_days),
        "lockup_ratio": _decimal_payload(row.lockup_ratio),
        "annualized_opportunity_cost_proxy": _decimal_payload(
            row.annualized_opportunity_cost_proxy,
        ),
        "opportunity_cost": _decimal_payload(row.opportunity_cost),
        "cash_lockup_status": row.cash_lockup_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: PaperCandidateCashLockupDigestCandidate,
    *,
    config: PaperCandidateCashLockupDigestConfig,
    generated_at: datetime,
) -> PaperCandidateCashLockupDigestRow:
    if candidate.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    cash_lockup_days = _add_decimal(
        candidate.expected_days_to_close,
        candidate.settlement_lag_days,
    )
    lockup_ratio = _divide_decimal(
        _add_decimal(candidate.proposed_notional, candidate.pending_cash_drag),
        candidate.available_cash,
    )
    opportunity_cost = _multiply_decimal(
        candidate.proposed_notional,
        config.annualized_opportunity_cost_proxy,
        cash_lockup_days,
        _divide_by=_DAYS_PER_YEAR,
    )
    status, terminal_reason = _row_status_and_reason(lockup_ratio, config)
    reason_codes = _normalize_reason_codes(
        (
            *candidate.reason_codes,
            terminal_reason,
            *_risk_reason_codes(candidate, opportunity_cost, config),
        ),
        require_nonempty=True,
    )
    return PaperCandidateCashLockupDigestRow(
        redacted_candidate_reference=_redacted_reference(
            "candidate_ref",
            candidate.candidate_reference,
        ),
        redacted_market_reference=_redacted_reference(
            "market_ref",
            candidate.market_reference,
        ),
        side=candidate.side,
        evaluated_at=candidate.evaluated_at,
        proposed_notional=candidate.proposed_notional,
        available_cash=candidate.available_cash,
        pending_cash_drag=candidate.pending_cash_drag,
        expected_days_to_close=candidate.expected_days_to_close,
        settlement_lag_days=candidate.settlement_lag_days,
        cash_lockup_days=cash_lockup_days,
        lockup_ratio=lockup_ratio,
        annualized_opportunity_cost_proxy=config.annualized_opportunity_cost_proxy,
        opportunity_cost=opportunity_cost,
        cash_lockup_status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reason(
    lockup_ratio: Decimal,
    config: PaperCandidateCashLockupDigestConfig,
) -> tuple[str, str]:
    if lockup_ratio >= config.blocked_lockup_ratio:
        return "blocked", _BLOCKED_RATIO_REASON_CODE
    if lockup_ratio >= config.watch_lockup_ratio:
        return "watch", _WATCH_RATIO_REASON_CODE
    return "pass", _PASS_REASON_CODE


def _risk_reason_codes(
    candidate: PaperCandidateCashLockupDigestCandidate,
    opportunity_cost: Decimal,
    config: PaperCandidateCashLockupDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.pending_cash_drag > _ZERO:
        reason_codes.append(_PENDING_CASH_DRAG_REASON_CODE)
    if opportunity_cost >= config.watch_opportunity_cost:
        reason_codes.append(_OPPORTUNITY_COST_WATCH_REASON_CODE)
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[PaperCandidateCashLockupDigestCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized = tuple(_candidate_from_supplied_row(row) for row in rows)
    seen: set[str] = set()
    for row in normalized:
        if row.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(row.candidate_reference)
    return normalized


def _candidate_from_supplied_row(
    row: object,
) -> PaperCandidateCashLockupDigestCandidate:
    if type(row) is PaperCandidateCashLockupDigestCandidate:
        _require_safety_flags("candidate", row)
        return row
    raise ValueError("candidates must contain PaperCandidateCashLockupDigestCandidate")


def _normalize_rows(
    rows: object,
) -> tuple[PaperCandidateCashLockupDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PaperCandidateCashLockupDigestRow:
            raise ValueError("rows must contain PaperCandidateCashLockupDigestRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: PaperCandidateCashLockupDigestRow,
) -> tuple[int, Decimal, str, str]:
    return (
        _ROW_STATUS_PRIORITY[row.cash_lockup_status],
        -row.lockup_ratio,
        row.redacted_candidate_reference,
        row.side,
    )


def _status_count(
    rows: tuple[PaperCandidateCashLockupDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.cash_lockup_status == status))


def _max_lockup_ratio(rows: tuple[PaperCandidateCashLockupDigestRow, ...]) -> Decimal:
    if not rows:
        return _zero()
    return max(row.lockup_ratio for row in rows)


def _max_cash_lockup_days(
    rows: tuple[PaperCandidateCashLockupDigestRow, ...],
) -> Decimal:
    if not rows:
        return _zero()
    return max(row.cash_lockup_days for row in rows)


def _report_status(rows: tuple[PaperCandidateCashLockupDigestRow, ...]) -> str:
    if any(row.cash_lockup_status == "blocked" for row in rows):
        return "blocked"
    if any(row.cash_lockup_status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[PaperCandidateCashLockupDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in _REPORT_REASON_PRIORITY
        if reason_code in observed
    )


def _validate_row(row: PaperCandidateCashLockupDigestRow) -> None:
    if row.cash_lockup_days != _add_decimal(
        row.expected_days_to_close,
        row.settlement_lag_days,
    ):
        raise ValueError("cash_lockup_days must match timing fields")
    if row.lockup_ratio != _divide_decimal(
        _add_decimal(row.proposed_notional, row.pending_cash_drag),
        row.available_cash,
    ):
        raise ValueError("lockup_ratio must match cash fields")
    if row.opportunity_cost != _multiply_decimal(
        row.proposed_notional,
        row.annualized_opportunity_cost_proxy,
        row.cash_lockup_days,
        _divide_by=_DAYS_PER_YEAR,
    ):
        raise ValueError("opportunity_cost must match row fields")


def _validate_report(report: PaperCandidateCashLockupDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.total_proposed_notional != _sum_decimal(
        row.proposed_notional for row in report.rows
    ):
        raise ValueError("total_proposed_notional must match rows")
    if report.total_pending_cash_drag != _sum_decimal(
        row.pending_cash_drag for row in report.rows
    ):
        raise ValueError("total_pending_cash_drag must match rows")
    if report.total_opportunity_cost != _sum_decimal(
        row.opportunity_cost for row in report.rows
    ):
        raise ValueError("total_opportunity_cost must match rows")
    if report.max_lockup_ratio != _max_lockup_ratio(report.rows):
        raise ValueError("max_lockup_ratio must match rows")
    if report.max_cash_lockup_days != _max_cash_lockup_days(report.rows):
        raise ValueError("max_cash_lockup_days must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in _UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must be nonempty")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string("reason_code", item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _add_decimal(*values: Decimal) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _multiply_decimal(
    *values: Decimal,
    _divide_by: Decimal | None = None,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        result = Decimal("1")
        for value in values:
            result *= value
        if _divide_by is not None:
            result /= _divide_by
    return _quantize(result)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(left / right)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _zero() -> Decimal:
    return _ZERO.quantize(_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _count_payload(value: Decimal) -> str:
    return format(value, "f")


def _redacted_reference(prefix: str, value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
