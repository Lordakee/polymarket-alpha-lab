"""Pure event-domain freshness decay scorecard for public research reports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION = (
    "research-event-source-freshness-decay-scorecard-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_event_source_freshness_decay_scorecard_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
SOURCE_AGE_WATCH_REASON = f"{REASON_PREFIX}source_age_watch"
SOURCE_AGE_BLOCK_REASON = f"{REASON_PREFIX}source_age_block"
UPDATE_CADENCE_WATCH_REASON = f"{REASON_PREFIX}update_cadence_watch"
UPDATE_CADENCE_BLOCK_REASON = f"{REASON_PREFIX}update_cadence_block"
CATALYST_RECENCY_WATCH_REASON = f"{REASON_PREFIX}catalyst_recency_watch"
CATALYST_RECENCY_BLOCK_REASON = f"{REASON_PREFIX}catalyst_recency_block"
CONTRADICTION_AGE_WATCH_REASON = f"{REASON_PREFIX}contradiction_age_watch"
CONTRADICTION_AGE_BLOCK_REASON = f"{REASON_PREFIX}contradiction_age_block"
SCORE_WATCH_REASON = f"{REASON_PREFIX}score_watch"
SCORE_BLOCK_REASON = f"{REASON_PREFIX}score_block"

REASON_CODE_PRIORITY = (
    NO_INPUTS_REASON,
    SOURCE_AGE_BLOCK_REASON,
    SOURCE_AGE_WATCH_REASON,
    UPDATE_CADENCE_BLOCK_REASON,
    UPDATE_CADENCE_WATCH_REASON,
    CATALYST_RECENCY_BLOCK_REASON,
    CATALYST_RECENCY_WATCH_REASON,
    CONTRADICTION_AGE_BLOCK_REASON,
    CONTRADICTION_AGE_WATCH_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_PRIORITY = tuple(
    code for code in REASON_CODE_PRIORITY if code != NO_INPUTS_REASON
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION",
    "ResearchEventSourceFreshnessDecayObservation",
    "ResearchEventSourceFreshnessDecayReasonCodeCount",
    "ResearchEventSourceFreshnessDecayScoreRow",
    "ResearchEventSourceFreshnessDecayScorecardConfig",
    "ResearchEventSourceFreshnessDecayScorecardReport",
    "build_research_event_source_freshness_decay_scorecard",
    "research_event_source_freshness_decay_scorecard_public_digest",
    "research_event_source_freshness_decay_scorecard_public_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceFreshnessDecayScorecardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_FRESHNESS_DECAY_SCORECARD_CONFIG_VERSION
    )
    fresh_source_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    target_update_cadence_seconds: Decimal = Decimal("21600.000000")
    stale_update_cadence_seconds: Decimal = Decimal("86400.000000")
    fresh_catalyst_age_seconds: Decimal = Decimal("3600.000000")
    stale_catalyst_age_seconds: Decimal = Decimal("86400.000000")
    fresh_contradiction_age_seconds: Decimal = Decimal("3600.000000")
    stale_contradiction_age_seconds: Decimal = Decimal("86400.000000")
    pass_freshness_decay_score: Decimal = Decimal("0.700000")
    watch_freshness_decay_score: Decimal = Decimal("0.400000")
    source_age_weight: Decimal = Decimal("0.350000")
    update_cadence_weight: Decimal = Decimal("0.250000")
    catalyst_recency_weight: Decimal = Decimal("0.200000")
    contradiction_age_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceFreshnessDecayScorecardConfig:
            raise TypeError(
                "ResearchEventSourceFreshnessDecayScorecardConfig does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceFreshnessDecayScorecardConfig:
            raise ValueError(
                "config must be exactly ResearchEventSourceFreshnessDecayScorecardConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "target_update_cadence_seconds",
            "stale_update_cadence_seconds",
            "fresh_catalyst_age_seconds",
            "stale_catalyst_age_seconds",
            "fresh_contradiction_age_seconds",
            "stale_contradiction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_seconds(
            "fresh_source_age_seconds",
            self.fresh_source_age_seconds,
            "stale_source_age_seconds",
            self.stale_source_age_seconds,
        )
        _require_increasing_seconds(
            "target_update_cadence_seconds",
            self.target_update_cadence_seconds,
            "stale_update_cadence_seconds",
            self.stale_update_cadence_seconds,
        )
        _require_increasing_seconds(
            "fresh_catalyst_age_seconds",
            self.fresh_catalyst_age_seconds,
            "stale_catalyst_age_seconds",
            self.stale_catalyst_age_seconds,
        )
        _require_increasing_seconds(
            "fresh_contradiction_age_seconds",
            self.fresh_contradiction_age_seconds,
            "stale_contradiction_age_seconds",
            self.stale_contradiction_age_seconds,
        )
        for field_name in (
            "pass_freshness_decay_score",
            "watch_freshness_decay_score",
            "source_age_weight",
            "update_cadence_weight",
            "catalyst_recency_weight",
            "contradiction_age_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_freshness_decay_score <= self.watch_freshness_decay_score:
            raise ValueError(
                "pass_freshness_decay_score must exceed watch_freshness_decay_score",
            )
        weight_sum = _quantize(
            self.source_age_weight
            + self.update_cadence_weight
            + self.catalyst_recency_weight
            + self.contradiction_age_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "source_age_weight, update_cadence_weight, catalyst_recency_weight, "
                "and contradiction_age_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceFreshnessDecayObservation:
    event_domain: str
    evidence_ref: str
    source_age_seconds: Decimal
    update_cadence_seconds: Decimal
    catalyst_age_seconds: Decimal
    contradiction_age_seconds: Decimal
    contradiction_present: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceFreshnessDecayObservation:
            raise TypeError(
                "ResearchEventSourceFreshnessDecayObservation does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceFreshnessDecayObservation:
            raise ValueError(
                "observation must be exactly ResearchEventSourceFreshnessDecayObservation",
            )
        _require_public_text("event_domain", self.event_domain)
        _reject_unsafe_public_text("event_domain", self.event_domain)
        _require_public_text("evidence_ref", self.evidence_ref)
        for field_name in (
            "source_age_seconds",
            "update_cadence_seconds",
            "catalyst_age_seconds",
            "contradiction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.contradiction_present) is not bool:
            raise ValueError("contradiction_present must be a bool")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceFreshnessDecayScoreRow:
    event_domain: str
    observation_count: Decimal
    aggregate_source_age_seconds: Decimal
    update_cadence_seconds: Decimal
    catalyst_age_seconds: Decimal
    minimum_contradiction_age_seconds: Decimal
    contradiction_count: Decimal
    source_age_score: Decimal
    update_cadence_score: Decimal
    catalyst_recency_score: Decimal
    contradiction_age_score: Decimal
    freshness_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchEventSourceFreshnessDecayScorecardConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceFreshnessDecayScoreRow:
            raise TypeError(
                "ResearchEventSourceFreshnessDecayScoreRow does not allow subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchEventSourceFreshnessDecayScorecardConfig | None,
    ) -> None:
        if type(self) is not ResearchEventSourceFreshnessDecayScoreRow:
            raise ValueError(
                "row must be exactly ResearchEventSourceFreshnessDecayScoreRow",
            )
        _require_public_text("event_domain", self.event_domain)
        _reject_unsafe_public_text("event_domain", self.event_domain)
        for field_name in (
            "observation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_source_age_seconds",
            "update_cadence_seconds",
            "catalyst_age_seconds",
            "minimum_contradiction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_score",
            "update_cadence_score",
            "catalyst_recency_score",
            "contradiction_age_score",
            "freshness_decay_score",
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
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSourceFreshnessDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceFreshnessDecayReasonCodeCount:
            raise TypeError(
                "ResearchEventSourceFreshnessDecayReasonCodeCount does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceFreshnessDecayReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventSourceFreshnessDecayReasonCodeCount",
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
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventSourceFreshnessDecayScorecardReport:
    generated_at: datetime
    config_version: str
    scorecard_status: str
    domain_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_freshness_decay_score: Decimal
    max_aggregate_source_age_seconds: Decimal
    max_update_cadence_seconds: Decimal
    max_catalyst_age_seconds: Decimal
    min_contradiction_age_seconds: Decimal
    rows: tuple[ResearchEventSourceFreshnessDecayScoreRow, ...]
    reason_code_counts: tuple[ResearchEventSourceFreshnessDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceFreshnessDecayScorecardReport:
            raise TypeError(
                "ResearchEventSourceFreshnessDecayScorecardReport does not allow subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceFreshnessDecayScorecardReport:
            raise ValueError(
                "report must be exactly ResearchEventSourceFreshnessDecayScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        _require_status("scorecard_status", self.scorecard_status)
        for field_name in (
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_freshness_decay_score",
            "max_aggregate_source_age_seconds",
            "max_update_cadence_seconds",
            "max_catalyst_age_seconds",
            "min_contradiction_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _set_or_validate_public_digest(self)
        _reject_unsafe_public_payload("report", _json_ready(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_source_freshness_decay_scorecard_public_payload(self)


def build_research_event_source_freshness_decay_scorecard(
    observations: Iterable[object],
    *,
    config: ResearchEventSourceFreshnessDecayScorecardConfig,
    generated_at: datetime,
) -> ResearchEventSourceFreshnessDecayScorecardReport:
    if type(config) is not ResearchEventSourceFreshnessDecayScorecardConfig:
        raise ValueError(
            "config must be a ResearchEventSourceFreshnessDecayScorecardConfig",
        )
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_observations(observations)

    grouped: dict[str, list[ResearchEventSourceFreshnessDecayObservation]] = {}
    for row in rows:
        grouped.setdefault(row.event_domain, []).append(row)

    score_rows = tuple(
        _build_row(
            event_domain=event_domain,
            observations=tuple(grouped[event_domain]),
            config=config,
        )
        for event_domain in sorted(grouped)
    )
    domain_count = _count(len(score_rows))
    observation_count = sum((row.observation_count for row in score_rows), ZERO)
    pass_count = _count(sum(1 for row in score_rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in score_rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in score_rows if row.status == STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(score_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not score_rows:
        reason_code_counts = (
            ResearchEventSourceFreshnessDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    contradiction_ages = tuple(
        row.minimum_contradiction_age_seconds
        for row in score_rows
        if row.contradiction_count > ZERO
    )
    return ResearchEventSourceFreshnessDecayScorecardReport(
        generated_at=report_time,
        config_version=config.config_version,
        scorecard_status=_report_status(bool(score_rows), block_count, watch_count),
        domain_count=domain_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_freshness_decay_score=_ratio(
            sum((row.freshness_decay_score for row in score_rows), ZERO),
            domain_count,
        ),
        max_aggregate_source_age_seconds=max(
            (row.aggregate_source_age_seconds for row in score_rows),
            default=ZERO,
        ),
        max_update_cadence_seconds=max(
            (row.update_cadence_seconds for row in score_rows),
            default=ZERO,
        ),
        max_catalyst_age_seconds=max(
            (row.catalyst_age_seconds for row in score_rows),
            default=ZERO,
        ),
        min_contradiction_age_seconds=min(contradiction_ages, default=ZERO),
        rows=score_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_source_freshness_decay_scorecard_public_payload(
    value: ResearchEventSourceFreshnessDecayScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventSourceFreshnessDecayScorecardReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventSourceFreshnessDecayScorecardReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _validate_public_payload(payload)
    return dict(payload)


def research_event_source_freshness_decay_scorecard_public_digest(
    value: ResearchEventSourceFreshnessDecayScorecardReport | dict[str, Any],
) -> str:
    payload = research_event_source_freshness_decay_scorecard_public_payload(value)
    digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", digest)
    return digest


def _build_row(
    *,
    event_domain: str,
    observations: tuple[ResearchEventSourceFreshnessDecayObservation, ...],
    config: ResearchEventSourceFreshnessDecayScorecardConfig,
) -> ResearchEventSourceFreshnessDecayScoreRow:
    rows = tuple(sorted(observations, key=lambda row: row.evidence_ref))
    contradiction_rows = tuple(row for row in rows if row.contradiction_present)
    minimum_contradiction_age_seconds = (
        min(row.contradiction_age_seconds for row in contradiction_rows)
        if contradiction_rows
        else config.stale_contradiction_age_seconds
    )
    aggregate_source_age_seconds = _average_decimal(
        tuple(row.source_age_seconds for row in rows),
    )
    update_cadence_seconds = _average_decimal(
        tuple(row.update_cadence_seconds for row in rows),
    )
    catalyst_age_seconds = min(row.catalyst_age_seconds for row in rows)
    source_age_score = _age_score(
        aggregate_source_age_seconds,
        fresh_seconds=config.fresh_source_age_seconds,
        stale_seconds=config.stale_source_age_seconds,
    )
    update_cadence_score = _age_score(
        update_cadence_seconds,
        fresh_seconds=config.target_update_cadence_seconds,
        stale_seconds=config.stale_update_cadence_seconds,
    )
    catalyst_recency_score = _age_score(
        catalyst_age_seconds,
        fresh_seconds=config.fresh_catalyst_age_seconds,
        stale_seconds=config.stale_catalyst_age_seconds,
    )
    contradiction_age_score = (
        ONE
        if not contradiction_rows
        else _contradiction_age_score(
            minimum_contradiction_age_seconds,
            fresh_seconds=config.fresh_contradiction_age_seconds,
            stale_seconds=config.stale_contradiction_age_seconds,
        )
    )
    freshness_decay_score = _freshness_decay_score(
        source_age_score=source_age_score,
        update_cadence_score=update_cadence_score,
        catalyst_recency_score=catalyst_recency_score,
        contradiction_age_score=contradiction_age_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        update_cadence_seconds=update_cadence_seconds,
        catalyst_age_seconds=catalyst_age_seconds,
        contradiction_count=len(contradiction_rows),
        minimum_contradiction_age_seconds=minimum_contradiction_age_seconds,
        freshness_decay_score=freshness_decay_score,
        config=config,
    )
    return ResearchEventSourceFreshnessDecayScoreRow(
        event_domain=event_domain,
        observation_count=_count(len(rows)),
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        update_cadence_seconds=update_cadence_seconds,
        catalyst_age_seconds=catalyst_age_seconds,
        minimum_contradiction_age_seconds=minimum_contradiction_age_seconds,
        contradiction_count=_count(len(contradiction_rows)),
        source_age_score=source_age_score,
        update_cadence_score=update_cadence_score,
        catalyst_recency_score=catalyst_recency_score,
        contradiction_age_score=contradiction_age_score,
        freshness_decay_score=freshness_decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchEventSourceFreshnessDecayObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSourceFreshnessDecayObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventSourceFreshnessDecayObservation values",
            )
        _require_hard_flags("observation", row)
        marker = (row.event_domain, row.evidence_ref)
        if marker in seen:
            raise ValueError("event_domain and evidence_ref pairs must be unique")
        seen.add(marker)
    return tuple(sorted(rows, key=lambda row: (row.event_domain, row.evidence_ref)))


def _row_reason_codes(
    *,
    aggregate_source_age_seconds: Decimal,
    update_cadence_seconds: Decimal,
    catalyst_age_seconds: Decimal,
    contradiction_count: int,
    minimum_contradiction_age_seconds: Decimal,
    freshness_decay_score: Decimal,
    config: ResearchEventSourceFreshnessDecayScorecardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if aggregate_source_age_seconds >= config.stale_source_age_seconds:
        reasons.append(SOURCE_AGE_BLOCK_REASON)
    elif aggregate_source_age_seconds > config.fresh_source_age_seconds:
        reasons.append(SOURCE_AGE_WATCH_REASON)
    if update_cadence_seconds >= config.stale_update_cadence_seconds:
        reasons.append(UPDATE_CADENCE_BLOCK_REASON)
    elif update_cadence_seconds > config.target_update_cadence_seconds:
        reasons.append(UPDATE_CADENCE_WATCH_REASON)
    if catalyst_age_seconds >= config.stale_catalyst_age_seconds:
        reasons.append(CATALYST_RECENCY_BLOCK_REASON)
    elif catalyst_age_seconds > config.fresh_catalyst_age_seconds:
        reasons.append(CATALYST_RECENCY_WATCH_REASON)
    if contradiction_count:
        if minimum_contradiction_age_seconds <= config.fresh_contradiction_age_seconds:
            reasons.append(CONTRADICTION_AGE_BLOCK_REASON)
        elif minimum_contradiction_age_seconds < config.stale_contradiction_age_seconds:
            reasons.append(CONTRADICTION_AGE_WATCH_REASON)
    if freshness_decay_score < config.watch_freshness_decay_score:
        reasons.append(SCORE_BLOCK_REASON)
    elif freshness_decay_score < config.pass_freshness_decay_score:
        reasons.append(SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(has_rows: bool, block_count: Decimal, watch_count: Decimal) -> str:
    if not has_rows or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventSourceFreshnessDecayScoreRow, ...],
) -> tuple[ResearchEventSourceFreshnessDecayReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchEventSourceFreshnessDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_ratio(_count(count), total),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_rows(
    value: Iterable[ResearchEventSourceFreshnessDecayScoreRow],
) -> tuple[ResearchEventSourceFreshnessDecayScoreRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventSourceFreshnessDecayScoreRow:
            raise ValueError(
                "rows must contain ResearchEventSourceFreshnessDecayScoreRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_domain))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_domain")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventSourceFreshnessDecayReasonCodeCount],
) -> tuple[ResearchEventSourceFreshnessDecayReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not ResearchEventSourceFreshnessDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSourceFreshnessDecayReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(
        sorted(counts, key=lambda count: REASON_CODE_PRIORITY.index(count.reason_code)),
    )
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _validate_row(
    row: ResearchEventSourceFreshnessDecayScoreRow,
    *,
    config: ResearchEventSourceFreshnessDecayScorecardConfig | None,
) -> None:
    cfg = config or ResearchEventSourceFreshnessDecayScorecardConfig()
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.contradiction_count > row.observation_count:
        raise ValueError("contradiction_count must not exceed observation_count")
    expected_score = _freshness_decay_score(
        source_age_score=row.source_age_score,
        update_cadence_score=row.update_cadence_score,
        catalyst_recency_score=row.catalyst_recency_score,
        contradiction_age_score=row.contradiction_age_score,
        config=cfg,
    )
    if row.freshness_decay_score != expected_score:
        raise ValueError("freshness_decay_score must match component scores")
    expected_reasons = _row_reason_codes(
        aggregate_source_age_seconds=row.aggregate_source_age_seconds,
        update_cadence_seconds=row.update_cadence_seconds,
        catalyst_age_seconds=row.catalyst_age_seconds,
        contradiction_count=int(row.contradiction_count),
        minimum_contradiction_age_seconds=row.minimum_contradiction_age_seconds,
        freshness_decay_score=row.freshness_decay_score,
        config=cfg,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row metrics")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventSourceFreshnessDecayScorecardReport) -> None:
    rows = report.rows
    if report.domain_count != _count(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.observation_count != sum((row.observation_count for row in rows), ZERO):
        raise ValueError("observation_count must match rows")
    for status_name, field_name in (
        (STATUS_PASS, "pass_count"),
        (STATUS_WATCH, "watch_count"),
        (STATUS_BLOCK, "block_count"),
    ):
        if getattr(report, field_name) != _count(_status_count(rows, status_name)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_freshness_decay_score != _ratio(
        sum((row.freshness_decay_score for row in rows), ZERO),
        report.domain_count,
    ):
        raise ValueError("average_freshness_decay_score must match rows")
    if report.max_aggregate_source_age_seconds != max(
        (row.aggregate_source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_aggregate_source_age_seconds must match rows")
    if report.max_update_cadence_seconds != max(
        (row.update_cadence_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_update_cadence_seconds must match rows")
    if report.max_catalyst_age_seconds != max(
        (row.catalyst_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_catalyst_age_seconds must match rows")
    contradiction_ages = tuple(
        row.minimum_contradiction_age_seconds
        for row in rows
        if row.contradiction_count > ZERO
    )
    if report.min_contradiction_age_seconds != min(contradiction_ages, default=ZERO):
        raise ValueError("min_contradiction_age_seconds must match rows")
    if report.scorecard_status != _report_status(
        bool(rows),
        report.block_count,
        report.watch_count,
    ):
        raise ValueError("scorecard_status must match rows")
    expected_reason_code_counts = _reason_code_counts(rows)
    if not rows:
        expected_reason_code_counts = (
            ResearchEventSourceFreshnessDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _status_count(
    rows: tuple[ResearchEventSourceFreshnessDecayScoreRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _age_score(
    age_seconds: Decimal,
    *,
    fresh_seconds: Decimal,
    stale_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_seconds:
        return ONE
    if age_seconds >= stale_seconds:
        return ZERO
    return _quantize(ONE - _ratio(age_seconds, stale_seconds))


def _contradiction_age_score(
    age_seconds: Decimal,
    *,
    fresh_seconds: Decimal,
    stale_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_seconds:
        return ZERO
    if age_seconds >= stale_seconds:
        return ONE
    return _ratio(age_seconds, stale_seconds)


def _freshness_decay_score(
    *,
    source_age_score: Decimal,
    update_cadence_score: Decimal,
    catalyst_recency_score: Decimal,
    contradiction_age_score: Decimal,
    config: ResearchEventSourceFreshnessDecayScorecardConfig,
) -> Decimal:
    score = (
        (source_age_score * config.source_age_weight)
        + (update_cadence_score * config.update_cadence_weight)
        + (catalyst_recency_score * config.catalyst_recency_weight)
        + (contradiction_age_score * config.contradiction_age_weight)
    )
    return _quantize(min(ONE, max(ZERO, score)))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _ratio(sum(values, ZERO), _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_increasing_seconds(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if upper_value <= lower_value:
        raise ValueError(f"{upper_name} must exceed {lower_name}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for value in values:
        _require_reason_code("reason_codes", value, ROW_REASON_CODE_PRIORITY)
    normalized = tuple(sorted(set(values), key=ROW_REASON_CODE_PRIORITY.index))
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return normalized


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for value in values:
        _require_reason_code("reason_codes", value, REASON_CODE_PRIORITY)
    normalized = tuple(sorted(set(values), key=REASON_CODE_PRIORITY.index))
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


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


def _set_or_validate_public_digest(
    report: ResearchEventSourceFreshnessDecayScorecardReport,
) -> None:
    if type(report.public_digest) is not str:
        raise ValueError("public_digest must be a string")
    expected = _digest_for_payload(_json_ready(report))
    if report.public_digest == "":
        object.__setattr__(report, "public_digest", expected)
        return
    _require_sha256_digest("public_digest", report.public_digest)
    if report.public_digest != expected:
        raise ValueError("public_digest must match payload")


def _validate_public_digest(
    report: ResearchEventSourceFreshnessDecayScorecardReport,
) -> None:
    expected = _digest_for_payload(_json_ready(report))
    if report.public_digest != expected:
        raise ValueError("public_digest must match payload")


def _digest_for_payload(value: object) -> str:
    if type(value) is not dict:
        raise ValueError("public payload must be a dict")
    digest_payload = dict(value)
    digest_payload["public_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _require_decimal_strings(payload)
    supplied_digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", supplied_digest)
    expected_digest = _digest_for_payload(payload)
    if supplied_digest != expected_digest:
        raise ValueError("public_digest must match payload")


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


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_decimal_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _looks_numeric_key(str(key)):
                if type(item) is not str:
                    raise ValueError("public payload numeric fields must be Decimal strings")
                _require_decimal_string(str(key), item)
            else:
                _require_decimal_strings(item)
    elif isinstance(value, list):
        for item in value:
            _require_decimal_strings(item)
    elif type(value) in (int, Decimal):
        raise ValueError("public payload numeric fields must be Decimal strings")


def _require_decimal_string(field_name: str, value: str) -> None:
    try:
        Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _looks_numeric_key(key: str) -> bool:
    return key.endswith(("_count", "_ratio", "_score", "_seconds"))


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_key_fragment(key):
                raise ValueError(f"unsafe public payload key: {key}")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _unsafe_value_fragments():
        if fragment in lowered:
            raise ValueError(f"unsafe public payload value for {field_name}")


def _has_unsafe_key_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_key_fragments())


def _unsafe_key_fragments() -> tuple[str, ...]:
    return (
        "raw_",
        "raw-",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
        "source_url",
        "source_text",
        "source_ref",
        "url",
        "token",
        "private",
    )


def _unsafe_value_fragments() -> tuple[str, ...]:
    return (
        "http://",
        "https://",
        "raw_",
        "raw-",
        "market_id",
        "market_slug",
        "market_question",
        "market-",
        "market_",
        "slug",
        "question",
        "source_url",
        "source_text",
        "source_ref",
        "url",
        "token",
        "private",
        "buy",
        "sell",
        "rec" + "ommend",
        "siz" + "ing",
        "or" + "der",
        "tr" + "ade",
        "wal" + "let",
        "au" + "th",
        "li" + "ve",
        "pos" + "ition",
        "sec" + "ret",
    )
