"""Read-only Phase 1 specialist source collection load balancer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_SOURCE_COLLECTION_LOAD_BALANCER_V2_CONFIG_VERSION = (
    "team-specialist-source-collection-load-balancer-v2"
)
ASSIGNMENT_STATUSES = ("watch", "blocked")
REPORT_STATUSES = ("ready", "watch", "blocked")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_PRIORITY_WEIGHT = Decimal("0.25")
_FIT_WEIGHT = Decimal("0.75")
_FOUR = Decimal("4")
_THREE = Decimal("3")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_TERMS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "mu" "tation",
    "b" "uy",
    "se" "ll",
    "tra" "de",
    "tra" "ding",
)
_REASON_SEQUENCE = (
    "queue_age_blocked",
    "queue_age_watch",
    "specialist_load_blocked",
    "specialist_load_watch",
    "category_expertise_strong",
    "category_expertise_weak",
    "source_family_gap_present",
    "source_family_skill_matched",
    "close_urgency_present",
    "contradiction_severity_present",
    "source_collection_load_balancer_ready",
    "source_collection_load_balancer_watch",
    "source_collection_load_balancer_blocked",
    "assignment_ranked",
    "assignment_unfilled",
)


@dataclass(frozen=True)
class TeamSpecialistSourceCollectionLoadBalancerV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_SOURCE_COLLECTION_LOAD_BALANCER_V2_CONFIG_VERSION
    queue_watch_age_seconds: Decimal = Decimal("3600.000000")
    queue_blocked_age_seconds: Decimal = Decimal("10800.000000")
    close_urgency_seconds: Decimal = Decimal("3600.000000")
    specialist_load_watch_ratio: Decimal = Decimal("0.750000")
    min_category_expertise_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "queue_watch_age_seconds",
            _normalize_positive_six_place_decimal(
                "queue_watch_age_seconds",
                self.queue_watch_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "queue_blocked_age_seconds",
            _normalize_positive_six_place_decimal(
                "queue_blocked_age_seconds",
                self.queue_blocked_age_seconds,
            ),
        )
        if self.queue_blocked_age_seconds < self.queue_watch_age_seconds:
            raise ValueError("queue_blocked_age_seconds must be at least queue_watch_age_seconds")
        object.__setattr__(
            self,
            "close_urgency_seconds",
            _normalize_positive_six_place_decimal(
                "close_urgency_seconds",
                self.close_urgency_seconds,
            ),
        )
        for field_name in (
            "specialist_load_watch_ratio",
            "min_category_expertise_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_score(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceCollectionQueueItemV2:
    collection_id: str
    team_id: str
    category_id: str
    source_family: str
    queued_at: datetime
    closes_at: datetime
    source_family_gap_score: Decimal
    contradiction_severity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("collection_id", "team_id", "category_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(self, "closes_at", _as_utc("closes_at", self.closes_at))
        for field_name in ("source_family_gap_score", "contradiction_severity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_score(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("queue item", self)
        _reject_unsafe_public_payload("queue item", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceCollectionSpecialistLoadV2:
    specialist_id: str
    team_id: str
    category_id: str
    source_families: tuple[str, ...]
    current_assignment_count: Decimal
    max_assignment_count: Decimal
    category_expertise_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("specialist_id", "team_id", "category_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families(self.source_families),
        )
        object.__setattr__(
            self,
            "current_assignment_count",
            _normalize_nonnegative_count(
                "current_assignment_count",
                self.current_assignment_count,
            ),
        )
        object.__setattr__(
            self,
            "max_assignment_count",
            _normalize_positive_count("max_assignment_count", self.max_assignment_count),
        )
        if self.current_assignment_count > self.max_assignment_count:
            raise ValueError("current_assignment_count must not exceed max_assignment_count")
        object.__setattr__(
            self,
            "category_expertise_score",
            _normalize_unit_score(
                "category_expertise_score",
                self.category_expertise_score,
            ),
        )
        _require_hard_flags("specialist", self)
        _reject_unsafe_public_payload("specialist", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistSourceCollectionAssignmentRowV2:
    collection_id: str
    team_id: str
    category_id: str
    source_family: str
    assignment_rank: Decimal
    assigned_specialist_id: str | None
    assignment_status: str
    queue_age_seconds: Decimal
    queue_age_score: Decimal
    specialist_load_ratio: Decimal
    specialist_remaining_capacity_count: Decimal
    category_expertise_score: Decimal
    source_family_gap_score: Decimal
    close_urgency_score: Decimal
    contradiction_severity_score: Decimal
    assignment_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("collection_id", "team_id", "category_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.assigned_specialist_id is not None:
            _require_canonical_string("assigned_specialist_id", self.assigned_specialist_id)
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "assignment_rank",
            _normalize_positive_count("assignment_rank", self.assignment_rank),
        )
        object.__setattr__(
            self,
            "specialist_remaining_capacity_count",
            _normalize_nonnegative_count(
                "specialist_remaining_capacity_count",
                self.specialist_remaining_capacity_count,
            ),
        )
        for field_name in (
            "queue_age_seconds",
            "queue_age_score",
            "specialist_load_ratio",
            "category_expertise_score",
            "source_family_gap_score",
            "close_urgency_score",
            "contradiction_severity_score",
            "assignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("assignment row", self)
        _reject_unsafe_public_payload("assignment row", _payload_value(self))
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match assignment row fields")


@dataclass(frozen=True)
class TeamSpecialistSourceCollectionLoadBalancerV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    queue_item_count: Decimal
    assigned_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    specialist_count: Decimal
    assignment_rows: tuple[TeamSpecialistSourceCollectionAssignmentRowV2, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "queue_item_count",
            "assigned_item_count",
            "watch_item_count",
            "blocked_item_count",
            "specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "assignment_rows",
            _normalize_assignment_rows(self.assignment_rows),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_counts(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_team_specialist_source_collection_load_balancer_v2(
    items: object,
    *,
    specialists: object,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceCollectionLoadBalancerV2Report:
    if type(config) is not TeamSpecialistSourceCollectionLoadBalancerV2Config:
        raise ValueError("config must be a TeamSpecialistSourceCollectionLoadBalancerV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_input_items(items, generated_at_utc)
    normalized_specialists = _normalize_specialists(specialists)
    rows = _ranked_assignment_rows(
        normalized_items,
        normalized_specialists,
        config=config,
        generated_at=generated_at_utc,
    )
    assigned_count = _count(
        sum(1 for row in rows if row.assignment_status == "watch"),
    )
    blocked_count = _count(
        sum(1 for row in rows if row.assignment_status == "blocked"),
    )
    report_status = _report_status(assigned_count, blocked_count)
    return TeamSpecialistSourceCollectionLoadBalancerV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        queue_item_count=_count(len(normalized_items)),
        assigned_item_count=assigned_count,
        watch_item_count=assigned_count,
        blocked_item_count=blocked_count,
        specialist_count=_count(len(normalized_specialists)),
        assignment_rows=rows,
        reason_codes=_report_reason_codes(rows, report_status),
    )


def team_specialist_source_collection_load_balancer_v2_payload(
    report: object,
) -> dict[str, Any]:
    if type(report) is TeamSpecialistSourceCollectionLoadBalancerV2Report:
        _validate_report_digest(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("payload", report)
        _require_payload_hard_flags(report)
        if _DIGEST_FIELD in report:
            _validate_payload_digest(report)
        return report
    raise ValueError("report must be a load balancer report or payload dict")


def _ranked_assignment_rows(
    items: tuple[TeamSpecialistSourceCollectionQueueItemV2, ...],
    specialists: tuple[TeamSpecialistSourceCollectionSpecialistLoadV2, ...],
    *,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    generated_at: datetime,
) -> tuple[TeamSpecialistSourceCollectionAssignmentRowV2, ...]:
    active_counts = {
        specialist.specialist_id: specialist.current_assignment_count
        for specialist in specialists
    }
    provisional_rows: list[TeamSpecialistSourceCollectionAssignmentRowV2] = []
    for item in sorted(
        items,
        key=lambda candidate: (
            -_item_priority_score(candidate, config=config, generated_at=generated_at),
            candidate.collection_id,
        ),
    ):
        row = _assignment_row(
            item,
            specialists,
            active_counts=active_counts,
            config=config,
            generated_at=generated_at,
        )
        provisional_rows.append(row)
        if row.assigned_specialist_id is not None:
            active_counts[row.assigned_specialist_id] += _COUNT_QUANTUM
    rows = tuple(
        sorted(
            provisional_rows,
            key=lambda row: (
                -row.assignment_score,
                row.collection_id,
            ),
        ),
    )
    return tuple(_with_assignment_rank(row, _count(index + 1)) for index, row in enumerate(rows))


def _assignment_row(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    specialists: tuple[TeamSpecialistSourceCollectionSpecialistLoadV2, ...],
    *,
    active_counts: dict[str, Decimal],
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceCollectionAssignmentRowV2:
    queue_age_seconds = _queue_age_seconds(item, generated_at)
    queue_age_score = _queue_age_score(queue_age_seconds, config)
    close_urgency_score = _close_urgency_score(item, generated_at, config)
    candidate = _best_specialist(
        item,
        specialists,
        active_counts=active_counts,
        config=config,
        generated_at=generated_at,
    )
    if candidate is None:
        return TeamSpecialistSourceCollectionAssignmentRowV2(
            collection_id=item.collection_id,
            team_id=item.team_id,
            category_id=item.category_id,
            source_family=item.source_family,
            assignment_rank=_COUNT_QUANTUM,
            assigned_specialist_id=None,
            assignment_status="blocked",
            queue_age_seconds=_six(queue_age_seconds),
            queue_age_score=_six(queue_age_score),
            specialist_load_ratio=_ONE_SCORE,
            specialist_remaining_capacity_count=_ZERO_COUNT,
            category_expertise_score=_ZERO_SCORE,
            source_family_gap_score=item.source_family_gap_score,
            close_urgency_score=_six(close_urgency_score),
            contradiction_severity_score=item.contradiction_severity_score,
            assignment_score=_ZERO_SCORE,
            reason_codes=_row_reason_codes(
                item,
            config=config,
            queue_age_seconds=queue_age_seconds,
            close_urgency_score=close_urgency_score,
            assigned=False,
            specialist=None,
            specialist_load_ratio=_ONE_SCORE,
            ),
        )
    specialist, assignment_score, specialist_load_ratio = candidate
    remaining_capacity = (
        specialist.max_assignment_count
        - active_counts[specialist.specialist_id]
        - _COUNT_QUANTUM
    )
    return TeamSpecialistSourceCollectionAssignmentRowV2(
        collection_id=item.collection_id,
        team_id=item.team_id,
        category_id=item.category_id,
        source_family=item.source_family,
        assignment_rank=_COUNT_QUANTUM,
        assigned_specialist_id=specialist.specialist_id,
        assignment_status="watch",
        queue_age_seconds=_six(queue_age_seconds),
        queue_age_score=_six(queue_age_score),
        specialist_load_ratio=_six(specialist_load_ratio),
        specialist_remaining_capacity_count=remaining_capacity,
        category_expertise_score=specialist.category_expertise_score,
        source_family_gap_score=item.source_family_gap_score,
        close_urgency_score=_six(close_urgency_score),
        contradiction_severity_score=item.contradiction_severity_score,
        assignment_score=_six(assignment_score),
        reason_codes=_row_reason_codes(
            item,
            config=config,
            queue_age_seconds=queue_age_seconds,
            close_urgency_score=close_urgency_score,
            assigned=True,
            specialist=specialist,
            specialist_load_ratio=specialist_load_ratio,
        ),
    )


def _with_assignment_rank(
    row: TeamSpecialistSourceCollectionAssignmentRowV2,
    assignment_rank: Decimal,
) -> TeamSpecialistSourceCollectionAssignmentRowV2:
    return TeamSpecialistSourceCollectionAssignmentRowV2(
        collection_id=row.collection_id,
        team_id=row.team_id,
        category_id=row.category_id,
        source_family=row.source_family,
        assignment_rank=assignment_rank,
        assigned_specialist_id=row.assigned_specialist_id,
        assignment_status=row.assignment_status,
        queue_age_seconds=row.queue_age_seconds,
        queue_age_score=row.queue_age_score,
        specialist_load_ratio=row.specialist_load_ratio,
        specialist_remaining_capacity_count=row.specialist_remaining_capacity_count,
        category_expertise_score=row.category_expertise_score,
        source_family_gap_score=row.source_family_gap_score,
        close_urgency_score=row.close_urgency_score,
        contradiction_severity_score=row.contradiction_severity_score,
        assignment_score=row.assignment_score,
        reason_codes=row.reason_codes,
    )


def _best_specialist(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    specialists: tuple[TeamSpecialistSourceCollectionSpecialistLoadV2, ...],
    *,
    active_counts: dict[str, Decimal],
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    generated_at: datetime,
) -> tuple[TeamSpecialistSourceCollectionSpecialistLoadV2, Decimal, Decimal] | None:
    candidates: list[tuple[Decimal, str, TeamSpecialistSourceCollectionSpecialistLoadV2, Decimal]] = []
    for specialist in specialists:
        if specialist.team_id != item.team_id or specialist.category_id != item.category_id:
            continue
        if item.source_family not in specialist.source_families:
            continue
        current_count = active_counts[specialist.specialist_id]
        if current_count >= specialist.max_assignment_count:
            continue
        load_ratio = _ratio(current_count, specialist.max_assignment_count)
        fit_score = _specialist_fit_score(specialist, load_ratio)
        assignment_score = _assignment_score(
            _item_priority_score(item, config=config, generated_at=generated_at),
            fit_score,
        )
        candidates.append((assignment_score, specialist.specialist_id, specialist, load_ratio))
    if not candidates:
        return None
    assignment_score, _, specialist, load_ratio = sorted(
        candidates,
        key=lambda candidate: (-candidate[0], candidate[1]),
    )[0]
    return specialist, assignment_score, load_ratio


def _item_priority_score(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    *,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    generated_at: datetime,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (
            _queue_age_score(_queue_age_seconds(item, generated_at), config)
            + item.source_family_gap_score
            + _close_urgency_score(item, generated_at, config)
            + item.contradiction_severity_score
        ) / _FOUR


def _specialist_fit_score(
    specialist: TeamSpecialistSourceCollectionSpecialistLoadV2,
    load_ratio: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (_ONE_SCORE + specialist.category_expertise_score + (_ONE_SCORE - load_ratio)) / _THREE


def _assignment_score(priority_score: Decimal, fit_score: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (_PRIORITY_WEIGHT * priority_score) + (_FIT_WEIGHT * fit_score)


def _queue_age_seconds(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    generated_at: datetime,
) -> Decimal:
    delta = generated_at - item.queued_at
    seconds = Decimal(str(delta.total_seconds()))
    if seconds < _ZERO_COUNT:
        raise ValueError("queued_at must not be after generated_at")
    return seconds


def _queue_age_score(
    queue_age_seconds: Decimal,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
) -> Decimal:
    return _capped_ratio(queue_age_seconds, config.queue_blocked_age_seconds)


def _close_urgency_score(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    generated_at: datetime,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
) -> Decimal:
    seconds_to_close = Decimal(str((item.closes_at - generated_at).total_seconds()))
    if seconds_to_close <= _ZERO_COUNT:
        return _ONE_SCORE
    if seconds_to_close >= config.close_urgency_seconds:
        return _ZERO_SCORE
    with localcontext(_DECIMAL_CONTEXT):
        return (config.close_urgency_seconds - seconds_to_close) / config.close_urgency_seconds


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_COUNT:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < _ZERO_SCORE:
        return _ZERO_SCORE
    if value > _ONE_SCORE:
        return _ONE_SCORE
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_COUNT:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return numerator / denominator


def _row_reason_codes(
    item: TeamSpecialistSourceCollectionQueueItemV2,
    *,
    config: TeamSpecialistSourceCollectionLoadBalancerV2Config,
    queue_age_seconds: Decimal,
    close_urgency_score: Decimal,
    assigned: bool,
    specialist: TeamSpecialistSourceCollectionSpecialistLoadV2 | None,
    specialist_load_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if queue_age_seconds >= config.queue_blocked_age_seconds:
        reason_codes.append("queue_age_blocked")
    elif queue_age_seconds >= config.queue_watch_age_seconds:
        reason_codes.append("queue_age_watch")
    if not assigned:
        reason_codes.append("specialist_load_blocked")
    elif specialist_load_ratio >= config.specialist_load_watch_ratio:
        reason_codes.append("specialist_load_watch")
    if specialist is not None:
        if specialist.category_expertise_score >= config.min_category_expertise_score:
            reason_codes.append("category_expertise_strong")
        else:
            reason_codes.append("category_expertise_weak")
    if item.source_family_gap_score > _ZERO_SCORE:
        reason_codes.append("source_family_gap_present")
    if assigned:
        reason_codes.append("source_family_skill_matched")
    if close_urgency_score > _ZERO_SCORE:
        reason_codes.append("close_urgency_present")
    if item.contradiction_severity_score > _ZERO_SCORE:
        reason_codes.append("contradiction_severity_present")
    reason_codes.append("assignment_ranked" if assigned else "assignment_unfilled")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[TeamSpecialistSourceCollectionAssignmentRowV2, ...],
    report_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in ("assignment_ranked", "assignment_unfilled"):
                reason_codes.append(reason_code)
    reason_codes.append(f"source_collection_load_balancer_{report_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(assigned_count: Decimal, blocked_count: Decimal) -> str:
    if blocked_count > _ZERO_COUNT:
        return "blocked"
    if assigned_count > _ZERO_COUNT:
        return "watch"
    return "ready"


def _normalize_input_items(
    value: object,
    generated_at: datetime,
) -> tuple[TeamSpecialistSourceCollectionQueueItemV2, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for item in rows:
        if type(item) is not TeamSpecialistSourceCollectionQueueItemV2:
            raise ValueError("items must contain exact queue items")
        _require_hard_flags("queue item", item)
        if item.collection_id in seen:
            raise ValueError("items must not repeat collection_id")
        seen.add(item.collection_id)
        _queue_age_seconds(item, generated_at)
    return rows


def _normalize_specialists(
    value: object,
) -> tuple[TeamSpecialistSourceCollectionSpecialistLoadV2, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("specialists must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for specialist in rows:
        if type(specialist) is not TeamSpecialistSourceCollectionSpecialistLoadV2:
            raise ValueError("specialists must contain exact specialist rows")
        _require_hard_flags("specialist", specialist)
        if specialist.specialist_id in seen:
            raise ValueError("specialists must not repeat specialist_id")
        seen.add(specialist.specialist_id)
    return tuple(sorted(rows, key=lambda specialist: specialist.specialist_id))


def _normalize_assignment_rows(
    value: object,
) -> tuple[TeamSpecialistSourceCollectionAssignmentRowV2, ...]:
    if type(value) is not tuple:
        raise ValueError("assignment_rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    expected_rank = _COUNT_QUANTUM
    for row in rows:
        if type(row) is not TeamSpecialistSourceCollectionAssignmentRowV2:
            raise ValueError("assignment_rows must contain exact assignment rows")
        _require_hard_flags("assignment row", row)
        if row.collection_id in seen:
            raise ValueError("assignment_rows must not repeat collection_id")
        seen.add(row.collection_id)
        if row.assignment_rank != expected_rank:
            raise ValueError("assignment_rank must be consecutive")
        _validate_row_digest(row)
        expected_rank += _COUNT_QUANTUM
    return rows


def _validate_report_counts(
    report: TeamSpecialistSourceCollectionLoadBalancerV2Report,
) -> None:
    if report.queue_item_count != _count(len(report.assignment_rows)):
        raise ValueError("queue_item_count must match assignment_rows")
    assigned_count = _count(
        sum(1 for row in report.assignment_rows if row.assignment_status == "watch"),
    )
    blocked_count = _count(
        sum(1 for row in report.assignment_rows if row.assignment_status == "blocked"),
    )
    if report.assigned_item_count != assigned_count:
        raise ValueError("assigned_item_count must match assignment_rows")
    if report.watch_item_count != assigned_count:
        raise ValueError("watch_item_count must match assignment_rows")
    if report.blocked_item_count != blocked_count:
        raise ValueError("blocked_item_count must match assignment_rows")
    if report.report_status != _report_status(assigned_count, blocked_count):
        raise ValueError("report_status must match assignment_rows")


def _normalize_source_families(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("source_families must be a tuple")
    if not value:
        raise ValueError("source_families must not be empty")
    families: list[str] = []
    seen: set[str] = set()
    for source_family in value:
        _require_canonical_string("source_families", source_family)
        if source_family in seen:
            raise ValueError("source_families must not repeat values")
        seen.add(source_family)
        families.append(source_family)
    return tuple(sorted(families))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_codes must be known")
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _count(value: int) -> Decimal:
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
    count = _normalize_nonnegative_count(field_name, value)
    if count <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return count


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


def _normalize_unit_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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


def _validate_row_digest(row: TeamSpecialistSourceCollectionAssignmentRowV2) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest tamper detected for assignment row")


def _validate_report_digest(
    report: TeamSpecialistSourceCollectionLoadBalancerV2Report,
) -> None:
    for row in report.assignment_rows:
        _validate_row_digest(row)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest tamper detected for report")


def _validate_payload_digest(payload: dict[str, object]) -> None:
    provided_digest = payload.get(_DIGEST_FIELD)
    if type(provided_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected_digest = _digest_value(payload)
    if provided_digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _digest_value(value: object) -> str:
    ready = _payload_value(value, omit_digest=True)
    _reject_unsafe_public_payload("derived validation payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, omit_digest: bool = False) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if omit_digest and field.name == _DIGEST_FIELD:
                continue
            ready[field.name] = _payload_value(
                getattr(value, field.name),
                omit_digest=omit_digest,
            )
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is list:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is dict:
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _payload_value(item, omit_digest=omit_digest)
        return ready
    if type(value) in (str, bool) or value is None:
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
    if type(value) is str:
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_COLLECTION_LOAD_BALANCER_V2_CONFIG_VERSION",
    "ASSIGNMENT_STATUSES",
    "REPORT_STATUSES",
    "TeamSpecialistSourceCollectionLoadBalancerV2Config",
    "TeamSpecialistSourceCollectionQueueItemV2",
    "TeamSpecialistSourceCollectionSpecialistLoadV2",
    "TeamSpecialistSourceCollectionAssignmentRowV2",
    "TeamSpecialistSourceCollectionLoadBalancerV2Report",
    "build_team_specialist_source_collection_load_balancer_v2",
    "team_specialist_source_collection_load_balancer_v2_payload",
)
