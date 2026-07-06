"""Pure Phase 1 resolution-rule change watch report.

This module reduces caller-supplied in-memory observations into a read-only
paper report. It performs no IO, credential handling, external lookups, durable
storage, custody handling, execution handling, or state-changing work.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchPacketResolutionRuleChangeWatchV2Config",
    "ResearchPacketResolutionRuleChangeWatchV2Observation",
    "ResearchPacketResolutionRuleChangeWatchV2Report",
    "ResearchPacketResolutionRuleChangeWatchV2Row",
    "build_research_packet_resolution_rule_change_watch_v2",
    "research_packet_resolution_rule_change_watch_v2_payload",
)


_DEFAULT_CONFIG_VERSION = "research-packet-resolution-rule-change-watch-v2"
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_DECIMAL_CONTEXT = Context(prec=64)
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

_PASS_STATUS = "pass"
_WATCH_STATUS = "watch"
_BLOCKED_STATUS = "blocked"
_EMPTY_STATUS = "empty"
_REPORT_STATUSES = (_PASS_STATUS, _WATCH_STATUS, _BLOCKED_STATUS, _EMPTY_STATUS)
_ROW_STATUSES = (_PASS_STATUS, _WATCH_STATUS, _BLOCKED_STATUS)

_RULE_CHANGE_PASS_STATUS = "rule_change_pass"
_RULE_CHANGE_WATCH_STATUS = "rule_change_watch"
_RULE_CHANGE_BLOCKED_STATUS = "rule_change_blocked"
_RULE_CHANGE_STATUSES = (
    _RULE_CHANGE_PASS_STATUS,
    _RULE_CHANGE_WATCH_STATUS,
    _RULE_CHANGE_BLOCKED_STATUS,
)

_SOURCE_FRESHNESS_PASS_STATUS = "source_freshness_pass"
_SOURCE_FRESHNESS_WATCH_STATUS = "source_freshness_watch"
_SOURCE_FRESHNESS_BLOCKED_STATUS = "source_freshness_blocked"
_SOURCE_FRESHNESS_STATUSES = (
    _SOURCE_FRESHNESS_PASS_STATUS,
    _SOURCE_FRESHNESS_WATCH_STATUS,
    _SOURCE_FRESHNESS_BLOCKED_STATUS,
)

_AMBIGUITY_PASS_STATUS = "ambiguity_pass"
_AMBIGUITY_WATCH_STATUS = "ambiguity_watch"
_AMBIGUITY_STATUSES = (_AMBIGUITY_PASS_STATUS, _AMBIGUITY_WATCH_STATUS)

_SOURCE_RELIABILITY_PASS_STATUS = "source_reliability_pass"
_SOURCE_RELIABILITY_WATCH_STATUS = "source_reliability_watch"
_SOURCE_RELIABILITY_STATUSES = (
    _SOURCE_RELIABILITY_PASS_STATUS,
    _SOURCE_RELIABILITY_WATCH_STATUS,
)

_PASS_REASON = "resolution_rule_change_watch_v2_pass"
_EMPTY_REASON = "resolution_rule_change_watch_v2_empty"
_RULE_CHANGE_BLOCKED_REASON = "resolution_rule_change_blocked"
_RULE_CHANGE_WATCH_REASON = "resolution_rule_change_watch"
_SOURCE_FRESHNESS_BLOCKED_REASON = "source_freshness_blocked"
_SOURCE_FRESHNESS_WATCH_REASON = "source_freshness_watch"
_AMBIGUITY_WATCH_REASON = "resolution_rule_ambiguity_watch"
_SOURCE_RELIABILITY_WATCH_REASON = "source_reliability_watch"
_REASON_PRIORITY = (
    _RULE_CHANGE_BLOCKED_REASON,
    _SOURCE_FRESHNESS_BLOCKED_REASON,
    _RULE_CHANGE_WATCH_REASON,
    _SOURCE_FRESHNESS_WATCH_REASON,
    _AMBIGUITY_WATCH_REASON,
    _SOURCE_RELIABILITY_WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)

_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleChangeWatchV2Config:
    config_version: str = _DEFAULT_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    watch_source_age_seconds: Decimal = Decimal("1800.000000")
    rule_change_block_score: Decimal = Decimal("0.800000")
    rule_change_watch_score: Decimal = Decimal("0.300000")
    ambiguity_watch_score: Decimal = Decimal("0.250000")
    min_source_reliability_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_source_age_seconds",
            "watch_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_change_block_score",
            "rule_change_watch_score",
            "ambiguity_watch_score",
            "min_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_source_age_seconds > self.max_source_age_seconds:
            raise ValueError(
                "watch_source_age_seconds must not exceed max_source_age_seconds",
            )
        if self.rule_change_watch_score > self.rule_change_block_score:
            raise ValueError(
                "rule_change_watch_score must not exceed rule_change_block_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleChangeWatchV2Observation:
    packet_reference: str
    event_title: str
    source_label: str
    resolution_rule_text: str
    source_published_at: datetime
    source_checked_at: datetime
    rule_change_risk_score: Decimal
    ambiguity_score: Decimal
    source_reliability_score: Decimal
    rule_change_evidence_present: bool
    ambiguous_resolution_terms: bool
    conflicting_source_terms: bool
    public_evidence_fields: tuple[tuple[str, str], ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_reference",
            "event_title",
            "source_label",
            "resolution_rule_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_published_at",
            _as_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "source_checked_at",
            _as_utc("source_checked_at", self.source_checked_at),
        )
        if self.source_published_at > self.source_checked_at:
            raise ValueError("source_published_at must not be after source_checked_at")
        for field_name in (
            "rule_change_risk_score",
            "ambiguity_score",
            "source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_change_evidence_present",
            "ambiguous_resolution_terms",
            "conflicting_source_terms",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "public_evidence_fields",
            _normalize_public_evidence_fields(self.public_evidence_fields),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleChangeWatchV2Row:
    redacted_packet_reference: str
    event_title: str
    source_label: str
    source_published_at: datetime
    source_checked_at: datetime
    source_age_seconds: Decimal
    rule_change_risk_score: Decimal
    ambiguity_score: Decimal
    source_reliability_score: Decimal
    rule_change_status: str
    source_freshness_status: str
    ambiguity_status: str
    source_reliability_status: str
    watch_status: str
    rule_change_watch: bool
    source_freshness_watch: bool
    ambiguity_watch: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(self.redacted_packet_reference)
        for field_name in ("event_title", "source_label"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_published_at",
            _as_utc("source_published_at", self.source_published_at),
        )
        object.__setattr__(
            self,
            "source_checked_at",
            _as_utc("source_checked_at", self.source_checked_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in (
            "rule_change_risk_score",
            "ambiguity_score",
            "source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("rule_change_status", self.rule_change_status, _RULE_CHANGE_STATUSES)
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            _SOURCE_FRESHNESS_STATUSES,
        )
        _require_member("ambiguity_status", self.ambiguity_status, _AMBIGUITY_STATUSES)
        _require_member(
            "source_reliability_status",
            self.source_reliability_status,
            _SOURCE_RELIABILITY_STATUSES,
        )
        _require_member("watch_status", self.watch_status, _ROW_STATUSES)
        for field_name in (
            "rule_change_watch",
            "source_freshness_watch",
            "ambiguity_watch",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleChangeWatchV2Report:
    generated_at: datetime
    config_version: str
    status: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_source_age_seconds: Decimal
    max_rule_change_risk_score: Decimal
    max_ambiguity_score: Decimal
    min_source_reliability_score: Decimal
    rows: tuple[ResearchPacketResolutionRuleChangeWatchV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, _REPORT_STATUSES)
        for field_name in (
            "source_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_rule_change_risk_score",
            "max_ambiguity_score",
            "min_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_packet_resolution_rule_change_watch_v2(
    observations: Iterable[object],
    *,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionRuleChangeWatchV2Report:
    if type(config) is not ResearchPacketResolutionRuleChangeWatchV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionRuleChangeWatchV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )

    return ResearchPacketResolutionRuleChangeWatchV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        source_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, _PASS_STATUS),
        watch_count=_status_count(rows, _WATCH_STATUS),
        blocked_count=_status_count(rows, _BLOCKED_STATUS),
        max_source_age_seconds=_max_decimal(
            (row.source_age_seconds for row in rows),
            default=_ZERO,
        ),
        max_rule_change_risk_score=_max_decimal(
            (row.rule_change_risk_score for row in rows),
            default=_ZERO,
        ),
        max_ambiguity_score=_max_decimal(
            (row.ambiguity_score for row in rows),
            default=_ZERO,
        ),
        min_source_reliability_score=_min_decimal(
            (row.source_reliability_score for row in rows),
            default=_ONE,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_resolution_rule_change_watch_v2_payload(
    report: ResearchPacketResolutionRuleChangeWatchV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketResolutionRuleChangeWatchV2Report:
        raise ValueError(
            "report must be a ResearchPacketResolutionRuleChangeWatchV2Report",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    _reject_unsafe_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _row_from_observation(
    observation: ResearchPacketResolutionRuleChangeWatchV2Observation,
    *,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionRuleChangeWatchV2Row:
    _require_not_future("source_checked_at", observation.source_checked_at, generated_at)
    source_age_seconds = _seconds_between(generated_at, observation.source_checked_at)
    rule_change_status = _rule_change_status(observation, config)
    source_freshness_status = _source_freshness_status(source_age_seconds, config)
    ambiguity_status = _ambiguity_status(observation, config)
    source_reliability_status = _source_reliability_status(observation, config)
    reason_codes = _row_reason_codes(
        rule_change_status=rule_change_status,
        source_freshness_status=source_freshness_status,
        ambiguity_status=ambiguity_status,
        source_reliability_status=source_reliability_status,
    )
    return ResearchPacketResolutionRuleChangeWatchV2Row(
        redacted_packet_reference=_redacted_reference(observation.packet_reference),
        event_title=observation.event_title,
        source_label=observation.source_label,
        source_published_at=observation.source_published_at,
        source_checked_at=observation.source_checked_at,
        source_age_seconds=source_age_seconds,
        rule_change_risk_score=observation.rule_change_risk_score,
        ambiguity_score=observation.ambiguity_score,
        source_reliability_score=observation.source_reliability_score,
        rule_change_status=rule_change_status,
        source_freshness_status=source_freshness_status,
        ambiguity_status=ambiguity_status,
        source_reliability_status=source_reliability_status,
        watch_status=_row_watch_status(reason_codes),
        rule_change_watch=rule_change_status != _RULE_CHANGE_PASS_STATUS,
        source_freshness_watch=source_freshness_status != _SOURCE_FRESHNESS_PASS_STATUS,
        ambiguity_watch=ambiguity_status != _AMBIGUITY_PASS_STATUS,
        reason_codes=reason_codes,
    )


def _rule_change_status(
    observation: ResearchPacketResolutionRuleChangeWatchV2Observation,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
) -> str:
    if (
        observation.rule_change_evidence_present
        or observation.rule_change_risk_score >= config.rule_change_block_score
    ):
        return _RULE_CHANGE_BLOCKED_STATUS
    if observation.rule_change_risk_score >= config.rule_change_watch_score:
        return _RULE_CHANGE_WATCH_STATUS
    return _RULE_CHANGE_PASS_STATUS


def _source_freshness_status(
    source_age_seconds: Decimal,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
) -> str:
    if source_age_seconds > config.max_source_age_seconds:
        return _SOURCE_FRESHNESS_BLOCKED_STATUS
    if source_age_seconds > config.watch_source_age_seconds:
        return _SOURCE_FRESHNESS_WATCH_STATUS
    return _SOURCE_FRESHNESS_PASS_STATUS


def _ambiguity_status(
    observation: ResearchPacketResolutionRuleChangeWatchV2Observation,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
) -> str:
    if (
        observation.ambiguous_resolution_terms
        or observation.conflicting_source_terms
        or observation.ambiguity_score >= config.ambiguity_watch_score
    ):
        return _AMBIGUITY_WATCH_STATUS
    return _AMBIGUITY_PASS_STATUS


def _source_reliability_status(
    observation: ResearchPacketResolutionRuleChangeWatchV2Observation,
    config: ResearchPacketResolutionRuleChangeWatchV2Config,
) -> str:
    if observation.source_reliability_score < config.min_source_reliability_score:
        return _SOURCE_RELIABILITY_WATCH_STATUS
    return _SOURCE_RELIABILITY_PASS_STATUS


def _row_reason_codes(
    *,
    rule_change_status: str,
    source_freshness_status: str,
    ambiguity_status: str,
    source_reliability_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if rule_change_status == _RULE_CHANGE_BLOCKED_STATUS:
        reasons.append(_RULE_CHANGE_BLOCKED_REASON)
    if source_freshness_status == _SOURCE_FRESHNESS_BLOCKED_STATUS:
        reasons.append(_SOURCE_FRESHNESS_BLOCKED_REASON)
    if rule_change_status == _RULE_CHANGE_WATCH_STATUS:
        reasons.append(_RULE_CHANGE_WATCH_REASON)
    if source_freshness_status == _SOURCE_FRESHNESS_WATCH_STATUS:
        reasons.append(_SOURCE_FRESHNESS_WATCH_REASON)
    if ambiguity_status == _AMBIGUITY_WATCH_STATUS:
        reasons.append(_AMBIGUITY_WATCH_REASON)
    if source_reliability_status == _SOURCE_RELIABILITY_WATCH_STATUS:
        reasons.append(_SOURCE_RELIABILITY_WATCH_REASON)
    if not reasons:
        reasons.append(_PASS_REASON)
    return tuple(reasons)


def _row_watch_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (_PASS_REASON,):
        return _PASS_STATUS
    if (
        _RULE_CHANGE_BLOCKED_REASON in reason_codes
        or _SOURCE_FRESHNESS_BLOCKED_REASON in reason_codes
    ):
        return _BLOCKED_STATUS
    return _WATCH_STATUS


def _report_status(
    rows: tuple[ResearchPacketResolutionRuleChangeWatchV2Row, ...],
) -> str:
    if not rows:
        return _EMPTY_STATUS
    if any(row.watch_status == _BLOCKED_STATUS for row in rows):
        return _BLOCKED_STATUS
    if any(row.watch_status == _WATCH_STATUS for row in rows):
        return _WATCH_STATUS
    return _PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionRuleChangeWatchV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(reason for reason in _REASON_PRIORITY if reason in observed)


def _validate_row(row: ResearchPacketResolutionRuleChangeWatchV2Row) -> None:
    expected_reasons = _row_reason_codes(
        rule_change_status=row.rule_change_status,
        source_freshness_status=row.source_freshness_status,
        ambiguity_status=row.ambiguity_status,
        source_reliability_status=row.source_reliability_status,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row statuses")
    if row.watch_status != _row_watch_status(row.reason_codes):
        raise ValueError("watch_status must match reason_codes")
    if row.rule_change_watch != (row.rule_change_status != _RULE_CHANGE_PASS_STATUS):
        raise ValueError("rule_change_watch must match rule_change_status")
    if row.source_freshness_watch != (
        row.source_freshness_status != _SOURCE_FRESHNESS_PASS_STATUS
    ):
        raise ValueError("source_freshness_watch must match source_freshness_status")
    if row.ambiguity_watch != (row.ambiguity_status != _AMBIGUITY_PASS_STATUS):
        raise ValueError("ambiguity_watch must match ambiguity_status")


def _validate_report(report: ResearchPacketResolutionRuleChangeWatchV2Report) -> None:
    if report.source_count != _count_decimal(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _status_count(report.rows, _PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, _WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, _BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.max_source_age_seconds != _max_decimal(
        (row.source_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_rule_change_risk_score != _max_decimal(
        (row.rule_change_risk_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_rule_change_risk_score must match rows")
    if report.max_ambiguity_score != _max_decimal(
        (row.ambiguity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_ambiguity_score must match rows")
    if report.min_source_reliability_score != _min_decimal(
        (row.source_reliability_score for row in report.rows),
        default=_ONE,
    ):
        raise ValueError("min_source_reliability_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchPacketResolutionRuleChangeWatchV2Observation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in normalized:
        if type(observation) is not ResearchPacketResolutionRuleChangeWatchV2Observation:
            raise ValueError(
                "observations must contain "
                "ResearchPacketResolutionRuleChangeWatchV2Observation",
            )
        _require_hard_flags("observation", observation)
        _reject_unsafe_public_payload("observation", observation)
    references = tuple(observation.packet_reference for observation in normalized)
    if len(references) != len(set(references)):
        raise ValueError("packet_reference values must be unique")
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionRuleChangeWatchV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketResolutionRuleChangeWatchV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionRuleChangeWatchV2Row",
            )
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    references = tuple(row.redacted_packet_reference for row in normalized)
    if len(references) != len(set(references)):
        raise ValueError("redacted_packet_reference values must be unique")
    return normalized


def _row_sort_key(
    row: ResearchPacketResolutionRuleChangeWatchV2Row,
) -> tuple[int, Decimal, Decimal, str]:
    priority = {_BLOCKED_STATUS: 0, _WATCH_STATUS: 1, _PASS_STATUS: 2}
    return (
        priority[row.watch_status],
        -row.rule_change_risk_score,
        -row.source_age_seconds,
        row.redacted_packet_reference,
    )


def _status_count(
    rows: tuple[ResearchPacketResolutionRuleChangeWatchV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.watch_status == status for row in rows))


def _normalize_public_evidence_fields(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("public_evidence_fields must be a tuple or list")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("public_evidence_fields must contain key/value pairs")
        key, field_value = item
        _require_canonical_string("public_evidence_fields key", key)
        _require_canonical_string("public_evidence_fields value", field_value)
        _reject_unsafe_public_text("public_evidence_fields key", key)
        _reject_unsafe_public_text("public_evidence_fields value", field_value)
        pairs.append((key, field_value))
    keys = tuple(key for key, _field_value in pairs)
    if len(keys) != len(set(keys)):
        raise ValueError("public_evidence_fields keys must be unique")
    return tuple(sorted(pairs))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for key, item in asdict(value).items():
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key)
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key)
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal public numeric values")
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public text")
    if "://" in lowered:
        raise ValueError(f"{field_name} contains unsafe public text")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _seconds_between(generated_at: datetime, source_checked_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - source_checked_at).total_seconds()))
    if seconds < _ZERO:
        raise ValueError("source_age_seconds must be nonnegative")
    return _normalize_nonnegative_decimal("source_age_seconds", seconds)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_redacted_reference(value: str) -> None:
    prefix = "packet_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 12
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_packet_reference must be a packet_ref digest")


def _redacted_reference(value: str) -> str:
    return f"packet_ref_{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _normalize_reason_codes(value: object, *, require_nonempty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    known_reasons = set(_REASON_PRIORITY)
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code not in known_reasons:
            raise ValueError("reason_codes must contain known reason codes")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < _QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default.quantize(_QUANT)
    return max(normalized).quantize(_QUANT)


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default.quantize(_QUANT)
    return min(normalized).quantize(_QUANT)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchPacketResolutionRuleChangeWatchV2Report,
) -> str:
    payload = _report_payload(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    raise ValueError("value is not JSON serializable")


def _report_payload(
    report: ResearchPacketResolutionRuleChangeWatchV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    return payload
