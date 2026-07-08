"""Pure report-only prioritizer for candidate event evidence gaps.

Callers provide typed, local research evidence snapshots. The module returns
deterministic public summaries for human collection workflow review.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-candidate-evidence-gap-prioritizer-v0"
STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_REASON = "evidence_gap_priority_pass"
WATCH_REASON = "evidence_gap_priority_watch"
BLOCK_REASON = "evidence_gap_priority_block"
NO_EVIDENCE_REASON = "no_candidate_evidence"
COVERAGE_REASON = "coverage_gap_present"
CONFLICT_REASON = "conflict_present"
STALE_REASON = "stale_evidence_present"
RELIABILITY_REASON = "low_reliability_present"
ITEM_FLOOR_REASON = "insufficient_evidence_items"
FAMILY_FLOOR_REASON = "insufficient_source_family"
HARD_GAP_REASON = "manual_hard_gap_flag"
READY_REASON = "manual_collection_ready"

STATUS_REASON_CODES = {
    "pass": PASS_REASON,
    "watch": WATCH_REASON,
    "block": BLOCK_REASON,
}

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "market",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "position",
    "buy",
    "sell",
    "recommend",
)


@dataclass(frozen=True)
class ResearchCandidateEvidenceGapPrioritizerConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_evidence_item_count: Decimal = Decimal("2.000000")
    min_source_family_count: Decimal = Decimal("2.000000")
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    min_coverage_score: Decimal = Decimal("0.750000")
    min_reliability_score: Decimal = Decimal("0.700000")
    pass_gap_priority_score: Decimal = Decimal("0.250000")
    block_gap_priority_score: Decimal = Decimal("0.650000")
    coverage_gap_weight: Decimal = Decimal("0.400000")
    conflict_weight: Decimal = Decimal("0.250000")
    recency_gap_weight: Decimal = Decimal("0.200000")
    reliability_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEvidenceGapPrioritizerConfig:
            raise TypeError(
                "ResearchCandidateEvidenceGapPrioritizerConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateEvidenceGapPrioritizerConfig:
            raise ValueError(
                "config must be exactly ResearchCandidateEvidenceGapPrioritizerConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in ("min_evidence_item_count", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "min_coverage_score",
            "min_reliability_score",
            "pass_gap_priority_score",
            "block_gap_priority_score",
            "coverage_gap_weight",
            "conflict_weight",
            "recency_gap_weight",
            "reliability_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_gap_priority_score <= self.pass_gap_priority_score:
            raise ValueError(
                "block_gap_priority_score must be greater than pass_gap_priority_score",
            )
        weight_sum = _normalize_probability(
            "gap priority weight sum",
            self.coverage_gap_weight
            + self.conflict_weight
            + self.recency_gap_weight
            + self.reliability_gap_weight,
        )
        if weight_sum != ONE:
            raise ValueError("gap priority weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateEvidenceGapItem:
    candidate_key: str
    evidence_key: str
    source_family: str
    observed_at: datetime
    evidence_coverage_score: Decimal
    source_reliability_score: Decimal
    conflict_flag: bool = False
    hard_gap_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEvidenceGapItem:
            raise TypeError(
                "ResearchCandidateEvidenceGapItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateEvidenceGapItem:
            raise ValueError("item must be exactly ResearchCandidateEvidenceGapItem")
        for field_name in ("candidate_key", "evidence_key", "source_family"):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("evidence_coverage_score", "source_reliability_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if type(self.conflict_flag) is not bool:
            raise ValueError("conflict_flag must be a bool")
        if type(self.hard_gap_flag) is not bool:
            raise ValueError("hard_gap_flag must be a bool")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchCandidateEvidenceGapPriorityRow:
    event_slot: str
    evidence_item_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    coverage_score: Decimal
    coverage_gap_score: Decimal
    conflict_score: Decimal
    recency_score: Decimal
    recency_gap_score: Decimal
    reliability_score: Decimal
    reliability_gap_score: Decimal
    gap_priority_score: Decimal
    stale_item_count: Decimal
    conflict_item_count: Decimal
    low_reliability_item_count: Decimal
    hard_gap_flag_count: Decimal
    manual_collection_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEvidenceGapPriorityRow:
            raise TypeError(
                "ResearchCandidateEvidenceGapPriorityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateEvidenceGapPriorityRow:
            raise ValueError(
                "row must be exactly ResearchCandidateEvidenceGapPriorityRow",
            )
        _require_public_string("event_slot", self.event_slot)
        for field_name in (
            "evidence_item_count",
            "source_family_count",
            "stale_item_count",
            "conflict_item_count",
            "low_reliability_item_count",
            "hard_gap_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        for field_name in (
            "coverage_score",
            "coverage_gap_score",
            "conflict_score",
            "recency_score",
            "recency_gap_score",
            "reliability_score",
            "reliability_gap_score",
            "gap_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("manual_collection_status", self.manual_collection_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchCandidateEvidenceGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEvidenceGapReasonCodeCount:
            raise TypeError(
                "ResearchCandidateEvidenceGapReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateEvidenceGapReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchCandidateEvidenceGapReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchCandidateEvidenceGapPrioritizerReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    evidence_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_gap_priority_score: Decimal
    status: str
    rows: tuple[ResearchCandidateEvidenceGapPriorityRow, ...]
    reason_code_counts: tuple[ResearchCandidateEvidenceGapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEvidenceGapPrioritizerReport:
            raise TypeError(
                "ResearchCandidateEvidenceGapPrioritizerReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateEvidenceGapPrioritizerReport:
            raise ValueError(
                "report must be exactly ResearchCandidateEvidenceGapPrioritizerReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "evidence_item_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_gap_priority_score",
            _normalize_probability("max_gap_priority_score", self.max_gap_priority_score),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_candidate_evidence_gap_prioritizer_public_payload(self)


def build_research_candidate_evidence_gap_prioritizer_report(
    evidence_items: Iterable[ResearchCandidateEvidenceGapItem],
    *,
    config: ResearchCandidateEvidenceGapPrioritizerConfig,
    generated_at: datetime,
) -> ResearchCandidateEvidenceGapPrioritizerReport:
    if type(config) is not ResearchCandidateEvidenceGapPrioritizerConfig:
        raise ValueError(
            "config must be a ResearchCandidateEvidenceGapPrioritizerConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_evidence_items(evidence_items, generated_at_utc)
    grouped: dict[str, list[ResearchCandidateEvidenceGapItem]] = {}
    for item in normalized_items:
        grouped.setdefault(item.candidate_key, []).append(item)

    rows = tuple(
        _row_for_candidate(
            candidate_key=candidate_key,
            event_slot=f"event-{index:03d}",
            evidence_items=tuple(grouped[candidate_key]),
            config=config,
            generated_at=generated_at_utc,
        )
        for index, candidate_key in enumerate(sorted(grouped), start=1)
    )
    reason_codes = _report_reason_codes(rows)

    return ResearchCandidateEvidenceGapPrioritizerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        evidence_item_count=sum((row.evidence_item_count for row in rows), ZERO),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        max_gap_priority_score=max((row.gap_priority_score for row in rows), default=ZERO),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_candidate_evidence_gap_prioritizer_public_payload(
    value: ResearchCandidateEvidenceGapPrioritizerReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchCandidateEvidenceGapPrioritizerReport:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchCandidateEvidenceGapPrioritizerReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_candidate_evidence_gap_prioritizer_public_payload(payload)
    return dict(payload)


def validate_research_candidate_evidence_gap_prioritizer_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    _require_public_status_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != research_candidate_evidence_gap_prioritizer_public_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def research_candidate_evidence_gap_prioritizer_public_digest(
    value: ResearchCandidateEvidenceGapPrioritizerReport | dict[str, Any],
) -> str:
    if type(value) is ResearchCandidateEvidenceGapPrioritizerReport:
        return _derived_validation_digest(value)
    if type(value) is dict:
        return _derived_validation_digest(value)
    raise ValueError(
        "value must be a ResearchCandidateEvidenceGapPrioritizerReport or dict",
    )


def _row_for_candidate(
    *,
    candidate_key: str,
    event_slot: str,
    evidence_items: tuple[ResearchCandidateEvidenceGapItem, ...],
    config: ResearchCandidateEvidenceGapPrioritizerConfig,
    generated_at: datetime,
) -> ResearchCandidateEvidenceGapPriorityRow:
    sorted_items = tuple(sorted(evidence_items, key=_item_sort_key))
    ages = tuple(_seconds_between(item.observed_at, generated_at) for item in sorted_items)
    latest_age = min(ages)
    recency_scores = tuple(
        _recency_score(
            age,
            fresh_age_seconds=config.fresh_age_seconds,
            stale_age_seconds=config.stale_age_seconds,
        )
        for age in ages
    )
    coverage_score = _average_decimal(
        tuple(item.evidence_coverage_score for item in sorted_items),
    )
    recency_score = _average_decimal(recency_scores)
    reliability_score = _average_decimal(
        tuple(item.source_reliability_score for item in sorted_items),
    )
    coverage_gap_score = _probability_delta(ONE, coverage_score)
    recency_gap_score = _probability_delta(ONE, recency_score)
    reliability_gap_score = _probability_delta(ONE, reliability_score)
    conflict_item_count = sum(1 for item in sorted_items if item.conflict_flag)
    conflict_score = _normalize_probability(
        "conflict_score",
        Decimal(conflict_item_count) / Decimal(len(sorted_items)),
    )
    gap_priority_score = _gap_priority_score(
        coverage_gap_score=coverage_gap_score,
        conflict_score=conflict_score,
        recency_gap_score=recency_gap_score,
        reliability_gap_score=reliability_gap_score,
        config=config,
    )
    source_family_count = len({item.source_family for item in sorted_items})
    stale_item_count = sum(1 for age in ages if age >= config.stale_age_seconds)
    low_reliability_item_count = sum(
        1
        for item in sorted_items
        if item.source_reliability_score < config.min_reliability_score
    )
    hard_gap_flag_count = sum(1 for item in sorted_items if item.hard_gap_flag)
    status = _row_status(
        evidence_item_count=len(sorted_items),
        source_family_count=source_family_count,
        conflict_item_count=conflict_item_count,
        hard_gap_flag_count=hard_gap_flag_count,
        gap_priority_score=gap_priority_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        evidence_item_count=len(sorted_items),
        source_family_count=source_family_count,
        coverage_score=coverage_score,
        stale_item_count=stale_item_count,
        conflict_item_count=conflict_item_count,
        low_reliability_item_count=low_reliability_item_count,
        hard_gap_flag_count=hard_gap_flag_count,
        config=config,
    )

    return ResearchCandidateEvidenceGapPriorityRow(
        event_slot=event_slot,
        evidence_item_count=_count(len(sorted_items)),
        source_family_count=_count(source_family_count),
        latest_evidence_age_seconds=latest_age,
        coverage_score=coverage_score,
        coverage_gap_score=coverage_gap_score,
        conflict_score=conflict_score,
        recency_score=recency_score,
        recency_gap_score=recency_gap_score,
        reliability_score=reliability_score,
        reliability_gap_score=reliability_gap_score,
        gap_priority_score=gap_priority_score,
        stale_item_count=_count(stale_item_count),
        conflict_item_count=_count(conflict_item_count),
        low_reliability_item_count=_count(low_reliability_item_count),
        hard_gap_flag_count=_count(hard_gap_flag_count),
        manual_collection_status=status,
        reason_codes=reason_codes,
    )


def _normalize_evidence_items(
    value: Iterable[ResearchCandidateEvidenceGapItem],
    generated_at: datetime,
) -> tuple[ResearchCandidateEvidenceGapItem, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence_items must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchCandidateEvidenceGapItem:
            raise ValueError(
                "evidence_items must contain ResearchCandidateEvidenceGapItem values",
            )
        _require_hard_flags("item", item)
        unique_key = (item.candidate_key, item.evidence_key)
        if unique_key in seen_keys:
            raise ValueError("evidence_key values must be unique per candidate_key")
        seen_keys.add(unique_key)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(sorted(items, key=_item_sort_key))


def _row_status(
    *,
    evidence_item_count: int,
    source_family_count: int,
    conflict_item_count: int,
    hard_gap_flag_count: int,
    gap_priority_score: Decimal,
    config: ResearchCandidateEvidenceGapPrioritizerConfig,
) -> str:
    if hard_gap_flag_count:
        return "block"
    if Decimal(evidence_item_count) < config.min_evidence_item_count:
        return "block"
    if gap_priority_score >= config.block_gap_priority_score:
        return "block"
    if gap_priority_score > config.pass_gap_priority_score:
        return "watch"
    if Decimal(source_family_count) < config.min_source_family_count:
        return "watch"
    if conflict_item_count:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    evidence_item_count: int,
    source_family_count: int,
    coverage_score: Decimal,
    stale_item_count: int,
    conflict_item_count: int,
    low_reliability_item_count: int,
    hard_gap_flag_count: int,
    config: ResearchCandidateEvidenceGapPrioritizerConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {STATUS_REASON_CODES[status]}
    if status == "pass":
        reason_codes.add(READY_REASON)
    if Decimal(evidence_item_count) < config.min_evidence_item_count:
        reason_codes.add(ITEM_FLOOR_REASON)
    if Decimal(source_family_count) < config.min_source_family_count:
        reason_codes.add(FAMILY_FLOOR_REASON)
    if coverage_score < config.min_coverage_score:
        reason_codes.add(COVERAGE_REASON)
    if stale_item_count:
        reason_codes.add(STALE_REASON)
    if conflict_item_count:
        reason_codes.add(CONFLICT_REASON)
    if low_reliability_item_count:
        reason_codes.add(RELIABILITY_REASON)
    if hard_gap_flag_count:
        reason_codes.add(HARD_GAP_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchCandidateEvidenceGapPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON,)
    if all(row.manual_collection_status == "pass" for row in rows):
        return (PASS_REASON,)
    reason_codes = {
        code
        for row in rows
        for code in row.reason_codes
        if code not in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    }
    if any(row.manual_collection_status == "block" for row in rows):
        reason_codes.add(BLOCK_REASON)
    else:
        reason_codes.add(WATCH_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if BLOCK_REASON in reason_codes or NO_EVIDENCE_REASON in reason_codes:
        return "block"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchCandidateEvidenceGapPriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCandidateEvidenceGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCandidateEvidenceGapReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchCandidateEvidenceGapReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _gap_priority_score(
    *,
    coverage_gap_score: Decimal,
    conflict_score: Decimal,
    recency_gap_score: Decimal,
    reliability_gap_score: Decimal,
    config: ResearchCandidateEvidenceGapPrioritizerConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            coverage_gap_score * config.coverage_gap_weight
            + conflict_score * config.conflict_weight
            + recency_gap_score * config.recency_gap_weight
            + reliability_gap_score * config.reliability_gap_weight
        )
    return _normalize_probability("gap_priority_score", score)


def _recency_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return ONE
    if age_seconds >= stale_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "recency_score",
            ONE - (age_seconds / stale_age_seconds),
        )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average",
            sum(values, ZERO) / Decimal(len(values)),
        )


def _probability_delta(value: Decimal, offset: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = value - offset
    if result <= ZERO:
        return ZERO
    return _normalize_probability("probability_delta", result)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("observed_at must not be after generated_at")
    return _normalize_nonnegative_decimal(
        "age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _status_count(
    rows: tuple[ResearchCandidateEvidenceGapPriorityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.manual_collection_status == status)


def _normalize_rows(
    value: object,
) -> tuple[ResearchCandidateEvidenceGapPriorityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchCandidateEvidenceGapPriorityRow:
            raise ValueError(
                "rows must contain ResearchCandidateEvidenceGapPriorityRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(value, key=lambda row: row.event_slot))
    if value != sorted_rows:
        raise ValueError("rows must be sorted by event_slot")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCandidateEvidenceGapReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in value:
        if type(count) is not ResearchCandidateEvidenceGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCandidateEvidenceGapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(value, key=lambda count: count.reason_code))
    if value != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return value


def _validate_row(row: ResearchCandidateEvidenceGapPriorityRow) -> None:
    if row.evidence_item_count <= ZERO:
        raise ValueError("evidence_item_count must be positive")
    if row.source_family_count > row.evidence_item_count:
        raise ValueError("source_family_count must not exceed evidence_item_count")
    if row.stale_item_count > row.evidence_item_count:
        raise ValueError("stale_item_count must not exceed evidence_item_count")
    if row.conflict_item_count > row.evidence_item_count:
        raise ValueError("conflict_item_count must not exceed evidence_item_count")
    if row.low_reliability_item_count > row.evidence_item_count:
        raise ValueError(
            "low_reliability_item_count must not exceed evidence_item_count",
        )
    if row.hard_gap_flag_count > row.evidence_item_count:
        raise ValueError("hard_gap_flag_count must not exceed evidence_item_count")
    if row.manual_collection_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("manual_collection_status must match reason_codes")


def _validate_report(report: ResearchCandidateEvidenceGapPrioritizerReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.evidence_item_count != sum(
        (row.evidence_item_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("evidence_item_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_gap_priority_score != max(
        (row.gap_priority_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_gap_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    if reason_codes == (PASS_REASON, READY_REASON):
        return "pass"
    raise ValueError("reason_codes must include exactly one status reason")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _set_or_validate_derived_validation_digest(
    report: ResearchCandidateEvidenceGapPrioritizerReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchCandidateEvidenceGapPrioritizerReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_status_values(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key.endswith("status") or key == "status":
                if item not in STATUSES:
                    raise ValueError(f"{key} must be one of {STATUSES}")
            _require_public_status_values(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_status_values(item)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(VALUE_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        normalized.append(item)
    codes = tuple(sorted(set(normalized)))
    status_reason_count = sum(
        1 for code in codes if code in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    )
    if status_reason_count > 1:
        raise ValueError(f"{field_name} must contain one status reason")
    if NO_EVIDENCE_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} no evidence reason must stand alone")
    return codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _item_sort_key(
    item: ResearchCandidateEvidenceGapItem,
) -> tuple[str, str, str, str]:
    return (
        item.candidate_key,
        item.evidence_key,
        item.source_family,
        item.observed_at.isoformat(),
    )


__all__ = (
    "ResearchCandidateEvidenceGapItem",
    "ResearchCandidateEvidenceGapPrioritizerConfig",
    "ResearchCandidateEvidenceGapPrioritizerReport",
    "ResearchCandidateEvidenceGapPriorityRow",
    "ResearchCandidateEvidenceGapReasonCodeCount",
    "build_research_candidate_evidence_gap_prioritizer_report",
    "research_candidate_evidence_gap_prioritizer_public_digest",
    "research_candidate_evidence_gap_prioritizer_public_payload",
    "validate_research_candidate_evidence_gap_prioritizer_public_payload",
)
