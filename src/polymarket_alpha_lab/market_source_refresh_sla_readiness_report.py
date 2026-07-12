from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_SOURCE_REFRESH_SLA_READINESS_CONFIG_VERSION",
    "MarketSourceRefreshSlaReadinessConfig",
    "MarketSourceRefreshSlaReadinessItem",
    "MarketSourceRefreshSlaReadinessReport",
    "MarketSourceRefreshSlaReadinessRow",
    "build_market_source_refresh_sla_readiness_report",
    "market_source_refresh_sla_readiness_report_payload",
)


DEFAULT_MARKET_SOURCE_REFRESH_SLA_READINESS_CONFIG_VERSION = (
    "market-source-refresh-sla-readiness-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_REFRESH_SLA_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_CONTRADICTION_STATUSES = ("none", "suspected", "confirmed")

_CONFIRMED_CONTRADICTION_REASON = "confirmed_source_contradiction"
_MARKET_CLOSE_STALE_BLOCK_REASON = "market_close_refresh_stale_block"
_REFRESH_DUE_REASON = "refresh_due_within_sla_window"
_OFFICIAL_STALE_REASON = "official_anchor_stale"
_INDEPENDENT_STALE_REASON = "independent_source_stale"
_SUSPECTED_CONTRADICTION_REASON = "suspected_source_contradiction"
_READY_REASON = "source_refresh_sla_ready"
_NO_CANDIDATES_REASON = "no_market_source_refresh_candidates"

_REASON_CODES = (
    _CONFIRMED_CONTRADICTION_REASON,
    _MARKET_CLOSE_STALE_BLOCK_REASON,
    _REFRESH_DUE_REASON,
    _OFFICIAL_STALE_REASON,
    _INDEPENDENT_STALE_REASON,
    _SUSPECTED_CONTRADICTION_REASON,
    _READY_REASON,
    _NO_CANDIDATES_REASON,
)
_REASON_WEIGHT = {
    reason_code: index for index, reason_code in enumerate(_REASON_CODES)
}

_NEXT_STEP_BY_STATUS = {
    "blocked": "block_report_only_source_refresh_review",
    "watch": "watch_report_only_source_refresh_queue",
    "pass": "allow_report_only_source_refresh_readiness",
}


@dataclass(frozen=True)
class MarketSourceRefreshSlaReadinessConfig:
    config_version: str = DEFAULT_MARKET_SOURCE_REFRESH_SLA_READINESS_CONFIG_VERSION
    official_anchor_stale_after_hours: Decimal = Decimal("6.000000")
    independent_source_stale_after_hours: Decimal = Decimal("12.000000")
    refresh_due_soon_hours: Decimal = Decimal("2.000000")
    market_close_urgent_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketSourceRefreshSlaReadinessConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "official_anchor_stale_after_hours",
            "independent_source_stale_after_hours",
            "refresh_due_soon_hours",
            "market_close_urgent_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketSourceRefreshSlaReadinessItem:
    candidate_id: str
    official_anchor_age_hours: Decimal
    independent_source_age_hours: Decimal
    refresh_due_hours: Decimal
    contradiction_status: str
    market_close_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketSourceRefreshSlaReadinessItem does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "official_anchor_age_hours",
            "independent_source_age_hours",
            "refresh_due_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_contradiction_status(
            "contradiction_status",
            self.contradiction_status,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketSourceRefreshSlaReadinessRow:
    candidate_id: str
    official_anchor_age_hours: Decimal
    independent_source_age_hours: Decimal
    refresh_due_hours: Decimal
    contradiction_status: str
    market_close_hours: Decimal
    refresh_sla_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketSourceRefreshSlaReadinessRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "official_anchor_age_hours",
            "independent_source_age_hours",
            "refresh_due_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_contradiction_status(
            "contradiction_status",
            self.contradiction_status,
        )
        _require_refresh_sla_status("refresh_sla_status", self.refresh_sla_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_canonical_string("manual_next_step", self.manual_next_step)
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketSourceRefreshSlaReadinessReport:
    config_version: str
    official_anchor_stale_after_hours: Decimal
    independent_source_stale_after_hours: Decimal
    refresh_due_soon_hours: Decimal
    market_close_urgent_hours: Decimal
    refresh_sla_status: str
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    stale_candidate_count: Decimal
    contradiction_candidate_count: Decimal
    due_candidate_count: Decimal
    urgent_close_candidate_count: Decimal
    pass_candidate_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketSourceRefreshSlaReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketSourceRefreshSlaReadinessReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "official_anchor_stale_after_hours",
            "independent_source_stale_after_hours",
            "refresh_due_soon_hours",
            "market_close_urgent_hours",
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "stale_candidate_count",
            "contradiction_candidate_count",
            "due_candidate_count",
            "urgent_close_candidate_count",
            "pass_candidate_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("pass_candidate_ratio", self.pass_candidate_ratio)
        _require_refresh_sla_status("refresh_sla_status", self.refresh_sla_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_source_refresh_sla_readiness_report(
    items: Iterable[MarketSourceRefreshSlaReadinessItem],
    *,
    config: MarketSourceRefreshSlaReadinessConfig,
) -> MarketSourceRefreshSlaReadinessReport:
    if type(config) is not MarketSourceRefreshSlaReadinessConfig:
        raise ValueError("config must be a MarketSourceRefreshSlaReadinessConfig")
    _require_hard_flags(config)
    source_items = _normalize_items(items)
    rows = tuple(
        sorted(
            (_row_from_item(item, config=config) for item in source_items),
            key=_row_sort_key,
        ),
    )
    candidate_count = _decimal_count(len(rows))
    pass_candidate_count = _status_count(rows, "pass")

    return MarketSourceRefreshSlaReadinessReport(
        config_version=config.config_version,
        official_anchor_stale_after_hours=config.official_anchor_stale_after_hours,
        independent_source_stale_after_hours=(
            config.independent_source_stale_after_hours
        ),
        refresh_due_soon_hours=config.refresh_due_soon_hours,
        market_close_urgent_hours=config.market_close_urgent_hours,
        refresh_sla_status=_report_status(rows),
        candidate_count=candidate_count,
        pass_candidate_count=pass_candidate_count,
        watch_candidate_count=_status_count(rows, "watch"),
        blocked_candidate_count=_status_count(rows, "blocked"),
        stale_candidate_count=_stale_candidate_count(rows),
        contradiction_candidate_count=_reason_count(
            rows,
            _CONFIRMED_CONTRADICTION_REASON,
        ),
        due_candidate_count=_reason_count(rows, _REFRESH_DUE_REASON),
        urgent_close_candidate_count=_reason_count(
            rows,
            _MARKET_CLOSE_STALE_BLOCK_REASON,
        ),
        pass_candidate_ratio=_ratio(pass_candidate_count, candidate_count),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_source_refresh_sla_readiness_report_payload(
    report: MarketSourceRefreshSlaReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceRefreshSlaReadinessReport:
        raise ValueError("report must be a MarketSourceRefreshSlaReadinessReport")
    _require_hard_flags(report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("payload must be a dict")
    return value


def _row_from_item(
    item: MarketSourceRefreshSlaReadinessItem,
    *,
    config: MarketSourceRefreshSlaReadinessConfig,
) -> MarketSourceRefreshSlaReadinessRow:
    reason_codes = _row_reason_codes(item, config=config)
    status = _row_status(reason_codes)
    return MarketSourceRefreshSlaReadinessRow(
        candidate_id=item.candidate_id,
        official_anchor_age_hours=item.official_anchor_age_hours,
        independent_source_age_hours=item.independent_source_age_hours,
        refresh_due_hours=item.refresh_due_hours,
        contradiction_status=item.contradiction_status,
        market_close_hours=item.market_close_hours,
        refresh_sla_status=status,
        reason_codes=reason_codes,
        manual_next_step=_NEXT_STEP_BY_STATUS[status],
    )


def _row_reason_codes(
    item: MarketSourceRefreshSlaReadinessItem,
    *,
    config: MarketSourceRefreshSlaReadinessConfig,
) -> tuple[str, ...]:
    requested_codes: list[str] = []
    official_is_stale = (
        item.official_anchor_age_hours > config.official_anchor_stale_after_hours
    )
    independent_is_stale = (
        item.independent_source_age_hours
        > config.independent_source_stale_after_hours
    )
    market_is_urgent = item.market_close_hours <= config.market_close_urgent_hours

    if item.contradiction_status == "confirmed":
        requested_codes.append(_CONFIRMED_CONTRADICTION_REASON)
    if market_is_urgent and (official_is_stale or independent_is_stale):
        requested_codes.append(_MARKET_CLOSE_STALE_BLOCK_REASON)
    if item.refresh_due_hours <= config.refresh_due_soon_hours:
        requested_codes.append(_REFRESH_DUE_REASON)
    if official_is_stale:
        requested_codes.append(_OFFICIAL_STALE_REASON)
    if independent_is_stale:
        requested_codes.append(_INDEPENDENT_STALE_REASON)
    if item.contradiction_status == "suspected":
        requested_codes.append(_SUSPECTED_CONTRADICTION_REASON)
    if not requested_codes:
        requested_codes.append(_READY_REASON)
    return tuple(
        reason_code for reason_code in _REASON_CODES if reason_code in requested_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        _CONFIRMED_CONTRADICTION_REASON in reason_codes
        or _MARKET_CLOSE_STALE_BLOCK_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (_READY_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[MarketSourceRefreshSlaReadinessRow, ...]) -> str:
    if not rows:
        return "blocked"
    return min((row.refresh_sla_status for row in rows), key=lambda item: _STATUS_WEIGHT[item])


def _report_reason_codes(
    rows: tuple[MarketSourceRefreshSlaReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_NO_CANDIDATES_REASON,)
    requested_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _READY_REASON
    }
    if not requested_codes:
        return (_READY_REASON,)
    return tuple(
        reason_code for reason_code in _REASON_CODES if reason_code in requested_codes
    )


def _normalize_items(
    items: Iterable[MarketSourceRefreshSlaReadinessItem],
) -> tuple[MarketSourceRefreshSlaReadinessItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for item in normalized:
        if type(item) is not MarketSourceRefreshSlaReadinessItem:
            raise ValueError(
                "items must contain MarketSourceRefreshSlaReadinessItem values",
            )
        _require_hard_flags(item)
        if item.candidate_id in seen_candidate_ids:
            raise ValueError("items must contain unique candidate_id values")
        seen_candidate_ids.add(item.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketSourceRefreshSlaReadinessRow],
) -> tuple[MarketSourceRefreshSlaReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_candidate_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketSourceRefreshSlaReadinessRow:
            raise ValueError(
                "rows must contain MarketSourceRefreshSlaReadinessRow values",
            )
        _require_hard_flags(row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("rows must contain unique candidate_id values")
        seen_candidate_ids.add(row.candidate_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic refresh sla sort")
    return normalized


def _validate_row_consistency(row: MarketSourceRefreshSlaReadinessRow) -> None:
    if row.refresh_sla_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match refresh_sla_status")
    if row.manual_next_step != _NEXT_STEP_BY_STATUS[row.refresh_sla_status]:
        raise ValueError("manual_next_step must match refresh_sla_status")
    has_stale_information = (
        _OFFICIAL_STALE_REASON in row.reason_codes
        or _INDEPENDENT_STALE_REASON in row.reason_codes
    )
    if has_stale_information and row.refresh_sla_status not in {"watch", "blocked"}:
        raise ValueError("stale source information can only watch or block")
    if row.refresh_sla_status == "pass" and row.reason_codes != (_READY_REASON,):
        raise ValueError("pass rows must use ready reason")
    if _READY_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("ready reason must not mix with attention reasons")


def _validate_report_consistency(report: MarketSourceRefreshSlaReadinessReport) -> None:
    rows = report.rows
    if report.candidate_count != _decimal_count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_candidate_count != _status_count(rows, "pass"):
        raise ValueError("pass_candidate_count must match rows")
    if report.watch_candidate_count != _status_count(rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_candidate_count must match rows")
    if report.stale_candidate_count != _stale_candidate_count(rows):
        raise ValueError("stale_candidate_count must match rows")
    if report.contradiction_candidate_count != _reason_count(
        rows,
        _CONFIRMED_CONTRADICTION_REASON,
    ):
        raise ValueError("contradiction_candidate_count must match rows")
    if report.due_candidate_count != _reason_count(rows, _REFRESH_DUE_REASON):
        raise ValueError("due_candidate_count must match rows")
    if report.urgent_close_candidate_count != _reason_count(
        rows,
        _MARKET_CLOSE_STALE_BLOCK_REASON,
    ):
        raise ValueError("urgent_close_candidate_count must match rows")
    if report.pass_candidate_ratio != _ratio(
        report.pass_candidate_count,
        report.candidate_count,
    ):
        raise ValueError("pass_candidate_ratio must match rows")
    if report.refresh_sla_status != _report_status(rows):
        raise ValueError("refresh_sla_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(row: MarketSourceRefreshSlaReadinessRow) -> tuple[int, int, str]:
    return (
        _STATUS_WEIGHT[row.refresh_sla_status],
        _primary_reason_weight(row.reason_codes),
        row.candidate_id,
    )


def _primary_reason_weight(reason_codes: tuple[str, ...]) -> int:
    return min(_REASON_WEIGHT[reason_code] for reason_code in reason_codes)


def _status_count(
    rows: tuple[MarketSourceRefreshSlaReadinessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.refresh_sla_status == status))


def _reason_count(
    rows: tuple[MarketSourceRefreshSlaReadinessRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _stale_candidate_count(
    rows: tuple[MarketSourceRefreshSlaReadinessRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if _OFFICIAL_STALE_REASON in row.reason_codes
            or _INDEPENDENT_STALE_REASON in row.reason_codes
        ),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_WEIGHT:
            raise ValueError("reason_codes must contain known values")
    expected = tuple(reason_code for reason_code in _REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_contradiction_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _CONTRADICTION_STATUSES:
        raise ValueError(f"{field_name} must be none, suspected, or confirmed")


def _require_refresh_sla_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _REFRESH_SLA_STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or pass")


def _require_ratio(field_name: str, value: Decimal) -> None:
    if value > _ONE:
        raise ValueError(f"{field_name} must be at most one")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")
