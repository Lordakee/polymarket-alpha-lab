"""Pure report-only event-resolution claim authority memory floor report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-event-resolution-claim-authority-memory-floor-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_EMPTY_REASON = "claim_authority_memory_floor_report_empty"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candidate",
    "candidate",
    "market",
    "source",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "private_",
    "secret",
    "credential",
    "://",
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionClaimAuthorityMemoryFloorConfig",
    "ResearchEventResolutionClaimAuthorityMemoryFloorInput",
    "ResearchEventResolutionClaimAuthorityMemoryFloorReport",
    "ResearchEventResolutionClaimAuthorityMemoryFloorRow",
    "build_research_event_resolution_claim_authority_memory_floor_report",
    "research_event_resolution_claim_authority_memory_floor_report_digest",
    "research_event_resolution_claim_authority_memory_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionClaimAuthorityMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
    )
    memory_age_watch_seconds: Decimal = Decimal("3600.000000")
    memory_age_block_seconds: Decimal = Decimal("86400.000000")
    floor_watch_score: Decimal = Decimal("0.700000")
    floor_block_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionClaimAuthorityMemoryFloorConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimAuthorityMemoryFloorConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionClaimAuthorityMemoryFloorConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
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
        if self.memory_age_block_seconds <= self.memory_age_watch_seconds:
            raise ValueError(
                "memory_age_block_seconds must exceed memory_age_watch_seconds",
            )
        if self.floor_block_score > self.floor_watch_score:
            raise ValueError("floor_block_score must not exceed floor_watch_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimAuthorityMemoryFloorInput:
    event_bucket: str
    claim_bucket: str
    private_subject_ref: str
    private_evidence_ref: str
    private_memory_ref: str
    claim_observed_at: datetime
    authority_memory_checked_at: datetime
    authority_score: Decimal
    parser_confidence: Decimal
    memory_support_score: Decimal
    resolution_confidence: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionClaimAuthorityMemoryFloorInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimAuthorityMemoryFloorInput:
            raise ValueError(
                "input must be exactly "
                "ResearchEventResolutionClaimAuthorityMemoryFloorInput",
            )
        for field_name in ("event_bucket", "claim_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "private_subject_ref",
            "private_evidence_ref",
            "private_memory_ref",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "authority_memory_checked_at",
            _as_utc(
                "authority_memory_checked_at",
                self.authority_memory_checked_at,
            ),
        )
        for field_name in (
            "authority_score",
            "parser_confidence",
            "memory_support_score",
            "resolution_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimAuthorityMemoryFloorRow:
    claim_digest: str
    authority_digest: str
    claim_age_seconds: Decimal
    memory_age_seconds: Decimal
    memory_age_watch_seconds: Decimal
    memory_age_block_seconds: Decimal
    floor_watch_score: Decimal
    floor_block_score: Decimal
    authority_score: Decimal
    parser_confidence: Decimal
    memory_support_score: Decimal
    resolution_confidence: Decimal
    memory_age_pressure_score: Decimal
    memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionClaimAuthorityMemoryFloorRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimAuthorityMemoryFloorRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionClaimAuthorityMemoryFloorRow",
            )
        _require_digest_reference("claim_digest", self.claim_digest)
        _require_digest_reference("authority_digest", self.authority_digest)
        for field_name in (
            "claim_age_seconds",
            "memory_age_seconds",
        ):
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
        for field_name in (
            "floor_watch_score",
            "floor_block_score",
            "authority_score",
            "parser_confidence",
            "memory_support_score",
            "resolution_confidence",
            "memory_age_pressure_score",
            "memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.floor_block_score > self.floor_watch_score:
            raise ValueError("floor_block_score must not exceed floor_watch_score")
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
class ResearchEventResolutionClaimAuthorityMemoryFloorReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_memory_floor_score: Decimal
    average_memory_floor_score: Decimal
    max_memory_age_seconds: Decimal
    status: str
    rows: tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionClaimAuthorityMemoryFloorReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimAuthorityMemoryFloorReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventResolutionClaimAuthorityMemoryFloorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
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
        for field_name in ("min_memory_floor_score", "average_memory_floor_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "rows",
            _normalize_report_rows(self.rows),
        )
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
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_event_resolution_claim_authority_memory_floor_report(
    rows: tuple[
        ResearchEventResolutionClaimAuthorityMemoryFloorInput
        | ResearchEventResolutionClaimAuthorityMemoryFloorRow,
        ...
    ]
    | list[
        ResearchEventResolutionClaimAuthorityMemoryFloorInput
        | ResearchEventResolutionClaimAuthorityMemoryFloorRow
    ],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig | None = None,
) -> ResearchEventResolutionClaimAuthorityMemoryFloorReport:
    if config is None:
        config = ResearchEventResolutionClaimAuthorityMemoryFloorConfig()
    if type(config) is not ResearchEventResolutionClaimAuthorityMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionClaimAuthorityMemoryFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(rows)
    for item in normalized_items:
        if type(item) is ResearchEventResolutionClaimAuthorityMemoryFloorInput:
            if item.claim_observed_at > generated_at:
                raise ValueError("claim_observed_at must not be after generated_at")
            if item.authority_memory_checked_at > generated_at:
                raise ValueError(
                    "authority_memory_checked_at must not be after generated_at",
                )
    report_rows = _sort_rows(
        tuple(
            item
            if type(item) is ResearchEventResolutionClaimAuthorityMemoryFloorRow
            else _row_for_input(item, config, generated_at)
            for item in normalized_items
        ),
    )
    return ResearchEventResolutionClaimAuthorityMemoryFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=_decimal_count(len(report_rows)),
        pass_count=_decimal_count(_status_count(report_rows, "pass")),
        watch_count=_decimal_count(_status_count(report_rows, "watch")),
        block_count=_decimal_count(_status_count(report_rows, "block")),
        min_memory_floor_score=min(
            (row.memory_floor_score for row in report_rows),
            default=_ZERO,
        ),
        average_memory_floor_score=_average(
            tuple(row.memory_floor_score for row in report_rows),
        ),
        max_memory_age_seconds=max(
            (row.memory_age_seconds for row in report_rows),
            default=_ZERO,
        ),
        status=_report_status(report_rows),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows),
    )


def research_event_resolution_claim_authority_memory_floor_report_payload(
    report: ResearchEventResolutionClaimAuthorityMemoryFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionClaimAuthorityMemoryFloorReport:
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
            "report must be a ResearchEventResolutionClaimAuthorityMemoryFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_raw_public_numbers("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


def research_event_resolution_claim_authority_memory_floor_report_digest(
    report: ResearchEventResolutionClaimAuthorityMemoryFloorReport,
) -> str:
    if type(report) is not ResearchEventResolutionClaimAuthorityMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchEventResolutionClaimAuthorityMemoryFloorReport",
        )
    _require_hard_flags("report", report)
    return _report_digest_from_report(report)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _row_for_input(
    item: ResearchEventResolutionClaimAuthorityMemoryFloorInput,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClaimAuthorityMemoryFloorRow:
    claim_age = _seconds_between(generated_at, item.claim_observed_at)
    memory_age = _seconds_between(generated_at, item.authority_memory_checked_at)
    memory_age_pressure = _memory_age_pressure_score(memory_age, config)
    memory_floor = min(
        item.authority_score,
        item.parser_confidence,
        item.memory_support_score,
        item.resolution_confidence,
    )
    status = _row_status(
        memory_age_seconds=memory_age,
        memory_floor_score=memory_floor,
        config=config,
    )
    return ResearchEventResolutionClaimAuthorityMemoryFloorRow(
        claim_digest=_digest_reference(
            f"{item.event_bucket}\x1f{item.claim_bucket}\x1f{item.private_subject_ref}",
        ),
        authority_digest=_digest_reference(
            f"{item.claim_bucket}\x1f{item.private_evidence_ref}\x1f{item.private_memory_ref}",
        ),
        claim_age_seconds=claim_age,
        memory_age_seconds=memory_age,
        memory_age_watch_seconds=config.memory_age_watch_seconds,
        memory_age_block_seconds=config.memory_age_block_seconds,
        floor_watch_score=config.floor_watch_score,
        floor_block_score=config.floor_block_score,
        authority_score=item.authority_score,
        parser_confidence=item.parser_confidence,
        memory_support_score=item.memory_support_score,
        resolution_confidence=item.resolution_confidence,
        memory_age_pressure_score=memory_age_pressure,
        memory_floor_score=memory_floor,
        status=status,
        reason_codes=_row_reason_codes(
            item_reason_codes=item.reason_codes,
            status=status,
            memory_age_seconds=memory_age,
            authority_score=item.authority_score,
            parser_confidence=item.parser_confidence,
            memory_support_score=item.memory_support_score,
            resolution_confidence=item.resolution_confidence,
            config=config,
        ),
    )


def _memory_age_pressure_score(
    memory_age_seconds: Decimal,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig,
) -> Decimal:
    if memory_age_seconds <= config.memory_age_watch_seconds:
        return _ZERO
    if memory_age_seconds >= config.memory_age_block_seconds:
        return _ONE
    return _clamp_ratio(memory_age_seconds / config.memory_age_block_seconds)


def _row_status(
    *,
    memory_age_seconds: Decimal,
    memory_floor_score: Decimal,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig,
) -> str:
    if (
        memory_age_seconds >= config.memory_age_block_seconds
        or memory_floor_score <= config.floor_block_score
    ):
        return "block"
    if (
        memory_age_seconds >= config.memory_age_watch_seconds
        or memory_floor_score < config.floor_watch_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item_reason_codes: tuple[str, ...],
    status: str,
    memory_age_seconds: Decimal,
    authority_score: Decimal,
    parser_confidence: Decimal,
    memory_support_score: Decimal,
    resolution_confidence: Decimal,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig,
) -> tuple[str, ...]:
    reasons = [f"claim_authority_memory_floor_{status}"]
    reasons.extend(
        _component_reason_codes(
            "authority_score",
            authority_score,
            config,
        ),
    )
    if memory_age_seconds >= config.memory_age_block_seconds:
        reasons.append("memory_age_block")
    elif memory_age_seconds >= config.memory_age_watch_seconds:
        reasons.append("memory_age_watch")
    reasons.extend(
        _component_reason_codes(
            "memory_support",
            memory_support_score,
            config,
        ),
    )
    reasons.extend(
        _component_reason_codes(
            "parser_confidence",
            parser_confidence,
            config,
        ),
    )
    reasons.extend(
        _component_reason_codes(
            "resolution_confidence",
            resolution_confidence,
            config,
        ),
    )
    reasons.extend(f"input_{reason}" for reason in item_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reasons), allow_empty=False)


def _component_reason_codes(
    prefix: str,
    score: Decimal,
    config: ResearchEventResolutionClaimAuthorityMemoryFloorConfig,
) -> tuple[str, ...]:
    if score <= config.floor_block_score:
        return (f"{prefix}_block",)
    if score < config.floor_watch_score:
        return (f"{prefix}_watch",)
    return ()


def _validate_row_consistency(
    row: ResearchEventResolutionClaimAuthorityMemoryFloorRow,
) -> None:
    expected_floor = min(
        row.authority_score,
        row.parser_confidence,
        row.memory_support_score,
        row.resolution_confidence,
    )
    if row.memory_floor_score != expected_floor:
        raise ValueError("memory_floor_score must match component score floor")
    config = ResearchEventResolutionClaimAuthorityMemoryFloorConfig(
        memory_age_watch_seconds=row.memory_age_watch_seconds,
        memory_age_block_seconds=row.memory_age_block_seconds,
        floor_watch_score=row.floor_watch_score,
        floor_block_score=row.floor_block_score,
    )
    expected_pressure = _memory_age_pressure_score(row.memory_age_seconds, config)
    if row.memory_age_pressure_score != expected_pressure:
        raise ValueError("memory_age_pressure_score must match memory age")
    expected_status = _row_status(
        memory_age_seconds=row.memory_age_seconds,
        memory_floor_score=row.memory_floor_score,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match memory floor score")

def _validate_report_consistency(
    report: ResearchEventResolutionClaimAuthorityMemoryFloorReport,
) -> None:
    rows = report.rows
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    row_count = _decimal_count(len(rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    for status in ("pass", "watch", "block"):
        expected_count = _decimal_count(_status_count(rows, status))
        actual_count = getattr(report, f"{status}_count")
        if actual_count != expected_count:
            raise ValueError(f"{status}_count must match rows")
    if report.min_memory_floor_score != min(
        (row.memory_floor_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_memory_floor_score must match rows")
    if report.average_memory_floor_score != _average(
        tuple(row.memory_floor_score for row in rows),
    ):
        raise ValueError("average_memory_floor_score must match rows")
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
    rows: tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "block"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...],
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
    rows: tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _sort_rows(
    rows: tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...],
) -> tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventResolutionClaimAuthorityMemoryFloorRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.status],
        row.memory_floor_score,
        -row.memory_age_seconds,
        row.claim_digest,
        row.authority_digest,
    )


def _normalize_inputs(
    value: object,
) -> tuple[
    ResearchEventResolutionClaimAuthorityMemoryFloorInput
    | ResearchEventResolutionClaimAuthorityMemoryFloorRow,
    ...
]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    items = tuple(value)
    for item in items:
        if type(item) not in (
            ResearchEventResolutionClaimAuthorityMemoryFloorInput,
            ResearchEventResolutionClaimAuthorityMemoryFloorRow,
        ):
            raise ValueError("rows must contain memory floor inputs or rows")
        _require_hard_flags("row", item)
    return items


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchEventResolutionClaimAuthorityMemoryFloorRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventResolutionClaimAuthorityMemoryFloorRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionClaimAuthorityMemoryFloorRow",
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
    row: ResearchEventResolutionClaimAuthorityMemoryFloorRow,
) -> str:
    payload = _json_ready(asdict(row))
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _sha256_payload(payload)


def _report_digest_from_report(
    report: ResearchEventResolutionClaimAuthorityMemoryFloorReport,
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


def _require_status(field_name: str, value: object) -> str:
    if value not in ("pass", "watch", "block"):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    if type(value) is not str:
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
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
        payload = asdict(value)
        _reject_unsafe_public_payload(
            field_name,
            payload,
            allow_json_containers=True,
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string(f"{field_name}.{key}", str(key))
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
