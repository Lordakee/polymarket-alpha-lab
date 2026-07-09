"""Pure event authority-claim conflict memory scorecard report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_RESEARCH_EVENT_AUTHORITY_CLAIM_CONFLICT_MEMORY_SCORECARD_CONFIG_VERSION = (
    "research-event-authority-claim-conflict-memory-scorecard-v0"
)
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DIGEST_PREFIX = "reacmsr-v0:"
_ROW_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_BAD_PUBLIC_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("can", "didate"),
        ("mar", "ket"),
        ("s", "lug"),
        ("ques", "tion"),
        ("sou", "rce"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
        ("data", "base"),
        ("wal", "let"),
        ("net", "work"),
        ("or", "der"),
        ("tra", "de"),
        ("li", "ve"),
        ("tra", "ding"),
        ("si", "zing"),
        ("recomm", "endation"),
    )
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventAuthorityClaimConflictMemoryScorecardConfig(
    _FinalPublicDataclass,
):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_CLAIM_CONFLICT_MEMORY_SCORECARD_CONFIG_VERSION
    )
    watch_conflict_memory_score: Decimal = Decimal("0.250000")
    block_conflict_memory_score: Decimal = Decimal("0.750000")
    max_unresolved_conflict_age_days: Decimal = Decimal("7.000000")
    conflict_weight: Decimal = Decimal("0.400003")
    memory_weight: Decimal = Decimal("0.200000")
    age_weight: Decimal = Decimal("0.299997")
    stale_memory_weight: Decimal = Decimal("0.100000")
    evidence_relief_per_item: Decimal = Decimal("0.039286")
    max_evidence_relief_score: Decimal = Decimal("0.078572")
    min_independent_evidence_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityClaimConflictMemoryScorecardConfig:
            raise ValueError(
                "config must be a "
                "ResearchEventAuthorityClaimConflictMemoryScorecardConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_conflict_memory_score",
            "block_conflict_memory_score",
            "conflict_weight",
            "memory_weight",
            "age_weight",
            "stale_memory_weight",
            "evidence_relief_per_item",
            "max_evidence_relief_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_conflict_age_days",
            _normalize_positive_decimal(
                "max_unresolved_conflict_age_days",
                self.max_unresolved_conflict_age_days,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_evidence_count",
            _normalize_positive_count(
                "min_independent_evidence_count",
                self.min_independent_evidence_count,
            ),
        )
        if self.watch_conflict_memory_score > self.block_conflict_memory_score:
            raise ValueError("watch_conflict_memory_score must not exceed block threshold")
        weight_sum = (
            self.conflict_weight
            + self.memory_weight
            + self.age_weight
            + self.stale_memory_weight
        ).quantize(_RATIO_QUANTUM)
        if weight_sum != _ONE_RATIO:
            raise ValueError("score weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityClaimConflictMemoryScorecardInput(
    _FinalPublicDataclass,
):
    event_key: str
    authority_key: str
    claim_key: str
    observed_at: datetime
    authority_claim_count: Decimal
    conflicting_claim_count: Decimal
    memory_observation_count: Decimal
    conflicting_memory_count: Decimal
    stale_memory_count: Decimal
    unresolved_conflict_age_days: Decimal
    independent_evidence_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityClaimConflictMemoryScorecardInput:
            raise ValueError(
                "input must be a "
                "ResearchEventAuthorityClaimConflictMemoryScorecardInput",
            )
        for field_name in ("event_key", "authority_key", "claim_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_claim_count",
            "conflicting_claim_count",
            "memory_observation_count",
            "conflicting_memory_count",
            "stale_memory_count",
            "independent_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_conflict_age_days",
            _normalize_nonnegative_decimal(
                "unresolved_conflict_age_days",
                self.unresolved_conflict_age_days,
            ),
        )
        if self.conflicting_claim_count > self.authority_claim_count:
            raise ValueError("conflicting_claim_count must not exceed authority_claim_count")
        if self.conflicting_memory_count > self.memory_observation_count:
            raise ValueError(
                "conflicting_memory_count must not exceed memory_observation_count",
            )
        if self.stale_memory_count > self.memory_observation_count:
            raise ValueError("stale_memory_count must not exceed memory_observation_count")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _reject_unsafe_public_payload("input", self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventAuthorityClaimConflictMemoryScorecardRow(
    _FinalPublicDataclass,
):
    event_key: str
    authority_key: str
    claim_key: str
    observed_at: datetime
    authority_claim_count: Decimal
    conflicting_claim_count: Decimal
    memory_observation_count: Decimal
    conflicting_memory_count: Decimal
    stale_memory_count: Decimal
    unresolved_conflict_age_days: Decimal
    independent_evidence_count: Decimal
    conflict_ratio: Decimal
    memory_conflict_ratio: Decimal
    stale_memory_ratio: Decimal
    age_pressure_score: Decimal
    evidence_relief_score: Decimal
    conflict_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityClaimConflictMemoryScorecardRow:
            raise ValueError(
                "row must be a ResearchEventAuthorityClaimConflictMemoryScorecardRow",
            )
        for field_name in ("event_key", "authority_key", "claim_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_claim_count",
            "conflicting_claim_count",
            "memory_observation_count",
            "conflicting_memory_count",
            "stale_memory_count",
            "independent_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_conflict_age_days",
            _normalize_nonnegative_decimal(
                "unresolved_conflict_age_days",
                self.unresolved_conflict_age_days,
            ),
        )
        for field_name in (
            "conflict_ratio",
            "memory_conflict_ratio",
            "stale_memory_ratio",
            "age_pressure_score",
            "evidence_relief_score",
            "conflict_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _set_or_require_digest(self, _row_digest(self))
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventAuthorityClaimConflictMemoryScorecardReport(
    _FinalPublicDataclass,
):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    conflicting_event_count: Decimal
    stale_memory_event_count: Decimal
    sparse_evidence_event_count: Decimal
    max_conflict_memory_score: Decimal
    average_conflict_memory_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventAuthorityClaimConflictMemoryScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityClaimConflictMemoryScorecardReport:
            raise ValueError(
                "report must be a "
                "ResearchEventAuthorityClaimConflictMemoryScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "conflicting_event_count",
            "stale_memory_event_count",
            "sparse_evidence_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_conflict_memory_score",
            "average_conflict_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.rows)
        for row in rows:
            if type(row) is not ResearchEventAuthorityClaimConflictMemoryScorecardRow:
                raise ValueError("rows must contain scorecard rows")
            _require_row_digest(row)
            _require_hard_flags("row", row)
        object.__setattr__(self, "rows", rows)
        _validate_report(self)
        _set_or_require_digest(self, _report_digest(self))
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_event_authority_claim_conflict_memory_scorecard_report(
    events: (
        list[ResearchEventAuthorityClaimConflictMemoryScorecardInput]
        | tuple[ResearchEventAuthorityClaimConflictMemoryScorecardInput, ...]
    ),
    *,
    config: ResearchEventAuthorityClaimConflictMemoryScorecardConfig | None = None,
    generated_at: datetime,
) -> ResearchEventAuthorityClaimConflictMemoryScorecardReport:
    if config is None:
        config = ResearchEventAuthorityClaimConflictMemoryScorecardConfig()
    if type(config) is not ResearchEventAuthorityClaimConflictMemoryScorecardConfig:
        raise ValueError(
            "config must be a "
            "ResearchEventAuthorityClaimConflictMemoryScorecardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    event,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for event in normalized_events
            ),
            key=_row_key,
        ),
    )
    return ResearchEventAuthorityClaimConflictMemoryScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        conflicting_event_count=_count(
            sum(1 for row in rows if row.conflicting_claim_count > _ZERO_COUNT),
        ),
        stale_memory_event_count=_count(
            sum(1 for row in rows if row.stale_memory_count > _ZERO_COUNT),
        ),
        sparse_evidence_event_count=_count(
            sum(
                1
                for row in rows
                if row.independent_evidence_count < config.min_independent_evidence_count
            ),
        ),
        max_conflict_memory_score=_max_ratio(
            tuple(row.conflict_memory_score for row in rows),
        ),
        average_conflict_memory_score=_average_ratio(
            tuple(row.conflict_memory_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_authority_claim_conflict_memory_scorecard_report_payload(
    report: ResearchEventAuthorityClaimConflictMemoryScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventAuthorityClaimConflictMemoryScorecardReport:
        _require_hard_flags("report", report)
        _require_report_digest(report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchEventAuthorityClaimConflictMemoryScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


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


def _normalize_events(
    events: (
        list[ResearchEventAuthorityClaimConflictMemoryScorecardInput]
        | tuple[ResearchEventAuthorityClaimConflictMemoryScorecardInput, ...]
    ),
) -> tuple[ResearchEventAuthorityClaimConflictMemoryScorecardInput, ...]:
    if type(events) not in (list, tuple):
        raise ValueError("events must be a list or tuple")
    normalized = tuple(events)
    seen: set[str] = set()
    for event in normalized:
        if type(event) is not ResearchEventAuthorityClaimConflictMemoryScorecardInput:
            raise ValueError("events must contain scorecard inputs")
        _require_hard_flags("input", event)
        if event.event_key in seen:
            raise ValueError("events must not contain duplicate event_key values")
        seen.add(event.event_key)
    return normalized


def _row_from_input(
    event: ResearchEventAuthorityClaimConflictMemoryScorecardInput,
    *,
    config: ResearchEventAuthorityClaimConflictMemoryScorecardConfig,
    generated_at: datetime,
) -> ResearchEventAuthorityClaimConflictMemoryScorecardRow:
    if event.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    conflict_ratio = _ratio(event.conflicting_claim_count, event.authority_claim_count)
    memory_conflict_ratio = _ratio(
        event.conflicting_memory_count,
        event.memory_observation_count,
    )
    stale_memory_ratio = _ratio(
        event.stale_memory_count,
        event.memory_observation_count,
    )
    age_pressure_score = _bounded_ratio(
        event.unresolved_conflict_age_days / config.max_unresolved_conflict_age_days,
    )
    evidence_relief_score = min(
        _bounded_ratio(event.independent_evidence_count * config.evidence_relief_per_item),
        config.max_evidence_relief_score,
    )
    conflict_memory_score = _bounded_ratio(
        (conflict_ratio * config.conflict_weight)
        + (memory_conflict_ratio * config.memory_weight)
        + (age_pressure_score * config.age_weight)
        + (stale_memory_ratio * config.stale_memory_weight)
        - evidence_relief_score,
    )
    status = _status_for_score(conflict_memory_score, config)
    return ResearchEventAuthorityClaimConflictMemoryScorecardRow(
        event_key=event.event_key,
        authority_key=event.authority_key,
        claim_key=event.claim_key,
        observed_at=event.observed_at,
        authority_claim_count=event.authority_claim_count,
        conflicting_claim_count=event.conflicting_claim_count,
        memory_observation_count=event.memory_observation_count,
        conflicting_memory_count=event.conflicting_memory_count,
        stale_memory_count=event.stale_memory_count,
        unresolved_conflict_age_days=event.unresolved_conflict_age_days,
        independent_evidence_count=event.independent_evidence_count,
        conflict_ratio=conflict_ratio,
        memory_conflict_ratio=memory_conflict_ratio,
        stale_memory_ratio=stale_memory_ratio,
        age_pressure_score=age_pressure_score,
        evidence_relief_score=evidence_relief_score,
        conflict_memory_score=conflict_memory_score,
        status=status,
        reason_codes=_row_reason_codes(
            event,
            status=status,
            config=config,
        ),
    )


def _row_reason_codes(
    event: ResearchEventAuthorityClaimConflictMemoryScorecardInput,
    *,
    status: str,
    config: ResearchEventAuthorityClaimConflictMemoryScorecardConfig,
) -> tuple[str, ...]:
    reason_codes = list(event.reason_codes)
    if event.conflicting_claim_count > _ZERO_COUNT:
        reason_codes.append("authority_claim_conflict_present")
    if event.conflicting_memory_count > _ZERO_COUNT:
        reason_codes.append("memory_conflict_present")
    if event.stale_memory_count > _ZERO_COUNT:
        reason_codes.append("stale_memory_present")
    if event.independent_evidence_count < config.min_independent_evidence_count:
        reason_codes.append("sparse_independent_evidence")
    reason_codes.append(f"authority_claim_conflict_memory_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row(
    row: ResearchEventAuthorityClaimConflictMemoryScorecardRow,
) -> None:
    if row.conflicting_claim_count > row.authority_claim_count:
        raise ValueError("conflicting_claim_count must not exceed authority_claim_count")
    if row.conflicting_memory_count > row.memory_observation_count:
        raise ValueError(
            "conflicting_memory_count must not exceed memory_observation_count",
        )
    if row.stale_memory_count > row.memory_observation_count:
        raise ValueError("stale_memory_count must not exceed memory_observation_count")
    if f"authority_claim_conflict_memory_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report(
    report: ResearchEventAuthorityClaimConflictMemoryScorecardReport,
) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted by status and score")
    if len({row.event_key for row in rows}) != len(rows):
        raise ValueError("rows must contain unique event_key values")
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.conflicting_event_count != _count(
        sum(1 for row in rows if row.conflicting_claim_count > _ZERO_COUNT),
    ):
        raise ValueError("conflicting_event_count must match rows")
    if report.stale_memory_event_count != _count(
        sum(1 for row in rows if row.stale_memory_count > _ZERO_COUNT),
    ):
        raise ValueError("stale_memory_event_count must match rows")
    if report.sparse_evidence_event_count != _count(
        sum(1 for row in rows if "sparse_independent_evidence" in row.reason_codes),
    ):
        raise ValueError("sparse_evidence_event_count must match rows")
    scores = tuple(row.conflict_memory_score for row in rows)
    if report.max_conflict_memory_score != _max_ratio(scores):
        raise ValueError("max_conflict_memory_score must match rows")
    if report.average_conflict_memory_score != _average_ratio(scores):
        raise ValueError("average_conflict_memory_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_for_score(
    score: Decimal,
    config: ResearchEventAuthorityClaimConflictMemoryScorecardConfig,
) -> str:
    if score >= config.block_conflict_memory_score:
        return "block"
    if score >= config.watch_conflict_memory_score:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchEventAuthorityClaimConflictMemoryScorecardRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityClaimConflictMemoryScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_claim_conflict_memory_report_block",)
    status = _report_status(rows)
    reason_codes = [f"authority_claim_conflict_memory_report_{status}"]
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    for reason_code in (
        "authority_claim_conflict_memory_block",
        "authority_claim_conflict_memory_watch",
        "authority_claim_conflict_memory_pass",
    ):
        if reason_code in observed:
            reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_key(
    row: ResearchEventAuthorityClaimConflictMemoryScorecardRow,
) -> tuple[int, Decimal, datetime, str]:
    return (
        _ROW_STATUS_RANK[row.status],
        -row.conflict_memory_score,
        row.observed_at,
        row.event_key,
    )


def _row_digest(row: ResearchEventAuthorityClaimConflictMemoryScorecardRow) -> str:
    return _digest(
        (
            "row",
            row.event_key,
            row.authority_key,
            row.claim_key,
            _datetime_payload(row.observed_at),
            _decimal_payload(row.authority_claim_count),
            _decimal_payload(row.conflicting_claim_count),
            _decimal_payload(row.memory_observation_count),
            _decimal_payload(row.conflicting_memory_count),
            _decimal_payload(row.stale_memory_count),
            _decimal_payload(row.unresolved_conflict_age_days),
            _decimal_payload(row.independent_evidence_count),
            _decimal_payload(row.conflict_ratio),
            _decimal_payload(row.memory_conflict_ratio),
            _decimal_payload(row.stale_memory_ratio),
            _decimal_payload(row.age_pressure_score),
            _decimal_payload(row.evidence_relief_score),
            _decimal_payload(row.conflict_memory_score),
            row.status,
            "|".join(row.reason_codes),
            str(row.paper_only),
            str(row.report_only),
            str(row.readonly),
        ),
    )


def _report_digest(
    report: ResearchEventAuthorityClaimConflictMemoryScorecardReport,
) -> str:
    return _digest(
        (
            "report",
            _datetime_payload(report.generated_at),
            report.config_version,
            _decimal_payload(report.event_count),
            _decimal_payload(report.pass_count),
            _decimal_payload(report.watch_count),
            _decimal_payload(report.block_count),
            _decimal_payload(report.conflicting_event_count),
            _decimal_payload(report.stale_memory_event_count),
            _decimal_payload(report.sparse_evidence_event_count),
            _decimal_payload(report.max_conflict_memory_score),
            _decimal_payload(report.average_conflict_memory_score),
            report.status,
            "|".join(report.reason_codes),
            "|".join(row.derived_validation_digest for row in report.rows),
            str(report.paper_only),
            str(report.report_only),
            str(report.readonly),
        ),
    )


def _digest(parts: tuple[str, ...]) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _set_or_require_digest(value: object, expected: str) -> None:
    current = getattr(value, "derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
    elif current != expected:
        raise ValueError("derived_validation_digest must match report fields")
    _require_digest_string(
        "derived_validation_digest",
        getattr(value, "derived_validation_digest"),
    )


def _require_row_digest(
    row: ResearchEventAuthorityClaimConflictMemoryScorecardRow,
) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest tamper detected")


def _require_report_digest(
    report: ResearchEventAuthorityClaimConflictMemoryScorecardReport,
) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest tamper detected")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numbers must be Decimal strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _json_dict_ready(value)
    if _is_allowed_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("unsafe payload object must be a plain value")
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _is_allowed_dataclass(value: object) -> bool:
    return type(value) in (
        ResearchEventAuthorityClaimConflictMemoryScorecardConfig,
        ResearchEventAuthorityClaimConflictMemoryScorecardInput,
        ResearchEventAuthorityClaimConflictMemoryScorecardRow,
        ResearchEventAuthorityClaimConflictMemoryScorecardReport,
        _DictFlags,
    )


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if _is_allowed_dataclass(value):
        for field in fields(value):
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError(f"unsafe payload object in {label}")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    if type(value) in (int, float):
        return
    raise ValueError(f"unsafe payload object in {label}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    if _has_bad_fragment(value):
        raise ValueError(f"unsafe public payload in {label}")


def _has_bad_fragment(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _BAD_PUBLIC_FRAGMENTS):
        return True
    marker = "".join(("d", "b"))
    return (
        normalized == marker
        or normalized.startswith(f"{marker}_")
        or normalized.endswith(f"_{marker}")
        or f"{marker} " in normalized
        or f" {marker}" in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_string(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) > 128 or not value[0].isalnum():
        raise ValueError(f"{field_name} must be a canonical public identifier")
    for character in value:
        if not (character.isalnum() or character in "_.-"):
            raise ValueError(f"{field_name} must be a canonical public identifier")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < _ZERO_RATIO or quantized > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _bounded_ratio(value: Decimal) -> Decimal:
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO:
        return _ZERO_RATIO
    if quantized > _ONE_RATIO:
        return _ONE_RATIO
    return quantized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    return _bounded_ratio(numerator / denominator)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_string("reason_codes", value)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return max(values).quantize(_RATIO_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return (sum(values, _ZERO_RATIO) / Decimal(len(values))).quantize(_RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_CLAIM_CONFLICT_MEMORY_SCORECARD_CONFIG_VERSION",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "ResearchEventAuthorityClaimConflictMemoryScorecardConfig",
    "ResearchEventAuthorityClaimConflictMemoryScorecardInput",
    "ResearchEventAuthorityClaimConflictMemoryScorecardRow",
    "ResearchEventAuthorityClaimConflictMemoryScorecardReport",
    "build_research_event_authority_claim_conflict_memory_scorecard_report",
    "research_event_authority_claim_conflict_memory_scorecard_report_payload",
)
