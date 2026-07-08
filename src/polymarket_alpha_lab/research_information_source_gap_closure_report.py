"""Pure report-only closure plan for research information-source gaps."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_INFORMATION_SOURCE_GAP_CLOSURE_CONFIG_VERSION = (
    "research-information-source-gap-closure-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "research_information_source_gap_closure_no_inputs"
PASS_REASON = "research_information_source_gap_closure_pass"
WATCH_REASON = "research_information_source_gap_closure_watch"
BLOCK_REASON = "research_information_source_gap_closure_block"
MISSING_SOURCES_WATCH_REASON = (
    "research_information_source_gap_closure_missing_sources_watch"
)
MISSING_SOURCES_BLOCK_REASON = (
    "research_information_source_gap_closure_missing_sources_block"
)
STALE_SOURCES_WATCH_REASON = (
    "research_information_source_gap_closure_stale_sources_watch"
)
STALE_SOURCES_BLOCK_REASON = (
    "research_information_source_gap_closure_stale_sources_block"
)

REPORT_REASON_CODES = (
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODES = (
    MISSING_SOURCES_BLOCK_REASON,
    STALE_SOURCES_BLOCK_REASON,
    MISSING_SOURCES_WATCH_REASON,
    STALE_SOURCES_WATCH_REASON,
    PASS_REASON,
)

PASS_ACTION = "maintain_research_information_source_coverage"
WATCH_ACTION = "schedule_public_research_source_refresh"
BLOCK_ACTION = "close_research_information_source_gap_before_workflow_use"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
HOUR_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE = Decimal("1")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("raw", "_", "source", "_", "ref"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        "question",
        "dsn",
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        "trade",
        "position",
        "buy",
        "sell",
        _join_parts("au", "th"),
        _join_parts("private", "_", "key"),
        "secret",
        "credential",
        "signing",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchInformationSourceGapClosureConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_INFORMATION_SOURCE_GAP_CLOSURE_CONFIG_VERSION
    watch_coverage_ratio: Decimal = Decimal("0.800000")
    block_coverage_ratio: Decimal = Decimal("0.500000")
    watch_fresh_ratio: Decimal = Decimal("0.800000")
    block_fresh_ratio: Decimal = Decimal("0.500000")
    watch_stale_age_hours: Decimal = Decimal("72.000000")
    block_stale_age_hours: Decimal = Decimal("168.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceGapClosureConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_coverage_ratio",
            "block_coverage_ratio",
            "watch_fresh_ratio",
            "block_fresh_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_stale_age_hours", "block_stale_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_coverage_ratio > self.watch_coverage_ratio:
            raise ValueError("block_coverage_ratio must be <= watch_coverage_ratio")
        if self.block_fresh_ratio > self.watch_fresh_ratio:
            raise ValueError("block_fresh_ratio must be <= watch_fresh_ratio")
        if self.block_stale_age_hours < self.watch_stale_age_hours:
            raise ValueError("block_stale_age_hours must be >= watch_stale_age_hours")
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchInformationSourceGapClosureInput(_FinalPublicDataclass):
    domain_name: str
    team_name: str
    source_family: str
    required_source_count: Decimal
    available_source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    oldest_source_age_hours: Decimal
    closure_sla_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceGapClosureInput, "input")
        for field_name in ("domain_name", "team_name", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "required_source_count",
            "available_source_count",
            "fresh_source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("oldest_source_age_hours", "closure_sla_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.available_source_count > self.required_source_count:
            raise ValueError("available_source_count must be <= required_source_count")
        if self.fresh_source_count > self.available_source_count:
            raise ValueError("fresh_source_count must be <= available_source_count")
        _require_hard_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchInformationSourceGapClosureAction(_FinalPublicDataclass):
    domain_name: str
    team_name: str
    source_family: str
    status: str
    closure_action: str
    required_source_count: Decimal
    available_source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    oldest_source_age_hours: Decimal
    closure_sla_hours: Decimal
    coverage_gap_count: Decimal
    freshness_gap_count: Decimal
    coverage_ratio: Decimal
    fresh_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceGapClosureAction, "action")
        for field_name in ("domain_name", "team_name", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        _require_public_string("closure_action", self.closure_action)
        for field_name in (
            "required_source_count",
            "available_source_count",
            "fresh_source_count",
            "stale_source_count",
            "coverage_gap_count",
            "freshness_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("oldest_source_age_hours", "closure_sla_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("coverage_ratio", "fresh_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_action(self)
        _require_hard_flags("action", self)
        _reject_unsafe_public_surface("action", self)


@dataclass(frozen=True)
class ResearchInformationSourceGapClosureReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_source_count: Decimal
    stale_source_count: Decimal
    average_coverage_ratio: Decimal
    minimum_fresh_ratio: Decimal
    rows: tuple[ResearchInformationSourceGapClosureAction, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceGapClosureReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_coverage_ratio", "minimum_fresh_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_actions(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_public_digest(self)
        _reject_unsafe_public_surface("report", self)


def build_research_information_source_gap_closure_report(
    inputs: list[ResearchInformationSourceGapClosureInput]
    | tuple[ResearchInformationSourceGapClosureInput, ...],
    *,
    config: ResearchInformationSourceGapClosureConfig,
    generated_at: datetime,
) -> ResearchInformationSourceGapClosureReport:
    if type(config) is not ResearchInformationSourceGapClosureConfig:
        raise ValueError("config must be a ResearchInformationSourceGapClosureConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    actions = tuple(
        sorted(
            (
                _action_from_input(input_row, config=config)
                for input_row in _normalize_inputs(inputs)
            ),
            key=_action_sort_key,
        ),
    )
    domain_team_count = _count(len(actions))
    pass_count = _status_count(actions, "pass")
    watch_count = _status_count(actions, "watch")
    block_count = _status_count(actions, "block")
    return ResearchInformationSourceGapClosureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(actions),
        reason_codes=_report_reason_codes(actions),
        domain_team_count=domain_team_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        missing_source_count=_sum_decimal(row.coverage_gap_count for row in actions),
        stale_source_count=_sum_decimal(row.stale_source_count for row in actions),
        average_coverage_ratio=_mean_decimal(
            tuple(row.coverage_ratio for row in actions),
        ),
        minimum_fresh_ratio=_min_decimal(tuple(row.fresh_ratio for row in actions)),
        rows=actions,
    )


def research_information_source_gap_closure_report_to_payload(
    report: ResearchInformationSourceGapClosureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchInformationSourceGapClosureReport:
        raise ValueError("report must be a ResearchInformationSourceGapClosureReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_information_source_gap_closure_digest(
    report: ResearchInformationSourceGapClosureReport,
) -> str:
    if type(report) is not ResearchInformationSourceGapClosureReport:
        raise ValueError("report must be a ResearchInformationSourceGapClosureReport")
    _require_hard_flags("report", report)
    if report.public_digest != _expected_public_digest(report):
        raise ValueError("public_digest must match report fields")
    return report.public_digest


def _normalize_inputs(
    value: object,
) -> tuple[ResearchInformationSourceGapClosureInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for input_row in inputs:
        if type(input_row) is not ResearchInformationSourceGapClosureInput:
            raise ValueError(
                "inputs must contain ResearchInformationSourceGapClosureInput values",
            )
        _require_hard_flags("input", input_row)
        key = (input_row.domain_name, input_row.team_name, input_row.source_family)
        if key in seen_keys:
            raise ValueError("duplicate domain/team/source family inputs")
        seen_keys.add(key)
    return inputs


def _action_from_input(
    input_row: ResearchInformationSourceGapClosureInput,
    *,
    config: ResearchInformationSourceGapClosureConfig,
) -> ResearchInformationSourceGapClosureAction:
    coverage_gap_count = max(ZERO, input_row.required_source_count - input_row.available_source_count)
    freshness_gap_count = max(ZERO, input_row.required_source_count - input_row.fresh_source_count)
    coverage_ratio = _ratio(input_row.available_source_count, input_row.required_source_count)
    fresh_ratio = _ratio(input_row.fresh_source_count, input_row.required_source_count)
    status = _action_status(
        coverage_ratio=coverage_ratio,
        fresh_ratio=fresh_ratio,
        oldest_source_age_hours=input_row.oldest_source_age_hours,
        closure_sla_hours=input_row.closure_sla_hours,
        config=config,
    )
    return ResearchInformationSourceGapClosureAction(
        domain_name=input_row.domain_name,
        team_name=input_row.team_name,
        source_family=input_row.source_family,
        status=status,
        closure_action=_closure_action(status),
        required_source_count=input_row.required_source_count,
        available_source_count=input_row.available_source_count,
        fresh_source_count=input_row.fresh_source_count,
        stale_source_count=input_row.stale_source_count,
        oldest_source_age_hours=input_row.oldest_source_age_hours,
        closure_sla_hours=input_row.closure_sla_hours,
        coverage_gap_count=coverage_gap_count,
        freshness_gap_count=freshness_gap_count,
        coverage_ratio=coverage_ratio,
        fresh_ratio=fresh_ratio,
        reason_codes=_action_reason_codes(
            status=status,
            coverage_gap_count=coverage_gap_count,
            freshness_gap_count=freshness_gap_count,
            coverage_ratio=coverage_ratio,
            fresh_ratio=fresh_ratio,
            oldest_source_age_hours=input_row.oldest_source_age_hours,
            closure_sla_hours=input_row.closure_sla_hours,
            config=config,
        ),
    )


def _action_status(
    *,
    coverage_ratio: Decimal,
    fresh_ratio: Decimal,
    oldest_source_age_hours: Decimal,
    closure_sla_hours: Decimal,
    config: ResearchInformationSourceGapClosureConfig,
) -> str:
    if (
        coverage_ratio < config.block_coverage_ratio
        or fresh_ratio < config.block_fresh_ratio
        or oldest_source_age_hours > config.block_stale_age_hours
    ):
        return "block"
    if (
        coverage_ratio < config.watch_coverage_ratio
        or fresh_ratio < config.watch_fresh_ratio
        or oldest_source_age_hours > config.watch_stale_age_hours
        or oldest_source_age_hours > closure_sla_hours
    ):
        return "watch"
    return "pass"


def _action_reason_codes(
    *,
    status: str,
    coverage_gap_count: Decimal,
    freshness_gap_count: Decimal,
    coverage_ratio: Decimal,
    fresh_ratio: Decimal,
    oldest_source_age_hours: Decimal,
    closure_sla_hours: Decimal,
    config: ResearchInformationSourceGapClosureConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    missing_reason = (
        MISSING_SOURCES_BLOCK_REASON
        if coverage_ratio < config.block_coverage_ratio
        else MISSING_SOURCES_WATCH_REASON
    )
    stale_reason = (
        STALE_SOURCES_BLOCK_REASON
        if fresh_ratio < config.block_fresh_ratio
        or oldest_source_age_hours > config.block_stale_age_hours
        else STALE_SOURCES_WATCH_REASON
    )
    reasons: list[str] = []
    if coverage_gap_count > ZERO or coverage_ratio < config.watch_coverage_ratio:
        reasons.append(missing_reason)
    if (
        freshness_gap_count > ZERO
        or fresh_ratio < config.watch_fresh_ratio
        or oldest_source_age_hours > closure_sla_hours
        or oldest_source_age_hours > config.watch_stale_age_hours
    ):
        reasons.append(stale_reason)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _closure_action(status: str) -> str:
    return {
        "pass": PASS_ACTION,
        "watch": WATCH_ACTION,
        "block": BLOCK_ACTION,
    }[status]


def _report_status(
    rows: tuple[ResearchInformationSourceGapClosureAction, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchInformationSourceGapClosureAction, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons: list[str] = []
    if any(row.status == "block" for row in rows):
        reasons.append(BLOCK_REASON)
    if any(row.status == "watch" for row in rows):
        reasons.append(WATCH_REASON)
    if any(row.status == "pass" for row in rows):
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _normalize_actions(
    value: object,
) -> tuple[ResearchInformationSourceGapClosureAction, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchInformationSourceGapClosureAction:
            raise ValueError(
                "rows must contain ResearchInformationSourceGapClosureAction values",
            )
        _require_hard_flags("action", row)
    return rows


def _action_sort_key(row: ResearchInformationSourceGapClosureAction) -> tuple[int, str, str, str]:
    return (STATUS_RANK[row.status], row.domain_name, row.team_name, row.source_family)


def _status_count(
    rows: tuple[ResearchInformationSourceGapClosureAction, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_action(row: ResearchInformationSourceGapClosureAction) -> None:
    if row.available_source_count > row.required_source_count:
        raise ValueError("available_source_count must be <= required_source_count")
    if row.fresh_source_count > row.available_source_count:
        raise ValueError("fresh_source_count must be <= available_source_count")
    if row.coverage_gap_count != max(
        ZERO,
        row.required_source_count - row.available_source_count,
    ):
        raise ValueError("coverage_gap_count must match source counts")
    if row.freshness_gap_count != max(
        ZERO,
        row.required_source_count - row.fresh_source_count,
    ):
        raise ValueError("freshness_gap_count must match source counts")
    if row.coverage_ratio != _ratio(row.available_source_count, row.required_source_count):
        raise ValueError("coverage_ratio must match source counts")
    if row.fresh_ratio != _ratio(row.fresh_source_count, row.required_source_count):
        raise ValueError("fresh_ratio must match source counts")
    if row.closure_action != _closure_action(row.status):
        raise ValueError("closure_action must match status")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match pass status")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("reason_codes must match gap status")


def _validate_report(report: ResearchInformationSourceGapClosureReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_action_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.domain_team_count != _count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.missing_source_count != _sum_decimal(
        row.coverage_gap_count for row in report.rows
    ):
        raise ValueError("missing_source_count must match rows")
    if report.stale_source_count != _sum_decimal(
        row.stale_source_count for row in report.rows
    ):
        raise ValueError("stale_source_count must match rows")
    if report.average_coverage_ratio != _mean_decimal(
        tuple(row.coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_coverage_ratio must match rows")
    if report.minimum_fresh_ratio != _min_decimal(
        tuple(row.fresh_ratio for row in report.rows),
    ):
        raise ValueError("minimum_fresh_ratio must match rows")


def _normalize_reason_codes(
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError("reason_codes must contain supported public reasons")
    normalized = tuple(reason for reason in allowed if reason in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(HOUR_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(ONE)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(ONE)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return min(values)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(ONE)


def _require_or_set_public_digest(
    report: ResearchInformationSourceGapClosureReport,
) -> None:
    expected_digest = _expected_public_digest(report)
    if report.public_digest:
        _require_public_digest("public_digest", report.public_digest)
        if report.public_digest != expected_digest:
            raise ValueError("public_digest must match report fields")
        return
    object.__setattr__(report, "public_digest", expected_digest)


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _expected_public_digest(
    report: ResearchInformationSourceGapClosureReport,
) -> str:
    payload: dict[str, object] = {}
    for field in fields(report):
        if field.name == "public_digest":
            continue
        payload[field.name] = getattr(report, field.name)
    canonical_payload = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(nested) for nested in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_surface(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            _reject_unsafe_public_text(f"{label}.{key}", str(key))
            _reject_unsafe_public_surface(f"{label}.{key}", nested)
        return
    if isinstance(value, tuple | list):
        for index, nested in enumerate(value):
            _reject_unsafe_public_surface(f"{label}[{index}]", nested)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_SOURCE_GAP_CLOSURE_CONFIG_VERSION",
    "ResearchInformationSourceGapClosureAction",
    "ResearchInformationSourceGapClosureConfig",
    "ResearchInformationSourceGapClosureInput",
    "ResearchInformationSourceGapClosureReport",
    "build_research_information_source_gap_closure_report",
    "research_information_source_gap_closure_digest",
    "research_information_source_gap_closure_report_to_payload",
)
