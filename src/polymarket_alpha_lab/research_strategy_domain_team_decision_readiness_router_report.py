"""Readonly strategy domain team decision readiness router report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, DecimalException
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION = (
    "research-strategy-domain-team-decision-readiness-router-report-v0"
)

SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EMPTY_REASON = "strategy_domain_team_decision_readiness_empty"
CLEAR_REASON = "strategy_domain_team_decision_readiness_clear"
ALIGNMENT_BLOCK_REASON = (
    "strategy_domain_team_decision_readiness_domain_alignment_block"
)
EVIDENCE_BLOCK_REASON = (
    "strategy_domain_team_decision_readiness_evidence_completeness_block"
)
CAPACITY_BLOCK_REASON = (
    "strategy_domain_team_decision_readiness_review_capacity_block"
)
DEPENDENCY_BLOCK_REASON = (
    "strategy_domain_team_decision_readiness_dependency_block"
)
AGE_BLOCK_REASON = "strategy_domain_team_decision_readiness_age_block"
ALIGNMENT_WATCH_REASON = (
    "strategy_domain_team_decision_readiness_domain_alignment_watch"
)
EVIDENCE_WATCH_REASON = (
    "strategy_domain_team_decision_readiness_evidence_completeness_watch"
)
CAPACITY_WATCH_REASON = (
    "strategy_domain_team_decision_readiness_review_capacity_watch"
)
DEPENDENCY_WATCH_REASON = (
    "strategy_domain_team_decision_readiness_dependency_watch"
)
AGE_WATCH_REASON = "strategy_domain_team_decision_readiness_age_watch"

ROW_REASON_CODES = (
    ALIGNMENT_BLOCK_REASON,
    EVIDENCE_BLOCK_REASON,
    CAPACITY_BLOCK_REASON,
    DEPENDENCY_BLOCK_REASON,
    AGE_BLOCK_REASON,
    ALIGNMENT_WATCH_REASON,
    EVIDENCE_WATCH_REASON,
    CAPACITY_WATCH_REASON,
    DEPENDENCY_WATCH_REASON,
    AGE_WATCH_REASON,
    CLEAR_REASON,
)
REPORT_BLOCK_REASON = (
    "strategy_domain_team_decision_readiness_block_packets_present"
)
REPORT_WATCH_REASON = (
    "strategy_domain_team_decision_readiness_watch_packets_present"
)
REPORT_PASS_REASON = "strategy_domain_team_decision_readiness_pass_packets_present"
REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("cand", "idate"),
    _join_parts("mark", "et"),
    _join_parts("sl", "ug"),
    _join_parts("que", "stion"),
    _join_parts("sou", "rce"),
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "endation"),
    _join_parts("au", "th"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    "://",
    "http",
    "www.",
    "jdbc:",
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyDomainTeamDecisionReadinessRouterConfig",
    "ResearchStrategyDomainTeamDecisionReadinessRouterInput",
    "ResearchStrategyDomainTeamDecisionReadinessRouterReport",
    "ResearchStrategyDomainTeamDecisionReadinessRouterRow",
    "build_research_strategy_domain_team_decision_readiness_router_report",
    "research_strategy_domain_team_decision_readiness_router_report_digest",
    "research_strategy_domain_team_decision_readiness_router_report_payload",
    "validate_research_strategy_domain_team_decision_readiness_router_report_digest",
    "validate_research_strategy_domain_team_decision_readiness_router_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamDecisionReadinessRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION
    )
    domain_alignment_watch_threshold: Decimal = Decimal("0.700000")
    domain_alignment_block_threshold: Decimal = Decimal("0.500000")
    evidence_completeness_watch_threshold: Decimal = Decimal("0.700000")
    evidence_completeness_block_threshold: Decimal = Decimal("0.500000")
    review_capacity_watch_threshold: Decimal = Decimal("0.500000")
    review_capacity_block_threshold: Decimal = Decimal("0.250000")
    open_dependency_watch_count: Decimal = Decimal("1.000000")
    open_dependency_block_count: Decimal = Decimal("3.000000")
    decision_age_watch_seconds: Decimal = Decimal("86400.000000")
    decision_age_block_seconds: Decimal = Decimal("172800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamDecisionReadinessRouterConfig:
            raise TypeError(
                "ResearchStrategyDomainTeamDecisionReadinessRouterConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamDecisionReadinessRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "domain_alignment_watch_threshold",
            "domain_alignment_block_threshold",
            "evidence_completeness_watch_threshold",
            "evidence_completeness_block_threshold",
            "review_capacity_watch_threshold",
            "review_capacity_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_dependency_watch_count",
            "open_dependency_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "decision_age_watch_seconds",
            "decision_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyDomainTeamDecisionReadinessRouterInput:
    packet_digest: str
    domain_label: str
    team_label: str
    observed_at: datetime
    domain_alignment_score: Decimal
    evidence_completeness_score: Decimal
    available_review_capacity_ratio: Decimal
    open_dependency_count: Decimal
    decision_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamDecisionReadinessRouterInput:
            raise TypeError(
                "ResearchStrategyDomainTeamDecisionReadinessRouterInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamDecisionReadinessRouterInput,
            "packet",
        )
        _require_sha256("packet_digest", self.packet_digest)
        object.__setattr__(
            self,
            "domain_label",
            _require_public_string("domain_label", self.domain_label),
        )
        object.__setattr__(
            self,
            "team_label",
            _require_public_string("team_label", self.team_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "domain_alignment_score",
            "evidence_completeness_score",
            "available_review_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_dependency_count",
            _require_nonnegative_decimal(
                "open_dependency_count",
                self.open_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "decision_age_seconds",
            _require_nonnegative_decimal(
                "decision_age_seconds",
                self.decision_age_seconds,
            ),
        )
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyDomainTeamDecisionReadinessRouterRow:
    router_rank: Decimal
    packet_digest: str
    domain_label: str
    team_label: str
    observed_at: datetime
    domain_alignment_score: Decimal
    evidence_completeness_score: Decimal
    available_review_capacity_ratio: Decimal
    open_dependency_count: Decimal
    decision_age_seconds: Decimal
    dependency_pressure_score: Decimal
    age_pressure_score: Decimal
    routing_pressure_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamDecisionReadinessRouterRow:
            raise TypeError(
                "ResearchStrategyDomainTeamDecisionReadinessRouterRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamDecisionReadinessRouterRow,
            "row",
        )
        object.__setattr__(
            self,
            "router_rank",
            _require_positive_decimal("router_rank", self.router_rank),
        )
        _require_sha256("packet_digest", self.packet_digest)
        object.__setattr__(
            self,
            "domain_label",
            _require_public_string("domain_label", self.domain_label),
        )
        object.__setattr__(
            self,
            "team_label",
            _require_public_string("team_label", self.team_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "domain_alignment_score",
            "evidence_completeness_score",
            "available_review_capacity_ratio",
            "dependency_pressure_score",
            "age_pressure_score",
            "routing_pressure_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_dependency_count",
            "decision_age_seconds",
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
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyDomainTeamDecisionReadinessRouterReport:
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    block_packet_count: Decimal
    average_readiness_score: Decimal
    lowest_readiness_score: Decimal
    max_routing_pressure_score: Decimal
    max_decision_age_seconds: Decimal
    max_open_dependency_count: Decimal
    rows: tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamDecisionReadinessRouterReport:
            raise TypeError(
                "ResearchStrategyDomainTeamDecisionReadinessRouterReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamDecisionReadinessRouterReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_DECISION_READINESS_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "block_packet_count",
            "max_decision_age_seconds",
            "max_open_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "lowest_readiness_score",
            "max_routing_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_domain_team_decision_readiness_router_report_payload(
            self,
        )


def build_research_strategy_domain_team_decision_readiness_router_report(
    packets: Iterable[ResearchStrategyDomainTeamDecisionReadinessRouterInput],
    *,
    config: ResearchStrategyDomainTeamDecisionReadinessRouterConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamDecisionReadinessRouterReport:
    cfg = config or ResearchStrategyDomainTeamDecisionReadinessRouterConfig()
    _require_exact_type(
        cfg,
        ResearchStrategyDomainTeamDecisionReadinessRouterConfig,
        "config",
    )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_packets(packets)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    base_rows = tuple(_row_for_packet(packet=item, config=cfg) for item in normalized)
    rows = tuple(
        _ranked_row(index=index, row=row)
        for index, row in enumerate(_sorted_rows(base_rows), start=1)
    )
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "packet_count": _count_decimal(len(rows)),
        "pass_packet_count": _status_count(rows, STATUS_PASS),
        "watch_packet_count": _status_count(rows, STATUS_WATCH),
        "block_packet_count": _status_count(rows, STATUS_BLOCK),
        "average_readiness_score": _average(row.readiness_score for row in rows),
        "lowest_readiness_score": min(
            (row.readiness_score for row in rows),
            default=ZERO,
        ),
        "max_routing_pressure_score": max(
            (row.routing_pressure_score for row in rows),
            default=ZERO,
        ),
        "max_decision_age_seconds": max(
            (row.decision_age_seconds for row in rows),
            default=ZERO,
        ),
        "max_open_dependency_count": max(
            (row.open_dependency_count for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchStrategyDomainTeamDecisionReadinessRouterReport(**values)


def research_strategy_domain_team_decision_readiness_router_report_digest(
    report: ResearchStrategyDomainTeamDecisionReadinessRouterReport | Mapping[str, Any],
) -> str:
    payload = research_strategy_domain_team_decision_readiness_router_report_payload(
        report,
    )
    digest_value = payload["derived_validation_digest"]
    if type(digest_value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest_value


def validate_research_strategy_domain_team_decision_readiness_router_report_digest(
    report: ResearchStrategyDomainTeamDecisionReadinessRouterReport,
) -> bool:
    _require_exact_type(
        report,
        ResearchStrategyDomainTeamDecisionReadinessRouterReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_matching_digest(_payload_value(report))
    return True


def research_strategy_domain_team_decision_readiness_router_report_payload(
    report: ResearchStrategyDomainTeamDecisionReadinessRouterReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainTeamDecisionReadinessRouterReport:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
    elif isinstance(report, Mapping):
        payload = dict(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchStrategyDomainTeamDecisionReadinessRouterReport",
        )
    return _validated_public_payload(payload)


def validate_research_strategy_domain_team_decision_readiness_router_report_payload(
    payload: dict[str, Any],
) -> bool:
    _validated_public_payload(payload)
    return True


def _validated_public_payload(payload: object) -> dict[str, Any]:
    try:
        if type(payload) is not dict:
            raise ValueError("must be a dict")
        _reject_unsafe_public_payload("public payload", payload)
        _require_payload_hard_flags(payload)
        report = _report_from_public_payload(payload)
        canonical_payload = _payload_value(report)
        if type(canonical_payload) is not dict:
            raise ValueError("must be a dict")
        if payload != canonical_payload:
            raise ValueError("must use canonical values")
        return canonical_payload
    except (DecimalException, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"public payload is invalid: {exc}") from exc


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainTeamDecisionReadinessRouterReport:
    _require_public_schema(
        "public payload",
        payload,
        ResearchStrategyDomainTeamDecisionReadinessRouterReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    reason_codes_value = payload["reason_codes"]
    if type(reason_codes_value) is not list:
        raise ValueError("reason_codes must be a list")
    return ResearchStrategyDomainTeamDecisionReadinessRouterReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_public_string(
            "config_version",
            payload["config_version"],
        ),
        status=_require_status("status", payload["status"]),
        packet_count=_public_nonnegative_decimal(
            "packet_count",
            payload["packet_count"],
        ),
        pass_packet_count=_public_nonnegative_decimal(
            "pass_packet_count",
            payload["pass_packet_count"],
        ),
        watch_packet_count=_public_nonnegative_decimal(
            "watch_packet_count",
            payload["watch_packet_count"],
        ),
        block_packet_count=_public_nonnegative_decimal(
            "block_packet_count",
            payload["block_packet_count"],
        ),
        average_readiness_score=_public_ratio_decimal(
            "average_readiness_score",
            payload["average_readiness_score"],
        ),
        lowest_readiness_score=_public_ratio_decimal(
            "lowest_readiness_score",
            payload["lowest_readiness_score"],
        ),
        max_routing_pressure_score=_public_ratio_decimal(
            "max_routing_pressure_score",
            payload["max_routing_pressure_score"],
        ),
        max_decision_age_seconds=_public_nonnegative_decimal(
            "max_decision_age_seconds",
            payload["max_decision_age_seconds"],
        ),
        max_open_dependency_count=_public_nonnegative_decimal(
            "max_open_dependency_count",
            payload["max_open_dependency_count"],
        ),
        rows=rows,
        reason_codes=_require_reason_codes(
            "reason_codes",
            tuple(reason_codes_value),
            REPORT_REASON_CODES,
        ),
        derived_validation_digest=_require_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchStrategyDomainTeamDecisionReadinessRouterRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain dict values")
    _require_public_schema(
        "public payload row",
        payload,
        ResearchStrategyDomainTeamDecisionReadinessRouterRow,
    )
    reason_codes_value = payload["reason_codes"]
    if type(reason_codes_value) is not list:
        raise ValueError("row reason_codes must be a list")
    return ResearchStrategyDomainTeamDecisionReadinessRouterRow(
        router_rank=_public_positive_decimal(
            "router_rank",
            payload["router_rank"],
        ),
        packet_digest=_require_sha256("packet_digest", payload["packet_digest"]),
        domain_label=_require_public_string(
            "domain_label",
            payload["domain_label"],
        ),
        team_label=_require_public_string("team_label", payload["team_label"]),
        observed_at=_public_datetime("observed_at", payload["observed_at"]),
        domain_alignment_score=_public_ratio_decimal(
            "domain_alignment_score",
            payload["domain_alignment_score"],
        ),
        evidence_completeness_score=_public_ratio_decimal(
            "evidence_completeness_score",
            payload["evidence_completeness_score"],
        ),
        available_review_capacity_ratio=_public_ratio_decimal(
            "available_review_capacity_ratio",
            payload["available_review_capacity_ratio"],
        ),
        open_dependency_count=_public_nonnegative_decimal(
            "open_dependency_count",
            payload["open_dependency_count"],
        ),
        decision_age_seconds=_public_nonnegative_decimal(
            "decision_age_seconds",
            payload["decision_age_seconds"],
        ),
        dependency_pressure_score=_public_ratio_decimal(
            "dependency_pressure_score",
            payload["dependency_pressure_score"],
        ),
        age_pressure_score=_public_ratio_decimal(
            "age_pressure_score",
            payload["age_pressure_score"],
        ),
        routing_pressure_score=_public_ratio_decimal(
            "routing_pressure_score",
            payload["routing_pressure_score"],
        ),
        readiness_score=_public_ratio_decimal(
            "readiness_score",
            payload["readiness_score"],
        ),
        status=_require_status("status", payload["status"]),
        reason_codes=_require_reason_codes(
            "reason_codes",
            tuple(reason_codes_value),
            ROW_REASON_CODES,
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _require_public_schema(
    name: str,
    payload: dict[str, Any],
    schema_type: type[object],
) -> None:
    expected_fields = frozenset(field.name for field in fields(schema_type))
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{name} fields must exactly match schema")


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _public_ratio_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, decimal_kind="ratio")


def _public_nonnegative_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, decimal_kind="nonnegative")


def _public_positive_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, decimal_kind="positive")


def _public_decimal(
    name: str,
    value: object,
    *,
    decimal_kind: str,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
        if decimal_kind == "ratio":
            normalized = _require_ratio_decimal(name, parsed)
        elif decimal_kind == "nonnegative":
            normalized = _require_nonnegative_decimal(name, parsed)
        elif decimal_kind == "positive":
            normalized = _require_positive_decimal(name, parsed)
        else:
            raise ValueError("decimal kind must be supported")
    except (DecimalException, ValueError) as exc:
        raise ValueError(f"{name} must be a canonical Decimal string") from exc
    if format(normalized, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _public_true(name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{name} must be True")
    return True


def _row_for_packet(
    *,
    packet: ResearchStrategyDomainTeamDecisionReadinessRouterInput,
    config: ResearchStrategyDomainTeamDecisionReadinessRouterConfig,
) -> ResearchStrategyDomainTeamDecisionReadinessRouterRow:
    dependency_pressure_score = _ratio_to_cap(
        packet.open_dependency_count,
        config.open_dependency_block_count,
    )
    age_pressure_score = _ratio_to_cap(
        packet.decision_age_seconds,
        config.decision_age_block_seconds,
    )
    routing_pressure_score = max(
        ONE - packet.domain_alignment_score,
        ONE - packet.evidence_completeness_score,
        ONE - packet.available_review_capacity_ratio,
        dependency_pressure_score,
        age_pressure_score,
    ).quantize(SIX)
    reason_codes = _row_reason_codes(
        domain_alignment_score=packet.domain_alignment_score,
        evidence_completeness_score=packet.evidence_completeness_score,
        available_review_capacity_ratio=packet.available_review_capacity_ratio,
        open_dependency_count=packet.open_dependency_count,
        decision_age_seconds=packet.decision_age_seconds,
        config=config,
    )
    return ResearchStrategyDomainTeamDecisionReadinessRouterRow(
        router_rank=ONE,
        packet_digest=packet.packet_digest,
        domain_label=packet.domain_label,
        team_label=packet.team_label,
        observed_at=packet.observed_at,
        domain_alignment_score=packet.domain_alignment_score,
        evidence_completeness_score=packet.evidence_completeness_score,
        available_review_capacity_ratio=packet.available_review_capacity_ratio,
        open_dependency_count=packet.open_dependency_count,
        decision_age_seconds=packet.decision_age_seconds,
        dependency_pressure_score=dependency_pressure_score,
        age_pressure_score=age_pressure_score,
        routing_pressure_score=routing_pressure_score,
        readiness_score=(ONE - routing_pressure_score).quantize(SIX),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _ranked_row(
    *,
    index: int,
    row: ResearchStrategyDomainTeamDecisionReadinessRouterRow,
) -> ResearchStrategyDomainTeamDecisionReadinessRouterRow:
    return ResearchStrategyDomainTeamDecisionReadinessRouterRow(
        router_rank=_count_decimal(index),
        packet_digest=row.packet_digest,
        domain_label=row.domain_label,
        team_label=row.team_label,
        observed_at=row.observed_at,
        domain_alignment_score=row.domain_alignment_score,
        evidence_completeness_score=row.evidence_completeness_score,
        available_review_capacity_ratio=row.available_review_capacity_ratio,
        open_dependency_count=row.open_dependency_count,
        decision_age_seconds=row.decision_age_seconds,
        dependency_pressure_score=row.dependency_pressure_score,
        age_pressure_score=row.age_pressure_score,
        routing_pressure_score=row.routing_pressure_score,
        readiness_score=row.readiness_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    domain_alignment_score: Decimal,
    evidence_completeness_score: Decimal,
    available_review_capacity_ratio: Decimal,
    open_dependency_count: Decimal,
    decision_age_seconds: Decimal,
    config: ResearchStrategyDomainTeamDecisionReadinessRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if domain_alignment_score < config.domain_alignment_block_threshold:
        reason_codes.append(ALIGNMENT_BLOCK_REASON)
    if evidence_completeness_score < config.evidence_completeness_block_threshold:
        reason_codes.append(EVIDENCE_BLOCK_REASON)
    if available_review_capacity_ratio < config.review_capacity_block_threshold:
        reason_codes.append(CAPACITY_BLOCK_REASON)
    if open_dependency_count >= config.open_dependency_block_count:
        reason_codes.append(DEPENDENCY_BLOCK_REASON)
    if decision_age_seconds >= config.decision_age_block_seconds:
        reason_codes.append(AGE_BLOCK_REASON)
    if reason_codes:
        return _require_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)
    if domain_alignment_score < config.domain_alignment_watch_threshold:
        reason_codes.append(ALIGNMENT_WATCH_REASON)
    if evidence_completeness_score < config.evidence_completeness_watch_threshold:
        reason_codes.append(EVIDENCE_WATCH_REASON)
    if available_review_capacity_ratio < config.review_capacity_watch_threshold:
        reason_codes.append(CAPACITY_WATCH_REASON)
    if open_dependency_count >= config.open_dependency_watch_count:
        reason_codes.append(DEPENDENCY_WATCH_REASON)
    if decision_age_seconds >= config.decision_age_watch_seconds:
        reason_codes.append(AGE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _require_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_REASON)
    if any(row.status == STATUS_PASS for row in rows):
        reason_codes.append(REPORT_PASS_REASON)
    return _require_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _normalize_packets(
    packets: Iterable[ResearchStrategyDomainTeamDecisionReadinessRouterInput],
) -> tuple[ResearchStrategyDomainTeamDecisionReadinessRouterInput, ...]:
    if isinstance(packets, (str, bytes)):
        raise ValueError("packets must be an iterable of packet values")
    try:
        normalized = tuple(packets)
    except TypeError as exc:
        raise ValueError("packets must be an iterable of packet values") from exc
    seen: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchStrategyDomainTeamDecisionReadinessRouterInput,
            "packet",
        )
        _require_hard_flags("packet", item)
        if item.packet_digest in seen:
            raise ValueError("packet_digest values must be unique")
        seen.add(item.packet_digest)
    return normalized


def _require_rows(
    rows: object,
) -> tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for index, row in enumerate(normalized, start=1):
        _require_exact_type(
            row,
            ResearchStrategyDomainTeamDecisionReadinessRouterRow,
            "row",
        )
        _require_hard_flags("row", row)
        if row.packet_digest in seen:
            raise ValueError("packet_digest values must be unique")
        seen.add(row.packet_digest)
        if row.router_rank != _count_decimal(index):
            raise ValueError("router_rank values must be sequential")
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be sorted by router pressure")
    return normalized


def _sorted_rows(
    rows: tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...],
) -> tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                -row.routing_pressure_score,
                -row.decision_age_seconds,
                -row.open_dependency_count,
                row.packet_digest,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    if status == STATUS_PASS:
        return 2
    raise ValueError("status must be one of pass, watch, block")


def _status_count(
    rows: tuple[ResearchStrategyDomainTeamDecisionReadinessRouterRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _six(sum(items, ZERO) / Decimal(len(items)))


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= ZERO:
        raise ValueError("cap must be positive")
    return _clamp_ratio(value / cap)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value.quantize(SIX)


def _validate_config(
    config: ResearchStrategyDomainTeamDecisionReadinessRouterConfig,
) -> None:
    if config.domain_alignment_block_threshold > config.domain_alignment_watch_threshold:
        raise ValueError(
            "domain_alignment_block_threshold must not exceed "
            "domain_alignment_watch_threshold",
        )
    if (
        config.evidence_completeness_block_threshold
        > config.evidence_completeness_watch_threshold
    ):
        raise ValueError(
            "evidence_completeness_block_threshold must not exceed "
            "evidence_completeness_watch_threshold",
        )
    if config.review_capacity_block_threshold > config.review_capacity_watch_threshold:
        raise ValueError(
            "review_capacity_block_threshold must not exceed "
            "review_capacity_watch_threshold",
        )
    if config.open_dependency_watch_count > config.open_dependency_block_count:
        raise ValueError("dependency_count thresholds must be increasing")
    if config.decision_age_watch_seconds > config.decision_age_block_seconds:
        raise ValueError("decision_age thresholds must be increasing")


def _validate_row(
    row: ResearchStrategyDomainTeamDecisionReadinessRouterRow,
) -> None:
    if row.dependency_pressure_score != _clamp_ratio(row.dependency_pressure_score):
        raise ValueError("dependency_pressure_score must be a ratio")
    if row.age_pressure_score != _clamp_ratio(row.age_pressure_score):
        raise ValueError("age_pressure_score must be a ratio")
    expected_pressure = max(
        ONE - row.domain_alignment_score,
        ONE - row.evidence_completeness_score,
        ONE - row.available_review_capacity_ratio,
        row.dependency_pressure_score,
        row.age_pressure_score,
    ).quantize(SIX)
    if row.routing_pressure_score != expected_pressure:
        raise ValueError("routing_pressure_score must match component values")
    if row.readiness_score != (ONE - row.routing_pressure_score).quantize(SIX):
        raise ValueError("readiness_score must match routing pressure")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchStrategyDomainTeamDecisionReadinessRouterReport,
) -> None:
    rows = report.rows
    _require_decimal_equal("packet_count", report.packet_count, _count_decimal(len(rows)))
    _require_decimal_equal(
        "pass_packet_count",
        report.pass_packet_count,
        _status_count(rows, STATUS_PASS),
    )
    _require_decimal_equal(
        "watch_packet_count",
        report.watch_packet_count,
        _status_count(rows, STATUS_WATCH),
    )
    _require_decimal_equal(
        "block_packet_count",
        report.block_packet_count,
        _status_count(rows, STATUS_BLOCK),
    )
    _require_decimal_equal(
        "average_readiness_score",
        report.average_readiness_score,
        _average(row.readiness_score for row in rows),
    )
    _require_decimal_equal(
        "lowest_readiness_score",
        report.lowest_readiness_score,
        min((row.readiness_score for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "max_routing_pressure_score",
        report.max_routing_pressure_score,
        max((row.routing_pressure_score for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "max_decision_age_seconds",
        report.max_decision_age_seconds,
        max((row.decision_age_seconds for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "max_open_dependency_count",
        report.max_open_dependency_count,
        max((row.open_dependency_count for row in rows), default=ZERO),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {field.name: getattr(value, field.name) for field in fields(value)}
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _require_safe_public_value("public payload value", value)
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_value("public payload key", key)
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_value(f"{name} key", key)
            _reject_unsafe_public_payload(f"{name}.{key}", item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(name, item)
        return
    if type(value) is str:
        _require_safe_public_value(name, value)
        return
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    raise ValueError("public payload contains unsupported value")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload {flag_name} must be True")
    rows = payload.get("rows", [])
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must be dicts")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"payload row {flag_name} must be True")


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")
    return value


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    _require_safe_public_value(name, value)
    return value


def _require_safe_public_value(name: str, value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _require_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 digest")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    known_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must contain at least one value")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in known_codes:
            raise ValueError(f"{name} must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must be unique")
    expected = tuple(code for code in known_codes if code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{name} must be deterministic")
    return reason_codes


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value.quantize(SIX)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value.quantize(SIX)


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value.quantize(SIX)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != expected.quantize(SIX):
        raise ValueError(f"{name} must match rows")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


ZERO_TIME_OFFSET = datetime(1970, 1, 1, tzinfo=UTC).utcoffset()


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
