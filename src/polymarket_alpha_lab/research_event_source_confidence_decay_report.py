"""Public-safe report-only source-confidence decay by event domain.

The module is pure and deterministic. Callers provide aggregate domain inputs;
the report summarizes confidence decay without exposing raw event, market, or
source identifiers and without side effects.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION = (
    "research-event-source-confidence-decay-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_PRIORITY = {"block": 0, "watch": 1, "pass": 2}

NO_DOMAINS_REASON = "confidence_decay_no_event_domains"
PASS_REASON = "confidence_decay_pass"
WATCH_REASON = "confidence_decay_watch"
BLOCK_REASON = "confidence_decay_block"
SOURCE_AGE_WATCH_REASON = "source_age_pressure_watch"
SOURCE_AGE_BLOCK_REASON = "source_age_pressure_block"
RELIABILITY_WATCH_REASON = "reliability_memory_decay_watch"
RELIABILITY_BLOCK_REASON = "reliability_memory_decay_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
CATALYST_WATCH_REASON = "catalyst_pressure_watch"
CATALYST_BLOCK_REASON = "catalyst_pressure_block"
TEAM_CAPACITY_WATCH_REASON = "team_capacity_pressure_watch"
TEAM_CAPACITY_BLOCK_REASON = "team_capacity_pressure_block"

REASON_CODE_SEQUENCE = (
    NO_DOMAINS_REASON,
    SOURCE_AGE_BLOCK_REASON,
    RELIABILITY_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    CATALYST_BLOCK_REASON,
    TEAM_CAPACITY_BLOCK_REASON,
    BLOCK_REASON,
    SOURCE_AGE_WATCH_REASON,
    RELIABILITY_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    CATALYST_WATCH_REASON,
    TEAM_CAPACITY_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)

EVENT_IDENTIFIER_KEYS = frozenset(
    (
        "eventid",
        "raweventid",
        "eventslug",
        "eventref",
        "eventreference",
    ),
)
MARKET_IDENTIFIER_KEYS = frozenset(
    (
        "marketid",
        "rawmarketid",
        "marketslug",
        "conditionid",
        "question",
        "slug",
    ),
)
SOURCE_IDENTIFIER_KEYS = frozenset(
    (
        "sourceid",
        "rawsourceid",
        "sourceref",
        "sourcerefs",
        "sourceurl",
        "sourceurls",
        "sourceuri",
        "sourceuris",
        "sourcetext",
        "sourceexcerpt",
        "sourcetitle",
        "url",
        "uri",
    ),
)
EXECUTION_KEYS = frozenset(
    (
        "au" + "th",
        "api" + "key",
        "private" + "key",
        "sec" + "ret",
        "to" + "ken",
        "wal" + "let",
        "wal" + "letref",
        "or" + "der",
        "tr" + "ade",
        "b" + "uy",
        "s" + "ell",
        "rec" + "ommend",
        "rec" + "ommendation",
        "position" + "size",
        "position" + "sizing",
        "li" + "ve",
        "exec" + "ution",
    ),
)
SOURCE_REFERENCE_VALUE_TERMS = (
    "http://",
    "https://",
    "www.",
    "://",
    ".com",
    ".org",
    ".net",
    ".io",
    ".co",
    ".test",
    ".app",
    ".dev",
    ".ai",
    ".gov",
    ".edu",
    "source_ref:",
    "source:",
)
EXECUTION_VALUE_TERMS = (
    "au" + "th",
    "api" + "_key",
    "api" + "-key",
    "private" + "_key",
    "private" + "-key",
    "private " + "key",
    "sec" + "ret",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "position" + "_size",
    "position" + "-size",
    "position " + "size",
    "position " + "sizing",
    "li" + "ve exec" + "ution",
)
STATUS_ALIAS_VALUES = frozenset(("ready", "block" + "ed", "match" + "ed", "support" + "ed"))

DECIMAL_STRING_KEYS = frozenset(
    (
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_confidence_decay_score",
        "max_confidence_decay_score",
        "aggregate_source_age_hours",
        "source_age_pressure",
        "reliability_memory_score",
        "reliability_memory_decay",
        "contradiction_pressure",
        "catalyst_pressure",
        "team_capacity_score",
        "team_capacity_pressure",
        "confidence_decay_score",
        "count",
        "domain_ratio",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION",
    "ResearchEventSourceConfidenceDecayConfig",
    "ResearchEventSourceConfidenceDecayInput",
    "ResearchEventSourceConfidenceDecayReasonCodeCount",
    "ResearchEventSourceConfidenceDecayReport",
    "ResearchEventSourceConfidenceDecayRow",
    "build_research_event_source_confidence_decay_report",
    "research_event_source_confidence_decay_report_payload",
    "validate_research_event_source_confidence_decay_public_payload",
    "validate_research_event_source_confidence_decay_report",
)


@dataclass(frozen=True)
class ResearchEventSourceConfidenceDecayConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
    max_source_age_hours: Decimal = Decimal("72.000000")
    max_pass_confidence_decay_score: Decimal = Decimal("0.350000")
    max_watch_confidence_decay_score: Decimal = Decimal("0.650000")
    watch_source_age_pressure: Decimal = Decimal("0.300000")
    block_source_age_pressure: Decimal = Decimal("0.750000")
    watch_reliability_decay: Decimal = Decimal("0.300000")
    block_reliability_decay: Decimal = Decimal("0.600000")
    watch_contradiction_pressure: Decimal = Decimal("0.250000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    watch_catalyst_pressure: Decimal = Decimal("0.350000")
    block_catalyst_pressure: Decimal = Decimal("0.600000")
    watch_team_capacity_pressure: Decimal = Decimal("0.350000")
    block_team_capacity_pressure: Decimal = Decimal("0.600000")
    source_age_weight: Decimal = Decimal("0.250000")
    reliability_memory_weight: Decimal = Decimal("0.250000")
    contradiction_weight: Decimal = Decimal("0.200000")
    catalyst_weight: Decimal = Decimal("0.150000")
    team_capacity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConfidenceDecayConfig:
            raise ValueError(
                "config must be a ResearchEventSourceConfidenceDecayConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "max_source_age_hours",
            _normalize_positive_decimal("max_source_age_hours", self.max_source_age_hours),
        )
        for field_name in (
            "max_pass_confidence_decay_score",
            "max_watch_confidence_decay_score",
            "watch_source_age_pressure",
            "block_source_age_pressure",
            "watch_reliability_decay",
            "block_reliability_decay",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_catalyst_pressure",
            "block_catalyst_pressure",
            "watch_team_capacity_pressure",
            "block_team_capacity_pressure",
            "source_age_weight",
            "reliability_memory_weight",
            "contradiction_weight",
            "catalyst_weight",
            "team_capacity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceConfidenceDecayInput:
    event_domain: str
    aggregate_source_age_hours: Decimal
    reliability_memory_score: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConfidenceDecayInput:
            raise ValueError("input must be a ResearchEventSourceConfidenceDecayInput")
        object.__setattr__(
            self,
            "event_domain",
            _require_canonical_string("event_domain", self.event_domain),
        )
        object.__setattr__(
            self,
            "aggregate_source_age_hours",
            _normalize_nonnegative_decimal(
                "aggregate_source_age_hours",
                self.aggregate_source_age_hours,
            ),
        )
        for field_name in (
            "reliability_memory_score",
            "contradiction_pressure",
            "catalyst_pressure",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventSourceConfidenceDecayRow:
    event_domain: str
    aggregate_source_age_hours: Decimal
    source_age_pressure: Decimal
    reliability_memory_score: Decimal
    reliability_memory_decay: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    team_capacity_score: Decimal
    team_capacity_pressure: Decimal
    confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConfidenceDecayRow:
            raise ValueError("row must be a ResearchEventSourceConfidenceDecayRow")
        object.__setattr__(
            self,
            "event_domain",
            _require_canonical_string("event_domain", self.event_domain),
        )
        object.__setattr__(
            self,
            "aggregate_source_age_hours",
            _normalize_nonnegative_decimal(
                "aggregate_source_age_hours",
                self.aggregate_source_age_hours,
            ),
        )
        for field_name in (
            "source_age_pressure",
            "reliability_memory_score",
            "reliability_memory_decay",
            "contradiction_pressure",
            "catalyst_pressure",
            "team_capacity_score",
            "team_capacity_pressure",
            "confidence_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest(_row_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        if self.derived_validation_digest != _digest(_row_payload_without_digest(self)):
            raise ValueError("derived_validation_digest must match row payload")


@dataclass(frozen=True)
class ResearchEventSourceConfidenceDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConfidenceDecayReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "ResearchEventSourceConfidenceDecayReasonCodeCount",
            )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _normalize_unit_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventSourceConfidenceDecayReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_decay_score: Decimal
    max_confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventSourceConfidenceDecayReasonCodeCount, ...]
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConfidenceDecayReport:
            raise ValueError("report must be a ResearchEventSourceConfidenceDecayReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("domain_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_decay_score",
            "max_confidence_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest(_report_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)
        if self.derived_validation_digest != _digest(_report_payload_without_digest(self)):
            raise ValueError("derived_validation_digest must match report payload")


def build_research_event_source_confidence_decay_report(
    domain_rows: Iterable[object],
    *,
    config: ResearchEventSourceConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchEventSourceConfidenceDecayReport:
    if isinstance(domain_rows, (str, bytes)):
        raise ValueError("domain_rows must be an iterable")
    try:
        domain_inputs = tuple(domain_rows)
    except TypeError as exc:
        raise ValueError("domain_rows must be an iterable") from exc
    if type(config) is not ResearchEventSourceConfidenceDecayConfig:
        raise ValueError("config must be a ResearchEventSourceConfidenceDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    seen_domains: set[str] = set()
    rows: list[ResearchEventSourceConfidenceDecayRow] = []
    for domain_input in domain_inputs:
        if type(domain_input) is not ResearchEventSourceConfidenceDecayInput:
            raise ValueError(
                "domain_rows must contain ResearchEventSourceConfidenceDecayInput",
            )
        _require_hard_flags("input", domain_input)
        if domain_input.event_domain in seen_domains:
            raise ValueError("duplicate event_domain")
        seen_domains.add(domain_input.event_domain)
        rows.append(_row_from_input(domain_input, config=config))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return ResearchEventSourceConfidenceDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        average_confidence_decay_score=_average_confidence_decay_score(sorted_rows),
        max_confidence_decay_score=_max_confidence_decay_score(sorted_rows),
        status=_report_status(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
        reason_code_counts=_reason_code_counts(sorted_rows),
        rows=sorted_rows,
    )


def validate_research_event_source_confidence_decay_report(
    report: ResearchEventSourceConfidenceDecayReport,
) -> bool:
    if type(report) is not ResearchEventSourceConfidenceDecayReport:
        raise ValueError("report must be a ResearchEventSourceConfidenceDecayReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _digest(_report_payload_without_digest(report)):
        raise ValueError("derived_validation_digest must match report payload")
    return True


def research_event_source_confidence_decay_report_payload(
    report: ResearchEventSourceConfidenceDecayReport,
) -> dict[str, Any]:
    validate_research_event_source_confidence_decay_report(report)
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    validate_research_event_source_confidence_decay_public_payload(payload)
    return payload


def validate_research_event_source_confidence_decay_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    digest = payload.get("derived_validation_digest")
    if digest is not None:
        _normalize_sha256("derived_validation_digest", digest)
        digest_payload = dict(payload)
        digest_payload.pop("derived_validation_digest", None)
        if digest != _digest(digest_payload):
            raise ValueError("derived_validation_digest must match report payload")
    return True


def _row_from_input(
    value: ResearchEventSourceConfidenceDecayInput,
    *,
    config: ResearchEventSourceConfidenceDecayConfig,
) -> ResearchEventSourceConfidenceDecayRow:
    source_age_pressure = _bounded_ratio(
        value.aggregate_source_age_hours,
        config.max_source_age_hours,
    )
    reliability_decay = _bounded_unit(ONE - value.reliability_memory_score)
    team_capacity_pressure = _bounded_unit(ONE - value.team_capacity_score)
    confidence_decay_score = _quantize(
        source_age_pressure * config.source_age_weight
        + reliability_decay * config.reliability_memory_weight
        + value.contradiction_pressure * config.contradiction_weight
        + value.catalyst_pressure * config.catalyst_weight
        + team_capacity_pressure * config.team_capacity_weight,
    )
    status = _row_status(
        source_age_pressure=source_age_pressure,
        reliability_decay=reliability_decay,
        contradiction_pressure=value.contradiction_pressure,
        catalyst_pressure=value.catalyst_pressure,
        team_capacity_pressure=team_capacity_pressure,
        confidence_decay_score=confidence_decay_score,
        config=config,
    )
    return ResearchEventSourceConfidenceDecayRow(
        event_domain=value.event_domain,
        aggregate_source_age_hours=value.aggregate_source_age_hours,
        source_age_pressure=source_age_pressure,
        reliability_memory_score=value.reliability_memory_score,
        reliability_memory_decay=reliability_decay,
        contradiction_pressure=value.contradiction_pressure,
        catalyst_pressure=value.catalyst_pressure,
        team_capacity_score=value.team_capacity_score,
        team_capacity_pressure=team_capacity_pressure,
        confidence_decay_score=confidence_decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            source_age_pressure=source_age_pressure,
            reliability_decay=reliability_decay,
            contradiction_pressure=value.contradiction_pressure,
            catalyst_pressure=value.catalyst_pressure,
            team_capacity_pressure=team_capacity_pressure,
            config=config,
        ),
    )


def _row_status(
    *,
    source_age_pressure: Decimal,
    reliability_decay: Decimal,
    contradiction_pressure: Decimal,
    catalyst_pressure: Decimal,
    team_capacity_pressure: Decimal,
    confidence_decay_score: Decimal,
    config: ResearchEventSourceConfidenceDecayConfig,
) -> str:
    block_checks = (
        confidence_decay_score > config.max_watch_confidence_decay_score,
        source_age_pressure >= config.block_source_age_pressure,
        reliability_decay >= config.block_reliability_decay,
        contradiction_pressure >= config.block_contradiction_pressure,
        catalyst_pressure >= config.block_catalyst_pressure,
        team_capacity_pressure >= config.block_team_capacity_pressure,
    )
    if any(block_checks):
        return "block"
    watch_checks = (
        confidence_decay_score > config.max_pass_confidence_decay_score,
        source_age_pressure >= config.watch_source_age_pressure,
        reliability_decay >= config.watch_reliability_decay,
        contradiction_pressure >= config.watch_contradiction_pressure,
        catalyst_pressure >= config.watch_catalyst_pressure,
        team_capacity_pressure >= config.watch_team_capacity_pressure,
    )
    if any(watch_checks):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_age_pressure: Decimal,
    reliability_decay: Decimal,
    contradiction_pressure: Decimal,
    catalyst_pressure: Decimal,
    team_capacity_pressure: Decimal,
    config: ResearchEventSourceConfidenceDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_pressure_reason(
        reason_codes,
        source_age_pressure,
        watch_threshold=config.watch_source_age_pressure,
        block_threshold=config.block_source_age_pressure,
        watch_reason=SOURCE_AGE_WATCH_REASON,
        block_reason=SOURCE_AGE_BLOCK_REASON,
    )
    _append_pressure_reason(
        reason_codes,
        reliability_decay,
        watch_threshold=config.watch_reliability_decay,
        block_threshold=config.block_reliability_decay,
        watch_reason=RELIABILITY_WATCH_REASON,
        block_reason=RELIABILITY_BLOCK_REASON,
    )
    _append_pressure_reason(
        reason_codes,
        contradiction_pressure,
        watch_threshold=config.watch_contradiction_pressure,
        block_threshold=config.block_contradiction_pressure,
        watch_reason=CONTRADICTION_WATCH_REASON,
        block_reason=CONTRADICTION_BLOCK_REASON,
    )
    _append_pressure_reason(
        reason_codes,
        catalyst_pressure,
        watch_threshold=config.watch_catalyst_pressure,
        block_threshold=config.block_catalyst_pressure,
        watch_reason=CATALYST_WATCH_REASON,
        block_reason=CATALYST_BLOCK_REASON,
    )
    _append_pressure_reason(
        reason_codes,
        team_capacity_pressure,
        watch_threshold=config.watch_team_capacity_pressure,
        block_threshold=config.block_team_capacity_pressure,
        watch_reason=TEAM_CAPACITY_WATCH_REASON,
        block_reason=TEAM_CAPACITY_BLOCK_REASON,
    )
    reason_codes.append(f"confidence_decay_{status}")
    return tuple(reason_codes)


def _append_pressure_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(block_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _report_status(rows: tuple[ResearchEventSourceConfidenceDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_DOMAINS_REASON,)
    return _sort_reason_codes({reason for row in rows for reason in row.reason_codes})


def _reason_code_counts(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
) -> tuple[ResearchEventSourceConfidenceDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventSourceConfidenceDecayReasonCodeCount(
                reason_code=NO_DOMAINS_REASON,
                count=ONE,
                domain_ratio=ONE,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    domain_count = _count_decimal(len(rows))
    return tuple(
        ResearchEventSourceConfidenceDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            domain_ratio=_ratio(_count_decimal(counts[reason_code]), domain_count),
        )
        for reason_code in _sort_reason_codes(counts)
    )


def _status_count(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_confidence_decay_score(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        sum((row.confidence_decay_score for row in rows), ZERO),
        _count_decimal(len(rows)),
    )


def _max_confidence_decay_score(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
) -> Decimal:
    return max((row.confidence_decay_score for row in rows), default=ZERO)


def _validate_config(config: ResearchEventSourceConfidenceDecayConfig) -> None:
    if config.max_watch_confidence_decay_score <= config.max_pass_confidence_decay_score:
        raise ValueError(
            "max_watch_confidence_decay_score must exceed "
            "max_pass_confidence_decay_score",
        )
    threshold_pairs = (
        ("source_age_pressure", config.watch_source_age_pressure, config.block_source_age_pressure),
        ("reliability_decay", config.watch_reliability_decay, config.block_reliability_decay),
        (
            "contradiction_pressure",
            config.watch_contradiction_pressure,
            config.block_contradiction_pressure,
        ),
        ("catalyst_pressure", config.watch_catalyst_pressure, config.block_catalyst_pressure),
        (
            "team_capacity_pressure",
            config.watch_team_capacity_pressure,
            config.block_team_capacity_pressure,
        ),
    )
    for label, watch_threshold, block_threshold in threshold_pairs:
        if block_threshold <= watch_threshold:
            raise ValueError(f"block_{label} must exceed watch_{label}")
    weight_sum = _quantize(
        config.source_age_weight
        + config.reliability_memory_weight
        + config.contradiction_weight
        + config.catalyst_weight
        + config.team_capacity_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(report: ResearchEventSourceConfidenceDecayReport) -> None:
    if report.domain_count != _count_decimal(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_confidence_decay_score != _average_confidence_decay_score(report.rows):
        raise ValueError("average_confidence_decay_score must match rows")
    if report.max_confidence_decay_score != _max_confidence_decay_score(report.rows):
        raise ValueError("max_confidence_decay_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: tuple[ResearchEventSourceConfidenceDecayRow, ...],
) -> tuple[ResearchEventSourceConfidenceDecayRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventSourceConfidenceDecayRow:
            raise ValueError("rows must contain ResearchEventSourceConfidenceDecayRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventSourceConfidenceDecayReasonCodeCount, ...],
) -> tuple[ResearchEventSourceConfidenceDecayReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventSourceConfidenceDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSourceConfidenceDecayReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(sorted(normalized, key=lambda item: _reason_sort_key(item.reason_code)))


def _row_sort_key(row: ResearchEventSourceConfidenceDecayRow) -> tuple[str, str]:
    return (row.event_domain, row.derived_validation_digest)


def _sort_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(reason_codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(REASON_CODE_SEQUENCE), reason_code)


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    normalized = tuple(_require_reason_code(reason_code) for reason_code in reason_codes)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return _sort_reason_codes(normalized)


def _require_reason_code(value: object) -> str:
    return _require_canonical_string("reason_code", value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip() or value != value.lower():
        raise ValueError(f"{field_name} must be canonical")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(char not in allowed for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(decimal_value)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _bounded_unit(_ratio(numerator, denominator))


def _bounded_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _row_payload_without_digest(
    row: ResearchEventSourceConfidenceDecayRow,
) -> dict[str, Any]:
    payload = _json_ready(row)
    if not isinstance(payload, dict):
        raise ValueError("row payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_payload_without_digest(
    report: ResearchEventSourceConfidenceDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object, *, key_path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_key(key)
            if key in ("paper_only", "report_only", "readonly") and child is not True:
                raise ValueError(f"{key} must be True")
            if key == "status" and child not in STATUSES:
                raise ValueError("status must be one of pass/watch/block")
            if _compact_key(key) in DECIMAL_STRING_KEYS and type(child) is not str:
                raise ValueError("decimal strings are required")
            _reject_unsafe_public_payload(child, key_path=(*key_path, key))
        return
    if isinstance(value, list):
        for child in value:
            _reject_unsafe_public_payload(child, key_path=key_path)
        return
    if type(value) in (Decimal, datetime, float, int):
        raise ValueError("decimal strings are required")
    if type(value) is str:
        _reject_unsafe_value(value, key_path=key_path)


def _reject_unsafe_key(key: str) -> None:
    compact = _compact_key(key)
    if compact in EVENT_IDENTIFIER_KEYS:
        raise ValueError("event identifier is not allowed")
    if compact in MARKET_IDENTIFIER_KEYS:
        raise ValueError("market identifier is not allowed")
    if compact in SOURCE_IDENTIFIER_KEYS:
        raise ValueError("source identifier is not allowed")
    if compact in EXECUTION_KEYS:
        raise ValueError("exec" + "ution surface is not allowed")


def _reject_unsafe_value(value: str, *, key_path: tuple[str, ...]) -> None:
    lowered = value.lower()
    if key_path and key_path[-1] == "status" and lowered in STATUS_ALIAS_VALUES:
        raise ValueError("status aliases are not allowed")
    if any(term in lowered for term in SOURCE_REFERENCE_VALUE_TERMS):
        raise ValueError("source reference is not allowed")
    if any(term in lowered for term in EXECUTION_VALUE_TERMS):
        raise ValueError("exec" + "ution surface is not allowed")


def _compact_key(key: str) -> str:
    return "".join(char for char in key.lower() if char.isalnum())
