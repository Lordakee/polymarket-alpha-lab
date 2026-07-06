"""Read-only paper candidate research risk register."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_RESEARCH_RISK_REGISTER_CONFIG_VERSION = (
    "strategy-candidate-research-risk-register-v10"
)

_SCORE_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_MINUTE_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_PRIORITIES = ("urgent", "elevated", "normal", "none")
_MITIGATION_STATUSES = ("open", "in_progress", "mitigated")

_EMPTY_REASON = "candidate_research_risk_register_empty"
_PASS_REASON = "candidate_research_risk_pass"
_REGISTER_BLOCK_REASON = "candidate_research_risk_register_block"
_REGISTER_WATCH_REASON = "candidate_research_risk_register_watch"
_REGISTER_PASS_REASON = "candidate_research_risk_register_pass"
_SCORE_BLOCK_REASON = "research_risk_score_block"
_SCORE_WATCH_REASON = "research_risk_score_watch"
_DUE_BLOCK_REASON = "research_resolution_due_soon_block"
_DUE_WATCH_REASON = "research_resolution_due_soon_watch"
_OPEN_REASON = "unmitigated_research_risk"

_REASON_PRIORITY = (
    _REGISTER_BLOCK_REASON,
    _REGISTER_WATCH_REASON,
    _REGISTER_PASS_REASON,
    _SCORE_BLOCK_REASON,
    _DUE_BLOCK_REASON,
    _OPEN_REASON,
    _SCORE_WATCH_REASON,
    _DUE_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)
_BLOCK_REASONS = frozenset(
    (
        _REGISTER_BLOCK_REASON,
        _SCORE_BLOCK_REASON,
        _DUE_BLOCK_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _REGISTER_WATCH_REASON,
        _SCORE_WATCH_REASON,
        _DUE_WATCH_REASON,
        _OPEN_REASON,
    ),
)


@dataclass(frozen=True)
class StrategyCandidateResearchRiskRegisterConfig:
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_RISK_REGISTER_CONFIG_VERSION
    watch_risk_score: Decimal = Decimal("0.250000")
    block_risk_score: Decimal = Decimal("0.600000")
    watch_resolution_minutes: Decimal = Decimal("240")
    block_resolution_minutes: Decimal = Decimal("60")
    top_risk_limit: Decimal = Decimal("5")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in ("watch_risk_score", "block_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_resolution_minutes",
            "block_resolution_minutes",
            "top_risk_limit",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_minutes(field_name, getattr(self, field_name)),
            )
        if self.block_risk_score < self.watch_risk_score:
            raise ValueError("block_risk_score must be at least watch_risk_score")
        if self.block_resolution_minutes > self.watch_resolution_minutes:
            raise ValueError(
                "block_resolution_minutes must be at most watch_resolution_minutes",
            )
        if self.top_risk_limit == _ZERO_COUNT:
            raise ValueError("top_risk_limit must be positive")
        require_paper_only_flags("candidate research risk config", self)


@dataclass(frozen=True)
class StrategyCandidateResearchRiskItem:
    market_id: str
    risk_items: tuple[str, ...]
    severity_score: Decimal
    likelihood_score: Decimal
    owner_team: str
    time_to_resolution_minutes: Decimal
    mitigation_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("market_id", self.market_id)
        object.__setattr__(
            self,
            "risk_items",
            _normalize_risk_items(self.risk_items),
        )
        object.__setattr__(
            self,
            "severity_score",
            _normalize_unit_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "likelihood_score",
            _normalize_unit_decimal("likelihood_score", self.likelihood_score),
        )
        _require_text("owner_team", self.owner_team)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_member(
            "mitigation_status",
            self.mitigation_status,
            _MITIGATION_STATUSES,
        )
        require_paper_only_flags("candidate research risk item", self)


@dataclass(frozen=True)
class StrategyCandidateResearchRiskRow:
    market_id: str
    risk_items: tuple[str, ...]
    risk_item_count: Decimal
    severity_score: Decimal
    likelihood_score: Decimal
    risk_score: Decimal
    owner_team: str
    time_to_resolution_minutes: Decimal
    mitigation_status: str
    register_status: str
    mitigation_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("market_id", self.market_id)
        object.__setattr__(
            self,
            "risk_items",
            _normalize_risk_items(self.risk_items),
        )
        object.__setattr__(
            self,
            "risk_item_count",
            _normalize_count("risk_item_count", self.risk_item_count),
        )
        object.__setattr__(
            self,
            "severity_score",
            _normalize_unit_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "likelihood_score",
            _normalize_unit_decimal("likelihood_score", self.likelihood_score),
        )
        object.__setattr__(
            self,
            "risk_score",
            _normalize_unit_decimal("risk_score", self.risk_score),
        )
        _require_text("owner_team", self.owner_team)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_member(
            "mitigation_status",
            self.mitigation_status,
            _MITIGATION_STATUSES,
        )
        _require_member("register_status", self.register_status, _STATUSES)
        _require_member("mitigation_priority", self.mitigation_priority, _PRIORITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("candidate research risk row", self)


@dataclass(frozen=True)
class StrategyCandidateResearchRiskRegisterReport:
    generated_at: datetime
    config_version: str
    risk_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_risk_score: Decimal
    register_status: str
    top_risks: tuple[StrategyCandidateResearchRiskRow, ...]
    mitigation_priority: str
    reason_codes: tuple[str, ...]
    risk_rows: tuple[StrategyCandidateResearchRiskRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("risk_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_risk_score",
            _normalize_unit_decimal("max_risk_score", self.max_risk_score),
        )
        _require_member("register_status", self.register_status, _STATUSES)
        object.__setattr__(self, "risk_rows", _normalize_rows("risk_rows", self.risk_rows))
        object.__setattr__(self, "top_risks", _normalize_rows("top_risks", self.top_risks))
        _require_member("mitigation_priority", self.mitigation_priority, _PRIORITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("candidate research risk report", self)
        require_paper_only_flags("candidate research risk report", self)


def build_strategy_candidate_research_risk_register(
    risk_items: Iterable[object],
    *,
    config: StrategyCandidateResearchRiskRegisterConfig,
    generated_at: datetime,
) -> StrategyCandidateResearchRiskRegisterReport:
    if type(config) is not StrategyCandidateResearchRiskRegisterConfig:
        raise ValueError("config must be a StrategyCandidateResearchRiskRegisterConfig")
    require_paper_only_flags("candidate research risk config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_item(item, config=config) for item in _normalize_input_items(risk_items)),
            key=_row_key,
        ),
    )
    top_risks = rows[: int(config.top_risk_limit)]
    return StrategyCandidateResearchRiskRegisterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        risk_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.register_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.register_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.register_status == "block")),
        max_risk_score=_max_decimal(row.risk_score for row in rows),
        register_status=_register_status(rows),
        top_risks=top_risks,
        mitigation_priority=_register_priority(rows),
        reason_codes=_report_reason_codes(rows),
        risk_rows=rows,
    )


def strategy_candidate_research_risk_register_payload(
    report: StrategyCandidateResearchRiskRegisterReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateResearchRiskRegisterReport:
        raise ValueError("report must be a StrategyCandidateResearchRiskRegisterReport")
    require_paper_only_flags("candidate research risk report", report)
    reject_unsafe_surface_fields("candidate research risk report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    require_paper_only_flags("candidate research risk payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_item(
    item: StrategyCandidateResearchRiskItem,
    *,
    config: StrategyCandidateResearchRiskRegisterConfig,
) -> StrategyCandidateResearchRiskRow:
    risk_score = _risk_score(item.severity_score, item.likelihood_score)
    reason_codes = _row_reason_codes(item, risk_score=risk_score, config=config)
    status = _status_from_reason_codes(reason_codes)
    return StrategyCandidateResearchRiskRow(
        market_id=item.market_id,
        risk_items=item.risk_items,
        risk_item_count=_count(len(item.risk_items)),
        severity_score=item.severity_score,
        likelihood_score=item.likelihood_score,
        risk_score=risk_score,
        owner_team=item.owner_team,
        time_to_resolution_minutes=item.time_to_resolution_minutes,
        mitigation_status=item.mitigation_status,
        register_status=status,
        mitigation_priority=_priority_from_status(status),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: StrategyCandidateResearchRiskItem,
    *,
    risk_score: Decimal,
    config: StrategyCandidateResearchRiskRegisterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if risk_score >= config.block_risk_score:
        reason_codes.append(_SCORE_BLOCK_REASON)
    elif risk_score >= config.watch_risk_score:
        reason_codes.append(_SCORE_WATCH_REASON)
    if item.mitigation_status != "mitigated":
        if item.time_to_resolution_minutes <= config.block_resolution_minutes:
            reason_codes.append(_DUE_BLOCK_REASON)
        elif item.time_to_resolution_minutes <= config.watch_resolution_minutes:
            reason_codes.append(_DUE_WATCH_REASON)
    if item.mitigation_status == "open":
        reason_codes.append(_OPEN_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _normalize_input_items(
    values: Iterable[object],
) -> tuple[StrategyCandidateResearchRiskItem, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("risk_items must be iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("risk_items must be iterable") from exc
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for item in items:
        if type(item) is not StrategyCandidateResearchRiskItem:
            raise ValueError(
                "risk_items must contain StrategyCandidateResearchRiskItem values",
            )
        require_paper_only_flags("candidate research risk item", item)
        item_key = (item.market_id, item.risk_items)
        if item_key in seen:
            raise ValueError("duplicate market risk")
        seen.add(item_key)
    return items


def _normalize_rows(
    field_name: str,
    rows: object,
) -> tuple[StrategyCandidateResearchRiskRow, ...]:
    if type(rows) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateResearchRiskRow:
            raise ValueError(f"{field_name} must contain StrategyCandidateResearchRiskRow")
        require_paper_only_flags("candidate research risk row", row)
    if len({(row.market_id, row.risk_items) for row in normalized}) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _validate_row(row: StrategyCandidateResearchRiskRow) -> None:
    if row.risk_item_count != _count(len(row.risk_items)):
        raise ValueError("risk_item_count must match risk_items")
    if row.risk_score != _risk_score(row.severity_score, row.likelihood_score):
        raise ValueError("risk_score must match severity_score and likelihood_score")
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.register_status != expected_status:
        raise ValueError("register_status must match reason_codes")
    if row.mitigation_priority != _priority_from_status(row.register_status):
        raise ValueError("mitigation_priority must match register_status")


def _validate_report(report: StrategyCandidateResearchRiskRegisterReport) -> None:
    rows = report.risk_rows
    if report.risk_count != _count(len(rows)):
        raise ValueError("risk_count must match risk_rows")
    if report.pass_count != _count(sum(1 for row in rows if row.register_status == "pass")):
        raise ValueError("pass_count must match risk_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.register_status == "watch")):
        raise ValueError("watch_count must match risk_rows")
    if report.block_count != _count(sum(1 for row in rows if row.register_status == "block")):
        raise ValueError("block_count must match risk_rows")
    if report.max_risk_score != _max_decimal(row.risk_score for row in rows):
        raise ValueError("max_risk_score must match risk_rows")
    if report.register_status != _register_status(rows):
        raise ValueError("register_status must match risk_rows")
    if report.top_risks != _expected_top_risks(report.top_risks, rows):
        raise ValueError("top_risks must match risk_rows")
    if report.mitigation_priority != _register_priority(rows):
        raise ValueError("mitigation_priority must match risk_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match risk_rows")


def _expected_top_risks(
    top_risks: tuple[StrategyCandidateResearchRiskRow, ...],
    rows: tuple[StrategyCandidateResearchRiskRow, ...],
) -> tuple[StrategyCandidateResearchRiskRow, ...]:
    if len(top_risks) > len(rows):
        return rows
    return rows[: len(top_risks)]


def _risk_score(severity_score: Decimal, likelihood_score: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (severity_score * likelihood_score).quantize(_SCORE_QUANTUM)


def _register_status(rows: tuple[StrategyCandidateResearchRiskRow, ...]) -> str:
    if any(row.register_status == "block" for row in rows):
        return "block"
    if any(row.register_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _register_priority(rows: tuple[StrategyCandidateResearchRiskRow, ...]) -> str:
    if any(row.mitigation_priority == "urgent" for row in rows):
        return "urgent"
    if any(row.mitigation_priority == "elevated" for row in rows):
        return "elevated"
    if rows:
        return "normal"
    return "none"


def _report_reason_codes(
    rows: tuple[StrategyCandidateResearchRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    status = _register_status(rows)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _BLOCK_REASONS or reason_code in _WATCH_REASONS
    }
    if status == "pass":
        return (_REGISTER_PASS_REASON,)
    register_reason = (
        _REGISTER_BLOCK_REASON if status == "block" else _REGISTER_WATCH_REASON
    )
    observed.add(register_reason)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in observed)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _priority_from_status(status: str) -> str:
    if status == "block":
        return "urgent"
    if status == "watch":
        return "elevated"
    return "normal"


def _row_key(
    row: StrategyCandidateResearchRiskRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_WEIGHT[row.register_status],
        -row.risk_score,
        row.time_to_resolution_minutes,
        -row.risk_item_count,
        row.market_id,
        row.owner_team,
    )


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for code in codes:
        _require_text("reason_codes", code)
        if code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        if code in {_REGISTER_BLOCK_REASON, _REGISTER_WATCH_REASON, _REGISTER_PASS_REASON}:
            raise ValueError("row reason_codes must not include register status")
        if code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(code)
    return tuple(sorted(codes, key=_REASON_PRIORITY.index))


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for code in codes:
        _require_text("reason_codes", code)
        if code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        if code in seen:
            raise ValueError("reason_codes must be unique")
        index = _REASON_PRIORITY.index(code)
        if index <= previous_index:
            raise ValueError("reason_codes must follow priority sequence")
        previous_index = index
        seen.add(code)
    return codes


def _normalize_risk_items(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("risk_items must be a list or tuple")
    items = tuple(value)
    if not items:
        raise ValueError("risk_items must not be empty")
    seen: set[str] = set()
    for item in items:
        _require_text("risk_items", item)
        if item in seen:
            raise ValueError("risk_items must be unique")
        seen.add(item)
    return items


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SCORE_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_minutes(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_MINUTE_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_RISK_REGISTER_CONFIG_VERSION",
    "StrategyCandidateResearchRiskItem",
    "StrategyCandidateResearchRiskRegisterConfig",
    "StrategyCandidateResearchRiskRegisterReport",
    "StrategyCandidateResearchRiskRow",
    "build_strategy_candidate_research_risk_register",
    "strategy_candidate_research_risk_register_payload",
)
