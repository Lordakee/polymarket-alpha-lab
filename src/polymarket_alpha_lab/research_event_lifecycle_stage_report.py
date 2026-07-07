"""Read-only research report for event lifecycle stage readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_LIFECYCLE_STAGE_CONFIG_VERSION = (
    "research-event-lifecycle-stage-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")

LIFECYCLE_STAGES = (
    "discovery",
    "evidence_collection",
    "conflict_validation",
    "near_settlement",
    "postmortem",
)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
STAGE_SORT_WEIGHT = {
    "conflict_validation": Decimal("0"),
    "near_settlement": Decimal("1"),
    "evidence_collection": Decimal("2"),
    "discovery": Decimal("3"),
    "postmortem": Decimal("4"),
}

ROW_REASON_CODES = (
    "lifecycle_stage_clear",
    "missing_primary_source",
    "insufficient_independent_sources",
    "incomplete_evidence",
    "weak_source_quality",
    "unresolved_conflict",
    "settlement_rule_unconfirmed",
    "settlement_window_imminent",
    "postmortem_missing",
    "postmortem_incomplete",
)
REPORT_REASON_CODES = (
    "lifecycle_report_empty",
    "lifecycle_report_clear",
    "lifecycle_block_present",
    "lifecycle_watch_present",
    "discovery_watch_present",
    "evidence_collection_watch_present",
    "conflict_validation_block_present",
    "near_settlement_block_present",
    "postmortem_watch_present",
)
NEXT_RESEARCH_ACTIONS = (
    "continue_stage_monitoring",
    "collect_primary_evidence",
    "catalog_public_sources",
    "resolve_source_conflict",
    "confirm_settlement_rules",
    "prepare_settlement_recheck",
    "write_postmortem_notes",
)

REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "event_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_stage_readiness_score",
    "min_stage_readiness_score",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "stage_readiness_score",
    "evidence_score",
    "source_quality_score",
    "conflict_score",
    "settlement_readiness_score",
    "postmortem_score",
    "seconds_until_settlement",
    "primary_source_count",
    "independent_source_count",
    "conflicting_source_count",
)
ROW_BOOL_PAYLOAD_FIELDS = (
    "settlement_rule_confirmed",
    "postmortem_completed",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "stage_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "event_id",
    "lifecycle_stage",
    "observed_at",
    "status",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    *ROW_BOOL_PAYLOAD_FIELDS,
    "next_research_actions",
    "reason_codes",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "trade",
    "mutation",
    "network",
    "database",
    "persist",
    "private_key",
    "secret",
    "token",
)


@dataclass(frozen=True)
class ResearchEventLifecycleStageConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_LIFECYCLE_STAGE_CONFIG_VERSION
    minimum_evidence_score: Decimal = Decimal("0.700000")
    minimum_source_quality_score: Decimal = Decimal("0.700000")
    maximum_conflict_score: Decimal = Decimal("0.300000")
    block_conflict_score: Decimal = Decimal("0.750000")
    minimum_settlement_readiness_score: Decimal = Decimal("0.800000")
    minimum_postmortem_score: Decimal = Decimal("0.700000")
    minimum_independent_source_count: Decimal = Decimal("2")
    near_settlement_seconds_threshold: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventLifecycleStageConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_LIFECYCLE_STAGE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "minimum_evidence_score",
            "minimum_source_quality_score",
            "maximum_conflict_score",
            "block_conflict_score",
            "minimum_settlement_readiness_score",
            "minimum_postmortem_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_independent_source_count",
            _normalize_nonnegative_count(
                "minimum_independent_source_count",
                self.minimum_independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "near_settlement_seconds_threshold",
            _normalize_nonnegative_count(
                "near_settlement_seconds_threshold",
                self.near_settlement_seconds_threshold,
            ),
        )
        require_paper_only_flags("research event lifecycle stage config", self)
        if self.maximum_conflict_score >= self.block_conflict_score:
            raise ValueError("maximum_conflict_score must be below block_conflict_score")


@dataclass(frozen=True)
class ResearchEventLifecycleStageInput:
    event_id: str
    lifecycle_stage: str
    observed_at: datetime
    evidence_score: Decimal
    source_quality_score: Decimal
    conflict_score: Decimal
    settlement_readiness_score: Decimal
    postmortem_score: Decimal
    seconds_until_settlement: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    settlement_rule_confirmed: bool
    postmortem_completed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventLifecycleStageInput:
            raise ValueError("input must be exact")
        _require_canonical_string("event_id", self.event_id)
        _reject_unsafe_fragment("event_id", self.event_id)
        _require_member("lifecycle_stage", self.lifecycle_stage, LIFECYCLE_STAGES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_score",
            "source_quality_score",
            "conflict_score",
            "settlement_readiness_score",
            "postmortem_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seconds_until_settlement",
            "primary_source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("settlement_rule_confirmed", "postmortem_completed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        require_paper_only_flags("research event lifecycle stage input", self)


@dataclass(frozen=True)
class ResearchEventLifecycleStageRow:
    event_id: str
    lifecycle_stage: str
    observed_at: datetime
    status: str
    stage_readiness_score: Decimal
    evidence_score: Decimal
    source_quality_score: Decimal
    conflict_score: Decimal
    settlement_readiness_score: Decimal
    postmortem_score: Decimal
    seconds_until_settlement: Decimal
    primary_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    settlement_rule_confirmed: bool
    postmortem_completed: bool
    next_research_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventLifecycleStageRow:
            raise ValueError("row must be exact")
        _require_canonical_string("event_id", self.event_id)
        _reject_unsafe_fragment("event_id", self.event_id)
        _require_member("lifecycle_stage", self.lifecycle_stage, LIFECYCLE_STAGES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "stage_readiness_score",
            "evidence_score",
            "source_quality_score",
            "conflict_score",
            "settlement_readiness_score",
            "postmortem_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seconds_until_settlement",
            "primary_source_count",
            "independent_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("settlement_rule_confirmed", "postmortem_completed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "next_research_actions",
            _normalize_string_tuple(
                "next_research_actions",
                self.next_research_actions,
                NEXT_RESEARCH_ACTIONS,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        require_paper_only_flags("research event lifecycle stage row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventLifecycleStageReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_stage_readiness_score: Decimal
    min_stage_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    stage_rows: tuple[ResearchEventLifecycleStageRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventLifecycleStageReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_LIFECYCLE_STAGE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_stage_readiness_score",
            "min_stage_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_score(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "stage_rows", _normalize_rows(self.stage_rows))
        require_paper_only_flags("research event lifecycle stage report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("research event lifecycle stage report", self)
        _validate_report_derived_validation_digest(self)


def build_research_event_lifecycle_stage_report(
    inputs: list[ResearchEventLifecycleStageInput]
    | tuple[ResearchEventLifecycleStageInput, ...],
    *,
    config: ResearchEventLifecycleStageConfig,
    generated_at: datetime,
) -> ResearchEventLifecycleStageReport:
    if type(config) is not ResearchEventLifecycleStageConfig:
        raise ValueError("config must be a ResearchEventLifecycleStageConfig")
    require_paper_only_flags("research event lifecycle stage config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _stage_row(row, config=config)
                for row in _normalize_inputs(inputs, generated_at)
            ),
            key=_row_sort_key,
        ),
    )
    event_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    average_score = _average_score(row.stage_readiness_score for row in rows)
    min_score = _min_score(row.stage_readiness_score for row in rows)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    digest = _derived_validation_digest(
        _report_payload_without_digest_values(
            generated_at=generated_at,
            config_version=config.config_version,
            event_count=event_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            average_stage_readiness_score=average_score,
            min_stage_readiness_score=min_score,
            status=status,
            reason_codes=reason_codes,
            stage_rows=rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )
    return ResearchEventLifecycleStageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_stage_readiness_score=average_score,
        min_stage_readiness_score=min_score,
        status=status,
        reason_codes=reason_codes,
        stage_rows=rows,
        derived_validation_digest=digest,
    )


def research_event_lifecycle_stage_report_payload(
    report: ResearchEventLifecycleStageReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventLifecycleStageReport:
        require_paper_only_flags("research event lifecycle stage report", report)
        _reject_unsafe_public_payload("research event lifecycle stage report", report)
        payload = _report_payload(report)
    elif type(report) is dict:
        _validate_public_payload(report)
        _reject_unsafe_public_payload("research event lifecycle stage payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchEventLifecycleStageReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags("research event lifecycle stage payload", _DictFlags(payload))
    return payload


def require_paper_only_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


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


def _normalize_inputs(
    values: list[ResearchEventLifecycleStageInput]
    | tuple[ResearchEventLifecycleStageInput, ...],
    generated_at: datetime,
) -> tuple[ResearchEventLifecycleStageInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(values)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventLifecycleStageInput:
            raise ValueError("inputs must contain ResearchEventLifecycleStageInput values")
        require_paper_only_flags("research event lifecycle stage input", row)
        if row.event_id in seen:
            raise ValueError("duplicate event_id values are not allowed")
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        seen.add(row.event_id)
    return rows


def _stage_row(
    source: ResearchEventLifecycleStageInput,
    *,
    config: ResearchEventLifecycleStageConfig,
) -> ResearchEventLifecycleStageRow:
    reason_codes = _row_reason_codes(source, config=config)
    return ResearchEventLifecycleStageRow(
        event_id=source.event_id,
        lifecycle_stage=source.lifecycle_stage,
        observed_at=source.observed_at,
        status=_row_status(source, config=config, reason_codes=reason_codes),
        stage_readiness_score=_stage_readiness_score(source),
        evidence_score=source.evidence_score,
        source_quality_score=source.source_quality_score,
        conflict_score=source.conflict_score,
        settlement_readiness_score=source.settlement_readiness_score,
        postmortem_score=source.postmortem_score,
        seconds_until_settlement=source.seconds_until_settlement,
        primary_source_count=source.primary_source_count,
        independent_source_count=source.independent_source_count,
        conflicting_source_count=source.conflicting_source_count,
        settlement_rule_confirmed=source.settlement_rule_confirmed,
        postmortem_completed=source.postmortem_completed,
        next_research_actions=_next_research_actions(source, config=config),
        reason_codes=reason_codes,
    )


def _stage_readiness_score(source: ResearchEventLifecycleStageInput) -> Decimal:
    if source.lifecycle_stage == "discovery":
        return source.source_quality_score
    if source.lifecycle_stage == "evidence_collection":
        return _average_score((source.evidence_score, source.source_quality_score))
    if source.lifecycle_stage == "conflict_validation":
        return _normalize_probability_score("stage_readiness_score", ONE_SCORE - source.conflict_score)
    if source.lifecycle_stage == "near_settlement":
        return source.settlement_readiness_score
    if source.lifecycle_stage == "postmortem":
        return source.postmortem_score
    raise ValueError("lifecycle_stage must contain known values")


def _row_status(
    source: ResearchEventLifecycleStageInput,
    *,
    config: ResearchEventLifecycleStageConfig,
    reason_codes: tuple[str, ...],
) -> str:
    if reason_codes == ("lifecycle_stage_clear",):
        return "pass"
    if source.lifecycle_stage == "discovery":
        return "watch"
    if source.lifecycle_stage == "evidence_collection":
        return "block"
    if source.lifecycle_stage == "conflict_validation":
        if source.conflict_score >= config.block_conflict_score:
            return "block"
        return "watch"
    if source.lifecycle_stage == "near_settlement":
        if not source.settlement_rule_confirmed:
            return "block"
        if source.settlement_readiness_score < config.minimum_settlement_readiness_score:
            return "watch"
        return "watch"
    if source.lifecycle_stage == "postmortem":
        return "watch"
    raise ValueError("lifecycle_stage must contain known values")


def _row_reason_codes(
    source: ResearchEventLifecycleStageInput,
    *,
    config: ResearchEventLifecycleStageConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if source.primary_source_count == ZERO_COUNT:
        codes.append("missing_primary_source")
    if source.independent_source_count < config.minimum_independent_source_count:
        codes.append("insufficient_independent_sources")
    if source.source_quality_score < config.minimum_source_quality_score:
        codes.append("weak_source_quality")
    if (
        source.lifecycle_stage == "evidence_collection"
        and source.evidence_score < config.minimum_evidence_score
    ):
        codes.append("incomplete_evidence")
    if (
        source.lifecycle_stage == "conflict_validation"
        and source.conflict_score > config.maximum_conflict_score
    ) or source.conflicting_source_count > ZERO_COUNT:
        codes.append("unresolved_conflict")
    if source.lifecycle_stage == "near_settlement":
        if not source.settlement_rule_confirmed:
            codes.append("settlement_rule_unconfirmed")
        if source.seconds_until_settlement <= config.near_settlement_seconds_threshold:
            codes.append("settlement_window_imminent")
    if source.lifecycle_stage == "postmortem":
        if not source.postmortem_completed:
            codes.append("postmortem_missing")
        if source.postmortem_score < config.minimum_postmortem_score:
            codes.append("postmortem_incomplete")
    return _stable_reason_codes(tuple(codes)) if codes else ("lifecycle_stage_clear",)


def _next_research_actions(
    source: ResearchEventLifecycleStageInput,
    *,
    config: ResearchEventLifecycleStageConfig,
) -> tuple[str, ...]:
    actions: list[str] = []
    if source.primary_source_count == ZERO_COUNT:
        actions.append("collect_primary_evidence")
    if (
        source.independent_source_count < config.minimum_independent_source_count
        or source.source_quality_score < config.minimum_source_quality_score
        or (
            source.lifecycle_stage == "evidence_collection"
            and source.evidence_score < config.minimum_evidence_score
        )
    ):
        actions.append("catalog_public_sources")
    if (
        source.lifecycle_stage == "conflict_validation"
        and source.conflict_score > config.maximum_conflict_score
    ) or source.conflicting_source_count > ZERO_COUNT:
        actions.append("resolve_source_conflict")
    if source.lifecycle_stage == "near_settlement":
        if not source.settlement_rule_confirmed:
            actions.append("confirm_settlement_rules")
        if source.seconds_until_settlement <= config.near_settlement_seconds_threshold:
            actions.append("prepare_settlement_recheck")
    if (
        source.lifecycle_stage == "postmortem"
        and (not source.postmortem_completed or source.postmortem_score < config.minimum_postmortem_score)
    ):
        actions.append("write_postmortem_notes")
    return _stable_actions(tuple(actions)) if actions else ("continue_stage_monitoring",)


def _validate_row(row: ResearchEventLifecycleStageRow) -> None:
    if row.reason_codes == ("lifecycle_stage_clear",):
        if row.next_research_actions != ("continue_stage_monitoring",):
            raise ValueError("clear rows must continue stage monitoring")
        if row.status != "pass":
            raise ValueError("clear rows must pass")
    elif row.next_research_actions == ("continue_stage_monitoring",):
        raise ValueError("flagged rows must include research actions")
    if row.reason_codes != _stable_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must be deterministic")
    if row.next_research_actions != _stable_actions(row.next_research_actions):
        raise ValueError("next_research_actions must be deterministic")


def _validate_report(report: ResearchEventLifecycleStageReport) -> None:
    if report.event_count != _count(len(report.stage_rows)):
        raise ValueError("event_count must match stage_rows")
    if report.pass_count != _status_count(report.stage_rows, "pass"):
        raise ValueError("pass_count must match stage_rows")
    if report.watch_count != _status_count(report.stage_rows, "watch"):
        raise ValueError("watch_count must match stage_rows")
    if report.block_count != _status_count(report.stage_rows, "block"):
        raise ValueError("block_count must match stage_rows")
    if report.event_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must sum to event_count")
    if report.average_stage_readiness_score != _average_score(
        row.stage_readiness_score for row in report.stage_rows
    ):
        raise ValueError("average_stage_readiness_score must match stage_rows")
    if report.min_stage_readiness_score != _min_score(
        row.stage_readiness_score for row in report.stage_rows
    ):
        raise ValueError("min_stage_readiness_score must match stage_rows")
    if report.status != _report_status(report.stage_rows):
        raise ValueError("status must match stage_rows")
    if report.reason_codes != _report_reason_codes(report.stage_rows):
        raise ValueError("reason_codes must match stage_rows")
    if report.stage_rows != tuple(sorted(report.stage_rows, key=_row_sort_key)):
        raise ValueError("stage_rows must use deterministic sequence")


def _validate_report_derived_validation_digest(
    report: ResearchEventLifecycleStageReport,
) -> None:
    _require_digest_string("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match derived report values")


def _report_status(rows: tuple[ResearchEventLifecycleStageRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventLifecycleStageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("lifecycle_report_empty",)
    if all(row.status == "pass" for row in rows):
        return ("lifecycle_report_clear",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("lifecycle_block_present")
    if any(row.status == "watch" for row in rows):
        codes.append("lifecycle_watch_present")
    if any(row.lifecycle_stage == "discovery" and row.status != "pass" for row in rows):
        codes.append("discovery_watch_present")
    if any(
        row.lifecycle_stage == "evidence_collection" and row.status != "pass"
        for row in rows
    ):
        codes.append("evidence_collection_watch_present")
    if any(
        row.lifecycle_stage == "conflict_validation" and row.status == "block"
        for row in rows
    ):
        codes.append("conflict_validation_block_present")
    if any(
        row.lifecycle_stage == "near_settlement" and row.status == "block"
        for row in rows
    ):
        codes.append("near_settlement_block_present")
    if any(row.lifecycle_stage == "postmortem" and row.status != "pass" for row in rows):
        codes.append("postmortem_watch_present")
    return tuple(codes)


def _row_sort_key(
    row: ResearchEventLifecycleStageRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        STAGE_SORT_WEIGHT[row.lifecycle_stage],
        row.stage_readiness_score,
        row.event_id,
    )


def _status_count(rows: tuple[ResearchEventLifecycleStageRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int) -> Decimal:
    return _normalize_nonnegative_count("count", Decimal(value))


def _average_score(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability_score(
            "average_stage_readiness_score",
            sum(items, ZERO_SCORE) / Decimal(len(items)),
        )


def _min_score(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_SCORE
    return min(items)


def _normalize_rows(value: object) -> tuple[ResearchEventLifecycleStageRow, ...]:
    if type(value) is not tuple:
        raise ValueError("stage_rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventLifecycleStageRow:
            raise ValueError("stage_rows must contain ResearchEventLifecycleStageRow values")
        require_paper_only_flags("research event lifecycle stage row", row)
        if row.event_id in seen:
            raise ValueError("duplicate event_id values are not allowed")
        seen.add(row.event_id)
    return rows


def _normalize_string_tuple(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    for value in normalized:
        _require_canonical_string(field_name, value)
        _reject_unsafe_fragment(field_name, value)
        if value not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    ordered = tuple(value for value in allowed if value in normalized)
    if ordered != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _stable_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value for value in ROW_REASON_CODES if value in values)


def _stable_actions(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value for value in NEXT_RESEARCH_ACTIONS if value in values)


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_RESEARCH_EVENT_LIFECYCLE_STAGE_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], STATUSES)
    _normalize_string_tuple("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    if type(payload["stage_rows"]) is not list:
        raise ValueError("stage_rows must be a list")
    for row in payload["stage_rows"]:
        _validate_public_row_payload(row)
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")
    _reject_public_numerics(payload)


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("stage_rows must contain JSON objects")
    _reject_unsafe_public_payload("stage row payload", value)
    _reject_unknown_payload_keys("stage row payload", value, ROW_PAYLOAD_KEYS)
    _require_canonical_string("event_id", value["event_id"])
    _require_member("lifecycle_stage", value["lifecycle_stage"], LIFECYCLE_STAGES)
    _require_canonical_string("observed_at", value["observed_at"])
    _require_member("status", value["status"], STATUSES)
    for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in ROW_BOOL_PAYLOAD_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_string_tuple(
        "next_research_actions",
        value["next_research_actions"],
        NEXT_RESEARCH_ACTIONS,
    )
    _normalize_string_tuple("reason_codes", value["reason_codes"], ROW_REASON_CODES)


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _report_payload(report: ResearchEventLifecycleStageReport) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "event_count": payload["event_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "average_stage_readiness_score": payload["average_stage_readiness_score"],
        "min_stage_readiness_score": payload["min_stage_readiness_score"],
        "status": payload["status"],
        "reason_codes": payload["reason_codes"],
        "stage_rows": payload["stage_rows"],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_payload_without_digest(
    report: ResearchEventLifecycleStageReport,
) -> dict[str, Any]:
    return _report_payload_without_digest_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_stage_readiness_score=report.average_stage_readiness_score,
        min_stage_readiness_score=report.min_stage_readiness_score,
        status=report.status,
        reason_codes=report.reason_codes,
        stage_rows=report.stage_rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_payload_without_digest_values(
    *,
    generated_at: datetime,
    config_version: str,
    event_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_stage_readiness_score: Decimal,
    min_stage_readiness_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    stage_rows: tuple[ResearchEventLifecycleStageRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": generated_at,
        "config_version": config_version,
        "event_count": event_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_stage_readiness_score": average_stage_readiness_score,
        "min_stage_readiness_score": min_stage_readiness_score,
        "status": status,
        "reason_codes": reason_codes,
        "stage_rows": tuple(_row_payload(row) for row in stage_rows),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ready


def _row_payload(row: ResearchEventLifecycleStageRow) -> dict[str, Any]:
    payload = {
        "event_id": row.event_id,
        "lifecycle_stage": row.lifecycle_stage,
        "observed_at": row.observed_at,
        "status": row.status,
        "stage_readiness_score": row.stage_readiness_score,
        "evidence_score": row.evidence_score,
        "source_quality_score": row.source_quality_score,
        "conflict_score": row.conflict_score,
        "settlement_readiness_score": row.settlement_readiness_score,
        "postmortem_score": row.postmortem_score,
        "seconds_until_settlement": row.seconds_until_settlement,
        "primary_source_count": row.primary_source_count,
        "independent_source_count": row.independent_source_count,
        "conflicting_source_count": row.conflicting_source_count,
        "settlement_rule_confirmed": row.settlement_rule_confirmed,
        "postmortem_completed": row.postmortem_completed,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
        "next_research_actions": row.next_research_actions,
        "reason_codes": row.reason_codes,
    }
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("row payload must be a JSON object")
    return ready


def _report_derived_validation_digest(
    report: ResearchEventLifecycleStageReport,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    return _derived_validation_digest(without_digest)


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _decimal_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(COUNT_QUANTUM))
    return str(_normalize_decimal("decimal", value, SCORE_QUANTUM))


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must contain known values")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _normalize_probability_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO_SCORE or normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != Decimal(value):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)
