"""Readonly event authority resolution memory decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-authority-resolution-memory-decay-report-v0"
)
RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_event_authority_resolution_memory_decay_empty"
CLEAR_REASON = "event_authority_resolution_memory_decay_clear"
AUTHORITY_RELIABILITY_WATCH_REASON = "authority_reliability_watch"
AUTHORITY_RELIABILITY_BLOCK_REASON = "authority_reliability_block"
RESOLUTION_AGE_WATCH_REASON = "resolution_age_watch"
RESOLUTION_AGE_BLOCK_REASON = "resolution_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
MEMORY_AGE_BLOCK_REASON = "memory_age_block"
PARSER_CONFIDENCE_WATCH_REASON = "parser_confidence_watch"
PARSER_CONFIDENCE_BLOCK_REASON = "parser_confidence_block"
EVIDENCE_QUORUM_WATCH_REASON = "evidence_quorum_watch"
EVIDENCE_QUORUM_BLOCK_REASON = "evidence_quorum_block"
CONFLICT_PRESSURE_WATCH_REASON = "conflict_pressure_watch"
CONFLICT_PRESSURE_BLOCK_REASON = "conflict_pressure_block"

ROW_REASON_CODES = (
    AUTHORITY_RELIABILITY_BLOCK_REASON,
    RESOLUTION_AGE_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    PARSER_CONFIDENCE_BLOCK_REASON,
    EVIDENCE_QUORUM_BLOCK_REASON,
    CONFLICT_PRESSURE_BLOCK_REASON,
    AUTHORITY_RELIABILITY_WATCH_REASON,
    RESOLUTION_AGE_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    PARSER_CONFIDENCE_WATCH_REASON,
    EVIDENCE_QUORUM_WATCH_REASON,
    CONFLICT_PRESSURE_WATCH_REASON,
    CLEAR_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SIX = Decimal("6.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DEFAULT_RESOLUTION_SCORE_BLOCK_SECONDS = Decimal("10800.000000")
DEFAULT_MEMORY_SCORE_BLOCK_SECONDS = Decimal("21600.000000")
DEFAULT_EVIDENCE_SCORE_WATCH_COUNT = Decimal("2.000000")
SHA256_HEX_LENGTH = 64


def _j(*parts: str) -> str:
    return "".join(parts)


BAD_PUBLIC_PARTS = frozenset(
    (
        _j("candi", "date"),
        _j("mar", "ket"),
        _j("que", "stion"),
        _j("sour", "ce"),
        _j("ur", "l"),
        _j("te", "xt"),
        _j("d", "sn"),
        _j("ta", "ble"),
        _j("to", "ken"),
        _j("wal", "let"),
        _j("ord", "er"),
        _j("tra", "de"),
        _j("li", "ve"),
        _j("data", "base"),
        _j("net", "work"),
        _j("siz", "ing"),
        _j("recomm", "endation"),
        _j(":", "//"),
        _j("ht", "tp"),
        "www.",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES",
    "ResearchEventAuthorityResolutionMemoryDecayConfig",
    "ResearchEventAuthorityResolutionMemoryDecayInput",
    "ResearchEventAuthorityResolutionMemoryDecayReport",
    "ResearchEventAuthorityResolutionMemoryDecayRow",
    "build_research_event_authority_resolution_memory_decay_report",
    "research_event_authority_resolution_memory_decay_report_digest",
    "research_event_authority_resolution_memory_decay_report_payload",
    "validate_research_event_authority_resolution_memory_decay_public_payload",
    "validate_research_event_authority_resolution_memory_decay_report_digest",
)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    authority_reliability_watch_below: Decimal = Decimal("0.700000")
    authority_reliability_block_below: Decimal = Decimal("0.400000")
    resolution_age_watch_seconds: Decimal = Decimal("3600.000000")
    resolution_age_block_seconds: Decimal = Decimal("10800.000000")
    memory_age_watch_seconds: Decimal = Decimal("7200.000000")
    memory_age_block_seconds: Decimal = Decimal("21600.000000")
    parser_confidence_watch_below: Decimal = Decimal("0.800000")
    parser_confidence_block_below: Decimal = Decimal("0.500000")
    evidence_quorum_watch_count: Decimal = Decimal("2.000000")
    conflict_watch_threshold: Decimal = Decimal("0.300000")
    conflict_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityResolutionMemoryDecayConfig:
            raise TypeError(
                "ResearchEventAuthorityResolutionMemoryDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryDecayConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventAuthorityResolutionMemoryDecayConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_reliability_watch_below",
            "authority_reliability_block_below",
            "parser_confidence_watch_below",
            "parser_confidence_block_below",
            "conflict_watch_threshold",
            "conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_age_watch_seconds",
            "resolution_age_block_seconds",
            "memory_age_watch_seconds",
            "memory_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_quorum_watch_count",
            _require_positive_count(
                "evidence_quorum_watch_count",
                self.evidence_quorum_watch_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_bad_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryDecayInput:
    event_digest: str
    authority_digest: str
    parsed_at: datetime
    authority_reliability_score: Decimal
    resolution_age_seconds: Decimal
    memory_age_seconds: Decimal
    parser_confidence_score: Decimal
    evidence_count: Decimal
    conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityResolutionMemoryDecayInput:
            raise TypeError(
                "ResearchEventAuthorityResolutionMemoryDecayInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryDecayInput:
            raise ValueError(
                "input must be exactly ResearchEventAuthorityResolutionMemoryDecayInput",
            )
        _require_digest("event_digest", self.event_digest)
        _require_digest("authority_digest", self.authority_digest)
        object.__setattr__(self, "parsed_at", _as_utc("parsed_at", self.parsed_at))
        for field_name in (
            "authority_reliability_score",
            "parser_confidence_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolution_age_seconds", "memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count("evidence_count", self.evidence_count),
        )
        _require_hard_flags("input", self)
        _reject_bad_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryDecayRow:
    event_digest: str
    authority_digest: str
    parsed_at: datetime
    observation_age_seconds: Decimal
    authority_reliability_score: Decimal
    authority_reliability_band: str
    resolution_age_seconds: Decimal
    resolution_freshness_band: str
    memory_age_seconds: Decimal
    memory_decay_band: str
    parser_confidence_score: Decimal
    parser_confidence_band: str
    evidence_count: Decimal
    evidence_quorum_band: str
    conflict_score: Decimal
    conflict_band: str
    authority_resolution_memory_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityResolutionMemoryDecayRow:
            raise TypeError(
                "ResearchEventAuthorityResolutionMemoryDecayRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryDecayRow:
            raise ValueError(
                "row must be exactly ResearchEventAuthorityResolutionMemoryDecayRow",
            )
        _require_digest("event_digest", self.event_digest)
        _require_digest("authority_digest", self.authority_digest)
        object.__setattr__(self, "parsed_at", _as_utc("parsed_at", self.parsed_at))
        for field_name in (
            "authority_reliability_score",
            "parser_confidence_score",
            "conflict_score",
            "authority_resolution_memory_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observation_age_seconds",
            "resolution_age_seconds",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count("evidence_count", self.evidence_count),
        )
        _require_one_of(
            "authority_reliability_band",
            self.authority_reliability_band,
            ("trusted", "thin", "weak"),
        )
        _require_one_of(
            "resolution_freshness_band",
            self.resolution_freshness_band,
            ("fresh", "stale", "expired"),
        )
        _require_one_of(
            "memory_decay_band",
            self.memory_decay_band,
            ("fresh", "stale", "expired"),
        )
        _require_one_of(
            "parser_confidence_band",
            self.parser_confidence_band,
            ("strong", "thin", "low"),
        )
        _require_one_of(
            "evidence_quorum_band",
            self.evidence_quorum_band,
            ("covered", "thin", "missing"),
        )
        _require_one_of(
            "conflict_band",
            self.conflict_band,
            ("clear", "elevated", "conflicted"),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_bad_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventAuthorityResolutionMemoryDecayReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    weak_authority_count: Decimal
    stale_resolution_count: Decimal
    decayed_memory_count: Decimal
    low_parser_confidence_count: Decimal
    thin_evidence_quorum_count: Decimal
    conflict_pressure_count: Decimal
    highest_authority_resolution_memory_decay_score: Decimal
    oldest_resolution_age_seconds: Decimal
    oldest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityResolutionMemoryDecayReport:
            raise TypeError(
                "ResearchEventAuthorityResolutionMemoryDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventAuthorityResolutionMemoryDecayReport:
            raise ValueError(
                "report must be exactly ResearchEventAuthorityResolutionMemoryDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "weak_authority_count",
            "stale_resolution_count",
            "decayed_memory_count",
            "low_parser_confidence_count",
            "thin_evidence_quorum_count",
            "conflict_pressure_count",
            "oldest_resolution_age_seconds",
            "oldest_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_authority_resolution_memory_decay_score",
            _require_ratio(
                "highest_authority_resolution_memory_decay_score",
                self.highest_authority_resolution_memory_decay_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_bad_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_authority_resolution_memory_decay_report_payload(self)


def build_research_event_authority_resolution_memory_decay_report(
    inputs: list[ResearchEventAuthorityResolutionMemoryDecayInput]
    | tuple[ResearchEventAuthorityResolutionMemoryDecayInput, ...],
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchEventAuthorityResolutionMemoryDecayReport:
    if config is None:
        config = ResearchEventAuthorityResolutionMemoryDecayConfig()
    if type(config) is not ResearchEventAuthorityResolutionMemoryDecayConfig:
        raise ValueError(
            "config must be a ResearchEventAuthorityResolutionMemoryDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _decay_rows(
        _normalize_inputs(inputs),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchEventAuthorityResolutionMemoryDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_event_count=_status_count(rows, "pass"),
        watch_event_count=_status_count(rows, "watch"),
        block_event_count=_status_count(rows, "block"),
        weak_authority_count=_reason_count(
            rows,
            (AUTHORITY_RELIABILITY_WATCH_REASON, AUTHORITY_RELIABILITY_BLOCK_REASON),
        ),
        stale_resolution_count=_reason_count(
            rows,
            (RESOLUTION_AGE_WATCH_REASON, RESOLUTION_AGE_BLOCK_REASON),
        ),
        decayed_memory_count=_reason_count(
            rows,
            (MEMORY_AGE_WATCH_REASON, MEMORY_AGE_BLOCK_REASON),
        ),
        low_parser_confidence_count=_reason_count(
            rows,
            (PARSER_CONFIDENCE_WATCH_REASON, PARSER_CONFIDENCE_BLOCK_REASON),
        ),
        thin_evidence_quorum_count=_reason_count(
            rows,
            (EVIDENCE_QUORUM_WATCH_REASON, EVIDENCE_QUORUM_BLOCK_REASON),
        ),
        conflict_pressure_count=_reason_count(
            rows,
            (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
        ),
        highest_authority_resolution_memory_decay_score=max(
            (row.authority_resolution_memory_decay_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_resolution_age_seconds=max(
            (row.resolution_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_authority_resolution_memory_decay_report_payload(
    report: ResearchEventAuthorityResolutionMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventAuthorityResolutionMemoryDecayReport:
        validate_research_event_authority_resolution_memory_decay_report_digest(report)
        _require_hard_flags("report", report)
        _reject_bad_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_event_authority_resolution_memory_decay_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_event_authority_resolution_memory_decay_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_research_event_authority_resolution_memory_decay_public_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchEventAuthorityResolutionMemoryDecayReport",
    )


def research_event_authority_resolution_memory_decay_report_digest(
    report: ResearchEventAuthorityResolutionMemoryDecayReport,
) -> str:
    if type(report) is not ResearchEventAuthorityResolutionMemoryDecayReport:
        raise ValueError(
            "report must be a ResearchEventAuthorityResolutionMemoryDecayReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_event_authority_resolution_memory_decay_report_digest(
    report: ResearchEventAuthorityResolutionMemoryDecayReport,
) -> None:
    if type(report) is not ResearchEventAuthorityResolutionMemoryDecayReport:
        raise ValueError(
            "report must be a ResearchEventAuthorityResolutionMemoryDecayReport",
        )
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_event_authority_resolution_memory_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_bad_public_payload("public payload", payload)
    _reject_public_numerics("public payload", payload)
    _reject_flag_downgrades("public payload", payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_status_values_in_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_validation_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    value: object,
) -> tuple[ResearchEventAuthorityResolutionMemoryDecayInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventAuthorityResolutionMemoryDecayInput:
            raise ValueError(
                "inputs must contain ResearchEventAuthorityResolutionMemoryDecayInput",
            )
        _require_hard_flags("input", row)
        if row.event_digest in seen:
            raise ValueError("inputs must be unique by event_digest")
        seen.add(row.event_digest)
    return tuple(sorted(rows, key=lambda row: row.event_digest))


def _decay_rows(
    inputs: tuple[ResearchEventAuthorityResolutionMemoryDecayInput, ...],
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
    generated_at: datetime,
) -> tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...]:
    return tuple(
        sorted(
            (_decay_row(row, config=config, generated_at=generated_at) for row in inputs),
            key=_row_sort_key,
        ),
    )


def _decay_row(
    row: ResearchEventAuthorityResolutionMemoryDecayInput,
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchEventAuthorityResolutionMemoryDecayRow:
    observation_age_seconds = _duration_seconds(row.parsed_at, generated_at)
    if observation_age_seconds < ZERO:
        raise ValueError("parsed_at must not be after generated_at")
    reason_codes = _row_reason_codes(row, config=config)
    return ResearchEventAuthorityResolutionMemoryDecayRow(
        event_digest=row.event_digest,
        authority_digest=row.authority_digest,
        parsed_at=row.parsed_at,
        observation_age_seconds=observation_age_seconds,
        authority_reliability_score=row.authority_reliability_score,
        authority_reliability_band=_authority_reliability_band(row, config=config),
        resolution_age_seconds=row.resolution_age_seconds,
        resolution_freshness_band=_age_band(
            row.resolution_age_seconds,
            watch_seconds=config.resolution_age_watch_seconds,
            block_seconds=config.resolution_age_block_seconds,
        ),
        memory_age_seconds=row.memory_age_seconds,
        memory_decay_band=_age_band(
            row.memory_age_seconds,
            watch_seconds=config.memory_age_watch_seconds,
            block_seconds=config.memory_age_block_seconds,
        ),
        parser_confidence_score=row.parser_confidence_score,
        parser_confidence_band=_parser_confidence_band(row, config=config),
        evidence_count=row.evidence_count,
        evidence_quorum_band=_coverage_band(
            row.evidence_count,
            watch_count=config.evidence_quorum_watch_count,
        ),
        conflict_score=row.conflict_score,
        conflict_band=_conflict_band(row, config=config),
        authority_resolution_memory_decay_score=_authority_resolution_memory_decay_score(row),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchEventAuthorityResolutionMemoryDecayInput,
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authority_reliability_score < config.authority_reliability_block_below:
        reasons.append(AUTHORITY_RELIABILITY_BLOCK_REASON)
    elif row.authority_reliability_score < config.authority_reliability_watch_below:
        reasons.append(AUTHORITY_RELIABILITY_WATCH_REASON)
    if row.resolution_age_seconds >= config.resolution_age_block_seconds:
        reasons.append(RESOLUTION_AGE_BLOCK_REASON)
    elif row.resolution_age_seconds > config.resolution_age_watch_seconds:
        reasons.append(RESOLUTION_AGE_WATCH_REASON)
    if row.memory_age_seconds >= config.memory_age_block_seconds:
        reasons.append(MEMORY_AGE_BLOCK_REASON)
    elif row.memory_age_seconds > config.memory_age_watch_seconds:
        reasons.append(MEMORY_AGE_WATCH_REASON)
    if row.parser_confidence_score < config.parser_confidence_block_below:
        reasons.append(PARSER_CONFIDENCE_BLOCK_REASON)
    elif row.parser_confidence_score < config.parser_confidence_watch_below:
        reasons.append(PARSER_CONFIDENCE_WATCH_REASON)
    if row.evidence_count < ONE:
        reasons.append(EVIDENCE_QUORUM_BLOCK_REASON)
    elif row.evidence_count < config.evidence_quorum_watch_count:
        reasons.append(EVIDENCE_QUORUM_WATCH_REASON)
    if row.conflict_score >= config.conflict_block_threshold:
        reasons.append(CONFLICT_PRESSURE_BLOCK_REASON)
    elif row.conflict_score >= config.conflict_watch_threshold:
        reasons.append(CONFLICT_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _authority_resolution_memory_decay_score(
    row: ResearchEventAuthorityResolutionMemoryDecayInput
    | ResearchEventAuthorityResolutionMemoryDecayRow,
) -> Decimal:
    score = (
        (ONE - row.authority_reliability_score)
        + _age_decay(row.resolution_age_seconds, DEFAULT_RESOLUTION_SCORE_BLOCK_SECONDS)
        + _age_decay(row.memory_age_seconds, DEFAULT_MEMORY_SCORE_BLOCK_SECONDS)
        + (ONE - row.parser_confidence_score)
        + _coverage_decay(row.evidence_count)
        + row.conflict_score
    ) / SIX
    return min(max(score, ZERO), ONE).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _age_decay(value: Decimal, block_seconds: Decimal) -> Decimal:
    return min(value / block_seconds, ONE).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _coverage_decay(value: Decimal) -> Decimal:
    if value >= DEFAULT_EVIDENCE_SCORE_WATCH_COUNT:
        return ZERO
    return ((DEFAULT_EVIDENCE_SCORE_WATCH_COUNT - value) / TWO).quantize(
        QUANT,
        rounding=ROUND_HALF_EVEN,
    )


def _authority_reliability_band(
    row: ResearchEventAuthorityResolutionMemoryDecayInput,
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
) -> str:
    if row.authority_reliability_score < config.authority_reliability_block_below:
        return "weak"
    if row.authority_reliability_score < config.authority_reliability_watch_below:
        return "thin"
    return "trusted"


def _age_band(
    value: Decimal,
    *,
    watch_seconds: Decimal,
    block_seconds: Decimal,
) -> str:
    if value >= block_seconds:
        return "expired"
    if value > watch_seconds:
        return "stale"
    return "fresh"


def _parser_confidence_band(
    row: ResearchEventAuthorityResolutionMemoryDecayInput,
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
) -> str:
    if row.parser_confidence_score < config.parser_confidence_block_below:
        return "low"
    if row.parser_confidence_score < config.parser_confidence_watch_below:
        return "thin"
    return "strong"


def _coverage_band(value: Decimal, *, watch_count: Decimal) -> str:
    if value < ONE:
        return "missing"
    if value < watch_count:
        return "thin"
    return "covered"


def _conflict_band(
    row: ResearchEventAuthorityResolutionMemoryDecayInput,
    *,
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
) -> str:
    if row.conflict_score >= config.conflict_block_threshold:
        return "conflicted"
    if row.conflict_score >= config.conflict_watch_threshold:
        return "elevated"
    return "clear"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    }
    if not found:
        return (CLEAR_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _row_sort_key(
    row: ResearchEventAuthorityResolutionMemoryDecayRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.authority_resolution_memory_decay_score,
        -row.observation_age_seconds,
        row.event_digest,
    )


def _status_count(
    rows: tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventAuthorityResolutionMemoryDecayRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchEventAuthorityResolutionMemoryDecayRow:
            raise ValueError(
                "rows must contain ResearchEventAuthorityResolutionMemoryDecayRow",
            )
        _require_hard_flags("row", row)
    return rows


def _validate_config(
    config: ResearchEventAuthorityResolutionMemoryDecayConfig,
) -> None:
    if (
        config.authority_reliability_block_below
        >= config.authority_reliability_watch_below
    ):
        raise ValueError(
            "authority_reliability_block_below must be below "
            "authority_reliability_watch_below",
        )
    if config.resolution_age_block_seconds <= config.resolution_age_watch_seconds:
        raise ValueError(
            "resolution_age_block_seconds must exceed resolution_age_watch_seconds",
        )
    if config.memory_age_block_seconds <= config.memory_age_watch_seconds:
        raise ValueError("memory_age_block_seconds must exceed memory_age_watch_seconds")
    if config.parser_confidence_block_below >= config.parser_confidence_watch_below:
        raise ValueError(
            "parser_confidence_block_below must be below "
            "parser_confidence_watch_below",
        )
    if config.conflict_block_threshold <= config.conflict_watch_threshold:
        raise ValueError("conflict_block_threshold must exceed conflict_watch_threshold")


def _validate_row(row: ResearchEventAuthorityResolutionMemoryDecayRow) -> None:
    expected_score = _authority_resolution_memory_decay_score(row)
    if row.authority_resolution_memory_decay_score != expected_score:
        raise ValueError(
            "authority_resolution_memory_decay_score is inconsistent with row",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status is inconsistent with reason_codes")


def _validate_report(report: ResearchEventAuthorityResolutionMemoryDecayReport) -> None:
    rows = report.rows
    expected_values = {
        "event_count": _count(len(rows)),
        "pass_event_count": _status_count(rows, "pass"),
        "watch_event_count": _status_count(rows, "watch"),
        "block_event_count": _status_count(rows, "block"),
        "weak_authority_count": _reason_count(
            rows,
            (AUTHORITY_RELIABILITY_WATCH_REASON, AUTHORITY_RELIABILITY_BLOCK_REASON),
        ),
        "stale_resolution_count": _reason_count(
            rows,
            (RESOLUTION_AGE_WATCH_REASON, RESOLUTION_AGE_BLOCK_REASON),
        ),
        "decayed_memory_count": _reason_count(
            rows,
            (MEMORY_AGE_WATCH_REASON, MEMORY_AGE_BLOCK_REASON),
        ),
        "low_parser_confidence_count": _reason_count(
            rows,
            (PARSER_CONFIDENCE_WATCH_REASON, PARSER_CONFIDENCE_BLOCK_REASON),
        ),
        "thin_evidence_quorum_count": _reason_count(
            rows,
            (EVIDENCE_QUORUM_WATCH_REASON, EVIDENCE_QUORUM_BLOCK_REASON),
        ),
        "conflict_pressure_count": _reason_count(
            rows,
            (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
        ),
        "highest_authority_resolution_memory_decay_score": max(
            (row.authority_resolution_memory_decay_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "oldest_resolution_age_seconds": max(
            (row.resolution_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "oldest_memory_age_seconds": max(
            (row.memory_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sort")


def _report_digest_from_public_payload(
    report: ResearchEventAuthorityResolutionMemoryDecayReport,
) -> str:
    return _payload_validation_digest(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: ResearchEventAuthorityResolutionMemoryDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return f"{value:.6f}"
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(start: datetime, finish: datetime) -> Decimal:
    delta = _as_utc("finish", finish) - _as_utc("start", start)
    return (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(QUANT)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    ).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for flag in ("paper_only", "report_only", "readonly"):
            if flag in value and value[flag] is not True:
                raise ValueError(f"{flag} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_bad_public_part(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha-256 hex digest")
    return value


def _require_one_of(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES:
        raise ValueError(
            f"{field_name} must be one of "
            f"{RESEARCH_EVENT_AUTHORITY_RESOLUTION_MEMORY_DECAY_STATUSES}",
        )


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must have exactly six decimal places")
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _reject_bad_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        _reject_bad_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_bad_public_part(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_bad_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_bad_public_payload(label, item)
        return
    if type(value) is str and _has_bad_public_part(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_bad_public_part(value: str) -> bool:
    lowered = value.lower()
    return any(part in lowered for part in BAD_PUBLIC_PARTS)


def _reject_public_numerics(label: str, value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numerics(label, item)
    elif type(value) in (Decimal, int, float):
        raise ValueError(f"{label} numeric values must be Decimal-derived strings")


def _validate_status_values_in_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            else:
                _validate_status_values_in_payload(item)
    elif isinstance(value, list):
        for item in value:
            _validate_status_values_in_payload(item)
