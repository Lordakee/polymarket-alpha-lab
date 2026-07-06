from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


DEFAULT_CONFIG_VERSION = "strategy-research-packet-readiness-v3"
READINESS_STATUSES = ("ready", "watch", "blocked")
MATERIAL_SECTIONS = (
    "forecast",
    "source_quorum",
    "resolution_contract",
    "cost_model",
    "team_memory",
    "audit_packet",
)
REASON_CODES = (
    "empty_input",
    "forecast_missing",
    "source_quorum_missing",
    "resolution_contract_missing",
    "cost_model_missing",
    "team_memory_missing",
    "audit_packet_missing",
)
SECTION_REASON_CODES = {
    "forecast": "forecast_missing",
    "source_quorum": "source_quorum_missing",
    "resolution_contract": "resolution_contract_missing",
    "cost_model": "cost_model_missing",
    "team_memory": "team_memory_missing",
    "audit_packet": "audit_packet_missing",
}
BLOCKING_SECTIONS = (
    "forecast",
    "source_quorum",
    "resolution_contract",
    "cost_model",
    "audit_packet",
)
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class StrategyResearchPacketReadinessV3Input:
    candidate_id: str
    market_slug: str
    research_generated_at: datetime
    forecast_probability: Decimal | None
    source_count: Decimal
    required_source_count: Decimal
    resolution_contract_present: bool
    cost_model_present: bool
    team_memory_present: bool
    audit_packet_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "research_generated_at",
            _as_utc("research_generated_at", self.research_generated_at),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_optional_probability(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_decimal(
                "required_source_count",
                self.required_source_count,
            ),
        )
        for field_name in (
            "resolution_contract_present",
            "cost_model_present",
            "team_memory_present",
            "audit_packet_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResearchPacketReadinessV3Row:
    candidate_id: str
    market_slug: str
    research_generated_at: datetime
    forecast_probability: Decimal | None
    source_count: Decimal
    required_source_count: Decimal
    forecast_present: bool
    source_quorum_met: bool
    resolution_contract_present: bool
    cost_model_present: bool
    team_memory_present: bool
    audit_packet_present: bool
    readiness_status: str
    missing_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "research_generated_at",
            _as_utc("research_generated_at", self.research_generated_at),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_optional_probability(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_decimal(
                "required_source_count",
                self.required_source_count,
            ),
        )
        for field_name in (
            "forecast_present",
            "source_quorum_met",
            "resolution_contract_present",
            "cost_model_present",
            "team_memory_present",
            "audit_packet_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_readiness_status("readiness_status", self.readiness_status)
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyResearchPacketReadinessV3Report:
    generated_at: datetime
    config_version: str
    readiness_status: str
    missing_sections: tuple[str, ...]
    reason_codes: tuple[str, ...]
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    rows: tuple[StrategyResearchPacketReadinessV3Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_readiness_status("readiness_status", self.readiness_status)
        object.__setattr__(
            self,
            "missing_sections",
            _normalize_missing_sections(self.missing_sections),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_strategy_research_packet_readiness_v3_report(
    candidates: tuple[StrategyResearchPacketReadinessV3Input, ...]
    | list[StrategyResearchPacketReadinessV3Input],
    *,
    generated_at: datetime,
    config_version: str = DEFAULT_CONFIG_VERSION,
) -> StrategyResearchPacketReadinessV3Report:
    _require_canonical_string("config_version", config_version)
    rows = tuple(_row_for_candidate(candidate) for candidate in _normalize_inputs(candidates))
    rows = tuple(sorted(rows, key=lambda row: (row.candidate_id, row.market_slug)))
    missing_sections = _report_missing_sections(rows)
    reason_codes = _report_reason_codes(rows)
    return StrategyResearchPacketReadinessV3Report(
        generated_at=generated_at,
        config_version=config_version,
        readiness_status=_status_from_missing_sections(missing_sections),
        missing_sections=missing_sections,
        reason_codes=reason_codes,
        candidate_count=_count(len(rows)),
        ready_count=_count(sum(1 for row in rows if row.readiness_status == "ready")),
        watch_count=_count(sum(1 for row in rows if row.readiness_status == "watch")),
        blocked_count=_count(sum(1 for row in rows if row.readiness_status == "blocked")),
        rows=rows,
    )


def _row_for_candidate(
    candidate: StrategyResearchPacketReadinessV3Input,
) -> StrategyResearchPacketReadinessV3Row:
    forecast_present = candidate.forecast_probability is not None
    source_quorum_met = candidate.source_count >= candidate.required_source_count
    missing_sections = _missing_sections(
        forecast_present=forecast_present,
        source_quorum_met=source_quorum_met,
        resolution_contract_present=candidate.resolution_contract_present,
        cost_model_present=candidate.cost_model_present,
        team_memory_present=candidate.team_memory_present,
        audit_packet_present=candidate.audit_packet_present,
    )
    return StrategyResearchPacketReadinessV3Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        research_generated_at=candidate.research_generated_at,
        forecast_probability=candidate.forecast_probability,
        source_count=candidate.source_count,
        required_source_count=candidate.required_source_count,
        forecast_present=forecast_present,
        source_quorum_met=source_quorum_met,
        resolution_contract_present=candidate.resolution_contract_present,
        cost_model_present=candidate.cost_model_present,
        team_memory_present=candidate.team_memory_present,
        audit_packet_present=candidate.audit_packet_present,
        readiness_status=_status_from_missing_sections(missing_sections),
        missing_sections=missing_sections,
        reason_codes=_reason_codes_from_missing_sections(missing_sections),
    )


def _normalize_inputs(
    candidates: tuple[StrategyResearchPacketReadinessV3Input, ...]
    | list[StrategyResearchPacketReadinessV3Input],
) -> tuple[StrategyResearchPacketReadinessV3Input, ...]:
    if type(candidates) not in (tuple, list):
        raise ValueError("candidates must be a list or tuple")
    normalized = tuple(candidates)
    for candidate in normalized:
        if type(candidate) is not StrategyResearchPacketReadinessV3Input:
            raise ValueError(
                "candidates must contain StrategyResearchPacketReadinessV3Input values",
            )
    return normalized


def _normalize_rows(
    rows: tuple[StrategyResearchPacketReadinessV3Row, ...],
) -> tuple[StrategyResearchPacketReadinessV3Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyResearchPacketReadinessV3Row:
            raise ValueError(
                "rows must contain StrategyResearchPacketReadinessV3Row values",
            )
    if normalized != tuple(sorted(normalized, key=lambda row: (row.candidate_id, row.market_slug))):
        raise ValueError("rows must use deterministic ordering")
    return normalized


def _missing_sections(
    *,
    forecast_present: bool,
    source_quorum_met: bool,
    resolution_contract_present: bool,
    cost_model_present: bool,
    team_memory_present: bool,
    audit_packet_present: bool,
) -> tuple[str, ...]:
    missing: list[str] = []
    if not forecast_present:
        missing.append("forecast")
    if not source_quorum_met:
        missing.append("source_quorum")
    if not resolution_contract_present:
        missing.append("resolution_contract")
    if not cost_model_present:
        missing.append("cost_model")
    if not team_memory_present:
        missing.append("team_memory")
    if not audit_packet_present:
        missing.append("audit_packet")
    return tuple(missing)


def _report_missing_sections(
    rows: tuple[StrategyResearchPacketReadinessV3Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return MATERIAL_SECTIONS
    return tuple(
        section
        for section in MATERIAL_SECTIONS
        if any(section in row.missing_sections for row in rows)
    )


def _reason_codes_from_missing_sections(
    missing_sections: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(SECTION_REASON_CODES[section] for section in missing_sections)


def _report_reason_codes(
    rows: tuple[StrategyResearchPacketReadinessV3Row, ...],
) -> tuple[str, ...]:
    missing_sections = _report_missing_sections(rows)
    reason_codes = _reason_codes_from_missing_sections(missing_sections)
    if not rows:
        return ("empty_input", *reason_codes)
    return reason_codes


def _status_from_missing_sections(missing_sections: tuple[str, ...]) -> str:
    if not missing_sections:
        return "ready"
    if any(section in BLOCKING_SECTIONS for section in missing_sections):
        return "blocked"
    return "watch"


def _validate_row_consistency(row: StrategyResearchPacketReadinessV3Row) -> None:
    expected_missing_sections = _missing_sections(
        forecast_present=row.forecast_present,
        source_quorum_met=row.source_quorum_met,
        resolution_contract_present=row.resolution_contract_present,
        cost_model_present=row.cost_model_present,
        team_memory_present=row.team_memory_present,
        audit_packet_present=row.audit_packet_present,
    )
    if row.missing_sections != expected_missing_sections:
        raise ValueError("missing_sections must match row evidence state")
    if row.reason_codes != _reason_codes_from_missing_sections(row.missing_sections):
        raise ValueError("reason_codes must match missing_sections")
    if row.readiness_status != _status_from_missing_sections(row.missing_sections):
        raise ValueError("readiness_status must match missing_sections")
    if row.forecast_present != (row.forecast_probability is not None):
        raise ValueError("forecast_present must match forecast_probability")
    if row.source_quorum_met != (row.source_count >= row.required_source_count):
        raise ValueError("source_quorum_met must match source_count")


def _validate_report_consistency(report: StrategyResearchPacketReadinessV3Report) -> None:
    expected_candidate_count = _count(len(report.rows))
    if report.candidate_count != expected_candidate_count:
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _count(
        sum(1 for row in report.rows if row.readiness_status == "ready"),
    ):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.readiness_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.readiness_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    expected_missing_sections = _report_missing_sections(report.rows)
    if report.missing_sections != expected_missing_sections:
        raise ValueError("missing_sections must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.readiness_status != _status_from_missing_sections(expected_missing_sections):
        raise ValueError("readiness_status must match missing_sections")


def _normalize_missing_sections(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("missing_sections must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("missing_sections must be an iterable") from exc
    if len(set(normalized)) != len(normalized):
        raise ValueError("missing_sections must not contain duplicates")
    for section in normalized:
        if type(section) is not str or section not in MATERIAL_SECTIONS:
            raise ValueError("missing_sections include an unknown section")
    if tuple(section for section in MATERIAL_SECTIONS if section in normalized) != normalized:
        raise ValueError("missing_sections must use deterministic ordering")
    return normalized


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for code in normalized:
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError("reason_codes include an unknown code")
    if tuple(code for code in REASON_CODES if code in normalized) != normalized:
        raise ValueError("reason_codes must use deterministic ordering")
    return normalized


def _normalize_optional_probability(name: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_bool(name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_readiness_status(name: str, value: str) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{name} must be one of {READINESS_STATUSES!r}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "MATERIAL_SECTIONS",
    "READINESS_STATUSES",
    "REASON_CODES",
    "StrategyResearchPacketReadinessV3Input",
    "StrategyResearchPacketReadinessV3Report",
    "StrategyResearchPacketReadinessV3Row",
    "build_strategy_research_packet_readiness_v3_report",
)
