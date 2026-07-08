"""Pure report-only policy-event signal tracker for caller-supplied evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_POLICY_EVENT_SIGNAL_TRACKER_CONFIG_VERSION = (
    "research-policy-event-signal-tracker-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = frozenset(("pass", "watch", "block"))
_SOURCE_TYPES = frozenset(("official", "primary", "secondary"))
_NODE_TYPES = frozenset(("official_schedule", "vote", "court", "regulatory"))
_MILESTONE_NODE_TYPES = frozenset(("vote", "court", "regulatory"))
_EVIDENCE_STANCES = frozenset(("supporting", "neutral", "counter"))
_SETTLEMENT_CLARITIES = frozenset(("clear", "ambiguous"))
_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "source_" + "u" + "rl",
    "source_" + "te" + "xt",
    "raw_" + "market_" + "question",
    "market_" + "question",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
)
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "official_schedule_present",
    "missing_official_schedule",
    "vote_court_regulatory_node_present",
    "missing_vote_court_regulatory_node",
    "source_independence_met",
    "insufficient_source_independence",
    "fresh_source_context",
    "stale_source_context",
    "no_counter_evidence",
    "counter_evidence_present",
    "settlement_terms_clear",
    "settlement_ambiguity_present",
    "policy_event_signal_pass",
    "policy_event_signal_watch",
    "policy_event_signal_block",
)


@dataclass(frozen=True)
class ResearchPolicyEventSignalTrackerConfig:
    config_version: str = DEFAULT_RESEARCH_POLICY_EVENT_SIGNAL_TRACKER_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("86400.000000")
    stale_age_seconds: Decimal = Decimal("604800.000000")
    min_independent_source_family_count: Decimal = Decimal("2.000000")
    min_milestone_node_count: Decimal = Decimal("1.000000")
    block_counter_evidence_count: Decimal = Decimal("2.000000")
    pass_signal_score: Decimal = Decimal("0.750000")
    watch_signal_score: Decimal = Decimal("0.400000")
    official_schedule_weight: Decimal = Decimal("0.300000")
    milestone_node_weight: Decimal = Decimal("0.250000")
    source_independence_weight: Decimal = Decimal("0.250000")
    recency_weight: Decimal = Decimal("0.200000")
    counter_evidence_penalty: Decimal = Decimal("0.350000")
    settlement_ambiguity_penalty: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPolicyEventSignalTrackerConfig:
            raise TypeError(
                "ResearchPolicyEventSignalTrackerConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPolicyEventSignalTrackerConfig:
            raise ValueError("config must be exactly ResearchPolicyEventSignalTrackerConfig")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_POLICY_EVENT_SIGNAL_TRACKER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "min_independent_source_family_count",
            "min_milestone_node_count",
            "block_counter_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_signal_score",
            "watch_signal_score",
            "official_schedule_weight",
            "milestone_node_weight",
            "source_independence_weight",
            "recency_weight",
            "counter_evidence_penalty",
            "settlement_ambiguity_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_signal_score <= self.watch_signal_score:
            raise ValueError("pass_signal_score must exceed watch_signal_score")
        weight_total = _quantize(
            self.official_schedule_weight
            + self.milestone_node_weight
            + self.source_independence_weight
            + self.recency_weight,
        )
        if weight_total != _ONE:
            raise ValueError("signal component weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPolicyEventSignalTrackerEvidence:
    signal_id: str
    evidence_id: str
    source_id: str
    source_family: str
    source_type: str
    node_type: str
    evidence_stance: str
    observed_at: datetime
    scheduled_event_at: datetime | None = None
    settlement_clarity: str = "clear"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPolicyEventSignalTrackerEvidence:
            raise TypeError(
                "ResearchPolicyEventSignalTrackerEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPolicyEventSignalTrackerEvidence:
            raise ValueError(
                "evidence must be exactly ResearchPolicyEventSignalTrackerEvidence",
            )
        for field_name in ("signal_id", "evidence_id", "source_id", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("source_type", self.source_type, _SOURCE_TYPES)
        _require_member("node_type", self.node_type, _NODE_TYPES)
        _require_member("evidence_stance", self.evidence_stance, _EVIDENCE_STANCES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_event_at",
            _as_optional_utc("scheduled_event_at", self.scheduled_event_at),
        )
        _require_member(
            "settlement_clarity",
            self.settlement_clarity,
            _SETTLEMENT_CLARITIES,
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPolicyEventSignalTrackerRow:
    signal_id: str
    evidence_count: Decimal
    source_count: Decimal
    source_family_count: Decimal
    official_schedule_count: Decimal
    milestone_node_count: Decimal
    vote_node_count: Decimal
    court_node_count: Decimal
    regulatory_node_count: Decimal
    counter_evidence_count: Decimal
    settlement_ambiguity_count: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    recency_score: Decimal
    official_schedule_score: Decimal
    milestone_node_score: Decimal
    source_independence_score: Decimal
    counter_evidence_penalty_score: Decimal
    settlement_ambiguity_penalty_score: Decimal
    signal_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPolicyEventSignalTrackerRow:
            raise TypeError(
                "ResearchPolicyEventSignalTrackerRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPolicyEventSignalTrackerRow:
            raise ValueError("row must be exactly ResearchPolicyEventSignalTrackerRow")
        _require_public_identifier("signal_id", self.signal_id)
        for field_name in (
            "evidence_count",
            "source_count",
            "source_family_count",
            "official_schedule_count",
            "milestone_node_count",
            "vote_node_count",
            "court_node_count",
            "regulatory_node_count",
            "counter_evidence_count",
            "settlement_ambiguity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "recency_score",
            "official_schedule_score",
            "milestone_node_score",
            "source_independence_score",
            "counter_evidence_penalty_score",
            "settlement_ambiguity_penalty_score",
            "signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPolicyEventSignalTrackerReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPolicyEventSignalTrackerReasonCodeCount:
            raise TypeError(
                "ResearchPolicyEventSignalTrackerReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPolicyEventSignalTrackerReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPolicyEventSignalTrackerReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchPolicyEventSignalTrackerReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_signal_score: Decimal
    status: str
    rows: tuple[ResearchPolicyEventSignalTrackerRow, ...]
    reason_code_counts: tuple[ResearchPolicyEventSignalTrackerReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPolicyEventSignalTrackerReport:
            raise TypeError(
                "ResearchPolicyEventSignalTrackerReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPolicyEventSignalTrackerReport:
            raise ValueError("report must be exactly ResearchPolicyEventSignalTrackerReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_POLICY_EVENT_SIGNAL_TRACKER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "signal_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_signal_score",
            _require_ratio_decimal("average_signal_score", self.average_signal_score),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_policy_event_signal_tracker_report(
    evidence: Sequence[ResearchPolicyEventSignalTrackerEvidence],
    *,
    generated_at: datetime,
    config: ResearchPolicyEventSignalTrackerConfig | None = None,
) -> ResearchPolicyEventSignalTrackerReport:
    """Build a deterministic local report for policy-event tracking signals."""

    if config is None:
        config = ResearchPolicyEventSignalTrackerConfig()
    if type(config) is not ResearchPolicyEventSignalTrackerConfig:
        raise ValueError("config must be a ResearchPolicyEventSignalTrackerConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    rows = _build_rows(normalized_evidence, config, generated_at)
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "signal_count": _decimal_count(len(rows)),
        "evidence_count": sum((row.evidence_count for row in rows), _ZERO),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_signal_score": _average(tuple(row.signal_score for row in rows)),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPolicyEventSignalTrackerReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_policy_event_signal_tracker_report_payload(
    report: ResearchPolicyEventSignalTrackerReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPolicyEventSignalTrackerReport:
        raise ValueError("report must be a ResearchPolicyEventSignalTrackerReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(
        "research policy event signal tracker payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_rows(
    evidence: tuple[ResearchPolicyEventSignalTrackerEvidence, ...],
    config: ResearchPolicyEventSignalTrackerConfig,
    generated_at: datetime,
) -> tuple[ResearchPolicyEventSignalTrackerRow, ...]:
    grouped: dict[str, list[ResearchPolicyEventSignalTrackerEvidence]] = {}
    for item in evidence:
        grouped.setdefault(item.signal_id, []).append(item)
    return tuple(
        _row_for_signal(
            signal_id=signal_id,
            evidence=tuple(grouped[signal_id]),
            config=config,
            generated_at=generated_at,
        )
        for signal_id in sorted(grouped)
    )


def _row_for_signal(
    *,
    signal_id: str,
    evidence: tuple[ResearchPolicyEventSignalTrackerEvidence, ...],
    config: ResearchPolicyEventSignalTrackerConfig,
    generated_at: datetime,
) -> ResearchPolicyEventSignalTrackerRow:
    ordered = tuple(
        sorted(
            evidence,
            key=lambda item: (item.evidence_id, item.observed_at, item.source_id),
        ),
    )
    latest = max(ordered, key=lambda item: item.observed_at)
    latest_age = _age_seconds(generated_at, latest.observed_at)
    official_schedule_count = _decimal_count(
        sum(
            1
            for item in ordered
            if item.node_type == "official_schedule" and item.source_type == "official"
        ),
    )
    vote_node_count = _decimal_count(sum(1 for item in ordered if item.node_type == "vote"))
    court_node_count = _decimal_count(sum(1 for item in ordered if item.node_type == "court"))
    regulatory_node_count = _decimal_count(
        sum(1 for item in ordered if item.node_type == "regulatory"),
    )
    milestone_node_count = _quantize(
        vote_node_count + court_node_count + regulatory_node_count,
    )
    source_count = _decimal_count(len({item.source_id for item in ordered}))
    source_family_count = _decimal_count(len({item.source_family for item in ordered}))
    counter_evidence_count = _decimal_count(
        sum(1 for item in ordered if item.evidence_stance == "counter"),
    )
    settlement_ambiguity_count = _decimal_count(
        sum(1 for item in ordered if item.settlement_clarity == "ambiguous"),
    )
    recency_score = _recency_score(
        latest_age,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
    )
    official_schedule_score = _present_score(official_schedule_count)
    milestone_node_score = _threshold_score(
        milestone_node_count,
        config.min_milestone_node_count,
    )
    source_independence_score = _threshold_score(
        source_family_count,
        config.min_independent_source_family_count,
    )
    counter_evidence_penalty_score = _clamp_ratio(
        counter_evidence_count * config.counter_evidence_penalty,
    )
    settlement_ambiguity_penalty_score = _clamp_ratio(
        settlement_ambiguity_count * config.settlement_ambiguity_penalty,
    )
    signal_score = _signal_score(
        recency_score=recency_score,
        official_schedule_score=official_schedule_score,
        milestone_node_score=milestone_node_score,
        source_independence_score=source_independence_score,
        counter_evidence_penalty_score=counter_evidence_penalty_score,
        settlement_ambiguity_penalty_score=settlement_ambiguity_penalty_score,
        config=config,
    )
    status = _row_status(
        official_schedule_count=official_schedule_count,
        milestone_node_count=milestone_node_count,
        source_family_count=source_family_count,
        counter_evidence_count=counter_evidence_count,
        settlement_ambiguity_count=settlement_ambiguity_count,
        latest_source_age_seconds=latest_age,
        signal_score=signal_score,
        config=config,
    )
    return ResearchPolicyEventSignalTrackerRow(
        signal_id=signal_id,
        evidence_count=_decimal_count(len(ordered)),
        source_count=source_count,
        source_family_count=source_family_count,
        official_schedule_count=official_schedule_count,
        milestone_node_count=milestone_node_count,
        vote_node_count=vote_node_count,
        court_node_count=court_node_count,
        regulatory_node_count=regulatory_node_count,
        counter_evidence_count=counter_evidence_count,
        settlement_ambiguity_count=settlement_ambiguity_count,
        latest_observed_at=latest.observed_at,
        latest_source_age_seconds=latest_age,
        recency_score=recency_score,
        official_schedule_score=official_schedule_score,
        milestone_node_score=milestone_node_score,
        source_independence_score=source_independence_score,
        counter_evidence_penalty_score=counter_evidence_penalty_score,
        settlement_ambiguity_penalty_score=settlement_ambiguity_penalty_score,
        signal_score=signal_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            official_schedule_count=official_schedule_count,
            milestone_node_count=milestone_node_count,
            source_family_count=source_family_count,
            counter_evidence_count=counter_evidence_count,
            settlement_ambiguity_count=settlement_ambiguity_count,
            latest_source_age_seconds=latest_age,
            config=config,
        ),
    )


def _signal_score(
    *,
    recency_score: Decimal,
    official_schedule_score: Decimal,
    milestone_node_score: Decimal,
    source_independence_score: Decimal,
    counter_evidence_penalty_score: Decimal,
    settlement_ambiguity_penalty_score: Decimal,
    config: ResearchPolicyEventSignalTrackerConfig,
) -> Decimal:
    raw_score = (
        official_schedule_score * config.official_schedule_weight
        + milestone_node_score * config.milestone_node_weight
        + source_independence_score * config.source_independence_weight
        + recency_score * config.recency_weight
        - counter_evidence_penalty_score
        - settlement_ambiguity_penalty_score
    )
    return _clamp_ratio(raw_score)


def _row_status(
    *,
    official_schedule_count: Decimal,
    milestone_node_count: Decimal,
    source_family_count: Decimal,
    counter_evidence_count: Decimal,
    settlement_ambiguity_count: Decimal,
    latest_source_age_seconds: Decimal,
    signal_score: Decimal,
    config: ResearchPolicyEventSignalTrackerConfig,
) -> str:
    if settlement_ambiguity_count > _ZERO:
        return "block"
    if counter_evidence_count >= config.block_counter_evidence_count:
        return "block"
    if official_schedule_count == _ZERO and milestone_node_count == _ZERO:
        return "block"
    if signal_score < config.watch_signal_score:
        return "block"
    if (
        signal_score >= config.pass_signal_score
        and official_schedule_count > _ZERO
        and milestone_node_count >= config.min_milestone_node_count
        and source_family_count >= config.min_independent_source_family_count
        and counter_evidence_count == _ZERO
        and latest_source_age_seconds < config.stale_age_seconds
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    official_schedule_count: Decimal,
    milestone_node_count: Decimal,
    source_family_count: Decimal,
    counter_evidence_count: Decimal,
    settlement_ambiguity_count: Decimal,
    latest_source_age_seconds: Decimal,
    config: ResearchPolicyEventSignalTrackerConfig,
) -> tuple[str, ...]:
    reason_codes = [
        (
            "official_schedule_present"
            if official_schedule_count > _ZERO
            else "missing_official_schedule"
        ),
        (
            "vote_court_regulatory_node_present"
            if milestone_node_count >= config.min_milestone_node_count
            else "missing_vote_court_regulatory_node"
        ),
        (
            "source_independence_met"
            if source_family_count >= config.min_independent_source_family_count
            else "insufficient_source_independence"
        ),
        (
            "stale_source_context"
            if latest_source_age_seconds >= config.stale_age_seconds
            else "fresh_source_context"
        ),
        (
            "counter_evidence_present"
            if counter_evidence_count > _ZERO
            else "no_counter_evidence"
        ),
        (
            "settlement_ambiguity_present"
            if settlement_ambiguity_count > _ZERO
            else "settlement_terms_clear"
        ),
        f"policy_event_signal_{status}",
    ]
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchPolicyEventSignalTrackerRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPolicyEventSignalTrackerRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    if all(row.status == "pass" for row in rows):
        return ("policy_event_signal_pass",)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _reason_code_counts(
    rows: tuple[ResearchPolicyEventSignalTrackerRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchPolicyEventSignalTrackerReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPolicyEventSignalTrackerReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchPolicyEventSignalTrackerReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _status_count(
    rows: tuple[ResearchPolicyEventSignalTrackerRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_evidence(
    evidence: Sequence[ResearchPolicyEventSignalTrackerEvidence],
) -> tuple[ResearchPolicyEventSignalTrackerEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchPolicyEventSignalTrackerEvidence] = []
    for item in evidence:
        if type(item) is not ResearchPolicyEventSignalTrackerEvidence:
            raise ValueError(
                "evidence items must be ResearchPolicyEventSignalTrackerEvidence",
            )
        _require_hard_flags("evidence", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.signal_id, item.evidence_id, item.observed_at),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchPolicyEventSignalTrackerRow],
) -> tuple[ResearchPolicyEventSignalTrackerRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPolicyEventSignalTrackerRow:
            raise ValueError("rows must contain ResearchPolicyEventSignalTrackerRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.signal_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by signal_id")
    return rows


def _normalize_reason_code_counts(
    counts: Sequence[ResearchPolicyEventSignalTrackerReasonCodeCount],
) -> tuple[ResearchPolicyEventSignalTrackerReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchPolicyEventSignalTrackerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPolicyEventSignalTrackerReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(
        sorted(
            counts,
            key=lambda count: _REASON_CODE_SEQUENCE.index(count.reason_code),
        ),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchPolicyEventSignalTrackerRow) -> None:
    if row.evidence_count <= _ZERO:
        raise ValueError("evidence_count must be positive")
    if row.source_count > row.evidence_count:
        raise ValueError("source_count must not exceed evidence_count")
    if row.source_family_count > row.evidence_count:
        raise ValueError("source_family_count must not exceed evidence_count")
    if row.official_schedule_count > row.evidence_count:
        raise ValueError("official_schedule_count must not exceed evidence_count")
    if row.milestone_node_count > row.evidence_count:
        raise ValueError("milestone_node_count must not exceed evidence_count")
    if row.vote_node_count + row.court_node_count + row.regulatory_node_count != (
        row.milestone_node_count
    ):
        raise ValueError("milestone_node_count must match node counts")
    if row.counter_evidence_count > row.evidence_count:
        raise ValueError("counter_evidence_count must not exceed evidence_count")
    if row.settlement_ambiguity_count > row.evidence_count:
        raise ValueError("settlement_ambiguity_count must not exceed evidence_count")
    status_reason_code = f"policy_event_signal_{row.status}"
    if status_reason_code not in row.reason_codes:
        raise ValueError("row status must be represented in reason_codes")
    if row.status == "pass" and (
        "missing_official_schedule" in row.reason_codes
        or "missing_vote_court_regulatory_node" in row.reason_codes
        or "insufficient_source_independence" in row.reason_codes
        or "counter_evidence_present" in row.reason_codes
        or "settlement_ambiguity_present" in row.reason_codes
    ):
        raise ValueError("pass rows must not contain blocking or watch reason codes")
    if row.status == "block" and row.signal_score >= Decimal("0.950000"):
        raise ValueError("block rows must not have near-certain signal scores")


def _validate_report_consistency(report: ResearchPolicyEventSignalTrackerReport) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), _ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_signal_score != _average(tuple(row.signal_score for row in report.rows)):
        raise ValueError("average_signal_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _require_nonnegative_decimal("source age seconds", seconds)


def _recency_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return _ONE
    if age_seconds >= stale_age_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (age_seconds / stale_age_seconds))


def _present_score(count: Decimal) -> Decimal:
    return _ONE if count > _ZERO else _ZERO


def _threshold_score(count: Decimal, threshold: Decimal) -> Decimal:
    return _clamp_ratio(count / threshold)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(allowed))}")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
            _reject_unsafe_public_payload(
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
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _report_values_without_digest(
    report: ResearchPolicyEventSignalTrackerReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived validation payload",
        payload,
        allow_json_containers=True,
    )
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
    if type(value) is int or type(value) is float:
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


__all__ = (
    "DEFAULT_RESEARCH_POLICY_EVENT_SIGNAL_TRACKER_CONFIG_VERSION",
    "ResearchPolicyEventSignalTrackerConfig",
    "ResearchPolicyEventSignalTrackerEvidence",
    "ResearchPolicyEventSignalTrackerReasonCodeCount",
    "ResearchPolicyEventSignalTrackerReport",
    "ResearchPolicyEventSignalTrackerRow",
    "build_research_policy_event_signal_tracker_report",
    "research_policy_event_signal_tracker_report_payload",
)
