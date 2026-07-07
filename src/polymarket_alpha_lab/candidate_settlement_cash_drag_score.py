"""Pure paper settlement cash-drag candidate scoring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "CandidateSettlementCashDragFacts",
    "CandidateSettlementCashDragScoreConfig",
    "CandidateSettlementCashDragScoreReport",
    "CandidateSettlementCashDragScoreRow",
    "build_candidate_settlement_cash_drag_score_report",
    "candidate_settlement_cash_drag_score_payload",
)


_CONFIG_VERSION = "candidate-settlement-cash-drag-score-v0"
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SUPPORTS = ("pass", "watch", "block")
_SUPPORT_RANK = {"block": 0, "watch": 1, "pass": 2}
_HEX = "0123456789abcdef"

_NOTIONAL_WEIGHT = Decimal("0.150000")
_RESOLUTION_WEIGHT = Decimal("0.200000")
_LAG_WEIGHT = Decimal("0.150000")
_DISPUTE_WEIGHT = Decimal("0.250000")
_PRESSURE_WEIGHT = Decimal("0.200000")
_FEE_BUFFER_WEIGHT = Decimal("0.050000")

_WATCH_DISPUTE_REVISION_RISK = Decimal("0.250000")
_BLOCKED_DISPUTE_REVISION_RISK = Decimal("0.900000")
_WATCH_PORTFOLIO_CASH_LOCKUP_PRESSURE = Decimal("0.250000")
_BLOCKED_PORTFOLIO_CASH_LOCKUP_PRESSURE = Decimal("0.750000")

_EMPTY_REASON = "settlement_cash_drag_score_empty"
_PASSED_REASON = "settlement_cash_drag_passed"
_WATCH_REASON = "settlement_cash_drag_watch"
_BLOCKED_REASON = "settlement_cash_drag_blocked"
_PAPER_CASH_DRAG_RISK_REASON = "paper_cash_drag_risk_high"
_RESOLUTION_WATCH_REASON = "resolution_lockup_watch"
_RESOLUTION_LONG_REASON = "resolution_lockup_long"
_LAG_WATCH_REASON = "settlement_lag_watch"
_LAG_LONG_REASON = "settlement_lag_long"
_DISPUTE_PRESENT_REASON = "dispute_revision_risk_present"
_DISPUTE_HIGH_REASON = "dispute_revision_risk_high"
_PRESSURE_PRESENT_REASON = "portfolio_cash_lockup_pressure_present"
_PRESSURE_HIGH_REASON = "portfolio_cash_lockup_pressure_high"
_FEE_SHORTFALL_REASON = "fee_cost_buffer_shortfall_present"
_REPORT_REASON_SEQUENCE = (
    _BLOCKED_REASON,
    _WATCH_REASON,
    _PASSED_REASON,
    _PAPER_CASH_DRAG_RISK_REASON,
    _RESOLUTION_WATCH_REASON,
    _RESOLUTION_LONG_REASON,
    _LAG_WATCH_REASON,
    _LAG_LONG_REASON,
    _DISPUTE_PRESENT_REASON,
    _DISPUTE_HIGH_REASON,
    _PRESSURE_PRESENT_REASON,
    _PRESSURE_HIGH_REASON,
    _FEE_SHORTFALL_REASON,
    _EMPTY_REASON,
)
_SUPPORT_REASONS = (_PASSED_REASON, _WATCH_REASON, _BLOCKED_REASON)


@dataclass(frozen=True)
class CandidateSettlementCashDragScoreConfig:
    config_version: str = _CONFIG_VERSION
    watch_score_threshold: Decimal = Decimal("0.250000")
    blocked_score_threshold: Decimal = Decimal("0.700000")
    notional_risk_cap: Decimal = Decimal("10000.000000")
    watch_paper_notional: Decimal = Decimal("5000.000000")
    resolution_days_cap: Decimal = Decimal("90.000000")
    watch_resolution_days: Decimal = Decimal("30.000000")
    blocked_resolution_days: Decimal = Decimal("90.000000")
    settlement_lag_days_cap: Decimal = Decimal("30.000000")
    watch_settlement_lag_days: Decimal = Decimal("7.000000")
    blocked_settlement_lag_days: Decimal = Decimal("14.000000")
    minimum_fee_cost_buffer_ratio: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateSettlementCashDragScoreConfig:
            raise ValueError("config must be CandidateSettlementCashDragScoreConfig")
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        for field_name in (
            "watch_score_threshold",
            "blocked_score_threshold",
            "minimum_fee_cost_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "notional_risk_cap",
            "watch_paper_notional",
            "resolution_days_cap",
            "watch_resolution_days",
            "blocked_resolution_days",
            "settlement_lag_days_cap",
            "watch_settlement_lag_days",
            "blocked_settlement_lag_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.blocked_score_threshold:
            raise ValueError("watch_score_threshold must not exceed blocked_score_threshold")
        if self.watch_resolution_days > self.blocked_resolution_days:
            raise ValueError("watch_resolution_days must not exceed blocked_resolution_days")
        if self.watch_settlement_lag_days > self.blocked_settlement_lag_days:
            raise ValueError(
                "watch_settlement_lag_days must not exceed blocked_settlement_lag_days",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class CandidateSettlementCashDragFacts:
    redacted_candidate_reference: str
    redacted_market_reference: str
    proposed_paper_notional: Decimal
    days_to_expected_resolution: Decimal
    settlement_lag_days: Decimal
    dispute_revision_risk: Decimal
    portfolio_cash_lockup_pressure: Decimal
    fee_cost_buffer: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateSettlementCashDragFacts:
            raise ValueError("facts must be CandidateSettlementCashDragFacts")
        object.__setattr__(
            self,
            "redacted_candidate_reference",
            _require_redacted_reference(
                "redacted_candidate_reference",
                self.redacted_candidate_reference,
                "candidate_ref_",
            ),
        )
        object.__setattr__(
            self,
            "redacted_market_reference",
            _require_redacted_reference(
                "redacted_market_reference",
                self.redacted_market_reference,
                "market_ref_",
            ),
        )
        object.__setattr__(
            self,
            "proposed_paper_notional",
            _require_positive_decimal(
                "proposed_paper_notional",
                self.proposed_paper_notional,
            ),
        )
        for field_name in (
            "days_to_expected_resolution",
            "settlement_lag_days",
            "fee_cost_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("dispute_revision_risk", "portfolio_cash_lockup_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_flags("facts", self)


@dataclass(frozen=True)
class CandidateSettlementCashDragScoreRow:
    redacted_candidate_reference: str
    redacted_market_reference: str
    settlement_cash_drag_score: Decimal
    risk_support: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateSettlementCashDragScoreRow:
            raise ValueError("row must be CandidateSettlementCashDragScoreRow")
        object.__setattr__(
            self,
            "redacted_candidate_reference",
            _require_redacted_reference(
                "redacted_candidate_reference",
                self.redacted_candidate_reference,
                "candidate_ref_",
            ),
        )
        object.__setattr__(
            self,
            "redacted_market_reference",
            _require_redacted_reference(
                "redacted_market_reference",
                self.redacted_market_reference,
                "market_ref_",
            ),
        )
        object.__setattr__(
            self,
            "settlement_cash_drag_score",
            _require_ratio("settlement_cash_drag_score", self.settlement_cash_drag_score),
        )
        _require_member("risk_support", self.risk_support, _SUPPORTS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class CandidateSettlementCashDragScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_settlement_cash_drag_score: Decimal
    risk_support: str
    reason_codes: tuple[str, ...]
    rows: tuple[CandidateSettlementCashDragScoreRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateSettlementCashDragScoreReport:
            raise ValueError("report must be CandidateSettlementCashDragScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_settlement_cash_drag_score",
            _require_ratio(
                "max_settlement_cash_drag_score",
                self.max_settlement_cash_drag_score,
            ),
        )
        _require_member("risk_support", self.risk_support, _SUPPORTS)
        object.__setattr__(self, "reason_codes", _normalize_reasons(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_flags("report", self)


def build_candidate_settlement_cash_drag_score_report(
    candidates: Iterable[CandidateSettlementCashDragFacts],
    *,
    config: CandidateSettlementCashDragScoreConfig,
    generated_at: datetime,
) -> CandidateSettlementCashDragScoreReport:
    if type(config) is not CandidateSettlementCashDragScoreConfig:
        raise ValueError("config must be CandidateSettlementCashDragScoreConfig")
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    seen: set[str] = set()
    rows: list[CandidateSettlementCashDragScoreRow] = []
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of CandidateSettlementCashDragFacts")
    try:
        candidate_tuple = tuple(candidates)
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of CandidateSettlementCashDragFacts",
        ) from exc
    for candidate in candidate_tuple:
        if type(candidate) is not CandidateSettlementCashDragFacts:
            raise ValueError("candidates must contain CandidateSettlementCashDragFacts")
        _require_flags("facts", candidate)
        if candidate.redacted_candidate_reference in seen:
            raise ValueError("duplicate redacted_candidate_reference")
        seen.add(candidate.redacted_candidate_reference)
        rows.append(_build_row(candidate, config))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if not sorted_rows:
        return CandidateSettlementCashDragScoreReport(
            generated_at=generated_at,
            config_version=config.config_version,
            candidate_count=_count_decimal(0),
            pass_count=_count_decimal(0),
            watch_count=_count_decimal(0),
            blocked_count=_count_decimal(0),
            max_settlement_cash_drag_score=_ZERO,
            risk_support="watch",
            reason_codes=(_EMPTY_REASON,),
            rows=(),
        )

    return CandidateSettlementCashDragScoreReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_support == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_support == "watch"),
        ),
        blocked_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_support == "block"),
        ),
        max_settlement_cash_drag_score=max(
            row.settlement_cash_drag_score for row in sorted_rows
        ),
        risk_support=_report_support(sorted_rows),
        reason_codes=_report_reasons(sorted_rows),
        rows=sorted_rows,
    )


def candidate_settlement_cash_drag_score_payload(
    report: CandidateSettlementCashDragScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateSettlementCashDragScoreReport:
        raise ValueError("report must be CandidateSettlementCashDragScoreReport")
    report = _revalidated_report(report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_text(report.candidate_count),
        "pass_count": _decimal_text(report.pass_count),
        "watch_count": _decimal_text(report.watch_count),
        "blocked_count": _decimal_text(report.blocked_count),
        "max_settlement_cash_drag_score": _decimal_text(
            report.max_settlement_cash_drag_score,
        ),
        "risk_support": report.risk_support,
        "reason_codes": list(report.reason_codes),
        "rows": [
            {
                "redacted_candidate_reference": row.redacted_candidate_reference,
                "redacted_market_reference": row.redacted_market_reference,
                "settlement_cash_drag_score": _decimal_text(
                    row.settlement_cash_drag_score,
                ),
                "risk_support": row.risk_support,
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
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
) -> CandidateSettlementCashDragScoreRow:
    fee_shortfall = _fee_cost_buffer_shortfall(candidate, config)
    score = _settlement_cash_drag_score(candidate, config, fee_shortfall)
    support = _risk_support(candidate, config, score, fee_shortfall)
    return CandidateSettlementCashDragScoreRow(
        redacted_candidate_reference=candidate.redacted_candidate_reference,
        redacted_market_reference=candidate.redacted_market_reference,
        settlement_cash_drag_score=score,
        risk_support=support,
        reason_codes=_row_reasons(candidate, config, fee_shortfall, support),
    )


def _revalidated_report(
    report: CandidateSettlementCashDragScoreReport,
) -> CandidateSettlementCashDragScoreReport:
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    return CandidateSettlementCashDragScoreReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        max_settlement_cash_drag_score=report.max_settlement_cash_drag_score,
        risk_support=report.risk_support,
        reason_codes=report.reason_codes,
        rows=tuple(_revalidated_row(row) for row in report.rows),
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _revalidated_row(
    row: CandidateSettlementCashDragScoreRow,
) -> CandidateSettlementCashDragScoreRow:
    if type(row) is not CandidateSettlementCashDragScoreRow:
        raise ValueError("rows must contain CandidateSettlementCashDragScoreRow")
    return CandidateSettlementCashDragScoreRow(
        redacted_candidate_reference=row.redacted_candidate_reference,
        redacted_market_reference=row.redacted_market_reference,
        settlement_cash_drag_score=row.settlement_cash_drag_score,
        risk_support=row.risk_support,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _settlement_cash_drag_score(
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
    fee_shortfall: Decimal,
) -> Decimal:
    fee_required = _required_fee_cost_buffer(candidate, config)
    score = (
        _ratio_to_cap(candidate.proposed_paper_notional, config.notional_risk_cap)
        * _NOTIONAL_WEIGHT
        + _ratio_to_cap(
            candidate.days_to_expected_resolution,
            config.resolution_days_cap,
        )
        * _RESOLUTION_WEIGHT
        + _ratio_to_cap(candidate.settlement_lag_days, config.settlement_lag_days_cap)
        * _LAG_WEIGHT
        + candidate.dispute_revision_risk * _DISPUTE_WEIGHT
        + candidate.portfolio_cash_lockup_pressure * _PRESSURE_WEIGHT
        + _safe_ratio(fee_shortfall, fee_required) * _FEE_BUFFER_WEIGHT
    )
    return min(max(_q(score), _ZERO), _ONE)


def _risk_support(
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
    score: Decimal,
    fee_shortfall: Decimal,
) -> str:
    if score >= config.blocked_score_threshold:
        return "block"
    if candidate.days_to_expected_resolution >= config.blocked_resolution_days:
        return "block"
    if candidate.settlement_lag_days >= config.blocked_settlement_lag_days:
        return "block"
    if candidate.dispute_revision_risk >= _BLOCKED_DISPUTE_REVISION_RISK:
        return "block"
    if (
        candidate.portfolio_cash_lockup_pressure
        >= _BLOCKED_PORTFOLIO_CASH_LOCKUP_PRESSURE
    ):
        return "block"
    if score >= config.watch_score_threshold:
        return "watch"
    if candidate.proposed_paper_notional >= config.watch_paper_notional:
        return "watch"
    if candidate.days_to_expected_resolution >= config.watch_resolution_days:
        return "watch"
    if candidate.settlement_lag_days >= config.watch_settlement_lag_days:
        return "watch"
    if candidate.dispute_revision_risk >= _WATCH_DISPUTE_REVISION_RISK:
        return "watch"
    if (
        candidate.portfolio_cash_lockup_pressure
        >= _WATCH_PORTFOLIO_CASH_LOCKUP_PRESSURE
    ):
        return "watch"
    if fee_shortfall > _ZERO:
        return "watch"
    return "pass"


def _row_reasons(
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
    fee_shortfall: Decimal,
    support: str,
) -> tuple[str, ...]:
    values = [_support_reason(support)]
    if candidate.proposed_paper_notional >= config.watch_paper_notional:
        values.append(_PAPER_CASH_DRAG_RISK_REASON)
    if candidate.days_to_expected_resolution >= config.blocked_resolution_days:
        values.append(_RESOLUTION_LONG_REASON)
    elif candidate.days_to_expected_resolution >= config.watch_resolution_days:
        values.append(_RESOLUTION_WATCH_REASON)
    if candidate.settlement_lag_days >= config.blocked_settlement_lag_days:
        values.append(_LAG_LONG_REASON)
    elif candidate.settlement_lag_days >= config.watch_settlement_lag_days:
        values.append(_LAG_WATCH_REASON)
    if candidate.dispute_revision_risk >= _BLOCKED_DISPUTE_REVISION_RISK:
        values.append(_DISPUTE_HIGH_REASON)
    elif candidate.dispute_revision_risk >= _WATCH_DISPUTE_REVISION_RISK:
        values.append(_DISPUTE_PRESENT_REASON)
    if (
        candidate.portfolio_cash_lockup_pressure
        >= _BLOCKED_PORTFOLIO_CASH_LOCKUP_PRESSURE
    ):
        values.append(_PRESSURE_HIGH_REASON)
    elif (
        candidate.portfolio_cash_lockup_pressure
        >= _WATCH_PORTFOLIO_CASH_LOCKUP_PRESSURE
    ):
        values.append(_PRESSURE_PRESENT_REASON)
    if fee_shortfall > _ZERO:
        values.append(_FEE_SHORTFALL_REASON)
    return tuple(values)


def _support_reason(support: str) -> str:
    if support == "block":
        return _BLOCKED_REASON
    if support == "watch":
        return _WATCH_REASON
    return _PASSED_REASON


def _required_fee_cost_buffer(
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
) -> Decimal:
    return _q(candidate.proposed_paper_notional * config.minimum_fee_cost_buffer_ratio)


def _fee_cost_buffer_shortfall(
    candidate: CandidateSettlementCashDragFacts,
    config: CandidateSettlementCashDragScoreConfig,
) -> Decimal:
    return max(_required_fee_cost_buffer(candidate, config) - candidate.fee_cost_buffer, _ZERO)


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    return _safe_ratio(min(value, cap), cap)


def _report_support(rows: tuple[CandidateSettlementCashDragScoreRow, ...]) -> str:
    if any(row.risk_support == "block" for row in rows):
        return "block"
    if any(row.risk_support == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reasons(
    rows: tuple[CandidateSettlementCashDragScoreRow, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    return tuple(reason for reason in _REPORT_REASON_SEQUENCE if reason in seen)


def _row_sort_key(
    row: CandidateSettlementCashDragScoreRow,
) -> tuple[int, Decimal, str, str]:
    return (
        _SUPPORT_RANK[row.risk_support],
        -row.settlement_cash_drag_score,
        row.redacted_candidate_reference,
        row.redacted_market_reference,
    )


def _validate_row(row: CandidateSettlementCashDragScoreRow) -> None:
    support_reason = _support_reason(row.risk_support)
    if row.reason_codes[0] != support_reason:
        raise ValueError("reason_codes must start with risk_support")
    for reason in row.reason_codes[1:]:
        if reason in _SUPPORT_REASONS:
            raise ValueError("reason_codes must not include conflicting risk_support")
    if _EMPTY_REASON in row.reason_codes:
        raise ValueError("reason_codes must not include empty report reason")


def _validate_report(report: CandidateSettlementCashDragScoreReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count does not match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.risk_support == "pass"),
    ):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.risk_support == "watch"),
    ):
        raise ValueError("watch_count does not match rows")
    if report.blocked_count != _count_decimal(
        sum(1 for row in report.rows if row.risk_support == "block"),
    ):
        raise ValueError("blocked_count does not match rows")
    if report.max_settlement_cash_drag_score != _max_score(report.rows):
        raise ValueError("max_settlement_cash_drag_score does not match rows")
    expected_support = "watch" if not report.rows else _report_support(report.rows)
    if report.risk_support != expected_support:
        raise ValueError("risk_support does not match rows")
    expected_reasons = (_EMPTY_REASON,) if not report.rows else _report_reasons(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match rows")


def _normalize_rows(
    rows: tuple[CandidateSettlementCashDragScoreRow, ...],
) -> tuple[CandidateSettlementCashDragScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not CandidateSettlementCashDragScoreRow:
            raise ValueError("rows must contain CandidateSettlementCashDragScoreRow")
        _require_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reasons(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty tuple")
    for reason in value:
        _require_text("reason_code", reason)
        if reason not in _REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code is not supported")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    return value


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_config_version(value: object) -> str:
    value = _require_text("config_version", value)
    if value != _CONFIG_VERSION:
        raise ValueError("config_version must be the supported public token")
    return value


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> str:
    value = _require_text(field_name, value)
    suffix = value.removeprefix(prefix)
    if suffix == value or len(suffix) != 16:
        raise ValueError(f"{field_name} must be redacted")
    if any(character not in _HEX for character in suffix):
        raise ValueError(f"{field_name} must be redacted")
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
    return _q(numerator / denominator)


def _max_score(rows: tuple[CandidateSettlementCashDragScoreRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.settlement_cash_drag_score for row in rows)


def _count_decimal(value: int) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _decimal_text(value: Decimal) -> str:
    return str(value)
