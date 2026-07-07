"""Pure Phase 1 SLA report for specialist evidence collection milestones."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json

from .team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)
from .team_taxonomy import require_team_category_pair


DEFAULT_TEAM_SPECIALIST_EVIDENCE_COLLECTION_SLA_V2_CONFIG_VERSION = (
    "team-specialist-evidence-collection-sla-v2"
)

DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_QUANT = Decimal("0.000001")
RATIO_QUANT = Decimal("0.000001")
SCORE_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")

ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ROW_STATUSES
QUEUE_PRIORITIES = ("low", "medium", "high", "critical")
QUEUE_PRIORITY_SCORES = {
    "low": ZERO,
    "medium": Decimal("0.333333"),
    "high": Decimal("0.666667"),
    "critical": ONE,
}

PASS_REASON = "specialist_evidence_collection_sla_pass"
WATCH_REASON = "specialist_evidence_collection_sla_watch"
BLOCKED_REASON = "specialist_evidence_collection_sla_blocked"
FIRST_SOURCE_SLA_BREACHED_REASON = "first_source_sla_breached"
OFFICIAL_SOURCE_SLA_BREACHED_REASON = "official_source_sla_breached"
INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON = (
    "independent_corroboration_sla_breached"
)
EVIDENCE_STALE_REASON = "evidence_stale"
CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON = (
    "contradiction_followup_sla_breached"
)
QUEUE_URGENCY_HIGH_REASON = "queue_urgency_high"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    FIRST_SOURCE_SLA_BREACHED_REASON,
    OFFICIAL_SOURCE_SLA_BREACHED_REASON,
    INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON,
    EVIDENCE_STALE_REASON,
    CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON,
    QUEUE_URGENCY_HIGH_REASON,
)
ROW_REASON_CODES = (
    PASS_REASON,
    FIRST_SOURCE_SLA_BREACHED_REASON,
    OFFICIAL_SOURCE_SLA_BREACHED_REASON,
    INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON,
    EVIDENCE_STALE_REASON,
    CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON,
    QUEUE_URGENCY_HIGH_REASON,
)
REPORT_REASON_CODES = REASON_CODES
BLOCKING_ROW_REASONS = (
    OFFICIAL_SOURCE_SLA_BREACHED_REASON,
    INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON,
    EVIDENCE_STALE_REASON,
    CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON,
)
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FIELD_FRAGMENTS = tuple(
    sorted(fragment for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS if fragment != "sign")
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(sorted(UNSAFE_SURFACE_FIELD_FRAGMENTS))

ROW_PAYLOAD_FIELDS = (
    "task_id",
    "team_id",
    "category_id",
    "row_status",
    "assigned_at",
    "first_source_at",
    "official_source_at",
    "independent_corroboration_at",
    "latest_evidence_at",
    "contradiction_detected_at",
    "contradiction_followed_up_at",
    "assigned_age_seconds",
    "first_source_latency_seconds",
    "official_source_latency_seconds",
    "independent_corroboration_latency_seconds",
    "latest_evidence_age_seconds",
    "contradiction_followup_latency_seconds",
    "queue_priority",
    "queue_urgency_score",
    "source_config_version",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "report_status",
    "task_count",
    "pass_row_count",
    "watch_row_count",
    "blocked_row_count",
    "issue_row_count",
    "issue_ratio",
    "first_source_sla_breach_count",
    "official_source_sla_breach_count",
    "independent_corroboration_sla_breach_count",
    "stale_evidence_count",
    "contradiction_followup_sla_breach_count",
    "high_queue_urgency_count",
    "max_queue_urgency_score",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


@dataclass(frozen=True)
class TeamSpecialistEvidenceCollectionSlaV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_EVIDENCE_COLLECTION_SLA_V2_CONFIG_VERSION
    )
    first_source_sla_seconds: Decimal = Decimal("900.000000")
    official_source_sla_seconds: Decimal = Decimal("1800.000000")
    independent_corroboration_sla_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_sla_seconds: Decimal = Decimal("7200.000000")
    contradiction_followup_sla_seconds: Decimal = Decimal("1200.000000")
    high_queue_urgency_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistEvidenceCollectionSlaV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, TeamSpecialistEvidenceCollectionSlaV2Config)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "first_source_sla_seconds",
            "official_source_sla_seconds",
            "independent_corroboration_sla_seconds",
            "stale_evidence_sla_seconds",
            "contradiction_followup_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "high_queue_urgency_threshold",
            _require_positive_probability(
                "high_queue_urgency_threshold",
                self.high_queue_urgency_threshold,
            ),
        )
        _reject_unsafe_public_payload("config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceCollectionSlaV2InputRow:
    task_id: str
    team_id: str
    category_id: str
    assigned_at: datetime
    first_source_at: datetime | None = None
    official_source_at: datetime | None = None
    independent_corroboration_at: datetime | None = None
    latest_evidence_at: datetime | None = None
    contradiction_detected_at: datetime | None = None
    contradiction_followed_up_at: datetime | None = None
    queue_priority: str = "medium"
    source_config_version: str = "phase1-source-manifest-v2"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistEvidenceCollectionSlaV2InputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input row", self, TeamSpecialistEvidenceCollectionSlaV2InputRow)
        object.__setattr__(
            self,
            "task_id",
            _require_canonical_string("task_id", self.task_id),
        )
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        object.__setattr__(
            self,
            "assigned_at",
            _as_utc("assigned_at", self.assigned_at),
        )
        for field_name in (
            "first_source_at",
            "official_source_at",
            "independent_corroboration_at",
            "latest_evidence_at",
            "contradiction_detected_at",
            "contradiction_followed_up_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "first_source_at",
            "official_source_at",
            "independent_corroboration_at",
            "latest_evidence_at",
            "contradiction_detected_at",
        ):
            _require_not_before_assigned_at(field_name, getattr(self, field_name), self)
        _validate_contradiction_followup_shape(self)
        object.__setattr__(
            self,
            "queue_priority",
            _require_member("queue_priority", self.queue_priority, QUEUE_PRIORITIES),
        )
        object.__setattr__(
            self,
            "source_config_version",
            _require_canonical_string(
                "source_config_version",
                self.source_config_version,
            ),
        )
        _reject_unsafe_public_payload("input row", self)
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceCollectionSlaV2Row:
    task_id: str
    team_id: str
    category_id: str
    row_status: str
    assigned_at: datetime
    first_source_at: datetime | None
    official_source_at: datetime | None
    independent_corroboration_at: datetime | None
    latest_evidence_at: datetime | None
    contradiction_detected_at: datetime | None
    contradiction_followed_up_at: datetime | None
    assigned_age_seconds: Decimal
    first_source_latency_seconds: Decimal
    official_source_latency_seconds: Decimal
    independent_corroboration_latency_seconds: Decimal
    latest_evidence_age_seconds: Decimal
    contradiction_followup_latency_seconds: Decimal
    queue_priority: str
    queue_urgency_score: Decimal
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistEvidenceCollectionSlaV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, TeamSpecialistEvidenceCollectionSlaV2Row)
        object.__setattr__(
            self,
            "task_id",
            _require_canonical_string("task_id", self.task_id),
        )
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        object.__setattr__(
            self,
            "row_status",
            _require_member("row_status", self.row_status, ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "assigned_at",
            _as_utc("assigned_at", self.assigned_at),
        )
        for field_name in (
            "first_source_at",
            "official_source_at",
            "independent_corroboration_at",
            "latest_evidence_at",
            "contradiction_detected_at",
            "contradiction_followed_up_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "assigned_age_seconds",
            "first_source_latency_seconds",
            "official_source_latency_seconds",
            "independent_corroboration_latency_seconds",
            "latest_evidence_age_seconds",
            "contradiction_followup_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_priority",
            _require_member("queue_priority", self.queue_priority, QUEUE_PRIORITIES),
        )
        object.__setattr__(
            self,
            "queue_urgency_score",
            _require_probability("queue_urgency_score", self.queue_urgency_score),
        )
        object.__setattr__(
            self,
            "source_config_version",
            _require_canonical_string(
                "source_config_version",
                self.source_config_version,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _reject_unsafe_public_payload("row", self)
        require_paper_only_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistEvidenceCollectionSlaV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    task_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    issue_row_count: Decimal
    issue_ratio: Decimal
    first_source_sla_breach_count: Decimal
    official_source_sla_breach_count: Decimal
    independent_corroboration_sla_breach_count: Decimal
    stale_evidence_count: Decimal
    contradiction_followup_sla_breach_count: Decimal
    high_queue_urgency_count: Decimal
    max_queue_urgency_score: Decimal
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistEvidenceCollectionSlaV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, TeamSpecialistEvidenceCollectionSlaV2Report)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, REPORT_STATUSES),
        )
        for field_name in (
            "task_count",
            "pass_row_count",
            "watch_row_count",
            "blocked_row_count",
            "issue_row_count",
            "first_source_sla_breach_count",
            "official_source_sla_breach_count",
            "independent_corroboration_sla_breach_count",
            "stale_evidence_count",
            "contradiction_followup_sla_breach_count",
            "high_queue_urgency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_probability("issue_ratio", self.issue_ratio),
        )
        object.__setattr__(
            self,
            "max_queue_urgency_score",
            _require_probability(
                "max_queue_urgency_score",
                self.max_queue_urgency_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _reject_unsafe_public_payload("report", self)
        require_paper_only_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return team_specialist_evidence_collection_sla_v2_report_to_payload(self)


def build_team_specialist_evidence_collection_sla_v2_report(
    source_rows: object,
    *,
    config: TeamSpecialistEvidenceCollectionSlaV2Config,
    generated_at: datetime,
) -> TeamSpecialistEvidenceCollectionSlaV2Report:
    _require_exact_type("config", config, TeamSpecialistEvidenceCollectionSlaV2Config)
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(source_rows)
    _validate_unique_task_ids(normalized_rows)
    _validate_no_future_times(normalized_rows, generated_at_utc)

    rows = _sort_rows(
        tuple(
            _row_from_input(source_row, config=config, generated_at=generated_at_utc)
            for source_row in normalized_rows
        ),
    )
    issue_count = _decimal_count(sum(1 for row in rows if row.row_status != "pass"))

    return TeamSpecialistEvidenceCollectionSlaV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        task_count=_decimal_count(len(rows)),
        pass_row_count=_status_count(rows, "pass"),
        watch_row_count=_status_count(rows, "watch"),
        blocked_row_count=_status_count(rows, "blocked"),
        issue_row_count=issue_count,
        issue_ratio=_ratio(issue_count, _decimal_count(len(rows))),
        first_source_sla_breach_count=_reason_count(
            rows,
            FIRST_SOURCE_SLA_BREACHED_REASON,
        ),
        official_source_sla_breach_count=_reason_count(
            rows,
            OFFICIAL_SOURCE_SLA_BREACHED_REASON,
        ),
        independent_corroboration_sla_breach_count=_reason_count(
            rows,
            INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON,
        ),
        stale_evidence_count=_reason_count(rows, EVIDENCE_STALE_REASON),
        contradiction_followup_sla_breach_count=_reason_count(
            rows,
            CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON,
        ),
        high_queue_urgency_count=_reason_count(rows, QUEUE_URGENCY_HIGH_REASON),
        max_queue_urgency_score=max(
            (row.queue_urgency_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def team_specialist_evidence_collection_sla_v2_report_to_payload(
    report: TeamSpecialistEvidenceCollectionSlaV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is TeamSpecialistEvidenceCollectionSlaV2Report:
        _reject_unsafe_public_payload("report", report)
        require_paper_only_flags("report", report)
        _validate_report_derived_validation_digest(report)
        _validate_report(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return _copy_json_object(report)
    raise ValueError(
        "report must be a TeamSpecialistEvidenceCollectionSlaV2Report or payload dict",
    )


def _row_from_input(
    source_row: TeamSpecialistEvidenceCollectionSlaV2InputRow,
    *,
    config: TeamSpecialistEvidenceCollectionSlaV2Config,
    generated_at: datetime,
) -> TeamSpecialistEvidenceCollectionSlaV2Row:
    assigned_age_seconds = _seconds_between(source_row.assigned_at, generated_at)
    first_source_latency_seconds = _milestone_latency_seconds(
        source_row.assigned_at,
        source_row.first_source_at,
        generated_at,
    )
    official_source_latency_seconds = _milestone_latency_seconds(
        source_row.assigned_at,
        source_row.official_source_at,
        generated_at,
    )
    independent_corroboration_latency_seconds = _milestone_latency_seconds(
        source_row.assigned_at,
        source_row.independent_corroboration_at,
        generated_at,
    )
    latest_evidence_age_seconds = _seconds_between(
        source_row.latest_evidence_at or source_row.assigned_at,
        generated_at,
    )
    contradiction_followup_latency_seconds = _contradiction_followup_latency_seconds(
        source_row,
        generated_at,
    )
    queue_urgency_score = _queue_urgency_score(
        source_row,
        config=config,
        assigned_age_seconds=assigned_age_seconds,
        first_source_latency_seconds=first_source_latency_seconds,
        official_source_latency_seconds=official_source_latency_seconds,
        independent_corroboration_latency_seconds=(
            independent_corroboration_latency_seconds
        ),
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        contradiction_followup_latency_seconds=contradiction_followup_latency_seconds,
    )
    reason_codes = _row_reason_codes(
        config=config,
        first_source_latency_seconds=first_source_latency_seconds,
        official_source_latency_seconds=official_source_latency_seconds,
        independent_corroboration_latency_seconds=(
            independent_corroboration_latency_seconds
        ),
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        contradiction_followup_latency_seconds=contradiction_followup_latency_seconds,
        queue_urgency_score=queue_urgency_score,
        has_contradiction=source_row.contradiction_detected_at is not None,
    )

    return TeamSpecialistEvidenceCollectionSlaV2Row(
        task_id=source_row.task_id,
        team_id=source_row.team_id,
        category_id=source_row.category_id,
        row_status=_row_status(reason_codes),
        assigned_at=source_row.assigned_at,
        first_source_at=source_row.first_source_at,
        official_source_at=source_row.official_source_at,
        independent_corroboration_at=source_row.independent_corroboration_at,
        latest_evidence_at=source_row.latest_evidence_at,
        contradiction_detected_at=source_row.contradiction_detected_at,
        contradiction_followed_up_at=source_row.contradiction_followed_up_at,
        assigned_age_seconds=assigned_age_seconds,
        first_source_latency_seconds=first_source_latency_seconds,
        official_source_latency_seconds=official_source_latency_seconds,
        independent_corroboration_latency_seconds=(
            independent_corroboration_latency_seconds
        ),
        latest_evidence_age_seconds=latest_evidence_age_seconds,
        contradiction_followup_latency_seconds=contradiction_followup_latency_seconds,
        queue_priority=source_row.queue_priority,
        queue_urgency_score=queue_urgency_score,
        source_config_version=source_row.source_config_version,
        reason_codes=reason_codes,
    )


def _queue_urgency_score(
    source_row: TeamSpecialistEvidenceCollectionSlaV2InputRow,
    *,
    config: TeamSpecialistEvidenceCollectionSlaV2Config,
    assigned_age_seconds: Decimal,
    first_source_latency_seconds: Decimal,
    official_source_latency_seconds: Decimal,
    independent_corroboration_latency_seconds: Decimal,
    latest_evidence_age_seconds: Decimal,
    contradiction_followup_latency_seconds: Decimal,
) -> Decimal:
    contradiction_score = ZERO
    if source_row.contradiction_detected_at is not None:
        contradiction_score = _capped_ratio(
            contradiction_followup_latency_seconds,
            config.contradiction_followup_sla_seconds,
        )
    return max(
        _capped_ratio(
            assigned_age_seconds,
            config.independent_corroboration_sla_seconds,
        ),
        _capped_ratio(
            first_source_latency_seconds,
            config.first_source_sla_seconds,
        ),
        _capped_ratio(
            official_source_latency_seconds,
            config.official_source_sla_seconds,
        ),
        _capped_ratio(
            independent_corroboration_latency_seconds,
            config.independent_corroboration_sla_seconds,
        ),
        _capped_ratio(latest_evidence_age_seconds, config.stale_evidence_sla_seconds),
        contradiction_score,
        QUEUE_PRIORITY_SCORES[source_row.queue_priority],
    ).quantize(SCORE_QUANT)


def _row_reason_codes(
    *,
    config: TeamSpecialistEvidenceCollectionSlaV2Config,
    first_source_latency_seconds: Decimal,
    official_source_latency_seconds: Decimal,
    independent_corroboration_latency_seconds: Decimal,
    latest_evidence_age_seconds: Decimal,
    contradiction_followup_latency_seconds: Decimal,
    queue_urgency_score: Decimal,
    has_contradiction: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if first_source_latency_seconds > config.first_source_sla_seconds:
        reasons.append(FIRST_SOURCE_SLA_BREACHED_REASON)
    if official_source_latency_seconds > config.official_source_sla_seconds:
        reasons.append(OFFICIAL_SOURCE_SLA_BREACHED_REASON)
    if (
        independent_corroboration_latency_seconds
        > config.independent_corroboration_sla_seconds
    ):
        reasons.append(INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON)
    if latest_evidence_age_seconds > config.stale_evidence_sla_seconds:
        reasons.append(EVIDENCE_STALE_REASON)
    if (
        has_contradiction
        and contradiction_followup_latency_seconds
        > config.contradiction_followup_sla_seconds
    ):
        reasons.append(CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON)
    if queue_urgency_score >= config.high_queue_urgency_threshold:
        reasons.append(QUEUE_URGENCY_HIGH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(reason in reason_codes for reason in BLOCKING_ROW_REASONS):
        return "blocked"
    return "watch"


def _report_status(rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...]) -> str:
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return (PASS_REASON,)
    reasons = [BLOCKED_REASON if status == "blocked" else WATCH_REASON]
    for reason in ROW_REASON_CODES[1:]:
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _normalize_input_rows(
    source_rows: object,
) -> tuple[TeamSpecialistEvidenceCollectionSlaV2InputRow, ...]:
    try:
        rows = tuple(source_rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_rows must be iterable") from exc
    for row in rows:
        _require_exact_type("source row", row, TeamSpecialistEvidenceCollectionSlaV2InputRow)
        require_paper_only_flags("source row", row)
    return rows


def _validate_unique_task_ids(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2InputRow, ...],
) -> None:
    task_ids = tuple(row.task_id for row in rows)
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("task_id values must be unique")


def _validate_no_future_times(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2InputRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        for field_name in (
            "assigned_at",
            "first_source_at",
            "official_source_at",
            "independent_corroboration_at",
            "latest_evidence_at",
            "contradiction_detected_at",
            "contradiction_followed_up_at",
        ):
            value = getattr(row, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        _require_exact_type("row", row, TeamSpecialistEvidenceCollectionSlaV2Row)
        require_paper_only_flags("row", row)
    return _sort_rows(rows)


def _sort_rows(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...],
) -> tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: TeamSpecialistEvidenceCollectionSlaV2Row,
) -> tuple[int, Decimal, datetime, str]:
    return (
        STATUS_WEIGHT[row.row_status],
        -row.queue_urgency_score,
        row.assigned_at,
        row.task_id,
    )


def _status_count(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[TeamSpecialistEvidenceCollectionSlaV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _validate_row(row: TeamSpecialistEvidenceCollectionSlaV2Row) -> None:
    if row.reason_codes == (PASS_REASON,) and row.row_status != "pass":
        raise ValueError("pass reason must have pass row_status")
    if row.reason_codes != (PASS_REASON,) and row.row_status == "pass":
        raise ValueError("pass row_status cannot have issue reason_codes")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: TeamSpecialistEvidenceCollectionSlaV2Report) -> None:
    rows = report.rows
    if report.task_count != _decimal_count(len(rows)):
        raise ValueError("task_count must match rows")
    if report.pass_row_count != _status_count(rows, "pass"):
        raise ValueError("pass_row_count must match rows")
    if report.watch_row_count != _status_count(rows, "watch"):
        raise ValueError("watch_row_count must match rows")
    if report.blocked_row_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_row_count must match rows")
    if report.issue_row_count != _decimal_count(
        sum(1 for row in rows if row.row_status != "pass"),
    ):
        raise ValueError("issue_row_count must match rows")
    if report.issue_ratio != _ratio(report.issue_row_count, report.task_count):
        raise ValueError("issue_ratio must match counts")
    if report.first_source_sla_breach_count != _reason_count(
        rows,
        FIRST_SOURCE_SLA_BREACHED_REASON,
    ):
        raise ValueError("first_source_sla_breach_count must match rows")
    if report.official_source_sla_breach_count != _reason_count(
        rows,
        OFFICIAL_SOURCE_SLA_BREACHED_REASON,
    ):
        raise ValueError("official_source_sla_breach_count must match rows")
    if report.independent_corroboration_sla_breach_count != _reason_count(
        rows,
        INDEPENDENT_CORROBORATION_SLA_BREACHED_REASON,
    ):
        raise ValueError("independent_corroboration_sla_breach_count must match rows")
    if report.stale_evidence_count != _reason_count(rows, EVIDENCE_STALE_REASON):
        raise ValueError("stale_evidence_count must match rows")
    if report.contradiction_followup_sla_breach_count != _reason_count(
        rows,
        CONTRADICTION_FOLLOWUP_SLA_BREACHED_REASON,
    ):
        raise ValueError("contradiction_followup_sla_breach_count must match rows")
    if report.high_queue_urgency_count != _reason_count(
        rows,
        QUEUE_URGENCY_HIGH_REASON,
    ):
        raise ValueError("high_queue_urgency_count must match rows")
    if report.max_queue_urgency_score != max(
        (row.queue_urgency_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_queue_urgency_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_not_before_assigned_at(
    field_name: str,
    value: datetime | None,
    row: TeamSpecialistEvidenceCollectionSlaV2InputRow,
) -> None:
    if value is not None and value < row.assigned_at:
        raise ValueError(f"{field_name} must not be before assigned_at")


def _validate_contradiction_followup_shape(
    row: TeamSpecialistEvidenceCollectionSlaV2InputRow,
) -> None:
    if (
        row.contradiction_followed_up_at is not None
        and row.contradiction_detected_at is None
    ):
        raise ValueError(
            "contradiction_followed_up_at requires contradiction_detected_at",
        )
    if row.contradiction_followed_up_at is not None:
        _require_not_before_assigned_at(
            "contradiction_followed_up_at",
            row.contradiction_followed_up_at,
            row,
        )
    if (
        row.contradiction_detected_at is not None
        and row.contradiction_followed_up_at is not None
        and row.contradiction_followed_up_at < row.contradiction_detected_at
    ):
        raise ValueError(
            "contradiction_followed_up_at must not be before contradiction_detected_at",
        )


def _milestone_latency_seconds(
    assigned_at: datetime,
    milestone_at: datetime | None,
    generated_at: datetime,
) -> Decimal:
    return _seconds_between(assigned_at, milestone_at or generated_at)


def _contradiction_followup_latency_seconds(
    row: TeamSpecialistEvidenceCollectionSlaV2InputRow,
    generated_at: datetime,
) -> Decimal:
    if row.contradiction_detected_at is None:
        return ZERO
    return _seconds_between(
        row.contradiction_detected_at,
        row.contradiction_followed_up_at or generated_at,
    )


def _seconds_between(start_at: datetime, end_at: datetime) -> Decimal:
    if end_at < start_at:
        raise ValueError("end_at must not be before start_at")
    delta = end_at - start_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        with localcontext(DECIMAL_CONTEXT):
            whole_seconds += Decimal(delta.microseconds) / Decimal(1000000)
    return whole_seconds.quantize(SECONDS_QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANT)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return ratio.quantize(SCORE_QUANT)


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(quantum)


def _require_positive_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    decimal_value = _require_decimal(field_name, value, quantum)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    decimal_value = _require_decimal(field_name, value, quantum)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    return _require_positive_decimal(field_name, value, SECONDS_QUANT)


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value, SECONDS_QUANT)


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value, SCORE_QUANT)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value, COUNT_QUANT)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member("reason_code", code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason for reason in allowed if reason in codes)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    _reject_unsafe_public_fields(label, value)
    _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_fields(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_field(label, field.name)
            _reject_unsafe_public_fields(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public fields must be strings")
            _reject_unsafe_public_field(label, key)
            _reject_unsafe_public_fields(f"{label}.{key}", child)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_unsafe_public_fields(f"{label}[{index}]", child)


def _reject_unsafe_public_field(label: str, field_name: str) -> None:
    lowered = field_name.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"unsafe public field in {label}: {field_name}")


def _reject_unsafe_public_text(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public fields must be strings")
            _reject_unsafe_public_text(f"{label}.{key}", child)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_unsafe_public_text(f"{label}[{index}]", child)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")


def _report_public_payload_values(
    report: TeamSpecialistEvidenceCollectionSlaV2Report,
) -> dict[str, object]:
    return {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value.quantize(COUNT_QUANT))
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(child) for key, child in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _report_derived_validation_digest(
    report: TeamSpecialistEvidenceCollectionSlaV2Report,
) -> str:
    return _digest_payload(_report_public_payload_values(report))


def _digest_payload(payload_without_digest: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_without_digest,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _validate_report_derived_validation_digest(
    report: TeamSpecialistEvidenceCollectionSlaV2Report,
) -> None:
    expected = _report_derived_validation_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public report payload")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    missing_fields = set(REPORT_PAYLOAD_FIELDS) - set(payload)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"payload missing required fields: {missing}")
    extra_fields = set(payload) - set(REPORT_PAYLOAD_FIELDS)
    if extra_fields:
        extra = ", ".join(sorted(extra_fields))
        raise ValueError(f"payload contains unknown fields: {extra}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    _require_payload_string("generated_at", payload["generated_at"])
    _require_payload_string("config_version", payload["config_version"])
    _require_member("report_status", payload["report_status"], REPORT_STATUSES)
    for field_name in (
        "task_count",
        "pass_row_count",
        "watch_row_count",
        "blocked_row_count",
        "issue_row_count",
        "issue_ratio",
        "first_source_sla_breach_count",
        "official_source_sla_breach_count",
        "independent_corroboration_sla_breach_count",
        "stale_evidence_count",
        "contradiction_followup_sla_breach_count",
        "high_queue_urgency_count",
        "max_queue_urgency_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_public_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _require_public_payload_flags(payload)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain objects")
        _validate_public_row_payload(row_payload)
    payload_without_digest = {
        field_name: payload[field_name]
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(
        payload_without_digest,
    ):
        raise ValueError("derived_validation_digest must match public report payload")


def _validate_public_row_payload(row_payload: dict[str, object]) -> None:
    missing_fields = set(ROW_PAYLOAD_FIELDS) - set(row_payload)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"row payload missing required fields: {missing}")
    extra_fields = set(row_payload) - set(ROW_PAYLOAD_FIELDS)
    if extra_fields:
        extra = ", ".join(sorted(extra_fields))
        raise ValueError(f"row payload contains unknown fields: {extra}")
    for field_name in (
        "task_id",
        "team_id",
        "category_id",
        "source_config_version",
    ):
        _require_payload_string(field_name, row_payload[field_name])
    _require_member("row_status", row_payload["row_status"], ROW_STATUSES)
    _require_member("queue_priority", row_payload["queue_priority"], QUEUE_PRIORITIES)
    for field_name in (
        "assigned_at",
        "first_source_at",
        "official_source_at",
        "independent_corroboration_at",
        "latest_evidence_at",
        "contradiction_detected_at",
        "contradiction_followed_up_at",
    ):
        _require_optional_payload_string(field_name, row_payload[field_name])
    for field_name in (
        "assigned_age_seconds",
        "first_source_latency_seconds",
        "official_source_latency_seconds",
        "independent_corroboration_latency_seconds",
        "latest_evidence_age_seconds",
        "contradiction_followup_latency_seconds",
        "queue_urgency_score",
    ):
        _require_decimal_payload_string(field_name, row_payload[field_name])
    _require_public_payload_reason_codes(
        "reason_codes",
        row_payload["reason_codes"],
        ROW_REASON_CODES,
    )
    _require_public_payload_flags(row_payload)


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_optional_payload_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_payload_string(field_name, value)


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if str(decimal_value.quantize(COUNT_QUANT)) != value:
        raise ValueError(f"{field_name} must be a six-decimal string")
    return decimal_value


def _require_public_payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value), allowed)


def _require_public_payload_flags(payload: dict[str, object]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _copy_json_object(payload: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    if type(copied) is not dict:
        raise ValueError("payload must be an object")
    return copied


__all__ = (
    "BLOCKED_REASON",
    "DEFAULT_TEAM_SPECIALIST_EVIDENCE_COLLECTION_SLA_V2_CONFIG_VERSION",
    "PASS_REASON",
    "REASON_CODES",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "TeamSpecialistEvidenceCollectionSlaV2Config",
    "TeamSpecialistEvidenceCollectionSlaV2InputRow",
    "TeamSpecialistEvidenceCollectionSlaV2Report",
    "TeamSpecialistEvidenceCollectionSlaV2Row",
    "build_team_specialist_evidence_collection_sla_v2_report",
    "team_specialist_evidence_collection_sla_v2_report_to_payload",
)
