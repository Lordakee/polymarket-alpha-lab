"""Pure report-only source authority consensus quorum scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_REPORT_CONFIG_VERSION = (
    "research-source-authority-consensus-quorum-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_consensus_quorum_empty"
CLEAR_REASON = "research_source_authority_consensus_quorum_clear"
WEAK_TIER_MIX_WATCH_REASON = (
    "research_source_authority_consensus_quorum_weak_tier_mix_watch"
)
WEAK_TIER_MIX_BLOCK_REASON = (
    "research_source_authority_consensus_quorum_weak_tier_mix_block"
)
STALE_SOURCES_WATCH_REASON = (
    "research_source_authority_consensus_quorum_stale_sources_watch"
)
STALE_SOURCES_BLOCK_REASON = (
    "research_source_authority_consensus_quorum_stale_sources_block"
)
LOW_INDEPENDENCE_WATCH_REASON = (
    "research_source_authority_consensus_quorum_low_independence_watch"
)
LOW_INDEPENDENCE_BLOCK_REASON = (
    "research_source_authority_consensus_quorum_low_independence_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "research_source_authority_consensus_quorum_contradiction_pressure_watch"
)
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "research_source_authority_consensus_quorum_contradiction_pressure_block"
)
COVERAGE_GAP_WATCH_REASON = (
    "research_source_authority_consensus_quorum_coverage_gap_watch"
)
COVERAGE_GAP_BLOCK_REASON = (
    "research_source_authority_consensus_quorum_coverage_gap_block"
)
LOW_SCORE_WATCH_REASON = "research_source_authority_consensus_quorum_low_score_watch"
LOW_SCORE_BLOCK_REASON = "research_source_authority_consensus_quorum_low_score_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    WEAK_TIER_MIX_BLOCK_REASON,
    STALE_SOURCES_BLOCK_REASON,
    LOW_INDEPENDENCE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    COVERAGE_GAP_BLOCK_REASON,
    LOW_SCORE_BLOCK_REASON,
    WEAK_TIER_MIX_WATCH_REASON,
    STALE_SOURCES_WATCH_REASON,
    LOW_INDEPENDENCE_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    COVERAGE_GAP_WATCH_REASON,
    LOW_SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SHA256_HEX_LENGTH = 64

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "recommendation",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "jdbc:",
    "candidate-",
    "candidate_",
    "raw_candidate",
    "candidate_id",
    "market-",
    "market_",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "api_key",
    "private_key",
    "bearer ",
    "_table",
    "table_",
    ".table",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityConsensusQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_REPORT_CONFIG_VERSION
    )
    min_primary_source_count: Decimal = Decimal("1.000000")
    min_total_source_count: Decimal = Decimal("3.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    coverage_gap_watch_score: Decimal = Decimal("0.250000")
    coverage_gap_block_score: Decimal = Decimal("0.500000")
    pass_consensus_score: Decimal = Decimal("0.750000")
    watch_consensus_score: Decimal = Decimal("0.450000")
    tier_mix_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.250000")
    contradiction_weight: Decimal = Decimal("0.150000")
    coverage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityConsensusQuorumConfig:
            raise TypeError(
                "ResearchSourceAuthorityConsensusQuorumConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityConsensusQuorumConfig:
            raise ValueError(
                "config must be exactly ResearchSourceAuthorityConsensusQuorumConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_primary_source_count",
            "min_total_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("freshness_watch_age_seconds", "freshness_block_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "coverage_gap_watch_score",
            "coverage_gap_block_score",
            "pass_consensus_score",
            "watch_consensus_score",
            "tier_mix_weight",
            "freshness_weight",
            "independence_weight",
            "contradiction_weight",
            "coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityConsensusQuorumInput:
    quorum_bucket: str
    primary_source_count: Decimal
    secondary_source_count: Decimal
    independent_source_count: Decimal
    max_source_age_seconds: Decimal
    contradiction_pressure_score: Decimal
    coverage_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityConsensusQuorumInput:
            raise TypeError(
                "ResearchSourceAuthorityConsensusQuorumInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityConsensusQuorumInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityConsensusQuorumInput",
            )
        object.__setattr__(
            self,
            "quorum_bucket",
            _require_public_bucket("quorum_bucket", self.quorum_bucket),
        )
        for field_name in (
            "primary_source_count",
            "secondary_source_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in ("contradiction_pressure_score", "coverage_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityConsensusQuorumRow:
    quorum_bucket: str
    primary_source_count: Decimal
    secondary_source_count: Decimal
    total_source_count: Decimal
    independent_source_count: Decimal
    max_source_age_seconds: Decimal
    contradiction_pressure_score: Decimal
    coverage_gap_score: Decimal
    source_tier_mix_score: Decimal
    freshness_score: Decimal
    independence_score: Decimal
    contradiction_support_score: Decimal
    coverage_score: Decimal
    consensus_score: Decimal
    quorum_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityConsensusQuorumRow:
            raise TypeError(
                "ResearchSourceAuthorityConsensusQuorumRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityConsensusQuorumRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityConsensusQuorumRow")
        object.__setattr__(
            self,
            "quorum_bucket",
            _require_public_bucket("quorum_bucket", self.quorum_bucket),
        )
        for field_name in (
            "primary_source_count",
            "secondary_source_count",
            "total_source_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "contradiction_pressure_score",
            "coverage_gap_score",
            "source_tier_mix_score",
            "freshness_score",
            "independence_score",
            "contradiction_support_score",
            "coverage_score",
            "consensus_score",
            "quorum_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityConsensusQuorumReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityConsensusQuorumReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthorityConsensusQuorumReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityConsensusQuorumReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceAuthorityConsensusQuorumReasonCodeCount",
            )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityConsensusQuorumReport:
    generated_at: datetime
    config_version: str
    quorum_item_count: Decimal
    pass_quorum_item_count: Decimal
    watch_quorum_item_count: Decimal
    block_quorum_item_count: Decimal
    weak_source_tier_mix_count: Decimal
    stale_source_count: Decimal
    thin_independence_count: Decimal
    contradiction_pressure_count: Decimal
    coverage_gap_count: Decimal
    lowest_consensus_score: Decimal
    highest_quorum_risk_score: Decimal
    oldest_source_age_seconds: Decimal
    highest_contradiction_pressure_score: Decimal
    highest_coverage_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityConsensusQuorumReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityConsensusQuorumReport:
            raise TypeError(
                "ResearchSourceAuthorityConsensusQuorumReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityConsensusQuorumReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityConsensusQuorumReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "quorum_item_count",
            "pass_quorum_item_count",
            "watch_quorum_item_count",
            "block_quorum_item_count",
            "weak_source_tier_mix_count",
            "stale_source_count",
            "thin_independence_count",
            "contradiction_pressure_count",
            "coverage_gap_count",
            "oldest_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_consensus_score",
            "highest_quorum_risk_score",
            "highest_contradiction_pressure_score",
            "highest_coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)


def build_research_source_authority_consensus_quorum_report(
    inputs: list[ResearchSourceAuthorityConsensusQuorumInput]
    | tuple[ResearchSourceAuthorityConsensusQuorumInput, ...],
    *,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityConsensusQuorumReport:
    if type(config) is not ResearchSourceAuthorityConsensusQuorumConfig:
        raise ValueError("config must be a ResearchSourceAuthorityConsensusQuorumConfig")
    _require_hard_flags("config", config)
    rows = _quorum_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityConsensusQuorumReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        quorum_item_count=_count(len(rows)),
        pass_quorum_item_count=_status_count(rows, "pass"),
        watch_quorum_item_count=_status_count(rows, "watch"),
        block_quorum_item_count=_status_count(rows, "block"),
        weak_source_tier_mix_count=_reason_count(
            rows,
            (WEAK_TIER_MIX_WATCH_REASON, WEAK_TIER_MIX_BLOCK_REASON),
        ),
        stale_source_count=_reason_count(
            rows,
            (STALE_SOURCES_WATCH_REASON, STALE_SOURCES_BLOCK_REASON),
        ),
        thin_independence_count=_reason_count(
            rows,
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        coverage_gap_count=_reason_count(
            rows,
            (COVERAGE_GAP_WATCH_REASON, COVERAGE_GAP_BLOCK_REASON),
        ),
        lowest_consensus_score=min(
            (row.consensus_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_quorum_risk_score=max(
            (row.quorum_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_source_age_seconds=max(
            (row.max_source_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_coverage_gap_score=max(
            (row.coverage_gap_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_authority_consensus_quorum_report_payload(
    report: ResearchSourceAuthorityConsensusQuorumReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityConsensusQuorumReport:
        raise ValueError("report must be a ResearchSourceAuthorityConsensusQuorumReport")
    validate_research_source_authority_consensus_quorum_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _require_public_payload_hard_flags(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_consensus_quorum_report_digest(
    report: ResearchSourceAuthorityConsensusQuorumReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityConsensusQuorumReport:
        raise ValueError("report must be a ResearchSourceAuthorityConsensusQuorumReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_consensus_quorum_report_digest(
    report: ResearchSourceAuthorityConsensusQuorumReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityConsensusQuorumReport:
        raise ValueError("report must be a ResearchSourceAuthorityConsensusQuorumReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_authority_consensus_quorum_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _require_public_payload_hard_flags(payload)
    _verify_public_digest(payload)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityConsensusQuorumInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityConsensusQuorumInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityConsensusQuorumInput",
            )
        _require_hard_flags("input", row)
        if row.quorum_bucket in seen:
            raise ValueError("inputs must be unique by quorum_bucket")
        seen.add(row.quorum_bucket)
    return tuple(sorted(rows, key=lambda row: row.quorum_bucket))


def _quorum_rows(
    inputs: tuple[ResearchSourceAuthorityConsensusQuorumInput, ...],
    *,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> tuple[ResearchSourceAuthorityConsensusQuorumRow, ...]:
    return tuple(sorted((_quorum_row(row, config=config) for row in inputs), key=_row_sort_key))


def _quorum_row(
    row: ResearchSourceAuthorityConsensusQuorumInput,
    *,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> ResearchSourceAuthorityConsensusQuorumRow:
    total_source_count = (row.primary_source_count + row.secondary_source_count).quantize(QUANT)
    source_tier_mix_score = _source_tier_mix_score(row, total_source_count, config=config)
    freshness_score = _freshness_score(row.max_source_age_seconds, config=config)
    independence_score = _bounded_ratio(
        row.independent_source_count,
        config.min_independent_source_count,
    )
    contradiction_support_score = (ONE - row.contradiction_pressure_score).quantize(QUANT)
    coverage_score = (ONE - row.coverage_gap_score).quantize(QUANT)
    consensus_score = _consensus_score(
        source_tier_mix_score=source_tier_mix_score,
        freshness_score=freshness_score,
        independence_score=independence_score,
        contradiction_support_score=contradiction_support_score,
        coverage_score=coverage_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        total_source_count=total_source_count,
        consensus_score=consensus_score,
        config=config,
    )
    return ResearchSourceAuthorityConsensusQuorumRow(
        quorum_bucket=row.quorum_bucket,
        primary_source_count=row.primary_source_count,
        secondary_source_count=row.secondary_source_count,
        total_source_count=total_source_count,
        independent_source_count=row.independent_source_count,
        max_source_age_seconds=row.max_source_age_seconds,
        contradiction_pressure_score=row.contradiction_pressure_score,
        coverage_gap_score=row.coverage_gap_score,
        source_tier_mix_score=source_tier_mix_score,
        freshness_score=freshness_score,
        independence_score=independence_score,
        contradiction_support_score=contradiction_support_score,
        coverage_score=coverage_score,
        consensus_score=consensus_score,
        quorum_risk_score=(ONE - consensus_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityConsensusQuorumInput,
    *,
    total_source_count: Decimal,
    consensus_score: Decimal,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.primary_source_count < config.min_primary_source_count:
        reasons.append(WEAK_TIER_MIX_BLOCK_REASON)
    elif total_source_count < config.min_total_source_count:
        reasons.append(WEAK_TIER_MIX_WATCH_REASON)
    if row.max_source_age_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_SOURCES_BLOCK_REASON)
    elif row.max_source_age_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_SOURCES_WATCH_REASON)
    if row.independent_source_count == ZERO:
        reasons.append(LOW_INDEPENDENCE_BLOCK_REASON)
    elif row.independent_source_count < config.min_independent_source_count:
        reasons.append(LOW_INDEPENDENCE_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.coverage_gap_score >= config.coverage_gap_block_score:
        reasons.append(COVERAGE_GAP_BLOCK_REASON)
    elif row.coverage_gap_score >= config.coverage_gap_watch_score:
        reasons.append(COVERAGE_GAP_WATCH_REASON)
    if consensus_score < config.watch_consensus_score:
        reasons.append(LOW_SCORE_BLOCK_REASON)
    elif consensus_score < config.pass_consensus_score:
        reasons.append(LOW_SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _source_tier_mix_score(
    row: ResearchSourceAuthorityConsensusQuorumInput,
    total_source_count: Decimal,
    *,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        primary_ratio = min(
            row.primary_source_count / config.min_primary_source_count,
            ONE,
        ).quantize(QUANT)
        total_ratio = min(total_source_count / config.min_total_source_count, ONE).quantize(
            QUANT,
        )
        return ((primary_ratio + total_ratio) / TWO).quantize(QUANT)


def _freshness_score(
    max_source_age_seconds: Decimal,
    *,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> Decimal:
    if max_source_age_seconds <= config.freshness_watch_age_seconds:
        return ONE
    if max_source_age_seconds >= config.freshness_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = config.freshness_block_age_seconds - config.freshness_watch_age_seconds
        stale_fraction = (max_source_age_seconds - config.freshness_watch_age_seconds) / span
        return (ONE - stale_fraction).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _consensus_score(
    *,
    source_tier_mix_score: Decimal,
    freshness_score: Decimal,
    independence_score: Decimal,
    contradiction_support_score: Decimal,
    coverage_score: Decimal,
    config: ResearchSourceAuthorityConsensusQuorumConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            source_tier_mix_score * config.tier_mix_weight
            + freshness_score * config.freshness_weight
            + independence_score * config.independence_weight
            + contradiction_support_score * config.contradiction_weight
            + coverage_score * config.coverage_weight
        )
        return min(score, ONE).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...],
) -> tuple[ResearchSourceAuthorityConsensusQuorumReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityConsensusQuorumReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceAuthorityConsensusQuorumReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(row: ResearchSourceAuthorityConsensusQuorumRow) -> tuple[Decimal, str]:
    return (-row.quorum_risk_score, row.quorum_bucket)


def _status_count(
    rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityConsensusQuorumRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityConsensusQuorumConfig) -> None:
    if config.min_primary_source_count > config.min_total_source_count:
        raise ValueError("min_primary_source_count must not exceed min_total_source_count")
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError("freshness_watch_age_seconds must be less than freshness_block_age_seconds")
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    if config.coverage_gap_watch_score > config.coverage_gap_block_score:
        raise ValueError("coverage_gap_watch_score must not exceed coverage_gap_block_score")
    if config.pass_consensus_score <= config.watch_consensus_score:
        raise ValueError("pass_consensus_score must be greater than watch_consensus_score")
    weight_sum = (
        config.tier_mix_weight
        + config.freshness_weight
        + config.independence_weight
        + config.contradiction_weight
        + config.coverage_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchSourceAuthorityConsensusQuorumRow) -> None:
    if row.total_source_count != (row.primary_source_count + row.secondary_source_count).quantize(
        QUANT,
    ):
        raise ValueError("total_source_count must match source counts")
    if row.quorum_risk_score != (ONE - row.consensus_score).quantize(QUANT):
        raise ValueError("quorum_risk_score must match consensus_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourceAuthorityConsensusQuorumReport) -> None:
    if report.quorum_item_count != _count(len(report.rows)):
        raise ValueError("quorum_item_count must match rows")
    for status, field_name in (
        ("pass", "pass_quorum_item_count"),
        ("watch", "watch_quorum_item_count"),
        ("block", "block_quorum_item_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "weak_source_tier_mix_count",
            (WEAK_TIER_MIX_WATCH_REASON, WEAK_TIER_MIX_BLOCK_REASON),
        ),
        ("stale_source_count", (STALE_SOURCES_WATCH_REASON, STALE_SOURCES_BLOCK_REASON)),
        (
            "thin_independence_count",
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        ("coverage_gap_count", (COVERAGE_GAP_WATCH_REASON, COVERAGE_GAP_BLOCK_REASON)),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.lowest_consensus_score != min(
        (row.consensus_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_consensus_score must match rows")
    if report.highest_quorum_risk_score != max(
        (row.quorum_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_quorum_risk_score must match rows")
    if report.oldest_source_age_seconds != max(
        (row.max_source_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_source_age_seconds must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.highest_coverage_gap_score != max(
        (row.coverage_gap_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_coverage_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic quorum risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityConsensusQuorumRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityConsensusQuorumRow:
            raise ValueError("rows must contain ResearchSourceAuthorityConsensusQuorumRow")
        _require_hard_flags("row", row)
        if row.quorum_bucket in seen:
            raise ValueError("rows must be unique by quorum_bucket")
        seen.add(row.quorum_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuthorityConsensusQuorumReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceAuthorityConsensusQuorumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityConsensusQuorumReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    expected_order = tuple(reason for reason in REPORT_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_bucket(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public bucket label")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _require_public_payload_hard_flags(
    value: object,
    *,
    field_name: str = "public payload",
) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name}.{flag_name} must be True")
        for key, item in value.items():
            _require_public_payload_hard_flags(
                item,
                field_name=f"{field_name}.{key}",
            )
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_hard_flags(
                item,
                field_name=f"{field_name}[{index}]",
            )


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(report: ResearchSourceAuthorityConsensusQuorumReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest_from_public_payload(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityConsensusQuorumReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    _require_public_payload_hard_flags(payload)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_CONSENSUS_QUORUM_STATUSES",
    "ResearchSourceAuthorityConsensusQuorumConfig",
    "ResearchSourceAuthorityConsensusQuorumInput",
    "ResearchSourceAuthorityConsensusQuorumReasonCodeCount",
    "ResearchSourceAuthorityConsensusQuorumReport",
    "ResearchSourceAuthorityConsensusQuorumRow",
    "build_research_source_authority_consensus_quorum_report",
    "research_source_authority_consensus_quorum_report_digest",
    "research_source_authority_consensus_quorum_report_payload",
    "validate_research_source_authority_consensus_quorum_public_payload",
    "validate_research_source_authority_consensus_quorum_report_digest",
)
