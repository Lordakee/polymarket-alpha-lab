"""Pure specialist evidence review queue report reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-specialist-evidence-review-queue-report-v0"
)
RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"

_PASS_REASON = "evidence_review_queue_pass"
_EMPTY_REASON = "evidence_review_queue_empty"
_QUEUE_BLOCK_REASON = "queue_age_block"
_QUEUE_WATCH_REASON = "queue_age_watch"
_EVIDENCE_BLOCK_REASON = "evidence_age_block"
_EVIDENCE_WATCH_REASON = "evidence_age_watch"
_FAMILY_BLOCK_REASON = "source_family_gap_block"
_FAMILY_WATCH_REASON = "source_family_gap_watch"
_CLAIM_BLOCK_REASON = "unresolved_claims_block"
_CLAIM_WATCH_REASON = "unresolved_claims_watch"
_CONTRADICTION_BLOCK_REASON = "contradiction_block"
_CONTRADICTION_WATCH_REASON = "contradiction_watch"
_STALE_BLOCK_REASON = "stale_source_block"
_STALE_WATCH_REASON = "stale_source_watch"
_REVIEWER_BLOCK_REASON = "reviewer_capacity_block"
_COMPLEXITY_BLOCK_REASON = "complexity_block"
_COMPLEXITY_WATCH_REASON = "complexity_watch"

_REASON_SEQUENCE = (
    _QUEUE_BLOCK_REASON,
    _EVIDENCE_BLOCK_REASON,
    _FAMILY_BLOCK_REASON,
    _CLAIM_BLOCK_REASON,
    _CONTRADICTION_BLOCK_REASON,
    _STALE_BLOCK_REASON,
    _REVIEWER_BLOCK_REASON,
    _COMPLEXITY_BLOCK_REASON,
    _QUEUE_WATCH_REASON,
    _EVIDENCE_WATCH_REASON,
    _FAMILY_WATCH_REASON,
    _CLAIM_WATCH_REASON,
    _CONTRADICTION_WATCH_REASON,
    _STALE_WATCH_REASON,
    _COMPLEXITY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)

_UNSAFE_PUBLIC_HEXES = (
    "63616e646964617465",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "6d61726b65745f7175657374696f6e",
    "6d61726b6574",
    "736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
    "64736e",
    "706f7374677265733a2f2f",
    "7461626c655f6e616d65",
    "746f6b656e",
    "736563726574",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "627579",
    "73656c6c",
    "6e6574776f726b",
    "6461746162617365",
    "6c697665",
    "73697a696e67",
    "7265636f6d6d656e646174696f6e",
    "65786563757465",
    "657865637574696f6e",
)
_UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii") for value in _UNSAFE_PUBLIC_HEXES
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "stale_evidence_count",
        "source_family_gap_count",
        "total_unresolved_claim_count",
        "total_contradiction_count",
        "total_stale_source_count",
        "reviewer_capacity_gap_count",
        "max_review_priority_score",
        "average_review_priority_score",
        "status",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "team_ref",
        "specialist_ref",
        "evidence_packet_digest",
        "source_bundle_digest",
        "queued_at",
        "evidence_observed_at",
        "queue_age_seconds",
        "evidence_age_seconds",
        "source_family_count",
        "unresolved_claim_count",
        "contradiction_count",
        "stale_source_count",
        "reviewer_available_count",
        "review_complexity_score",
        "queue_age_component",
        "evidence_age_component",
        "source_family_gap",
        "unresolved_claim_component",
        "contradiction_component",
        "stale_source_component",
        "reviewer_capacity_gap",
        "complexity_component",
        "review_priority_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_COUNT_PAYLOAD_FIELDS = (
    "item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "stale_evidence_count",
    "source_family_gap_count",
    "total_unresolved_claim_count",
    "total_contradiction_count",
    "total_stale_source_count",
    "reviewer_capacity_gap_count",
)
_REPORT_SCORE_PAYLOAD_FIELDS = (
    "max_review_priority_score",
    "average_review_priority_score",
)
_ROW_COUNT_PAYLOAD_FIELDS = (
    "source_family_count",
    "unresolved_claim_count",
    "contradiction_count",
    "stale_source_count",
    "reviewer_available_count",
)
_ROW_DURATION_PAYLOAD_FIELDS = (
    "queue_age_seconds",
    "evidence_age_seconds",
)
_ROW_SCORE_PAYLOAD_FIELDS = (
    "review_complexity_score",
    "queue_age_component",
    "evidence_age_component",
    "source_family_gap",
    "unresolved_claim_component",
    "contradiction_component",
    "stale_source_component",
    "reviewer_capacity_gap",
    "complexity_component",
    "review_priority_score",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReviewQueueReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_REPORT_CONFIG_VERSION
    )
    queue_watch_age_seconds: Decimal = Decimal("3600.000000")
    queue_block_age_seconds: Decimal = Decimal("10800.000000")
    evidence_watch_age_seconds: Decimal = Decimal("86400.000000")
    evidence_block_age_seconds: Decimal = Decimal("259200.000000")
    min_pass_source_family_count: Decimal = Decimal("3")
    unresolved_watch_claim_count: Decimal = Decimal("1")
    unresolved_block_claim_count: Decimal = Decimal("3")
    contradiction_watch_count: Decimal = Decimal("1")
    contradiction_block_count: Decimal = Decimal("2")
    stale_source_watch_count: Decimal = Decimal("1")
    stale_source_block_count: Decimal = Decimal("3")
    min_reviewer_available_count: Decimal = Decimal("1")
    complexity_watch_score: Decimal = Decimal("0.500000")
    complexity_block_score: Decimal = Decimal("0.800000")
    queue_age_weight: Decimal = Decimal("0.200000")
    evidence_age_weight: Decimal = Decimal("0.150000")
    source_family_weight: Decimal = Decimal("0.150000")
    unresolved_claim_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.150000")
    stale_source_weight: Decimal = Decimal("0.100000")
    reviewer_capacity_weight: Decimal = Decimal("0.050000")
    complexity_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "queue_watch_age_seconds",
            "queue_block_age_seconds",
            "evidence_watch_age_seconds",
            "evidence_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_source_family_count",
            "unresolved_watch_claim_count",
            "unresolved_block_claim_count",
            "contradiction_watch_count",
            "contradiction_block_count",
            "stale_source_watch_count",
            "stale_source_block_count",
            "min_reviewer_available_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "complexity_watch_score",
            "complexity_block_score",
            "queue_age_weight",
            "evidence_age_weight",
            "source_family_weight",
            "unresolved_claim_weight",
            "contradiction_weight",
            "stale_source_weight",
            "reviewer_capacity_weight",
            "complexity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.queue_block_age_seconds <= self.queue_watch_age_seconds:
            raise ValueError("queue_block_age_seconds must exceed watch threshold")
        if self.evidence_block_age_seconds <= self.evidence_watch_age_seconds:
            raise ValueError("evidence_block_age_seconds must exceed watch threshold")
        if self.unresolved_block_claim_count <= self.unresolved_watch_claim_count:
            raise ValueError("unresolved_block_claim_count must exceed watch threshold")
        if self.contradiction_block_count <= self.contradiction_watch_count:
            raise ValueError("contradiction_block_count must exceed watch threshold")
        if self.stale_source_block_count <= self.stale_source_watch_count:
            raise ValueError("stale_source_block_count must exceed watch threshold")
        if self.complexity_block_score <= self.complexity_watch_score:
            raise ValueError("complexity_block_score must exceed watch threshold")
        weight_sum = _six(
            self.queue_age_weight
            + self.evidence_age_weight
            + self.source_family_weight
            + self.unresolved_claim_weight
            + self.contradiction_weight
            + self.stale_source_weight
            + self.reviewer_capacity_weight
            + self.complexity_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReviewQueueItem:
    team_ref: str
    specialist_ref: str
    evidence_packet_digest: str
    source_bundle_digest: str
    queued_at: datetime
    evidence_observed_at: datetime
    source_family_count: Decimal
    unresolved_claim_count: Decimal
    contradiction_count: Decimal
    stale_source_count: Decimal
    reviewer_available_count: Decimal
    review_complexity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("item", self, ResearchTeamSpecialistEvidenceReviewQueueItem)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("evidence_packet_digest", "source_bundle_digest"):
            _require_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "source_family_count",
            "unresolved_claim_count",
            "contradiction_count",
            "stale_source_count",
            "reviewer_available_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_complexity_score",
            _normalize_unit_decimal(
                "review_complexity_score",
                self.review_complexity_score,
            ),
        )
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReviewQueueRow:
    team_ref: str
    specialist_ref: str
    evidence_packet_digest: str
    source_bundle_digest: str
    queued_at: datetime
    evidence_observed_at: datetime
    queue_age_seconds: Decimal
    evidence_age_seconds: Decimal
    source_family_count: Decimal
    unresolved_claim_count: Decimal
    contradiction_count: Decimal
    stale_source_count: Decimal
    reviewer_available_count: Decimal
    review_complexity_score: Decimal
    queue_age_component: Decimal
    evidence_age_component: Decimal
    source_family_gap: Decimal
    unresolved_claim_component: Decimal
    contradiction_component: Decimal
    stale_source_component: Decimal
    reviewer_capacity_gap: Decimal
    complexity_component: Decimal
    review_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    _validation_config: InitVar[
        ResearchTeamSpecialistEvidenceReviewQueueReportConfig | None
    ] = None

    def __post_init__(
        self,
        _validation_config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig | None,
    ) -> None:
        _require_exact_type("row", self, ResearchTeamSpecialistEvidenceReviewQueueRow)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("evidence_packet_digest", "source_bundle_digest"):
            _require_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "queue_age_seconds",
            "evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "source_family_count",
            "unresolved_claim_count",
            "contradiction_count",
            "stale_source_count",
            "reviewer_available_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_complexity_score",
            "queue_age_component",
            "evidence_age_component",
            "source_family_gap",
            "unresolved_claim_component",
            "contradiction_component",
            "stale_source_component",
            "reviewer_capacity_gap",
            "complexity_component",
            "review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_metrics(
            self,
            config=(
                ResearchTeamSpecialistEvidenceReviewQueueReportConfig()
                if _validation_config is None
                else _validation_config
            ),
        )
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistEvidenceReviewQueueReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_evidence_count: Decimal
    source_family_gap_count: Decimal
    total_unresolved_claim_count: Decimal
    total_contradiction_count: Decimal
    total_stale_source_count: Decimal
    reviewer_capacity_gap_count: Decimal
    max_review_priority_score: Decimal
    average_review_priority_score: Decimal
    status: str
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamSpecialistEvidenceReviewQueueReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_evidence_count",
            "source_family_gap_count",
            "total_unresolved_claim_count",
            "total_contradiction_count",
            "total_stale_source_count",
            "reviewer_capacity_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_review_priority_score",
            "average_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report_metrics(self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_research_team_specialist_evidence_review_queue_report(
    items: list[ResearchTeamSpecialistEvidenceReviewQueueItem]
    | tuple[ResearchTeamSpecialistEvidenceReviewQueueItem, ...],
    *,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceReviewQueueReport:
    if type(config) is not ResearchTeamSpecialistEvidenceReviewQueueReportConfig:
        raise ValueError("config must be an evidence review queue report config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    queue_items = _normalize_items(items, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_item(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in queue_items
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    return ResearchTeamSpecialistEvidenceReviewQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        stale_evidence_count=_count(
            sum(1 for row in rows if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)),
        ),
        source_family_gap_count=_count(
            sum(1 for row in rows if _has_any(row, _FAMILY_WATCH_REASON, _FAMILY_BLOCK_REASON)),
        ),
        total_unresolved_claim_count=_sum_rows(rows, "unresolved_claim_count"),
        total_contradiction_count=_sum_rows(rows, "contradiction_count"),
        total_stale_source_count=_sum_rows(rows, "stale_source_count"),
        reviewer_capacity_gap_count=_count(
            sum(1 for row in rows if _REVIEWER_BLOCK_REASON in row.reason_codes),
        ),
        max_review_priority_score=_max_review_priority_score(rows),
        average_review_priority_score=_average_review_priority_score(rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_specialist_evidence_review_queue_report_digest(
    report: ResearchTeamSpecialistEvidenceReviewQueueReport,
) -> str:
    payload = research_team_specialist_evidence_review_queue_report_payload(report)
    digest = payload.get(_DIGEST_FIELD)
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    return digest


def research_team_specialist_evidence_review_queue_report_payload(
    report: ResearchTeamSpecialistEvidenceReviewQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_non_string_numeric(report)
        _require_json_payload("evidence review queue payload", report)
        _require_payload_statuses(report)
        _reject_unsafe_public_payload("evidence review queue payload", report)
        _require_payload_shape(report)
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchTeamSpecialistEvidenceReviewQueueReport:
        raise ValueError("report must be an evidence review queue report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload("evidence review queue payload", payload)
    _validate_payload_digest(payload)
    return payload


def _row_from_item(
    item: ResearchTeamSpecialistEvidenceReviewQueueItem,
    *,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistEvidenceReviewQueueRow:
    queue_age_seconds = _seconds_between(generated_at, item.queued_at)
    evidence_age_seconds = _seconds_between(generated_at, item.evidence_observed_at)
    queue_age_component = _capped_ratio(queue_age_seconds, config.queue_block_age_seconds)
    evidence_age_component = _capped_ratio(evidence_age_seconds, config.evidence_block_age_seconds)
    source_family_gap = _source_family_gap(item, config)
    unresolved_claim_component = _capped_ratio(
        item.unresolved_claim_count,
        config.unresolved_block_claim_count,
    )
    contradiction_component = _capped_ratio(
        item.contradiction_count,
        config.contradiction_block_count,
    )
    stale_source_component = _capped_ratio(
        item.stale_source_count,
        config.stale_source_block_count,
    )
    reviewer_capacity_gap = _reviewer_capacity_gap(item, config)
    complexity_component = item.review_complexity_score
    reason_codes = _row_reason_codes(
        item,
        config=config,
        queue_age_seconds=queue_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
    )
    return ResearchTeamSpecialistEvidenceReviewQueueRow(
        team_ref=item.team_ref,
        specialist_ref=item.specialist_ref,
        evidence_packet_digest=item.evidence_packet_digest,
        source_bundle_digest=item.source_bundle_digest,
        queued_at=item.queued_at,
        evidence_observed_at=item.evidence_observed_at,
        queue_age_seconds=queue_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        source_family_count=item.source_family_count,
        unresolved_claim_count=item.unresolved_claim_count,
        contradiction_count=item.contradiction_count,
        stale_source_count=item.stale_source_count,
        reviewer_available_count=item.reviewer_available_count,
        review_complexity_score=item.review_complexity_score,
        queue_age_component=queue_age_component,
        evidence_age_component=evidence_age_component,
        source_family_gap=source_family_gap,
        unresolved_claim_component=unresolved_claim_component,
        contradiction_component=contradiction_component,
        stale_source_component=stale_source_component,
        reviewer_capacity_gap=reviewer_capacity_gap,
        complexity_component=complexity_component,
        review_priority_score=_review_priority_score(
            queue_age_component=queue_age_component,
            evidence_age_component=evidence_age_component,
            source_family_gap=source_family_gap,
            unresolved_claim_component=unresolved_claim_component,
            contradiction_component=contradiction_component,
            stale_source_component=stale_source_component,
            reviewer_capacity_gap=reviewer_capacity_gap,
            complexity_component=complexity_component,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        _validation_config=config,
    )


def _row_reason_codes(
    item: ResearchTeamSpecialistEvidenceReviewQueueItem,
    *,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
    queue_age_seconds: Decimal,
    evidence_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if queue_age_seconds >= config.queue_block_age_seconds:
        reason_codes.append(_QUEUE_BLOCK_REASON)
    elif queue_age_seconds >= config.queue_watch_age_seconds:
        reason_codes.append(_QUEUE_WATCH_REASON)
    if evidence_age_seconds >= config.evidence_block_age_seconds:
        reason_codes.append(_EVIDENCE_BLOCK_REASON)
    elif evidence_age_seconds >= config.evidence_watch_age_seconds:
        reason_codes.append(_EVIDENCE_WATCH_REASON)
    if item.source_family_count <= _ZERO_COUNT:
        reason_codes.append(_FAMILY_BLOCK_REASON)
    elif item.source_family_count < config.min_pass_source_family_count:
        reason_codes.append(_FAMILY_WATCH_REASON)
    if item.unresolved_claim_count >= config.unresolved_block_claim_count:
        reason_codes.append(_CLAIM_BLOCK_REASON)
    elif item.unresolved_claim_count >= config.unresolved_watch_claim_count:
        reason_codes.append(_CLAIM_WATCH_REASON)
    if item.contradiction_count >= config.contradiction_block_count:
        reason_codes.append(_CONTRADICTION_BLOCK_REASON)
    elif item.contradiction_count >= config.contradiction_watch_count:
        reason_codes.append(_CONTRADICTION_WATCH_REASON)
    if item.stale_source_count >= config.stale_source_block_count:
        reason_codes.append(_STALE_BLOCK_REASON)
    elif item.stale_source_count >= config.stale_source_watch_count:
        reason_codes.append(_STALE_WATCH_REASON)
    if item.reviewer_available_count < config.min_reviewer_available_count:
        reason_codes.append(_REVIEWER_BLOCK_REASON)
    if item.review_complexity_score >= config.complexity_block_score:
        reason_codes.append(_COMPLEXITY_BLOCK_REASON)
    elif item.review_complexity_score >= config.complexity_watch_score:
        reason_codes.append(_COMPLEXITY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...]) -> str:
    if not rows:
        return "pass"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _PASS_REASON
    }
    if not reason_codes:
        return (_PASS_REASON,)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _review_priority_score(
    *,
    queue_age_component: Decimal,
    evidence_age_component: Decimal,
    source_family_gap: Decimal,
    unresolved_claim_component: Decimal,
    contradiction_component: Decimal,
    stale_source_component: Decimal,
    reviewer_capacity_gap: Decimal,
    complexity_component: Decimal,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
) -> Decimal:
    return _six(
        queue_age_component * config.queue_age_weight
        + evidence_age_component * config.evidence_age_weight
        + source_family_gap * config.source_family_weight
        + unresolved_claim_component * config.unresolved_claim_weight
        + contradiction_component * config.contradiction_weight
        + stale_source_component * config.stale_source_weight
        + reviewer_capacity_gap * config.reviewer_capacity_weight
        + complexity_component * config.complexity_weight,
    )


def _source_family_gap(
    item: ResearchTeamSpecialistEvidenceReviewQueueItem,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
) -> Decimal:
    if item.source_family_count >= config.min_pass_source_family_count:
        return _ZERO_SCORE
    return _six(
        (config.min_pass_source_family_count - item.source_family_count)
        / config.min_pass_source_family_count,
    )


def _reviewer_capacity_gap(
    item: ResearchTeamSpecialistEvidenceReviewQueueItem,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
) -> Decimal:
    if item.reviewer_available_count >= config.min_reviewer_available_count:
        return _ZERO_SCORE
    return _six(
        (config.min_reviewer_available_count - item.reviewer_available_count)
        / config.min_reviewer_available_count,
    )


def _max_review_priority_score(
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return max(row.review_priority_score for row in rows)


def _average_review_priority_score(
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(sum((row.review_priority_score for row in rows), _ZERO_SCORE) / Decimal(len(rows)))


def _has_any(
    row: ResearchTeamSpecialistEvidenceReviewQueueRow,
    watch_reason: str,
    block_reason: str,
) -> bool:
    return watch_reason in row.reason_codes or block_reason in row.reason_codes


def _normalize_items(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistEvidenceReviewQueueItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    items = tuple(value)
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistEvidenceReviewQueueItem:
            raise ValueError("items must contain exact evidence review queue items")
        _require_hard_flags("item", item)
        if item.queued_at > generated_at:
            raise ValueError("queued_at must not be in the future")
        if item.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
        if item.evidence_packet_digest in seen:
            raise ValueError("items must not repeat evidence packet digests")
        seen.add(item.evidence_packet_digest)
    return tuple(sorted(items, key=_item_sort_key))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistEvidenceReviewQueueRow:
            raise ValueError("rows must contain exact evidence review queue rows")
        _require_hard_flags("row", row)
        if row.evidence_packet_digest in seen:
            raise ValueError("rows must not repeat evidence packet digests")
        seen.add(row.evidence_packet_digest)
        _validate_row_digest(row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by refs and digest")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason code counts")
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: _reason_index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted")
    return rows


def _validate_row_metrics(
    row: ResearchTeamSpecialistEvidenceReviewQueueRow,
    *,
    config: ResearchTeamSpecialistEvidenceReviewQueueReportConfig,
) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.review_priority_score != _review_priority_score(
        queue_age_component=row.queue_age_component,
        evidence_age_component=row.evidence_age_component,
        source_family_gap=row.source_family_gap,
        unresolved_claim_component=row.unresolved_claim_component,
        contradiction_component=row.contradiction_component,
        stale_source_component=row.stale_source_component,
        reviewer_capacity_gap=row.reviewer_capacity_gap,
        complexity_component=row.complexity_component,
        config=config,
    ):
        raise ValueError("review_priority_score must match row components")


def _validate_report_metrics(report: ResearchTeamSpecialistEvidenceReviewQueueReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.stale_evidence_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _EVIDENCE_WATCH_REASON, _EVIDENCE_BLOCK_REASON)
        ),
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.source_family_gap_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any(row, _FAMILY_WATCH_REASON, _FAMILY_BLOCK_REASON)
        ),
    ):
        raise ValueError("source_family_gap_count must match rows")
    if report.total_unresolved_claim_count != _sum_rows(report.rows, "unresolved_claim_count"):
        raise ValueError("total_unresolved_claim_count must match rows")
    if report.total_contradiction_count != _sum_rows(report.rows, "contradiction_count"):
        raise ValueError("total_contradiction_count must match rows")
    if report.total_stale_source_count != _sum_rows(report.rows, "stale_source_count"):
        raise ValueError("total_stale_source_count must match rows")
    if report.reviewer_capacity_gap_count != _count(
        sum(1 for row in report.rows if _REVIEWER_BLOCK_REASON in row.reason_codes),
    ):
        raise ValueError("reviewer_capacity_gap_count must match rows")
    if report.max_review_priority_score != _max_review_priority_score(report.rows):
        raise ValueError("max_review_priority_score must match rows")
    if report.average_review_priority_score != _average_review_priority_score(report.rows):
        raise ValueError("average_review_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _item_sort_key(
    item: ResearchTeamSpecialistEvidenceReviewQueueItem,
) -> tuple[str, str, str]:
    return (item.team_ref, item.specialist_ref, item.evidence_packet_digest)


def _row_sort_key(row: ResearchTeamSpecialistEvidenceReviewQueueRow) -> tuple[int, Decimal, str, str, str]:
    return (
        -_status_rank(row.status),
        -row.review_priority_score,
        row.team_ref,
        row.specialist_ref,
        row.evidence_packet_digest,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _normalize_nonnegative_six_place_decimal("seconds", _six(seconds))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_SCORE:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < _ZERO_SCORE:
        return _ZERO_SCORE
    if value > _ONE_SCORE:
        return _ONE_SCORE
    return _six(value)


def _sum_rows(
    rows: tuple[ResearchTeamSpecialistEvidenceReviewQueueRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), _ZERO_COUNT),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _six(value)
    if quantized < _ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _reason_index(reason_code: str) -> int:
    return _REASON_SEQUENCE.index(reason_code)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(field_name: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exact {expected.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field_name} must be a sha256 digest")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    _reject_unsafe_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")
    _reject_payload_flag_downgrades(payload)


def _reject_payload_flag_downgrades(value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"payload {field_name} must be True")
        for item in value.values():
            _reject_payload_flag_downgrades(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_payload_flag_downgrades(item)


def _require_json_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} JSON object keys must be strings")
            _require_json_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _require_json_payload(label, item)
        return
    if type(value) is tuple:
        raise ValueError(f"{label} JSON arrays must use lists")
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} contains an unsupported JSON value")


def _require_payload_statuses(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key == "status" or key.endswith("_status"):
                _require_member(
                    key,
                    item,
                    RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES,
                )
            _require_payload_statuses(item)
        return
    if type(value) is list:
        for item in value:
            _require_payload_statuses(item)


def _require_payload_shape(payload: dict[str, Any]) -> None:
    if frozenset(payload) != _REPORT_PAYLOAD_FIELDS:
        raise ValueError("payload fields must match the evidence review queue report schema")
    _require_payload_datetime("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    for field_name in _REPORT_COUNT_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, payload[field_name], "count")
    for field_name in _REPORT_SCORE_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, payload[field_name], "unit")
    _require_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_validation_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )

    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a JSON list")
    for row in rows:
        _require_row_payload_shape(row)

    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a JSON list")
    for reason_code_count in reason_code_counts:
        _require_reason_code_count_payload_shape(reason_code_count)


def _require_row_payload_shape(value: object) -> None:
    if type(value) is not dict or frozenset(value) != _ROW_PAYLOAD_FIELDS:
        raise ValueError("row fields must match the evidence review queue row schema")
    for field_name in ("team_ref", "specialist_ref"):
        _require_public_string(field_name, value[field_name])
    for field_name in ("evidence_packet_digest", "source_bundle_digest"):
        _require_digest(field_name, value[field_name])
    for field_name in ("queued_at", "evidence_observed_at"):
        _require_payload_datetime(field_name, value[field_name])
    for field_name in _ROW_COUNT_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, value[field_name], "count")
    for field_name in _ROW_DURATION_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, value[field_name], "duration")
    for field_name in _ROW_SCORE_PAYLOAD_FIELDS:
        _require_payload_decimal(field_name, value[field_name], "unit")
    _require_payload_reason_codes("reason_codes", value["reason_codes"])
    _require_validation_digest(
        "derived_validation_digest",
        value["derived_validation_digest"],
    )


def _require_reason_code_count_payload_shape(value: object) -> None:
    if type(value) is not dict or frozenset(value) != _REASON_CODE_COUNT_PAYLOAD_FIELDS:
        raise ValueError("reason code count fields must match the report schema")
    _require_reason_code("reason_code", value["reason_code"])
    _require_payload_decimal("count", value["count"], "positive_count")


def _require_payload_decimal(field_name: str, value: object, kind: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if kind == "count":
        normalized = _normalize_nonnegative_count(field_name, decimal_value)
    elif kind == "positive_count":
        normalized = _normalize_positive_count(field_name, decimal_value)
    elif kind == "duration":
        normalized = _normalize_nonnegative_six_place_decimal(field_name, decimal_value)
    elif kind == "unit":
        normalized = _normalize_unit_decimal(field_name, decimal_value)
    else:
        raise ValueError("unsupported payload Decimal kind")
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _validate_row_digest(row: ResearchTeamSpecialistEvidenceReviewQueueRow) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest tamper detected in row")


def _validate_report_digest(report: ResearchTeamSpecialistEvidenceReviewQueueReport) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest tamper detected in report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    expected = _payload_digest(payload)
    if payload.get(_DIGEST_FIELD) != expected:
        raise ValueError("derived_validation_digest must match payload")
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict and _DIGEST_FIELD in row:
                expected_row_digest = _payload_digest(row)
                if row.get(_DIGEST_FIELD) != expected_row_digest:
                    raise ValueError("derived_validation_digest must match payload row")


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = _strip_digest_fields(payload)
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    stripped = _strip_digest_fields(payload)
    encoded = json.dumps(stripped, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _strip_digest_fields(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != _DIGEST_FIELD
        }
    if type(value) is list:
        return [_strip_digest_fields(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float values are not supported in public payloads")
    if type(value) is int:
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public Decimal values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_EVIDENCE_REVIEW_QUEUE_STATUSES",
    "ResearchTeamSpecialistEvidenceReviewQueueReportConfig",
    "ResearchTeamSpecialistEvidenceReviewQueueItem",
    "ResearchTeamSpecialistEvidenceReviewQueueReasonCodeCount",
    "ResearchTeamSpecialistEvidenceReviewQueueRow",
    "ResearchTeamSpecialistEvidenceReviewQueueReport",
    "build_research_team_specialist_evidence_review_queue_report",
    "research_team_specialist_evidence_review_queue_report_digest",
    "research_team_specialist_evidence_review_queue_report_payload",
)
