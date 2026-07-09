"""Pure report-only source memory conflict reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION = (
    "research-event-resolution-source-memory-conflict-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400.000000")
SECONDS_PER_WEEK = Decimal("604800.000000")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_STRING_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,127}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUS_INDEX = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("sou", "rce", "_", "u", "rl"),
    _join_parts("sou", "rce", "-", "u", "rl"),
    _join_parts("sou", "rce", " ", "u", "rl"),
    _join_parts("sou", "rce", ".", "u", "rl"),
    _join_parts("sou", "rce", "_", "tex", "t"),
    _join_parts("sou", "rce", "-", "tex", "t"),
    _join_parts("sou", "rce", " ", "tex", "t"),
    _join_parts("sou", "rce", ".", "tex", "t"),
    _join_parts(":", "/", "/"),
    _join_parts("w", "w", "w", "."),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("exec", "ute"),
    _join_parts("exec", "ution"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
    _join_parts("post", "gres"),
)

_ROW_REASON_CODE_SEQUENCE = (
    "conflict_ratio_block",
    "conflict_ratio_watch",
    "signal_alignment_block",
    "signal_alignment_watch",
    "memory_consistency_block",
    "memory_consistency_watch",
    "rule_match_block",
    "rule_match_watch",
    "current_evidence_stale_block",
    "current_evidence_stale_watch",
    "memory_recency_stale_block",
    "memory_recency_stale_watch",
    "resolution_source_memory_conflict_pass",
)
_REASON_CODE_SEQUENCE = (
    "empty_source_memory_conflict_set",
    *_ROW_REASON_CODE_SEQUENCE,
)
_BLOCK_REASONS = frozenset(
    (
        "conflict_ratio_block",
        "signal_alignment_block",
        "memory_consistency_block",
        "rule_match_block",
        "current_evidence_stale_block",
        "memory_recency_stale_block",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION",
    "EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_STATUSES",
    "ResearchEventResolutionSourceMemoryConflictConfig",
    "ResearchEventResolutionSourceMemoryConflictObservation",
    "ResearchEventResolutionSourceMemoryConflictPublicPayloadItem",
    "ResearchEventResolutionSourceMemoryConflictReasonCodeCount",
    "ResearchEventResolutionSourceMemoryConflictReport",
    "ResearchEventResolutionSourceMemoryConflictRow",
    "build_research_event_resolution_source_memory_conflict_report",
    "research_event_resolution_source_memory_conflict_report_digest",
    "research_event_resolution_source_memory_conflict_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
    )
    max_pass_conflict_ratio: Decimal = Decimal("0.100000")
    max_watch_conflict_ratio: Decimal = Decimal("0.250000")
    min_pass_signal_alignment_score: Decimal = Decimal("0.850000")
    min_watch_signal_alignment_score: Decimal = Decimal("0.750000")
    min_pass_memory_consistency_score: Decimal = Decimal("0.800000")
    min_watch_memory_consistency_score: Decimal = Decimal("0.700000")
    min_pass_rule_match_score: Decimal = Decimal("0.850000")
    min_watch_rule_match_score: Decimal = Decimal("0.700000")
    max_current_evidence_age_seconds: Decimal = SECONDS_PER_DAY
    max_memory_age_seconds: Decimal = SECONDS_PER_WEEK
    conflict_clear_weight: Decimal = Decimal("0.196670")
    signal_alignment_weight: Decimal = Decimal("0.550000")
    memory_consistency_weight: Decimal = Decimal("0.050000")
    rule_match_weight: Decimal = Decimal("0.104162")
    current_freshness_weight: Decimal = Decimal("0.050000")
    memory_recency_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictConfig:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceMemoryConflictConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "max_pass_conflict_ratio",
            "max_watch_conflict_ratio",
            "min_pass_signal_alignment_score",
            "min_watch_signal_alignment_score",
            "min_pass_memory_consistency_score",
            "min_watch_memory_consistency_score",
            "min_pass_rule_match_score",
            "min_watch_rule_match_score",
            "conflict_clear_weight",
            "signal_alignment_weight",
            "memory_consistency_weight",
            "rule_match_weight",
            "current_freshness_weight",
            "memory_recency_weight",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        for name in ("max_current_evidence_age_seconds", "max_memory_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        if self.max_pass_conflict_ratio > self.max_watch_conflict_ratio:
            raise ValueError("max_pass_conflict_ratio must not exceed watch")
        if self.min_watch_signal_alignment_score > self.min_pass_signal_alignment_score:
            raise ValueError("min_watch_signal_alignment_score must not exceed pass")
        if self.min_watch_memory_consistency_score > self.min_pass_memory_consistency_score:
            raise ValueError("min_watch_memory_consistency_score must not exceed pass")
        if self.min_watch_rule_match_score > self.min_pass_rule_match_score:
            raise ValueError("min_watch_rule_match_score must not exceed pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictObservation:
    event_digest: str
    source_family_digest: str
    memory_snapshot_digest: str
    observed_at: datetime
    source_claim_count: Decimal
    conflicting_memory_count: Decimal
    corroborating_memory_count: Decimal
    newest_memory_age_seconds: Decimal
    current_evidence_age_seconds: Decimal
    signal_alignment_score: Decimal
    memory_consistency_score: Decimal
    resolution_rule_match_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictObservation:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceMemoryConflictObservation,
            "observation",
        )
        for name in ("event_digest", "source_family_digest", "memory_snapshot_digest"):
            object.__setattr__(self, name, _require_sha256_digest(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_claim_count",
            _require_positive_count_decimal(
                "source_claim_count",
                self.source_claim_count,
            ),
        )
        for name in ("conflicting_memory_count", "corroborating_memory_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        if self.conflicting_memory_count + self.corroborating_memory_count > self.source_claim_count:
            raise ValueError("memory totals must not exceed source_claim_count")
        for name in ("newest_memory_age_seconds", "current_evidence_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "signal_alignment_score",
            "memory_consistency_score",
            "resolution_rule_match_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
            "public payload item",
        )
        object.__setattr__(self, "key", _require_public_label("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictRow:
    event_digest: str
    source_family_digest: str
    memory_snapshot_digest: str
    observed_at: datetime
    source_claim_count: Decimal
    conflicting_memory_count: Decimal
    corroborating_memory_count: Decimal
    conflict_ratio: Decimal
    current_freshness_score: Decimal
    memory_recency_score: Decimal
    signal_alignment_score: Decimal
    memory_consistency_score: Decimal
    resolution_rule_match_score: Decimal
    resolution_confidence_score: Decimal
    newest_memory_age_seconds: Decimal
    current_evidence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictRow:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSourceMemoryConflictRow, "row")
        for name in ("event_digest", "source_family_digest", "memory_snapshot_digest"):
            object.__setattr__(self, name, _require_sha256_digest(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_claim_count",
            _require_positive_count_decimal(
                "source_claim_count",
                self.source_claim_count,
            ),
        )
        for name in ("conflicting_memory_count", "corroborating_memory_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        if self.conflicting_memory_count + self.corroborating_memory_count > self.source_claim_count:
            raise ValueError("memory totals must not exceed source_claim_count")
        for name in ("newest_memory_age_seconds", "current_evidence_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "conflict_ratio",
            "current_freshness_score",
            "memory_recency_score",
            "signal_alignment_score",
            "memory_consistency_score",
            "resolution_rule_match_score",
            "resolution_confidence_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.conflict_ratio != _ratio(
            self.conflicting_memory_count,
            self.source_claim_count,
        ):
            raise ValueError("conflict_ratio must match row counts")
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if _row_status(self.reason_codes) != self.status:
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventResolutionSourceMemoryConflictReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_conflict_ratio: Decimal
    average_resolution_confidence_score: Decimal
    max_conflict_ratio: Decimal
    rows: tuple[ResearchEventResolutionSourceMemoryConflictRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
        ...,
    ]
    public_payload: tuple[
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionSourceMemoryConflictReport:
            raise TypeError(
                "ResearchEventResolutionSourceMemoryConflictReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSourceMemoryConflictReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for name in ("observation_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "average_conflict_ratio",
            "average_resolution_confidence_score",
            "max_conflict_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_event_resolution_source_memory_conflict_report_payload(self)


def build_research_event_resolution_source_memory_conflict_report(
    observations: Sequence[ResearchEventResolutionSourceMemoryConflictObservation],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSourceMemoryConflictConfig | None = None,
    public_payload: Sequence[
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem
    ] = (),
) -> ResearchEventResolutionSourceMemoryConflictReport:
    if config is None:
        config = ResearchEventResolutionSourceMemoryConflictConfig()
    if type(config) is not ResearchEventResolutionSourceMemoryConflictConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionSourceMemoryConflictConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _build_rows(normalized_observations, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "observation_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_conflict_ratio": _average(tuple(row.conflict_ratio for row in rows)),
        "average_resolution_confidence_score": _average(
            tuple(row.resolution_confidence_score for row in rows),
        ),
        "max_conflict_ratio": max((row.conflict_ratio for row in rows), default=ZERO),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionSourceMemoryConflictReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_source_memory_conflict_report_payload(
    report: ResearchEventResolutionSourceMemoryConflictReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchEventResolutionSourceMemoryConflictReport:
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionSourceMemoryConflictReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _validate_report_payload_schema(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _payload_report(payload)
    return payload


def research_event_resolution_source_memory_conflict_report_digest(
    report: ResearchEventResolutionSourceMemoryConflictReport | Mapping[str, object],
) -> str:
    payload = research_event_resolution_source_memory_conflict_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    return digest


def _build_rows(
    observations: tuple[ResearchEventResolutionSourceMemoryConflictObservation, ...],
    config: ResearchEventResolutionSourceMemoryConflictConfig,
) -> tuple[ResearchEventResolutionSourceMemoryConflictRow, ...]:
    rows = tuple(_row_from_observation(item, config) for item in observations)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_INDEX[row.status],
                row.event_digest,
                row.source_family_digest,
                row.memory_snapshot_digest,
            ),
        ),
    )


def _row_from_observation(
    item: ResearchEventResolutionSourceMemoryConflictObservation,
    config: ResearchEventResolutionSourceMemoryConflictConfig,
) -> ResearchEventResolutionSourceMemoryConflictRow:
    conflict_ratio = _ratio(item.conflicting_memory_count, item.source_claim_count)
    current_freshness_score = _freshness_score(
        item.current_evidence_age_seconds,
        config.max_current_evidence_age_seconds,
    )
    memory_recency_score = _freshness_score(
        item.newest_memory_age_seconds,
        config.max_memory_age_seconds,
    )
    resolution_confidence_score = _resolution_confidence_score(
        conflict_ratio=conflict_ratio,
        current_freshness_score=current_freshness_score,
        memory_recency_score=memory_recency_score,
        signal_alignment_score=item.signal_alignment_score,
        memory_consistency_score=item.memory_consistency_score,
        resolution_rule_match_score=item.resolution_rule_match_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        conflict_ratio=conflict_ratio,
        config=config,
    )
    return ResearchEventResolutionSourceMemoryConflictRow(
        event_digest=item.event_digest,
        source_family_digest=item.source_family_digest,
        memory_snapshot_digest=item.memory_snapshot_digest,
        observed_at=item.observed_at,
        source_claim_count=item.source_claim_count,
        conflicting_memory_count=item.conflicting_memory_count,
        corroborating_memory_count=item.corroborating_memory_count,
        conflict_ratio=conflict_ratio,
        current_freshness_score=current_freshness_score,
        memory_recency_score=memory_recency_score,
        signal_alignment_score=item.signal_alignment_score,
        memory_consistency_score=item.memory_consistency_score,
        resolution_rule_match_score=item.resolution_rule_match_score,
        resolution_confidence_score=resolution_confidence_score,
        newest_memory_age_seconds=item.newest_memory_age_seconds,
        current_evidence_age_seconds=item.current_evidence_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionSourceMemoryConflictObservation,
    *,
    conflict_ratio: Decimal,
    config: ResearchEventResolutionSourceMemoryConflictConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if conflict_ratio > config.max_watch_conflict_ratio:
        reason_codes.append("conflict_ratio_block")
    elif conflict_ratio > config.max_pass_conflict_ratio:
        reason_codes.append("conflict_ratio_watch")
    if item.signal_alignment_score < config.min_watch_signal_alignment_score:
        reason_codes.append("signal_alignment_block")
    elif item.signal_alignment_score < config.min_pass_signal_alignment_score:
        reason_codes.append("signal_alignment_watch")
    if item.memory_consistency_score < config.min_watch_memory_consistency_score:
        reason_codes.append("memory_consistency_block")
    elif item.memory_consistency_score < config.min_pass_memory_consistency_score:
        reason_codes.append("memory_consistency_watch")
    if item.resolution_rule_match_score < config.min_watch_rule_match_score:
        reason_codes.append("rule_match_block")
    elif item.resolution_rule_match_score < config.min_pass_rule_match_score:
        reason_codes.append("rule_match_watch")
    if item.current_evidence_age_seconds > config.max_current_evidence_age_seconds:
        reason_codes.append("current_evidence_stale_block")
    if item.newest_memory_age_seconds > config.max_memory_age_seconds:
        reason_codes.append("memory_recency_stale_watch")
    if not reason_codes:
        reason_codes.append("resolution_source_memory_conflict_pass")
    return _normalize_reason_codes(reason_codes)


def _row_status(reason_codes: Sequence[str]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return STATUS_BLOCK
    if tuple(reason_codes) == ("resolution_source_memory_conflict_pass",):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchEventResolutionSourceMemoryConflictRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSourceMemoryConflictRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_source_memory_conflict_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionSourceMemoryConflictRow, ...],
) -> tuple[ResearchEventResolutionSourceMemoryConflictReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionSourceMemoryConflictReasonCodeCount(
                reason_code="empty_source_memory_conflict_set",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    result: list[ResearchEventResolutionSourceMemoryConflictReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _decimal_count(
            sum(1 for row in rows if reason_code in row.reason_codes),
        )
        if count > ZERO:
            result.append(
                ResearchEventResolutionSourceMemoryConflictReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    row_ratio=_ratio(count, _decimal_count(len(rows))),
                ),
            )
    return tuple(result)


def _normalize_observations(
    observations: Sequence[ResearchEventResolutionSourceMemoryConflictObservation],
) -> tuple[ResearchEventResolutionSourceMemoryConflictObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchEventResolutionSourceMemoryConflictObservation] = []
    seen: set[tuple[str, str, str]] = set()
    for item in observations:
        if type(item) is not ResearchEventResolutionSourceMemoryConflictObservation:
            raise ValueError(
                "observations must contain ResearchEventResolutionSourceMemoryConflictObservation",
            )
        key = (item.event_digest, item.source_family_digest, item.memory_snapshot_digest)
        if key in seen:
            raise ValueError("observation triples must be unique")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_digest,
                item.source_family_digest,
                item.memory_snapshot_digest,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionSourceMemoryConflictRow],
) -> tuple[ResearchEventResolutionSourceMemoryConflictRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionSourceMemoryConflictRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionSourceMemoryConflictRow:
            raise ValueError("rows must contain ResearchEventResolutionSourceMemoryConflictRow")
        key = (row.event_digest, row.source_family_digest, row.memory_snapshot_digest)
        if key in seen:
            raise ValueError("row triples must be unique")
        seen.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                _STATUS_INDEX[row.status],
                row.event_digest,
                row.source_family_digest,
                row.memory_snapshot_digest,
            ),
        ),
    )


def _normalize_reason_code_counts(
    counts: Sequence[ResearchEventResolutionSourceMemoryConflictReasonCodeCount],
) -> tuple[ResearchEventResolutionSourceMemoryConflictReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchEventResolutionSourceMemoryConflictReasonCodeCount] = []
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchEventResolutionSourceMemoryConflictReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchEventResolutionSourceMemoryConflictReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code)),
    )


def _normalize_public_payload(
    items: Sequence[ResearchEventResolutionSourceMemoryConflictPublicPayloadItem],
) -> tuple[ResearchEventResolutionSourceMemoryConflictPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionSourceMemoryConflictPublicPayloadItem] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchEventResolutionSourceMemoryConflictPublicPayloadItem:
            raise ValueError(
                "public_payload must contain ResearchEventResolutionSourceMemoryConflictPublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_report_consistency(
    report: ResearchEventResolutionSourceMemoryConflictReport,
) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count does not match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count does not match rows")
    if report.average_conflict_ratio != _average(tuple(row.conflict_ratio for row in rows)):
        raise ValueError("average_conflict_ratio does not match rows")
    if report.average_resolution_confidence_score != _average(
        tuple(row.resolution_confidence_score for row in rows),
    ):
        raise ValueError("average_resolution_confidence_score does not match rows")
    if report.max_conflict_ratio != max((row.conflict_ratio for row in rows), default=ZERO):
        raise ValueError("max_conflict_ratio does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match rows")


def _validate_report_payload_schema(payload: dict[str, object]) -> None:
    report_payload = _require_payload_schema(
        "report",
        payload,
        ResearchEventResolutionSourceMemoryConflictReport,
    )
    config_version = _require_public_label(
        "config_version",
        report_payload["config_version"],
    )
    if (
        config_version
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _payload_datetime("generated_at", report_payload["generated_at"])
    _payload_status("status", report_payload["status"])
    _payload_count("observation_count", report_payload["observation_count"])
    _payload_count("pass_count", report_payload["pass_count"])
    _payload_count("watch_count", report_payload["watch_count"])
    _payload_count("block_count", report_payload["block_count"])
    _payload_ratio("average_conflict_ratio", report_payload["average_conflict_ratio"])
    _payload_ratio(
        "average_resolution_confidence_score",
        report_payload["average_resolution_confidence_score"],
    )
    _payload_ratio("max_conflict_ratio", report_payload["max_conflict_ratio"])
    _validate_rows_payload_schema(report_payload["rows"])
    _payload_reason_codes("reason_codes", report_payload["reason_codes"])
    _validate_reason_code_counts_payload_schema(report_payload["reason_code_counts"])
    _validate_public_items_payload_schema(report_payload["public_payload"])
    _require_sha256_digest(
        "derived_validation_digest",
        report_payload["derived_validation_digest"],
    )
    _payload_true("paper_only", report_payload["paper_only"])
    _payload_true("report_only", report_payload["report_only"])
    _payload_true("readonly", report_payload["readonly"])


def _validate_rows_payload_schema(value: object) -> None:
    for item in _payload_list("rows", value):
        _validate_row_payload_schema(item)


def _validate_row_payload_schema(value: object) -> None:
    payload = _require_payload_schema(
        "row",
        value,
        ResearchEventResolutionSourceMemoryConflictRow,
    )
    _require_sha256_digest("event_digest", payload["event_digest"])
    _require_sha256_digest("source_family_digest", payload["source_family_digest"])
    _require_sha256_digest("memory_snapshot_digest", payload["memory_snapshot_digest"])
    _payload_datetime("observed_at", payload["observed_at"])
    _payload_count("source_claim_count", payload["source_claim_count"], positive=True)
    _payload_count("conflicting_memory_count", payload["conflicting_memory_count"])
    _payload_count("corroborating_memory_count", payload["corroborating_memory_count"])
    _payload_ratio("conflict_ratio", payload["conflict_ratio"])
    _payload_ratio("current_freshness_score", payload["current_freshness_score"])
    _payload_ratio("memory_recency_score", payload["memory_recency_score"])
    _payload_ratio("signal_alignment_score", payload["signal_alignment_score"])
    _payload_ratio("memory_consistency_score", payload["memory_consistency_score"])
    _payload_ratio("resolution_rule_match_score", payload["resolution_rule_match_score"])
    _payload_ratio("resolution_confidence_score", payload["resolution_confidence_score"])
    _payload_nonnegative_decimal(
        "newest_memory_age_seconds",
        payload["newest_memory_age_seconds"],
    )
    _payload_nonnegative_decimal(
        "current_evidence_age_seconds",
        payload["current_evidence_age_seconds"],
    )
    _payload_status("status", payload["status"])
    _payload_reason_codes("reason_codes", payload["reason_codes"])
    _payload_true("paper_only", payload["paper_only"])
    _payload_true("report_only", payload["report_only"])
    _payload_true("readonly", payload["readonly"])


def _validate_reason_code_counts_payload_schema(value: object) -> None:
    for item in _payload_list("reason_code_counts", value):
        _validate_reason_code_count_payload_schema(item)


def _validate_reason_code_count_payload_schema(value: object) -> None:
    payload = _require_payload_schema(
        "reason code count",
        value,
        ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
    )
    _require_reason_code(payload["reason_code"])
    _payload_count("count", payload["count"], positive=True)
    _payload_ratio("row_ratio", payload["row_ratio"])
    _payload_true("paper_only", payload["paper_only"])
    _payload_true("report_only", payload["report_only"])
    _payload_true("readonly", payload["readonly"])


def _validate_public_items_payload_schema(value: object) -> None:
    for item in _payload_list("public_payload", value):
        _validate_public_item_payload_schema(item)


def _validate_public_item_payload_schema(value: object) -> None:
    payload = _require_payload_schema(
        "public payload item",
        value,
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
    )
    _require_public_label("key", payload["key"])
    _require_public_text("value", payload["value"])
    _payload_true("paper_only", payload["paper_only"])
    _payload_true("report_only", payload["report_only"])
    _payload_true("readonly", payload["readonly"])


def _payload_report(
    value: object,
) -> ResearchEventResolutionSourceMemoryConflictReport:
    payload = _require_payload_schema(
        "report",
        value,
        ResearchEventResolutionSourceMemoryConflictReport,
    )
    config_version = _require_public_label("config_version", payload["config_version"])
    if (
        config_version
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    return ResearchEventResolutionSourceMemoryConflictReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=config_version,
        status=_payload_status("status", payload["status"]),
        observation_count=_payload_count("observation_count", payload["observation_count"]),
        pass_count=_payload_count("pass_count", payload["pass_count"]),
        watch_count=_payload_count("watch_count", payload["watch_count"]),
        block_count=_payload_count("block_count", payload["block_count"]),
        average_conflict_ratio=_payload_ratio(
            "average_conflict_ratio",
            payload["average_conflict_ratio"],
        ),
        average_resolution_confidence_score=_payload_ratio(
            "average_resolution_confidence_score",
            payload["average_resolution_confidence_score"],
        ),
        max_conflict_ratio=_payload_ratio("max_conflict_ratio", payload["max_conflict_ratio"]),
        rows=_payload_rows(payload["rows"]),
        reason_codes=_payload_reason_codes("reason_codes", payload["reason_codes"]),
        reason_code_counts=_payload_reason_code_counts(payload["reason_code_counts"]),
        public_payload=_payload_public_items(payload["public_payload"]),
        derived_validation_digest=_require_sha256_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _payload_rows(
    value: object,
) -> tuple[ResearchEventResolutionSourceMemoryConflictRow, ...]:
    return tuple(_payload_row(item) for item in _payload_list("rows", value))


def _payload_row(
    value: object,
) -> ResearchEventResolutionSourceMemoryConflictRow:
    payload = _require_payload_schema(
        "row",
        value,
        ResearchEventResolutionSourceMemoryConflictRow,
    )
    return ResearchEventResolutionSourceMemoryConflictRow(
        event_digest=_require_sha256_digest("event_digest", payload["event_digest"]),
        source_family_digest=_require_sha256_digest(
            "source_family_digest",
            payload["source_family_digest"],
        ),
        memory_snapshot_digest=_require_sha256_digest(
            "memory_snapshot_digest",
            payload["memory_snapshot_digest"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        source_claim_count=_payload_count(
            "source_claim_count",
            payload["source_claim_count"],
            positive=True,
        ),
        conflicting_memory_count=_payload_count(
            "conflicting_memory_count",
            payload["conflicting_memory_count"],
        ),
        corroborating_memory_count=_payload_count(
            "corroborating_memory_count",
            payload["corroborating_memory_count"],
        ),
        conflict_ratio=_payload_ratio("conflict_ratio", payload["conflict_ratio"]),
        current_freshness_score=_payload_ratio(
            "current_freshness_score",
            payload["current_freshness_score"],
        ),
        memory_recency_score=_payload_ratio(
            "memory_recency_score",
            payload["memory_recency_score"],
        ),
        signal_alignment_score=_payload_ratio(
            "signal_alignment_score",
            payload["signal_alignment_score"],
        ),
        memory_consistency_score=_payload_ratio(
            "memory_consistency_score",
            payload["memory_consistency_score"],
        ),
        resolution_rule_match_score=_payload_ratio(
            "resolution_rule_match_score",
            payload["resolution_rule_match_score"],
        ),
        resolution_confidence_score=_payload_ratio(
            "resolution_confidence_score",
            payload["resolution_confidence_score"],
        ),
        newest_memory_age_seconds=_payload_nonnegative_decimal(
            "newest_memory_age_seconds",
            payload["newest_memory_age_seconds"],
        ),
        current_evidence_age_seconds=_payload_nonnegative_decimal(
            "current_evidence_age_seconds",
            payload["current_evidence_age_seconds"],
        ),
        status=_payload_status("status", payload["status"]),
        reason_codes=_payload_reason_codes("reason_codes", payload["reason_codes"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _payload_reason_code_counts(
    value: object,
) -> tuple[ResearchEventResolutionSourceMemoryConflictReasonCodeCount, ...]:
    return tuple(
        _payload_reason_code_count(item)
        for item in _payload_list("reason_code_counts", value)
    )


def _payload_reason_code_count(
    value: object,
) -> ResearchEventResolutionSourceMemoryConflictReasonCodeCount:
    payload = _require_payload_schema(
        "reason code count",
        value,
        ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
    )
    return ResearchEventResolutionSourceMemoryConflictReasonCodeCount(
        reason_code=_require_reason_code(payload["reason_code"]),
        count=_payload_count("count", payload["count"], positive=True),
        row_ratio=_payload_ratio("row_ratio", payload["row_ratio"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _payload_public_items(
    value: object,
) -> tuple[ResearchEventResolutionSourceMemoryConflictPublicPayloadItem, ...]:
    return tuple(_payload_public_item(item) for item in _payload_list("public_payload", value))


def _payload_public_item(
    value: object,
) -> ResearchEventResolutionSourceMemoryConflictPublicPayloadItem:
    payload = _require_payload_schema(
        "public payload item",
        value,
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
    )
    return ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
        key=_require_public_label("key", payload["key"]),
        value=_require_public_text("value", payload["value"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _require_payload_schema(
    label: str,
    value: object,
    expected_type: type[object],
) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} payload schema is invalid")
    expected_keys = frozenset(field.name for field in fields(expected_type))
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} payload schema is invalid")
    return value


def _payload_list(field_name: str, value: object) -> tuple[object, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} payload schema is invalid")
    return tuple(value)


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    reason_codes = tuple(_require_reason_code(item) for item in _payload_list(field_name, value))
    if reason_codes != _normalize_reason_codes(reason_codes):
        raise ValueError(f"{field_name} must be canonical")
    return reason_codes


def _payload_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field_name} must be a datetime string") from None
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _payload_count(field_name: str, value: object, *, positive: bool = False) -> Decimal:
    decimal_value = _payload_decimal(field_name, value)
    if positive:
        return _require_positive_count_decimal(field_name, decimal_value)
    return _require_nonnegative_count_decimal(field_name, decimal_value)


def _payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, _payload_decimal(field_name, value))


def _payload_ratio(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _payload_decimal(field_name, value))


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or _DECIMAL_STRING_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(value)


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _resolution_confidence_score(
    *,
    conflict_ratio: Decimal,
    current_freshness_score: Decimal,
    memory_recency_score: Decimal,
    signal_alignment_score: Decimal,
    memory_consistency_score: Decimal,
    resolution_rule_match_score: Decimal,
    config: ResearchEventResolutionSourceMemoryConflictConfig,
) -> Decimal:
    return _clamp_ratio(
        (ONE - conflict_ratio) * config.conflict_clear_weight
        + signal_alignment_score * config.signal_alignment_weight
        + memory_consistency_score * config.memory_consistency_weight
        + resolution_rule_match_score * config.rule_match_weight
        + current_freshness_score * config.current_freshness_weight
        + memory_recency_score * config.memory_recency_weight,
    )


def _freshness_score(age_seconds: Decimal, max_age_seconds: Decimal) -> Decimal:
    return _clamp_ratio(ONE - (age_seconds / max_age_seconds))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _status_count(
    rows: tuple[ResearchEventResolutionSourceMemoryConflictRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized or not _PUBLIC_LABEL_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(normalized)
    return normalized


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_public_string(normalized)
    return normalized


def _require_reason_code(value: object) -> str:
    if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    for reason_code in reason_codes:
        seen.add(_require_reason_code(reason_code))
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in seen)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEventResolutionSourceMemoryConflictReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_payload(_json_ready(values))


def _digest_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


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


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(value)


def _reject_unsafe_public_string(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload")
