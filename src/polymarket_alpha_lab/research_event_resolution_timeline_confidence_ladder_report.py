"""Phase 1 report-only event resolution timeline confidence ladder."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION = (
    "research-event-resolution-timeline-confidence-ladder-report-v0"
)

LADDER_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PARTIAL_CONTRADICTION_MULTIPLIER = Decimal("0.400000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("que", "stion"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    "dsn",
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "end"),
)

REASON_CODE_SEQUENCE = (
    "timeline_confidence_blocked_dependency_pressure",
    "timeline_confidence_blocked_contradiction_pressure",
    "timeline_confidence_block_threshold",
    "timeline_confidence_watch_threshold",
    "timeline_confidence_pass_threshold",
    "timeline_confidence_confirmation_quorum_shortfall",
    "timeline_confidence_evidence_quorum_shortfall",
    "timeline_confidence_stale_update",
    "timeline_confidence_deadline_pressure",
    "timeline_confidence_overdue_resolution",
    "timeline_confidence_dependency_pressure",
    "timeline_confidence_contradiction_pressure",
    "timeline_confidence_empty",
    "timeline_confidence_block_present",
    "timeline_confidence_watch_present",
    "timeline_confidence_clear",
)


@dataclass(frozen=True)
class ResearchEventResolutionTimelineConfidenceLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION
    )
    pass_threshold: Decimal = Decimal("0.700000")
    watch_threshold: Decimal = Decimal("0.400000")
    required_confirmation_count: Decimal = Decimal("2.000000")
    required_independent_evidence_count: Decimal = Decimal("3.000000")
    blocked_unresolved_dependency_count: Decimal = Decimal("3.000000")
    blocked_contradiction_count: Decimal = Decimal("2.000000")
    fresh_timeline_seconds: Decimal = Decimal("3600.000000")
    stale_timeline_seconds: Decimal = Decimal("21600.000000")
    deadline_pressure_window_seconds: Decimal = Decimal("7200.000000")
    confirmation_weight: Decimal = Decimal("0.250000")
    independent_evidence_weight: Decimal = Decimal("0.250000")
    recency_weight: Decimal = Decimal("0.200000")
    dependency_penalty_weight: Decimal = Decimal("0.200000")
    contradiction_penalty_weight: Decimal = Decimal("0.250000")
    overdue_penalty_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("pass_threshold", "watch_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_threshold <= self.watch_threshold:
            raise ValueError("pass_threshold must exceed watch_threshold")
        for field_name in (
            "required_confirmation_count",
            "required_independent_evidence_count",
            "blocked_unresolved_dependency_count",
            "blocked_contradiction_count",
            "fresh_timeline_seconds",
            "stale_timeline_seconds",
            "deadline_pressure_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_timeline_seconds <= self.fresh_timeline_seconds:
            raise ValueError("stale_timeline_seconds must exceed fresh_timeline_seconds")
        for field_name in (
            "confirmation_weight",
            "independent_evidence_weight",
            "recency_weight",
            "dependency_penalty_weight",
            "contradiction_penalty_weight",
            "overdue_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("timeline confidence ladder config", self)
        _reject_unsafe_public_value("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimelineInput:
    event_alias: str
    checkpoint_alias: str
    confirmation_count: Decimal
    independent_evidence_count: Decimal
    unresolved_dependency_count: Decimal
    contradiction_count: Decimal
    timeline_updated_at: datetime
    expected_resolution_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_alias", "checkpoint_alias"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "confirmation_count",
            "independent_evidence_count",
            "unresolved_dependency_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "timeline_updated_at",
            _as_utc("timeline_updated_at", self.timeline_updated_at),
        )
        object.__setattr__(
            self,
            "expected_resolution_at",
            _as_utc("expected_resolution_at", self.expected_resolution_at),
        )
        require_paper_only_flags("timeline confidence ladder input", self)
        _reject_unsafe_public_value("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimelineConfidenceLadderRow:
    event_alias: str
    checkpoint_alias: str
    confirmation_count: Decimal
    independent_evidence_count: Decimal
    unresolved_dependency_count: Decimal
    contradiction_count: Decimal
    confirmation_score: Decimal
    independent_evidence_score: Decimal
    recency_score: Decimal
    dependency_penalty: Decimal
    contradiction_penalty: Decimal
    overdue_penalty: Decimal
    seconds_since_timeline_update: Decimal
    seconds_until_expected_resolution: Decimal
    confidence_score: Decimal
    ladder_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_alias", "checkpoint_alias"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "confirmation_count",
            "independent_evidence_count",
            "unresolved_dependency_count",
            "contradiction_count",
            "confirmation_score",
            "independent_evidence_score",
            "recency_score",
            "dependency_penalty",
            "contradiction_penalty",
            "overdue_penalty",
            "seconds_since_timeline_update",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_until_expected_resolution",
            _require_decimal(
                "seconds_until_expected_resolution",
                self.seconds_until_expected_resolution,
            ),
        )
        _require_ladder_status("ladder_status", self.ladder_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("timeline confidence ladder row", self)
        _reject_unsafe_public_value("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimelineConfidenceLadderReport:
    generated_at: datetime
    config_version: str
    ladder_status: str
    checkpoint_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_score: Decimal
    max_dependency_penalty: Decimal
    max_contradiction_penalty: Decimal
    min_seconds_until_expected_resolution: Decimal | None
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_ladder_status("ladder_status", self.ladder_status)
        for field_name in (
            "checkpoint_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_confidence_score",
            "max_dependency_penalty",
            "max_contradiction_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_seconds_until_expected_resolution",
            _normalize_optional_decimal(
                "min_seconds_until_expected_resolution",
                self.min_seconds_until_expected_resolution,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        require_paper_only_flags("timeline confidence ladder report", self)
        _reject_unsafe_public_value("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_from_payload(_public_payload(self, include_digest=False)),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            expected = _digest_from_payload(_public_payload(self, include_digest=False))
            if self.derived_validation_digest != expected:
                raise ValueError("derived_validation_digest does not match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return _public_payload(self, include_digest=True)


def build_research_event_resolution_timeline_confidence_ladder_report(
    checkpoints: Sequence[ResearchEventResolutionTimelineInput],
    *,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
    generated_at: datetime,
) -> ResearchEventResolutionTimelineConfidenceLadderReport:
    if type(config) is not ResearchEventResolutionTimelineConfidenceLadderConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionTimelineConfidenceLadderConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_checkpoints = _normalize_checkpoints(
        checkpoints,
        generated_at=generated_at_utc,
    )
    rows = _sort_rows(
        tuple(
            _row_from_checkpoint(item, config=config, generated_at=generated_at_utc)
            for item in normalized_checkpoints
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "ladder_status": _report_status(rows),
        "checkpoint_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_confidence_score": _average(tuple(row.confidence_score for row in rows)),
        "max_dependency_penalty": max((row.dependency_penalty for row in rows), default=ZERO),
        "max_contradiction_penalty": max(
            (row.contradiction_penalty for row in rows),
            default=ZERO,
        ),
        "min_seconds_until_expected_resolution": _min_seconds_until_expected_resolution(
            rows,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionTimelineConfidenceLadderReport(**values)


def research_event_resolution_timeline_confidence_ladder_report_to_payload(
    report: ResearchEventResolutionTimelineConfidenceLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionTimelineConfidenceLadderReport:
        raise ValueError(
            "report must be a ResearchEventResolutionTimelineConfidenceLadderReport",
        )
    require_paper_only_flags("timeline confidence ladder report", report)
    return report.public_payload


def _normalize_checkpoints(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchEventResolutionTimelineInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("checkpoints must be a sequence")
    checkpoints = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in checkpoints:
        if type(item) is not ResearchEventResolutionTimelineInput:
            raise ValueError("checkpoints must contain timeline inputs")
        require_paper_only_flags("timeline confidence ladder input", item)
        if item.timeline_updated_at > generated_at:
            raise ValueError("timeline_updated_at must not be after generated_at")
        key = (item.event_alias, item.checkpoint_alias)
        if key in seen:
            raise ValueError("checkpoint_alias must be unique per event_alias")
        seen.add(key)
    return tuple(sorted(checkpoints, key=lambda item: (item.event_alias, item.checkpoint_alias)))


def _row_from_checkpoint(
    item: ResearchEventResolutionTimelineInput,
    *,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
    generated_at: datetime,
) -> ResearchEventResolutionTimelineConfidenceLadderRow:
    confirmation_score = _confirmation_score(item, config)
    independent_evidence_score = _independent_evidence_score(item, config)
    seconds_since_timeline_update = _age_seconds(generated_at, item.timeline_updated_at)
    recency_score = _recency_score(seconds_since_timeline_update, config)
    dependency_penalty = _dependency_penalty(item.unresolved_dependency_count, config)
    contradiction_penalty = _contradiction_penalty(item.contradiction_count, config)
    seconds_until_expected_resolution = _signed_age_seconds(
        item.expected_resolution_at,
        generated_at,
    )
    overdue_penalty = _overdue_penalty(seconds_until_expected_resolution, config)
    confidence_score = _clamp_ratio(
        confirmation_score
        + independent_evidence_score
        + recency_score
        - dependency_penalty
        - contradiction_penalty
        - overdue_penalty,
    )
    status = _row_status(
        item,
        config=config,
        confidence_score=confidence_score,
    )
    return ResearchEventResolutionTimelineConfidenceLadderRow(
        event_alias=item.event_alias,
        checkpoint_alias=item.checkpoint_alias,
        confirmation_count=item.confirmation_count,
        independent_evidence_count=item.independent_evidence_count,
        unresolved_dependency_count=item.unresolved_dependency_count,
        contradiction_count=item.contradiction_count,
        confirmation_score=confirmation_score,
        independent_evidence_score=independent_evidence_score,
        recency_score=recency_score,
        dependency_penalty=dependency_penalty,
        contradiction_penalty=contradiction_penalty,
        overdue_penalty=overdue_penalty,
        seconds_since_timeline_update=seconds_since_timeline_update,
        seconds_until_expected_resolution=seconds_until_expected_resolution,
        confidence_score=confidence_score,
        ladder_status=status,
        reason_codes=_row_reason_codes(
            item,
            config=config,
            status=status,
            confidence_score=confidence_score,
            seconds_since_timeline_update=seconds_since_timeline_update,
            seconds_until_expected_resolution=seconds_until_expected_resolution,
        ),
    )


def _row_status(
    item: ResearchEventResolutionTimelineInput,
    *,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
    confidence_score: Decimal,
) -> str:
    if item.unresolved_dependency_count >= config.blocked_unresolved_dependency_count:
        return "block"
    if item.contradiction_count >= config.blocked_contradiction_count:
        return "block"
    if confidence_score < config.watch_threshold:
        return "block"
    if (
        confidence_score >= config.pass_threshold
        and item.confirmation_count >= config.required_confirmation_count
        and item.independent_evidence_count >= config.required_independent_evidence_count
        and item.unresolved_dependency_count == ZERO
        and item.contradiction_count == ZERO
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    item: ResearchEventResolutionTimelineInput,
    *,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
    status: str,
    confidence_score: Decimal,
    seconds_since_timeline_update: Decimal,
    seconds_until_expected_resolution: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.unresolved_dependency_count >= config.blocked_unresolved_dependency_count:
        reason_codes.append("timeline_confidence_blocked_dependency_pressure")
    if item.contradiction_count >= config.blocked_contradiction_count:
        reason_codes.append("timeline_confidence_blocked_contradiction_pressure")
    if (
        status == "block"
        and confidence_score < config.watch_threshold
        and not reason_codes
    ):
        reason_codes.append("timeline_confidence_block_threshold")
    elif status == "watch":
        reason_codes.append("timeline_confidence_watch_threshold")
    elif status == "pass":
        reason_codes.append("timeline_confidence_pass_threshold")
    if item.confirmation_count < config.required_confirmation_count:
        reason_codes.append("timeline_confidence_confirmation_quorum_shortfall")
    if item.independent_evidence_count < config.required_independent_evidence_count:
        reason_codes.append("timeline_confidence_evidence_quorum_shortfall")
    if seconds_since_timeline_update >= config.stale_timeline_seconds:
        reason_codes.append("timeline_confidence_stale_update")
    if _has_deadline_pressure(seconds_until_expected_resolution, config):
        reason_codes.append("timeline_confidence_deadline_pressure")
    if seconds_until_expected_resolution < ZERO:
        reason_codes.append("timeline_confidence_overdue_resolution")
    if ZERO < item.unresolved_dependency_count < config.blocked_unresolved_dependency_count:
        reason_codes.append("timeline_confidence_dependency_pressure")
    if ZERO < item.contradiction_count < config.blocked_contradiction_count:
        reason_codes.append("timeline_confidence_contradiction_pressure")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("timeline_confidence_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if any(row.ladder_status == "block" for row in rows):
        reason_codes.append("timeline_confidence_block_present")
    elif any(row.ladder_status == "watch" for row in rows):
        reason_codes.append("timeline_confidence_watch_present")
    else:
        reason_codes.append("timeline_confidence_clear")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...],
) -> str:
    if any(row.ladder_status == "block" for row in rows):
        return "block"
    if any(row.ladder_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_row(row: ResearchEventResolutionTimelineConfidenceLadderRow) -> None:
    for field_name in (
        "confirmation_score",
        "independent_evidence_score",
        "recency_score",
        "dependency_penalty",
        "contradiction_penalty",
        "overdue_penalty",
        "confidence_score",
    ):
        if getattr(row, field_name) > ONE:
            raise ValueError(f"{field_name} must be at most one")
    if row.ladder_status == "pass" and (
        "timeline_confidence_pass_threshold" not in row.reason_codes
    ):
        raise ValueError("pass rows require pass reason")
    if row.ladder_status == "watch" and (
        "timeline_confidence_watch_threshold" not in row.reason_codes
    ):
        raise ValueError("watch rows require watch reason")
    if row.ladder_status == "block" and not any(
        reason_code
        in (
            "timeline_confidence_blocked_dependency_pressure",
            "timeline_confidence_blocked_contradiction_pressure",
            "timeline_confidence_block_threshold",
        )
        for reason_code in row.reason_codes
    ):
        raise ValueError("block rows require block reason")


def _validate_report(report: ResearchEventResolutionTimelineConfidenceLadderReport) -> None:
    if report.checkpoint_count != _decimal_count(len(report.rows)):
        raise ValueError("checkpoint_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _decimal_count(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.checkpoint_count:
        raise ValueError("status counts must sum to checkpoint_count")
    if report.average_confidence_score != _average(
        tuple(row.confidence_score for row in report.rows),
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.max_dependency_penalty != max(
        (row.dependency_penalty for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_dependency_penalty must match rows")
    if report.max_contradiction_penalty != max(
        (row.contradiction_penalty for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_penalty must match rows")
    if report.min_seconds_until_expected_resolution != _min_seconds_until_expected_resolution(
        report.rows,
    ):
        raise ValueError("min_seconds_until_expected_resolution must match rows")
    if report.ladder_status != _report_status(report.rows):
        raise ValueError("ladder_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("rows must be a sequence")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventResolutionTimelineConfidenceLadderRow:
            raise ValueError("rows must contain timeline confidence ladder rows")
        require_paper_only_flags("timeline confidence ladder row", row)
    return _sort_rows(rows)


def _sort_rows(
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...],
) -> tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.ladder_status],
                row.event_alias,
                row.checkpoint_alias,
            ),
        ),
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in value:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _confirmation_score(
    item: ResearchEventResolutionTimelineInput,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    return _quantize(
        min(_ratio(item.confirmation_count, config.required_confirmation_count), ONE)
        * config.confirmation_weight,
    )


def _independent_evidence_score(
    item: ResearchEventResolutionTimelineInput,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    return _quantize(
        min(
            _ratio(
                item.independent_evidence_count,
                config.required_independent_evidence_count,
            ),
            ONE,
        )
        * config.independent_evidence_weight,
    )


def _recency_score(
    seconds_since_timeline_update: Decimal,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    if seconds_since_timeline_update <= config.fresh_timeline_seconds:
        return config.recency_weight
    if seconds_since_timeline_update >= config.stale_timeline_seconds:
        return ZERO
    seconds_after_fresh = seconds_since_timeline_update - config.fresh_timeline_seconds
    remaining = config.stale_timeline_seconds - seconds_after_fresh
    return _quantize(_ratio(remaining, config.stale_timeline_seconds) * config.recency_weight)


def _dependency_penalty(
    unresolved_dependency_count: Decimal,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    pressure = min(
        _ratio(
            unresolved_dependency_count,
            config.blocked_unresolved_dependency_count,
        ),
        ONE,
    )
    return _quantize(pressure * config.dependency_penalty_weight)


def _contradiction_penalty(
    contradiction_count: Decimal,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    if contradiction_count >= config.blocked_contradiction_count:
        return config.contradiction_penalty_weight
    pressure = min(_ratio(contradiction_count, config.blocked_contradiction_count), ONE)
    return _quantize(
        pressure
        * config.contradiction_penalty_weight
        * PARTIAL_CONTRADICTION_MULTIPLIER,
    )


def _overdue_penalty(
    seconds_until_expected_resolution: Decimal,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> Decimal:
    if seconds_until_expected_resolution >= ZERO:
        return ZERO
    return config.overdue_penalty_weight


def _has_deadline_pressure(
    seconds_until_expected_resolution: Decimal,
    config: ResearchEventResolutionTimelineConfidenceLadderConfig,
) -> bool:
    return (
        ZERO <= seconds_until_expected_resolution
        and seconds_until_expected_resolution <= config.deadline_pressure_window_seconds
    )


def _min_seconds_until_expected_resolution(
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.seconds_until_expected_resolution for row in rows)


def _status_count(
    rows: tuple[ResearchEventResolutionTimelineConfidenceLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.ladder_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(numerator / denominator)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    value = _signed_age_seconds(end_at, start_at)
    if value < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return value


def _signed_age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize(value)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ladder_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in LADDER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _public_payload(
    report: ResearchEventResolutionTimelineConfidenceLadderReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    values = asdict(report)
    digest = values.pop("derived_validation_digest", "")
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be an object")
    if include_digest:
        payload["derived_validation_digest"] = digest
    _reject_unsafe_public_value("public payload", payload, allow_json_containers=True)
    return payload


def _digest_from_payload(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_value("digest payload", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_value(
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
            _reject_unsafe_public_value(
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
            _reject_unsafe_public_value(
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
            _reject_unsafe_public_value(
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
    raise ValueError(f"{current_path} is not a supported public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_TIMELINE_CONFIDENCE_LADDER_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionTimelineConfidenceLadderConfig",
    "ResearchEventResolutionTimelineConfidenceLadderReport",
    "ResearchEventResolutionTimelineConfidenceLadderRow",
    "ResearchEventResolutionTimelineInput",
    "build_research_event_resolution_timeline_confidence_ladder_report",
    "research_event_resolution_timeline_confidence_ladder_report_to_payload",
)
