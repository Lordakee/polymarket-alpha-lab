"""Report-only primary-claim conflict resolution ladder for research sources."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_CONFLICT_RESOLUTION_LADDER_CONFIG_VERSION = (
    "research-source-primary-claim-conflict-resolution-ladder-report-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUSES = ("pass", "watch", "block")
CLAIM_POSITIONS = ("affirmed", "disputed")
LADDER_STEPS = (
    "unresolved_primary_conflict",
    "precedence_ladder_review",
    "thin_primary_claim_support",
    "primary_claim_consensus",
)
ROW_REASON_CODES = (
    "unresolved_primary_conflict",
    "precedence_ladder_review",
    "stale_primary_claim_inputs",
    "thin_primary_claim_support",
    "primary_claim_consensus_clear",
)
REPORT_REASON_CODES = (
    "no_primary_claim_inputs",
    "unresolved_primary_conflict",
    "precedence_ladder_review",
    "stale_primary_claim_inputs",
    "thin_primary_claim_support",
    "primary_claim_consensus_clear",
)
UNSAFE_PUBLIC_TERMS = (
    "auth",
    "buy",
    "candidate",
    "database",
    "dsn",
    "http",
    "live",
    "market",
    "network",
    "order",
    "position",
    "question",
    "recommend",
    "sell",
    "sizing",
    "slug",
    "source_text",
    "table",
    "token",
    "trade",
    "url",
    "wallet",
)


__all__ = (
    "ResearchSourcePrimaryClaimConflictResolutionLadderConfig",
    "ResearchSourcePrimaryClaimConflictResolutionLadderInput",
    "ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount",
    "ResearchSourcePrimaryClaimConflictResolutionLadderReport",
    "ResearchSourcePrimaryClaimConflictResolutionLadderRow",
    "build_research_source_primary_claim_conflict_resolution_ladder_report",
    "research_source_primary_claim_conflict_resolution_ladder_report_digest",
    "research_source_primary_claim_conflict_resolution_ladder_report_payload",
)


class _FinalFrozenDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _FinalFrozenDataclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} is final")


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimConflictResolutionLadderConfig(_FinalFrozenDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_CONFLICT_RESOLUTION_LADDER_CONFIG_VERSION
    )
    stale_after_seconds: Decimal = Decimal("86400.000000")
    min_primary_count: Decimal = Decimal("2")
    min_independent_family_count: Decimal = Decimal("2")
    precedence_override_gap: Decimal = Decimal("2")
    min_pass_resolution_score: Decimal = Decimal("0.700000")
    min_watch_resolution_score: Decimal = Decimal("0.450000")
    stale_penalty: Decimal = Decimal("0.200000")
    unresolved_conflict_penalty: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_after_seconds",
            _normalize_positive_seconds("stale_after_seconds", self.stale_after_seconds),
        )
        for field_name in (
            "min_primary_count",
            "min_independent_family_count",
            "precedence_override_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_resolution_score",
            "min_watch_resolution_score",
            "stale_penalty",
            "unresolved_conflict_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if self.min_watch_resolution_score > self.min_pass_resolution_score:
            raise ValueError(
                "min_watch_resolution_score must not exceed min_pass_resolution_score",
            )
        _validate_config(self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimConflictResolutionLadderInput(_FinalFrozenDataclass):
    claim_ref: str
    reference_ref: str
    family_ref: str
    claim_position: str
    primary: bool
    precedence_rank: Decimal
    observed_at: datetime
    confidence_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("claim_ref", "reference_ref", "family_ref"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("claim_position", self.claim_position, CLAIM_POSITIONS)
        if type(self.primary) is not bool:
            raise ValueError("primary must be a bool")
        object.__setattr__(
            self,
            "precedence_rank",
            _normalize_positive_count("precedence_rank", self.precedence_rank),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _normalize_score("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_input(self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimConflictResolutionLadderRow(_FinalFrozenDataclass):
    claim_digest: str
    status: str
    ladder_step: str
    reference_count: Decimal
    primary_count: Decimal
    family_count: Decimal
    conflicting_primary_count: Decimal
    stale_reference_count: Decimal
    top_precedence_rank: Decimal
    runner_up_precedence_rank: Decimal
    precedence_gap: Decimal
    average_confidence_score: Decimal
    resolution_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_reference("claim_digest", self.claim_digest)
        _require_member("status", self.status, STATUSES)
        _require_member("ladder_step", self.ladder_step, LADDER_STEPS)
        for field_name in (
            "reference_count",
            "primary_count",
            "family_count",
            "conflicting_primary_count",
            "stale_reference_count",
            "top_precedence_rank",
            "runner_up_precedence_rank",
            "precedence_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "resolution_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount(
    _FinalFrozenDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _validate_reason_code_count(self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimConflictResolutionLadderReport(_FinalFrozenDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig
    status: str
    claim_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    conflict_count: Decimal
    stale_count: Decimal
    average_resolution_score: Decimal
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...]
    reason_code_counts: tuple[
        ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if type(self.config) is not ResearchSourcePrimaryClaimConflictResolutionLadderConfig:
            raise ValueError(
                "config must be a "
                "ResearchSourcePrimaryClaimConflictResolutionLadderConfig",
            )
        _validate_config(self.config)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "claim_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "conflict_count",
            "stale_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_resolution_score",
            _normalize_score(
                "average_resolution_score",
                self.average_resolution_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_source_primary_claim_conflict_resolution_ladder_report(
    rows: list[ResearchSourcePrimaryClaimConflictResolutionLadderInput]
    | tuple[ResearchSourcePrimaryClaimConflictResolutionLadderInput, ...],
    *,
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryClaimConflictResolutionLadderReport:
    if type(config) is not ResearchSourcePrimaryClaimConflictResolutionLadderConfig:
        raise ValueError(
            "config must be a "
            "ResearchSourcePrimaryClaimConflictResolutionLadderConfig",
        )
    _validate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_source_rows(rows)
    for row in inputs:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")

    grouped: dict[str, list[ResearchSourcePrimaryClaimConflictResolutionLadderInput]] = {}
    for row in inputs:
        grouped.setdefault(row.claim_ref, []).append(row)

    report_rows = tuple(
        sorted(
            (
                _row_for_claim(
                    claim_ref=claim_ref,
                    rows=tuple(grouped[claim_ref]),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for claim_ref in grouped
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows, len(inputs))
    reason_code_counts = _reason_code_counts(report_rows, reason_codes)

    return ResearchSourcePrimaryClaimConflictResolutionLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        status=_report_status(report_rows),
        claim_count=_count(len(report_rows)),
        input_count=_count(len(inputs)),
        pass_count=_status_count(report_rows, "pass"),
        watch_count=_status_count(report_rows, "watch"),
        block_count=_status_count(report_rows, "block"),
        conflict_count=_count(
            sum(
                1
                for row in report_rows
                if row.conflicting_primary_count > ZERO_COUNT
            ),
        ),
        stale_count=_count(
            sum(
                1
                for row in report_rows
                if row.stale_reference_count > ZERO_COUNT
            ),
        ),
        average_resolution_score=_average_score(
            tuple(row.resolution_score for row in report_rows),
        ),
        rows=report_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_source_primary_claim_conflict_resolution_ladder_report_payload(
    report: ResearchSourcePrimaryClaimConflictResolutionLadderReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchSourcePrimaryClaimConflictResolutionLadderReport:
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _thaw_json_object(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchSourcePrimaryClaimConflictResolutionLadderReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    _validate_public_payload(payload)
    return _freeze_json_object(payload)


def research_source_primary_claim_conflict_resolution_ladder_report_digest(
    report: ResearchSourcePrimaryClaimConflictResolutionLadderReport,
) -> str:
    if type(report) is not ResearchSourcePrimaryClaimConflictResolutionLadderReport:
        raise ValueError(
            "report must be a "
            "ResearchSourcePrimaryClaimConflictResolutionLadderReport",
        )
    _validate_report(report)
    return _report_digest(report)


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


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _normalize_source_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimConflictResolutionLadderInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryClaimConflictResolutionLadderInput:
            raise ValueError(
                "rows must contain "
                "ResearchSourcePrimaryClaimConflictResolutionLadderInput values",
            )
        _validate_input(row)
        key = (row.claim_ref, row.reference_ref)
        if key in seen_refs:
            raise ValueError("duplicate claim_ref and reference_ref values are not allowed")
        seen_refs.add(key)
    return rows


def _row_for_claim(
    *,
    claim_ref: str,
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderInput, ...],
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryClaimConflictResolutionLadderRow:
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.claim_position,
                row.family_ref,
                row.reference_ref,
            ),
        ),
    )
    primary_rows = tuple(row for row in sorted_rows if row.primary)
    primary_positions = {row.claim_position for row in primary_rows}
    reference_count = _count(len(sorted_rows))
    primary_count = _count(len(primary_rows))
    family_count = _count(len({row.family_ref for row in primary_rows}))
    stale_count = _count(
        sum(
            1
            for row in sorted_rows
            if _age_seconds(row.observed_at, generated_at) > config.stale_after_seconds
        ),
    )
    average_confidence = _average_score(tuple(row.confidence_score for row in primary_rows))
    top_rank, runner_up_rank = _precedence_ranks_by_position(primary_rows)
    precedence_gap = _precedence_gap(top_rank, runner_up_rank)
    has_conflict = len(primary_positions) > 1
    stale_penalty = config.stale_penalty if stale_count > ZERO_COUNT else ZERO_SCORE

    if not primary_rows or primary_count < config.min_primary_count:
        ladder_step = "thin_primary_claim_support"
        resolution_score = _resolution_score(average_confidence, stale_penalty)
        status = _score_status(resolution_score, config=config, force_watch=True)
    elif has_conflict and precedence_gap < config.precedence_override_gap:
        ladder_step = "unresolved_primary_conflict"
        resolution_score = _resolution_score(
            average_confidence,
            stale_penalty,
            config.unresolved_conflict_penalty,
        )
        status = "block"
    elif has_conflict:
        ladder_step = "precedence_ladder_review"
        resolution_score = _resolution_score(average_confidence, stale_penalty)
        status = "watch"
    else:
        ladder_step = "primary_claim_consensus"
        resolution_score = _resolution_score(average_confidence, stale_penalty)
        status = _score_status(resolution_score, config=config, force_watch=False)
        if family_count < config.min_independent_family_count and status == "pass":
            status = "watch"
            ladder_step = "thin_primary_claim_support"

    reason_codes = _row_reason_codes(
        ladder_step=ladder_step,
        stale_count=stale_count,
    )

    return ResearchSourcePrimaryClaimConflictResolutionLadderRow(
        claim_digest=_digest_reference(claim_ref),
        status=status,
        ladder_step=ladder_step,
        reference_count=reference_count,
        primary_count=primary_count,
        family_count=family_count,
        conflicting_primary_count=primary_count if has_conflict else ZERO_COUNT,
        stale_reference_count=stale_count,
        top_precedence_rank=top_rank,
        runner_up_precedence_rank=runner_up_rank,
        precedence_gap=precedence_gap,
        average_confidence_score=average_confidence,
        resolution_score=resolution_score,
        reason_codes=reason_codes,
    )


def _precedence_ranks_by_position(
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderInput, ...],
) -> tuple[Decimal, Decimal]:
    if not rows:
        return ZERO_COUNT, ZERO_COUNT
    position_ranks: dict[str, Decimal] = {}
    for row in rows:
        current = position_ranks.get(row.claim_position, ZERO_COUNT)
        position_ranks[row.claim_position] = max(current, row.precedence_rank)
    sorted_ranks = tuple(sorted(position_ranks.values(), reverse=True))
    top_rank = sorted_ranks[0]
    runner_up_rank = sorted_ranks[1] if len(sorted_ranks) > 1 else ZERO_COUNT
    return top_rank, runner_up_rank


def _row_reason_codes(*, ladder_step: str, stale_count: Decimal) -> tuple[str, ...]:
    reason_code = (
        "primary_claim_consensus_clear"
        if ladder_step == "primary_claim_consensus"
        else ladder_step
    )
    codes = [reason_code]
    if stale_count > ZERO_COUNT:
        codes.append("stale_primary_claim_inputs")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _score_status(
    resolution_score: Decimal,
    *,
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
    force_watch: bool,
) -> str:
    if resolution_score < config.min_watch_resolution_score:
        return "block"
    if force_watch or resolution_score < config.min_pass_resolution_score:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...],
    input_count: int,
) -> tuple[str, ...]:
    if input_count == 0:
        return ("no_primary_claim_inputs",)
    codes = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _reason_code_counts(
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount(
                reason_code=reason_codes[0],
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REPORT_REASON_CODES.index(item[0]),
        )
    )


def _status_count(
    rows: tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        average = sum(values, ZERO_SCORE) / _count(len(values))
    return _normalize_score("average_score", average)


def _precedence_gap(top_rank: Decimal, runner_up_rank: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        difference = top_rank - runner_up_rank
    return _normalize_nonnegative_count("precedence_gap", max(ZERO_COUNT, difference))


def _resolution_score(
    average_confidence_score: Decimal,
    stale_penalty: Decimal,
    unresolved_conflict_penalty: Decimal = ZERO_SCORE,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            average_confidence_score
            - stale_penalty
            - unresolved_conflict_penalty
        )
    return _clamped_score(score)


def _row_sort_key(
    row: ResearchSourcePrimaryClaimConflictResolutionLadderRow,
) -> tuple[int, str]:
    return (STATUSES[::-1].index(row.status), row.claim_digest)


def _validate_config(
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
) -> None:
    _require_public_string("config_version", config.config_version)
    _require_canonical_decimal(
        "stale_after_seconds",
        config.stale_after_seconds,
        _normalize_positive_seconds,
    )
    for field_name in (
        "min_primary_count",
        "min_independent_family_count",
        "precedence_override_gap",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(config, field_name),
            _normalize_positive_count,
        )
    for field_name in (
        "min_pass_resolution_score",
        "min_watch_resolution_score",
        "stale_penalty",
        "unresolved_conflict_penalty",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(config, field_name),
            _normalize_score,
        )
    if config.min_watch_resolution_score > config.min_pass_resolution_score:
        raise ValueError(
            "min_watch_resolution_score must not exceed min_pass_resolution_score",
        )
    _require_hard_flags("config", config)


def _validate_input(
    row: ResearchSourcePrimaryClaimConflictResolutionLadderInput,
) -> None:
    for field_name in ("claim_ref", "reference_ref", "family_ref"):
        _require_public_string(field_name, getattr(row, field_name))
    _require_member("claim_position", row.claim_position, CLAIM_POSITIONS)
    if type(row.primary) is not bool:
        raise ValueError("primary must be a bool")
    _require_canonical_decimal(
        "precedence_rank",
        row.precedence_rank,
        _normalize_positive_count,
    )
    if type(row.observed_at) is not datetime or row.observed_at.tzinfo is not UTC:
        raise ValueError("observed_at must be a canonical UTC datetime")
    _require_canonical_decimal(
        "confidence_score",
        row.confidence_score,
        _normalize_score,
    )
    if row.reason_codes != _normalize_input_reason_codes(
        "reason_codes",
        row.reason_codes,
    ):
        raise ValueError("reason_codes must be canonical")
    _require_hard_flags("input", row)


def _validate_reason_code_count(
    reason_code_count: ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount,
) -> None:
    _require_member(
        "reason_code",
        reason_code_count.reason_code,
        REPORT_REASON_CODES,
    )
    _require_canonical_decimal(
        "reason_code_count",
        reason_code_count.count,
        _normalize_positive_count,
    )
    _require_hard_flags("reason_code_count", reason_code_count)


def _validate_row(row: ResearchSourcePrimaryClaimConflictResolutionLadderRow) -> None:
    _require_digest_reference("claim_digest", row.claim_digest)
    _require_member("status", row.status, STATUSES)
    _require_member("ladder_step", row.ladder_step, LADDER_STEPS)
    for field_name in (
        "reference_count",
        "primary_count",
        "family_count",
        "conflicting_primary_count",
        "stale_reference_count",
        "top_precedence_rank",
        "runner_up_precedence_rank",
        "precedence_gap",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_nonnegative_count,
        )
    for field_name in ("average_confidence_score", "resolution_score"):
        _require_canonical_decimal(
            field_name,
            getattr(row, field_name),
            _normalize_score,
        )
    if row.reason_codes != _normalize_reason_codes(
        "reason_codes",
        row.reason_codes,
        allowed=ROW_REASON_CODES,
        allow_empty=False,
    ):
        raise ValueError("reason_codes must be canonical")
    if row.primary_count > row.reference_count:
        raise ValueError("primary_count must not exceed reference_count")
    if row.family_count > row.primary_count:
        raise ValueError("family_count must not exceed primary_count")
    if row.conflicting_primary_count > row.primary_count:
        raise ValueError("conflicting_primary_count must not exceed primary_count")
    if row.stale_reference_count > row.reference_count:
        raise ValueError("stale_reference_count must not exceed reference_count")
    expected_reasons = _row_reason_codes(
        ladder_step=row.ladder_step,
        stale_count=row.stale_reference_count,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match ladder_step")
    if row.ladder_step == "primary_claim_consensus" and row.status == "block":
        raise ValueError("status must support primary claim consensus")
    if row.ladder_step == "unresolved_primary_conflict" and row.status != "block":
        raise ValueError("status must block unresolved primary conflicts")
    if row.ladder_step == "precedence_ladder_review" and row.status != "watch":
        raise ValueError("status must watch precedence ladder reviews")
    _require_hard_flags("row", row)


def _validate_row_against_config(
    row: ResearchSourcePrimaryClaimConflictResolutionLadderRow,
    config: ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
) -> None:
    if row.primary_count == ZERO_COUNT:
        if any(
            value != ZERO_COUNT
            for value in (
                row.family_count,
                row.conflicting_primary_count,
                row.top_precedence_rank,
                row.runner_up_precedence_rank,
                row.precedence_gap,
            )
        ):
            raise ValueError("primary claim fields must be zero without primary inputs")
        if row.average_confidence_score != ZERO_SCORE:
            raise ValueError("average_confidence_score must be zero without primary inputs")
    else:
        if row.family_count == ZERO_COUNT:
            raise ValueError("family_count must be positive with primary inputs")
        if row.top_precedence_rank == ZERO_COUNT:
            raise ValueError("top_precedence_rank must be positive with primary inputs")

    has_conflict = row.conflicting_primary_count > ZERO_COUNT
    if has_conflict:
        if (
            row.primary_count < _count(2)
            or row.conflicting_primary_count != row.primary_count
            or row.runner_up_precedence_rank == ZERO_COUNT
        ):
            raise ValueError("conflicting_primary_count must describe a primary conflict")
    elif row.runner_up_precedence_rank != ZERO_COUNT:
        raise ValueError("runner_up_precedence_rank requires a primary conflict")
    if row.top_precedence_rank < row.runner_up_precedence_rank:
        raise ValueError("top_precedence_rank must not be below runner_up_precedence_rank")
    if row.precedence_gap != _precedence_gap(
        row.top_precedence_rank,
        row.runner_up_precedence_rank,
    ):
        raise ValueError("precedence_gap must match precedence ranks")

    stale_penalty = config.stale_penalty if row.stale_reference_count > ZERO_COUNT else ZERO_SCORE
    if row.primary_count < config.min_primary_count:
        expected_step = "thin_primary_claim_support"
        expected_score = _resolution_score(
            row.average_confidence_score,
            stale_penalty,
        )
        expected_status = _score_status(
            expected_score,
            config=config,
            force_watch=True,
        )
    elif has_conflict and row.precedence_gap < config.precedence_override_gap:
        expected_step = "unresolved_primary_conflict"
        expected_score = _resolution_score(
            row.average_confidence_score,
            stale_penalty,
            config.unresolved_conflict_penalty,
        )
        expected_status = "block"
    elif has_conflict:
        expected_step = "precedence_ladder_review"
        expected_score = _resolution_score(
            row.average_confidence_score,
            stale_penalty,
        )
        expected_status = "watch"
    else:
        expected_step = "primary_claim_consensus"
        expected_score = _resolution_score(
            row.average_confidence_score,
            stale_penalty,
        )
        expected_status = _score_status(
            expected_score,
            config=config,
            force_watch=False,
        )
        if (
            row.family_count < config.min_independent_family_count
            and expected_status == "pass"
        ):
            expected_status = "watch"
            expected_step = "thin_primary_claim_support"
    if row.ladder_step != expected_step:
        raise ValueError("ladder_step must match primary claim fields")
    if row.resolution_score != expected_score:
        raise ValueError("resolution_score must match row components")
    if row.status != expected_status:
        raise ValueError("status must match resolution_score and ladder_step")
    expected_reasons = _row_reason_codes(
        ladder_step=expected_step,
        stale_count=row.stale_reference_count,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row components")


def _validate_report(
    report: ResearchSourcePrimaryClaimConflictResolutionLadderReport,
) -> None:
    if type(report.generated_at) is not datetime or report.generated_at.tzinfo is not UTC:
        raise ValueError("generated_at must be a canonical UTC datetime")
    _require_public_string("config_version", report.config_version)
    if type(report.config) is not ResearchSourcePrimaryClaimConflictResolutionLadderConfig:
        raise ValueError(
            "config must be a "
            "ResearchSourcePrimaryClaimConflictResolutionLadderConfig",
        )
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    _validate_config(report.config)
    _require_member("status", report.status, STATUSES)
    for field_name in (
        "claim_count",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "conflict_count",
        "stale_count",
    ):
        _require_canonical_decimal(
            field_name,
            getattr(report, field_name),
            _normalize_nonnegative_count,
        )
    _require_canonical_decimal(
        "average_resolution_score",
        report.average_resolution_score,
        _normalize_score,
    )
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a canonical tuple")
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a canonical tuple")
    for row in report.rows:
        if type(row) is not ResearchSourcePrimaryClaimConflictResolutionLadderRow:
            raise ValueError("rows must contain canonical row values")
        _validate_row(row)
        _validate_row_against_config(row, report.config)
    for reason_code_count in report.reason_code_counts:
        if type(reason_code_count) is not ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount:
            raise ValueError("reason_code_counts must contain canonical values")
        _validate_reason_code_count(reason_code_count)
    if report.reason_codes != _normalize_reason_codes(
        "reason_codes",
        report.reason_codes,
        allowed=REPORT_REASON_CODES,
        allow_empty=False,
    ):
        raise ValueError("reason_codes must be canonical")
    if report.claim_count != _count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.input_count != _sum_count_values(
        tuple(row.reference_count for row in report.rows),
    ):
        raise ValueError("input_count must match row reference_count values")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.conflict_count != _count(
        sum(
            1
            for row in report.rows
            if row.conflicting_primary_count > ZERO_COUNT
        ),
    ):
        raise ValueError("conflict_count must match rows")
    if report.stale_count != _count(
        sum(
            1
            for row in report.rows
            if row.stale_reference_count > ZERO_COUNT
        ),
    ):
        raise ValueError("stale_count must match rows")
    if report.average_resolution_score != _average_score(
        tuple(row.resolution_score for row in report.rows),
    ):
        raise ValueError("average_resolution_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.input_count)):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if not report.rows and report.input_count != ZERO_COUNT:
        raise ValueError("input_count must match rows")
    _require_hard_flags("report", report)


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimConflictResolutionLadderRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryClaimConflictResolutionLadderRow:
            raise ValueError(
                "rows must contain "
                "ResearchSourcePrimaryClaimConflictResolutionLadderRow values",
            )
        _validate_row(row)
        if row.claim_digest in seen_digests:
            raise ValueError("duplicate claim_digest values are not allowed")
        seen_digests.add(row.claim_digest)
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount "
                "values",
            )
        _validate_reason_code_count(count)
    if tuple(
        sorted(
            counts,
            key=lambda count: REPORT_REASON_CODES.index(count.reason_code),
        ),
    ) != counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in codes) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _normalize_input_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_public_string(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(codes))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _normalize_nonnegative_seconds("observed_at_age_seconds", seconds)


def _count(value: int | Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_count_values(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_COUNT)
    return _normalize_nonnegative_count("count total", total)


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(quantum)
            if normalized.is_zero():
                return Decimal("0").quantize(quantum)
            return normalized
    except InvalidOperation as error:
        raise ValueError(f"{field_name} must fit the fixed Decimal context") from error


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    normalized = _normalize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _normalize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SCORE or value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    normalized = _normalize_decimal(field_name, value, SCORE_QUANTUM)
    if normalized < ZERO_SCORE or normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_canonical_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> None:
    normalized = normalizer(field_name, value)
    if type(value) is not Decimal or value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{field_name} must be a canonical Decimal")


def _clamped_score(value: Decimal) -> Decimal:
    return _normalize_score("score", max(ZERO_SCORE, min(ONE_SCORE, value)))


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_digest_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_digest_string(field_name, value.removeprefix("sha256:"))


def _require_digest_string(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _digest_reference(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _report_digest(
    report: ResearchSourcePrimaryClaimConflictResolutionLadderReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    return _payload_digest(payload_without_digest)


def _payload_digest(payload_without_digest: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest_string("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    if digest != _payload_digest(payload_without_digest):
        raise ValueError("derived_validation_digest must match report contents")


def _validate_public_payload(
    payload: dict[str, Any],
) -> ResearchSourcePrimaryClaimConflictResolutionLadderReport:
    _require_payload_keys(
        "payload",
        payload,
        ResearchSourcePrimaryClaimConflictResolutionLadderReport,
    )
    config_payload = _payload_object(payload, "config")
    _require_payload_keys(
        "config payload",
        config_payload,
        ResearchSourcePrimaryClaimConflictResolutionLadderConfig,
    )
    config = ResearchSourcePrimaryClaimConflictResolutionLadderConfig(
        config_version=_payload_string(config_payload, "config_version"),
        stale_after_seconds=_payload_decimal(config_payload, "stale_after_seconds"),
        min_primary_count=_payload_decimal(config_payload, "min_primary_count"),
        min_independent_family_count=_payload_decimal(
            config_payload,
            "min_independent_family_count",
        ),
        precedence_override_gap=_payload_decimal(
            config_payload,
            "precedence_override_gap",
        ),
        min_pass_resolution_score=_payload_decimal(
            config_payload,
            "min_pass_resolution_score",
        ),
        min_watch_resolution_score=_payload_decimal(
            config_payload,
            "min_watch_resolution_score",
        ),
        stale_penalty=_payload_decimal(config_payload, "stale_penalty"),
        unresolved_conflict_penalty=_payload_decimal(
            config_payload,
            "unresolved_conflict_penalty",
        ),
        paper_only=_payload_bool(config_payload, "paper_only"),
        report_only=_payload_bool(config_payload, "report_only"),
        readonly=_payload_bool(config_payload, "readonly"),
    )
    rows_payload = _payload_array(payload, "rows")
    rows = tuple(_row_from_payload(value) for value in rows_payload)
    reason_code_counts_payload = _payload_array(payload, "reason_code_counts")
    reason_code_counts = tuple(
        _reason_code_count_from_payload(value)
        for value in reason_code_counts_payload
    )
    report = ResearchSourcePrimaryClaimConflictResolutionLadderReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        config=config,
        status=_payload_string(payload, "status"),
        claim_count=_payload_decimal(payload, "claim_count"),
        input_count=_payload_decimal(payload, "input_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        conflict_count=_payload_decimal(payload, "conflict_count"),
        stale_count=_payload_decimal(payload, "stale_count"),
        average_resolution_score=_payload_decimal(
            payload,
            "average_resolution_score",
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_payload_string_tuple(payload, "reason_codes"),
        derived_validation_digest=_payload_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )
    canonical_payload = _json_ready(report)
    if payload != canonical_payload:
        raise ValueError("payload must use canonical JSON values")
    return report


def _row_from_payload(
    value: object,
) -> ResearchSourcePrimaryClaimConflictResolutionLadderRow:
    if type(value) is not dict:
        raise ValueError("payload rows must be JSON objects")
    _require_payload_keys(
        "row payload",
        value,
        ResearchSourcePrimaryClaimConflictResolutionLadderRow,
    )
    return ResearchSourcePrimaryClaimConflictResolutionLadderRow(
        claim_digest=_payload_string(value, "claim_digest"),
        status=_payload_string(value, "status"),
        ladder_step=_payload_string(value, "ladder_step"),
        reference_count=_payload_decimal(value, "reference_count"),
        primary_count=_payload_decimal(value, "primary_count"),
        family_count=_payload_decimal(value, "family_count"),
        conflicting_primary_count=_payload_decimal(
            value,
            "conflicting_primary_count",
        ),
        stale_reference_count=_payload_decimal(value, "stale_reference_count"),
        top_precedence_rank=_payload_decimal(value, "top_precedence_rank"),
        runner_up_precedence_rank=_payload_decimal(value, "runner_up_precedence_rank"),
        precedence_gap=_payload_decimal(value, "precedence_gap"),
        average_confidence_score=_payload_decimal(
            value,
            "average_confidence_score",
        ),
        resolution_score=_payload_decimal(value, "resolution_score"),
        reason_codes=_payload_string_tuple(value, "reason_codes"),
        paper_only=_payload_bool(value, "paper_only"),
        report_only=_payload_bool(value, "report_only"),
        readonly=_payload_bool(value, "readonly"),
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys(
        "reason_code_count payload",
        value,
        ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount,
    )
    return ResearchSourcePrimaryClaimConflictResolutionLadderReasonCodeCount(
        reason_code=_payload_string(value, "reason_code"),
        count=_payload_decimal(value, "count"),
        paper_only=_payload_bool(value, "paper_only"),
        report_only=_payload_bool(value, "report_only"),
        readonly=_payload_bool(value, "readonly"),
    )


def _require_payload_keys(context: str, value: dict[str, Any], cls: type[Any]) -> None:
    expected = tuple(field.name for field in fields(cls))
    if tuple(value) != expected:
        raise ValueError(f"{context} keys must match the canonical schema and order")


def _payload_object(value: dict[str, Any], field_name: str) -> dict[str, Any]:
    item = value[field_name]
    if type(item) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return item


def _payload_array(value: dict[str, Any], field_name: str) -> list[Any]:
    item = value[field_name]
    if type(item) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return item


def _payload_string(value: dict[str, Any], field_name: str) -> str:
    item = value[field_name]
    if type(item) is not str:
        raise ValueError(f"{field_name} must be a JSON string")
    return item


def _payload_bool(value: dict[str, Any], field_name: str) -> bool:
    item = value[field_name]
    if type(item) is not bool:
        raise ValueError(f"{field_name} must be a JSON bool")
    return item


def _payload_decimal(value: dict[str, Any], field_name: str) -> Decimal:
    text = _payload_string(value, field_name)
    try:
        return Decimal(text)
    except Exception as error:
        raise ValueError(f"{field_name} must be a Decimal string") from error


def _payload_datetime(value: dict[str, Any], field_name: str) -> datetime:
    text = _payload_string(value, field_name)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from error
    return _as_utc(field_name, parsed)


def _payload_string_tuple(value: dict[str, Any], field_name: str) -> tuple[str, ...]:
    items = _payload_array(value, field_name)
    for item in items:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain JSON strings")
    return tuple(items)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _thaw_json_object(value: object) -> dict[str, Any]:
    thawed = _thaw_json_value(value)
    if type(thawed) is not dict:
        raise ValueError("report payload must be a JSON object")
    return thawed


def _thaw_json_value(value: object) -> Any:
    if type(value) in (dict, FrozenJsonObject):
        return {
            _thaw_json_key(key): _thaw_json_value(item)
            for key, item in value.items()
        }
    if type(value) is list or type(value) is FrozenJsonArray:
        return [_thaw_json_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("payload must use exact JSON scalar and container types")


def _thaw_json_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    return value


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if isinstance(value, Decimal):
        return
    if isinstance(value, datetime):
        return
    if type(value) is str:
        lowered = value.lower()
        if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"{context} contains unsafe public value")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_name = field.name.lower()
            if any(term in field_name for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"{context} contains unsafe public field")
            _reject_unsafe_public_payload(context, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"{context} contains unsafe public key")
            _reject_unsafe_public_payload(context, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) in (int, float):
        raise ValueError(f"{context} contains non-Decimal numeric value")
