"""Report-only Phase 1 team research readiness dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_memory_quality_gate import TeamMemoryQualityGateResult
from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_research_calibration_snapshot import (
    TeamResearchCalibrationSnapshotReport,
)
from polymarket_alpha_lab.team_research_coverage_map import TeamResearchCoverageMapReport
from polymarket_alpha_lab.team_research_handoff import (
    TeamResearchHandoffSummary,
    team_research_handoff_payload,
)
from polymarket_alpha_lab.team_source_reliability import TeamSourceReliabilityReport


DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION = (
    "team-research-readiness-dashboard-v0"
)

COMPONENTS = (
    "calibration",
    "coverage",
    "handoff",
    "quality_gate",
    "source_reliability",
)
READINESS_STATUSES = ("research_ready", "needs_review", "blocked")
REASON_CODES = (
    "dashboard_memory_ready",
    "dashboard_memory_needs_review",
    "dashboard_memory_blocked",
    "dashboard_memory_empty",
    "dashboard_source_reliability_ready",
    "dashboard_source_reliability_needs_review",
    "dashboard_source_reliability_missing",
    "dashboard_handoffs_ready",
    "dashboard_handoffs_need_review",
    "dashboard_handoffs_blocked",
    "dashboard_handoffs_empty",
    "dashboard_calibration_ready",
    "dashboard_calibration_stale_unresolved",
    "dashboard_coverage_ready",
    "dashboard_coverage_gaps_present",
    "dashboard_coverage_blocked",
)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class TeamResearchReadinessDashboardConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamResearchReadinessDashboardConfig", self)


@dataclass(frozen=True)
class TeamResearchReadinessDashboardRow:
    component: str
    subject_id: str
    readiness_status: str
    generated_at: datetime
    item_count: int
    watch_count: int
    blocked_count: int
    readiness_score: Decimal | None
    redacted_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("component", self.component, COMPONENTS)
        _require_canonical_string("subject_id", self.subject_id)
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("item_count", "watch_count", "blocked_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.watch_count > self.item_count:
            raise ValueError("watch_count must not exceed item_count")
        if self.blocked_count > self.item_count:
            raise ValueError("blocked_count must not exceed item_count")
        object.__setattr__(
            self,
            "readiness_score",
            _normalize_optional_ratio("readiness_score", self.readiness_score),
        )
        object.__setattr__(
            self,
            "redacted_refs",
            _normalize_redacted_refs(self.redacted_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        require_paper_only_flags("TeamResearchReadinessDashboardRow", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(
                    component=self.component,
                    subject_id=self.subject_id,
                    readiness_status=self.readiness_status,
                    generated_at=self.generated_at,
                    item_count=self.item_count,
                    watch_count=self.watch_count,
                    blocked_count=self.blocked_count,
                    readiness_score=self.readiness_score,
                    redacted_refs=self.redacted_refs,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


@dataclass(frozen=True)
class TeamResearchReadinessDashboardReport:
    generated_at: datetime
    config_version: str
    dashboard_status: str
    component_count: int
    research_ready_component_count: int
    needs_review_component_count: int
    blocked_component_count: int
    readiness_ratio: Decimal | None
    needs_review_ratio: Decimal | None
    blocked_ratio: Decimal | None
    memory_quality_gate_count: int
    memory_quality_gate_research_ready_count: int
    memory_quality_gate_needs_review_count: int
    memory_quality_gate_blocked_count: int
    source_reliability_row_count: int
    source_reliability_watch_count: int
    source_reliability_blocked_count: int
    handoff_count: int
    handoff_watch_count: int
    handoff_blocked_count: int
    calibration_outcome_count: int
    calibration_stale_unresolved_count: int
    coverage_observation_count: int
    coverage_gap_count: int
    coverage_blocked_count: int
    rows: tuple[TeamResearchReadinessDashboardRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("dashboard_status", self.dashboard_status, READINESS_STATUSES)
        for field_name in (
            "component_count",
            "research_ready_component_count",
            "needs_review_component_count",
            "blocked_component_count",
            "memory_quality_gate_count",
            "memory_quality_gate_research_ready_count",
            "memory_quality_gate_needs_review_count",
            "memory_quality_gate_blocked_count",
            "source_reliability_row_count",
            "source_reliability_watch_count",
            "source_reliability_blocked_count",
            "handoff_count",
            "handoff_watch_count",
            "handoff_blocked_count",
            "calibration_outcome_count",
            "calibration_stale_unresolved_count",
            "coverage_observation_count",
            "coverage_gap_count",
            "coverage_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in ("readiness_ratio", "needs_review_ratio", "blocked_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_dashboard_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("TeamResearchReadinessDashboardReport", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(
                    generated_at=self.generated_at,
                    config_version=self.config_version,
                    dashboard_status=self.dashboard_status,
                    component_count=self.component_count,
                    research_ready_component_count=self.research_ready_component_count,
                    needs_review_component_count=self.needs_review_component_count,
                    blocked_component_count=self.blocked_component_count,
                    readiness_ratio=self.readiness_ratio,
                    needs_review_ratio=self.needs_review_ratio,
                    blocked_ratio=self.blocked_ratio,
                    memory_quality_gate_count=self.memory_quality_gate_count,
                    memory_quality_gate_research_ready_count=(
                        self.memory_quality_gate_research_ready_count
                    ),
                    memory_quality_gate_needs_review_count=(
                        self.memory_quality_gate_needs_review_count
                    ),
                    memory_quality_gate_blocked_count=(
                        self.memory_quality_gate_blocked_count
                    ),
                    source_reliability_row_count=self.source_reliability_row_count,
                    source_reliability_watch_count=self.source_reliability_watch_count,
                    source_reliability_blocked_count=self.source_reliability_blocked_count,
                    handoff_count=self.handoff_count,
                    handoff_watch_count=self.handoff_watch_count,
                    handoff_blocked_count=self.handoff_blocked_count,
                    calibration_outcome_count=self.calibration_outcome_count,
                    calibration_stale_unresolved_count=(
                        self.calibration_stale_unresolved_count
                    ),
                    coverage_observation_count=self.coverage_observation_count,
                    coverage_gap_count=self.coverage_gap_count,
                    coverage_blocked_count=self.coverage_blocked_count,
                    rows=self.rows,
                    reason_codes=self.reason_codes,
                ),
            ),
        )


def build_team_research_readiness_dashboard(
    *,
    quality_gates: list[TeamMemoryQualityGateResult]
    | tuple[TeamMemoryQualityGateResult, ...],
    source_reliability_report: TeamSourceReliabilityReport | None,
    handoff_summary: TeamResearchHandoffSummary,
    calibration_snapshot: TeamResearchCalibrationSnapshotReport,
    coverage_map: TeamResearchCoverageMapReport,
    config: TeamResearchReadinessDashboardConfig,
    generated_at: datetime,
) -> TeamResearchReadinessDashboardReport:
    if type(config) is not TeamResearchReadinessDashboardConfig:
        raise ValueError("config must be a TeamResearchReadinessDashboardConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_quality_gates = _normalize_quality_gates(quality_gates)
    normalized_source_reliability_report = _normalize_source_reliability_report(
        source_reliability_report,
    )
    if type(handoff_summary) is not TeamResearchHandoffSummary:
        raise ValueError("handoff_summary must be a TeamResearchHandoffSummary")
    if type(calibration_snapshot) is not TeamResearchCalibrationSnapshotReport:
        raise ValueError(
            "calibration_snapshot must be a TeamResearchCalibrationSnapshotReport",
        )
    if type(coverage_map) is not TeamResearchCoverageMapReport:
        raise ValueError("coverage_map must be a TeamResearchCoverageMapReport")
    for label, value in (
        ("handoff_summary", handoff_summary),
        ("calibration_snapshot", calibration_snapshot),
        ("coverage_map", coverage_map),
    ):
        require_paper_only_flags(label, value)

    rows = _dashboard_rows(
        quality_gates=normalized_quality_gates,
        source_reliability_report=normalized_source_reliability_report,
        handoff_summary=handoff_summary,
        calibration_snapshot=calibration_snapshot,
        coverage_map=coverage_map,
    )
    reason_codes = _dashboard_reason_codes(
        quality_gates=normalized_quality_gates,
        source_reliability_report=normalized_source_reliability_report,
        handoff_summary=handoff_summary,
        calibration_snapshot=calibration_snapshot,
        coverage_map=coverage_map,
    )
    research_ready_component_count = sum(
        1 for row in _component_rows(rows) if row.readiness_status == "research_ready"
    )
    needs_review_component_count = sum(
        1 for row in _component_rows(rows) if row.readiness_status == "needs_review"
    )
    blocked_component_count = sum(
        1 for row in _component_rows(rows) if row.readiness_status == "blocked"
    )
    component_count = (
        research_ready_component_count
        + needs_review_component_count
        + blocked_component_count
    )

    return TeamResearchReadinessDashboardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        dashboard_status=_dashboard_status(rows),
        component_count=component_count,
        research_ready_component_count=research_ready_component_count,
        needs_review_component_count=needs_review_component_count,
        blocked_component_count=blocked_component_count,
        readiness_ratio=_ratio_or_none(research_ready_component_count, component_count),
        needs_review_ratio=_ratio_or_none(needs_review_component_count, component_count),
        blocked_ratio=_ratio_or_none(blocked_component_count, component_count),
        memory_quality_gate_count=len(normalized_quality_gates),
        memory_quality_gate_research_ready_count=_quality_gate_status_count(
            normalized_quality_gates,
            "research_ready",
        ),
        memory_quality_gate_needs_review_count=_quality_gate_status_count(
            normalized_quality_gates,
            "needs_review",
        ),
        memory_quality_gate_blocked_count=_quality_gate_status_count(
            normalized_quality_gates,
            "blocked",
        ),
        source_reliability_row_count=(
            0
            if normalized_source_reliability_report is None
            else _as_nonnegative_count_int(
                "source_reliability_row_count",
                normalized_source_reliability_report.row_count,
            )
        ),
        source_reliability_watch_count=_source_reliability_watch_count(
            normalized_source_reliability_report,
        ),
        source_reliability_blocked_count=0,
        handoff_count=_as_nonnegative_count_int(
            "handoff_count",
            handoff_summary.handoff_count,
        ),
        handoff_watch_count=_as_nonnegative_count_int(
            "handoff_watch_count",
            handoff_summary.watch_count,
        ),
        handoff_blocked_count=_as_nonnegative_count_int(
            "handoff_blocked_count",
            handoff_summary.blocked_count,
        ),
        calibration_outcome_count=_as_nonnegative_count_int(
            "calibration_outcome_count",
            calibration_snapshot.outcome_count,
        ),
        calibration_stale_unresolved_count=_as_nonnegative_count_int(
            "calibration_stale_unresolved_count",
            calibration_snapshot.stale_unresolved_count,
        ),
        coverage_observation_count=_as_nonnegative_count_int(
            "coverage_observation_count",
            coverage_map.observation_count,
        ),
        coverage_gap_count=_coverage_gap_count(coverage_map),
        coverage_blocked_count=_coverage_blocked_count(coverage_map),
        rows=rows,
        reason_codes=reason_codes,
    )


def team_research_readiness_dashboard_payload(
    report: TeamResearchReadinessDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not TeamResearchReadinessDashboardReport:
        if type(report) is not dict:
            raise ValueError("report must be a TeamResearchReadinessDashboardReport")
        _reject_unsafe_public_payload("team research readiness dashboard payload", report)
        payload = _json_ready_public_payload(report, allow_int=False)
    else:
        _validate_report_runtime(report)
        _reject_unsafe_public_payload("team research readiness dashboard report", report)
        payload = _json_ready_public_payload(asdict(report), allow_int=True)
    if type(payload) is not dict:
        raise ValueError("dashboard payload must be a JSON object")
    _reject_unsafe_public_payload("team research readiness dashboard payload", payload)
    _require_payload_flags(payload)
    _validate_payload_digest(payload)
    return _redact_sensitive_payload(payload)


def _redacted_handoff_payloads(
    summary: TeamResearchHandoffSummary,
) -> dict[str, dict[str, Any]]:
    payload = team_research_handoff_payload(summary)
    items = payload.get("items")
    if not isinstance(items, list):
        return {}
    redacted_by_subject: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        source_team_id = item.get("source_team_id")
        target_team_id = item.get("target_team_id")
        if type(source_team_id) is str and type(target_team_id) is str:
            redacted_by_subject[f"{source_team_id}>{target_team_id}"] = item
    return redacted_by_subject


def _redacted_handoff_payload_ref(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return f"handoff_payload:<redacted>:{digest}"


def _dashboard_rows(
    *,
    quality_gates: tuple[TeamMemoryQualityGateResult, ...],
    source_reliability_report: TeamSourceReliabilityReport | None,
    handoff_summary: TeamResearchHandoffSummary,
    calibration_snapshot: TeamResearchCalibrationSnapshotReport,
    coverage_map: TeamResearchCoverageMapReport,
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    rows: list[TeamResearchReadinessDashboardRow] = []
    rows.extend(_calibration_rows(calibration_snapshot))
    rows.extend(_coverage_rows(coverage_map))
    rows.extend(_handoff_rows(handoff_summary))
    rows.extend(_quality_gate_rows(quality_gates))
    rows.extend(_source_reliability_rows(source_reliability_report))
    return tuple(sorted(rows, key=_row_sort_key))


def _calibration_rows(
    report: TeamResearchCalibrationSnapshotReport,
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    status = "needs_review" if report.stale_unresolved_count > 0 else "research_ready"
    reason_codes = (
        ("dashboard_calibration_stale_unresolved",)
        if report.stale_unresolved_count > 0
        else ("dashboard_calibration_ready",)
    )
    return (
        TeamResearchReadinessDashboardRow(
            component="calibration",
            subject_id="team-research-calibration",
            readiness_status=status,
            generated_at=report.generated_at,
            item_count=report.outcome_count,
            watch_count=report.stale_unresolved_count,
            blocked_count=0,
            readiness_score=_ratio_or_none(
                report.outcome_count - report.stale_unresolved_count,
                report.outcome_count,
            ),
            redacted_refs=tuple(
                f"calibration:{item.team_id}:{item.outcome_id}"
                for item in report.stale_unresolved_items
            )
            or ("calibration:all",),
            reason_codes=reason_codes,
        ),
    )


def _coverage_rows(
    report: TeamResearchCoverageMapReport,
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    gap_count = _coverage_gap_count(report)
    blocked_count = _coverage_blocked_count(report)
    if report.coverage_status == "blocked":
        status = "blocked"
    elif report.coverage_status == "watch":
        status = "needs_review"
    else:
        status = "research_ready"
    return (
        TeamResearchReadinessDashboardRow(
            component="coverage",
            subject_id="team-research-coverage",
            readiness_status=status,
            generated_at=report.generated_at,
            item_count=report.observation_count,
            watch_count=gap_count,
            blocked_count=blocked_count,
            readiness_score=_ratio_or_none(
                report.observation_count - gap_count - blocked_count,
                report.observation_count,
            ),
            redacted_refs=tuple(
                ref
                for row in report.coverage_rows
                for ref in row.redacted_public_identifiers
            )
            or ("coverage:empty",),
            reason_codes=_coverage_dashboard_reason_codes(report),
        ),
    )


def _handoff_rows(
    summary: TeamResearchHandoffSummary,
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    if summary.handoff_count == 0:
        return (
            TeamResearchReadinessDashboardRow(
                component="handoff",
                subject_id="team-research-handoffs",
                readiness_status="blocked",
                generated_at=summary.generated_at,
                item_count=0,
                watch_count=0,
                blocked_count=0,
                readiness_score=None,
                redacted_refs=("handoff:empty",),
                reason_codes=("dashboard_handoffs_empty",),
            ),
        )
    rows: list[TeamResearchReadinessDashboardRow] = []
    redacted_payloads = _redacted_handoff_payloads(summary)
    for item in summary.items:
        subject_id = f"{item.source_team_id}>{item.target_team_id}"
        if item.handoff_status == "blocked":
            status = "blocked"
        elif item.handoff_status == "watch":
            status = "needs_review"
        else:
            status = "research_ready"
        rows.append(
            TeamResearchReadinessDashboardRow(
                component="handoff",
                subject_id=subject_id,
                readiness_status=status,
                generated_at=item.updated_at,
                item_count=1,
                watch_count=1 if item.handoff_status == "watch" else 0,
                blocked_count=1 if item.handoff_status == "blocked" else 0,
                readiness_score=ONE if item.handoff_status == "ready" else ZERO,
                redacted_refs=(
                    f"handoff:{subject_id}",
                    _redacted_handoff_payload_ref(redacted_payloads.get(subject_id, {})),
                ),
                reason_codes=item.reason_codes,
            ),
        )
    return tuple(rows)


def _quality_gate_rows(
    quality_gates: tuple[TeamMemoryQualityGateResult, ...],
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    if not quality_gates:
        return (
            TeamResearchReadinessDashboardRow(
                component="quality_gate",
                subject_id="team-memory-quality-gates",
                readiness_status="blocked",
                generated_at=datetime.min.replace(tzinfo=UTC),
                item_count=0,
                watch_count=0,
                blocked_count=0,
                readiness_score=None,
                redacted_refs=("memory:empty",),
                reason_codes=("dashboard_memory_empty",),
            ),
        )
    rows: list[TeamResearchReadinessDashboardRow] = []
    for gate in quality_gates:
        rows.append(
            TeamResearchReadinessDashboardRow(
                component="quality_gate",
                subject_id=gate.redacted_memory_id,
                readiness_status=gate.gate_status,
                generated_at=gate.generated_at,
                item_count=gate.team_count,
                watch_count=_ratio_count(gate.watch_source_ratio, gate.team_count)
                + gate.stale_source_count
                + gate.current_watch_streak_count,
                blocked_count=_ratio_count(gate.blocked_source_ratio, gate.team_count)
                + gate.research_gap_count
                + gate.current_blocked_streak_count,
                readiness_score=gate.latest_quality_score,
                redacted_refs=(gate.redacted_memory_id,),
                reason_codes=gate.reason_codes,
            ),
        )
    return tuple(rows)


def _source_reliability_rows(
    report: TeamSourceReliabilityReport | None,
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    if report is None:
        return (
            TeamResearchReadinessDashboardRow(
                component="source_reliability",
                subject_id="team-source-reliability",
                readiness_status="blocked",
                generated_at=datetime.min.replace(tzinfo=UTC),
                item_count=0,
                watch_count=0,
                blocked_count=0,
                readiness_score=None,
                redacted_refs=("source:empty",),
                reason_codes=("dashboard_source_reliability_missing",),
            ),
        )
    if report.row_count == 0:
        return (
            TeamResearchReadinessDashboardRow(
                component="source_reliability",
                subject_id="team-source-reliability",
                readiness_status="blocked",
                generated_at=report.generated_at,
                item_count=0,
                watch_count=0,
                blocked_count=0,
                readiness_score=None,
                redacted_refs=("source:empty",),
                reason_codes=("dashboard_source_reliability_missing",),
            ),
        )
    rows: list[TeamResearchReadinessDashboardRow] = []
    for row in report.rows:
        is_watch = row.status == "source_reliability_watch"
        rows.append(
            TeamResearchReadinessDashboardRow(
                component="source_reliability",
                subject_id=f"{row.team_id}:{row.source_id}",
                readiness_status="needs_review" if is_watch else "research_ready",
                generated_at=row.latest_generated_at,
                item_count=row.evidence_count,
                watch_count=1 if is_watch else 0,
                blocked_count=0,
                readiness_score=row.reliability_score,
                redacted_refs=(f"source:{row.team_id}:{row.source_id}",),
                reason_codes=(f"{row.status}:{row.reliability_grade}",),
            ),
        )
    return tuple(rows)


def _dashboard_reason_codes(
    *,
    quality_gates: tuple[TeamMemoryQualityGateResult, ...],
    source_reliability_report: TeamSourceReliabilityReport | None,
    handoff_summary: TeamResearchHandoffSummary,
    calibration_snapshot: TeamResearchCalibrationSnapshotReport,
    coverage_map: TeamResearchCoverageMapReport,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(_memory_dashboard_reason_code(quality_gates))
    reason_codes.append(_source_reliability_dashboard_reason_code(source_reliability_report))
    reason_codes.append(_handoff_dashboard_reason_code(handoff_summary))
    reason_codes.append(_calibration_dashboard_reason_code(calibration_snapshot))
    reason_codes.extend(_coverage_dashboard_reason_codes(coverage_map))
    return tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code in reason_codes
        and reason_code not in {
            "dashboard_memory_ready",
            "dashboard_source_reliability_ready",
            "dashboard_handoffs_ready",
            "dashboard_calibration_ready",
            "dashboard_coverage_ready",
        }
    ) or (
        "dashboard_memory_ready",
        "dashboard_source_reliability_ready",
        "dashboard_handoffs_ready",
        "dashboard_calibration_ready",
        "dashboard_coverage_ready",
    )


def _memory_dashboard_reason_code(
    quality_gates: tuple[TeamMemoryQualityGateResult, ...],
) -> str:
    if not quality_gates:
        return "dashboard_memory_empty"
    if any(gate.gate_status == "blocked" for gate in quality_gates):
        return "dashboard_memory_blocked"
    if any(gate.gate_status == "needs_review" for gate in quality_gates):
        return "dashboard_memory_needs_review"
    return "dashboard_memory_ready"


def _source_reliability_dashboard_reason_code(
    report: TeamSourceReliabilityReport | None,
) -> str:
    if report is None or report.row_count == 0:
        return "dashboard_source_reliability_missing"
    if _source_reliability_watch_count(report) > 0:
        return "dashboard_source_reliability_needs_review"
    return "dashboard_source_reliability_ready"


def _handoff_dashboard_reason_code(summary: TeamResearchHandoffSummary) -> str:
    if summary.handoff_count == 0:
        return "dashboard_handoffs_empty"
    if summary.handoff_status == "blocked":
        return "dashboard_handoffs_blocked"
    if summary.handoff_status == "watch":
        return "dashboard_handoffs_need_review"
    return "dashboard_handoffs_ready"


def _calibration_dashboard_reason_code(
    report: TeamResearchCalibrationSnapshotReport,
) -> str:
    if report.stale_unresolved_count > 0:
        return "dashboard_calibration_stale_unresolved"
    return "dashboard_calibration_ready"


def _coverage_dashboard_reason_codes(
    report: TeamResearchCoverageMapReport,
) -> tuple[str, ...]:
    if report.coverage_status == "blocked":
        return ("dashboard_coverage_blocked",)
    if _coverage_gap_count(report) > 0:
        return ("dashboard_coverage_gaps_present",)
    return ("dashboard_coverage_ready",)


def _dashboard_status(rows: tuple[TeamResearchReadinessDashboardRow, ...]) -> str:
    component_rows = _component_rows(rows)
    if not component_rows:
        return "blocked"
    if any(row.readiness_status == "blocked" for row in component_rows):
        return "blocked"
    if any(row.readiness_status == "needs_review" for row in component_rows):
        return "needs_review"
    return "research_ready"


def _component_rows(
    rows: tuple[TeamResearchReadinessDashboardRow, ...],
) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    by_component: dict[str, TeamResearchReadinessDashboardRow] = {}
    for row in rows:
        current = by_component.get(row.component)
        if current is None:
            by_component[row.component] = row
            continue
        by_component[row.component] = _merge_component_row(current, row)
    return tuple(by_component[component] for component in sorted(by_component))


def _merge_component_row(
    first: TeamResearchReadinessDashboardRow,
    second: TeamResearchReadinessDashboardRow,
) -> TeamResearchReadinessDashboardRow:
    status = _merged_status(first.readiness_status, second.readiness_status)
    item_count = first.item_count + second.item_count
    watch_count = first.watch_count + second.watch_count
    blocked_count = first.blocked_count + second.blocked_count
    return TeamResearchReadinessDashboardRow(
        component=first.component,
        subject_id=f"{first.component}:component-summary",
        readiness_status=status,
        generated_at=max(first.generated_at, second.generated_at),
        item_count=item_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        readiness_score=_ratio_or_none(item_count - watch_count - blocked_count, item_count),
        redacted_refs=tuple(sorted(set(first.redacted_refs + second.redacted_refs))),
        reason_codes=tuple(dict.fromkeys(first.reason_codes + second.reason_codes)),
    )


def _merged_status(first: str, second: str) -> str:
    if "blocked" in (first, second):
        return "blocked"
    if "needs_review" in (first, second):
        return "needs_review"
    return "research_ready"


def _quality_gate_status_count(
    quality_gates: tuple[TeamMemoryQualityGateResult, ...],
    status: str,
) -> int:
    return sum(1 for gate in quality_gates if gate.gate_status == status)


def _source_reliability_watch_count(report: TeamSourceReliabilityReport | None) -> int:
    if report is None:
        return 0
    return sum(1 for row in report.rows if row.status == "source_reliability_watch")


def _coverage_gap_count(report: TeamResearchCoverageMapReport) -> int:
    return sum(row.observation_count for row in report.coverage_rows if row.evidence_status == "gap")


def _coverage_blocked_count(report: TeamResearchCoverageMapReport) -> int:
    return sum(
        row.observation_count
        for row in report.coverage_rows
        if row.evidence_status == "blocked"
    )


def _normalize_quality_gates(value: object) -> tuple[TeamMemoryQualityGateResult, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("quality_gates must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamMemoryQualityGateResult:
            raise ValueError("quality_gates must contain TeamMemoryQualityGateResult values")
        require_paper_only_flags("quality gate", row)
    return tuple(sorted(rows, key=lambda row: row.redacted_memory_id))


def _normalize_source_reliability_report(
    value: object,
) -> TeamSourceReliabilityReport | None:
    if value is None:
        return None
    if type(value) is not TeamSourceReliabilityReport:
        raise ValueError("source_reliability_report must be a TeamSourceReliabilityReport")
    require_paper_only_flags("source_reliability_report", value)
    return value


def _normalize_rows(value: object) -> tuple[TeamResearchReadinessDashboardRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[str, str] | None = None
    for row in rows:
        if type(row) is not TeamResearchReadinessDashboardRow:
            raise ValueError("rows must contain TeamResearchReadinessDashboardRow values")
        require_paper_only_flags("dashboard row", row)
        key = (row.component, row.subject_id)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be deterministic by component and subject_id")
        previous_key = key
    return rows


def _normalize_dashboard_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_string_tuple("reason_codes", value, allow_empty=False)
    for reason_code in reason_codes:
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain dashboard reason codes")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic reason sequence")
    return reason_codes


def _normalize_redacted_refs(value: object) -> tuple[str, ...]:
    refs = _normalize_string_tuple("redacted_refs", value, allow_empty=False)
    for ref in refs:
        if not (
            ref.startswith("memory:")
            or ref.startswith("public_id_sha256:")
            or ref.startswith("calibration:")
            or ref.startswith("coverage:")
            or ref.startswith("handoff:")
            or ref.startswith("handoff_payload:")
            or ref.startswith("source:")
        ):
            raise ValueError("redacted_refs must contain redacted refs")
    return refs


def _validate_report_consistency(report: TeamResearchReadinessDashboardReport) -> None:
    if report.component_count != (
        report.research_ready_component_count
        + report.needs_review_component_count
        + report.blocked_component_count
    ):
        raise ValueError("component_count must match component status counts")
    if report.component_count == 0:
        if (
            report.readiness_ratio is not None
            or report.needs_review_ratio is not None
            or report.blocked_ratio is not None
        ):
            raise ValueError("ratios must be absent without components")
    else:
        if report.readiness_ratio != _ratio_or_none(
            report.research_ready_component_count,
            report.component_count,
        ):
            raise ValueError("readiness_ratio must match component counts")
        if report.needs_review_ratio != _ratio_or_none(
            report.needs_review_component_count,
            report.component_count,
        ):
            raise ValueError("needs_review_ratio must match component counts")
        if report.blocked_ratio != _ratio_or_none(
            report.blocked_component_count,
            report.component_count,
        ):
            raise ValueError("blocked_ratio must match component counts")
    if report.dashboard_status != _dashboard_status(report.rows):
        raise ValueError("dashboard_status must match rows")


def _validate_report_runtime(report: TeamResearchReadinessDashboardReport) -> None:
    require_paper_only_flags("TeamResearchReadinessDashboardReport", report)
    _as_utc("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    _require_member("dashboard_status", report.dashboard_status, READINESS_STATUSES)
    for field_name in (
        "component_count",
        "research_ready_component_count",
        "needs_review_component_count",
        "blocked_component_count",
        "memory_quality_gate_count",
        "memory_quality_gate_research_ready_count",
        "memory_quality_gate_needs_review_count",
        "memory_quality_gate_blocked_count",
        "source_reliability_row_count",
        "source_reliability_watch_count",
        "source_reliability_blocked_count",
        "handoff_count",
        "handoff_watch_count",
        "handoff_blocked_count",
        "calibration_outcome_count",
        "calibration_stale_unresolved_count",
        "coverage_observation_count",
        "coverage_gap_count",
        "coverage_blocked_count",
    ):
        _require_nonnegative_int(field_name, getattr(report, field_name))
    for field_name in ("readiness_ratio", "needs_review_ratio", "blocked_ratio"):
        _normalize_optional_ratio(field_name, getattr(report, field_name))
    _normalize_rows(report.rows)
    _normalize_dashboard_reason_codes(report.reason_codes)
    for row in report.rows:
        _validate_row_runtime(row)
    _validate_report_consistency(report)
    if report.validation_digest != _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        dashboard_status=report.dashboard_status,
        component_count=report.component_count,
        research_ready_component_count=report.research_ready_component_count,
        needs_review_component_count=report.needs_review_component_count,
        blocked_component_count=report.blocked_component_count,
        readiness_ratio=report.readiness_ratio,
        needs_review_ratio=report.needs_review_ratio,
        blocked_ratio=report.blocked_ratio,
        memory_quality_gate_count=report.memory_quality_gate_count,
        memory_quality_gate_research_ready_count=(
            report.memory_quality_gate_research_ready_count
        ),
        memory_quality_gate_needs_review_count=(
            report.memory_quality_gate_needs_review_count
        ),
        memory_quality_gate_blocked_count=report.memory_quality_gate_blocked_count,
        source_reliability_row_count=report.source_reliability_row_count,
        source_reliability_watch_count=report.source_reliability_watch_count,
        source_reliability_blocked_count=report.source_reliability_blocked_count,
        handoff_count=report.handoff_count,
        handoff_watch_count=report.handoff_watch_count,
        handoff_blocked_count=report.handoff_blocked_count,
        calibration_outcome_count=report.calibration_outcome_count,
        calibration_stale_unresolved_count=report.calibration_stale_unresolved_count,
        coverage_observation_count=report.coverage_observation_count,
        coverage_gap_count=report.coverage_gap_count,
        coverage_blocked_count=report.coverage_blocked_count,
        rows=report.rows,
        reason_codes=report.reason_codes,
    ):
        raise ValueError("validation_digest must match report")


def _validate_row_runtime(row: TeamResearchReadinessDashboardRow) -> None:
    require_paper_only_flags("TeamResearchReadinessDashboardRow", row)
    _require_member("component", row.component, COMPONENTS)
    _require_canonical_string("subject_id", row.subject_id)
    _require_member("readiness_status", row.readiness_status, READINESS_STATUSES)
    _as_utc("generated_at", row.generated_at)
    for field_name in ("item_count", "watch_count", "blocked_count"):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    if row.watch_count > row.item_count:
        raise ValueError("watch_count must not exceed item_count")
    if row.blocked_count > row.item_count:
        raise ValueError("blocked_count must not exceed item_count")
    _normalize_optional_ratio("readiness_score", row.readiness_score)
    _normalize_redacted_refs(row.redacted_refs)
    _normalize_string_tuple("reason_codes", row.reason_codes, allow_empty=False)
    if row.validation_digest != _row_validation_digest(
        component=row.component,
        subject_id=row.subject_id,
        readiness_status=row.readiness_status,
        generated_at=row.generated_at,
        item_count=row.item_count,
        watch_count=row.watch_count,
        blocked_count=row.blocked_count,
        readiness_score=row.readiness_score,
        redacted_refs=row.redacted_refs,
        reason_codes=row.reason_codes,
    ):
        raise ValueError("validation_digest must match row")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload)
    expected_row_digests = tuple(_payload_row_digest(row) for row in rows)
    for row, expected_digest in zip(rows, expected_row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != expected_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        expected_row_digests,
    ):
        raise ValueError("validation_digest must match payload")
    _validate_payload_report_consistency(payload, rows)


def _validate_payload_report_consistency(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
) -> None:
    component_rows = _payload_component_rows(rows)
    research_ready_count = sum(
        1 for row in component_rows if row["readiness_status"] == "research_ready"
    )
    needs_review_count = sum(
        1 for row in component_rows if row["readiness_status"] == "needs_review"
    )
    blocked_count = sum(1 for row in component_rows if row["readiness_status"] == "blocked")
    component_count = research_ready_count + needs_review_count + blocked_count
    if _payload_required_count(payload, "component_count") != component_count:
        raise ValueError("component_count must match payload rows")
    if (
        _payload_required_count(payload, "research_ready_component_count")
        != research_ready_count
    ):
        raise ValueError("research_ready_component_count must match payload rows")
    if _payload_required_count(payload, "needs_review_component_count") != needs_review_count:
        raise ValueError("needs_review_component_count must match payload rows")
    if _payload_required_count(payload, "blocked_component_count") != blocked_count:
        raise ValueError("blocked_component_count must match payload rows")
    if _payload_required_string(payload, "dashboard_status") != _payload_dashboard_status(
        component_rows,
    ):
        raise ValueError("dashboard_status must match payload rows")
    if _payload_optional_decimal(payload, "readiness_ratio") != _ratio_or_none(
        research_ready_count,
        component_count,
    ):
        raise ValueError("readiness_ratio must match payload rows")
    if _payload_optional_decimal(payload, "needs_review_ratio") != _ratio_or_none(
        needs_review_count,
        component_count,
    ):
        raise ValueError("needs_review_ratio must match payload rows")
    if _payload_optional_decimal(payload, "blocked_ratio") != _ratio_or_none(
        blocked_count,
        component_count,
    ):
        raise ValueError("blocked_ratio must match payload rows")


def _payload_component_rows(rows: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    by_component: dict[str, dict[str, Any]] = {}
    previous_key: tuple[str, str] | None = None
    for row in rows:
        component = _payload_required_member(row, "component", COMPONENTS)
        subject_id = _payload_required_string(row, "subject_id")
        key = (component, subject_id)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be deterministic by component and subject_id")
        previous_key = key
        current = by_component.get(component)
        if current is None:
            by_component[component] = row
            continue
        by_component[component] = {
            "component": component,
            "readiness_status": _merged_status(
                _payload_required_member(
                    current,
                    "readiness_status",
                    READINESS_STATUSES,
                ),
                _payload_required_member(row, "readiness_status", READINESS_STATUSES),
            ),
        }
    return tuple(by_component[component] for component in sorted(by_component))


def _payload_dashboard_status(rows: tuple[dict[str, Any], ...]) -> str:
    if not rows:
        return "blocked"
    statuses = tuple(
        _payload_required_member(row, "readiness_status", READINESS_STATUSES)
        for row in rows
    )
    if "blocked" in statuses:
        return "blocked"
    if "needs_review" in statuses:
        return "needs_review"
    return "research_ready"


def _redact_sensitive_payload(value: object) -> dict[str, Any]:
    redacted = _redact_sensitive_value(value)
    if type(redacted) is not dict:
        raise ValueError("dashboard payload must be a JSON object")
    return redacted


def _redact_sensitive_value(value: object, *, force: bool = False) -> object:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            should_redact = force or _is_sensitive_key(key)
            redacted[key] = (
                "<redacted>"
                if should_redact and not isinstance(item, (dict, list))
                else _redact_sensitive_value(item, force=should_redact)
            )
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_value(item, force=force) for item in value]
    if force:
        return "<redacted>"
    if type(value) is str and _is_sensitive_text(value):
        return "<redacted>"
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(
        fragment in normalized
        for fragment in ("api_key", "secret", "token", "password", "credential")
    )


def _is_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "api_key=",
            "secret=",
            "token=",
            "password=",
            "credential=",
        )
    )


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_values(label, value)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _json_ready_public_payload(value: Any, *, allow_int: bool) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return _datetime_payload(value)
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        if not allow_int:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        return _count_payload(value)
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_public_payload(item, allow_int=allow_int)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public_payload(item, allow_int=allow_int) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    digest = _require_validation_digest(field_name, value)
    if digest != expected_digest:
        raise ValueError(f"{field_name} must match derived values")
    return digest


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _row_validation_digest(
    *,
    component: str,
    subject_id: str,
    readiness_status: str,
    generated_at: datetime,
    item_count: int,
    watch_count: int,
    blocked_count: int,
    readiness_score: Decimal | None,
    redacted_refs: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "team_research_readiness_dashboard_row",
            component,
            subject_id,
            readiness_status,
            _datetime_payload(generated_at),
            _count_payload(item_count),
            _count_payload(watch_count),
            _count_payload(blocked_count),
            _optional_decimal_payload(readiness_score),
            _string_sequence_payload(redacted_refs),
            _string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    dashboard_status: str,
    component_count: int,
    research_ready_component_count: int,
    needs_review_component_count: int,
    blocked_component_count: int,
    readiness_ratio: Decimal | None,
    needs_review_ratio: Decimal | None,
    blocked_ratio: Decimal | None,
    memory_quality_gate_count: int,
    memory_quality_gate_research_ready_count: int,
    memory_quality_gate_needs_review_count: int,
    memory_quality_gate_blocked_count: int,
    source_reliability_row_count: int,
    source_reliability_watch_count: int,
    source_reliability_blocked_count: int,
    handoff_count: int,
    handoff_watch_count: int,
    handoff_blocked_count: int,
    calibration_outcome_count: int,
    calibration_stale_unresolved_count: int,
    coverage_observation_count: int,
    coverage_gap_count: int,
    coverage_blocked_count: int,
    rows: tuple[TeamResearchReadinessDashboardRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "team_research_readiness_dashboard_report",
            _datetime_payload(generated_at),
            config_version,
            dashboard_status,
            _count_payload(component_count),
            _count_payload(research_ready_component_count),
            _count_payload(needs_review_component_count),
            _count_payload(blocked_component_count),
            _optional_decimal_payload(readiness_ratio),
            _optional_decimal_payload(needs_review_ratio),
            _optional_decimal_payload(blocked_ratio),
            _count_payload(memory_quality_gate_count),
            _count_payload(memory_quality_gate_research_ready_count),
            _count_payload(memory_quality_gate_needs_review_count),
            _count_payload(memory_quality_gate_blocked_count),
            _count_payload(source_reliability_row_count),
            _count_payload(source_reliability_watch_count),
            _count_payload(source_reliability_blocked_count),
            _count_payload(handoff_count),
            _count_payload(handoff_watch_count),
            _count_payload(handoff_blocked_count),
            _count_payload(calibration_outcome_count),
            _count_payload(calibration_stale_unresolved_count),
            _count_payload(coverage_observation_count),
            _count_payload(coverage_gap_count),
            _count_payload(coverage_blocked_count),
            _string_sequence_payload(tuple(row.validation_digest for row in rows)),
            _string_sequence_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_row_digest(row: dict[str, Any]) -> str:
    _require_payload_flags(row)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "team_research_readiness_dashboard_row",
            _payload_required_member(row, "component", COMPONENTS),
            _payload_required_string(row, "subject_id"),
            _payload_required_member(row, "readiness_status", READINESS_STATUSES),
            _payload_required_datetime_string(row, "generated_at"),
            _payload_required_count_string(row, "item_count"),
            _payload_required_count_string(row, "watch_count"),
            _payload_required_count_string(row, "blocked_count"),
            _payload_optional_decimal_string(row, "readiness_score"),
            _string_sequence_payload(_payload_required_string_sequence(row, "redacted_refs")),
            _string_sequence_payload(_payload_required_string_sequence(row, "reason_codes")),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "team_research_readiness_dashboard_report",
            _payload_required_datetime_string(payload, "generated_at"),
            _payload_required_string(payload, "config_version"),
            _payload_required_member(payload, "dashboard_status", READINESS_STATUSES),
            _payload_required_count_string(payload, "component_count"),
            _payload_required_count_string(payload, "research_ready_component_count"),
            _payload_required_count_string(payload, "needs_review_component_count"),
            _payload_required_count_string(payload, "blocked_component_count"),
            _payload_optional_decimal_string(payload, "readiness_ratio"),
            _payload_optional_decimal_string(payload, "needs_review_ratio"),
            _payload_optional_decimal_string(payload, "blocked_ratio"),
            _payload_required_count_string(payload, "memory_quality_gate_count"),
            _payload_required_count_string(
                payload,
                "memory_quality_gate_research_ready_count",
            ),
            _payload_required_count_string(
                payload,
                "memory_quality_gate_needs_review_count",
            ),
            _payload_required_count_string(payload, "memory_quality_gate_blocked_count"),
            _payload_required_count_string(payload, "source_reliability_row_count"),
            _payload_required_count_string(payload, "source_reliability_watch_count"),
            _payload_required_count_string(payload, "source_reliability_blocked_count"),
            _payload_required_count_string(payload, "handoff_count"),
            _payload_required_count_string(payload, "handoff_watch_count"),
            _payload_required_count_string(payload, "handoff_blocked_count"),
            _payload_required_count_string(payload, "calibration_outcome_count"),
            _payload_required_count_string(payload, "calibration_stale_unresolved_count"),
            _payload_required_count_string(payload, "coverage_observation_count"),
            _payload_required_count_string(payload, "coverage_gap_count"),
            _payload_required_count_string(payload, "coverage_blocked_count"),
            _string_sequence_payload(row_digests),
            _string_sequence_payload(_payload_required_report_reason_codes(payload)),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _hash_parts(parts: tuple[str, ...]) -> str:
    rendered = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _count_payload(value: int) -> str:
    _require_nonnegative_int("count", value)
    return str(Decimal(value))


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return str(_quantize_ratio(value))


def _optional_decimal_payload(value: Decimal | None) -> str:
    if value is None:
        return "<none>"
    return _decimal_payload(value)


def _string_sequence_payload(values: tuple[str, ...]) -> str:
    return "\x1f".join(values)


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        normalized.append(row)
    return tuple(normalized)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    return _require_validation_digest(field_name, payload.get(field_name))


def _payload_required_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_canonical_string(field_name, value)
    return value


def _payload_required_count(payload: dict[str, Any], field_name: str) -> int:
    return int(Decimal(_payload_required_count_string(payload, field_name)))


def _payload_required_count_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if (
        not decimal_value.is_finite()
        or decimal_value < ZERO
        or decimal_value != decimal_value.to_integral_value()
    ):
        raise ValueError(f"{field_name} must be a nonnegative count string")
    canonical = _count_payload(int(decimal_value))
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical count string")
    return canonical


def _payload_optional_decimal(payload: dict[str, Any], field_name: str) -> Decimal | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    return _normalize_ratio(field_name, Decimal(value))


def _payload_optional_decimal_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_optional_decimal(payload, field_name)
    return _optional_decimal_payload(value)


def _payload_required_datetime_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    canonical = _datetime_payload(parsed)
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return canonical


def _payload_required_string_sequence(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of canonical strings")
    return _normalize_string_tuple(field_name, value, allow_empty=False)


def _payload_required_report_reason_codes(payload: dict[str, Any]) -> tuple[str, ...]:
    reason_codes = _payload_required_string_sequence(payload, "reason_codes")
    for reason_code in reason_codes:
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain dashboard reason codes")
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic reason sequence")
    return reason_codes


def _row_sort_key(row: TeamResearchReadinessDashboardRow) -> tuple[str, str]:
    return (row.component, row.subject_id)


def _ratio_or_none(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(Decimal(numerator) / Decimal(denominator))


def _ratio_count(ratio: Decimal | None, total: int) -> int:
    if ratio is None:
        return 0
    with localcontext(DECIMAL_CONTEXT):
        return int((ratio * Decimal(total)).to_integral_value(rounding=ROUND_HALF_EVEN))


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_nonnegative_count_int(field_name: str, value: object) -> int:
    if type(value) is int:
        if value < 0:
            raise ValueError(f"{field_name} must be nonnegative")
        return value
    if type(value) is Decimal:
        if (
            not value.is_finite()
            or value < ZERO
            or value != value.to_integral_value()
        ):
            raise ValueError(f"{field_name} must be a nonnegative count")
        return int(value)
    raise ValueError(f"{field_name} must be an int or Decimal count")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_RESEARCH_READINESS_DASHBOARD_CONFIG_VERSION",
    "TeamResearchReadinessDashboardConfig",
    "TeamResearchReadinessDashboardReport",
    "TeamResearchReadinessDashboardRow",
    "build_team_research_readiness_dashboard",
    "team_research_readiness_dashboard_payload",
)
