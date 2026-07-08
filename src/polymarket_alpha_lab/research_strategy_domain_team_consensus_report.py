"""Pure report for domain-team consensus quality review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any, Mapping


__all__ = (
    "ResearchStrategyDomainTeamConsensusConfig",
    "ResearchStrategyDomainTeamConsensusInput",
    "ResearchStrategyDomainTeamConsensusReasonCodeCount",
    "ResearchStrategyDomainTeamConsensusReport",
    "ResearchStrategyDomainTeamConsensusRow",
    "build_research_strategy_domain_team_consensus_report",
    "research_strategy_domain_team_consensus_report_digest",
    "research_strategy_domain_team_consensus_report_payload",
)

DEFAULT_CONFIG_VERSION = "research-strategy-domain-team-consensus-report-v0"
STATUSES = ("pass", "watch", "block")
QUALITY_FIELDS = (
    "specialist_agreement",
    "memory_freshness",
    "evidence_coverage",
)
PRESSURE_FIELDS = (
    "unresolved_dissent",
    "escalation_urgency",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TERMS = (
    "au" "th",
    "b" "uy",
    "condition",
    "event",
    "execution",
    "identifier",
    "market",
    "mutation",
    "or" "der",
    "raw",
    "se" "ll",
    "signing",
    "source",
    "token",
    "tr" "ade",
    "wa" "llet",
)
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyDomainTeamConsensusConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_dimension_score: Decimal = Decimal("0.700000")
    watch_dimension_score: Decimal = Decimal("0.400000")
    pass_consensus_quality_score: Decimal = Decimal("0.750000")
    watch_consensus_quality_score: Decimal = Decimal("0.500000")
    specialist_agreement_weight: Decimal = Decimal("0.200000")
    memory_freshness_weight: Decimal = Decimal("0.200000")
    evidence_coverage_weight: Decimal = Decimal("0.200000")
    dissent_resolution_weight: Decimal = Decimal("0.200000")
    escalation_stability_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_dimension_score",
            "watch_dimension_score",
            "pass_consensus_quality_score",
            "watch_consensus_quality_score",
            "specialist_agreement_weight",
            "memory_freshness_weight",
            "evidence_coverage_weight",
            "dissent_resolution_weight",
            "escalation_stability_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_dimension_score <= self.watch_dimension_score:
            raise ValueError("pass_dimension_score must exceed watch_dimension_score")
        if self.pass_consensus_quality_score <= self.watch_consensus_quality_score:
            raise ValueError(
                "pass_consensus_quality_score must exceed "
                "watch_consensus_quality_score",
            )
        if _config_weight_sum(self) != ONE:
            raise ValueError("consensus quality weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamConsensusInput:
    domain_team_label: str
    specialist_agreement: Decimal
    memory_freshness: Decimal
    evidence_coverage: Decimal
    unresolved_dissent: Decimal
    escalation_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("domain_team_label", self.domain_team_label)
        for field_name in (*QUALITY_FIELDS, *PRESSURE_FIELDS):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamConsensusRow:
    domain_team_label: str
    specialist_agreement: Decimal
    memory_freshness: Decimal
    evidence_coverage: Decimal
    unresolved_dissent: Decimal
    escalation_urgency: Decimal
    specialist_agreement_score: Decimal
    memory_freshness_score: Decimal
    evidence_coverage_score: Decimal
    dissent_resolution_score: Decimal
    escalation_stability_score: Decimal
    consensus_quality_score: Decimal
    lowest_dimension_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("domain_team_label", self.domain_team_label)
        for field_name in (
            *QUALITY_FIELDS,
            *PRESSURE_FIELDS,
            "specialist_agreement_score",
            "memory_freshness_score",
            "evidence_coverage_score",
            "dissent_resolution_score",
            "escalation_stability_score",
            "consensus_quality_score",
            "lowest_dimension_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamConsensusReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamConsensusReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_consensus_quality_score: Decimal | None
    min_specialist_agreement: Decimal | None
    min_memory_freshness: Decimal | None
    min_evidence_coverage: Decimal | None
    max_unresolved_dissent: Decimal | None
    max_escalation_urgency: Decimal | None
    status: str
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...]
    reason_code_counts: tuple[ResearchStrategyDomainTeamConsensusReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_consensus_quality_score",
            "min_specialist_agreement",
            "min_memory_freshness",
            "min_evidence_coverage",
            "max_unresolved_dissent",
            "max_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = research_strategy_domain_team_consensus_report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_domain_team_consensus_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyDomainTeamConsensusConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamConsensusReport:
    if type(config) is not ResearchStrategyDomainTeamConsensusConfig:
        raise ValueError("config must be a ResearchStrategyDomainTeamConsensusConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.domain_team_label)
    )
    reason_codes = _summary_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_consensus_quality_score": _average_consensus_quality_score(rows),
        "min_specialist_agreement": _min_or_none(
            row.specialist_agreement for row in rows
        ),
        "min_memory_freshness": _min_or_none(row.memory_freshness for row in rows),
        "min_evidence_coverage": _min_or_none(row.evidence_coverage for row in rows),
        "max_unresolved_dissent": _max_or_none(row.unresolved_dissent for row in rows),
        "max_escalation_urgency": _max_or_none(row.escalation_urgency for row in rows),
        "status": _summary_status(reason_codes),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyDomainTeamConsensusReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_domain_team_consensus_report_payload(
    report: ResearchStrategyDomainTeamConsensusReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDomainTeamConsensusReport:
        raise ValueError("report must be a ResearchStrategyDomainTeamConsensusReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_domain_team_consensus_report_digest(
    report: ResearchStrategyDomainTeamConsensusReport,
) -> str:
    if type(report) is not ResearchStrategyDomainTeamConsensusReport:
        raise ValueError("report must be a ResearchStrategyDomainTeamConsensusReport")
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _report_digest_from_values(values)


def _row_from_input(
    item: ResearchStrategyDomainTeamConsensusInput,
    *,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> ResearchStrategyDomainTeamConsensusRow:
    specialist_agreement_score = item.specialist_agreement
    memory_freshness_score = item.memory_freshness
    evidence_coverage_score = item.evidence_coverage
    dissent_resolution_score = _inverse_score(item.unresolved_dissent)
    escalation_stability_score = _inverse_score(item.escalation_urgency)
    score = _consensus_quality_score(
        specialist_agreement_score=specialist_agreement_score,
        memory_freshness_score=memory_freshness_score,
        evidence_coverage_score=evidence_coverage_score,
        dissent_resolution_score=dissent_resolution_score,
        escalation_stability_score=escalation_stability_score,
        config=config,
    )
    lowest_dimension_score = min(
        specialist_agreement_score,
        memory_freshness_score,
        evidence_coverage_score,
        dissent_resolution_score,
        escalation_stability_score,
    )
    status = _row_status(
        consensus_quality_score=score,
        lowest_dimension_score=lowest_dimension_score,
        config=config,
    )
    return ResearchStrategyDomainTeamConsensusRow(
        domain_team_label=item.domain_team_label,
        specialist_agreement=item.specialist_agreement,
        memory_freshness=item.memory_freshness,
        evidence_coverage=item.evidence_coverage,
        unresolved_dissent=item.unresolved_dissent,
        escalation_urgency=item.escalation_urgency,
        specialist_agreement_score=specialist_agreement_score,
        memory_freshness_score=memory_freshness_score,
        evidence_coverage_score=evidence_coverage_score,
        dissent_resolution_score=dissent_resolution_score,
        escalation_stability_score=escalation_stability_score,
        consensus_quality_score=score,
        lowest_dimension_score=lowest_dimension_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _consensus_quality_score(
    *,
    specialist_agreement_score: Decimal,
    memory_freshness_score: Decimal,
    evidence_coverage_score: Decimal,
    dissent_resolution_score: Decimal,
    escalation_stability_score: Decimal,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            specialist_agreement_score * config.specialist_agreement_weight
            + memory_freshness_score * config.memory_freshness_weight
            + evidence_coverage_score * config.evidence_coverage_weight
            + dissent_resolution_score * config.dissent_resolution_weight
            + escalation_stability_score * config.escalation_stability_weight
        )
    return _quantize(score)


def _row_status(
    *,
    consensus_quality_score: Decimal,
    lowest_dimension_score: Decimal,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> str:
    if (
        consensus_quality_score < config.watch_consensus_quality_score
        or lowest_dimension_score < config.watch_dimension_score
    ):
        return "block"
    if (
        consensus_quality_score < config.pass_consensus_quality_score
        or lowest_dimension_score < config.pass_dimension_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyDomainTeamConsensusInput,
    *,
    status: str,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> tuple[str, ...]:
    codes = (
        f"domain_team_consensus_quality_{status}",
        f"evidence_coverage_{_quality_status(item.evidence_coverage, config)}",
        f"escalation_urgency_{_pressure_status(item.escalation_urgency, config)}",
        f"memory_freshness_{_quality_status(item.memory_freshness, config)}",
        f"report_only_domain_team_consensus_{status}",
        f"specialist_agreement_{_quality_status(item.specialist_agreement, config)}",
        f"unresolved_dissent_{_pressure_status(item.unresolved_dissent, config)}",
    )
    normalized = list(codes)
    for code in item.reason_codes:
        input_code = f"input_{code}"
        if input_code not in normalized:
            normalized.append(input_code)
    return tuple(
        code
        for code in (
            f"domain_team_consensus_quality_{status}",
            "evidence_coverage_block",
            "evidence_coverage_watch",
            "evidence_coverage_pass",
            "escalation_urgency_block",
            "escalation_urgency_watch",
            "escalation_urgency_pass",
            *sorted(code for code in normalized if code.startswith("input_")),
            "memory_freshness_block",
            "memory_freshness_watch",
            "memory_freshness_pass",
            f"report_only_domain_team_consensus_{status}",
            "specialist_agreement_block",
            "specialist_agreement_watch",
            "specialist_agreement_pass",
            "unresolved_dissent_block",
            "unresolved_dissent_watch",
            "unresolved_dissent_pass",
        )
        if code in normalized
    )


def _quality_status(
    value: Decimal,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> str:
    if value < config.watch_dimension_score:
        return "block"
    if value < config.pass_dimension_score:
        return "watch"
    return "pass"


def _pressure_status(
    value: Decimal,
    config: ResearchStrategyDomainTeamConsensusConfig,
) -> str:
    if value >= config.watch_dimension_score:
        return "block"
    if value > ONE - config.pass_dimension_score:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyDomainTeamConsensusInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyDomainTeamConsensusInput:
    if type(value) is ResearchStrategyDomainTeamConsensusInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyDomainTeamConsensusInput(
        domain_team_label=_field_value(value, "domain_team_label"),
        specialist_agreement=_field_value(value, "specialist_agreement"),
        memory_freshness=_field_value(value, "memory_freshness"),
        evidence_coverage=_field_value(value, "evidence_coverage"),
        unresolved_dissent=_field_value(value, "unresolved_dissent"),
        escalation_urgency=_field_value(value, "escalation_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_domain_team_consensus_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("domain_team_consensus_quality_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_domain_team_consensus_inputs",):
        return "block"
    if "domain_team_consensus_quality_block" in reason_codes:
        return "block"
    if "domain_team_consensus_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyDomainTeamConsensusReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainTeamConsensusReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainTeamConsensusReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_consensus_quality_score(
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.consensus_quality_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return min(items)


def _normalize_rows(
    rows: tuple[ResearchStrategyDomainTeamConsensusRow, ...],
) -> tuple[ResearchStrategyDomainTeamConsensusRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyDomainTeamConsensusRow:
            raise ValueError("rows must contain ResearchStrategyDomainTeamConsensusRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.domain_team_label))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by domain_team_label")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyDomainTeamConsensusReasonCodeCount, ...],
) -> tuple[ResearchStrategyDomainTeamConsensusReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyDomainTeamConsensusReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainTeamConsensusReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchStrategyDomainTeamConsensusRow) -> None:
    if row.specialist_agreement_score != row.specialist_agreement:
        raise ValueError("specialist_agreement_score must match specialist_agreement")
    if row.memory_freshness_score != row.memory_freshness:
        raise ValueError("memory_freshness_score must match memory_freshness")
    if row.evidence_coverage_score != row.evidence_coverage:
        raise ValueError("evidence_coverage_score must match evidence_coverage")
    if row.dissent_resolution_score != _inverse_score(row.unresolved_dissent):
        raise ValueError("dissent_resolution_score must match unresolved_dissent")
    if row.escalation_stability_score != _inverse_score(row.escalation_urgency):
        raise ValueError("escalation_stability_score must match escalation_urgency")
    calculated_lowest = min(
        row.specialist_agreement_score,
        row.memory_freshness_score,
        row.evidence_coverage_score,
        row.dissent_resolution_score,
        row.escalation_stability_score,
    )
    if row.lowest_dimension_score != calculated_lowest:
        raise ValueError("lowest_dimension_score must match dimensions")
    highest_dimension = max(
        row.specialist_agreement_score,
        row.memory_freshness_score,
        row.evidence_coverage_score,
        row.dissent_resolution_score,
        row.escalation_stability_score,
    )
    if (
        row.consensus_quality_score < row.lowest_dimension_score
        or row.consensus_quality_score > highest_dimension
    ):
        raise ValueError("consensus_quality_score must stay within dimension bounds")
    expected_code = f"domain_team_consensus_quality_{row.status}"
    if expected_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyDomainTeamConsensusReport,
) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_consensus_quality_score != _average_consensus_quality_score(
        report.rows,
    ):
        raise ValueError("average_consensus_quality_score must match rows")
    if report.min_specialist_agreement != _min_or_none(
        row.specialist_agreement for row in report.rows
    ):
        raise ValueError("min_specialist_agreement must match rows")
    if report.min_memory_freshness != _min_or_none(
        row.memory_freshness for row in report.rows
    ):
        raise ValueError("min_memory_freshness must match rows")
    if report.min_evidence_coverage != _min_or_none(
        row.evidence_coverage for row in report.rows
    ):
        raise ValueError("min_evidence_coverage must match rows")
    if report.max_unresolved_dissent != _max_or_none(
        row.unresolved_dissent for row in report.rows
    ):
        raise ValueError("max_unresolved_dissent must match rows")
    if report.max_escalation_urgency != _max_or_none(
        row.escalation_urgency for row in report.rows
    ):
        raise ValueError("max_escalation_urgency must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    raise ValueError("payload value is not JSON serializable")


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _payload_value(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _inverse_score(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _config_weight_sum(config: ResearchStrategyDomainTeamConsensusConfig) -> Decimal:
    return _quantize(
        config.specialist_agreement_weight
        + config.memory_freshness_weight
        + config.evidence_coverage_weight
        + config.dissent_resolution_weight
        + config.escalation_stability_weight,
    )


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public reason code")
    lowered = value.lower()
    if lowered != value:
        raise ValueError(f"{field_name} must be lowercase")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")
