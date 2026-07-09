"""Report-only event resolution signal reversal decay reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-signal-reversal-decay-report-v0"
)
EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PAYLOAD_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

REPORT_ACTION_BY_STATUS = {
    "pass": "paper_event_resolution_signal_reversal_decay_monitor",
    "watch": "paper_event_resolution_signal_reversal_decay_watch",
    "block": "paper_event_resolution_signal_reversal_decay_block",
}
REPORT_REASON_BY_STATUS = {
    "pass": "event_resolution_signal_reversal_decay_report_pass",
    "watch": "event_resolution_signal_reversal_decay_report_watch",
    "block": "event_resolution_signal_reversal_decay_report_block",
}
STATUS_REASON_BY_STATUS = {
    "pass": "event_resolution_signal_reversal_decay_pass",
    "watch": "event_resolution_signal_reversal_decay_watch",
    "block": "event_resolution_signal_reversal_decay_block",
}

SIGNAL_REVERSAL_HIGH_REASON = "signal_reversal_high"
EVIDENCE_CONFIDENCE_DECAY_REASON = "evidence_confidence_decay"
AUTHORITY_CONFLICT_PRESSURE_REASON = "authority_conflict_pressure"
CORROBORATION_GAP_REASON = "corroboration_gap"
POST_RESOLUTION_DECAY_REASON = "post_resolution_decay"

ROW_REASON_CODES = (
    AUTHORITY_CONFLICT_PRESSURE_REASON,
    CORROBORATION_GAP_REASON,
    EVIDENCE_CONFIDENCE_DECAY_REASON,
    POST_RESOLUTION_DECAY_REASON,
    SIGNAL_REVERSAL_HIGH_REASON,
    STATUS_REASON_BY_STATUS["pass"],
    STATUS_REASON_BY_STATUS["watch"],
    STATUS_REASON_BY_STATUS["block"],
)
REPORT_REASON_CODES = (
    REPORT_REASON_BY_STATUS["pass"],
    REPORT_REASON_BY_STATUS["watch"],
    REPORT_REASON_BY_STATUS["block"],
    *ROW_REASON_CODES,
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "live",
        "raw",
        "scrape",
        "network",
        "database",
        "recommend",
        "sizing",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "live",
        "raw_source",
        "scrape",
        "network",
        "database",
        "recommend",
        "sizing",
    ),
)
UNSAFE_PUBLIC_KEYS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ),
)
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "report_action",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_reversal_decay_score",
        "max_reversal_decay_score",
        "max_signal_reversal_magnitude",
        "max_post_resolution_age_hours",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "event_digest",
        "status",
        "observed_at",
        "resolved_at",
        "observation_age_hours",
        "post_resolution_age_hours",
        "signal_reversal_magnitude",
        "evidence_confidence_decay_score",
        "authority_conflict_score",
        "corroboration_count",
        "expected_corroboration_count",
        "corroboration_gap_score",
        "post_resolution_decay_score",
        "reversal_decay_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "event_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION",
    "EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES",
    "ResearchEventResolutionSignalReversalDecayConfig",
    "ResearchEventResolutionSignalReversalDecayObservation",
    "ResearchEventResolutionSignalReversalDecayReasonCodeCount",
    "ResearchEventResolutionSignalReversalDecayReport",
    "ResearchEventResolutionSignalReversalDecayRow",
    "build_research_event_resolution_signal_reversal_decay_report",
    "research_event_resolution_signal_reversal_decay_report_digest",
    "research_event_resolution_signal_reversal_decay_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchEventResolutionSignalReversalDecayConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION
    )
    watch_score_threshold: Decimal = Decimal("0.350000")
    block_score_threshold: Decimal = Decimal("0.700000")
    post_resolution_decay_window_hours: Decimal = Decimal("18.000000")
    signal_reversal_watch_threshold: Decimal = Decimal("0.250000")
    evidence_confidence_decay_watch_threshold: Decimal = Decimal("0.250000")
    authority_conflict_watch_threshold: Decimal = Decimal("0.250000")
    post_resolution_decay_watch_threshold: Decimal = Decimal("0.500000")
    signal_reversal_magnitude_weight: Decimal = Decimal("0.400000")
    evidence_confidence_decay_weight: Decimal = Decimal("0.200000")
    authority_conflict_weight: Decimal = Decimal("0.200000")
    corroboration_gap_weight: Decimal = Decimal("0.100000")
    post_resolution_decay_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSignalReversalDecayConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_score_threshold",
            "block_score_threshold",
            "signal_reversal_watch_threshold",
            "evidence_confidence_decay_watch_threshold",
            "authority_conflict_watch_threshold",
            "post_resolution_decay_watch_threshold",
            "signal_reversal_magnitude_weight",
            "evidence_confidence_decay_weight",
            "authority_conflict_weight",
            "corroboration_gap_weight",
            "post_resolution_decay_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "post_resolution_decay_window_hours",
            _require_positive_decimal(
                "post_resolution_decay_window_hours",
                self.post_resolution_decay_window_hours,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionSignalReversalDecayObservation(_FinalDataclass):
    private_event_reference: str
    observed_at: datetime
    resolved_at: datetime
    pre_resolution_signal_score: Decimal
    post_resolution_signal_score: Decimal
    evidence_confidence_score: Decimal
    authority_conflict_score: Decimal
    corroboration_count: Decimal
    expected_corroboration_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSignalReversalDecayObservation,
            "observation",
        )
        if type(self.private_event_reference) is not str:
            raise ValueError("private_event_reference must be a string")
        if not self.private_event_reference:
            raise ValueError("private_event_reference must not be empty")
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        if self.resolved_at < self.observed_at:
            raise ValueError("resolved_at must not be before observed_at")
        for field_name in (
            "pre_resolution_signal_score",
            "post_resolution_signal_score",
            "evidence_confidence_score",
            "authority_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_count_decimal(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        object.__setattr__(
            self,
            "expected_corroboration_count",
            _require_positive_count_decimal(
                "expected_corroboration_count",
                self.expected_corroboration_count,
            ),
        )
        if self.corroboration_count > self.expected_corroboration_count:
            raise ValueError(
                "corroboration_count must not exceed expected_corroboration_count",
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionSignalReversalDecayRow(_FinalDataclass):
    event_digest: str
    status: str
    observed_at: datetime
    resolved_at: datetime
    observation_age_hours: Decimal
    post_resolution_age_hours: Decimal
    signal_reversal_magnitude: Decimal
    evidence_confidence_decay_score: Decimal
    authority_conflict_score: Decimal
    corroboration_count: Decimal
    expected_corroboration_count: Decimal
    corroboration_gap_score: Decimal
    post_resolution_decay_score: Decimal
    reversal_decay_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSignalReversalDecayRow, "row")
        _require_digest("event_digest", self.event_digest)
        _require_status("status", self.status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "observation_age_hours",
            "post_resolution_age_hours",
            "corroboration_count",
            "expected_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_reversal_magnitude",
            "evidence_confidence_decay_score",
            "authority_conflict_score",
            "corroboration_gap_score",
            "post_resolution_decay_score",
            "reversal_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionSignalReversalDecayReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionSignalReversalDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventResolutionSignalReversalDecayReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    report_action: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reversal_decay_score: Decimal
    max_reversal_decay_score: Decimal
    max_signal_reversal_magnitude: Decimal
    max_post_resolution_age_hours: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventResolutionSignalReversalDecayReasonCodeCount, ...]
    rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionSignalReversalDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_public_label("report_action", self.report_action)
        if self.report_action != REPORT_ACTION_BY_STATUS[self.status]:
            raise ValueError("report_action must match status")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_post_resolution_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reversal_decay_score",
            "max_reversal_decay_score",
            "max_signal_reversal_magnitude",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_values_without_digest(self)),
            )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_signal_reversal_decay_report_payload(self)


def build_research_event_resolution_signal_reversal_decay_report(
    observations: Sequence[ResearchEventResolutionSignalReversalDecayObservation],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSignalReversalDecayConfig | None = None,
) -> ResearchEventResolutionSignalReversalDecayReport:
    """Build a deterministic report-only snapshot of post-resolution reversal decay."""

    if config is None:
        config = ResearchEventResolutionSignalReversalDecayConfig()
    if type(config) is not ResearchEventResolutionSignalReversalDecayConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionSignalReversalDecayConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    generated_at=generated_at,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "report_action": REPORT_ACTION_BY_STATUS[status],
        "event_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_reversal_decay_score": _average(
            tuple(row.reversal_decay_score for row in rows),
        ),
        "max_reversal_decay_score": max(
            (row.reversal_decay_score for row in rows),
            default=ZERO,
        ),
        "max_signal_reversal_magnitude": max(
            (row.signal_reversal_magnitude for row in rows),
            default=ZERO,
        ),
        "max_post_resolution_age_hours": max(
            (row.post_resolution_age_hours for row in rows),
            default=ZERO,
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionSignalReversalDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_signal_reversal_decay_report_payload(
    report: ResearchEventResolutionSignalReversalDecayReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionSignalReversalDecayReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionSignalReversalDecayReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_flags(payload)
    _validate_payload_statuses(payload)
    _validate_payload_schema(payload)
    _validate_payload_digest(payload)
    return payload


def research_event_resolution_signal_reversal_decay_report_digest(
    report: ResearchEventResolutionSignalReversalDecayReport | Mapping[str, Any],
) -> str:
    payload = research_event_resolution_signal_reversal_decay_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observation(
    observation: ResearchEventResolutionSignalReversalDecayObservation,
    *,
    generated_at: datetime,
    config: ResearchEventResolutionSignalReversalDecayConfig,
) -> ResearchEventResolutionSignalReversalDecayRow:
    if observation.resolved_at > generated_at:
        raise ValueError("resolved_at must not be after generated_at")
    observation_age_hours = _duration_hours(observation.observed_at, generated_at)
    post_resolution_age_hours = _duration_hours(observation.resolved_at, generated_at)
    signal_reversal_magnitude = _clamp_ratio(
        abs(observation.post_resolution_signal_score - observation.pre_resolution_signal_score),
    )
    evidence_confidence_decay_score = _clamp_ratio(
        ONE - observation.evidence_confidence_score,
    )
    corroboration_gap_score = _clamp_ratio(
        _safe_ratio(
            observation.expected_corroboration_count - observation.corroboration_count,
            observation.expected_corroboration_count,
        ),
    )
    post_resolution_decay_score = _clamp_ratio(
        _safe_ratio(
            post_resolution_age_hours,
            config.post_resolution_decay_window_hours,
        ),
    )
    reversal_decay_score = _clamp_ratio(
        (signal_reversal_magnitude * config.signal_reversal_magnitude_weight)
        + (
            evidence_confidence_decay_score
            * config.evidence_confidence_decay_weight
        )
        + (observation.authority_conflict_score * config.authority_conflict_weight)
        + (corroboration_gap_score * config.corroboration_gap_weight)
        + (post_resolution_decay_score * config.post_resolution_decay_weight),
    )
    status = _row_status(reversal_decay_score, config)
    return ResearchEventResolutionSignalReversalDecayRow(
        event_digest=_event_digest(observation.private_event_reference),
        status=status,
        observed_at=observation.observed_at,
        resolved_at=observation.resolved_at,
        observation_age_hours=observation_age_hours,
        post_resolution_age_hours=post_resolution_age_hours,
        signal_reversal_magnitude=signal_reversal_magnitude,
        evidence_confidence_decay_score=evidence_confidence_decay_score,
        authority_conflict_score=observation.authority_conflict_score,
        corroboration_count=observation.corroboration_count,
        expected_corroboration_count=observation.expected_corroboration_count,
        corroboration_gap_score=corroboration_gap_score,
        post_resolution_decay_score=post_resolution_decay_score,
        reversal_decay_score=reversal_decay_score,
        reason_codes=_row_reason_codes(
            status=status,
            signal_reversal_magnitude=signal_reversal_magnitude,
            evidence_confidence_decay_score=evidence_confidence_decay_score,
            authority_conflict_score=observation.authority_conflict_score,
            corroboration_gap_score=corroboration_gap_score,
            post_resolution_decay_score=post_resolution_decay_score,
            config=config,
        ),
    )


def _row_reason_codes(
    *,
    status: str,
    signal_reversal_magnitude: Decimal,
    evidence_confidence_decay_score: Decimal,
    authority_conflict_score: Decimal,
    corroboration_gap_score: Decimal,
    post_resolution_decay_score: Decimal,
    config: ResearchEventResolutionSignalReversalDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_conflict_score >= config.authority_conflict_watch_threshold:
        reasons.append(AUTHORITY_CONFLICT_PRESSURE_REASON)
    if corroboration_gap_score > ZERO:
        reasons.append(CORROBORATION_GAP_REASON)
    if evidence_confidence_decay_score >= config.evidence_confidence_decay_watch_threshold:
        reasons.append(EVIDENCE_CONFIDENCE_DECAY_REASON)
    if post_resolution_decay_score >= config.post_resolution_decay_watch_threshold:
        reasons.append(POST_RESOLUTION_DECAY_REASON)
    if signal_reversal_magnitude >= config.signal_reversal_watch_threshold:
        reasons.append(SIGNAL_REVERSAL_HIGH_REASON)
    reasons.append(STATUS_REASON_BY_STATUS[status])
    return _require_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(
    reversal_decay_score: Decimal,
    config: ResearchEventResolutionSignalReversalDecayConfig,
) -> str:
    if reversal_decay_score >= config.block_score_threshold:
        return "block"
    if reversal_decay_score >= config.watch_score_threshold:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...],
    status: str,
) -> tuple[str, ...]:
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    return (
        REPORT_REASON_BY_STATUS[status],
        *(reason for reason in ROW_REASON_CODES if reason in row_reasons),
    )


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...],
) -> tuple[ResearchEventResolutionSignalReversalDecayReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchEventResolutionSignalReversalDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            event_ratio=_safe_ratio(_decimal_count(counts[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if counts[reason_code]
    )


def _normalize_observations(
    observations: Sequence[ResearchEventResolutionSignalReversalDecayObservation],
) -> tuple[ResearchEventResolutionSignalReversalDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchEventResolutionSignalReversalDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventResolutionSignalReversalDecayObservation",
            )
        digest = _event_digest(observation.private_event_reference)
        if digest in seen:
            raise ValueError("private_event_reference values must be unique")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...],
) -> tuple[ResearchEventResolutionSignalReversalDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventResolutionSignalReversalDecayRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionSignalReversalDecayRow",
            )
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted by reversal decay priority")
    if len({row.event_digest for row in normalized}) != len(normalized):
        raise ValueError("rows must have unique event_digest values")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventResolutionSignalReversalDecayReasonCodeCount, ...],
) -> tuple[ResearchEventResolutionSignalReversalDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchEventResolutionSignalReversalDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionSignalReversalDecayReasonCodeCount",
            )
    expected = tuple(
        sorted(normalized, key=lambda item: ROW_REASON_CODES.index(item.reason_code)),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted")
    if len({item.reason_code for item in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must be unique")
    return normalized


def _row_sort_key(
    row: ResearchEventResolutionSignalReversalDecayRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.reversal_decay_score,
        -row.signal_reversal_magnitude,
        row.event_digest,
    )


def _status_count(
    rows: tuple[ResearchEventResolutionSignalReversalDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_config(config: ResearchEventResolutionSignalReversalDecayConfig) -> None:
    if config.block_score_threshold <= config.watch_score_threshold:
        raise ValueError("block_score_threshold must exceed watch_score_threshold")
    weights = (
        config.signal_reversal_magnitude_weight
        + config.evidence_confidence_decay_weight
        + config.authority_conflict_weight
        + config.corroboration_gap_weight
        + config.post_resolution_decay_weight
    )
    if _quantize(weights) != ONE:
        raise ValueError("reversal decay weights must sum to 1.000000")


def _validate_row(row: ResearchEventResolutionSignalReversalDecayRow) -> None:
    if row.resolved_at < row.observed_at:
        raise ValueError("resolved_at must not be before observed_at")
    if row.expected_corroboration_count <= ZERO:
        raise ValueError("expected_corroboration_count must be positive")
    if row.corroboration_count > row.expected_corroboration_count:
        raise ValueError(
            "corroboration_count must not exceed expected_corroboration_count",
        )


def _validate_report(report: ResearchEventResolutionSignalReversalDecayReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal block rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.average_reversal_decay_score != _average(
        tuple(row.reversal_decay_score for row in report.rows),
    ):
        raise ValueError("average_reversal_decay_score must match rows")
    if report.max_reversal_decay_score != max(
        (row.reversal_decay_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_reversal_decay_score must match rows")
    if report.max_signal_reversal_magnitude != max(
        (row.signal_reversal_magnitude for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_reversal_magnitude must match rows")
    if report.max_post_resolution_age_hours != max(
        (row.post_resolution_age_hours for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_post_resolution_age_hours must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status" and item not in EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    if frozenset(payload) != REPORT_PAYLOAD_KEYS:
        raise ValueError("payload schema must match report")
    _validate_payload_flags_object("payload", payload)
    _validate_payload_string(
        "config_version",
        payload["config_version"],
        expected=DEFAULT_RESEARCH_EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_REPORT_CONFIG_VERSION,
    )
    _validate_payload_status_value("status", payload["status"])
    _validate_payload_string(
        "report_action",
        payload["report_action"],
        expected=REPORT_ACTION_BY_STATUS[payload["status"]],
    )
    for key in (
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_reversal_decay_score",
        "max_reversal_decay_score",
        "max_signal_reversal_magnitude",
        "max_post_resolution_age_hours",
    ):
        _validate_payload_decimal_string(key, payload[key])
    _validate_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _validate_payload_reason_code_counts(payload["reason_code_counts"])
    _validate_payload_rows(payload["rows"])


def _validate_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows schema must be a list")
    for row in value:
        if type(row) is not dict or frozenset(row) != ROW_PAYLOAD_KEYS:
            raise ValueError("rows schema must match report rows")
        _validate_payload_flags_object("row", row)
        _require_digest("event_digest", row["event_digest"])
        _validate_payload_status_value("status", row["status"])
        _validate_payload_datetime_string("observed_at", row["observed_at"])
        _validate_payload_datetime_string("resolved_at", row["resolved_at"])
        for key in (
            "observation_age_hours",
            "post_resolution_age_hours",
            "signal_reversal_magnitude",
            "evidence_confidence_decay_score",
            "authority_conflict_score",
            "corroboration_count",
            "expected_corroboration_count",
            "corroboration_gap_score",
            "post_resolution_decay_score",
            "reversal_decay_score",
        ):
            _validate_payload_decimal_string(key, row[key])
        _validate_payload_reason_codes(
            "row reason_codes",
            row["reason_codes"],
            ROW_REASON_CODES,
        )


def _validate_payload_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts schema must be a list")
    for item in value:
        if type(item) is not dict or frozenset(item) != REASON_CODE_COUNT_PAYLOAD_KEYS:
            raise ValueError("reason_code_counts schema must match report")
        _validate_payload_flags_object("reason_code_count", item)
        _require_reason_code("reason_code", item["reason_code"], ROW_REASON_CODES)
        _validate_payload_decimal_string("count", item["count"])
        _validate_payload_decimal_string("event_ratio", item["event_ratio"])


def _validate_payload_flags_object(label: str, value: Mapping[str, object]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _validate_payload_status_value(name: str, value: object) -> None:
    if type(value) is not str or value not in EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _validate_payload_string(
    name: str,
    value: object,
    *,
    expected: str | None = None,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if expected is not None and value != expected:
        raise ValueError(f"{name} must match report")


def _validate_payload_datetime_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{name} must be UTC-normalized")


def _validate_payload_decimal_string(name: str, value: object) -> None:
    if type(value) is not str or not PAYLOAD_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a Decimal string")


def _validate_payload_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    normalized = tuple(_require_reason_code(name, item, allowed) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must be unique")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a SHA-256 hex digest")
    expected = _payload_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _report_values_without_digest(
    report: ResearchEventResolutionSignalReversalDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    if type(ready) is not dict:
        raise ValueError("report values must produce a JSON object")
    return _payload_digest(ready)


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _event_digest(private_event_reference: str) -> str:
    return sha256(private_event_reference.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and not isinstance(value, tuple):
            raise ValueError(f"{label} public payload containers must be tuples")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_public_value(value):
        raise ValueError(f"unsafe public payload value in {label}")


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.lower()
    return normalized in UNSAFE_PUBLIC_KEYS or any(
        fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS
    )


def _has_unsafe_public_value(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _has_unsafe_public_value(value):
        raise ValueError(f"{name} must not expose unsafe public surfaces")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in EVENT_RESOLUTION_SIGNAL_REVERSAL_DECAY_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be supported")
    return value


def _require_reason_codes(
    name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, value, allowed) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must be unique")
    return tuple(reason for reason in allowed if reason in set(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, flag_name, None)
        if flag is not True:
            raise ValueError(f"{label} {flag_name} must be True")
        _require_bool(flag_name, flag)


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return decimal_value


def _require_positive_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), ZERO), ONE)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_hours(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    if seconds < ZERO:
        raise ValueError("duration must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(seconds / SECONDS_PER_HOUR)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError("JSON string exposes unsafe public surfaces")
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError("JSON object key exposes unsafe public surfaces")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _public_dataclass_names() -> tuple[str, ...]:
    return tuple(
        name
        for name, value in globals().items()
        if name.startswith("ResearchEventResolutionSignalReversalDecay")
        and isinstance(value, type)
        and is_dataclass(value)
    )


def _assert_public_dataclass_flags() -> None:
    for name in _public_dataclass_names():
        cls = globals()[name]
        field_names = {field.name for field in fields(cls)}
        if {"paper_only", "report_only", "readonly"} - field_names:
            raise RuntimeError(f"{name} must expose hard report-only flags")


_assert_public_dataclass_flags()
