"""Immutable summaries for specialist research packet review."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION = (
    "team-research-review-checklist-v0"
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = tuple(
    "".join(chr(code) for code in codes)
    for codes in (
        (109, 97, 114, 107, 101, 116, 95, 115, 108, 117, 103),
        (113, 117, 101, 115, 116, 105, 111, 110),
        (105, 110, 118, 101, 115, 116, 109, 101, 110, 116),
        (114, 97, 110, 107, 105, 110, 103),
        (98, 117, 121),
        (115, 101, 108, 108),
        (116, 114, 97, 100, 101),
        (119, 97, 108, 108, 101, 116),
        (111, 114, 100, 101, 114),
        (112, 111, 115, 105, 116, 105, 111, 110),
        (115, 116, 114, 97, 116, 101, 103, 121, 95, 119, 101, 105, 103, 104, 116),
        (97, 117, 116, 104),
        (110, 101, 116, 119, 111, 114, 107),
        (108, 105, 118, 101),
        (112, 114, 105, 118, 97, 116, 101, 95, 107, 101, 121),
    )
)

PASS_REASON = "team_research_review_checklist_passed"
BLOCKERS_REASON = "team_research_review_blockers_present"
CALIBRATION_REASON = "team_research_review_calibration_missing"
EVIDENCE_REASON = "team_research_review_evidence_incomplete"
MEMORY_REASON = "team_research_review_memory_not_ready"
SOURCE_REASON = "team_research_review_source_not_fresh"
EMPTY_REASON = "team_research_review_empty_packets"

REASON_CODES = (
    PASS_REASON,
    BLOCKERS_REASON,
    CALIBRATION_REASON,
    EVIDENCE_REASON,
    MEMORY_REASON,
    SOURCE_REASON,
    EMPTY_REASON,
)
SUMMARY_STATUSES = ("pass", "blocked")
SOURCE_STATUSES = ("fresh", "stale", "missing")
NEXT_STEPS = {
    "pass": "review_complete",
    "blocked": "resolve_research_review_blockers",
}
MASK = "<redacted>"

__all__ = (
    "DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION",
    "TeamResearchReviewChecklistConfig",
    "TeamResearchReviewChecklistItem",
    "TeamResearchReviewChecklistReasonCodeCount",
    "TeamResearchReviewChecklistReport",
    "TeamResearchReviewChecklistTeamSummary",
    "build_team_research_review_checklist_report",
)


@dataclass(frozen=True)
class TeamResearchReviewChecklistConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_REVIEW_CHECKLIST_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_count_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamResearchReviewChecklistItem:
    team_id: str
    packet_id: str
    evidence_completion_ratio: Decimal
    latest_source_observed_at: datetime | None
    memory_ready: bool
    calibration_available: bool
    blocker_codes: tuple[str, ...] = ()
    reviewer_notes: tuple[str, ...] = ()
    source_status: str | None = None
    source_age_seconds: Decimal | None = None
    redacted_reviewer_notes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("packet_id", self.packet_id)
        object.__setattr__(
            self,
            "evidence_completion_ratio",
            _ratio("evidence_completion_ratio", self.evidence_completion_ratio),
        )
        if self.latest_source_observed_at is not None:
            object.__setattr__(
                self,
                "latest_source_observed_at",
                _as_utc("latest_source_observed_at", self.latest_source_observed_at),
            )
        _require_bool("memory_ready", self.memory_ready)
        _require_bool("calibration_available", self.calibration_available)
        object.__setattr__(
            self,
            "blocker_codes",
            _normalize_string_tuple(
                "blocker_codes",
                self.blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_notes",
            _redact_notes(
                _normalize_string_tuple(
                    "reviewer_notes",
                    self.reviewer_notes,
                    allow_empty=True,
                ),
            ),
        )
        if self.source_status is not None:
            _require_source_status("source_status", self.source_status)
        if self.source_age_seconds is not None:
            object.__setattr__(
                self,
                "source_age_seconds",
                _require_nonnegative_count_decimal(
                    "source_age_seconds",
                    self.source_age_seconds,
                ),
            )
        object.__setattr__(
            self,
            "redacted_reviewer_notes",
            _normalize_redacted_notes(self.redacted_reviewer_notes, self.reviewer_notes),
        )
        _validate_item_shape(self)
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload(
            "team research review checklist item",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamResearchReviewChecklistReasonCodeCount:
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
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamResearchReviewChecklistTeamSummary:
    team_id: str
    packet_count: Decimal
    complete_evidence_count: Decimal
    fresh_source_count: Decimal
    memory_ready_count: Decimal
    calibration_available_count: Decimal
    blocked_packet_count: Decimal
    evidence_completion_ratio: Decimal | None
    summary_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for name in (
            "packet_count",
            "complete_evidence_count",
            "fresh_source_count",
            "memory_ready_count",
            "calibration_available_count",
            "blocked_packet_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        if self.evidence_completion_ratio is not None:
            object.__setattr__(
                self,
                "evidence_completion_ratio",
                _ratio("evidence_completion_ratio", self.evidence_completion_ratio),
            )
        _require_summary_status("summary_status", self.summary_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_team_summary_shape(self)
        _require_hard_flags("team_summary", self)


@dataclass(frozen=True)
class TeamResearchReviewChecklistReport:
    generated_at: datetime
    config_version: str
    summary_status: str
    review_next_step: str
    packet_count: Decimal
    complete_evidence_count: Decimal
    fresh_source_count: Decimal
    memory_ready_count: Decimal
    calibration_available_count: Decimal
    blocked_packet_count: Decimal
    incomplete_evidence_count: Decimal
    stale_or_missing_source_count: Decimal
    memory_not_ready_count: Decimal
    calibration_missing_count: Decimal
    evidence_completion_ratio: Decimal | None
    derived_validation_digest: str
    items: tuple[TeamResearchReviewChecklistItem, ...]
    team_summaries: tuple[TeamResearchReviewChecklistTeamSummary, ...]
    reason_code_counts: tuple[TeamResearchReviewChecklistReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_summary_status("summary_status", self.summary_status)
        _require_canonical_string("review_next_step", self.review_next_step)
        for name in (
            "packet_count",
            "complete_evidence_count",
            "fresh_source_count",
            "memory_ready_count",
            "calibration_available_count",
            "blocked_packet_count",
            "incomplete_evidence_count",
            "stale_or_missing_source_count",
            "memory_not_ready_count",
            "calibration_missing_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        if self.evidence_completion_ratio is not None:
            object.__setattr__(
                self,
                "evidence_completion_ratio",
                _ratio("evidence_completion_ratio", self.evidence_completion_ratio),
            )
        object.__setattr__(self, "items", _normalize_items(self.items))
        object.__setattr__(
            self,
            "team_summaries",
            _normalize_team_summaries(self.team_summaries),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_shape(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(
            "team research review checklist report",
            _payload_value(asdict(self)),
        )

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("team research review checklist payload", payload)
        if not isinstance(payload, dict):
            raise ValueError("team research review checklist payload must be an object")
        return payload


def build_team_research_review_checklist_report(
    items: list[TeamResearchReviewChecklistItem]
    | tuple[TeamResearchReviewChecklistItem, ...],
    *,
    config: TeamResearchReviewChecklistConfig,
    generated_at: datetime,
) -> TeamResearchReviewChecklistReport:
    if type(config) is not TeamResearchReviewChecklistConfig:
        raise ValueError("config must be a TeamResearchReviewChecklistConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_raw_items(items)
    reviewed_items = _reviewed_items(
        normalized_items,
        generated_at=generated_at_utc,
        max_source_age_seconds=config.max_source_age_seconds,
    )
    packet_count = len(reviewed_items)
    complete_evidence_count = sum(
        1 for item in reviewed_items if item.evidence_completion_ratio == ONE
    )
    fresh_source_count = sum(1 for item in reviewed_items if item.source_status == "fresh")
    memory_ready_count = sum(1 for item in reviewed_items if item.memory_ready)
    calibration_available_count = sum(
        1 for item in reviewed_items if item.calibration_available
    )
    blocked_packet_count = sum(1 for item in reviewed_items if item.blocker_codes)
    reason_codes = _report_reason_codes(reviewed_items)
    summary_status = _summary_status(reason_codes)

    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "summary_status": summary_status,
        "review_next_step": NEXT_STEPS[summary_status],
        "packet_count": _count_decimal(packet_count),
        "complete_evidence_count": _count_decimal(complete_evidence_count),
        "fresh_source_count": _count_decimal(fresh_source_count),
        "memory_ready_count": _count_decimal(memory_ready_count),
        "calibration_available_count": _count_decimal(calibration_available_count),
        "blocked_packet_count": _count_decimal(blocked_packet_count),
        "incomplete_evidence_count": _count_decimal(
            packet_count - complete_evidence_count,
        ),
        "stale_or_missing_source_count": _count_decimal(packet_count - fresh_source_count),
        "memory_not_ready_count": _count_decimal(packet_count - memory_ready_count),
        "calibration_missing_count": _count_decimal(
            packet_count - calibration_available_count,
        ),
        "evidence_completion_ratio": _average_ratio(
            tuple(item.evidence_completion_ratio for item in reviewed_items),
        ),
        "items": reviewed_items,
        "team_summaries": _team_summaries(reviewed_items),
        "reason_code_counts": _reason_code_counts(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _derived_validation_digest(report_values)
    return TeamResearchReviewChecklistReport(**report_values)


def _reviewed_items(
    items: tuple[TeamResearchReviewChecklistItem, ...],
    *,
    generated_at: datetime,
    max_source_age_seconds: Decimal,
) -> tuple[TeamResearchReviewChecklistItem, ...]:
    return tuple(
        sorted(
            (
                _reviewed_item(
                    item,
                    generated_at=generated_at,
                    max_source_age_seconds=max_source_age_seconds,
                )
                for item in items
            ),
            key=lambda item: (item.team_id, item.packet_id),
        ),
    )


def _reviewed_item(
    item: TeamResearchReviewChecklistItem,
    *,
    generated_at: datetime,
    max_source_age_seconds: Decimal,
) -> TeamResearchReviewChecklistItem:
    if item.latest_source_observed_at is None:
        source_status = "missing"
        source_age_seconds = None
    else:
        if item.latest_source_observed_at > generated_at:
            raise ValueError("latest_source_observed_at must not be in the future")
        source_age_seconds = _age_seconds(generated_at, item.latest_source_observed_at)
        source_status = (
            "fresh" if source_age_seconds <= max_source_age_seconds else "stale"
        )
    return TeamResearchReviewChecklistItem(
        team_id=item.team_id,
        packet_id=item.packet_id,
        evidence_completion_ratio=item.evidence_completion_ratio,
        latest_source_observed_at=item.latest_source_observed_at,
        memory_ready=item.memory_ready,
        calibration_available=item.calibration_available,
        blocker_codes=item.blocker_codes,
        reviewer_notes=item.reviewer_notes,
        source_status=source_status,
        source_age_seconds=source_age_seconds,
        redacted_reviewer_notes=_redact_notes(item.reviewer_notes),
    )


def _team_summaries(
    items: tuple[TeamResearchReviewChecklistItem, ...],
) -> tuple[TeamResearchReviewChecklistTeamSummary, ...]:
    team_ids = tuple(sorted({item.team_id for item in items}))
    return tuple(_team_summary(team_id, items) for team_id in team_ids)


def _team_summary(
    team_id: str,
    items: tuple[TeamResearchReviewChecklistItem, ...],
) -> TeamResearchReviewChecklistTeamSummary:
    team_items = tuple(item for item in items if item.team_id == team_id)
    reason_codes = _report_reason_codes(team_items)
    return TeamResearchReviewChecklistTeamSummary(
        team_id=team_id,
        packet_count=_count_decimal(len(team_items)),
        complete_evidence_count=_count_decimal(
            sum(1 for item in team_items if item.evidence_completion_ratio == ONE),
        ),
        fresh_source_count=_count_decimal(
            sum(1 for item in team_items if item.source_status == "fresh"),
        ),
        memory_ready_count=_count_decimal(
            sum(1 for item in team_items if item.memory_ready),
        ),
        calibration_available_count=_count_decimal(
            sum(1 for item in team_items if item.calibration_available),
        ),
        blocked_packet_count=_count_decimal(
            sum(1 for item in team_items if item.blocker_codes),
        ),
        evidence_completion_ratio=_average_ratio(
            tuple(item.evidence_completion_ratio for item in team_items),
        ),
        summary_status=_summary_status(reason_codes),
        reason_codes=reason_codes,
    )


def _report_reason_codes(
    items: tuple[TeamResearchReviewChecklistItem, ...],
) -> tuple[str, ...]:
    if not items:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(item.blocker_codes for item in items):
        reason_codes.append(BLOCKERS_REASON)
    if any(not item.calibration_available for item in items):
        reason_codes.append(CALIBRATION_REASON)
    if any(item.evidence_completion_ratio < ONE for item in items):
        reason_codes.append(EVIDENCE_REASON)
    if any(not item.memory_ready for item in items):
        reason_codes.append(MEMORY_REASON)
    if any(item.source_status != "fresh" for item in items):
        reason_codes.append(SOURCE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if reason_codes:
        return "blocked"
    raise ValueError("reason_codes must contain at least one value")


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return (sum(values, ZERO) / Decimal(len(values))).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamResearchReviewChecklistReasonCodeCount, ...]:
    return tuple(
        TeamResearchReviewChecklistReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(reason_codes.count(reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _normalize_raw_items(
    items: list[TeamResearchReviewChecklistItem]
    | tuple[TeamResearchReviewChecklistItem, ...],
) -> tuple[TeamResearchReviewChecklistItem, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized = tuple(items)
    seen_packet_ids: set[str] = set()
    for item in normalized:
        if type(item) is not TeamResearchReviewChecklistItem:
            raise ValueError("items must contain TeamResearchReviewChecklistItem values")
        _require_hard_flags("item", item)
        if item.packet_id in seen_packet_ids:
            raise ValueError("items packet_id values must be unique")
        seen_packet_ids.add(item.packet_id)
    return normalized


def _normalize_items(
    items: tuple[TeamResearchReviewChecklistItem, ...],
) -> tuple[TeamResearchReviewChecklistItem, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized = tuple(items)
    seen_packet_ids: set[str] = set()
    for item in normalized:
        if type(item) is not TeamResearchReviewChecklistItem:
            raise ValueError("items must contain TeamResearchReviewChecklistItem values")
        _require_hard_flags("item", item)
        if item.packet_id in seen_packet_ids:
            raise ValueError("items packet_id values must be unique")
        seen_packet_ids.add(item.packet_id)
    if normalized != tuple(sorted(normalized, key=lambda item: (item.team_id, item.packet_id))):
        raise ValueError("items must be sorted by team_id and packet_id")
    return normalized


def _normalize_team_summaries(
    summaries: tuple[TeamResearchReviewChecklistTeamSummary, ...],
) -> tuple[TeamResearchReviewChecklistTeamSummary, ...]:
    if type(summaries) not in (list, tuple):
        raise ValueError("team_summaries must be a list or tuple")
    normalized = tuple(summaries)
    seen_team_ids: set[str] = set()
    for summary in normalized:
        if type(summary) is not TeamResearchReviewChecklistTeamSummary:
            raise ValueError("team_summaries must contain team summary values")
        _require_hard_flags("team_summary", summary)
        if summary.team_id in seen_team_ids:
            raise ValueError("team_summaries team_id values must be unique")
        seen_team_ids.add(summary.team_id)
    if normalized != tuple(sorted(normalized, key=lambda summary: summary.team_id)):
        raise ValueError("team_summaries must be sorted by team_id")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[TeamResearchReviewChecklistReasonCodeCount, ...],
) -> tuple[TeamResearchReviewChecklistReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamResearchReviewChecklistReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts)
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _normalize_string_tuple(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must contain at least one value")
    for value in normalized:
        _require_canonical_string(name, value)
    if name == "blocker_codes" and len(set(normalized)) != len(normalized):
        raise ValueError("blocker_codes must be unique")
    if name == "blocker_codes" and normalized != tuple(sorted(normalized)):
        raise ValueError("blocker_codes must be sorted")
    return normalized


def _normalize_redacted_notes(
    redacted_notes: tuple[str, ...],
    reviewer_notes: tuple[str, ...],
) -> tuple[str, ...]:
    if redacted_notes:
        return _redact_notes(
            _normalize_string_tuple(
                "redacted_reviewer_notes",
                redacted_notes,
                allow_empty=True,
            ),
        )
    return reviewer_notes


def _redact_notes(notes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_redact_note(note) for note in notes)


def _redact_note(note: str) -> str:
    keys = (
        "dsn",
        "token",
        "secret",
        "api" + "_" + "key",
        "pass" + "word",
        "private" + "_" + "key",
    )
    pattern = re.compile(
        r"(?i)\b(" + "|".join(re.escape(key) for key in keys) + r")\s*=\s*[^;\s,)]*",
    )
    return pattern.sub(lambda match: f"sensitive={MASK}", note)


def _validate_item_shape(item: TeamResearchReviewChecklistItem) -> None:
    if item.source_status is None and item.source_age_seconds is not None:
        raise ValueError("source_age_seconds requires source_status")
    if item.source_status == "fresh" and item.source_age_seconds is None:
        raise ValueError("fresh source_status requires source_age_seconds")
    if item.source_status == "stale" and item.source_age_seconds is None:
        raise ValueError("stale source_status requires source_age_seconds")
    if item.source_status == "missing" and item.source_age_seconds is not None:
        raise ValueError("missing source_status cannot include source_age_seconds")


def _validate_team_summary_shape(summary: TeamResearchReviewChecklistTeamSummary) -> None:
    if summary.packet_count == ZERO:
        raise ValueError("packet_count must be positive for team_summaries")
    for name in (
        "complete_evidence_count",
        "fresh_source_count",
        "memory_ready_count",
        "calibration_available_count",
        "blocked_packet_count",
    ):
        if getattr(summary, name) > summary.packet_count:
            raise ValueError(f"{name} must not exceed packet_count")
    if summary.evidence_completion_ratio is None:
        raise ValueError("evidence_completion_ratio is required for team_summaries")
    if summary.summary_status != _summary_status(summary.reason_codes):
        raise ValueError("summary_status must match reason_codes")


def _validate_report_shape(report: TeamResearchReviewChecklistReport) -> None:
    if report.packet_count != _count_decimal(len(report.items)):
        raise ValueError("packet_count must match items")
    expected_complete = _count_decimal(
        sum(1 for item in report.items if item.evidence_completion_ratio == ONE),
    )
    if report.complete_evidence_count != expected_complete:
        raise ValueError("complete_evidence_count must match items")
    if report.fresh_source_count != _count_decimal(
        sum(1 for item in report.items if item.source_status == "fresh"),
    ):
        raise ValueError("fresh_source_count must match items")
    if report.memory_ready_count != _count_decimal(
        sum(1 for item in report.items if item.memory_ready),
    ):
        raise ValueError("memory_ready_count must match items")
    if report.calibration_available_count != _count_decimal(
        sum(1 for item in report.items if item.calibration_available),
    ):
        raise ValueError("calibration_available_count must match items")
    if report.blocked_packet_count != _count_decimal(
        sum(1 for item in report.items if item.blocker_codes),
    ):
        raise ValueError("blocked_packet_count must match items")
    if report.incomplete_evidence_count != report.packet_count - expected_complete:
        raise ValueError("incomplete_evidence_count must match items")
    if report.stale_or_missing_source_count != report.packet_count - report.fresh_source_count:
        raise ValueError("stale_or_missing_source_count must match items")
    if report.memory_not_ready_count != report.packet_count - report.memory_ready_count:
        raise ValueError("memory_not_ready_count must match items")
    if (
        report.calibration_missing_count
        != report.packet_count - report.calibration_available_count
    ):
        raise ValueError("calibration_missing_count must match items")
    if report.evidence_completion_ratio != _average_ratio(
        tuple(item.evidence_completion_ratio for item in report.items),
    ):
        raise ValueError("evidence_completion_ratio must match items")
    if report.team_summaries != _team_summaries(report.items):
        raise ValueError("team_summaries must summarize items")
    if report.reason_codes != _report_reason_codes(report.items):
        raise ValueError("reason_codes must match items")
    if report.summary_status != _summary_status(report.reason_codes):
        raise ValueError("summary_status must match reason_codes")
    if report.review_next_step != NEXT_STEPS[report.summary_status]:
        raise ValueError("review_next_step must match summary_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must summarize reason_codes")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.microseconds:
        return _count_decimal(delta.days * 86_400 + delta.seconds + 1)
    return _count_decimal(delta.days * 86_400 + delta.seconds)


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return str(value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP))
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) in (int, float):
        raise ValueError("payload numeric value must use Decimal")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not payload serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    normalized = value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    return normalized


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_sha256_digest(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} must contain known reason codes")


def _require_source_status(name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_STATUSES:
        raise ValueError(f"{name} must be fresh, stale, or missing")


def _require_summary_status(name: str, value: object) -> None:
    if type(value) is not str or value not in SUMMARY_STATUSES:
        raise ValueError(f"{name} must be pass or blocked")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_nonnegative_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be a nonnegative int")
    if value < 0:
        raise ValueError(f"{name} must be a nonnegative int")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be a positive int")
    if value <= 0:
        raise ValueError(f"{name} must be a positive int")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
