"""Pure report-only source authority recheck consensus scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_REPORT_CONFIG_VERSION = (
    "research-source-authority-recheck-consensus-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_recheck_consensus_empty"
CLEAR_REASON = "research_source_authority_recheck_consensus_clear"
INSUFFICIENT_AUTHORITY_BLOCK_REASON = (
    "research_source_authority_recheck_consensus_insufficient_authority_block"
)
LOW_COVERAGE_WATCH_REASON = (
    "research_source_authority_recheck_consensus_low_coverage_watch"
)
LOW_COVERAGE_BLOCK_REASON = (
    "research_source_authority_recheck_consensus_low_coverage_block"
)
STALE_RECHECK_WATCH_REASON = (
    "research_source_authority_recheck_consensus_stale_recheck_watch"
)
STALE_RECHECK_BLOCK_REASON = (
    "research_source_authority_recheck_consensus_stale_recheck_block"
)
DISSENT_WATCH_REASON = "research_source_authority_recheck_consensus_dissent_watch"
DISSENT_BLOCK_REASON = "research_source_authority_recheck_consensus_dissent_block"
LOW_CONSENSUS_WATCH_REASON = (
    "research_source_authority_recheck_consensus_low_consensus_watch"
)
LOW_CONSENSUS_BLOCK_REASON = (
    "research_source_authority_recheck_consensus_low_consensus_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    INSUFFICIENT_AUTHORITY_BLOCK_REASON,
    LOW_COVERAGE_BLOCK_REASON,
    STALE_RECHECK_BLOCK_REASON,
    DISSENT_BLOCK_REASON,
    LOW_CONSENSUS_BLOCK_REASON,
    LOW_COVERAGE_WATCH_REASON,
    STALE_RECHECK_WATCH_REASON,
    DISSENT_WATCH_REASON,
    LOW_CONSENSUS_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "slug",
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
    "mysql://",
    "jdbc:",
    "candidate-",
    "candidate_id",
    "market-",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityRecheckConsensusConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_REPORT_CONFIG_VERSION
    )
    min_authoritative_source_count: Decimal = Decimal("2.000000")
    min_rechecked_source_count: Decimal = Decimal("2.000000")
    recheck_coverage_watch_ratio: Decimal = Decimal("0.750000")
    recheck_coverage_block_ratio: Decimal = Decimal("0.500000")
    stale_recheck_watch_age_seconds: Decimal = Decimal("3600.000000")
    stale_recheck_block_age_seconds: Decimal = Decimal("7200.000000")
    dissent_watch_ratio: Decimal = Decimal("0.250000")
    dissent_block_ratio: Decimal = Decimal("0.500000")
    consensus_pass_ratio: Decimal = Decimal("0.800000")
    consensus_watch_ratio: Decimal = Decimal("0.600000")
    consensus_weight: Decimal = Decimal("0.500000")
    coverage_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.200000")
    dissent_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityRecheckConsensusConfig:
            raise TypeError(
                "ResearchSourceAuthorityRecheckConsensusConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityRecheckConsensusConfig:
            raise ValueError(
                "config must be exactly ResearchSourceAuthorityRecheckConsensusConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_authoritative_source_count",
            "min_rechecked_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_recheck_watch_age_seconds",
            "stale_recheck_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recheck_coverage_watch_ratio",
            "recheck_coverage_block_ratio",
            "dissent_watch_ratio",
            "dissent_block_ratio",
            "consensus_pass_ratio",
            "consensus_watch_ratio",
            "consensus_weight",
            "coverage_weight",
            "freshness_weight",
            "dissent_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRecheckConsensusInput:
    authority_bucket: str
    authoritative_source_count: Decimal
    rechecked_source_count: Decimal
    agreeing_source_count: Decimal
    dissenting_source_count: Decimal
    max_recheck_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityRecheckConsensusInput:
            raise TypeError(
                "ResearchSourceAuthorityRecheckConsensusInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityRecheckConsensusInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityRecheckConsensusInput",
            )
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_bucket("authority_bucket", self.authority_bucket),
        )
        for field_name in (
            "authoritative_source_count",
            "rechecked_source_count",
            "agreeing_source_count",
            "dissenting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recheck_age_seconds",
            _require_nonnegative_decimal(
                "max_recheck_age_seconds",
                self.max_recheck_age_seconds,
            ),
        )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityRecheckConsensusRow:
    authority_bucket: str
    authoritative_source_count: Decimal
    rechecked_source_count: Decimal
    agreeing_source_count: Decimal
    dissenting_source_count: Decimal
    max_recheck_age_seconds: Decimal
    recheck_coverage_ratio: Decimal
    consensus_ratio: Decimal
    freshness_score: Decimal
    dissent_ratio: Decimal
    authority_consensus_score: Decimal
    recheck_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityRecheckConsensusRow:
            raise TypeError(
                "ResearchSourceAuthorityRecheckConsensusRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityRecheckConsensusRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityRecheckConsensusRow")
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_bucket("authority_bucket", self.authority_bucket),
        )
        for field_name in (
            "authoritative_source_count",
            "rechecked_source_count",
            "agreeing_source_count",
            "dissenting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recheck_age_seconds",
            _require_nonnegative_decimal(
                "max_recheck_age_seconds",
                self.max_recheck_age_seconds,
            ),
        )
        for field_name in (
            "recheck_coverage_ratio",
            "consensus_ratio",
            "freshness_score",
            "dissent_ratio",
            "authority_consensus_score",
            "recheck_risk_score",
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
class ResearchSourceAuthorityRecheckConsensusReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityRecheckConsensusReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthorityRecheckConsensusReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityRecheckConsensusReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceAuthorityRecheckConsensusReasonCodeCount",
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
class ResearchSourceAuthorityRecheckConsensusReport:
    generated_at: datetime
    config_version: str
    authority_bucket_count: Decimal
    pass_bucket_count: Decimal
    watch_bucket_count: Decimal
    block_bucket_count: Decimal
    low_authority_count: Decimal
    low_recheck_coverage_count: Decimal
    stale_recheck_count: Decimal
    dissenting_authority_count: Decimal
    low_consensus_count: Decimal
    lowest_authority_consensus_score: Decimal
    highest_recheck_risk_score: Decimal
    oldest_recheck_age_seconds: Decimal
    highest_dissent_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityRecheckConsensusReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityRecheckConsensusReport:
            raise TypeError(
                "ResearchSourceAuthorityRecheckConsensusReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityRecheckConsensusReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityRecheckConsensusReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "authority_bucket_count",
            "pass_bucket_count",
            "watch_bucket_count",
            "block_bucket_count",
            "low_authority_count",
            "low_recheck_coverage_count",
            "stale_recheck_count",
            "dissenting_authority_count",
            "low_consensus_count",
            "oldest_recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_authority_consensus_score",
            "highest_recheck_risk_score",
            "highest_dissent_ratio",
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


def build_research_source_authority_recheck_consensus_report(
    inputs: list[ResearchSourceAuthorityRecheckConsensusInput]
    | tuple[ResearchSourceAuthorityRecheckConsensusInput, ...],
    *,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityRecheckConsensusReport:
    if type(config) is not ResearchSourceAuthorityRecheckConsensusConfig:
        raise ValueError("config must be a ResearchSourceAuthorityRecheckConsensusConfig")
    _require_hard_flags("config", config)
    rows = _recheck_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityRecheckConsensusReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        authority_bucket_count=_count(len(rows)),
        pass_bucket_count=_status_count(rows, "pass"),
        watch_bucket_count=_status_count(rows, "watch"),
        block_bucket_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(rows, (INSUFFICIENT_AUTHORITY_BLOCK_REASON,)),
        low_recheck_coverage_count=_reason_count(
            rows,
            (LOW_COVERAGE_WATCH_REASON, LOW_COVERAGE_BLOCK_REASON),
        ),
        stale_recheck_count=_reason_count(
            rows,
            (STALE_RECHECK_WATCH_REASON, STALE_RECHECK_BLOCK_REASON),
        ),
        dissenting_authority_count=_reason_count(
            rows,
            (DISSENT_WATCH_REASON, DISSENT_BLOCK_REASON),
        ),
        low_consensus_count=_reason_count(
            rows,
            (LOW_CONSENSUS_WATCH_REASON, LOW_CONSENSUS_BLOCK_REASON),
        ),
        lowest_authority_consensus_score=min(
            (row.authority_consensus_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_recheck_risk_score=max(
            (row.recheck_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_recheck_age_seconds=max(
            (row.max_recheck_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_dissent_ratio=max(
            (row.dissent_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_authority_recheck_consensus_report_payload(
    report: ResearchSourceAuthorityRecheckConsensusReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityRecheckConsensusReport:
        raise ValueError("report must be a ResearchSourceAuthorityRecheckConsensusReport")
    validate_research_source_authority_recheck_consensus_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_recheck_consensus_report_digest(
    report: ResearchSourceAuthorityRecheckConsensusReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityRecheckConsensusReport:
        raise ValueError("report must be a ResearchSourceAuthorityRecheckConsensusReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_recheck_consensus_report_digest(
    report: ResearchSourceAuthorityRecheckConsensusReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityRecheckConsensusReport:
        raise ValueError("report must be a ResearchSourceAuthorityRecheckConsensusReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_authority_recheck_consensus_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityRecheckConsensusInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityRecheckConsensusInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityRecheckConsensusInput",
            )
        _require_hard_flags("input", row)
        if row.authority_bucket in seen:
            raise ValueError("inputs must be unique by authority_bucket")
        seen.add(row.authority_bucket)
    return tuple(sorted(rows, key=lambda row: row.authority_bucket))


def _recheck_rows(
    inputs: tuple[ResearchSourceAuthorityRecheckConsensusInput, ...],
    *,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
) -> tuple[ResearchSourceAuthorityRecheckConsensusRow, ...]:
    return tuple(sorted((_recheck_row(row, config=config) for row in inputs), key=_row_sort_key))


def _recheck_row(
    row: ResearchSourceAuthorityRecheckConsensusInput,
    *,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
) -> ResearchSourceAuthorityRecheckConsensusRow:
    recheck_coverage_ratio = _bounded_ratio(
        row.rechecked_source_count,
        row.authoritative_source_count,
    )
    consensus_ratio = _bounded_ratio(
        row.agreeing_source_count,
        row.rechecked_source_count,
    )
    freshness_score = _freshness_score(row.max_recheck_age_seconds, config=config)
    dissent_ratio = _bounded_ratio(
        row.dissenting_source_count,
        row.rechecked_source_count,
    )
    authority_consensus_score = _authority_consensus_score(
        consensus_ratio=consensus_ratio,
        coverage_ratio=recheck_coverage_ratio,
        freshness_score=freshness_score,
        dissent_ratio=dissent_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        recheck_coverage_ratio=recheck_coverage_ratio,
        consensus_ratio=consensus_ratio,
        authority_consensus_score=authority_consensus_score,
        config=config,
    )
    return ResearchSourceAuthorityRecheckConsensusRow(
        authority_bucket=row.authority_bucket,
        authoritative_source_count=row.authoritative_source_count,
        rechecked_source_count=row.rechecked_source_count,
        agreeing_source_count=row.agreeing_source_count,
        dissenting_source_count=row.dissenting_source_count,
        max_recheck_age_seconds=row.max_recheck_age_seconds,
        recheck_coverage_ratio=recheck_coverage_ratio,
        consensus_ratio=consensus_ratio,
        freshness_score=freshness_score,
        dissent_ratio=dissent_ratio,
        authority_consensus_score=authority_consensus_score,
        recheck_risk_score=(ONE - authority_consensus_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityRecheckConsensusInput,
    *,
    recheck_coverage_ratio: Decimal,
    consensus_ratio: Decimal,
    authority_consensus_score: Decimal,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authoritative_source_count < config.min_authoritative_source_count:
        reasons.append(INSUFFICIENT_AUTHORITY_BLOCK_REASON)
    if recheck_coverage_ratio < config.recheck_coverage_block_ratio:
        reasons.append(LOW_COVERAGE_BLOCK_REASON)
    elif recheck_coverage_ratio < config.recheck_coverage_watch_ratio:
        reasons.append(LOW_COVERAGE_WATCH_REASON)
    if row.max_recheck_age_seconds >= config.stale_recheck_block_age_seconds:
        reasons.append(STALE_RECHECK_BLOCK_REASON)
    elif row.max_recheck_age_seconds > config.stale_recheck_watch_age_seconds:
        reasons.append(STALE_RECHECK_WATCH_REASON)
    if row.dissenting_source_count > ZERO:
        dissent_ratio = _bounded_ratio(row.dissenting_source_count, row.rechecked_source_count)
        if dissent_ratio >= config.dissent_block_ratio:
            reasons.append(DISSENT_BLOCK_REASON)
        elif dissent_ratio >= config.dissent_watch_ratio:
            reasons.append(DISSENT_WATCH_REASON)
    if consensus_ratio < config.consensus_watch_ratio:
        reasons.append(LOW_CONSENSUS_BLOCK_REASON)
    elif (
        consensus_ratio < config.consensus_pass_ratio
        or authority_consensus_score < config.consensus_pass_ratio
    ):
        reasons.append(LOW_CONSENSUS_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _freshness_score(
    max_recheck_age_seconds: Decimal,
    *,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
) -> Decimal:
    if max_recheck_age_seconds <= config.stale_recheck_watch_age_seconds:
        return ONE
    if max_recheck_age_seconds >= config.stale_recheck_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = (
            config.stale_recheck_block_age_seconds
            - config.stale_recheck_watch_age_seconds
        )
        stale_fraction = (
            max_recheck_age_seconds - config.stale_recheck_watch_age_seconds
        ) / span
        return (ONE - stale_fraction).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _authority_consensus_score(
    *,
    consensus_ratio: Decimal,
    coverage_ratio: Decimal,
    freshness_score: Decimal,
    dissent_ratio: Decimal,
    config: ResearchSourceAuthorityRecheckConsensusConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            consensus_ratio * config.consensus_weight
            + coverage_ratio * config.coverage_weight
            + freshness_score * config.freshness_weight
            + (ONE - dissent_ratio).quantize(QUANT) * config.dissent_weight
        )
        return min(score, ONE).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...],
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
    rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...],
) -> tuple[ResearchSourceAuthorityRecheckConsensusReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityRecheckConsensusReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceAuthorityRecheckConsensusReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(row: ResearchSourceAuthorityRecheckConsensusRow) -> tuple[Decimal, str]:
    return (-row.recheck_risk_score, row.authority_bucket)


def _status_count(
    rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityRecheckConsensusRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityRecheckConsensusConfig) -> None:
    if config.recheck_coverage_block_ratio > config.recheck_coverage_watch_ratio:
        raise ValueError(
            "recheck_coverage_block_ratio must not exceed recheck_coverage_watch_ratio",
        )
    if config.stale_recheck_watch_age_seconds >= config.stale_recheck_block_age_seconds:
        raise ValueError(
            "stale_recheck_watch_age_seconds must be less than block age seconds",
        )
    if config.dissent_watch_ratio > config.dissent_block_ratio:
        raise ValueError("dissent_watch_ratio must not exceed dissent_block_ratio")
    if config.consensus_pass_ratio <= config.consensus_watch_ratio:
        raise ValueError("consensus_pass_ratio must be greater than consensus_watch_ratio")
    weight_sum = (
        config.consensus_weight
        + config.coverage_weight
        + config.freshness_weight
        + config.dissent_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_input(row: ResearchSourceAuthorityRecheckConsensusInput) -> None:
    rechecked_parts = row.agreeing_source_count + row.dissenting_source_count
    if rechecked_parts > row.rechecked_source_count:
        raise ValueError("rechecked_source_count must cover agreeing and dissenting counts")
    if row.rechecked_source_count > row.authoritative_source_count:
        raise ValueError("rechecked_source_count must not exceed authoritative_source_count")


def _validate_row(row: ResearchSourceAuthorityRecheckConsensusRow) -> None:
    if row.agreeing_source_count + row.dissenting_source_count > row.rechecked_source_count:
        raise ValueError("rechecked_source_count must cover agreeing and dissenting counts")
    if row.rechecked_source_count > row.authoritative_source_count:
        raise ValueError("rechecked_source_count must not exceed authoritative_source_count")
    if row.recheck_risk_score != (ONE - row.authority_consensus_score).quantize(QUANT):
        raise ValueError("recheck_risk_score must match authority_consensus_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourceAuthorityRecheckConsensusReport) -> None:
    if report.authority_bucket_count != _count(len(report.rows)):
        raise ValueError("authority_bucket_count must match rows")
    for status, field_name in (
        ("pass", "pass_bucket_count"),
        ("watch", "watch_bucket_count"),
        ("block", "block_bucket_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("low_authority_count", (INSUFFICIENT_AUTHORITY_BLOCK_REASON,)),
        (
            "low_recheck_coverage_count",
            (LOW_COVERAGE_WATCH_REASON, LOW_COVERAGE_BLOCK_REASON),
        ),
        ("stale_recheck_count", (STALE_RECHECK_WATCH_REASON, STALE_RECHECK_BLOCK_REASON)),
        ("dissenting_authority_count", (DISSENT_WATCH_REASON, DISSENT_BLOCK_REASON)),
        ("low_consensus_count", (LOW_CONSENSUS_WATCH_REASON, LOW_CONSENSUS_BLOCK_REASON)),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.lowest_authority_consensus_score != min(
        (row.authority_consensus_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authority_consensus_score must match rows")
    if report.highest_recheck_risk_score != max(
        (row.recheck_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_recheck_risk_score must match rows")
    if report.oldest_recheck_age_seconds != max(
        (row.max_recheck_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_recheck_age_seconds must match rows")
    if report.highest_dissent_ratio != max(
        (row.dissent_ratio for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_dissent_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic recheck risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityRecheckConsensusRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityRecheckConsensusRow:
            raise ValueError("rows must contain ResearchSourceAuthorityRecheckConsensusRow")
        _require_hard_flags("row", row)
        if row.authority_bucket in seen:
            raise ValueError("rows must be unique by authority_bucket")
        seen.add(row.authority_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuthorityRecheckConsensusReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceAuthorityRecheckConsensusReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityRecheckConsensusReasonCodeCount",
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
        or value not in RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_STATUSES
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


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(report: ResearchSourceAuthorityRecheckConsensusReport) -> None:
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
    report: ResearchSourceAuthorityRecheckConsensusReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
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
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_RECHECK_CONSENSUS_STATUSES",
    "ResearchSourceAuthorityRecheckConsensusConfig",
    "ResearchSourceAuthorityRecheckConsensusInput",
    "ResearchSourceAuthorityRecheckConsensusReasonCodeCount",
    "ResearchSourceAuthorityRecheckConsensusReport",
    "ResearchSourceAuthorityRecheckConsensusRow",
    "build_research_source_authority_recheck_consensus_report",
    "research_source_authority_recheck_consensus_report_digest",
    "research_source_authority_recheck_consensus_report_payload",
    "validate_research_source_authority_recheck_consensus_public_payload",
    "validate_research_source_authority_recheck_consensus_report_digest",
)
