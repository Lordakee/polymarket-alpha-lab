"""Pure aggregate router report for domain team memory readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_DOMAIN_TEAM_MEMORY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-domain-team-memory-router-report-v0"
)
STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "research_domain_team_memory_router_memory_freshness_block",
    "research_domain_team_memory_router_review_load_block",
    "research_domain_team_memory_router_evidence_gap_block",
    "research_domain_team_memory_router_escalation_fit_block",
    "research_domain_team_memory_router_memory_freshness_watch",
    "research_domain_team_memory_router_review_load_watch",
    "research_domain_team_memory_router_evidence_gap_watch",
    "research_domain_team_memory_router_escalation_fit_watch",
    "research_domain_team_memory_router_ready",
)
REPORT_REASON_CODES = (
    "research_domain_team_memory_router_block_domains_present",
    "research_domain_team_memory_router_watch_domains_present",
    "research_domain_team_memory_router_ready",
    "research_domain_team_memory_router_empty",
)
ZERO = Decimal("0")
ONE = Decimal("1")
QUANT = Decimal("0.000001")
DIGEST_HEX_LENGTH = 64
UNSAFE_PUBLIC_FRAGMENTS = (
    "acc" "ount",
    "au" "th",
    "b" "uy",
    "bro" "ker",
    "can" "cel",
    "cre" "dential",
    "data" "base",
    "env" "iron",
    "li" "ve",
    "net" "work",
    "or" "der",
    "post" "gres",
    "pri" "vate_key",
    "req" "uest",
    "se" "cret",
    "se" "ll",
    "soc" "ket",
    "s" "qlite",
    "sub" "mit",
    "supa" "base",
    "tr" "ade",
    "wa" "llet",
)


@dataclass(frozen=True)
class ResearchDomainTeamMemoryRouterReportConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_TEAM_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    memory_freshness_watch_threshold: Decimal = Decimal("0.750000")
    memory_freshness_block_threshold: Decimal = Decimal("0.600000")
    review_load_watch_threshold: Decimal = Decimal("0.750000")
    review_load_block_threshold: Decimal = Decimal("1.000000")
    evidence_gap_watch_threshold: Decimal = Decimal("0.250000")
    evidence_gap_block_threshold: Decimal = Decimal("0.500000")
    escalation_fit_watch_threshold: Decimal = Decimal("0.750000")
    escalation_fit_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamMemoryRouterReportConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "memory_freshness_watch_threshold",
            "memory_freshness_block_threshold",
            "review_load_watch_threshold",
            "review_load_block_threshold",
            "evidence_gap_watch_threshold",
            "evidence_gap_block_threshold",
            "escalation_fit_watch_threshold",
            "escalation_fit_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.memory_freshness_block_threshold > self.memory_freshness_watch_threshold:
            raise ValueError(
                "memory_freshness_block_threshold must not exceed "
                "memory_freshness_watch_threshold",
            )
        if self.review_load_watch_threshold > self.review_load_block_threshold:
            raise ValueError(
                "review_load_watch_threshold must not exceed "
                "review_load_block_threshold",
            )
        if self.evidence_gap_watch_threshold > self.evidence_gap_block_threshold:
            raise ValueError(
                "evidence_gap_watch_threshold must not exceed "
                "evidence_gap_block_threshold",
            )
        if self.escalation_fit_block_threshold > self.escalation_fit_watch_threshold:
            raise ValueError(
                "escalation_fit_block_threshold must not exceed "
                "escalation_fit_watch_threshold",
            )
        require_paper_only_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainTeamMemoryRouterDomainInput:
    domain_label: str
    memory_fresh_team_count: Decimal
    memory_team_count: Decimal
    review_queue_count: Decimal
    review_capacity_count: Decimal
    evidence_gap_count: Decimal
    evidence_target_count: Decimal
    escalation_fit_count: Decimal
    escalation_candidate_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamMemoryRouterDomainInput, "domain_input")
        _require_public_string("domain_label", self.domain_label)
        for field_name in (
            "memory_fresh_team_count",
            "memory_team_count",
            "review_queue_count",
            "review_capacity_count",
            "evidence_gap_count",
            "evidence_target_count",
            "escalation_fit_count",
            "escalation_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_team_count",
            "review_capacity_count",
            "evidence_target_count",
            "escalation_candidate_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        _validate_count_bounds(self)
        require_paper_only_flags("domain_input", self)
        _reject_unsafe_public_payload("domain_input", self)


@dataclass(frozen=True)
class ResearchDomainTeamMemoryRouterDomainRow:
    domain_label: str
    memory_fresh_team_count: Decimal
    memory_team_count: Decimal
    memory_freshness_ratio: Decimal
    review_queue_count: Decimal
    review_capacity_count: Decimal
    review_load_ratio: Decimal
    evidence_gap_count: Decimal
    evidence_target_count: Decimal
    evidence_gap_pressure: Decimal
    escalation_fit_count: Decimal
    escalation_candidate_count: Decimal
    escalation_fit_ratio: Decimal
    readiness_score: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamMemoryRouterDomainRow, "row")
        _require_public_string("domain_label", self.domain_label)
        for field_name in (
            "memory_fresh_team_count",
            "memory_team_count",
            "review_queue_count",
            "review_capacity_count",
            "evidence_gap_count",
            "evidence_target_count",
            "escalation_fit_count",
            "escalation_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_team_count",
            "review_capacity_count",
            "evidence_target_count",
            "escalation_candidate_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "memory_freshness_ratio",
            "review_load_ratio",
            "evidence_gap_pressure",
            "escalation_fit_ratio",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("router_status", self.router_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_count_bounds(self)
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainTeamMemoryRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainTeamMemoryRouterReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        require_paper_only_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainTeamMemoryRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    average_readiness_score: Decimal
    lowest_readiness_score: Decimal
    lowest_memory_freshness_ratio: Decimal
    max_review_load_ratio: Decimal
    max_evidence_gap_pressure: Decimal
    lowest_escalation_fit_ratio: Decimal
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...]
    reason_code_counts: tuple[ResearchDomainTeamMemoryRouterReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("router_status", self.router_status)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "lowest_readiness_score",
            "lowest_memory_freshness_ratio",
            "max_review_load_ratio",
            "max_evidence_gap_pressure",
            "lowest_escalation_fit_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_domain_team_memory_router_report(
    domain_inputs: list[ResearchDomainTeamMemoryRouterDomainInput]
    | tuple[ResearchDomainTeamMemoryRouterDomainInput, ...],
    *,
    config: ResearchDomainTeamMemoryRouterReportConfig,
    generated_at: datetime,
) -> ResearchDomainTeamMemoryRouterReport:
    if type(config) is not ResearchDomainTeamMemoryRouterReportConfig:
        raise ValueError("config must be a ResearchDomainTeamMemoryRouterReportConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_domain_inputs(domain_inputs)
    rows = tuple(_row_for_domain(domain_input, config) for domain_input in inputs)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "router_status": _status_from_report_reason_codes(reason_codes),
        "domain_count": _decimal_count(len(rows)),
        "pass_domain_count": _status_count(rows, "pass"),
        "watch_domain_count": _status_count(rows, "watch"),
        "block_domain_count": _status_count(rows, "block"),
        "average_readiness_score": _average(rows, "readiness_score"),
        "lowest_readiness_score": _minimum(rows, "readiness_score"),
        "lowest_memory_freshness_ratio": _minimum(rows, "memory_freshness_ratio"),
        "max_review_load_ratio": _maximum(rows, "review_load_ratio"),
        "max_evidence_gap_pressure": _maximum(rows, "evidence_gap_pressure"),
        "lowest_escalation_fit_ratio": _minimum(rows, "escalation_fit_ratio"),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainTeamMemoryRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_domain_team_memory_router_report_payload(
    report: ResearchDomainTeamMemoryRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainTeamMemoryRouterReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchDomainTeamMemoryRouterReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_for_domain(
    domain_input: ResearchDomainTeamMemoryRouterDomainInput,
    config: ResearchDomainTeamMemoryRouterReportConfig,
) -> ResearchDomainTeamMemoryRouterDomainRow:
    memory_freshness_ratio = _ratio(
        domain_input.memory_fresh_team_count,
        domain_input.memory_team_count,
    )
    review_load_ratio = _ratio(
        domain_input.review_queue_count,
        domain_input.review_capacity_count,
    )
    evidence_gap_pressure = _ratio(
        domain_input.evidence_gap_count,
        domain_input.evidence_target_count,
    )
    escalation_fit_ratio = _ratio(
        domain_input.escalation_fit_count,
        domain_input.escalation_candidate_count,
    )
    readiness_score = (
        memory_freshness_ratio
        + (ONE - review_load_ratio)
        + (ONE - evidence_gap_pressure)
        + escalation_fit_ratio
    ) / Decimal("4")
    reason_codes = _row_reason_codes(
        memory_freshness_ratio=memory_freshness_ratio,
        review_load_ratio=review_load_ratio,
        evidence_gap_pressure=evidence_gap_pressure,
        escalation_fit_ratio=escalation_fit_ratio,
        config=config,
    )
    return ResearchDomainTeamMemoryRouterDomainRow(
        domain_label=domain_input.domain_label,
        memory_fresh_team_count=domain_input.memory_fresh_team_count,
        memory_team_count=domain_input.memory_team_count,
        memory_freshness_ratio=memory_freshness_ratio,
        review_queue_count=domain_input.review_queue_count,
        review_capacity_count=domain_input.review_capacity_count,
        review_load_ratio=review_load_ratio,
        evidence_gap_count=domain_input.evidence_gap_count,
        evidence_target_count=domain_input.evidence_target_count,
        evidence_gap_pressure=evidence_gap_pressure,
        escalation_fit_count=domain_input.escalation_fit_count,
        escalation_candidate_count=domain_input.escalation_candidate_count,
        escalation_fit_ratio=escalation_fit_ratio,
        readiness_score=readiness_score.quantize(QUANT),
        router_status=_status_from_row_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_freshness_ratio: Decimal,
    review_load_ratio: Decimal,
    evidence_gap_pressure: Decimal,
    escalation_fit_ratio: Decimal,
    config: ResearchDomainTeamMemoryRouterReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_freshness_ratio < config.memory_freshness_block_threshold:
        reason_codes.append("research_domain_team_memory_router_memory_freshness_block")
    if review_load_ratio >= config.review_load_block_threshold:
        reason_codes.append("research_domain_team_memory_router_review_load_block")
    if evidence_gap_pressure >= config.evidence_gap_block_threshold:
        reason_codes.append("research_domain_team_memory_router_evidence_gap_block")
    if escalation_fit_ratio < config.escalation_fit_block_threshold:
        reason_codes.append("research_domain_team_memory_router_escalation_fit_block")
    if reason_codes:
        return tuple(reason_codes)
    if memory_freshness_ratio < config.memory_freshness_watch_threshold:
        reason_codes.append("research_domain_team_memory_router_memory_freshness_watch")
    if review_load_ratio >= config.review_load_watch_threshold:
        reason_codes.append("research_domain_team_memory_router_review_load_watch")
    if evidence_gap_pressure >= config.evidence_gap_watch_threshold:
        reason_codes.append("research_domain_team_memory_router_evidence_gap_watch")
    if escalation_fit_ratio < config.escalation_fit_watch_threshold:
        reason_codes.append("research_domain_team_memory_router_escalation_fit_watch")
    if reason_codes:
        return tuple(reason_codes)
    return ("research_domain_team_memory_router_ready",)


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_domain_team_memory_router_empty",)
    reason_codes: list[str] = []
    if any(row.router_status == "block" for row in rows):
        reason_codes.append("research_domain_team_memory_router_block_domains_present")
    if any(row.router_status == "watch" for row in rows):
        reason_codes.append("research_domain_team_memory_router_watch_domains_present")
    if not reason_codes:
        reason_codes.append("research_domain_team_memory_router_ready")
    return tuple(reason_codes)


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_report_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "research_domain_team_memory_router_block_domains_present" in reason_codes
        or "research_domain_team_memory_router_empty" in reason_codes
    ):
        return "block"
    if "research_domain_team_memory_router_watch_domains_present" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
) -> tuple[ResearchDomainTeamMemoryRouterReasonCodeCount, ...]:
    all_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchDomainTeamMemoryRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(all_reason_codes.count(reason_code)),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in all_reason_codes
    )


def _normalize_domain_inputs(
    value: object,
) -> tuple[ResearchDomainTeamMemoryRouterDomainInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("domain_inputs must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainTeamMemoryRouterDomainInput:
            raise ValueError("domain_inputs must contain domain input values")
        require_paper_only_flags("domain_input", row)
        if row.domain_label in seen_labels:
            raise ValueError("domain_label values must be unique")
        seen_labels.add(row.domain_label)
    return tuple(sorted(rows, key=lambda row: row.domain_label))


def _normalize_rows(
    value: object,
) -> tuple[ResearchDomainTeamMemoryRouterDomainRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainTeamMemoryRouterDomainRow:
            raise ValueError("rows must contain domain row values")
        require_paper_only_flags("row", row)
        if row.domain_label in seen_labels:
            raise ValueError("domain_label values must be unique")
        seen_labels.add(row.domain_label)
    return tuple(sorted(rows, key=lambda row: row.domain_label))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchDomainTeamMemoryRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen_reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainTeamMemoryRouterReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
        require_paper_only_flags("reason_code_count", row)
    expected = tuple(row for code in ROW_REASON_CODES for row in rows if row.reason_code == code)
    if rows != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in known_reason_codes if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_count_bounds(
    value: ResearchDomainTeamMemoryRouterDomainInput
    | ResearchDomainTeamMemoryRouterDomainRow,
) -> None:
    if value.memory_fresh_team_count > value.memory_team_count:
        raise ValueError("memory_fresh_team_count must not exceed memory_team_count")
    if value.review_queue_count > value.review_capacity_count:
        raise ValueError("review_queue_count must not exceed review_capacity_count")
    if value.evidence_gap_count > value.evidence_target_count:
        raise ValueError("evidence_gap_count must not exceed evidence_target_count")
    if value.escalation_fit_count > value.escalation_candidate_count:
        raise ValueError(
            "escalation_fit_count must not exceed escalation_candidate_count",
        )


def _validate_row_consistency(row: ResearchDomainTeamMemoryRouterDomainRow) -> None:
    if row.memory_freshness_ratio != _ratio(
        row.memory_fresh_team_count,
        row.memory_team_count,
    ):
        raise ValueError("memory_freshness_ratio must match counts")
    if row.review_load_ratio != _ratio(row.review_queue_count, row.review_capacity_count):
        raise ValueError("review_load_ratio must match counts")
    if row.evidence_gap_pressure != _ratio(row.evidence_gap_count, row.evidence_target_count):
        raise ValueError("evidence_gap_pressure must match counts")
    if row.escalation_fit_ratio != _ratio(
        row.escalation_fit_count,
        row.escalation_candidate_count,
    ):
        raise ValueError("escalation_fit_ratio must match counts")
    expected_score = (
        row.memory_freshness_ratio
        + (ONE - row.review_load_ratio)
        + (ONE - row.evidence_gap_pressure)
        + row.escalation_fit_ratio
    ) / Decimal("4")
    if row.readiness_score != expected_score.quantize(QUANT):
        raise ValueError("readiness_score must match component ratios")
    if row.router_status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("router_status must match reason_codes")


def _validate_report_consistency(report: ResearchDomainTeamMemoryRouterReport) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_domain_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _status_count(report.rows, "block"):
        raise ValueError("block_domain_count must match rows")
    if report.average_readiness_score != _average(report.rows, "readiness_score"):
        raise ValueError("average_readiness_score must match rows")
    if report.lowest_readiness_score != _minimum(report.rows, "readiness_score"):
        raise ValueError("lowest_readiness_score must match rows")
    if report.lowest_memory_freshness_ratio != _minimum(
        report.rows,
        "memory_freshness_ratio",
    ):
        raise ValueError("lowest_memory_freshness_ratio must match rows")
    if report.max_review_load_ratio != _maximum(report.rows, "review_load_ratio"):
        raise ValueError("max_review_load_ratio must match rows")
    if report.max_evidence_gap_pressure != _maximum(report.rows, "evidence_gap_pressure"):
        raise ValueError("max_evidence_gap_pressure must match rows")
    if report.lowest_escalation_fit_ratio != _minimum(report.rows, "escalation_fit_ratio"):
        raise ValueError("lowest_escalation_fit_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.router_status != _status_from_report_reason_codes(report.reason_codes):
        raise ValueError("router_status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


@dataclass(frozen=True)
class _DictFlags:
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


def _status_count(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.router_status == status))


def _average(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return (
        sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows))
    ).quantize(QUANT)


def _minimum(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return min(getattr(row, field_name) for row in rows).quantize(QUANT)


def _maximum(
    rows: tuple[ResearchDomainTeamMemoryRouterDomainRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return max(getattr(row, field_name) for row in rows).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return (numerator / denominator).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} must be public")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _report_values_without_digest(
    report: ResearchDomainTeamMemoryRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest_payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(QUANT))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _require_public_string(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_public_string(item_path, key)
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
    "ResearchDomainTeamMemoryRouterReportConfig",
    "ResearchDomainTeamMemoryRouterDomainInput",
    "ResearchDomainTeamMemoryRouterDomainRow",
    "ResearchDomainTeamMemoryRouterReasonCodeCount",
    "ResearchDomainTeamMemoryRouterReport",
    "build_research_domain_team_memory_router_report",
    "research_domain_team_memory_router_report_payload",
)
