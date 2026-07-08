from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_RESOLUTION_DISPUTE_HISTORY_REPORT_CONFIG_VERSION = (
    "research-resolution-dispute-history-report-v0"
)

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_STATUSES = ("pass", "watch", "block")
_RISK_LAYERS = ("low", "medium", "high")
_RETROSPECTIVE_OUTCOMES = ("clean", "contained", "unclear", "reversed")
_RETROSPECTIVE_RISK = {
    "clean": Decimal("0.000000"),
    "contained": Decimal("0.250000"),
    "unclear": Decimal("0.600000"),
    "reversed": Decimal("1.000000"),
}
_ROW_REASON_CODE_SEQUENCE = (
    "dispute_frequency_low",
    "dispute_frequency_watch",
    "dispute_frequency_block",
    "rule_ambiguity_present",
    "rule_ambiguity_severe",
    "evidence_dependency_watch",
    "evidence_dependency_block",
    "retrospective_clean",
    "retrospective_contained",
    "retrospective_unclear",
    "retrospective_reversed",
    "risk_layer_low",
    "risk_layer_medium",
    "risk_layer_high",
    "resolution_dispute_history_pass",
    "resolution_dispute_history_watch",
    "resolution_dispute_history_block",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "no_disputes_to_assess",
    "resolution_dispute_history_pass",
    "resolution_dispute_history_watch",
    "resolution_dispute_history_block",
    "dispute_frequency_watch",
    "dispute_frequency_block",
    "rule_ambiguity_present",
    "rule_ambiguity_severe",
    "evidence_dependency_watch",
    "evidence_dependency_block",
    "retrospective_unclear",
    "retrospective_reversed",
    "risk_layer_high",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "market",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "http",
    "live",
    "auth",
    "wallet",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
)


