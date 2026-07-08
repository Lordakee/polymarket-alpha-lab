"""Pure outcome revision risk report for settled or near-settlement events."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import re
from typing import Any


__all__ = (
    "ResearchOutcomeRevisionRiskConfig",
    "ResearchOutcomeRevisionRiskObservation",
    "ResearchOutcomeRevisionRiskReasonCodeCount",
    "ResearchOutcomeRevisionRiskReport",
    "ResearchOutcomeRevisionRiskRow",
    "build_research_outcome_revision_risk_report",
    "research_outcome_revision_risk_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-outcome-revision-risk-report-v0"
STATUSES = ("pass", "watch", "block")
LIFECYCLE_STAGES = ("settled", "near_settlement")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=28)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "r" + "aw",
    "mar" + "ket",
    "sou" + "rce",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "://",
    "@",
    "?",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchOutcomeRevisionRiskConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    near_settlement_seconds: Decimal = Decimal("86400")
    watch_evidence_update_count: Decimal = Decimal("1")
    block_contradicting_update_count: Decimal = Decimal("1")
    min_reliability_score: Decimal = Decimal("0.700000")
    block_reliability_score: Decimal = Decimal("0.400000")
    watch_postmortem_impact_score: Decimal = Decimal("0.400000")
    high_postmortem_impact_score: Decimal = Decimal("0.700000")
    watch_revision_risk_score: Decimal = Decimal("0.300000")
    block_revision_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeRevisionRiskConfig:
            raise TypeError("ResearchOutcomeRevisionRiskConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeRevisionRiskConfig:
            raise ValueError("config must be exactly ResearchOutcomeRevisionRiskConfig")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "near_settlement_seconds",
            _require_positive_decimal("near_settlement_seconds", self.near_settlement_seconds),
        )
        for field_name in ("watch_evidence_update_count", "block_contradicting_update_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_reliability_score",
            "block_reliability_score",
            "watch_postmortem_impact_score",
            "high_postmortem_impact_score",
            "watch_revision_risk_score",
            "block_revision_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_reliability_score < self.block_reliability_score:
            raise ValueError("min_reliability_score must be >= block_reliability_score")
        if self.high_postmortem_impact_score < self.watch_postmortem_impact_score:
            raise ValueError(
                "high_postmortem_impact_score must be >= watch_postmortem_impact_score",
            )
        if self.block_revision_risk_score < self.watch_revision_risk_score:
            raise ValueError("block_revision_risk_score must be >= watch_revision_risk_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchOutcomeRevisionRiskObservation:
    event_id: str
    outcome_id: str
    observation_id: str
    lifecycle_stage: str
    observed_at: datetime
    settlement_at: datetime | None
    expected_settlement_at: datetime | None
    dispute_window_ends_at: datetime | None
    evidence_update_count: Decimal = Decimal("0")
    contradicting_evidence_update_count: Decimal = Decimal("0")
    evidence_reliability_score: Decimal = Decimal("0.800000")
    postmortem_impact_score: Decimal = Decimal("0.000000")
    memory_update_needed: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeRevisionRiskObservation:
            raise TypeError(
                "ResearchOutcomeRevisionRiskObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeRevisionRiskObservation:
            raise ValueError(
                "observation must be exactly ResearchOutcomeRevisionRiskObservation",
            )
        for field_name in ("event_id", "outcome_id", "observation_id"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_enum("lifecycle_stage", self.lifecycle_stage, LIFECYCLE_STAGES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_at",
            _as_optional_utc("settlement_at", self.settlement_at),
        )
        object.__setattr__(
            self,
            "expected_settlement_at",
            _as_optional_utc("expected_settlement_at", self.expected_settlement_at),
        )
        object.__setattr__(
            self,
            "dispute_window_ends_at",
            _as_optional_utc("dispute_window_ends_at", self.dispute_window_ends_at),
        )
        if self.lifecycle_stage == "settled":
            if self.settlement_at is None:
                raise ValueError("settlement_at is required for settled observations")
            if self.expected_settlement_at is not None:
                raise ValueError("expected_settlement_at must be None for settled observations")
            if self.settlement_at > self.observed_at:
                raise ValueError("settlement_at must be <= observed_at")
        if self.lifecycle_stage == "near_settlement":
            if self.settlement_at is not None:
                raise ValueError("settlement_at must be None for near_settlement observations")
            if self.expected_settlement_at is None:
                raise ValueError(
                    "expected_settlement_at is required for near_settlement observations",
                )
            if self.expected_settlement_at < self.observed_at:
                raise ValueError("expected_settlement_at must be >= observed_at")
        if self.dispute_window_ends_at is not None:
            anchor = self.settlement_at or self.expected_settlement_at
            if anchor is not None and self.dispute_window_ends_at < anchor:
                raise ValueError("dispute_window_ends_at must be >= settlement anchor")
        for field_name in ("evidence_update_count", "contradicting_evidence_update_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradicting_evidence_update_count > self.evidence_update_count:
            raise ValueError(
                "contradicting_evidence_update_count must be <= evidence_update_count",
            )
        for field_name in ("evidence_reliability_score", "postmortem_impact_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("memory_update_needed", self.memory_update_needed)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchOutcomeRevisionRiskRow:
    event_id: str
    outcome_id: str
    observation_count: Decimal
    settled_observation_count: Decimal
    near_settlement_observation_count: Decimal
    active_dispute_window_count: Decimal
    evidence_update_count: Decimal
    contradicting_evidence_update_count: Decimal
    memory_update_needed_count: Decimal
    evidence_reliability_score: Decimal
    postmortem_impact_score: Decimal
    revision_risk_score: Decimal
    latest_observed_at: datetime
    observation_ids: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeRevisionRiskRow:
            raise TypeError("ResearchOutcomeRevisionRiskRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeRevisionRiskRow:
            raise ValueError("row must be exactly ResearchOutcomeRevisionRiskRow")
        for field_name in ("event_id", "outcome_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "settled_observation_count",
            "near_settlement_observation_count",
            "active_dispute_window_count",
            "evidence_update_count",
            "contradicting_evidence_update_count",
            "memory_update_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_reliability_score",
            "postmortem_impact_score",
            "revision_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "observation_ids",
            _normalize_string_tuple("observation_ids", self.observation_ids, allow_empty=False),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchOutcomeRevisionRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeRevisionRiskReasonCodeCount:
            raise TypeError(
                "ResearchOutcomeRevisionRiskReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeRevisionRiskReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly ResearchOutcomeRevisionRiskReasonCodeCount",
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
class ResearchOutcomeRevisionRiskReport:
    generated_at: datetime
    config_version: str
    event_outcome_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_update_needed_count: Decimal
    status: str
    rows: tuple[ResearchOutcomeRevisionRiskRow, ...]
    reason_code_counts: tuple[ResearchOutcomeRevisionRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeRevisionRiskReport:
            raise TypeError("ResearchOutcomeRevisionRiskReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeRevisionRiskReport:
            raise ValueError("report must be exactly ResearchOutcomeRevisionRiskReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_outcome_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "memory_update_needed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)


def build_research_outcome_revision_risk_report(
    observations: Iterable[object],
    *,
    config: ResearchOutcomeRevisionRiskConfig,
    generated_at: datetime,
) -> ResearchOutcomeRevisionRiskReport:
    if type(config) is not ResearchOutcomeRevisionRiskConfig:
        raise ValueError("config must be a ResearchOutcomeRevisionRiskConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    for item in observation_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be <= generated_at")
        if item.settlement_at is not None and item.settlement_at > generated_at_utc:
            raise ValueError("settlement_at must be <= generated_at")

    grouped: dict[tuple[str, str], list[ResearchOutcomeRevisionRiskObservation]] = {}
    for item in observation_items:
        grouped.setdefault((item.event_id, item.outcome_id), []).append(item)

    rows = tuple(
        _row_from_observations(
            event_id=event_id,
            outcome_id=outcome_id,
            observations=tuple(grouped[(event_id, outcome_id)]),
            config=config,
            generated_at=generated_at_utc,
        )
        for event_id, outcome_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchOutcomeRevisionRiskReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_outcome_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        memory_update_needed_count=sum(
            (row.memory_update_needed_count for row in rows),
            ZERO,
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_outcome_revision_risk_report_payload(
    report: ResearchOutcomeRevisionRiskReport,
) -> dict[str, Any]:
    if type(report) is not ResearchOutcomeRevisionRiskReport:
        raise ValueError("report must be a ResearchOutcomeRevisionRiskReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    return payload


def _row_from_observations(
    *,
    event_id: str,
    outcome_id: str,
    observations: tuple[ResearchOutcomeRevisionRiskObservation, ...],
    config: ResearchOutcomeRevisionRiskConfig,
    generated_at: datetime,
) -> ResearchOutcomeRevisionRiskRow:
    ordered = tuple(sorted(observations, key=lambda item: item.observation_id))
    observation_count = _decimal_count(len(ordered))
    settled_count = _decimal_count(sum(1 for item in ordered if item.lifecycle_stage == "settled"))
    near_count = _decimal_count(
        sum(1 for item in ordered if item.lifecycle_stage == "near_settlement"),
    )
    active_dispute_count = _decimal_count(
        sum(1 for item in ordered if _dispute_window_is_active(item, generated_at)),
    )
    evidence_update_count = sum((item.evidence_update_count for item in ordered), ZERO)
    contradicting_update_count = sum(
        (item.contradicting_evidence_update_count for item in ordered),
        ZERO,
    )
    memory_update_needed_count = _decimal_count(
        sum(1 for item in ordered if item.memory_update_needed),
    )
    reliability_score = _average_probability(
        tuple(item.evidence_reliability_score for item in ordered),
    )
    postmortem_impact_score = max(item.postmortem_impact_score for item in ordered)
    revision_risk_score = _revision_risk_score(
        observation_count=observation_count,
        active_dispute_window_count=active_dispute_count,
        evidence_update_count=evidence_update_count,
        contradicting_evidence_update_count=contradicting_update_count,
        evidence_reliability_score=reliability_score,
        postmortem_impact_score=postmortem_impact_score,
        memory_update_needed_count=memory_update_needed_count,
        config=config,
    )
    status = _row_status(
        near_settlement_observation_count=near_count,
        active_dispute_window_count=active_dispute_count,
        evidence_update_count=evidence_update_count,
        contradicting_evidence_update_count=contradicting_update_count,
        evidence_reliability_score=reliability_score,
        postmortem_impact_score=postmortem_impact_score,
        memory_update_needed_count=memory_update_needed_count,
        revision_risk_score=revision_risk_score,
        config=config,
    )

    reason_codes = _row_reason_codes(
        observations=ordered,
        settled_observation_count=settled_count,
        near_settlement_observation_count=near_count,
        active_dispute_window_count=active_dispute_count,
        evidence_update_count=evidence_update_count,
        contradicting_evidence_update_count=contradicting_update_count,
        memory_update_needed_count=memory_update_needed_count,
        evidence_reliability_score=reliability_score,
        postmortem_impact_score=postmortem_impact_score,
        revision_risk_score=revision_risk_score,
        status=status,
        config=config,
    )

    return ResearchOutcomeRevisionRiskRow(
        event_id=event_id,
        outcome_id=outcome_id,
        observation_count=observation_count,
        settled_observation_count=settled_count,
        near_settlement_observation_count=near_count,
        active_dispute_window_count=active_dispute_count,
        evidence_update_count=evidence_update_count,
        contradicting_evidence_update_count=contradicting_update_count,
        memory_update_needed_count=memory_update_needed_count,
        evidence_reliability_score=reliability_score,
        postmortem_impact_score=postmortem_impact_score,
        revision_risk_score=revision_risk_score,
        latest_observed_at=max(item.observed_at for item in ordered),
        observation_ids=tuple(item.observation_id for item in ordered),
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    near_settlement_observation_count: Decimal,
    active_dispute_window_count: Decimal,
    evidence_update_count: Decimal,
    contradicting_evidence_update_count: Decimal,
    evidence_reliability_score: Decimal,
    postmortem_impact_score: Decimal,
    memory_update_needed_count: Decimal,
    revision_risk_score: Decimal,
    config: ResearchOutcomeRevisionRiskConfig,
) -> str:
    if (
        contradicting_evidence_update_count >= config.block_contradicting_update_count
        or evidence_reliability_score < config.block_reliability_score
        or revision_risk_score >= config.block_revision_risk_score
        or (
            active_dispute_window_count > ZERO
            and postmortem_impact_score >= config.high_postmortem_impact_score
        )
    ):
        return "block"
    if (
        near_settlement_observation_count > ZERO
        or active_dispute_window_count > ZERO
        or evidence_update_count >= config.watch_evidence_update_count
        or evidence_reliability_score < config.min_reliability_score
        or postmortem_impact_score >= config.watch_postmortem_impact_score
        or memory_update_needed_count > ZERO
        or revision_risk_score >= config.watch_revision_risk_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observations: tuple[ResearchOutcomeRevisionRiskObservation, ...],
    settled_observation_count: Decimal,
    near_settlement_observation_count: Decimal,
    active_dispute_window_count: Decimal,
    evidence_update_count: Decimal,
    contradicting_evidence_update_count: Decimal,
    memory_update_needed_count: Decimal,
    evidence_reliability_score: Decimal,
    postmortem_impact_score: Decimal,
    revision_risk_score: Decimal,
    status: str,
    config: ResearchOutcomeRevisionRiskConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for item in observations:
        reason_codes.extend(f"input_{reason_code}" for reason_code in item.reason_codes)
    if settled_observation_count > ZERO:
        reason_codes.append("settled_event")
    if near_settlement_observation_count > ZERO:
        reason_codes.append("near_settlement_event")
    reason_codes.append(
        "dispute_window_active"
        if active_dispute_window_count > ZERO
        else "dispute_window_clear",
    )
    if evidence_update_count >= config.watch_evidence_update_count:
        reason_codes.append("evidence_update_present")
    else:
        reason_codes.append("evidence_update_clear")
    if contradicting_evidence_update_count >= config.block_contradicting_update_count:
        reason_codes.append("contradicting_evidence_update")
    if evidence_reliability_score < config.block_reliability_score:
        reason_codes.append("evidence_reliability_block")
    elif evidence_reliability_score < config.min_reliability_score:
        reason_codes.append("evidence_reliability_watch")
    else:
        reason_codes.append("evidence_reliability_pass")
    if postmortem_impact_score >= config.high_postmortem_impact_score:
        reason_codes.append("postmortem_impact_block")
    elif postmortem_impact_score >= config.watch_postmortem_impact_score:
        reason_codes.append("postmortem_impact_watch")
    else:
        reason_codes.append("postmortem_impact_low")
    reason_codes.append(
        "memory_update_needed"
        if memory_update_needed_count > ZERO
        else "memory_update_not_needed",
    )
    if revision_risk_score >= config.block_revision_risk_score:
        reason_codes.append("revision_risk_score_block")
    elif revision_risk_score >= config.watch_revision_risk_score:
        reason_codes.append("revision_risk_score_watch")
    else:
        reason_codes.append("revision_risk_score_low")
    reason_codes.append(f"outcome_revision_risk_{status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _revision_risk_score(
    *,
    observation_count: Decimal,
    active_dispute_window_count: Decimal,
    evidence_update_count: Decimal,
    contradicting_evidence_update_count: Decimal,
    evidence_reliability_score: Decimal,
    postmortem_impact_score: Decimal,
    memory_update_needed_count: Decimal,
    config: ResearchOutcomeRevisionRiskConfig,
) -> Decimal:
    dispute_component = _quantize(
        _ratio(active_dispute_window_count, observation_count) * Decimal("0.200000"),
    )
    update_denominator = observation_count * config.watch_evidence_update_count
    update_component = _quantize(
        min(_ratio(evidence_update_count, update_denominator), ONE) * Decimal("0.150000"),
    )
    contradiction_component = _quantize(
        min(
            _ratio(
                contradicting_evidence_update_count,
                config.block_contradicting_update_count,
            ),
            ONE,
        )
        * Decimal("0.250000"),
    )
    reliability_component = _quantize(
        (ONE - evidence_reliability_score) * Decimal("0.200000"),
    )
    postmortem_component = _quantize(postmortem_impact_score * Decimal("0.150000"))
    memory_component = _quantize(
        _ratio(memory_update_needed_count, observation_count) * Decimal("0.050000"),
    )
    return min(
        _quantize(
            dispute_component
            + update_component
            + contradiction_component
            + reliability_component
            + postmortem_component
            + memory_component,
        ),
        ONE.quantize(RATIO_QUANTUM),
    )


def _summary_status(rows: tuple[ResearchOutcomeRevisionRiskRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(rows: tuple[ResearchOutcomeRevisionRiskRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_outcome_revision_observations",)
    return (f"outcome_revision_risk_{_summary_status(rows)}",)


def _reason_code_counts(
    rows: tuple[ResearchOutcomeRevisionRiskRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchOutcomeRevisionRiskReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchOutcomeRevisionRiskReasonCodeCount(
                reason_code=reason_code,
                count=Decimal("1"),
            )
            for reason_code in report_reason_codes
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchOutcomeRevisionRiskReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchOutcomeRevisionRiskObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable of observation objects")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observation objects") from exc
    return tuple(_coerce_observation(value) for value in items)


def _coerce_observation(value: object) -> ResearchOutcomeRevisionRiskObservation:
    if type(value) is ResearchOutcomeRevisionRiskObservation:
        return value
    if isinstance(value, Mapping):
        _reject_unsafe_public_payload("observation", value, allow_json_containers=True)
    return ResearchOutcomeRevisionRiskObservation(
        event_id=_field_value(value, "event_id"),
        outcome_id=_field_value(value, "outcome_id"),
        observation_id=_field_value(value, "observation_id"),
        lifecycle_stage=_field_value(value, "lifecycle_stage"),
        observed_at=_field_value(value, "observed_at"),
        settlement_at=_field_value(value, "settlement_at"),
        expected_settlement_at=_field_value(value, "expected_settlement_at"),
        dispute_window_ends_at=_field_value(value, "dispute_window_ends_at"),
        evidence_update_count=_field_value(
            value,
            "evidence_update_count",
            default=Decimal("0"),
        ),
        contradicting_evidence_update_count=_field_value(
            value,
            "contradicting_evidence_update_count",
            default=Decimal("0"),
        ),
        evidence_reliability_score=_field_value(
            value,
            "evidence_reliability_score",
            default=Decimal("0.800000"),
        ),
        postmortem_impact_score=_field_value(
            value,
            "postmortem_impact_score",
            default=Decimal("0.000000"),
        ),
        memory_update_needed=_field_value(value, "memory_update_needed", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only", default=True),
        report_only=_field_value(value, "report_only", default=True),
        readonly=_field_value(value, "readonly", default=True),
    )


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> Any:
    if isinstance(value, Mapping) and field_name in value:
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _dispute_window_is_active(
    item: ResearchOutcomeRevisionRiskObservation,
    generated_at: datetime,
) -> bool:
    return item.dispute_window_ends_at is not None and generated_at <= item.dispute_window_ends_at


def _normalize_rows(value: object) -> tuple[ResearchOutcomeRevisionRiskRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchOutcomeRevisionRiskRow:
            raise ValueError("rows must contain ResearchOutcomeRevisionRiskRow values")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchOutcomeRevisionRiskReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchOutcomeRevisionRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchOutcomeRevisionRiskReasonCodeCount values",
            )
    return value


def _validate_row_consistency(row: ResearchOutcomeRevisionRiskRow) -> None:
    if (
        row.settled_observation_count + row.near_settlement_observation_count
        != row.observation_count
    ):
        raise ValueError("lifecycle observation counts must match observation_count")
    for field_name in (
        "active_dispute_window_count",
        "memory_update_needed_count",
    ):
        if getattr(row, field_name) > row.observation_count:
            raise ValueError(f"{field_name} must be <= observation_count")
    if row.contradicting_evidence_update_count > row.evidence_update_count:
        raise ValueError(
            "contradicting_evidence_update_count must be <= evidence_update_count",
        )
    if _decimal_count(len(row.observation_ids)) != row.observation_count:
        raise ValueError("observation_ids must match observation_count")
    expected_status_code = f"outcome_revision_risk_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchOutcomeRevisionRiskReport) -> None:
    if report.event_outcome_count != _decimal_count(len(report.rows)):
        raise ValueError("event_outcome_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.memory_update_needed_count != sum(
        (row.memory_update_needed_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("memory_update_needed_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(rows: tuple[ResearchOutcomeRevisionRiskRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal = _require_decimal(field_name, value)
    quantized = decimal.quantize(COUNT_QUANTUM)
    if decimal != quantized:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    quantized = _require_nonnegative_whole_decimal(field_name, value)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    quantized = _quantize(normalized)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return quantized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a finite Decimal") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase reason code")
    _reject_unsafe_public_string(field_name, value)


def _require_enum(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_status(field_name: str, value: str) -> None:
    _require_enum(field_name, value, STATUSES)


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


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


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_public_string(field_name, item)
    return tuple(sorted(dict.fromkeys(value)))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_reason_code(field_name, item)
    return tuple(sorted(dict.fromkeys(value)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) is bool or type(value) is str:
        return value
    raise ValueError("payload value is not JSON serializable")
