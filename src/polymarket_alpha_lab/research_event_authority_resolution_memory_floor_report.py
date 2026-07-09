"""Pure report-only authority-resolution memory floor report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-event-authority-resolution-memory-floor-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_EMPTY_REASON = "authority_resolution_memory_floor_report_empty"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candi" + "date",
    "candi" + "date",
    "mar" + "ket",
    "slu" + "g",
    "ques" + "tion",
    "so" + "urce",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "live " + "trading",
    "siz" + "ing",
    "recommen" + "dation",
    "private_",
    "secret",
    "credential",
    "://",
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchEventAuthorityResolutionMemoryFloorConfig",
    "ResearchEventAuthorityResolutionMemoryFloorInput",
    "ResearchEventAuthorityResolutionMemoryFloorReport",
    "ResearchEventAuthorityResolutionMemoryFloorRow",
    "build_research_event_authority_resolution_memory_floor_report",
    "research_event_authority_resolution_memory_floor_report_digest",
    "research_event_authority_resolution_memory_floor_report_payload",
    "validate_research_event_authority_resolution_memory_floor_public_payload",
)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION
    )
    memory_age_watch_seconds: Decimal = Decimal("3600.000000")
    memory_age_block_seconds: Decimal = Decimal("86400.000000")
    floor_watch_score: Decimal = Decimal("0.700000")
    floor_block_score: Decimal = Decimal("0.500000")
    gap_block_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventAuthorityResolutionMemoryFloorConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryFloorConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventAuthorityResolutionMemoryFloorConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("memory_age_watch_seconds", "memory_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("floor_watch_score", "floor_block_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gap_block_count",
            _require_positive_whole_decimal("gap_block_count", self.gap_block_count),
        )
        if self.memory_age_block_seconds <= self.memory_age_watch_seconds:
            raise ValueError(
                "memory_age_block_seconds must exceed memory_age_watch_seconds",
            )
        if self.floor_block_score > self.floor_watch_score:
            raise ValueError("floor_block_score must not exceed floor_watch_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryFloorInput:
    event_bucket: str
    resolution_bucket: str
    private_subject_ref: str
    private_venue_ref: str
    private_evidence_ref: str
    private_memory_ref: str
    observed_at: datetime
    authority_resolution_checked_at: datetime
    authority_memory_score: Decimal
    rule_alignment_score: Decimal
    evidence_consensus_score: Decimal
    finality_confidence_score: Decimal
    unresolved_gap_count: Decimal = Decimal("0.000000")
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventAuthorityResolutionMemoryFloorInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryFloorInput:
            raise ValueError(
                "input must be exactly ResearchEventAuthorityResolutionMemoryFloorInput",
            )
        for field_name in ("event_bucket", "resolution_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "private_subject_ref",
            "private_venue_ref",
            "private_evidence_ref",
            "private_memory_ref",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "authority_resolution_checked_at",
            _as_utc(
                "authority_resolution_checked_at",
                self.authority_resolution_checked_at,
            ),
        )
        for field_name in (
            "authority_memory_score",
            "rule_alignment_score",
            "evidence_consensus_score",
            "finality_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_gap_count",
            _require_nonnegative_whole_decimal(
                "unresolved_gap_count",
                self.unresolved_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryFloorRow:
    event_digest: str
    authority_digest: str
    resolution_digest: str
    observed_age_seconds: Decimal
    memory_age_seconds: Decimal
    memory_age_watch_seconds: Decimal
    memory_age_block_seconds: Decimal
    floor_watch_score: Decimal
    floor_block_score: Decimal
    gap_block_count: Decimal
    authority_memory_score: Decimal
    rule_alignment_score: Decimal
    evidence_consensus_score: Decimal
    finality_confidence_score: Decimal
    unresolved_gap_count: Decimal
    memory_age_pressure_score: Decimal
    resolution_memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventAuthorityResolutionMemoryFloorRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryFloorRow:
            raise ValueError(
                "row must be exactly ResearchEventAuthorityResolutionMemoryFloorRow",
            )
        for field_name in ("event_digest", "authority_digest", "resolution_digest"):
            _require_digest_reference(field_name, getattr(self, field_name))
        for field_name in ("observed_age_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_age_watch_seconds", "memory_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.memory_age_block_seconds <= self.memory_age_watch_seconds:
            raise ValueError(
                "memory_age_block_seconds must exceed memory_age_watch_seconds",
            )
        for field_name in ("floor_watch_score", "floor_block_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.floor_block_score > self.floor_watch_score:
            raise ValueError("floor_block_score must not exceed floor_watch_score")
        object.__setattr__(
            self,
            "gap_block_count",
            _require_positive_whole_decimal("gap_block_count", self.gap_block_count),
        )
        for field_name in (
            "authority_memory_score",
            "rule_alignment_score",
            "evidence_consensus_score",
            "finality_confidence_score",
            "memory_age_pressure_score",
            "resolution_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_gap_count",
            _require_nonnegative_whole_decimal(
                "unresolved_gap_count",
                self.unresolved_gap_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest_from_row(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match row payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryFloorReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_resolution_memory_floor_score: Decimal
    average_resolution_memory_floor_score: Decimal
    max_memory_age_seconds: Decimal
    status: str
    rows: tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventAuthorityResolutionMemoryFloorReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryFloorReport:
            raise ValueError(
                "report must be exactly ResearchEventAuthorityResolutionMemoryFloorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_resolution_memory_floor_score",
            "average_resolution_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_report(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_event_authority_resolution_memory_floor_report(
    items: tuple[
        ResearchEventAuthorityResolutionMemoryFloorInput
        | ResearchEventAuthorityResolutionMemoryFloorRow,
        ...
    ]
    | list[
        ResearchEventAuthorityResolutionMemoryFloorInput
        | ResearchEventAuthorityResolutionMemoryFloorRow
    ],
    *,
    generated_at: datetime,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig | None = None,
) -> ResearchEventAuthorityResolutionMemoryFloorReport:
    if config is None:
        config = ResearchEventAuthorityResolutionMemoryFloorConfig()
    if type(config) is not ResearchEventAuthorityResolutionMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchEventAuthorityResolutionMemoryFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    for item in normalized_items:
        if type(item) is ResearchEventAuthorityResolutionMemoryFloorInput:
            if item.observed_at > generated_at:
                raise ValueError("observed_at must not be after generated_at")
            if item.authority_resolution_checked_at > generated_at:
                raise ValueError(
                    "authority_resolution_checked_at must not be after generated_at",
                )
    rows = _sort_rows(
        tuple(
            item
            if type(item) is ResearchEventAuthorityResolutionMemoryFloorRow
            else _row_for_input(item, config, generated_at)
            for item in normalized_items
        ),
    )
    return ResearchEventAuthorityResolutionMemoryFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        item_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        min_resolution_memory_floor_score=min(
            (row.resolution_memory_floor_score for row in rows),
            default=_ZERO,
        ),
        average_resolution_memory_floor_score=_average(
            tuple(row.resolution_memory_floor_score for row in rows),
        ),
        max_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_event_authority_resolution_memory_floor_report_payload(
    report: ResearchEventAuthorityResolutionMemoryFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventAuthorityResolutionMemoryFloorReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _reject_raw_public_numbers("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
    else:
        raise ValueError(
            "report must be a ResearchEventAuthorityResolutionMemoryFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_authority_resolution_memory_floor_public_payload(payload)
    return payload


def validate_research_event_authority_resolution_memory_floor_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_raw_public_numbers("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_schema(payload)
    _validate_payload_digest(payload)
    return True


def research_event_authority_resolution_memory_floor_report_digest(
    report: ResearchEventAuthorityResolutionMemoryFloorReport,
) -> str:
    if type(report) is not ResearchEventAuthorityResolutionMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchEventAuthorityResolutionMemoryFloorReport",
        )
    _require_hard_flags("report", report)
    return _report_digest_from_report(report)


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


def _row_for_input(
    item: ResearchEventAuthorityResolutionMemoryFloorInput,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchEventAuthorityResolutionMemoryFloorRow:
    observed_age = _seconds_between(generated_at, item.observed_at)
    memory_age = _seconds_between(generated_at, item.authority_resolution_checked_at)
    memory_age_pressure = _memory_age_pressure_score(memory_age, config)
    resolution_memory_floor = min(
        item.authority_memory_score,
        item.rule_alignment_score,
        item.evidence_consensus_score,
        item.finality_confidence_score,
    )
    status = _row_status(
        memory_age_seconds=memory_age,
        resolution_memory_floor_score=resolution_memory_floor,
        unresolved_gap_count=item.unresolved_gap_count,
        config=config,
    )
    return ResearchEventAuthorityResolutionMemoryFloorRow(
        event_digest=_digest_reference(
            f"{item.event_bucket}\x1f{item.private_subject_ref}\x1f{item.private_venue_ref}",
        ),
        authority_digest=_digest_reference(
            f"{item.resolution_bucket}\x1f{item.private_evidence_ref}",
        ),
        resolution_digest=_digest_reference(
            f"{item.resolution_bucket}\x1f{item.private_memory_ref}",
        ),
        observed_age_seconds=observed_age,
        memory_age_seconds=memory_age,
        memory_age_watch_seconds=config.memory_age_watch_seconds,
        memory_age_block_seconds=config.memory_age_block_seconds,
        floor_watch_score=config.floor_watch_score,
        floor_block_score=config.floor_block_score,
        gap_block_count=config.gap_block_count,
        authority_memory_score=item.authority_memory_score,
        rule_alignment_score=item.rule_alignment_score,
        evidence_consensus_score=item.evidence_consensus_score,
        finality_confidence_score=item.finality_confidence_score,
        unresolved_gap_count=item.unresolved_gap_count,
        memory_age_pressure_score=memory_age_pressure,
        resolution_memory_floor_score=resolution_memory_floor,
        status=status,
        reason_codes=_row_reason_codes(
            item_reason_codes=item.reason_codes,
            status=status,
            memory_age_seconds=memory_age,
            authority_memory_score=item.authority_memory_score,
            rule_alignment_score=item.rule_alignment_score,
            evidence_consensus_score=item.evidence_consensus_score,
            finality_confidence_score=item.finality_confidence_score,
            unresolved_gap_count=item.unresolved_gap_count,
            config=config,
        ),
    )


def _memory_age_pressure_score(
    memory_age_seconds: Decimal,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig,
) -> Decimal:
    if memory_age_seconds <= config.memory_age_watch_seconds:
        return _ZERO
    if memory_age_seconds >= config.memory_age_block_seconds:
        return _ONE
    return _clamp_ratio(memory_age_seconds / config.memory_age_block_seconds)


def _row_status(
    *,
    memory_age_seconds: Decimal,
    resolution_memory_floor_score: Decimal,
    unresolved_gap_count: Decimal,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig,
) -> str:
    if (
        memory_age_seconds >= config.memory_age_block_seconds
        or resolution_memory_floor_score <= config.floor_block_score
        or unresolved_gap_count >= config.gap_block_count
    ):
        return "block"
    if (
        memory_age_seconds >= config.memory_age_watch_seconds
        or resolution_memory_floor_score < config.floor_watch_score
        or unresolved_gap_count > _ZERO
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item_reason_codes: tuple[str, ...],
    status: str,
    memory_age_seconds: Decimal,
    authority_memory_score: Decimal,
    rule_alignment_score: Decimal,
    evidence_consensus_score: Decimal,
    finality_confidence_score: Decimal,
    unresolved_gap_count: Decimal,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig,
) -> tuple[str, ...]:
    reasons = [f"authority_resolution_memory_floor_{status}"]
    reasons.extend(
        _component_reason_codes(
            "authority_memory_score",
            authority_memory_score,
            config,
        ),
    )
    reasons.extend(
        _component_reason_codes(
            "rule_alignment_score",
            rule_alignment_score,
            config,
        ),
    )
    reasons.extend(
        _component_reason_codes(
            "evidence_consensus_score",
            evidence_consensus_score,
            config,
        ),
    )
    reasons.extend(
        _component_reason_codes(
            "finality_confidence_score",
            finality_confidence_score,
            config,
        ),
    )
    if memory_age_seconds >= config.memory_age_block_seconds:
        reasons.append("memory_age_block")
    elif memory_age_seconds >= config.memory_age_watch_seconds:
        reasons.append("memory_age_watch")
    if unresolved_gap_count >= config.gap_block_count:
        reasons.append("unresolved_gap_block")
    elif unresolved_gap_count > _ZERO:
        reasons.append("unresolved_gap_watch")
    reasons.extend(f"input_{reason}" for reason in item_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reasons), allow_empty=False)


def _component_reason_codes(
    prefix: str,
    score: Decimal,
    config: ResearchEventAuthorityResolutionMemoryFloorConfig,
) -> tuple[str, ...]:
    if score <= config.floor_block_score:
        return (f"{prefix}_block",)
    if score < config.floor_watch_score:
        return (f"{prefix}_watch",)
    return ()


def _validate_row_consistency(
    row: ResearchEventAuthorityResolutionMemoryFloorRow,
) -> None:
    expected_floor = min(
        row.authority_memory_score,
        row.rule_alignment_score,
        row.evidence_consensus_score,
        row.finality_confidence_score,
    )
    if row.resolution_memory_floor_score != expected_floor:
        raise ValueError(
            "resolution_memory_floor_score must match component score floor",
        )
    config = ResearchEventAuthorityResolutionMemoryFloorConfig(
        memory_age_watch_seconds=row.memory_age_watch_seconds,
        memory_age_block_seconds=row.memory_age_block_seconds,
        floor_watch_score=row.floor_watch_score,
        floor_block_score=row.floor_block_score,
        gap_block_count=row.gap_block_count,
    )
    expected_pressure = _memory_age_pressure_score(row.memory_age_seconds, config)
    if row.memory_age_pressure_score != expected_pressure:
        raise ValueError("memory_age_pressure_score must match memory age")
    expected_status = _row_status(
        memory_age_seconds=row.memory_age_seconds,
        resolution_memory_floor_score=row.resolution_memory_floor_score,
        unresolved_gap_count=row.unresolved_gap_count,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match resolution memory floor")


def _validate_report_consistency(
    report: ResearchEventAuthorityResolutionMemoryFloorReport,
) -> None:
    rows = report.rows
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    item_count = _decimal_count(len(rows))
    if report.item_count != item_count:
        raise ValueError("item_count must match rows")
    for status in ("pass", "watch", "block"):
        expected_count = _decimal_count(_status_count(rows, status))
        actual_count = getattr(report, f"{status}_count")
        if actual_count != expected_count:
            raise ValueError(f"{status}_count must match rows")
    if report.min_resolution_memory_floor_score != min(
        (row.resolution_memory_floor_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_resolution_memory_floor_score must match rows")
    if report.average_resolution_memory_floor_score != _average(
        tuple(row.resolution_memory_floor_score for row in rows),
    ):
        raise ValueError("average_resolution_memory_floor_score must match rows")
    if report.max_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _report_status(
    rows: tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "block"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reasons: list[str] = []
    for row in rows:
        for reason in row.reason_codes:
            if reason not in reasons:
                reasons.append(reason)
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _sort_rows(
    rows: tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...],
) -> tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventAuthorityResolutionMemoryFloorRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.status],
        row.resolution_memory_floor_score,
        -row.memory_age_seconds,
        row.event_digest,
        row.authority_digest,
        row.resolution_digest,
    )


def _normalize_inputs(
    value: object,
) -> tuple[
    ResearchEventAuthorityResolutionMemoryFloorInput
    | ResearchEventAuthorityResolutionMemoryFloorRow,
    ...
]:
    if type(value) not in (tuple, list):
        raise ValueError("items must be a tuple or list")
    items = tuple(value)
    for item in items:
        if type(item) not in (
            ResearchEventAuthorityResolutionMemoryFloorInput,
            ResearchEventAuthorityResolutionMemoryFloorRow,
        ):
            raise ValueError("items must contain memory floor inputs or rows")
        _require_hard_flags("item", item)
    return items


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchEventAuthorityResolutionMemoryFloorRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventAuthorityResolutionMemoryFloorRow:
            raise ValueError(
                "rows must contain ResearchEventAuthorityResolutionMemoryFloorRow",
            )
        _require_hard_flags("row", row)
    return rows


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _q(
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _q(sum(values, _ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _q(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _q(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _digest_reference(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _row_digest_from_row(
    row: ResearchEventAuthorityResolutionMemoryFloorRow,
) -> str:
    payload = _json_ready(asdict(row))
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _sha256_payload(payload)


def _report_digest_from_report(
    report: ResearchEventAuthorityResolutionMemoryFloorReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _sha256_payload(payload)


def _sha256_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if _sha256_payload(unsigned) != digest:
        raise ValueError("derived_validation_digest does not match report payload")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_digest = row.get("derived_validation_digest")
        if type(row_digest) is not str:
            raise ValueError("row derived_validation_digest must be a sha256 digest")
        _require_sha256_digest("row derived_validation_digest", row_digest)
        row_unsigned = dict(row)
        row_unsigned.pop("derived_validation_digest", None)
        if _sha256_payload(row_unsigned) != row_digest:
            raise ValueError("derived_validation_digest does not match row payload")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    report_keys = {
        "generated_at",
        "config_version",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_resolution_memory_floor_score",
        "average_resolution_memory_floor_score",
        "max_memory_age_seconds",
        "status",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    row_keys = {
        "event_digest",
        "authority_digest",
        "resolution_digest",
        "observed_age_seconds",
        "memory_age_seconds",
        "memory_age_watch_seconds",
        "memory_age_block_seconds",
        "floor_watch_score",
        "floor_block_score",
        "gap_block_count",
        "authority_memory_score",
        "rule_alignment_score",
        "evidence_consensus_score",
        "finality_confidence_score",
        "unresolved_gap_count",
        "memory_age_pressure_score",
        "resolution_memory_floor_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != report_keys:
        raise ValueError("public payload must use the report schema")
    if payload["config_version"] != (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_FLOOR_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    _require_public_datetime_string("generated_at", payload["generated_at"])
    for field_name in (
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_resolution_memory_floor_score",
        "average_resolution_memory_floor_score",
        "max_memory_age_seconds",
    ):
        _require_decimal_string(field_name, payload[field_name])
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_reason_codes("reason_codes", payload["reason_codes"], allow_empty=False)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        if set(row) != row_keys:
            raise ValueError("row payload must use the report schema")
        for field_name in ("event_digest", "authority_digest", "resolution_digest"):
            _require_digest_reference(field_name, row[field_name])
        _require_status("row status", row["status"])
        if type(row["reason_codes"]) is not list:
            raise ValueError("row reason_codes must be a list")
        _normalize_reason_codes(
            "row reason_codes",
            row["reason_codes"],
            allow_empty=False,
        )
        for field_name in (
            "observed_age_seconds",
            "memory_age_seconds",
            "memory_age_watch_seconds",
            "memory_age_block_seconds",
            "floor_watch_score",
            "floor_block_score",
            "gap_block_count",
            "authority_memory_score",
            "rule_alignment_score",
            "evidence_consensus_score",
            "finality_confidence_score",
            "unresolved_gap_count",
            "memory_age_pressure_score",
            "resolution_memory_floor_score",
        ):
            _require_decimal_string(field_name, row[field_name])
        _require_hard_flags("row", _DictFlags(row))


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _require_nonempty_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_datetime_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone data")
    if parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_digest_reference(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or not value.startswith("sha256:")
        or not _DIGEST_RE.fullmatch(value.removeprefix("sha256:"))
    ):
        raise ValueError(f"{field_name} must be a sha256 digest reference")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    _require_decimal(field_name, Decimal(value))
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ("pass", "watch", "block"):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not _REASON_CODE_RE.fullmatch(value):
            raise ValueError(f"{field_name} must contain reason code identifiers")
        if value in normalized:
            raise ValueError(f"{field_name} must not contain duplicate values")
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(
            field_name,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(f"{field_name}.{key}", key)
            _reject_unsafe_public_payload(
                f"{field_name}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if allow_json_containers and isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{field_name}[{index}]",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public payload content")


def _reject_raw_public_numbers(field_name: str, value: object) -> None:
    if type(value) in (int, float):
        raise ValueError(f"{field_name} numeric values must be Decimal|string")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_raw_public_numbers(f"{field_name}.{key}", item)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_raw_public_numbers(f"{field_name}[{index}]", item)
