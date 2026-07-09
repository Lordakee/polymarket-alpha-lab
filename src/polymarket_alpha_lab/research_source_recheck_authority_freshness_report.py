"""Pure report-only source recheck authority freshness scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_REPORT_CONFIG_VERSION = (
    "research-source-recheck-authority-freshness-report-v0"
)
RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_recheck_authority_freshness_empty"
CLEAR_REASON = "research_source_recheck_authority_freshness_clear"
LOW_AUTHORITY_WATCH_REASON = (
    "research_source_recheck_authority_freshness_low_authority_watch"
)
LOW_AUTHORITY_BLOCK_REASON = (
    "research_source_recheck_authority_freshness_low_authority_block"
)
STALE_RECHECK_WATCH_REASON = (
    "research_source_recheck_authority_freshness_stale_recheck_watch"
)
STALE_RECHECK_BLOCK_REASON = (
    "research_source_recheck_authority_freshness_stale_recheck_block"
)
THIN_AUTHORITY_CORROBORATION_WATCH_REASON = (
    "research_source_recheck_authority_freshness_"
    "thin_authority_corroboration_watch"
)
THIN_AUTHORITY_CORROBORATION_BLOCK_REASON = (
    "research_source_recheck_authority_freshness_"
    "thin_authority_corroboration_block"
)
LOW_RETRIEVAL_CONFIDENCE_WATCH_REASON = (
    "research_source_recheck_authority_freshness_low_retrieval_confidence_watch"
)
LOW_RETRIEVAL_CONFIDENCE_BLOCK_REASON = (
    "research_source_recheck_authority_freshness_low_retrieval_confidence_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "research_source_recheck_authority_freshness_contradiction_pressure_watch"
)
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "research_source_recheck_authority_freshness_contradiction_pressure_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    STALE_RECHECK_BLOCK_REASON,
    THIN_AUTHORITY_CORROBORATION_BLOCK_REASON,
    LOW_RETRIEVAL_CONFIDENCE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    STALE_RECHECK_WATCH_REASON,
    THIN_AUTHORITY_CORROBORATION_WATCH_REASON,
    LOW_RETRIEVAL_CONFIDENCE_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
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
class ResearchSourceRecheckAuthorityFreshnessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_REPORT_CONFIG_VERSION
    )
    authority_watch_floor: Decimal = Decimal("0.700000")
    authority_block_floor: Decimal = Decimal("0.500000")
    recheck_freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    recheck_freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    authority_corroboration_watch_count: Decimal = Decimal("2.000000")
    authority_corroboration_block_count: Decimal = Decimal("0.000000")
    retrieval_confidence_watch_floor: Decimal = Decimal("0.800000")
    retrieval_confidence_block_floor: Decimal = Decimal("0.600000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    authority_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.250000")
    corroboration_weight: Decimal = Decimal("0.200000")
    retrieval_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRecheckAuthorityFreshnessConfig:
            raise TypeError(
                "ResearchSourceRecheckAuthorityFreshnessConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRecheckAuthorityFreshnessConfig:
            raise ValueError(
                "config must be exactly ResearchSourceRecheckAuthorityFreshnessConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "authority_watch_floor",
            "authority_block_floor",
            "retrieval_confidence_watch_floor",
            "retrieval_confidence_block_floor",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "authority_weight",
            "freshness_weight",
            "corroboration_weight",
            "retrieval_weight",
            "contradiction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recheck_freshness_watch_age_seconds",
            "recheck_freshness_block_age_seconds",
            "authority_corroboration_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name))
                if field_name == "authority_corroboration_watch_count"
                else _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_corroboration_block_count",
            _require_nonnegative_whole_decimal(
                "authority_corroboration_block_count",
                self.authority_corroboration_block_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceRecheckAuthorityFreshnessInput:
    source_bucket: str
    source_authority_score: Decimal
    latest_recheck_age_seconds: Decimal
    authoritative_corroboration_count: Decimal
    retrieval_confidence_score: Decimal
    contradiction_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRecheckAuthorityFreshnessInput:
            raise TypeError(
                "ResearchSourceRecheckAuthorityFreshnessInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRecheckAuthorityFreshnessInput:
            raise ValueError(
                "input must be exactly ResearchSourceRecheckAuthorityFreshnessInput",
            )
        object.__setattr__(
            self,
            "source_bucket",
            _require_public_bucket("source_bucket", self.source_bucket),
        )
        for field_name in (
            "source_authority_score",
            "retrieval_confidence_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_recheck_age_seconds",
            _require_nonnegative_decimal(
                "latest_recheck_age_seconds",
                self.latest_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "authoritative_corroboration_count",
            _require_nonnegative_whole_decimal(
                "authoritative_corroboration_count",
                self.authoritative_corroboration_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceRecheckAuthorityFreshnessRow:
    source_bucket: str
    source_authority_score: Decimal
    authority_band: str
    latest_recheck_age_seconds: Decimal
    freshness_band: str
    authoritative_corroboration_count: Decimal
    authority_corroboration_score: Decimal
    retrieval_confidence_score: Decimal
    contradiction_pressure_score: Decimal
    authority_freshness_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRecheckAuthorityFreshnessRow:
            raise TypeError(
                "ResearchSourceRecheckAuthorityFreshnessRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRecheckAuthorityFreshnessRow:
            raise ValueError("row must be exactly ResearchSourceRecheckAuthorityFreshnessRow")
        object.__setattr__(
            self,
            "source_bucket",
            _require_public_bucket("source_bucket", self.source_bucket),
        )
        for field_name in (
            "source_authority_score",
            "authority_corroboration_score",
            "retrieval_confidence_score",
            "contradiction_pressure_score",
            "authority_freshness_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_recheck_age_seconds",
            _require_nonnegative_decimal(
                "latest_recheck_age_seconds",
                self.latest_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "authoritative_corroboration_count",
            _require_nonnegative_whole_decimal(
                "authoritative_corroboration_count",
                self.authoritative_corroboration_count,
            ),
        )
        _require_authority_band("authority_band", self.authority_band)
        _require_freshness_band("freshness_band", self.freshness_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceRecheckAuthorityFreshnessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRecheckAuthorityFreshnessReasonCodeCount:
            raise TypeError(
                "ResearchSourceRecheckAuthorityFreshnessReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRecheckAuthorityFreshnessReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceRecheckAuthorityFreshnessReasonCodeCount",
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
class ResearchSourceRecheckAuthorityFreshnessReport:
    generated_at: datetime
    config_version: str
    recheck_bucket_count: Decimal
    pass_recheck_bucket_count: Decimal
    watch_recheck_bucket_count: Decimal
    block_recheck_bucket_count: Decimal
    low_authority_count: Decimal
    stale_recheck_count: Decimal
    thin_authority_corroboration_count: Decimal
    low_retrieval_confidence_count: Decimal
    contradiction_pressure_count: Decimal
    highest_authority_freshness_risk_score: Decimal
    oldest_recheck_age_seconds: Decimal
    lowest_source_authority_score: Decimal
    lowest_authoritative_corroboration_count: Decimal
    lowest_retrieval_confidence_score: Decimal
    highest_contradiction_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceRecheckAuthorityFreshnessReasonCodeCount, ...]
    rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRecheckAuthorityFreshnessReport:
            raise TypeError(
                "ResearchSourceRecheckAuthorityFreshnessReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRecheckAuthorityFreshnessReport:
            raise ValueError(
                "report must be exactly ResearchSourceRecheckAuthorityFreshnessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "recheck_bucket_count",
            "pass_recheck_bucket_count",
            "watch_recheck_bucket_count",
            "block_recheck_bucket_count",
            "low_authority_count",
            "stale_recheck_count",
            "thin_authority_corroboration_count",
            "low_retrieval_confidence_count",
            "contradiction_pressure_count",
            "oldest_recheck_age_seconds",
            "lowest_authoritative_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_authority_freshness_risk_score",
            "lowest_source_authority_score",
            "lowest_retrieval_confidence_score",
            "highest_contradiction_pressure_score",
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


def build_research_source_recheck_authority_freshness_report(
    inputs: list[ResearchSourceRecheckAuthorityFreshnessInput]
    | tuple[ResearchSourceRecheckAuthorityFreshnessInput, ...],
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
    generated_at: datetime,
) -> ResearchSourceRecheckAuthorityFreshnessReport:
    if type(config) is not ResearchSourceRecheckAuthorityFreshnessConfig:
        raise ValueError("config must be a ResearchSourceRecheckAuthorityFreshnessConfig")
    _require_hard_flags("config", config)
    rows = _recheck_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceRecheckAuthorityFreshnessReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        recheck_bucket_count=_count(len(rows)),
        pass_recheck_bucket_count=_status_count(rows, "pass"),
        watch_recheck_bucket_count=_status_count(rows, "watch"),
        block_recheck_bucket_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        stale_recheck_count=_reason_count(
            rows,
            (STALE_RECHECK_WATCH_REASON, STALE_RECHECK_BLOCK_REASON),
        ),
        thin_authority_corroboration_count=_reason_count(
            rows,
            (
                THIN_AUTHORITY_CORROBORATION_WATCH_REASON,
                THIN_AUTHORITY_CORROBORATION_BLOCK_REASON,
            ),
        ),
        low_retrieval_confidence_count=_reason_count(
            rows,
            (LOW_RETRIEVAL_CONFIDENCE_WATCH_REASON, LOW_RETRIEVAL_CONFIDENCE_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        highest_authority_freshness_risk_score=max(
            (row.authority_freshness_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_recheck_age_seconds=max(
            (row.latest_recheck_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_source_authority_score=min(
            (row.source_authority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_authoritative_corroboration_count=min(
            (row.authoritative_corroboration_count for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_retrieval_confidence_score=min(
            (row.retrieval_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_recheck_authority_freshness_report_payload(
    report: ResearchSourceRecheckAuthorityFreshnessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceRecheckAuthorityFreshnessReport:
        raise ValueError("report must be a ResearchSourceRecheckAuthorityFreshnessReport")
    validate_research_source_recheck_authority_freshness_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_recheck_authority_freshness_report_digest(
    report: ResearchSourceRecheckAuthorityFreshnessReport,
) -> str:
    if type(report) is not ResearchSourceRecheckAuthorityFreshnessReport:
        raise ValueError("report must be a ResearchSourceRecheckAuthorityFreshnessReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_recheck_authority_freshness_report_digest(
    report: ResearchSourceRecheckAuthorityFreshnessReport,
) -> None:
    if type(report) is not ResearchSourceRecheckAuthorityFreshnessReport:
        raise ValueError("report must be a ResearchSourceRecheckAuthorityFreshnessReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_recheck_authority_freshness_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceRecheckAuthorityFreshnessInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceRecheckAuthorityFreshnessInput:
            raise ValueError(
                "inputs must contain ResearchSourceRecheckAuthorityFreshnessInput",
            )
        _require_hard_flags("input", row)
        if row.source_bucket in seen:
            raise ValueError("inputs must be unique by source_bucket")
        seen.add(row.source_bucket)
    return tuple(sorted(rows, key=lambda row: row.source_bucket))


def _recheck_rows(
    inputs: tuple[ResearchSourceRecheckAuthorityFreshnessInput, ...],
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...]:
    return tuple(sorted((_recheck_row(row, config=config) for row in inputs), key=_row_sort_key))


def _recheck_row(
    row: ResearchSourceRecheckAuthorityFreshnessInput,
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> ResearchSourceRecheckAuthorityFreshnessRow:
    authority_corroboration_score = _bounded_ratio(
        row.authoritative_corroboration_count,
        config.authority_corroboration_watch_count,
    )
    risk_score = _authority_freshness_risk_score(
        source_authority_score=row.source_authority_score,
        latest_recheck_age_seconds=row.latest_recheck_age_seconds,
        authority_corroboration_score=authority_corroboration_score,
        retrieval_confidence_score=row.retrieval_confidence_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        config=config,
    )
    reason_codes = _row_reason_codes(row, config=config)
    return ResearchSourceRecheckAuthorityFreshnessRow(
        source_bucket=row.source_bucket,
        source_authority_score=row.source_authority_score,
        authority_band=_authority_band(row.source_authority_score, config=config),
        latest_recheck_age_seconds=row.latest_recheck_age_seconds,
        freshness_band=_freshness_band(row.latest_recheck_age_seconds, config=config),
        authoritative_corroboration_count=row.authoritative_corroboration_count,
        authority_corroboration_score=authority_corroboration_score,
        retrieval_confidence_score=row.retrieval_confidence_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        authority_freshness_risk_score=risk_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceRecheckAuthorityFreshnessInput,
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.source_authority_score <= config.authority_block_floor:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif row.source_authority_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.latest_recheck_age_seconds >= config.recheck_freshness_block_age_seconds:
        reasons.append(STALE_RECHECK_BLOCK_REASON)
    elif row.latest_recheck_age_seconds > config.recheck_freshness_watch_age_seconds:
        reasons.append(STALE_RECHECK_WATCH_REASON)
    if row.authoritative_corroboration_count <= config.authority_corroboration_block_count:
        reasons.append(THIN_AUTHORITY_CORROBORATION_BLOCK_REASON)
    elif row.authoritative_corroboration_count < config.authority_corroboration_watch_count:
        reasons.append(THIN_AUTHORITY_CORROBORATION_WATCH_REASON)
    if row.retrieval_confidence_score <= config.retrieval_confidence_block_floor:
        reasons.append(LOW_RETRIEVAL_CONFIDENCE_BLOCK_REASON)
    elif row.retrieval_confidence_score < config.retrieval_confidence_watch_floor:
        reasons.append(LOW_RETRIEVAL_CONFIDENCE_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _authority_freshness_risk_score(
    *,
    source_authority_score: Decimal,
    latest_recheck_age_seconds: Decimal,
    authority_corroboration_score: Decimal,
    retrieval_confidence_score: Decimal,
    contradiction_pressure_score: Decimal,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - source_authority_score
        freshness_pressure = min(
            latest_recheck_age_seconds / config.recheck_freshness_block_age_seconds,
            ONE,
        )
        corroboration_gap = ONE - authority_corroboration_score
        retrieval_gap = ONE - retrieval_confidence_score
        score = (
            authority_gap * config.authority_weight
            + freshness_pressure * config.freshness_weight
            + corroboration_gap * config.corroboration_weight
            + retrieval_gap * config.retrieval_weight
            + contradiction_pressure_score * config.contradiction_weight
        )
        return min(score, ONE).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _authority_band(
    value: Decimal,
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> str:
    if value >= config.authority_watch_floor:
        return "high"
    if value <= config.authority_block_floor:
        return "low"
    return "medium"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceRecheckAuthorityFreshnessConfig,
) -> str:
    if value <= config.recheck_freshness_watch_age_seconds:
        return "fresh"
    if value < config.recheck_freshness_block_age_seconds:
        return "aging"
    return "stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...],
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
    rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...],
) -> tuple[ResearchSourceRecheckAuthorityFreshnessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceRecheckAuthorityFreshnessReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceRecheckAuthorityFreshnessReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(row: ResearchSourceRecheckAuthorityFreshnessRow) -> tuple[Decimal, str]:
    return (-row.authority_freshness_risk_score, row.source_bucket)


def _status_count(
    rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceRecheckAuthorityFreshnessConfig) -> None:
    if config.authority_watch_floor <= config.authority_block_floor:
        raise ValueError("authority_watch_floor must be greater than authority_block_floor")
    if (
        config.recheck_freshness_watch_age_seconds
        >= config.recheck_freshness_block_age_seconds
    ):
        raise ValueError(
            "recheck_freshness_watch_age_seconds must be less than block age seconds",
        )
    if (
        config.authority_corroboration_block_count
        >= config.authority_corroboration_watch_count
    ):
        raise ValueError(
            "authority_corroboration_block_count must be less than watch count",
        )
    if config.retrieval_confidence_watch_floor <= config.retrieval_confidence_block_floor:
        raise ValueError(
            "retrieval_confidence_watch_floor must be greater than block floor",
        )
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    weight_sum = (
        config.authority_weight
        + config.freshness_weight
        + config.corroboration_weight
        + config.retrieval_weight
        + config.contradiction_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchSourceRecheckAuthorityFreshnessRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourceRecheckAuthorityFreshnessReport) -> None:
    if report.recheck_bucket_count != _count(len(report.rows)):
        raise ValueError("recheck_bucket_count must match rows")
    for status, field_name in (
        ("pass", "pass_recheck_bucket_count"),
        ("watch", "watch_recheck_bucket_count"),
        ("block", "block_recheck_bucket_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_authority_count",
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        (
            "stale_recheck_count",
            (STALE_RECHECK_WATCH_REASON, STALE_RECHECK_BLOCK_REASON),
        ),
        (
            "thin_authority_corroboration_count",
            (
                THIN_AUTHORITY_CORROBORATION_WATCH_REASON,
                THIN_AUTHORITY_CORROBORATION_BLOCK_REASON,
            ),
        ),
        (
            "low_retrieval_confidence_count",
            (
                LOW_RETRIEVAL_CONFIDENCE_WATCH_REASON,
                LOW_RETRIEVAL_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_authority_freshness_risk_score != max(
        (row.authority_freshness_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_authority_freshness_risk_score must match rows")
    if report.oldest_recheck_age_seconds != max(
        (row.latest_recheck_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_recheck_age_seconds must match rows")
    if report.lowest_source_authority_score != min(
        (row.source_authority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_source_authority_score must match rows")
    if report.lowest_authoritative_corroboration_count != min(
        (row.authoritative_corroboration_count for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authoritative_corroboration_count must match rows")
    if report.lowest_retrieval_confidence_score != min(
        (row.retrieval_confidence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_retrieval_confidence_score must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic authority freshness risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceRecheckAuthorityFreshnessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceRecheckAuthorityFreshnessRow:
            raise ValueError("rows must contain ResearchSourceRecheckAuthorityFreshnessRow")
        _require_hard_flags("row", row)
        if row.source_bucket in seen:
            raise ValueError("rows must be unique by source_bucket")
        seen.add(row.source_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceRecheckAuthorityFreshnessReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceRecheckAuthorityFreshnessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceRecheckAuthorityFreshnessReasonCodeCount",
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
        or value not in RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_authority_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "aging", "stale"):
        raise ValueError(f"{field_name} must be fresh, aging, or stale")


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


def _require_or_set_digest(report: ResearchSourceRecheckAuthorityFreshnessReport) -> None:
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
    report: ResearchSourceRecheckAuthorityFreshnessReport,
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
    "DEFAULT_RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RECHECK_AUTHORITY_FRESHNESS_STATUSES",
    "ResearchSourceRecheckAuthorityFreshnessConfig",
    "ResearchSourceRecheckAuthorityFreshnessInput",
    "ResearchSourceRecheckAuthorityFreshnessReasonCodeCount",
    "ResearchSourceRecheckAuthorityFreshnessReport",
    "ResearchSourceRecheckAuthorityFreshnessRow",
    "build_research_source_recheck_authority_freshness_report",
    "research_source_recheck_authority_freshness_report_digest",
    "research_source_recheck_authority_freshness_report_payload",
    "validate_research_source_recheck_authority_freshness_public_payload",
    "validate_research_source_recheck_authority_freshness_report_digest",
)