@dataclass(frozen=True)
class ResearchResolutionDisputeHistoryConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_DISPUTE_HISTORY_REPORT_CONFIG_VERSION
    watch_dispute_frequency: Decimal = Decimal("0.150000")
    block_dispute_frequency: Decimal = Decimal("0.300000")
    watch_rule_ambiguity: Decimal = Decimal("0.350000")
    block_rule_ambiguity: Decimal = Decimal("0.650000")
    watch_evidence_dependency: Decimal = Decimal("0.500000")
    block_evidence_dependency: Decimal = Decimal("0.750000")
    pass_risk_score_ceiling: Decimal = Decimal("0.300000")
    block_risk_score_floor: Decimal = Decimal("0.700000")
    dispute_frequency_weight: Decimal = Decimal("0.300000")
    rule_ambiguity_weight: Decimal = Decimal("0.250000")
    evidence_dependency_weight: Decimal = Decimal("0.250000")
    retrospective_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionDisputeHistoryConfig:
            raise TypeError("ResearchResolutionDisputeHistoryConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionDisputeHistoryConfig:
            raise ValueError("config must be a ResearchResolutionDisputeHistoryConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_DISPUTE_HISTORY_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_dispute_frequency",
            "block_dispute_frequency",
            "watch_rule_ambiguity",
            "block_rule_ambiguity",
            "watch_evidence_dependency",
            "block_evidence_dependency",
            "pass_risk_score_ceiling",
            "block_risk_score_floor",
            "dispute_frequency_weight",
            "rule_ambiguity_weight",
            "evidence_dependency_weight",
            "retrospective_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResolutionDisputeHistoryIncident:
    condition_id: str
    incident_id: str
    observed_at: datetime
    settlement_count: Decimal
    dispute_count: Decimal
    ambiguous_rule_count: Decimal
    evidence_family_count: Decimal
    independent_evidence_family_count: Decimal
    official_evidence_count: Decimal
    retrospective_outcome: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionDisputeHistoryIncident:
            raise TypeError("ResearchResolutionDisputeHistoryIncident does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionDisputeHistoryIncident:
            raise ValueError("incident must be a ResearchResolutionDisputeHistoryIncident")
        _require_public_identifier("condition_id", self.condition_id)
        _require_public_identifier("incident_id", self.incident_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "settlement_count",
            "dispute_count",
            "ambiguous_rule_count",
            "evidence_family_count",
            "independent_evidence_family_count",
            "official_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("retrospective_outcome", self.retrospective_outcome, _RETROSPECTIVE_OUTCOMES)
        _validate_incident(self)
        _require_hard_flags("incident", self)
        _reject_unsafe_public_payload("incident", self)


@dataclass(frozen=True)
class ResearchResolutionDisputeHistoryRow:
    condition_id: str
    incident_id: str
    observed_at: datetime
    settlement_count: Decimal
    dispute_count: Decimal
    dispute_frequency: Decimal
    ambiguous_rule_count: Decimal
    rule_ambiguity_ratio: Decimal
    evidence_family_count: Decimal
    independent_evidence_family_count: Decimal
    official_evidence_count: Decimal
    evidence_dependency_score: Decimal
    retrospective_outcome: str
    retrospective_risk_score: Decimal
    risk_score: Decimal
    risk_layer: str
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionDisputeHistoryRow:
            raise TypeError("ResearchResolutionDisputeHistoryRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionDisputeHistoryRow:
            raise ValueError("row must be a ResearchResolutionDisputeHistoryRow")
        _require_public_identifier("condition_id", self.condition_id)
        _require_public_identifier("incident_id", self.incident_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "settlement_count",
            "dispute_count",
            "ambiguous_rule_count",
            "evidence_family_count",
            "independent_evidence_family_count",
            "official_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dispute_frequency",
            "rule_ambiguity_ratio",
            "evidence_dependency_score",
            "retrospective_risk_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("retrospective_outcome", self.retrospective_outcome, _RETROSPECTIVE_OUTCOMES)
        _require_member("risk_layer", self.risk_layer, _RISK_LAYERS)
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        expected_digest = _derived_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchResolutionDisputeHistoryReport:
    generated_at: datetime
    config_version: str
    incident_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_risk_layer_count: Decimal
    average_dispute_frequency: Decimal
    average_rule_ambiguity_ratio: Decimal
    average_evidence_dependency_score: Decimal
    average_retrospective_risk_score: Decimal
    average_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchResolutionDisputeHistoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionDisputeHistoryReport:
            raise TypeError("ResearchResolutionDisputeHistoryReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionDisputeHistoryReport:
            raise ValueError("report must be a ResearchResolutionDisputeHistoryReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_DISPUTE_HISTORY_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "incident_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_risk_layer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_dispute_frequency",
            "average_rule_ambiguity_ratio",
            "average_evidence_dependency_score",
            "average_retrospective_risk_score",
            "average_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        expected_digest = _derived_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_resolution_dispute_history_report_payload(self)


def build_research_resolution_dispute_history_report(
    incidents: Sequence[ResearchResolutionDisputeHistoryIncident],
    *,
    generated_at: datetime,
    config: ResearchResolutionDisputeHistoryConfig | None = None,
) -> ResearchResolutionDisputeHistoryReport:
    if config is None:
        config = ResearchResolutionDisputeHistoryConfig()
    if type(config) is not ResearchResolutionDisputeHistoryConfig:
        raise ValueError("config must be a ResearchResolutionDisputeHistoryConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_incidents = _normalize_incidents(incidents)
    for incident in normalized_incidents:
        if incident.observed_at > generated_at_utc:
            raise ValueError("incident observed_at must not be after generated_at")
    rows = tuple(_row_for_incident(incident, config=config) for incident in normalized_incidents)
    return ResearchResolutionDisputeHistoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        incident_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_risk_layer_count=_count(sum(1 for row in rows if row.risk_layer == "high")),
        average_dispute_frequency=_average(tuple(row.dispute_frequency for row in rows)),
        average_rule_ambiguity_ratio=_average(tuple(row.rule_ambiguity_ratio for row in rows)),
        average_evidence_dependency_score=_average(
            tuple(row.evidence_dependency_score for row in rows),
        ),
        average_retrospective_risk_score=_average(
            tuple(row.retrospective_risk_score for row in rows),
        ),
        average_risk_score=_average(tuple(row.risk_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_resolution_dispute_history_report_payload(
    report: ResearchResolutionDisputeHistoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionDisputeHistoryReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _require_expected_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_flag_downgrades("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchResolutionDisputeHistoryReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return _mapping_value(self.value, "paper_only")

    @property
    def report_only(self) -> object:
        return _mapping_value(self.value, "report_only")

    @property
    def readonly(self) -> object:
        return _mapping_value(self.value, "readonly")


def _mapping_value(value: Mapping[str, Any], key: str) -> object:
    return value[key] if key in value else None


def _row_for_incident(
    incident: ResearchResolutionDisputeHistoryIncident,
    *,
    config: ResearchResolutionDisputeHistoryConfig,
) -> ResearchResolutionDisputeHistoryRow:
    dispute_frequency = _ratio(incident.dispute_count, incident.settlement_count)
    rule_ambiguity_ratio = _ratio(incident.ambiguous_rule_count, incident.dispute_count)
    dependency_score = _evidence_dependency_score(incident)
    retrospective_risk_score = _RETROSPECTIVE_RISK[incident.retrospective_outcome]
    risk_score = _clamp_ratio(
        dispute_frequency * config.dispute_frequency_weight
        + rule_ambiguity_ratio * config.rule_ambiguity_weight
        + dependency_score * config.evidence_dependency_weight
        + retrospective_risk_score * config.retrospective_weight,
    )
    risk_layer = _risk_layer(risk_score, config=config)
    status = _row_status(
        dispute_frequency=dispute_frequency,
        rule_ambiguity_ratio=rule_ambiguity_ratio,
        dependency_score=dependency_score,
        risk_score=risk_score,
        config=config,
    )
    return ResearchResolutionDisputeHistoryRow(
        condition_id=incident.condition_id,
        incident_id=incident.incident_id,
        observed_at=incident.observed_at,
        settlement_count=incident.settlement_count,
        dispute_count=incident.dispute_count,
        dispute_frequency=dispute_frequency,
        ambiguous_rule_count=incident.ambiguous_rule_count,
        rule_ambiguity_ratio=rule_ambiguity_ratio,
        evidence_family_count=incident.evidence_family_count,
        independent_evidence_family_count=incident.independent_evidence_family_count,
        official_evidence_count=incident.official_evidence_count,
        evidence_dependency_score=dependency_score,
        retrospective_outcome=incident.retrospective_outcome,
        retrospective_risk_score=retrospective_risk_score,
        risk_score=risk_score,
        risk_layer=risk_layer,
        status=status,
        reason_codes=_row_reason_codes(
            dispute_frequency=dispute_frequency,
            rule_ambiguity_ratio=rule_ambiguity_ratio,
            dependency_score=dependency_score,
            retrospective_outcome=incident.retrospective_outcome,
            risk_layer=risk_layer,
            status=status,
            config=config,
        ),
    )


def _evidence_dependency_score(incident: ResearchResolutionDisputeHistoryIncident) -> Decimal:
    if incident.evidence_family_count == _ZERO_COUNT:
        return _ONE_RATIO
    concentration_risk = _ONE_RATIO - _ratio(
        incident.independent_evidence_family_count,
        incident.evidence_family_count,
    )
    official_gap_risk = _ONE_RATIO if incident.official_evidence_count == _ZERO_COUNT else _ZERO_RATIO
    return _clamp_ratio((concentration_risk + official_gap_risk) / Decimal("2"))


def _risk_layer(
    risk_score: Decimal,
    *,
    config: ResearchResolutionDisputeHistoryConfig,
) -> str:
    if risk_score >= config.block_risk_score_floor:
        return "high"
    if risk_score > config.pass_risk_score_ceiling:
        return "medium"
    return "low"


def _row_status(
    *,
    dispute_frequency: Decimal,
    rule_ambiguity_ratio: Decimal,
    dependency_score: Decimal,
    risk_score: Decimal,
    config: ResearchResolutionDisputeHistoryConfig,
) -> str:
    if (
        dispute_frequency >= config.block_dispute_frequency
        or rule_ambiguity_ratio >= config.block_rule_ambiguity
        or dependency_score >= config.block_evidence_dependency
        or risk_score >= config.block_risk_score_floor
    ):
        return "block"
    if (
        dispute_frequency >= config.watch_dispute_frequency
        or rule_ambiguity_ratio >= config.watch_rule_ambiguity
        or dependency_score >= config.watch_evidence_dependency
        or risk_score > config.pass_risk_score_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    dispute_frequency: Decimal,
    rule_ambiguity_ratio: Decimal,
    dependency_score: Decimal,
    retrospective_outcome: str,
    risk_layer: str,
    status: str,
    config: ResearchResolutionDisputeHistoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if dispute_frequency >= config.block_dispute_frequency:
        reason_codes.append("dispute_frequency_block")
    elif dispute_frequency >= config.watch_dispute_frequency:
        reason_codes.append("dispute_frequency_watch")
    else:
        reason_codes.append("dispute_frequency_low")
    if rule_ambiguity_ratio >= config.block_rule_ambiguity:
        reason_codes.append("rule_ambiguity_severe")
    elif rule_ambiguity_ratio > _ZERO_RATIO:
        reason_codes.append("rule_ambiguity_present")
    if dependency_score >= config.block_evidence_dependency:
        reason_codes.append("evidence_dependency_block")
    elif dependency_score >= config.watch_evidence_dependency:
        reason_codes.append("evidence_dependency_watch")
    reason_codes.append(f"retrospective_{retrospective_outcome}")
    reason_codes.append(f"risk_layer_{risk_layer}")
    reason_codes.append(f"resolution_dispute_history_{status}")
    return _normalize_reason_codes(tuple(reason_codes), _ROW_REASON_CODE_SEQUENCE)


def _report_status(rows: tuple[ResearchResolutionDisputeHistoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchResolutionDisputeHistoryRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_disputes_to_assess",)
    reason_codes: list[str] = [f"resolution_dispute_history_{_report_status(rows)}"]
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _REPORT_REASON_CODE_SEQUENCE
        )
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


def _status_count(
    rows: tuple[ResearchResolutionDisputeHistoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_incidents(
    incidents: Sequence[ResearchResolutionDisputeHistoryIncident],
) -> tuple[ResearchResolutionDisputeHistoryIncident, ...]:
    if isinstance(incidents, (str, bytes)) or not isinstance(incidents, Sequence):
        raise ValueError("incidents must be a sequence")
    normalized = tuple(incidents)
    seen: set[tuple[str, str]] = set()
    for incident in normalized:
        if type(incident) is not ResearchResolutionDisputeHistoryIncident:
            raise ValueError("incidents must contain resolution dispute history incidents")
        _require_hard_flags("incident", incident)
        key = (incident.condition_id, incident.incident_id)
        if key in seen:
            raise ValueError("incidents must have unique condition and incident ids")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.condition_id, item.incident_id)))


def _normalize_rows(
    rows: Sequence[ResearchResolutionDisputeHistoryRow],
) -> tuple[ResearchResolutionDisputeHistoryRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchResolutionDisputeHistoryRow:
            raise ValueError("rows must contain resolution dispute history rows")
        _require_expected_digest(row)
        _require_hard_flags("row", row)
        key = (row.condition_id, row.incident_id)
        if key in seen:
            raise ValueError("rows must have unique condition and incident ids")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda row: (row.condition_id, row.incident_id)))


def _validate_config(config: ResearchResolutionDisputeHistoryConfig) -> None:
    if config.watch_dispute_frequency >= config.block_dispute_frequency:
        raise ValueError("watch_dispute_frequency must be below block_dispute_frequency")
    if config.watch_rule_ambiguity >= config.block_rule_ambiguity:
        raise ValueError("watch_rule_ambiguity must be below block_rule_ambiguity")
    if config.watch_evidence_dependency >= config.block_evidence_dependency:
        raise ValueError("watch_evidence_dependency must be below block_evidence_dependency")
    if config.pass_risk_score_ceiling >= config.block_risk_score_floor:
        raise ValueError("pass_risk_score_ceiling must be below block_risk_score_floor")
    weight_sum = _quantize_ratio(
        config.dispute_frequency_weight
        + config.rule_ambiguity_weight
        + config.evidence_dependency_weight
        + config.retrospective_weight,
    )
    if weight_sum != _ONE_RATIO:
        raise ValueError("risk weights must sum to one")


def _validate_incident(incident: ResearchResolutionDisputeHistoryIncident) -> None:
    if incident.dispute_count > incident.settlement_count:
        raise ValueError("dispute_count must not exceed settlement_count")
    if incident.ambiguous_rule_count > incident.dispute_count:
        raise ValueError("ambiguous_rule_count must not exceed dispute_count")
    if incident.independent_evidence_family_count > incident.evidence_family_count:
        raise ValueError(
            "independent_evidence_family_count must not exceed evidence_family_count",
        )


def _validate_row(row: ResearchResolutionDisputeHistoryRow) -> None:
    if row.dispute_frequency != _ratio(row.dispute_count, row.settlement_count):
        raise ValueError("dispute_frequency must match counts")
    if row.rule_ambiguity_ratio != _ratio(row.ambiguous_rule_count, row.dispute_count):
        raise ValueError("rule_ambiguity_ratio must match counts")
    if row.dispute_count > row.settlement_count:
        raise ValueError("dispute_count must not exceed settlement_count")
    if row.ambiguous_rule_count > row.dispute_count:
        raise ValueError("ambiguous_rule_count must not exceed dispute_count")
    if row.independent_evidence_family_count > row.evidence_family_count:
        raise ValueError(
            "independent_evidence_family_count must not exceed evidence_family_count",
        )
    if row.status == "pass" and "resolution_dispute_history_pass" not in row.reason_codes:
        raise ValueError("pass rows must include pass reason code")
    if row.status == "watch" and "resolution_dispute_history_watch" not in row.reason_codes:
        raise ValueError("watch rows must include watch reason code")
    if row.status == "block" and "resolution_dispute_history_block" not in row.reason_codes:
        raise ValueError("block rows must include block reason code")


def _validate_report(report: ResearchResolutionDisputeHistoryReport) -> None:
    if report.incident_count != _count(len(report.rows)):
        raise ValueError("incident_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.high_risk_layer_count != _count(sum(1 for row in report.rows if row.risk_layer == "high")):
        raise ValueError("high_risk_layer_count must match rows")
    if report.average_dispute_frequency != _average(tuple(row.dispute_frequency for row in report.rows)):
        raise ValueError("average_dispute_frequency must match rows")
    if report.average_rule_ambiguity_ratio != _average(
        tuple(row.rule_ambiguity_ratio for row in report.rows),
    ):
        raise ValueError("average_rule_ambiguity_ratio must match rows")
    if report.average_evidence_dependency_score != _average(
        tuple(row.evidence_dependency_score for row in report.rows),
    ):
        raise ValueError("average_evidence_dependency_score must match rows")
    if report.average_retrospective_risk_score != _average(
        tuple(row.retrospective_risk_score for row in report.rows),
    ):
        raise ValueError("average_retrospective_risk_score must match rows")
    if report.average_risk_score != _average(tuple(row.risk_score for row in report.rows)):
        raise ValueError("average_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_expected_digest(
    value: ResearchResolutionDisputeHistoryRow | ResearchResolutionDisputeHistoryReport,
) -> None:
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest mismatch")


def _derived_digest(
    value: ResearchResolutionDisputeHistoryRow | ResearchResolutionDisputeHistoryReport,
) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or type(value) is str:
        return value
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError("value is not JSON serializable")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in _PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered:
            raise ValueError(f"unsafe public field in {path}: {key}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"unsafe public value in {label}")
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered:
            raise ValueError(f"unsafe public value in {label}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(_COUNT_QUANTUM)
    if decimal_value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(
        _RATIO_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < _ZERO_RATIO or decimal_value > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    return _quantize_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return _quantize_ratio(sum(values, _ZERO_RATIO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize_ratio(value)
    if quantized < _ZERO_RATIO:
        return _ZERO_RATIO
    if quantized > _ONE_RATIO:
        return _ONE_RATIO
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported_codes:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported_codes if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_DISPUTE_HISTORY_REPORT_CONFIG_VERSION",
    "ResearchResolutionDisputeHistoryConfig",
    "ResearchResolutionDisputeHistoryIncident",
    "ResearchResolutionDisputeHistoryReport",
    "ResearchResolutionDisputeHistoryRow",
    "build_research_resolution_dispute_history_report",
    "research_resolution_dispute_history_report_payload",
)
