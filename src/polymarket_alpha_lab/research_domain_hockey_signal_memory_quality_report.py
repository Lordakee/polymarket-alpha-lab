"""Pure hockey team memory quality report for caller-supplied inputs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-hockey-signal-memory-quality-report-v0"
)
HOCKEY_SIGNAL_MEMORY_QUALITY_STATUSES = ("pass", "watch", "block")
HOCKEY_SIGNAL_MEMORY_KINDS = (
    "goalie",
    "injury",
    "schedule",
    "travel",
    "team_form",
)

HOCKEY_SIGNAL_MEMORY_QUALITY_REASON_CODES = (
    "hockey_goalie_memory_missing",
    "hockey_injury_memory_missing",
    "hockey_schedule_memory_missing",
    "hockey_travel_memory_missing",
    "hockey_team_form_memory_missing",
    "hockey_goalie_memory_stale",
    "hockey_injury_memory_stale",
    "hockey_schedule_memory_stale",
    "hockey_travel_memory_stale",
    "hockey_team_form_memory_stale",
    "hockey_goalie_memory_conflicting",
    "hockey_injury_memory_conflicting",
    "hockey_schedule_memory_conflicting",
    "hockey_travel_memory_conflicting",
    "hockey_team_form_memory_conflicting",
    "hockey_signal_memory_age_watch",
    "hockey_signal_memory_age_block",
    "hockey_signal_memory_quality_watch",
    "hockey_signal_memory_quality_block",
    "hockey_goalie_memory_clear",
    "hockey_injury_memory_clear",
    "hockey_schedule_memory_clear",
    "hockey_travel_memory_clear",
    "hockey_team_form_memory_clear",
    "hockey_signal_memory_quality_no_inputs",
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "HOCKEY_SIGNAL_MEMORY_QUALITY_STATUSES",
    "HOCKEY_SIGNAL_MEMORY_KINDS",
    "HOCKEY_SIGNAL_MEMORY_QUALITY_REASON_CODES",
    "ResearchDomainHockeySignalMemoryQualityConfig",
    "ResearchDomainHockeySignalMemoryQualityInput",
    "ResearchDomainHockeySignalMemoryQualityReasonCodeCount",
    "ResearchDomainHockeySignalMemoryQualityReport",
    "ResearchDomainHockeySignalMemoryQualityRow",
    "build_research_domain_hockey_signal_memory_quality_report",
    "research_domain_hockey_signal_memory_quality_report_payload",
)

ZERO = Decimal("0")
ONE = Decimal("1")
THREE = Decimal("3")
RATIO_QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
KIND_RANK = {kind: index for index, kind in enumerate(HOCKEY_SIGNAL_MEMORY_KINDS)}


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("candi", "date"),
        _join("mar", "ket"),
        _join("sl", "ug"),
        _join("ques", "tion"),
        _join("u", "rl"),
        _join("so", "urce"),
        _join("d", "sn"),
        _join("ta", "ble"),
        _join("to", "ken"),
        _join("wal", "let"),
        _join("au", "th"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("data", "base"),
        _join("net", "work"),
        _join("li", "ve"),
        _join("reco", "mmend"),
        _join("si", "zing"),
    ),
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchDomainHockeySignalMemoryQualityConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_memory_age_seconds: Decimal = Decimal("21600.000000")
    block_memory_age_seconds: Decimal = Decimal("86400.000000")
    watch_missing_memory_item_count: Decimal = Decimal("1")
    block_missing_memory_item_count: Decimal = Decimal("2")
    watch_stale_memory_item_count: Decimal = Decimal("1")
    block_stale_memory_item_count: Decimal = Decimal("2")
    watch_conflicting_memory_item_count: Decimal = Decimal("1")
    block_conflicting_memory_item_count: Decimal = Decimal("2")
    watch_min_quality_score: Decimal = Decimal("0.850000")
    block_min_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainHockeySignalMemoryQualityConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in ("watch_memory_age_seconds", "block_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_memory_age_seconds <= self.watch_memory_age_seconds:
            raise ValueError(
                "block_memory_age_seconds must exceed watch_memory_age_seconds",
            )
        for field_name in (
            "watch_missing_memory_item_count",
            "block_missing_memory_item_count",
            "watch_stale_memory_item_count",
            "block_stale_memory_item_count",
            "watch_conflicting_memory_item_count",
            "block_conflicting_memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_watch_block_threshold(
            "missing_memory_item_count",
            self.watch_missing_memory_item_count,
            self.block_missing_memory_item_count,
        )
        _require_watch_block_threshold(
            "stale_memory_item_count",
            self.watch_stale_memory_item_count,
            self.block_stale_memory_item_count,
        )
        _require_watch_block_threshold(
            "conflicting_memory_item_count",
            self.watch_conflicting_memory_item_count,
            self.block_conflicting_memory_item_count,
        )
        for field_name in ("watch_min_quality_score", "block_min_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_min_quality_score <= self.block_min_quality_score:
            raise ValueError("watch_min_quality_score must exceed block_min_quality_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainHockeySignalMemoryQualityInput(_NoSubclass):
    event_label: str
    team_label: str
    memory_kind: str
    latest_memory_at: datetime
    expected_memory_item_count: Decimal
    available_memory_item_count: Decimal
    stale_memory_item_count: Decimal
    conflicting_memory_item_count: Decimal
    redaction_confirmed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainHockeySignalMemoryQualityInput, "input")
        for field_name in ("event_label", "team_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_memory_kind("memory_kind", self.memory_kind)
        object.__setattr__(
            self,
            "latest_memory_at",
            _as_utc("latest_memory_at", self.latest_memory_at),
        )
        for field_name in (
            "expected_memory_item_count",
            "available_memory_item_count",
            "stale_memory_item_count",
            "conflicting_memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.available_memory_item_count > self.expected_memory_item_count:
            raise ValueError(
                "available_memory_item_count must not exceed expected_memory_item_count",
            )
        if self.stale_memory_item_count > self.available_memory_item_count:
            raise ValueError(
                "stale_memory_item_count must not exceed available_memory_item_count",
            )
        if self.conflicting_memory_item_count > self.available_memory_item_count:
            raise ValueError(
                "conflicting_memory_item_count must not exceed "
                "available_memory_item_count",
            )
        if type(self.redaction_confirmed) is not bool or not self.redaction_confirmed:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainHockeySignalMemoryQualityRow(_NoSubclass):
    event_label: str
    team_label: str
    memory_kind: str
    latest_memory_at: datetime | None
    expected_memory_item_count: Decimal
    available_memory_item_count: Decimal
    missing_memory_item_count: Decimal
    stale_memory_item_count: Decimal
    conflicting_memory_item_count: Decimal
    memory_age_seconds: Decimal
    completeness_score: Decimal
    freshness_score: Decimal
    non_conflict_score: Decimal
    memory_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainHockeySignalMemoryQualityRow, "row")
        for field_name in ("event_label", "team_label"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_memory_kind("memory_kind", self.memory_kind)
        object.__setattr__(
            self,
            "latest_memory_at",
            _as_optional_utc("latest_memory_at", self.latest_memory_at),
        )
        for field_name in (
            "expected_memory_item_count",
            "available_memory_item_count",
            "missing_memory_item_count",
            "stale_memory_item_count",
            "conflicting_memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_age_seconds",
            "completeness_score",
            "freshness_score",
            "non_conflict_score",
            "memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_or_seconds(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_counts(self)


@dataclass(frozen=True)
class ResearchDomainHockeySignalMemoryQualityReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainHockeySignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainHockeySignalMemoryQualityReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    event_team_count: Decimal
    row_count: Decimal
    required_memory_kind_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_kind_count: Decimal
    stale_kind_count: Decimal
    conflicting_kind_count: Decimal
    missing_memory_item_total: Decimal
    stale_memory_item_total: Decimal
    conflicting_memory_item_total: Decimal
    max_memory_age_seconds: Decimal
    min_memory_quality_score: Decimal
    status: str
    rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...]
    reason_code_counts: tuple[ResearchDomainHockeySignalMemoryQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainHockeySignalMemoryQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "event_team_count",
            "row_count",
            "required_memory_kind_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_kind_count",
            "stale_kind_count",
            "conflicting_kind_count",
            "missing_memory_item_total",
            "stale_memory_item_total",
            "conflicting_memory_item_total",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_seconds(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_memory_quality_score",
            _require_ratio_decimal(
                "min_memory_quality_score",
                self.min_memory_quality_score,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_counts(self)
        expected_digest = _payload_digest(_unsigned_report_payload(self))
        if self.derived_validation_digest:
            if not DIGEST_RE.fullmatch(self.derived_validation_digest):
                raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_hockey_signal_memory_quality_report_payload(self)


def build_research_domain_hockey_signal_memory_quality_report(
    memory_inputs: Iterable[object],
    *,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainHockeySignalMemoryQualityReport:
    _require_exact_type(config, ResearchDomainHockeySignalMemoryQualityConfig, "config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_inputs)
    for item in inputs:
        if item.latest_memory_at > generated_at_utc:
            raise ValueError("latest_memory_at must not be after generated_at")
    rows = _build_rows(inputs, config=config, generated_at=generated_at_utc)
    reason_codes = _summary_reason_codes(rows)
    return ResearchDomainHockeySignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_team_count=_decimal_count(len({(row.event_label, row.team_label) for row in rows})),
        row_count=_decimal_count(len(rows)),
        required_memory_kind_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        missing_kind_count=_decimal_count(
            sum(1 for row in rows if row.latest_memory_at is None),
        ),
        stale_kind_count=_decimal_count(
            sum(1 for row in rows if row.stale_memory_item_count > ZERO),
        ),
        conflicting_kind_count=_decimal_count(
            sum(1 for row in rows if row.conflicting_memory_item_count > ZERO),
        ),
        missing_memory_item_total=sum(
            (row.missing_memory_item_count for row in rows),
            ZERO,
        ),
        stale_memory_item_total=sum((row.stale_memory_item_count for row in rows), ZERO),
        conflicting_memory_item_total=sum(
            (row.conflicting_memory_item_count for row in rows),
            ZERO,
        ),
        max_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=ZERO.quantize(RATIO_QUANTUM),
        ),
        min_memory_quality_score=min(
            (row.memory_quality_score for row in rows),
            default=ZERO.quantize(RATIO_QUANTUM),
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_domain_hockey_signal_memory_quality_report_payload(
    report: ResearchDomainHockeySignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainHockeySignalMemoryQualityReport:
        _require_hard_flags("report", report)
        payload = _signed_report_payload(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchDomainHockeySignalMemoryQualityReport or dict",
        )
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def _build_rows(
    inputs: tuple[ResearchDomainHockeySignalMemoryQualityInput, ...],
    *,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
    generated_at: datetime,
) -> tuple[ResearchDomainHockeySignalMemoryQualityRow, ...]:
    if not inputs:
        return ()
    by_group: dict[tuple[str, str], dict[str, ResearchDomainHockeySignalMemoryQualityInput]] = {}
    for item in inputs:
        group = by_group.setdefault((item.event_label, item.team_label), {})
        if item.memory_kind in group:
            raise ValueError("memory_kind must be unique per event_label and team_label")
        group[item.memory_kind] = item
    rows: list[ResearchDomainHockeySignalMemoryQualityRow] = []
    for event_label, team_label in sorted(by_group):
        grouped_items = by_group[(event_label, team_label)]
        for memory_kind in HOCKEY_SIGNAL_MEMORY_KINDS:
            item = grouped_items.get(memory_kind)
            if item is None:
                rows.append(
                    _missing_row(
                        event_label=event_label,
                        team_label=team_label,
                        memory_kind=memory_kind,
                        config=config,
                    ),
                )
            else:
                rows.append(_row_from_input(item, config=config, generated_at=generated_at))
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_input(
    item: ResearchDomainHockeySignalMemoryQualityInput,
    *,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainHockeySignalMemoryQualityRow:
    age_seconds = _age_seconds(generated_at, item.latest_memory_at)
    missing_count = item.expected_memory_item_count - item.available_memory_item_count
    completeness_score = (
        ONE
        if item.expected_memory_item_count == ZERO
        else _ratio(item.available_memory_item_count, item.expected_memory_item_count)
    )
    freshness_score = _freshness_score(
        age_seconds,
        block_memory_age_seconds=config.block_memory_age_seconds,
    )
    non_conflict_score = (
        ZERO.quantize(RATIO_QUANTUM)
        if item.available_memory_item_count == ZERO
        else _ratio(
            item.available_memory_item_count - item.conflicting_memory_item_count,
            item.available_memory_item_count,
        )
    )
    memory_quality_score = _quantize(
        (completeness_score + freshness_score + non_conflict_score) / THREE,
    )
    status = _row_status(
        memory_age_seconds=age_seconds,
        missing_memory_item_count=missing_count,
        stale_memory_item_count=item.stale_memory_item_count,
        conflicting_memory_item_count=item.conflicting_memory_item_count,
        memory_quality_score=memory_quality_score,
        config=config,
    )
    return ResearchDomainHockeySignalMemoryQualityRow(
        event_label=item.event_label,
        team_label=item.team_label,
        memory_kind=item.memory_kind,
        latest_memory_at=item.latest_memory_at,
        expected_memory_item_count=item.expected_memory_item_count,
        available_memory_item_count=item.available_memory_item_count,
        missing_memory_item_count=missing_count,
        stale_memory_item_count=item.stale_memory_item_count,
        conflicting_memory_item_count=item.conflicting_memory_item_count,
        memory_age_seconds=age_seconds,
        completeness_score=completeness_score,
        freshness_score=freshness_score,
        non_conflict_score=non_conflict_score,
        memory_quality_score=memory_quality_score,
        status=status,
        reason_codes=_row_reason_codes(
            memory_kind=item.memory_kind,
            status=status,
            memory_age_seconds=age_seconds,
            missing_memory_item_count=missing_count,
            stale_memory_item_count=item.stale_memory_item_count,
            conflicting_memory_item_count=item.conflicting_memory_item_count,
            latest_memory_at=item.latest_memory_at,
            config=config,
        ),
    )


def _missing_row(
    *,
    event_label: str,
    team_label: str,
    memory_kind: str,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
) -> ResearchDomainHockeySignalMemoryQualityRow:
    return ResearchDomainHockeySignalMemoryQualityRow(
        event_label=event_label,
        team_label=team_label,
        memory_kind=memory_kind,
        latest_memory_at=None,
        expected_memory_item_count=ONE,
        available_memory_item_count=ZERO,
        missing_memory_item_count=ONE,
        stale_memory_item_count=ZERO,
        conflicting_memory_item_count=ZERO,
        memory_age_seconds=_quantize(config.block_memory_age_seconds),
        completeness_score=ZERO.quantize(RATIO_QUANTUM),
        freshness_score=ZERO.quantize(RATIO_QUANTUM),
        non_conflict_score=ZERO.quantize(RATIO_QUANTUM),
        memory_quality_score=ZERO.quantize(RATIO_QUANTUM),
        status="block",
        reason_codes=(
            f"hockey_{memory_kind}_memory_missing",
            "hockey_signal_memory_quality_block",
        ),
    )


def _row_status(
    *,
    memory_age_seconds: Decimal,
    missing_memory_item_count: Decimal,
    stale_memory_item_count: Decimal,
    conflicting_memory_item_count: Decimal,
    memory_quality_score: Decimal,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
) -> str:
    if (
        memory_age_seconds >= config.block_memory_age_seconds
        or missing_memory_item_count >= config.block_missing_memory_item_count
        or stale_memory_item_count >= config.block_stale_memory_item_count
        or conflicting_memory_item_count >= config.block_conflicting_memory_item_count
        or memory_quality_score < config.block_min_quality_score
    ):
        return "block"
    if (
        memory_age_seconds >= config.watch_memory_age_seconds
        or missing_memory_item_count >= config.watch_missing_memory_item_count
        or stale_memory_item_count >= config.watch_stale_memory_item_count
        or conflicting_memory_item_count >= config.watch_conflicting_memory_item_count
        or memory_quality_score < config.watch_min_quality_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    memory_kind: str,
    status: str,
    memory_age_seconds: Decimal,
    missing_memory_item_count: Decimal,
    stale_memory_item_count: Decimal,
    conflicting_memory_item_count: Decimal,
    latest_memory_at: datetime | None,
    config: ResearchDomainHockeySignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if missing_memory_item_count > ZERO:
        reasons.append(f"hockey_{memory_kind}_memory_missing")
    if stale_memory_item_count > ZERO:
        reasons.append(f"hockey_{memory_kind}_memory_stale")
    if conflicting_memory_item_count > ZERO:
        reasons.append(f"hockey_{memory_kind}_memory_conflicting")
    if latest_memory_at is not None:
        if memory_age_seconds >= config.block_memory_age_seconds:
            reasons.append("hockey_signal_memory_age_block")
        elif memory_age_seconds >= config.watch_memory_age_seconds:
            reasons.append("hockey_signal_memory_age_watch")
    if status == "block":
        reasons.append("hockey_signal_memory_quality_block")
    elif status == "watch":
        reasons.append("hockey_signal_memory_quality_watch")
    else:
        reasons.append(f"hockey_{memory_kind}_memory_clear")
    return tuple(dict.fromkeys(reasons))


def _summary_reason_codes(
    rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("hockey_signal_memory_quality_no_inputs",)
    reasons: list[str] = []
    block_generic: list[str] = []
    for row in rows:
        if row.status == "block":
            for reason in row.reason_codes:
                if reason in {
                    "hockey_signal_memory_age_block",
                    "hockey_signal_memory_quality_block",
                }:
                    block_generic.append(reason)
                else:
                    reasons.append(reason)
    for reason in ("hockey_signal_memory_age_block", "hockey_signal_memory_quality_block"):
        if reason in block_generic:
            reasons.append(reason)
    for row in rows:
        if row.status != "block":
            reasons.extend(row.reason_codes)
    return tuple(dict.fromkeys(reasons))


def _summary_status(rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchDomainHockeySignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchDomainHockeySignalMemoryQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchDomainHockeySignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_inputs(
    memory_inputs: Iterable[object],
) -> tuple[ResearchDomainHockeySignalMemoryQualityInput, ...]:
    if isinstance(memory_inputs, (str, bytes)):
        raise ValueError("memory_inputs must be an iterable")
    try:
        values = tuple(memory_inputs)
    except TypeError as exc:
        raise ValueError("memory_inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchDomainHockeySignalMemoryQualityInput:
    if type(value) is ResearchDomainHockeySignalMemoryQualityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchDomainHockeySignalMemoryQualityInput(
        event_label=_field_value(value, "event_label"),
        team_label=_field_value(value, "team_label"),
        memory_kind=_field_value(value, "memory_kind"),
        latest_memory_at=_field_value(value, "latest_memory_at"),
        expected_memory_item_count=_field_value(value, "expected_memory_item_count"),
        available_memory_item_count=_field_value(value, "available_memory_item_count"),
        stale_memory_item_count=_field_value(value, "stale_memory_item_count"),
        conflicting_memory_item_count=_field_value(value, "conflicting_memory_item_count"),
        redaction_confirmed=_field_value(value, "redaction_confirmed"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _row_sort_key(row: ResearchDomainHockeySignalMemoryQualityRow) -> tuple[int, int, str, str]:
    return (
        STATUS_RANK[row.status],
        KIND_RANK[row.memory_kind],
        row.event_label,
        row.team_label,
    )


def _status_count(
    rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchDomainHockeySignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainHockeySignalMemoryQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDomainHockeySignalMemoryQualityRow:
            raise ValueError(
                "rows must contain ResearchDomainHockeySignalMemoryQualityRow values",
            )
        _require_hard_flags("row", row)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchDomainHockeySignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainHockeySignalMemoryQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchDomainHockeySignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainHockeySignalMemoryQualityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if tuple(sorted(counts, key=lambda item: item.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_counts(row: ResearchDomainHockeySignalMemoryQualityRow) -> None:
    if row.available_memory_item_count > row.expected_memory_item_count:
        raise ValueError(
            "available_memory_item_count must not exceed expected_memory_item_count",
        )
    if (
        row.expected_memory_item_count - row.available_memory_item_count
        != row.missing_memory_item_count
    ):
        raise ValueError("missing_memory_item_count must match expected less available")
    if row.stale_memory_item_count > row.available_memory_item_count:
        raise ValueError(
            "stale_memory_item_count must not exceed available_memory_item_count",
        )
    if row.conflicting_memory_item_count > row.available_memory_item_count:
        raise ValueError(
            "conflicting_memory_item_count must not exceed available_memory_item_count",
        )


def _validate_report_counts(
    report: ResearchDomainHockeySignalMemoryQualityReport,
) -> None:
    rows = report.rows
    if report.event_team_count != _decimal_count(
        len({(row.event_label, row.team_label) for row in rows}),
    ):
        raise ValueError("event_team_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.required_memory_kind_count != _decimal_count(len(rows)):
        raise ValueError("required_memory_kind_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.missing_kind_count != _decimal_count(
        sum(1 for row in rows if row.latest_memory_at is None),
    ):
        raise ValueError("missing_kind_count must match rows")
    if report.stale_kind_count != _decimal_count(
        sum(1 for row in rows if row.stale_memory_item_count > ZERO),
    ):
        raise ValueError("stale_kind_count must match rows")
    if report.conflicting_kind_count != _decimal_count(
        sum(1 for row in rows if row.conflicting_memory_item_count > ZERO),
    ):
        raise ValueError("conflicting_kind_count must match rows")
    if report.missing_memory_item_total != sum(
        (row.missing_memory_item_count for row in rows),
        ZERO,
    ):
        raise ValueError("missing_memory_item_total must match rows")
    if report.stale_memory_item_total != sum(
        (row.stale_memory_item_count for row in rows),
        ZERO,
    ):
        raise ValueError("stale_memory_item_total must match rows")
    if report.conflicting_memory_item_total != sum(
        (row.conflicting_memory_item_count for row in rows),
        ZERO,
    ):
        raise ValueError("conflicting_memory_item_total must match rows")
    expected_max_age = max(
        (row.memory_age_seconds for row in rows),
        default=ZERO.quantize(RATIO_QUANTUM),
    )
    if report.max_memory_age_seconds != expected_max_age:
        raise ValueError("max_memory_age_seconds must match rows")
    expected_min_score = min(
        (row.memory_quality_score for row in rows),
        default=ZERO.quantize(RATIO_QUANTUM),
    )
    if report.min_memory_quality_score != expected_min_score:
        raise ValueError("min_memory_quality_score must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _age_seconds(generated_at: datetime, latest_memory_at: datetime) -> Decimal:
    delta = generated_at - latest_memory_at
    return _quantize(
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _freshness_score(
    age_seconds: Decimal,
    *,
    block_memory_age_seconds: Decimal,
) -> Decimal:
    if age_seconds >= block_memory_age_seconds:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(ONE - (age_seconds / block_memory_age_seconds))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize(max(ZERO, min(ONE, numerator / denominator)))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    return _quantize(_require_nonnegative_decimal(field_name, value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_ratio_or_seconds(field_name: str, value: object) -> Decimal:
    if field_name.endswith("_seconds"):
        return _require_nonnegative_seconds(field_name, value)
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public-safe label")
    _reject_unsafe_text(field_name, value)


def _require_memory_kind(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HOCKEY_SIGNAL_MEMORY_KINDS:
        raise ValueError(f"{field_name} must be one of {HOCKEY_SIGNAL_MEMORY_KINDS}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HOCKEY_SIGNAL_MEMORY_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if value not in HOCKEY_SIGNAL_MEMORY_QUALITY_REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must be nonempty")
    for value in values:
        _require_reason_code(field_name, value)
    return values


def _require_watch_block_threshold(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"watch_{field_name} must not exceed block_{field_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _unsigned_report_payload(
    report: ResearchDomainHockeySignalMemoryQualityReport,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest":
            continue
        payload[field.name] = _payload_value(getattr(report, field.name))
    return payload


def _signed_report_payload(
    report: ResearchDomainHockeySignalMemoryQualityReport,
) -> dict[str, Any]:
    payload = _unsigned_report_payload(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    if _payload_digest(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            _reject_unsafe_text("public payload key", key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_text("public payload value", value)
    elif type(value) in (int, float):
        raise ValueError("unsafe public numeric payload value")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public-safe text")
