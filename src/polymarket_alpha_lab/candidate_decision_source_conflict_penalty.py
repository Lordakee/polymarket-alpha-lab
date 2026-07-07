"""Pure Phase 1 candidate source-conflict penalty scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION = (
    "candidate-decision-source-conflict-penalty-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PENALTY_BANDS = frozenset(("pass", "watch", "block"))
PUBLIC_REF_RE = re.compile(r"^redacted_[A-Za-z0-9_.-]{1,119}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionSourceConflictPenaltyAggregate",
        "CandidateDecisionSourceConflictPenaltyConfig",
        "CandidateDecisionSourceConflictPenaltyReport",
        "CandidateDecisionSourceConflictPenaltyRow",
    ),
)
_PUBLIC_DATACLASS_REGISTRY: set[str] = set()
ROW_REASON_CODE_SEQUENCE = (
    "no_contradictory_source_stances",
    "contradictory_source_stance_watch",
    "contradictory_source_stance_block",
    "independent_source_conflict_watch",
    "independent_source_conflict_block",
    "authority_conflict_watch",
    "authority_conflict_block",
    "fresh_conflict_watch",
    "fresh_conflict_block",
    "conflict_severity_watch",
    "conflict_severity_block",
    "source_conflict_penalty_watch_score",
    "source_conflict_penalty_block_score",
    "source_conflict_penalty_pass",
)
REPORT_REASON_CODE_SEQUENCE = (
    "source_conflict_penalty_report_pass",
    "source_conflict_penalty_report_watch",
    "source_conflict_penalty_report_block",
    "source_conflict_penalty_report_empty",
    *ROW_REASON_CODE_SEQUENCE,
)
BLOCK_REASON_CODES = frozenset(
    (
        "contradictory_source_stance_block",
        "independent_source_conflict_block",
        "authority_conflict_block",
        "fresh_conflict_block",
        "conflict_severity_block",
        "source_conflict_penalty_block_score",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "contradictory_source_stance_watch",
        "independent_source_conflict_watch",
        "authority_conflict_watch",
        "fresh_conflict_watch",
        "conflict_severity_watch",
        "source_conflict_penalty_watch_score",
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "raw_text",
        "dsn",
        "table",
        "wallet",
        "auth_token",
        "order",
        "trade",
        "private_key",
        "token",
        "position",
        "sizing",
        "recommendation",
        "account",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "http",
        "www.",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "raw_text",
        "dsn",
        "table_name",
        "wallet",
        "auth_token",
        "order",
        "trade",
        "private_key",
        "token",
        "position_size",
        "buy",
        "sell",
        "recommendation",
        "account",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("subclassing is not allowed")
        if cls.__name__ in _PUBLIC_DATACLASS_REGISTRY and cls.__name__ in globals():
            raise TypeError("public dataclass name is already bound")
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")
        if cls.__name__ in _PUBLIC_DATACLASS_REGISTRY:
            raise TypeError("public dataclass is already registered")
        _PUBLIC_DATACLASS_REGISTRY.add(cls.__name__)


@dataclass(frozen=True)
class CandidateDecisionSourceConflictPenaltyConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION
    pass_penalty_threshold: Decimal = Decimal("0.250000")
    watch_penalty_threshold: Decimal = Decimal("0.600000")
    max_pass_contradictory_stance_ratio: Decimal = Decimal("0.250000")
    max_watch_contradictory_stance_ratio: Decimal = Decimal("0.500000")
    max_pass_independence_conflict_score: Decimal = Decimal("0.500000")
    max_watch_independence_conflict_score: Decimal = Decimal("0.800000")
    max_pass_authority_conflict_score: Decimal = Decimal("0.500000")
    max_watch_authority_conflict_score: Decimal = Decimal("0.800000")
    max_pass_freshness_conflict_score: Decimal = Decimal("0.500000")
    max_watch_freshness_conflict_score: Decimal = Decimal("0.800000")
    max_pass_conflict_severity_score: Decimal = Decimal("0.300000")
    max_watch_conflict_severity_score: Decimal = Decimal("0.700000")
    contradictory_stance_ratio_weight: Decimal = Decimal("0.300000")
    source_independence_weight: Decimal = Decimal("0.200000")
    authority_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    conflict_severity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionSourceConflictPenaltyConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "pass_penalty_threshold",
            "watch_penalty_threshold",
            "max_pass_contradictory_stance_ratio",
            "max_watch_contradictory_stance_ratio",
            "max_pass_independence_conflict_score",
            "max_watch_independence_conflict_score",
            "max_pass_authority_conflict_score",
            "max_watch_authority_conflict_score",
            "max_pass_freshness_conflict_score",
            "max_watch_freshness_conflict_score",
            "max_pass_conflict_severity_score",
            "max_watch_conflict_severity_score",
            "contradictory_stance_ratio_weight",
            "source_independence_weight",
            "authority_weight",
            "freshness_weight",
            "conflict_severity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CandidateDecisionSourceConflictPenaltyAggregate(_FinalPublicDataclass):
    redacted_candidate_key: str
    observed_at: datetime
    supporting_stance_count: Decimal
    contradictory_stance_count: Decimal
    neutral_stance_count: Decimal
    source_independence_score: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    conflict_severity_score: Decimal
    aggregate_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("aggregate", self, CandidateDecisionSourceConflictPenaltyAggregate)
        object.__setattr__(
            self,
            "redacted_candidate_key",
            _require_redacted_key("redacted_candidate_key", self.redacted_candidate_key),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "supporting_stance_count",
            "contradictory_stance_count",
            "neutral_stance_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_independence_score",
            "authority_score",
            "freshness_score",
            "conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_version",
            _require_public_identifier("aggregate_version", self.aggregate_version),
        )
        if _total_stance_count(self) == ZERO:
            raise ValueError("total stance count must be positive")
        _require_phase_flags("aggregate", self)
        _reject_unsafe_public_payload("aggregate", self)


@dataclass(frozen=True)
class CandidateDecisionSourceConflictPenaltyRow(_FinalPublicDataclass):
    rank: Decimal
    redacted_candidate_key: str
    supporting_stance_count: Decimal
    contradictory_stance_count: Decimal
    neutral_stance_count: Decimal
    total_stance_count: Decimal
    contradictory_stance_ratio: Decimal
    source_independence_score: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    conflict_severity_score: Decimal
    conflict_penalty_score: Decimal
    penalty_band: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, CandidateDecisionSourceConflictPenaltyRow)
        object.__setattr__(self, "rank", _require_count_decimal("rank", self.rank))
        if self.rank <= ZERO:
            raise ValueError("rank must be positive")
        object.__setattr__(
            self,
            "redacted_candidate_key",
            _require_redacted_key("redacted_candidate_key", self.redacted_candidate_key),
        )
        for field_name in (
            "supporting_stance_count",
            "contradictory_stance_count",
            "neutral_stance_count",
            "total_stance_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradictory_stance_ratio",
            "source_independence_score",
            "authority_score",
            "freshness_score",
            "conflict_severity_score",
            "conflict_penalty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "penalty_band",
            _require_penalty_band("penalty_band", self.penalty_band),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _require_phase_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match row payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_row(self)


@dataclass(frozen=True)
class CandidateDecisionSourceConflictPenaltyReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    penalty_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_conflict_penalty_score: Decimal
    max_conflict_penalty_score: Decimal
    max_contradictory_stance_ratio: Decimal
    max_conflict_severity_score: Decimal
    rows: tuple[CandidateDecisionSourceConflictPenaltyRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionSourceConflictPenaltyReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "penalty_status",
            _require_penalty_band("penalty_status", self.penalty_status),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_conflict_penalty_score",
            "max_conflict_penalty_score",
            "max_contradictory_stance_ratio",
            "max_conflict_severity_score",
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_phase_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "candidate decision source conflict penalty payload",
            payload,
            allow_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_candidate_decision_source_conflict_penalty(
    aggregates: Sequence[CandidateDecisionSourceConflictPenaltyAggregate],
    *,
    generated_at: datetime,
    config: CandidateDecisionSourceConflictPenaltyConfig | None = None,
) -> CandidateDecisionSourceConflictPenaltyReport:
    """Build a local paper-only source-conflict penalty report."""

    if config is None:
        config = CandidateDecisionSourceConflictPenaltyConfig()
    if type(config) is not CandidateDecisionSourceConflictPenaltyConfig:
        raise ValueError("config must be a CandidateDecisionSourceConflictPenaltyConfig")
    _require_phase_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_aggregates = _normalize_aggregates(aggregates)
    for item in normalized_aggregates:
        if item.observed_at > generated_at:
            raise ValueError("aggregate observed_at must not be after generated_at")
    rows_without_rank = tuple(_row_from_aggregate(item, config) for item in normalized_aggregates)
    rows = _rank_rows(rows_without_rank)
    report = CandidateDecisionSourceConflictPenaltyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        penalty_status=_report_status(rows),
        candidate_count=_count(len(rows)),
        pass_count=_count(_band_count(rows, "pass")),
        watch_count=_count(_band_count(rows, "watch")),
        block_count=_count(_band_count(rows, "block")),
        average_conflict_penalty_score=_average(
            tuple(row.conflict_penalty_score for row in rows),
        ),
        max_conflict_penalty_score=max(
            (row.conflict_penalty_score for row in rows),
            default=ZERO,
        ),
        max_contradictory_stance_ratio=max(
            (row.contradictory_stance_ratio for row in rows),
            default=ZERO,
        ),
        max_conflict_severity_score=max(
            (row.conflict_severity_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )
    return report


def candidate_decision_source_conflict_penalty_payload(
    report: CandidateDecisionSourceConflictPenaltyReport,
) -> dict[str, object]:
    if type(report) is not CandidateDecisionSourceConflictPenaltyReport:
        raise ValueError("report must be a CandidateDecisionSourceConflictPenaltyReport")
    _require_phase_flags("report", report)
    return report.payload


def _row_from_aggregate(
    aggregate: CandidateDecisionSourceConflictPenaltyAggregate,
    config: CandidateDecisionSourceConflictPenaltyConfig,
) -> CandidateDecisionSourceConflictPenaltyRow:
    total_count = _total_stance_count(aggregate)
    contradictory_ratio = _safe_ratio(aggregate.contradictory_stance_count, total_count)
    penalty_score = _penalty_score(aggregate, contradictory_ratio, config)
    reason_codes = _row_reason_codes(aggregate, contradictory_ratio, penalty_score, config)
    return CandidateDecisionSourceConflictPenaltyRow(
        rank=ONE,
        redacted_candidate_key=aggregate.redacted_candidate_key,
        supporting_stance_count=aggregate.supporting_stance_count,
        contradictory_stance_count=aggregate.contradictory_stance_count,
        neutral_stance_count=aggregate.neutral_stance_count,
        total_stance_count=total_count,
        contradictory_stance_ratio=contradictory_ratio,
        source_independence_score=aggregate.source_independence_score,
        authority_score=aggregate.authority_score,
        freshness_score=aggregate.freshness_score,
        conflict_severity_score=aggregate.conflict_severity_score,
        conflict_penalty_score=penalty_score,
        penalty_band=_penalty_band(reason_codes),
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[CandidateDecisionSourceConflictPenaltyRow, ...],
) -> tuple[CandidateDecisionSourceConflictPenaltyRow, ...]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.conflict_penalty_score,
            row.redacted_candidate_key,
        ),
    )
    return tuple(
        CandidateDecisionSourceConflictPenaltyRow(
            rank=_count(index + 1),
            redacted_candidate_key=row.redacted_candidate_key,
            supporting_stance_count=row.supporting_stance_count,
            contradictory_stance_count=row.contradictory_stance_count,
            neutral_stance_count=row.neutral_stance_count,
            total_stance_count=row.total_stance_count,
            contradictory_stance_ratio=row.contradictory_stance_ratio,
            source_independence_score=row.source_independence_score,
            authority_score=row.authority_score,
            freshness_score=row.freshness_score,
            conflict_severity_score=row.conflict_severity_score,
            conflict_penalty_score=row.conflict_penalty_score,
            penalty_band=row.penalty_band,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows)
    )


def _penalty_score(
    aggregate: CandidateDecisionSourceConflictPenaltyAggregate,
    contradictory_ratio: Decimal,
    config: CandidateDecisionSourceConflictPenaltyConfig,
) -> Decimal:
    if aggregate.contradictory_stance_count == ZERO:
        return ZERO
    return _clamp_ratio(
        contradictory_ratio * config.contradictory_stance_ratio_weight
        + aggregate.source_independence_score * config.source_independence_weight
        + aggregate.authority_score * config.authority_weight
        + aggregate.freshness_score * config.freshness_weight
        + aggregate.conflict_severity_score * config.conflict_severity_weight,
    )


def _row_reason_codes(
    aggregate: CandidateDecisionSourceConflictPenaltyAggregate,
    contradictory_ratio: Decimal,
    penalty_score: Decimal,
    config: CandidateDecisionSourceConflictPenaltyConfig,
) -> tuple[str, ...]:
    if aggregate.contradictory_stance_count == ZERO:
        return ("no_contradictory_source_stances", "source_conflict_penalty_pass")

    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        contradictory_ratio,
        config.max_pass_contradictory_stance_ratio,
        config.max_watch_contradictory_stance_ratio,
        "contradictory_source_stance_watch",
        "contradictory_source_stance_block",
    )
    _append_threshold_reason(
        reason_codes,
        aggregate.source_independence_score,
        config.max_pass_independence_conflict_score,
        config.max_watch_independence_conflict_score,
        "independent_source_conflict_watch",
        "independent_source_conflict_block",
    )
    _append_threshold_reason(
        reason_codes,
        aggregate.authority_score,
        config.max_pass_authority_conflict_score,
        config.max_watch_authority_conflict_score,
        "authority_conflict_watch",
        "authority_conflict_block",
    )
    _append_threshold_reason(
        reason_codes,
        aggregate.freshness_score,
        config.max_pass_freshness_conflict_score,
        config.max_watch_freshness_conflict_score,
        "fresh_conflict_watch",
        "fresh_conflict_block",
    )
    _append_threshold_reason(
        reason_codes,
        aggregate.conflict_severity_score,
        config.max_pass_conflict_severity_score,
        config.max_watch_conflict_severity_score,
        "conflict_severity_watch",
        "conflict_severity_block",
    )
    if penalty_score > config.watch_penalty_threshold:
        reason_codes.append("source_conflict_penalty_block_score")
    elif penalty_score > config.pass_penalty_threshold:
        reason_codes.append("source_conflict_penalty_watch_score")
    if not reason_codes:
        reason_codes.append("source_conflict_penalty_pass")
    return _normalize_reason_codes(tuple(reason_codes), ROW_REASON_CODE_SEQUENCE)


def _append_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > pass_threshold:
        reason_codes.append(watch_reason)


def _penalty_band(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[CandidateDecisionSourceConflictPenaltyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.penalty_band == "block" for row in rows):
        return "block"
    if any(row.penalty_band == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionSourceConflictPenaltyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_conflict_penalty_report_empty",)
    reason_codes: list[str] = [f"source_conflict_penalty_report_{_report_status(rows)}"]
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), REPORT_REASON_CODE_SEQUENCE)


def _band_count(
    rows: tuple[CandidateDecisionSourceConflictPenaltyRow, ...],
    penalty_band: str,
) -> int:
    return sum(1 for row in rows if row.penalty_band == penalty_band)


def _validate_config(config: CandidateDecisionSourceConflictPenaltyConfig) -> None:
    for pass_field, watch_field in (
        ("pass_penalty_threshold", "watch_penalty_threshold"),
        (
            "max_pass_contradictory_stance_ratio",
            "max_watch_contradictory_stance_ratio",
        ),
        (
            "max_pass_independence_conflict_score",
            "max_watch_independence_conflict_score",
        ),
        ("max_pass_authority_conflict_score", "max_watch_authority_conflict_score"),
        ("max_pass_freshness_conflict_score", "max_watch_freshness_conflict_score"),
        ("max_pass_conflict_severity_score", "max_watch_conflict_severity_score"),
    ):
        if getattr(config, pass_field) > getattr(config, watch_field):
            raise ValueError(f"{pass_field} must not exceed {watch_field}")
    total_weight = _quantize(
        config.contradictory_stance_ratio_weight
        + config.source_independence_weight
        + config.authority_weight
        + config.freshness_weight
        + config.conflict_severity_weight,
    )
    if total_weight != ONE:
        raise ValueError("penalty weights must sum to 1.000000")


def _validate_row(row: CandidateDecisionSourceConflictPenaltyRow) -> None:
    expected_total = _quantize(
        row.supporting_stance_count
        + row.contradictory_stance_count
        + row.neutral_stance_count,
    )
    if row.total_stance_count != expected_total:
        raise ValueError("total_stance_count must match stance counts")
    if row.total_stance_count <= ZERO:
        raise ValueError("total_stance_count must be positive")
    expected_ratio = _safe_ratio(row.contradictory_stance_count, row.total_stance_count)
    if row.contradictory_stance_ratio != expected_ratio:
        raise ValueError("contradictory_stance_ratio must match stance counts")
    if row.penalty_band != _penalty_band(row.reason_codes):
        raise ValueError("penalty_band must match reason_codes")
    if row.penalty_band == "pass" and "source_conflict_penalty_pass" not in row.reason_codes:
        raise ValueError("pass rows must include source_conflict_penalty_pass")


def _validate_report(report: CandidateDecisionSourceConflictPenaltyReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(_band_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_band_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_band_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_conflict_penalty_score != _average(
        tuple(row.conflict_penalty_score for row in report.rows),
    ):
        raise ValueError("average_conflict_penalty_score must match rows")
    expected_max_penalty = max(
        (row.conflict_penalty_score for row in report.rows),
        default=ZERO,
    )
    if report.max_conflict_penalty_score != expected_max_penalty:
        raise ValueError("max_conflict_penalty_score must match rows")
    expected_max_ratio = max(
        (row.contradictory_stance_ratio for row in report.rows),
        default=ZERO,
    )
    if report.max_contradictory_stance_ratio != expected_max_ratio:
        raise ValueError("max_contradictory_stance_ratio must match rows")
    expected_max_severity = max(
        (row.conflict_severity_score for row in report.rows),
        default=ZERO,
    )
    if report.max_conflict_severity_score != expected_max_severity:
        raise ValueError("max_conflict_severity_score must match rows")
    if report.penalty_status != _report_status(report.rows):
        raise ValueError("penalty_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(index + 1) for index in range(len(report.rows)))
    if tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must use contiguous rank values")


def _normalize_aggregates(
    aggregates: Sequence[CandidateDecisionSourceConflictPenaltyAggregate],
) -> tuple[CandidateDecisionSourceConflictPenaltyAggregate, ...]:
    if isinstance(aggregates, (str, bytes)) or not isinstance(aggregates, Sequence):
        raise ValueError("aggregates must be a sequence")
    normalized: list[CandidateDecisionSourceConflictPenaltyAggregate] = []
    seen_keys: set[str] = set()
    for aggregate in aggregates:
        if type(aggregate) is not CandidateDecisionSourceConflictPenaltyAggregate:
            raise ValueError(
                "aggregates must contain CandidateDecisionSourceConflictPenaltyAggregate",
            )
        if aggregate.redacted_candidate_key in seen_keys:
            raise ValueError("redacted_candidate_key values must be unique")
        seen_keys.add(aggregate.redacted_candidate_key)
        normalized.append(aggregate)
    return tuple(
        sorted(
            normalized,
            key=lambda aggregate: (aggregate.observed_at, aggregate.redacted_candidate_key),
        ),
    )


def _normalize_rows(
    rows: Sequence[CandidateDecisionSourceConflictPenaltyRow],
) -> tuple[CandidateDecisionSourceConflictPenaltyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[CandidateDecisionSourceConflictPenaltyRow] = []
    for row in rows:
        if type(row) is not CandidateDecisionSourceConflictPenaltyRow:
            raise ValueError("rows must contain CandidateDecisionSourceConflictPenaltyRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.rank))


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_redacted_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("redacted_"):
        raise ValueError(f"{field_name} must be redacted")
    if not PUBLIC_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public redacted key")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty public identifier")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    whole_value = decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if decimal_value != whole_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _require_required_precision(field_name, decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _require_required_precision(field_name, decimal_value)


def _require_penalty_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PENALTY_BANDS:
        raise ValueError(f"{field_name} must be a supported penalty band")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    reason_code_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in reason_code_sequence:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in reason_code_sequence if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _total_stance_count(aggregate: CandidateDecisionSourceConflictPenaltyAggregate) -> Decimal:
    return _quantize(
        aggregate.supporting_stance_count
        + aggregate.contradictory_stance_count
        + aggregate.neutral_stance_count,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _row_digest(row: CandidateDecisionSourceConflictPenaltyRow) -> str:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return _digest_values(values)


def _report_digest(report: CandidateDecisionSourceConflictPenaltyReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _digest_values(values)


def _digest_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_containers=allow_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_containers=allow_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    normalized = _normalize_unsafe_scan_text(key)
    if any(
        _unsafe_fragment_present(fragment, key, normalized)
        for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS
    ):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    normalized = _normalize_unsafe_scan_text(value)
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(
        _unsafe_fragment_present(fragment, value, normalized)
        for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS
    ):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_required_precision(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return normalized


def _unsafe_fragment_present(fragment: str, value: str, normalized: str) -> bool:
    fragment_normalized = _normalize_unsafe_scan_text(fragment)
    compact_value = re.sub(r"[^a-z0-9]+", "", value.lower())
    compact_fragment = re.sub(r"[^a-z0-9]+", "", fragment.lower())
    return (
        fragment in value.lower()
        or fragment_normalized in normalized
        or compact_fragment in compact_value
    )


def _normalize_unsafe_scan_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _split_camel_case(value).lower()).strip("_")


def _split_camel_case(value: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION",
    "CandidateDecisionSourceConflictPenaltyAggregate",
    "CandidateDecisionSourceConflictPenaltyConfig",
    "CandidateDecisionSourceConflictPenaltyReport",
    "CandidateDecisionSourceConflictPenaltyRow",
    "build_candidate_decision_source_conflict_penalty",
    "candidate_decision_source_conflict_penalty_payload",
)
