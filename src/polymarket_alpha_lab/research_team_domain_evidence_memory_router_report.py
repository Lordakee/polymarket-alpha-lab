"""Pure report for routing team/domain evidence-memory readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-team-domain-evidence-memory-router-report-v0"
)
STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "research_team_domain_evidence_memory_router_memory_match_block",
    "research_team_domain_evidence_memory_router_independence_block",
    "research_team_domain_evidence_memory_router_stale_memory_block",
    "research_team_domain_evidence_memory_router_conflict_pressure_block",
    "research_team_domain_evidence_memory_router_memory_match_watch",
    "research_team_domain_evidence_memory_router_independence_watch",
    "research_team_domain_evidence_memory_router_stale_memory_watch",
    "research_team_domain_evidence_memory_router_conflict_pressure_watch",
    "research_team_domain_evidence_memory_router_ready",
)
REPORT_REASON_CODES = (
    "research_team_domain_evidence_memory_router_block_routes_present",
    "research_team_domain_evidence_memory_router_watch_routes_present",
    "research_team_domain_evidence_memory_router_ready",
    "research_team_domain_evidence_memory_router_empty",
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
    "can" "didate",
    "cre" "dential",
    "data" "base",
    "ds" "n",
    "env" "iron",
    "li" "ve",
    "mark" "et",
    "net" "work",
    "or" "der",
    "post" "gres",
    "pri" "vate_key",
    "ques" "tion",
    "rec" "ommendation",
    "req" "uest",
    "se" "cret",
    "se" "ll",
    "si" "zing",
    "s" "lug",
    "soc" "ket",
    "sou" "rce",
    "s" "qlite",
    "sub" "mit",
    "supa" "base",
    "ta" "ble",
    "tok" "en",
    "tr" "ade",
    "url",
    "wa" "llet",
)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryRouterReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    )
    memory_match_watch_threshold: Decimal = Decimal("0.800000")
    memory_match_block_threshold: Decimal = Decimal("0.600000")
    independence_watch_threshold: Decimal = Decimal("0.750000")
    independence_block_threshold: Decimal = Decimal("0.500000")
    stale_memory_watch_threshold: Decimal = Decimal("0.250000")
    stale_memory_block_threshold: Decimal = Decimal("0.500000")
    conflict_pressure_watch_threshold: Decimal = Decimal("0.250000")
    conflict_pressure_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainEvidenceMemoryRouterReportConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "memory_match_watch_threshold",
            "memory_match_block_threshold",
            "independence_watch_threshold",
            "independence_block_threshold",
            "stale_memory_watch_threshold",
            "stale_memory_block_threshold",
            "conflict_pressure_watch_threshold",
            "conflict_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.memory_match_block_threshold > self.memory_match_watch_threshold:
            raise ValueError(
                "memory_match_block_threshold must not exceed "
                "memory_match_watch_threshold",
            )
        if self.independence_block_threshold > self.independence_watch_threshold:
            raise ValueError(
                "independence_block_threshold must not exceed "
                "independence_watch_threshold",
            )
        if self.stale_memory_watch_threshold > self.stale_memory_block_threshold:
            raise ValueError(
                "stale_memory_watch_threshold must not exceed "
                "stale_memory_block_threshold",
            )
        if self.conflict_pressure_watch_threshold > self.conflict_pressure_block_threshold:
            raise ValueError(
                "conflict_pressure_watch_threshold must not exceed "
                "conflict_pressure_block_threshold",
            )
        require_paper_only_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryRouterInput:
    domain_label: str
    team_label: str
    memory_match_count: Decimal
    evidence_item_count: Decimal
    independent_evidence_count: Decimal
    required_independent_evidence_count: Decimal
    stale_memory_count: Decimal
    memory_item_count: Decimal
    unresolved_conflict_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainEvidenceMemoryRouterInput, "input")
        _require_public_string("domain_label", self.domain_label)
        _require_public_string("team_label", self.team_label)
        for field_name in (
            "memory_match_count",
            "evidence_item_count",
            "independent_evidence_count",
            "required_independent_evidence_count",
            "stale_memory_count",
            "memory_item_count",
            "unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "required_independent_evidence_count",
            "memory_item_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        _validate_count_bounds(self)
        require_paper_only_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainEvidenceMemoryRouterRow:
    domain_label: str
    team_label: str
    memory_match_count: Decimal
    evidence_item_count: Decimal
    memory_match_ratio: Decimal
    independent_evidence_count: Decimal
    required_independent_evidence_count: Decimal
    independence_ratio: Decimal
    stale_memory_count: Decimal
    memory_item_count: Decimal
    stale_memory_ratio: Decimal
    unresolved_conflict_count: Decimal
    conflict_pressure_ratio: Decimal
    readiness_score: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainEvidenceMemoryRouterRow, "row")
        _require_public_string("domain_label", self.domain_label)
        _require_public_string("team_label", self.team_label)
        for field_name in (
            "memory_match_count",
            "evidence_item_count",
            "independent_evidence_count",
            "required_independent_evidence_count",
            "stale_memory_count",
            "memory_item_count",
            "unresolved_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "required_independent_evidence_count",
            "memory_item_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "memory_match_ratio",
            "independence_ratio",
            "stale_memory_ratio",
            "conflict_pressure_ratio",
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
class ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount,
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
class ResearchTeamDomainEvidenceMemoryRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    route_count: Decimal
    pass_route_count: Decimal
    watch_route_count: Decimal
    block_route_count: Decimal
    average_readiness_score: Decimal
    lowest_readiness_score: Decimal
    lowest_memory_match_ratio: Decimal
    lowest_independence_ratio: Decimal
    max_stale_memory_ratio: Decimal
    max_conflict_pressure_ratio: Decimal
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount, ...]
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
            "route_count",
            "pass_route_count",
            "watch_route_count",
            "block_route_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "lowest_readiness_score",
            "lowest_memory_match_ratio",
            "lowest_independence_ratio",
            "max_stale_memory_ratio",
            "max_conflict_pressure_ratio",
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
        _validate_public_report_payload(payload)
        return payload


def build_research_team_domain_evidence_memory_router_report(
    inputs: list[ResearchTeamDomainEvidenceMemoryRouterInput]
    | tuple[ResearchTeamDomainEvidenceMemoryRouterInput, ...],
    *,
    config: ResearchTeamDomainEvidenceMemoryRouterReportConfig,
    generated_at: datetime,
) -> ResearchTeamDomainEvidenceMemoryRouterReport:
    if type(config) is not ResearchTeamDomainEvidenceMemoryRouterReportConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainEvidenceMemoryRouterReportConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_input(input_value, config) for input_value in normalized_inputs)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "router_status": _status_from_report_reason_codes(reason_codes),
        "route_count": _decimal_count(len(rows)),
        "pass_route_count": _status_count(rows, "pass"),
        "watch_route_count": _status_count(rows, "watch"),
        "block_route_count": _status_count(rows, "block"),
        "average_readiness_score": _average(rows, "readiness_score"),
        "lowest_readiness_score": _minimum(rows, "readiness_score"),
        "lowest_memory_match_ratio": _minimum(rows, "memory_match_ratio"),
        "lowest_independence_ratio": _minimum(rows, "independence_ratio"),
        "max_stale_memory_ratio": _maximum(rows, "stale_memory_ratio"),
        "max_conflict_pressure_ratio": _maximum(rows, "conflict_pressure_ratio"),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainEvidenceMemoryRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_domain_evidence_memory_router_report_payload(
    report: ResearchTeamDomainEvidenceMemoryRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainEvidenceMemoryRouterReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainEvidenceMemoryRouterReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_report_payload(payload)
    return payload


def validate_research_team_domain_evidence_memory_router_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_report_payload(payload)
    return True


def _row_for_input(
    input_value: ResearchTeamDomainEvidenceMemoryRouterInput,
    config: ResearchTeamDomainEvidenceMemoryRouterReportConfig,
) -> ResearchTeamDomainEvidenceMemoryRouterRow:
    memory_match_ratio = _ratio(
        input_value.memory_match_count,
        input_value.evidence_item_count,
    )
    independence_ratio = _ratio(
        input_value.independent_evidence_count,
        input_value.required_independent_evidence_count,
    )
    stale_memory_ratio = _ratio(
        input_value.stale_memory_count,
        input_value.memory_item_count,
    )
    conflict_pressure_ratio = _ratio(
        input_value.unresolved_conflict_count,
        input_value.evidence_item_count,
    )
    readiness_score = (
        memory_match_ratio
        + independence_ratio
        + (ONE - stale_memory_ratio)
        + (ONE - conflict_pressure_ratio)
    ) / Decimal("4")
    reason_codes = _row_reason_codes(
        memory_match_ratio=memory_match_ratio,
        independence_ratio=independence_ratio,
        stale_memory_ratio=stale_memory_ratio,
        conflict_pressure_ratio=conflict_pressure_ratio,
        config=config,
    )
    return ResearchTeamDomainEvidenceMemoryRouterRow(
        domain_label=input_value.domain_label,
        team_label=input_value.team_label,
        memory_match_count=input_value.memory_match_count,
        evidence_item_count=input_value.evidence_item_count,
        memory_match_ratio=memory_match_ratio,
        independent_evidence_count=input_value.independent_evidence_count,
        required_independent_evidence_count=input_value.required_independent_evidence_count,
        independence_ratio=independence_ratio,
        stale_memory_count=input_value.stale_memory_count,
        memory_item_count=input_value.memory_item_count,
        stale_memory_ratio=stale_memory_ratio,
        unresolved_conflict_count=input_value.unresolved_conflict_count,
        conflict_pressure_ratio=conflict_pressure_ratio,
        readiness_score=readiness_score.quantize(QUANT),
        router_status=_status_from_row_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_match_ratio: Decimal,
    independence_ratio: Decimal,
    stale_memory_ratio: Decimal,
    conflict_pressure_ratio: Decimal,
    config: ResearchTeamDomainEvidenceMemoryRouterReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_match_ratio < config.memory_match_block_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_memory_match_block")
    if independence_ratio < config.independence_block_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_independence_block")
    if stale_memory_ratio >= config.stale_memory_block_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_stale_memory_block")
    if conflict_pressure_ratio >= config.conflict_pressure_block_threshold:
        reason_codes.append(
            "research_team_domain_evidence_memory_router_conflict_pressure_block",
        )
    if reason_codes:
        return tuple(reason_codes)
    if memory_match_ratio < config.memory_match_watch_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_memory_match_watch")
    if independence_ratio < config.independence_watch_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_independence_watch")
    if stale_memory_ratio >= config.stale_memory_watch_threshold:
        reason_codes.append("research_team_domain_evidence_memory_router_stale_memory_watch")
    if conflict_pressure_ratio >= config.conflict_pressure_watch_threshold:
        reason_codes.append(
            "research_team_domain_evidence_memory_router_conflict_pressure_watch",
        )
    if reason_codes:
        return tuple(reason_codes)
    return ("research_team_domain_evidence_memory_router_ready",)


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_team_domain_evidence_memory_router_empty",)
    reason_codes: list[str] = []
    if any(row.router_status == "block" for row in rows):
        reason_codes.append("research_team_domain_evidence_memory_router_block_routes_present")
    if any(row.router_status == "watch" for row in rows):
        reason_codes.append("research_team_domain_evidence_memory_router_watch_routes_present")
    if not reason_codes:
        reason_codes.append("research_team_domain_evidence_memory_router_ready")
    return tuple(reason_codes)


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_report_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        "research_team_domain_evidence_memory_router_block_routes_present" in reason_codes
        or "research_team_domain_evidence_memory_router_empty" in reason_codes
    ):
        return "block"
    if "research_team_domain_evidence_memory_router_watch_routes_present" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
) -> tuple[ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount, ...]:
    all_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(all_reason_codes.count(reason_code)),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in all_reason_codes
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchTeamDomainEvidenceMemoryRouterInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainEvidenceMemoryRouterInput:
            raise ValueError("inputs must contain input values")
        require_paper_only_flags("input", row)
        label = (row.domain_label, row.team_label)
        if label in seen_labels:
            raise ValueError("domain_label and team_label values must be unique")
        seen_labels.add(label)
    return tuple(sorted(rows, key=lambda row: (row.domain_label, row.team_label)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainEvidenceMemoryRouterRow:
            raise ValueError("rows must contain row values")
        require_paper_only_flags("row", row)
        label = (row.domain_label, row.team_label)
        if label in seen_labels:
            raise ValueError("domain_label and team_label values must be unique")
        seen_labels.add(label)
    return tuple(sorted(rows, key=lambda row: (row.domain_label, row.team_label)))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen_reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount:
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
    value: ResearchTeamDomainEvidenceMemoryRouterInput
    | ResearchTeamDomainEvidenceMemoryRouterRow,
) -> None:
    if value.memory_match_count > value.evidence_item_count:
        raise ValueError("memory_match_count must not exceed evidence_item_count")
    if value.independent_evidence_count > value.required_independent_evidence_count:
        raise ValueError(
            "independent_evidence_count must not exceed "
            "required_independent_evidence_count",
        )
    if value.stale_memory_count > value.memory_item_count:
        raise ValueError("stale_memory_count must not exceed memory_item_count")
    if value.unresolved_conflict_count > value.evidence_item_count:
        raise ValueError("unresolved_conflict_count must not exceed evidence_item_count")


def _validate_row_consistency(row: ResearchTeamDomainEvidenceMemoryRouterRow) -> None:
    if row.memory_match_ratio != _ratio(row.memory_match_count, row.evidence_item_count):
        raise ValueError("memory_match_ratio must match counts")
    if row.independence_ratio != _ratio(
        row.independent_evidence_count,
        row.required_independent_evidence_count,
    ):
        raise ValueError("independence_ratio must match counts")
    if row.stale_memory_ratio != _ratio(row.stale_memory_count, row.memory_item_count):
        raise ValueError("stale_memory_ratio must match counts")
    if row.conflict_pressure_ratio != _ratio(
        row.unresolved_conflict_count,
        row.evidence_item_count,
    ):
        raise ValueError("conflict_pressure_ratio must match counts")
    expected_score = (
        row.memory_match_ratio
        + row.independence_ratio
        + (ONE - row.stale_memory_ratio)
        + (ONE - row.conflict_pressure_ratio)
    ) / Decimal("4")
    if row.readiness_score != expected_score.quantize(QUANT):
        raise ValueError("readiness_score must match component ratios")
    if row.router_status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("router_status must match reason_codes")


def _validate_report_consistency(report: ResearchTeamDomainEvidenceMemoryRouterReport) -> None:
    if report.route_count != _decimal_count(len(report.rows)):
        raise ValueError("route_count must match rows")
    if report.pass_route_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_route_count must match rows")
    if report.watch_route_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_route_count must match rows")
    if report.block_route_count != _status_count(report.rows, "block"):
        raise ValueError("block_route_count must match rows")
    if report.average_readiness_score != _average(report.rows, "readiness_score"):
        raise ValueError("average_readiness_score must match rows")
    if report.lowest_readiness_score != _minimum(report.rows, "readiness_score"):
        raise ValueError("lowest_readiness_score must match rows")
    if report.lowest_memory_match_ratio != _minimum(report.rows, "memory_match_ratio"):
        raise ValueError("lowest_memory_match_ratio must match rows")
    if report.lowest_independence_ratio != _minimum(report.rows, "independence_ratio"):
        raise ValueError("lowest_independence_ratio must match rows")
    if report.max_stale_memory_ratio != _maximum(report.rows, "stale_memory_ratio"):
        raise ValueError("max_stale_memory_ratio must match rows")
    if report.max_conflict_pressure_ratio != _maximum(rows=report.rows, field_name="conflict_pressure_ratio"):
        raise ValueError("max_conflict_pressure_ratio must match rows")
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
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.router_status == status))


def _average(
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return (
        sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows))
    ).quantize(QUANT)


def _minimum(
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return min(getattr(row, field_name) for row in rows).quantize(QUANT)


def _maximum(
    rows: tuple[ResearchTeamDomainEvidenceMemoryRouterRow, ...],
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
    report: ResearchTeamDomainEvidenceMemoryRouterReport,
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


def _validate_public_report_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    required_keys = {
        "generated_at",
        "config_version",
        "router_status",
        "route_count",
        "pass_route_count",
        "watch_route_count",
        "block_route_count",
        "average_readiness_score",
        "lowest_readiness_score",
        "lowest_memory_match_ratio",
        "lowest_independence_ratio",
        "max_stale_memory_ratio",
        "max_conflict_pressure_ratio",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_keys:
        raise ValueError("payload fields must match public report contract")
    _require_status("router_status", payload["router_status"])
    _require_sha256_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in (
        "route_count",
        "pass_route_count",
        "watch_route_count",
        "block_route_count",
        "average_readiness_score",
        "lowest_readiness_score",
        "lowest_memory_match_ratio",
        "lowest_independence_ratio",
        "max_stale_memory_ratio",
        "max_conflict_pressure_ratio",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row_payload in payload["rows"]:
        _validate_public_row_payload(row_payload)
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count_payload in payload["reason_code_counts"]:
        _validate_public_reason_count_payload(count_payload)
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_reason_codes(tuple(payload["reason_codes"]), REPORT_REASON_CODES)
    expected_digest = _report_digest_from_values(_payload_without_digest(payload))
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainEvidenceMemoryRouterReport:
    return ResearchTeamDomainEvidenceMemoryRouterReport(
        generated_at=_datetime_from_payload_string("generated_at", payload["generated_at"]),
        config_version=_public_payload_string("config_version", payload["config_version"]),
        router_status=_public_payload_string("router_status", payload["router_status"]),
        route_count=_require_decimal_payload_string("route_count", payload["route_count"]),
        pass_route_count=_require_decimal_payload_string(
            "pass_route_count",
            payload["pass_route_count"],
        ),
        watch_route_count=_require_decimal_payload_string(
            "watch_route_count",
            payload["watch_route_count"],
        ),
        block_route_count=_require_decimal_payload_string(
            "block_route_count",
            payload["block_route_count"],
        ),
        average_readiness_score=_require_decimal_payload_string(
            "average_readiness_score",
            payload["average_readiness_score"],
        ),
        lowest_readiness_score=_require_decimal_payload_string(
            "lowest_readiness_score",
            payload["lowest_readiness_score"],
        ),
        lowest_memory_match_ratio=_require_decimal_payload_string(
            "lowest_memory_match_ratio",
            payload["lowest_memory_match_ratio"],
        ),
        lowest_independence_ratio=_require_decimal_payload_string(
            "lowest_independence_ratio",
            payload["lowest_independence_ratio"],
        ),
        max_stale_memory_ratio=_require_decimal_payload_string(
            "max_stale_memory_ratio",
            payload["max_stale_memory_ratio"],
        ),
        max_conflict_pressure_ratio=_require_decimal_payload_string(
            "max_conflict_pressure_ratio",
            payload["max_conflict_pressure_ratio"],
        ),
        rows=tuple(_row_from_public_payload(row_payload) for row_payload in payload["rows"]),
        reason_code_counts=tuple(
            _reason_count_from_public_payload(count_payload)
            for count_payload in payload["reason_code_counts"]
        ),
        reason_codes=tuple(payload["reason_codes"]),
        derived_validation_digest=_public_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    payload: object,
) -> ResearchTeamDomainEvidenceMemoryRouterRow:
    _validate_public_row_payload(payload)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    return ResearchTeamDomainEvidenceMemoryRouterRow(
        domain_label=_public_payload_string("domain_label", payload["domain_label"]),
        team_label=_public_payload_string("team_label", payload["team_label"]),
        memory_match_count=_require_decimal_payload_string(
            "memory_match_count",
            payload["memory_match_count"],
        ),
        evidence_item_count=_require_decimal_payload_string(
            "evidence_item_count",
            payload["evidence_item_count"],
        ),
        memory_match_ratio=_require_decimal_payload_string(
            "memory_match_ratio",
            payload["memory_match_ratio"],
        ),
        independent_evidence_count=_require_decimal_payload_string(
            "independent_evidence_count",
            payload["independent_evidence_count"],
        ),
        required_independent_evidence_count=_require_decimal_payload_string(
            "required_independent_evidence_count",
            payload["required_independent_evidence_count"],
        ),
        independence_ratio=_require_decimal_payload_string(
            "independence_ratio",
            payload["independence_ratio"],
        ),
        stale_memory_count=_require_decimal_payload_string(
            "stale_memory_count",
            payload["stale_memory_count"],
        ),
        memory_item_count=_require_decimal_payload_string(
            "memory_item_count",
            payload["memory_item_count"],
        ),
        stale_memory_ratio=_require_decimal_payload_string(
            "stale_memory_ratio",
            payload["stale_memory_ratio"],
        ),
        unresolved_conflict_count=_require_decimal_payload_string(
            "unresolved_conflict_count",
            payload["unresolved_conflict_count"],
        ),
        conflict_pressure_ratio=_require_decimal_payload_string(
            "conflict_pressure_ratio",
            payload["conflict_pressure_ratio"],
        ),
        readiness_score=_require_decimal_payload_string(
            "readiness_score",
            payload["readiness_score"],
        ),
        router_status=_public_payload_string("router_status", payload["router_status"]),
        reason_codes=tuple(payload["reason_codes"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _reason_count_from_public_payload(
    payload: object,
) -> ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount:
    _validate_public_reason_count_payload(payload)
    if type(payload) is not dict:
        raise ValueError("reason count payload must be a JSON object")
    return ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount(
        reason_code=_public_payload_string("reason_code", payload["reason_code"]),
        count=_require_decimal_payload_string("count", payload["count"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _datetime_from_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime payload string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime payload string") from exc
    return _as_utc(field_name, parsed)


def _public_payload_string(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    return value


def _validate_public_row_payload(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    required_keys = {
        "domain_label",
        "team_label",
        "memory_match_count",
        "evidence_item_count",
        "memory_match_ratio",
        "independent_evidence_count",
        "required_independent_evidence_count",
        "independence_ratio",
        "stale_memory_count",
        "memory_item_count",
        "stale_memory_ratio",
        "unresolved_conflict_count",
        "conflict_pressure_ratio",
        "readiness_score",
        "router_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_keys:
        raise ValueError("row payload fields must match public contract")
    require_paper_only_flags("row payload", _DictFlags(payload))
    _require_public_string("domain_label", payload["domain_label"])
    _require_public_string("team_label", payload["team_label"])
    _require_status("router_status", payload["router_status"])
    for field_name in (
        "memory_match_count",
        "evidence_item_count",
        "memory_match_ratio",
        "independent_evidence_count",
        "required_independent_evidence_count",
        "independence_ratio",
        "stale_memory_count",
        "memory_item_count",
        "stale_memory_ratio",
        "unresolved_conflict_count",
        "conflict_pressure_ratio",
        "readiness_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    if type(payload["reason_codes"]) is not list:
        raise ValueError("row reason_codes must be a list")
    _normalize_reason_codes(tuple(payload["reason_codes"]), ROW_REASON_CODES)


def _validate_public_reason_count_payload(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("reason count payload must be a JSON object")
    required_keys = {"reason_code", "count", "paper_only", "report_only", "readonly"}
    if set(payload) != required_keys:
        raise ValueError("reason count payload fields must match public contract")
    require_paper_only_flags("reason count payload", _DictFlags(payload))
    _require_public_string("reason_code", payload["reason_code"])
    if payload["reason_code"] not in ROW_REASON_CODES:
        raise ValueError("reason_code must be known")
    _require_decimal_payload_string("count", payload["count"])


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal payload string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal payload string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != str(decimal_value.quantize(QUANT)):
        raise ValueError(f"{field_name} must be canonical")
    return decimal_value


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    return unsigned_payload


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
    "DEFAULT_RESEARCH_TEAM_DOMAIN_EVIDENCE_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
    "ResearchTeamDomainEvidenceMemoryRouterReportConfig",
    "ResearchTeamDomainEvidenceMemoryRouterInput",
    "ResearchTeamDomainEvidenceMemoryRouterRow",
    "ResearchTeamDomainEvidenceMemoryRouterReasonCodeCount",
    "ResearchTeamDomainEvidenceMemoryRouterReport",
    "build_research_team_domain_evidence_memory_router_report",
    "research_team_domain_evidence_memory_router_report_payload",
    "validate_research_team_domain_evidence_memory_router_public_payload",
)
