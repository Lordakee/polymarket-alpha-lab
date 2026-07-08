"""Pure public report summarizing event-domain source-disagreement decay."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_DISAGREEMENT_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-source-disagreement-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_event_source_disagreement_decay_report_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
CONTRADICTION_PERSISTENCE_WATCH_REASON = (
    f"{REASON_PREFIX}contradiction_persistence_watch"
)
CONTRADICTION_PERSISTENCE_BLOCK_REASON = (
    f"{REASON_PREFIX}contradiction_persistence_block"
)
SOURCE_RELIABILITY_WATCH_REASON = f"{REASON_PREFIX}source_reliability_watch"
SOURCE_RELIABILITY_BLOCK_REASON = f"{REASON_PREFIX}source_reliability_block"
EVIDENCE_FRESHNESS_WATCH_REASON = f"{REASON_PREFIX}evidence_freshness_watch"
EVIDENCE_FRESHNESS_BLOCK_REASON = f"{REASON_PREFIX}evidence_freshness_block"
CATALYST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}catalyst_pressure_watch"
CATALYST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}catalyst_pressure_block"
RESOLUTION_PROXIMITY_WATCH_REASON = f"{REASON_PREFIX}resolution_proximity_watch"
RESOLUTION_PROXIMITY_BLOCK_REASON = f"{REASON_PREFIX}resolution_proximity_block"
SCORE_WATCH_REASON = f"{REASON_PREFIX}score_watch"
SCORE_BLOCK_REASON = f"{REASON_PREFIX}score_block"

REASON_CODE_PRIORITY = (
    NO_INPUTS_REASON,
    CONTRADICTION_PERSISTENCE_BLOCK_REASON,
    CONTRADICTION_PERSISTENCE_WATCH_REASON,
    SOURCE_RELIABILITY_BLOCK_REASON,
    SOURCE_RELIABILITY_WATCH_REASON,
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    CATALYST_PRESSURE_BLOCK_REASON,
    CATALYST_PRESSURE_WATCH_REASON,
    RESOLUTION_PROXIMITY_BLOCK_REASON,
    RESOLUTION_PROXIMITY_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_PRIORITY = tuple(
    reason_code for reason_code in REASON_CODE_PRIORITY if reason_code != NO_INPUTS_REASON
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "event" + "_id",
    "event" + "_slug",
    "event" + "_identifier",
    "market" + "_id",
    "market" + "_slug",
    "market" + "_identifier",
    "source" + "_id",
    "source" + "_name",
    "source" + "_url",
    "raw" + "_text",
    "url",
    "private",
    "private" + "_key",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tr" + "ade",
    "credential",
    "secret",
    "token",
    "reco" + "mmend",
    "siz" + "ing",
    "pos" + "ition",
    "b" + "uy",
    "se" + "ll",
)

PUBLIC_DECIMAL_STRING_KEYS = {
    "aggregate_contradiction_age_seconds",
    "average_evidence_freshness",
    "average_persistence_score",
    "average_source_reliability",
    "block_count",
    "catalyst_pressure",
    "contradiction_persistence_score",
    "contradictory_source_count",
    "count",
    "domain_count",
    "evidence_freshness",
    "input_count",
    "max_catalyst_pressure",
    "max_persistence_score",
    "max_resolution_proximity",
    "min_aggregate_contradiction_age_seconds",
    "observation_count",
    "pass_count",
    "persistence_score",
    "resolution_proximity",
    "row_ratio",
    "source_count",
    "source_disagreement_share",
    "source_reliability",
    "source_reliability_risk_score",
    "watch_count",
}


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_DISAGREEMENT_DECAY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventSourceDisagreementDecayConfig",
    "ResearchEventSourceDisagreementDecayInput",
    "ResearchEventSourceDisagreementDecayReasonCodeCount",
    "ResearchEventSourceDisagreementDecayReport",
    "ResearchEventSourceDisagreementDecayRow",
    "build_research_event_source_disagreement_decay_report",
    "research_event_source_disagreement_decay_report_public_digest",
    "research_event_source_disagreement_decay_report_public_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceDisagreementDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_DISAGREEMENT_DECAY_REPORT_CONFIG_VERSION
    )
    fresh_contradiction_age_seconds: Decimal = Decimal("3600.000000")
    stale_contradiction_age_seconds: Decimal = Decimal("86400.000000")
    watch_persistence_score: Decimal = Decimal("0.350000")
    block_persistence_score: Decimal = Decimal("0.650000")
    watch_source_reliability_floor: Decimal = Decimal("0.700000")
    block_source_reliability_floor: Decimal = Decimal("0.400000")
    watch_evidence_freshness: Decimal = Decimal("0.400000")
    block_evidence_freshness: Decimal = Decimal("0.750000")
    watch_catalyst_pressure: Decimal = Decimal("0.400000")
    block_catalyst_pressure: Decimal = Decimal("0.750000")
    watch_resolution_proximity: Decimal = Decimal("0.400000")
    block_resolution_proximity: Decimal = Decimal("0.750000")
    watch_contradiction_persistence_score: Decimal = Decimal("0.250000")
    block_contradiction_persistence_score: Decimal = Decimal("0.900000")
    contradiction_age_weight: Decimal = Decimal("0.300000")
    source_reliability_weight: Decimal = Decimal("0.250000")
    evidence_freshness_weight: Decimal = Decimal("0.150000")
    catalyst_pressure_weight: Decimal = Decimal("0.150000")
    resolution_proximity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceDisagreementDecayConfig:
            raise ValueError(
                "config must be exactly ResearchEventSourceDisagreementDecayConfig",
            )
        _require_public_text("config_version", self.config_version)
        _reject_unsafe_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_contradiction_age_seconds",
            "stale_contradiction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_contradiction_age_seconds <= self.fresh_contradiction_age_seconds:
            raise ValueError(
                "stale_contradiction_age_seconds must exceed "
                "fresh_contradiction_age_seconds",
            )
        for field_name in (
            "watch_persistence_score",
            "block_persistence_score",
            "watch_source_reliability_floor",
            "block_source_reliability_floor",
            "watch_evidence_freshness",
            "block_evidence_freshness",
            "watch_catalyst_pressure",
            "block_catalyst_pressure",
            "watch_resolution_proximity",
            "block_resolution_proximity",
            "watch_contradiction_persistence_score",
            "block_contradiction_persistence_score",
            "contradiction_age_weight",
            "source_reliability_weight",
            "evidence_freshness_weight",
            "catalyst_pressure_weight",
            "resolution_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_persistence_score <= self.watch_persistence_score:
            raise ValueError("block_persistence_score must exceed watch_persistence_score")
        if self.block_source_reliability_floor > self.watch_source_reliability_floor:
            raise ValueError(
                "block_source_reliability_floor must not exceed "
                "watch_source_reliability_floor",
            )
        for block_name, block_value, watch_name, watch_value in (
            (
                "block_evidence_freshness",
                self.block_evidence_freshness,
                "watch_evidence_freshness",
                self.watch_evidence_freshness,
            ),
            (
                "block_catalyst_pressure",
                self.block_catalyst_pressure,
                "watch_catalyst_pressure",
                self.watch_catalyst_pressure,
            ),
            (
                "block_resolution_proximity",
                self.block_resolution_proximity,
                "watch_resolution_proximity",
                self.watch_resolution_proximity,
            ),
            (
                "block_contradiction_persistence_score",
                self.block_contradiction_persistence_score,
                "watch_contradiction_persistence_score",
                self.watch_contradiction_persistence_score,
            ),
        ):
            if block_value < watch_value:
                raise ValueError(f"{block_name} must not be below {watch_name}")
        weight_sum = _quantize(
            self.contradiction_age_weight
            + self.source_reliability_weight
            + self.evidence_freshness_weight
            + self.catalyst_pressure_weight
            + self.resolution_proximity_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "contradiction_age_weight, source_reliability_weight, "
                "evidence_freshness_weight, catalyst_pressure_weight, and "
                "resolution_proximity_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceDisagreementDecayInput:
    event_domain: str
    aggregate_contradiction_age_seconds: Decimal
    source_reliability: Decimal
    evidence_freshness: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    contradictory_source_count: Decimal
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceDisagreementDecayInput:
            raise ValueError(
                "input must be exactly ResearchEventSourceDisagreementDecayInput",
            )
        _require_public_text("event_domain", self.event_domain)
        _reject_unsafe_public_text("event_domain", self.event_domain)
        object.__setattr__(
            self,
            "aggregate_contradiction_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_contradiction_age_seconds",
                self.aggregate_contradiction_age_seconds,
            ),
        )
        for field_name in (
            "source_reliability",
            "evidence_freshness",
            "catalyst_pressure",
            "resolution_proximity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradictory_source_count",
            _require_nonnegative_decimal(
                "contradictory_source_count",
                self.contradictory_source_count,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_decimal("source_count", self.source_count),
        )
        if self.contradictory_source_count > self.source_count:
            raise ValueError(
                "contradictory_source_count must not exceed source_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventSourceDisagreementDecayRow:
    event_domain: str
    observation_count: Decimal
    aggregate_contradiction_age_seconds: Decimal
    source_reliability: Decimal
    evidence_freshness: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    contradictory_source_count: Decimal
    source_count: Decimal
    source_disagreement_share: Decimal
    contradiction_persistence_score: Decimal
    source_reliability_risk_score: Decimal
    persistence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchEventSourceDisagreementDecayConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchEventSourceDisagreementDecayConfig | None,
    ) -> None:
        if type(self) is not ResearchEventSourceDisagreementDecayRow:
            raise ValueError("row must be exactly ResearchEventSourceDisagreementDecayRow")
        _require_public_text("event_domain", self.event_domain)
        _reject_unsafe_public_text("event_domain", self.event_domain)
        for field_name in (
            "observation_count",
            "aggregate_contradiction_age_seconds",
            "contradictory_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_decimal("source_count", self.source_count),
        )
        for field_name in (
            "source_reliability",
            "evidence_freshness",
            "catalyst_pressure",
            "resolution_proximity",
            "source_disagreement_share",
            "contradiction_persistence_score",
            "source_reliability_risk_score",
            "persistence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self, config=validation_config)


@dataclass(frozen=True)
class ResearchEventSourceDisagreementDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceDisagreementDecayReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchEventSourceDisagreementDecayReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_PRIORITY)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventSourceDisagreementDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    domain_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_persistence_score: Decimal
    max_persistence_score: Decimal
    min_aggregate_contradiction_age_seconds: Decimal
    average_source_reliability: Decimal | None
    average_evidence_freshness: Decimal | None
    max_catalyst_pressure: Decimal
    max_resolution_proximity: Decimal
    rows: tuple[ResearchEventSourceDisagreementDecayRow, ...]
    reason_code_counts: tuple[ResearchEventSourceDisagreementDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceDisagreementDecayReport:
            raise ValueError(
                "report must be exactly ResearchEventSourceDisagreementDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _reject_unsafe_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "domain_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_persistence_score",
            "max_persistence_score",
            "min_aggregate_contradiction_age_seconds",
            "max_catalyst_pressure",
            "max_resolution_proximity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_source_reliability", "average_evidence_freshness"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _public_digest_from_report(self)
        if self.public_digest:
            digest = _require_sha256_digest("public_digest", self.public_digest)
            object.__setattr__(self, "public_digest", digest)
            if digest != expected_digest:
                raise ValueError("public_digest must match report payload")
        else:
            object.__setattr__(self, "public_digest", expected_digest)
        _reject_unsafe_public_payload("report", _json_ready(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_source_disagreement_decay_report_public_payload(self)


def build_research_event_source_disagreement_decay_report(
    inputs: Iterable[object],
    *,
    config: ResearchEventSourceDisagreementDecayConfig,
    generated_at: datetime,
) -> ResearchEventSourceDisagreementDecayReport:
    if type(config) is not ResearchEventSourceDisagreementDecayConfig:
        raise ValueError("config must be a ResearchEventSourceDisagreementDecayConfig")
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    grouped: dict[str, list[ResearchEventSourceDisagreementDecayInput]] = {}
    for row in normalized_inputs:
        grouped.setdefault(row.event_domain, []).append(row)

    rows = tuple(
        _row_from_inputs(
            event_domain=event_domain,
            inputs=tuple(grouped[event_domain]),
            config=config,
        )
        for event_domain in sorted(grouped)
    )
    domain_count = _count(len(rows))
    input_count = _count(len(normalized_inputs))
    pass_count = _count(sum(1 for row in rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in rows if row.status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventSourceDisagreementDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    return ResearchEventSourceDisagreementDecayReport(
        generated_at=report_time,
        config_version=config.config_version,
        status=_report_status(bool(rows), block_count, watch_count),
        domain_count=domain_count,
        input_count=input_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_persistence_score=_ratio(
            sum((row.persistence_score for row in rows), ZERO),
            domain_count,
        ),
        max_persistence_score=max(
            (row.persistence_score for row in rows),
            default=ZERO,
        ),
        min_aggregate_contradiction_age_seconds=min(
            (row.aggregate_contradiction_age_seconds for row in rows),
            default=ZERO,
        ),
        average_source_reliability=_average_optional(
            tuple(row.source_reliability for row in rows),
        ),
        average_evidence_freshness=_average_optional(
            tuple(row.evidence_freshness for row in rows),
        ),
        max_catalyst_pressure=max(
            (row.catalyst_pressure for row in rows),
            default=ZERO,
        ),
        max_resolution_proximity=max(
            (row.resolution_proximity for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_source_disagreement_decay_report_public_payload(
    value: ResearchEventSourceDisagreementDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventSourceDisagreementDecayReport:
        _validate_report(value)
        if value.public_digest != _public_digest_from_report(value):
            raise ValueError("public_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventSourceDisagreementDecayReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _validate_public_payload(payload)
    return dict(payload)


def research_event_source_disagreement_decay_report_public_digest(
    value: ResearchEventSourceDisagreementDecayReport | dict[str, Any],
) -> str:
    payload = research_event_source_disagreement_decay_report_public_payload(value)
    digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", digest)
    return digest


def _row_from_inputs(
    *,
    event_domain: str,
    inputs: tuple[ResearchEventSourceDisagreementDecayInput, ...],
    config: ResearchEventSourceDisagreementDecayConfig,
) -> ResearchEventSourceDisagreementDecayRow:
    rows = tuple(
        sorted(
            inputs,
            key=lambda item: (
                item.aggregate_contradiction_age_seconds,
                item.source_reliability,
                item.evidence_freshness,
                item.catalyst_pressure,
                item.resolution_proximity,
            ),
        ),
    )
    aggregate_contradiction_age_seconds = _average_decimal(
        tuple(item.aggregate_contradiction_age_seconds for item in rows),
    )
    source_reliability = _average_decimal(tuple(item.source_reliability for item in rows))
    evidence_freshness = _average_decimal(tuple(item.evidence_freshness for item in rows))
    catalyst_pressure = _average_decimal(tuple(item.catalyst_pressure for item in rows))
    resolution_proximity = _average_decimal(tuple(item.resolution_proximity for item in rows))
    contradictory_source_count = sum(
        (item.contradictory_source_count for item in rows),
        ZERO,
    )
    source_count = sum((item.source_count for item in rows), ZERO)
    source_disagreement_share = _ratio(contradictory_source_count, source_count)
    contradiction_persistence_score = _contradiction_persistence_score(
        aggregate_contradiction_age_seconds,
        config=config,
    )
    source_reliability_risk_score = _bounded_probability(ONE - source_reliability)
    persistence_score = _persistence_score(
        contradiction_persistence_score=contradiction_persistence_score,
        source_reliability_risk_score=source_reliability_risk_score,
        evidence_freshness=evidence_freshness,
        catalyst_pressure=catalyst_pressure,
        resolution_proximity=resolution_proximity,
        config=config,
    )
    status = _status_for_score(persistence_score, config=config)
    return ResearchEventSourceDisagreementDecayRow(
        event_domain=event_domain,
        observation_count=_count(len(rows)),
        aggregate_contradiction_age_seconds=aggregate_contradiction_age_seconds,
        source_reliability=source_reliability,
        evidence_freshness=evidence_freshness,
        catalyst_pressure=catalyst_pressure,
        resolution_proximity=resolution_proximity,
        contradictory_source_count=contradictory_source_count,
        source_count=source_count,
        source_disagreement_share=source_disagreement_share,
        contradiction_persistence_score=contradiction_persistence_score,
        source_reliability_risk_score=source_reliability_risk_score,
        persistence_score=persistence_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            contradiction_persistence_score=contradiction_persistence_score,
            source_reliability=source_reliability,
            evidence_freshness=evidence_freshness,
            catalyst_pressure=catalyst_pressure,
            resolution_proximity=resolution_proximity,
            persistence_score=persistence_score,
            config=config,
        ),
        validation_config=config,
    )


def _contradiction_persistence_score(
    aggregate_contradiction_age_seconds: Decimal,
    *,
    config: ResearchEventSourceDisagreementDecayConfig,
) -> Decimal:
    if aggregate_contradiction_age_seconds <= config.fresh_contradiction_age_seconds:
        return ONE
    if aggregate_contradiction_age_seconds >= config.stale_contradiction_age_seconds:
        return ZERO
    span = config.stale_contradiction_age_seconds - config.fresh_contradiction_age_seconds
    remaining = config.stale_contradiction_age_seconds - aggregate_contradiction_age_seconds
    return _ratio(remaining, span)


def _persistence_score(
    *,
    contradiction_persistence_score: Decimal,
    source_reliability_risk_score: Decimal,
    evidence_freshness: Decimal,
    catalyst_pressure: Decimal,
    resolution_proximity: Decimal,
    config: ResearchEventSourceDisagreementDecayConfig,
) -> Decimal:
    return _bounded_probability(
        contradiction_persistence_score * config.contradiction_age_weight
        + source_reliability_risk_score * config.source_reliability_weight
        + evidence_freshness * config.evidence_freshness_weight
        + catalyst_pressure * config.catalyst_pressure_weight
        + resolution_proximity * config.resolution_proximity_weight,
    )


def _row_reason_codes(
    *,
    status: str,
    contradiction_persistence_score: Decimal,
    source_reliability: Decimal,
    evidence_freshness: Decimal,
    catalyst_pressure: Decimal,
    resolution_proximity: Decimal,
    persistence_score: Decimal,
    config: ResearchEventSourceDisagreementDecayConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (PASS_REASON,)
    codes: list[str] = []
    if (
        contradiction_persistence_score
        >= config.block_contradiction_persistence_score
    ):
        codes.append(CONTRADICTION_PERSISTENCE_BLOCK_REASON)
    elif (
        contradiction_persistence_score
        >= config.watch_contradiction_persistence_score
    ):
        codes.append(CONTRADICTION_PERSISTENCE_WATCH_REASON)
    if source_reliability <= config.block_source_reliability_floor:
        codes.append(SOURCE_RELIABILITY_BLOCK_REASON)
    elif source_reliability <= config.watch_source_reliability_floor:
        codes.append(SOURCE_RELIABILITY_WATCH_REASON)
    if evidence_freshness >= config.block_evidence_freshness:
        codes.append(EVIDENCE_FRESHNESS_BLOCK_REASON)
    elif evidence_freshness >= config.watch_evidence_freshness:
        codes.append(EVIDENCE_FRESHNESS_WATCH_REASON)
    if catalyst_pressure >= config.block_catalyst_pressure:
        codes.append(CATALYST_PRESSURE_BLOCK_REASON)
    elif catalyst_pressure >= config.watch_catalyst_pressure:
        codes.append(CATALYST_PRESSURE_WATCH_REASON)
    if resolution_proximity >= config.block_resolution_proximity:
        codes.append(RESOLUTION_PROXIMITY_BLOCK_REASON)
    elif resolution_proximity >= config.watch_resolution_proximity:
        codes.append(RESOLUTION_PROXIMITY_WATCH_REASON)
    if persistence_score >= config.block_persistence_score:
        codes.append(SCORE_BLOCK_REASON)
    else:
        codes.append(SCORE_WATCH_REASON)
    return _normalize_row_reason_codes(tuple(codes))


def _status_for_score(
    persistence_score: Decimal,
    *,
    config: ResearchEventSourceDisagreementDecayConfig,
) -> str:
    if persistence_score >= config.block_persistence_score:
        return STATUS_BLOCK
    if persistence_score >= config.watch_persistence_score:
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchEventSourceDisagreementDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventSourceDisagreementDecayInput:
            raise ValueError(
                "inputs must contain ResearchEventSourceDisagreementDecayInput values",
            )
        _require_hard_flags("input", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchEventSourceDisagreementDecayRow, ...],
) -> tuple[ResearchEventSourceDisagreementDecayRow, ...]:
    for row in rows:
        if type(row) is not ResearchEventSourceDisagreementDecayRow:
            raise ValueError(
                "rows must contain ResearchEventSourceDisagreementDecayRow values",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=lambda row: row.event_domain))


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventSourceDisagreementDecayReasonCodeCount, ...],
) -> tuple[ResearchEventSourceDisagreementDecayReasonCodeCount, ...]:
    for count in counts:
        if type(count) is not ResearchEventSourceDisagreementDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSourceDisagreementDecayReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    priority = {reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)}
    return tuple(sorted(counts, key=lambda item: priority[item.reason_code]))


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(dict.fromkeys(reason_codes))
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_PRIORITY)
    priority = {reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)}
    return tuple(sorted(normalized, key=lambda reason_code: priority[reason_code]))


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(dict.fromkeys(reason_codes))
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_PRIORITY)
    priority = {reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)}
    return tuple(sorted(normalized, key=lambda reason_code: priority[reason_code]))


def _reason_code_counts(
    rows: tuple[ResearchEventSourceDisagreementDecayRow, ...],
) -> tuple[ResearchEventSourceDisagreementDecayReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchEventSourceDisagreementDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(_count(counts[reason_code]), row_count),
        )
        for reason_code in REASON_CODE_PRIORITY
        if reason_code != NO_INPUTS_REASON and counts[reason_code]
    )


def _report_status(has_rows: bool, block_count: Decimal, watch_count: Decimal) -> str:
    if not has_rows:
        return STATUS_BLOCK
    if block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _validate_row(
    row: ResearchEventSourceDisagreementDecayRow,
    *,
    config: ResearchEventSourceDisagreementDecayConfig | None,
) -> None:
    validation_config = config or ResearchEventSourceDisagreementDecayConfig()
    if row.contradictory_source_count > row.source_count:
        raise ValueError("contradictory_source_count must not exceed source_count")
    if row.source_disagreement_share != _ratio(
        row.contradictory_source_count,
        row.source_count,
    ):
        raise ValueError("source_disagreement_share must match source counts")
    expected_source_risk = _bounded_probability(ONE - row.source_reliability)
    if row.source_reliability_risk_score != expected_source_risk:
        raise ValueError(
            "source_reliability_risk_score must match source_reliability",
        )
    expected_persistence_score = _persistence_score(
        contradiction_persistence_score=row.contradiction_persistence_score,
        source_reliability_risk_score=row.source_reliability_risk_score,
        evidence_freshness=row.evidence_freshness,
        catalyst_pressure=row.catalyst_pressure,
        resolution_proximity=row.resolution_proximity,
        config=validation_config,
    )
    if row.persistence_score != expected_persistence_score:
        raise ValueError("persistence_score must match component scores")
    expected_status = _status_for_score(
        row.persistence_score,
        config=validation_config,
    )
    if row.status != expected_status:
        raise ValueError("status must match persistence_score")
    expected_reason_codes = _row_reason_codes(
        status=row.status,
        contradiction_persistence_score=row.contradiction_persistence_score,
        source_reliability=row.source_reliability,
        evidence_freshness=row.evidence_freshness,
        catalyst_pressure=row.catalyst_pressure,
        resolution_proximity=row.resolution_proximity,
        persistence_score=row.persistence_score,
        config=validation_config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")


def _validate_report(report: ResearchEventSourceDisagreementDecayReport) -> None:
    rows = report.rows
    domain_count = _count(len(rows))
    if report.domain_count != domain_count:
        raise ValueError("domain_count must match rows")
    if report.input_count != sum((row.observation_count for row in rows), ZERO):
        raise ValueError("input_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(bool(rows), report.block_count, report.watch_count):
        raise ValueError("status must match rows")
    expected_reason_codes = (
        (NO_INPUTS_REASON,)
        if not rows
        else tuple(item.reason_code for item in _reason_code_counts(rows))
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if tuple(item.reason_code for item in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.average_persistence_score != _ratio(
        sum((row.persistence_score for row in rows), ZERO),
        domain_count,
    ):
        raise ValueError("average_persistence_score must match rows")
    if report.max_persistence_score != max(
        (row.persistence_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_persistence_score must match rows")
    if report.min_aggregate_contradiction_age_seconds != min(
        (row.aggregate_contradiction_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_aggregate_contradiction_age_seconds must match rows")
    if report.average_source_reliability != _average_optional(
        tuple(row.source_reliability for row in rows),
    ):
        raise ValueError("average_source_reliability must match rows")
    if report.average_evidence_freshness != _average_optional(
        tuple(row.evidence_freshness for row in rows),
    ):
        raise ValueError("average_evidence_freshness must match rows")
    if report.max_catalyst_pressure != max(
        (row.catalyst_pressure for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_catalyst_pressure must match rows")
    if report.max_resolution_proximity != max(
        (row.resolution_proximity for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_resolution_proximity must match rows")


def _public_digest_from_report(report: ResearchEventSourceDisagreementDecayReport) -> str:
    payload = _json_ready(report, skip_public_digest=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_digest_from_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "public_digest"
    }
    encoded = json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any, *, skip_public_digest: bool = False) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in fields(value):
            if skip_public_digest and field.name == "public_digest":
                continue
            result[field.name] = _json_ready(
                getattr(value, field.name),
                skip_public_digest=skip_public_digest,
            )
        return result
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal payload values must be exact Decimal values")
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item, skip_public_digest=skip_public_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, skip_public_digest=skip_public_digest) for item in value]
    if isinstance(value, dict):
        return {
            _json_ready(key, skip_public_digest=skip_public_digest): _json_ready(
                item,
                skip_public_digest=skip_public_digest,
            )
            for key, item in value.items()
        }
    if type(value) in (str, bool):
        return value
    raise ValueError("public payload values must use Decimal strings")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload_values(payload)
    digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", digest)
    expected_digest = _public_digest_from_payload(payload)
    if digest != expected_digest:
        raise ValueError("public_digest must match public payload")


def _validate_public_payload_values(value: Any, *, key_name: str | None = None) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _validate_public_payload_values(item, key_name=key)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload_values(item, key_name=key_name)
        return
    if type(value) in (int, float, Decimal) or type(value) is datetime:
        raise ValueError("public payload numeric values must be Decimal strings")
    if key_name in PUBLIC_DECIMAL_STRING_KEYS:
        if type(value) is not str:
            raise ValueError("public payload numeric values must be Decimal strings")
        _require_decimal_string(key_name, value)
        return
    if value is not None and type(value) not in (str, bool):
        raise ValueError("public payload values must be public JSON values")


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = _json_ready(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
                raise ValueError(f"unsafe public payload key: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload value: {label}")


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_text(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except Exception as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(
    field_name: str,
    value: str,
    allowed_reason_codes: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in allowed_reason_codes:
        raise ValueError(f"{field_name} contains an unknown reason code")
    return value


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _require_decimal_string(field_name: str, value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal strings") from exc
    normalized = _require_decimal(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must use Decimal strings")
    return normalized


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{label}.{field_name} must be a bool")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be true")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _bounded_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _bounded_probability(numerator / denominator)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _count(len(values)))


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average_decimal(values)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))
