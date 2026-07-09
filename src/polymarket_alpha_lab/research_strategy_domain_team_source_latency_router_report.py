"""Report-only domain/team source latency router."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SOURCE_LATENCY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-team-source-latency-router-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SOURCE_LATENCY_ROUTER_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyDomainTeamSourceLatencyRouterConfig",
    "ResearchStrategyDomainTeamSourceLatencyRouterInput",
    "ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount",
    "ResearchStrategyDomainTeamSourceLatencyRouterReport",
    "ResearchStrategyDomainTeamSourceLatencyRouterRow",
    "build_research_strategy_domain_team_source_latency_router_report",
    "research_strategy_domain_team_source_latency_router_digest",
    "research_strategy_domain_team_source_latency_router_digest_payload",
    "research_strategy_domain_team_source_latency_router_report_payload",
)


STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

MISSING_INPUTS_REASON = "domain_team_source_latency_router_missing_inputs"
PASS_REASON = "domain_team_source_latency_router_pass"
WATCH_REASON = "domain_team_source_latency_router_watch"
BLOCK_REASON = "domain_team_source_latency_router_block"
MISSING_ROUTE_REASON = "missing_route_timestamp"
LATENCY_BLOCK_REASON = "latency_above_block_threshold"
LATENCY_WATCH_REASON = "latency_above_watch_threshold"
FRESHNESS_BLOCK_REASON = "freshness_below_block_threshold"
FRESHNESS_WATCH_REASON = "freshness_below_watch_threshold"
CONFIDENCE_BLOCK_REASON = "confidence_below_block_threshold"
CONFIDENCE_WATCH_REASON = "confidence_below_watch_threshold"

REASON_CODE_SEQUENCE = (
    MISSING_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    MISSING_ROUTE_REASON,
    LATENCY_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    FRESHNESS_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    CONFIDENCE_BLOCK_REASON,
    CONFIDENCE_WATCH_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)
BLOCK_REASON_SET = frozenset(
    (
        BLOCK_REASON,
        MISSING_ROUTE_REASON,
        LATENCY_BLOCK_REASON,
        FRESHNESS_BLOCK_REASON,
        CONFIDENCE_BLOCK_REASON,
    ),
)
WATCH_REASON_SET = frozenset(
    (
        WATCH_REASON,
        LATENCY_WATCH_REASON,
        FRESHNESS_WATCH_REASON,
        CONFIDENCE_WATCH_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "source" "_" "url",
    "source" "-" "url",
    "source" " " "url",
    "source" "_" "text",
    "source" "-" "text",
    "source" " " "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "wal" "let",
    "or" "der",
    "tr" "ade",
    "b" "uy",
    "s" "ell",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "auth_",
    "_auth",
    "auth-",
    "-auth",
    "auth ",
    " auth",
    "li" "ve",
    "http://",
    "https://",
    "www.",
)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSourceLatencyRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SOURCE_LATENCY_ROUTER_REPORT_CONFIG_VERSION
    )
    latency_watch_seconds: Decimal = Decimal("900.000000")
    latency_block_seconds: Decimal = Decimal("3600.000000")
    freshness_watch_threshold: Decimal = Decimal("0.700000")
    freshness_block_threshold: Decimal = Decimal("0.250000")
    confidence_watch_threshold: Decimal = Decimal("0.700000")
    confidence_block_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSourceLatencyRouterConfig:
            raise TypeError(
                "ResearchStrategyDomainTeamSourceLatencyRouterConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_supported_config_version(self.config_version)
        for field_name in ("latency_watch_seconds", "latency_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.latency_block_seconds <= self.latency_watch_seconds:
            raise ValueError("latency_block_seconds must exceed latency_watch_seconds")
        for field_name in (
            "freshness_watch_threshold",
            "freshness_block_threshold",
            "confidence_watch_threshold",
            "confidence_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_watch_threshold <= self.freshness_block_threshold:
            raise ValueError(
                "freshness_watch_threshold must exceed freshness_block_threshold",
            )
        if self.confidence_watch_threshold <= self.confidence_block_threshold:
            raise ValueError(
                "confidence_watch_threshold must exceed confidence_block_threshold",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSourceLatencyRouterInput:
    route_ref: str
    domain_label: str
    team_label: str
    lane_label: str
    observed_at: datetime
    routed_at: datetime | None
    freshness_score: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSourceLatencyRouterInput:
            raise TypeError(
                "ResearchStrategyDomainTeamSourceLatencyRouterInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_private_ref("route_ref", self.route_ref)
        for field_name in ("domain_label", "team_label", "lane_label"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.routed_at is not None:
            object.__setattr__(self, "routed_at", _as_utc("routed_at", self.routed_at))
            if self.routed_at < self.observed_at:
                raise ValueError("routed_at must be at or after observed_at")
        object.__setattr__(
            self,
            "freshness_score",
            _require_probability_decimal("freshness_score", self.freshness_score),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability_decimal("confidence_score", self.confidence_score),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSourceLatencyRouterRow:
    rank: Decimal
    domain_label: str
    team_label: str
    lane_label: str
    sample_count: Decimal
    routed_count: Decimal
    missing_route_count: Decimal
    average_latency_seconds: Decimal
    max_latency_seconds: Decimal
    min_freshness_score: Decimal
    min_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSourceLatencyRouterRow:
            raise TypeError(
                "ResearchStrategyDomainTeamSourceLatencyRouterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _require_positive_whole_decimal("rank", self.rank))
        for field_name in ("domain_label", "team_label", "lane_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in ("sample_count", "routed_count", "missing_route_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_latency_seconds",
            "max_latency_seconds",
            "min_freshness_score",
            "min_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        digest = _digest(_row_digest_payload(self))
        if self.public_payload_digest:
            _require_digest("public_payload_digest", self.public_payload_digest)
            if self.public_payload_digest != digest:
                raise ValueError("public_payload_digest must match row payload")
        else:
            object.__setattr__(self, "public_payload_digest", digest)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount:
            raise TypeError(
                "ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_reason_code(self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSourceLatencyRouterReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_route_count: Decimal
    average_latency_seconds: Decimal
    max_latency_seconds: Decimal
    min_freshness_score: Decimal
    min_confidence_score: Decimal
    rows: tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSourceLatencyRouterReport:
            raise TypeError(
                "ResearchStrategyDomainTeamSourceLatencyRouterReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_route_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_latency_seconds",
            "max_latency_seconds",
            "min_freshness_score",
            "min_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        digest = _digest(
            research_strategy_domain_team_source_latency_router_digest_payload(self),
        )
        if self.public_payload_digest:
            _require_digest("public_payload_digest", self.public_payload_digest)
            if self.public_payload_digest != digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", digest)


def build_research_strategy_domain_team_source_latency_router_report(
    inputs: Iterable[ResearchStrategyDomainTeamSourceLatencyRouterInput],
    *,
    config: ResearchStrategyDomainTeamSourceLatencyRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamSourceLatencyRouterReport:
    if type(config) is not ResearchStrategyDomainTeamSourceLatencyRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainTeamSourceLatencyRouterConfig",
        )

    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    routed_latencies = tuple(
        _latency_seconds(item.observed_at, item.routed_at)
        for item in normalized_inputs
        if item.routed_at is not None
    )
    min_freshness_score = (
        min((item.freshness_score for item in normalized_inputs), default=ZERO)
    )
    min_confidence_score = (
        min((item.confidence_score for item in normalized_inputs), default=ZERO)
    )

    return ResearchStrategyDomainTeamSourceLatencyRouterReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_decimal_count(len(normalized_inputs)),
        group_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_row_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_row_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_row_status_count(rows, STATUS_BLOCK)),
        missing_route_count=_decimal_count(
            sum(1 for item in normalized_inputs if item.routed_at is None),
        ),
        average_latency_seconds=_decimal_average(routed_latencies),
        max_latency_seconds=max(routed_latencies, default=ZERO),
        min_freshness_score=min_freshness_score,
        min_confidence_score=min_confidence_score,
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_strategy_domain_team_source_latency_router_digest(
    report: ResearchStrategyDomainTeamSourceLatencyRouterReport,
) -> str:
    _require_report(report)
    return _digest(
        research_strategy_domain_team_source_latency_router_digest_payload(report),
    )


def research_strategy_domain_team_source_latency_router_digest_payload(
    report: ResearchStrategyDomainTeamSourceLatencyRouterReport,
) -> dict[str, Any]:
    _require_report(report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "observation_count": _decimal_to_string(report.observation_count),
        "group_count": _decimal_to_string(report.group_count),
        "pass_count": _decimal_to_string(report.pass_count),
        "watch_count": _decimal_to_string(report.watch_count),
        "block_count": _decimal_to_string(report.block_count),
        "missing_route_count": _decimal_to_string(report.missing_route_count),
        "average_latency_seconds": _decimal_to_string(report.average_latency_seconds),
        "max_latency_seconds": _decimal_to_string(report.max_latency_seconds),
        "min_freshness_score": _decimal_to_string(report.min_freshness_score),
        "min_confidence_score": _decimal_to_string(report.min_confidence_score),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def research_strategy_domain_team_source_latency_router_report_payload(
    report: ResearchStrategyDomainTeamSourceLatencyRouterReport,
) -> dict[str, Any]:
    payload = research_strategy_domain_team_source_latency_router_digest_payload(report)
    payload["public_payload_digest"] = report.public_payload_digest
    return payload


def _build_rows(
    inputs: tuple[ResearchStrategyDomainTeamSourceLatencyRouterInput, ...],
    config: ResearchStrategyDomainTeamSourceLatencyRouterConfig,
) -> tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[ResearchStrategyDomainTeamSourceLatencyRouterInput],
    ] = {}
    for item in inputs:
        grouped.setdefault(
            (item.domain_label, item.team_label, item.lane_label),
            [],
        ).append(item)

    row_values = tuple(
        _row_values(domain_label, team_label, lane_label, tuple(group_items), config)
        for (domain_label, team_label, lane_label), group_items in grouped.items()
    )
    sorted_values = tuple(
        sorted(
            row_values,
            key=lambda item: (
                STATUS_RANK[item["status"]],
                item["domain_label"],
                item["team_label"],
                item["lane_label"],
            ),
        ),
    )
    return tuple(
        ResearchStrategyDomainTeamSourceLatencyRouterRow(
            rank=_decimal_count(index),
            **values,
        )
        for index, values in enumerate(sorted_values, start=1)
    )


def _row_values(
    domain_label: str,
    team_label: str,
    lane_label: str,
    inputs: tuple[ResearchStrategyDomainTeamSourceLatencyRouterInput, ...],
    config: ResearchStrategyDomainTeamSourceLatencyRouterConfig,
) -> dict[str, Any]:
    routed_latencies = tuple(
        _latency_seconds(item.observed_at, item.routed_at)
        for item in inputs
        if item.routed_at is not None
    )
    missing_route_count = len(inputs) - len(routed_latencies)
    min_freshness_score = min(item.freshness_score for item in inputs)
    min_confidence_score = min(item.confidence_score for item in inputs)
    max_latency_seconds = max(routed_latencies, default=ZERO)
    reason_codes = _row_reason_codes(
        missing_route_count=_decimal_count(missing_route_count),
        max_latency_seconds=max_latency_seconds,
        min_freshness_score=min_freshness_score,
        min_confidence_score=min_confidence_score,
        config=config,
    )
    return {
        "domain_label": domain_label,
        "team_label": team_label,
        "lane_label": lane_label,
        "sample_count": _decimal_count(len(inputs)),
        "routed_count": _decimal_count(len(routed_latencies)),
        "missing_route_count": _decimal_count(missing_route_count),
        "average_latency_seconds": _decimal_average(routed_latencies),
        "max_latency_seconds": max_latency_seconds,
        "min_freshness_score": min_freshness_score,
        "min_confidence_score": min_confidence_score,
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    *,
    missing_route_count: Decimal,
    max_latency_seconds: Decimal,
    min_freshness_score: Decimal,
    min_confidence_score: Decimal,
    config: ResearchStrategyDomainTeamSourceLatencyRouterConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []

    if missing_route_count > ZERO:
        block_reasons.append(MISSING_ROUTE_REASON)
    if max_latency_seconds > config.latency_block_seconds:
        block_reasons.append(LATENCY_BLOCK_REASON)
    elif max_latency_seconds > config.latency_watch_seconds:
        watch_reasons.append(LATENCY_WATCH_REASON)
    if min_freshness_score < config.freshness_block_threshold:
        block_reasons.append(FRESHNESS_BLOCK_REASON)
    elif min_freshness_score < config.freshness_watch_threshold:
        watch_reasons.append(FRESHNESS_WATCH_REASON)
    if min_confidence_score < config.confidence_block_threshold:
        block_reasons.append(CONFIDENCE_BLOCK_REASON)
    elif min_confidence_score < config.confidence_watch_threshold:
        watch_reasons.append(CONFIDENCE_WATCH_REASON)

    if block_reasons:
        return (BLOCK_REASON, *block_reasons)
    if watch_reasons:
        return (WATCH_REASON, *watch_reasons)
    return (PASS_REASON,)


def _report_status(
    rows: tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    active = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not active:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in active)


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts = {
        reason_code: sum(
            ONE for row in rows for row_reason in row.reason_codes if row_reason == reason_code
        )
        for reason_code in report_reason_codes
    }
    return tuple(
        ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in report_reason_codes
    )


def _row_status_count(
    rows: tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_SET for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_SET for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _validate_row_consistency(
    row: ResearchStrategyDomainTeamSourceLatencyRouterRow,
) -> None:
    if row.sample_count != row.routed_count + row.missing_route_count:
        raise ValueError("sample_count must equal routed_count plus missing_route_count")
    if row.routed_count == ZERO:
        if row.average_latency_seconds != ZERO or row.max_latency_seconds != ZERO:
            raise ValueError("latency seconds must be zero when routed_count is zero")
    elif row.average_latency_seconds > row.max_latency_seconds:
        raise ValueError("average_latency_seconds must be at most max_latency_seconds")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyDomainTeamSourceLatencyRouterReport,
) -> None:
    rows = report.rows
    if report.observation_count != sum((row.sample_count for row in rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.group_count != _decimal_count(len(rows)):
        raise ValueError("group_count must match rows")
    if report.pass_count != _decimal_count(_row_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_row_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_row_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.missing_route_count != sum(
        (row.missing_route_count for row in rows),
        ZERO,
    ):
        raise ValueError("missing_route_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if rows:
        if report.max_latency_seconds != max(row.max_latency_seconds for row in rows):
            raise ValueError("max_latency_seconds must match rows")
        if report.min_freshness_score != min(row.min_freshness_score for row in rows):
            raise ValueError("min_freshness_score must match rows")
        if report.min_confidence_score != min(row.min_confidence_score for row in rows):
            raise ValueError("min_confidence_score must match rows")
    elif (
        report.average_latency_seconds != ZERO
        or report.max_latency_seconds != ZERO
        or report.min_freshness_score != ZERO
        or report.min_confidence_score != ZERO
    ):
        raise ValueError("empty report numeric summaries must be zero")


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyDomainTeamSourceLatencyRouterInput],
) -> tuple[ResearchStrategyDomainTeamSourceLatencyRouterInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError(
            "inputs must be an iterable of "
            "ResearchStrategyDomainTeamSourceLatencyRouterInput",
        )
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of "
            "ResearchStrategyDomainTeamSourceLatencyRouterInput",
        ) from exc
    for item in normalized:
        if type(item) is not ResearchStrategyDomainTeamSourceLatencyRouterInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategyDomainTeamSourceLatencyRouterInput values",
            )
        _require_hard_flags(item)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyDomainTeamSourceLatencyRouterRow],
) -> tuple[ResearchStrategyDomainTeamSourceLatencyRouterRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyDomainTeamSourceLatencyRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainTeamSourceLatencyRouterRow "
                "values",
            )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use contiguous Decimal ranks")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: Iterable[ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount],
) -> tuple[ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount values",
            )
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return normalized


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if PASS_REASON in reason_codes and reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must not mix pass with watch or block reasons")
    if MISSING_INPUTS_REASON in reason_codes and reason_codes != (MISSING_INPUTS_REASON,):
        raise ValueError("reason_codes must not mix missing inputs with row reasons")
    return reason_codes


def _row_digest_payload(
    row: ResearchStrategyDomainTeamSourceLatencyRouterRow,
) -> dict[str, Any]:
    return {
        "rank": _decimal_to_string(row.rank),
        "domain_label": row.domain_label,
        "team_label": row.team_label,
        "lane_label": row.lane_label,
        "sample_count": _decimal_to_string(row.sample_count),
        "routed_count": _decimal_to_string(row.routed_count),
        "missing_route_count": _decimal_to_string(row.missing_route_count),
        "average_latency_seconds": _decimal_to_string(row.average_latency_seconds),
        "max_latency_seconds": _decimal_to_string(row.max_latency_seconds),
        "min_freshness_score": _decimal_to_string(row.min_freshness_score),
        "min_confidence_score": _decimal_to_string(row.min_confidence_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_payload(row: ResearchStrategyDomainTeamSourceLatencyRouterRow) -> dict[str, Any]:
    payload = _row_digest_payload(row)
    payload["public_payload_digest"] = row.public_payload_digest
    return payload


def _reason_code_count_payload(
    item: ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_to_string(item.count),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _require_report(report: object) -> None:
    if type(report) is not ResearchStrategyDomainTeamSourceLatencyRouterReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainTeamSourceLatencyRouterReport",
        )


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe public label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose private routing surfaces")


def _require_supported_config_version(value: object) -> None:
    if (
        type(value) is not str
        or value
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SOURCE_LATENCY_ROUTER_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must match the supported report version")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError("reason_code must match latency router semantics")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable to 0.000001") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _latency_seconds(observed_at: datetime, routed_at: datetime | None) -> Decimal:
    if routed_at is None:
        return ZERO
    delta = routed_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("latency_seconds", seconds + microseconds)


def _decimal_average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_nonnegative_decimal(
            "average",
            sum(values, ZERO) / _decimal_count(len(values)),
        )


def _decimal_to_string(value: Decimal) -> str:
    return f"{value.quantize(QUANTUM):f}"


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
