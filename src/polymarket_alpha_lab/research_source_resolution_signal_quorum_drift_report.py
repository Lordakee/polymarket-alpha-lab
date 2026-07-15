"""Pure report-only source resolution signal quorum drift scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_REPORT_CONFIG_VERSION = (
    "research-source-resolution-signal-quorum-drift-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_STATUSES = (
    "pass",
    "watch",
    "block",
)

_REASON_PREFIX = "research_source_resolution_signal_quorum_drift_"
EMPTY_REASON = f"{_REASON_PREFIX}empty"
CLEAR_REASON = f"{_REASON_PREFIX}clear"
WEAK_AUTHORITY_MIX_BLOCK_REASON = f"{_REASON_PREFIX}weak_authority_mix_block"
FRESHNESS_LAG_BLOCK_REASON = f"{_REASON_PREFIX}freshness_lag_block"
THIN_CORROBORATION_BLOCK_REASON = f"{_REASON_PREFIX}thin_corroboration_block"
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    f"{_REASON_PREFIX}contradiction_pressure_block"
)
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = (
    f"{_REASON_PREFIX}low_extraction_confidence_block"
)
LOW_SCORE_BLOCK_REASON = f"{_REASON_PREFIX}low_score_block"
WEAK_AUTHORITY_MIX_WATCH_REASON = f"{_REASON_PREFIX}weak_authority_mix_watch"
FRESHNESS_LAG_WATCH_REASON = f"{_REASON_PREFIX}freshness_lag_watch"
THIN_CORROBORATION_WATCH_REASON = f"{_REASON_PREFIX}thin_corroboration_watch"
CONTRADICTION_PRESSURE_WATCH_REASON = (
    f"{_REASON_PREFIX}contradiction_pressure_watch"
)
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = (
    f"{_REASON_PREFIX}low_extraction_confidence_watch"
)
LOW_SCORE_WATCH_REASON = f"{_REASON_PREFIX}low_score_watch"

ROW_REASON_CODES = (
    CLEAR_REASON,
    WEAK_AUTHORITY_MIX_BLOCK_REASON,
    FRESHNESS_LAG_BLOCK_REASON,
    THIN_CORROBORATION_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    LOW_SCORE_BLOCK_REASON,
    WEAK_AUTHORITY_MIX_WATCH_REASON,
    FRESHNESS_LAG_WATCH_REASON,
    THIN_CORROBORATION_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    LOW_SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason
    for reason in REPORT_REASON_CODES
    if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
SHA256_HEX_LENGTH = 64

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate_id",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order_id",
    "trade_id",
    "live_surface",
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
    "candidate_id",
    "market-",
    "market_",
    "market_id",
    "market_slug",
    "market_question",
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

REPORT_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "signal_count",
    "pass_signal_count",
    "watch_signal_count",
    "block_signal_count",
    "weak_authority_mix_count",
    "freshness_lag_count",
    "thin_corroboration_count",
    "contradiction_pressure_count",
    "low_extraction_confidence_count",
    "lowest_quorum_signal_score",
    "highest_quorum_drift_score",
    "highest_freshness_lag_seconds",
    "highest_contradiction_pressure_score",
    "lowest_extraction_confidence_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_PAYLOAD_KEYS = (
    "analyst_bucket",
    "authoritative_source_count",
    "supporting_source_count",
    "total_source_count",
    "corroborating_source_count",
    "freshness_lag_seconds",
    "contradiction_pressure_score",
    "extraction_confidence_score",
    "source_authority_mix_score",
    "freshness_score",
    "corroboration_breadth_score",
    "contradiction_support_score",
    "extraction_confidence_support_score",
    "quorum_signal_score",
    "quorum_drift_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalQuorumDriftConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_REPORT_CONFIG_VERSION
    )
    min_authoritative_source_count: Decimal = Decimal("1.000000")
    min_total_source_count: Decimal = Decimal("3.000000")
    min_corroborating_source_count: Decimal = Decimal("3.000000")
    freshness_watch_lag_seconds: Decimal = Decimal("3600.000000")
    freshness_block_lag_seconds: Decimal = Decimal("7200.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    extraction_confidence_watch_floor: Decimal = Decimal("0.700000")
    extraction_confidence_block_floor: Decimal = Decimal("0.400000")
    pass_quorum_signal_score: Decimal = Decimal("0.750000")
    watch_quorum_signal_score: Decimal = Decimal("0.450000")
    authority_mix_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    corroboration_breadth_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    extraction_confidence_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionSignalQuorumDriftConfig:
            raise TypeError(
                "ResearchSourceResolutionSignalQuorumDriftConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionSignalQuorumDriftConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceResolutionSignalQuorumDriftConfig",
            )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "min_authoritative_source_count",
            "min_total_source_count",
            "min_corroborating_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_lag_seconds",
            "freshness_block_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
            "pass_quorum_signal_score",
            "watch_quorum_signal_score",
            "authority_mix_weight",
            "freshness_weight",
            "corroboration_breadth_weight",
            "contradiction_pressure_weight",
            "extraction_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalQuorumDriftInput:
    analyst_bucket: str
    authoritative_source_count: Decimal
    supporting_source_count: Decimal
    corroborating_source_count: Decimal
    freshness_lag_seconds: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionSignalQuorumDriftInput:
            raise TypeError(
                "ResearchSourceResolutionSignalQuorumDriftInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionSignalQuorumDriftInput:
            raise ValueError(
                "input must be exactly ResearchSourceResolutionSignalQuorumDriftInput",
            )
        object.__setattr__(
            self,
            "analyst_bucket",
            _require_public_bucket("analyst_bucket", self.analyst_bucket),
        )
        for field_name in (
            "authoritative_source_count",
            "supporting_source_count",
            "corroborating_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        for field_name in (
            "contradiction_pressure_score",
            "extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionSignalQuorumDriftRow:
    analyst_bucket: str
    authoritative_source_count: Decimal
    supporting_source_count: Decimal
    total_source_count: Decimal
    corroborating_source_count: Decimal
    freshness_lag_seconds: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    source_authority_mix_score: Decimal
    freshness_score: Decimal
    corroboration_breadth_score: Decimal
    contradiction_support_score: Decimal
    extraction_confidence_support_score: Decimal
    quorum_signal_score: Decimal
    quorum_drift_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionSignalQuorumDriftRow:
            raise TypeError(
                "ResearchSourceResolutionSignalQuorumDriftRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionSignalQuorumDriftRow:
            raise ValueError(
                "row must be exactly ResearchSourceResolutionSignalQuorumDriftRow",
            )
        object.__setattr__(
            self,
            "analyst_bucket",
            _require_public_bucket("analyst_bucket", self.analyst_bucket),
        )
        for field_name in (
            "authoritative_source_count",
            "supporting_source_count",
            "total_source_count",
            "corroborating_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        for field_name in (
            "contradiction_pressure_score",
            "extraction_confidence_score",
            "source_authority_mix_score",
            "freshness_score",
            "corroboration_breadth_score",
            "contradiction_support_score",
            "extraction_confidence_support_score",
            "quorum_signal_score",
            "quorum_drift_score",
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
class ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
            raise TypeError(
                "ResearchSourceResolutionSignalQuorumDriftReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceResolutionSignalQuorumDriftReasonCodeCount",
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
class ResearchSourceResolutionSignalQuorumDriftReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    block_signal_count: Decimal
    weak_authority_mix_count: Decimal
    freshness_lag_count: Decimal
    thin_corroboration_count: Decimal
    contradiction_pressure_count: Decimal
    low_extraction_confidence_count: Decimal
    lowest_quorum_signal_score: Decimal
    highest_quorum_drift_score: Decimal
    highest_freshness_lag_seconds: Decimal
    highest_contradiction_pressure_score: Decimal
    lowest_extraction_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceResolutionSignalQuorumDriftReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionSignalQuorumDriftReport:
            raise TypeError(
                "ResearchSourceResolutionSignalQuorumDriftReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionSignalQuorumDriftReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceResolutionSignalQuorumDriftReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "block_signal_count",
            "weak_authority_mix_count",
            "freshness_lag_count",
            "thin_corroboration_count",
            "contradiction_pressure_count",
            "low_extraction_confidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "highest_freshness_lag_seconds",
            _require_nonnegative_decimal(
                "highest_freshness_lag_seconds",
                self.highest_freshness_lag_seconds,
            ),
        )
        for field_name in (
            "lowest_quorum_signal_score",
            "highest_quorum_drift_score",
            "highest_contradiction_pressure_score",
            "lowest_extraction_confidence_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
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


def build_research_source_resolution_signal_quorum_drift_report(
    inputs: list[ResearchSourceResolutionSignalQuorumDriftInput]
    | tuple[ResearchSourceResolutionSignalQuorumDriftInput, ...],
    *,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionSignalQuorumDriftReport:
    if type(config) is not ResearchSourceResolutionSignalQuorumDriftConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionSignalQuorumDriftConfig",
        )
    config = _revalidate_config(config)
    rows = _quorum_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceResolutionSignalQuorumDriftReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        signal_count=_count(len(rows)),
        pass_signal_count=_status_count(rows, "pass"),
        watch_signal_count=_status_count(rows, "watch"),
        block_signal_count=_status_count(rows, "block"),
        weak_authority_mix_count=_reason_count(
            rows,
            (WEAK_AUTHORITY_MIX_WATCH_REASON, WEAK_AUTHORITY_MIX_BLOCK_REASON),
        ),
        freshness_lag_count=_reason_count(
            rows,
            (FRESHNESS_LAG_WATCH_REASON, FRESHNESS_LAG_BLOCK_REASON),
        ),
        thin_corroboration_count=_reason_count(
            rows,
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (
                CONTRADICTION_PRESSURE_WATCH_REASON,
                CONTRADICTION_PRESSURE_BLOCK_REASON,
            ),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        lowest_quorum_signal_score=min(
            (row.quorum_signal_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_quorum_drift_score=max(
            (row.quorum_drift_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_freshness_lag_seconds=max(
            (row.freshness_lag_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_extraction_confidence_score=min(
            (row.extraction_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_resolution_signal_quorum_drift_report_payload(
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> dict[str, Any]:
    revalidated_report = _revalidate_report(report)
    payload = _json_ready(revalidated_report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_or_raise(payload)
    return payload


def research_source_resolution_signal_quorum_drift_report_digest(
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> str:
    return _revalidate_report(report).derived_validation_digest


def validate_research_source_resolution_signal_quorum_drift_report_digest(
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> None:
    _revalidate_report(report)


def validate_research_source_resolution_signal_quorum_drift_public_payload(
    payload: object,
) -> None:
    _validate_public_payload_or_raise(payload)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceResolutionSignalQuorumDriftInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized: list[ResearchSourceResolutionSignalQuorumDriftInput] = []
    seen: set[str] = set()
    for raw_input in value:
        item = _revalidate_input(raw_input)
        if item.analyst_bucket in seen:
            raise ValueError("inputs must be unique by analyst_bucket")
        seen.add(item.analyst_bucket)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.analyst_bucket))


def _quorum_rows(
    inputs: tuple[ResearchSourceResolutionSignalQuorumDriftInput, ...],
    *,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...]:
    return tuple(
        sorted(
            (_quorum_row(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )


def _quorum_row(
    item: ResearchSourceResolutionSignalQuorumDriftInput,
    *,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> ResearchSourceResolutionSignalQuorumDriftRow:
    total_source_count = _quantize(
        item.authoritative_source_count + item.supporting_source_count,
    )
    source_authority_mix_score = _source_authority_mix_score(
        item,
        total_source_count,
        config=config,
    )
    freshness_score = _freshness_score(item.freshness_lag_seconds, config=config)
    corroboration_breadth_score = _bounded_ratio(
        item.corroborating_source_count,
        config.min_corroborating_source_count,
    )
    contradiction_support_score = _quantize(
        ONE - item.contradiction_pressure_score,
    )
    extraction_confidence_support_score = item.extraction_confidence_score
    quorum_signal_score = _quorum_signal_score(
        source_authority_mix_score=source_authority_mix_score,
        freshness_score=freshness_score,
        corroboration_breadth_score=corroboration_breadth_score,
        contradiction_support_score=contradiction_support_score,
        extraction_confidence_support_score=extraction_confidence_support_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        total_source_count=total_source_count,
        quorum_signal_score=quorum_signal_score,
        config=config,
    )
    return ResearchSourceResolutionSignalQuorumDriftRow(
        analyst_bucket=item.analyst_bucket,
        authoritative_source_count=item.authoritative_source_count,
        supporting_source_count=item.supporting_source_count,
        total_source_count=total_source_count,
        corroborating_source_count=item.corroborating_source_count,
        freshness_lag_seconds=item.freshness_lag_seconds,
        contradiction_pressure_score=item.contradiction_pressure_score,
        extraction_confidence_score=item.extraction_confidence_score,
        source_authority_mix_score=source_authority_mix_score,
        freshness_score=freshness_score,
        corroboration_breadth_score=corroboration_breadth_score,
        contradiction_support_score=contradiction_support_score,
        extraction_confidence_support_score=extraction_confidence_support_score,
        quorum_signal_score=quorum_signal_score,
        quorum_drift_score=_quantize(ONE - quorum_signal_score),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchSourceResolutionSignalQuorumDriftInput,
    *,
    total_source_count: Decimal,
    quorum_signal_score: Decimal,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.authoritative_source_count < config.min_authoritative_source_count:
        reasons.append(WEAK_AUTHORITY_MIX_BLOCK_REASON)
    elif total_source_count < config.min_total_source_count:
        reasons.append(WEAK_AUTHORITY_MIX_WATCH_REASON)
    if item.freshness_lag_seconds >= config.freshness_block_lag_seconds:
        reasons.append(FRESHNESS_LAG_BLOCK_REASON)
    elif item.freshness_lag_seconds > config.freshness_watch_lag_seconds:
        reasons.append(FRESHNESS_LAG_WATCH_REASON)
    if item.corroborating_source_count == ZERO:
        reasons.append(THIN_CORROBORATION_BLOCK_REASON)
    elif item.corroborating_source_count < config.min_corroborating_source_count:
        reasons.append(THIN_CORROBORATION_WATCH_REASON)
    if item.contradiction_pressure_score >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif item.contradiction_pressure_score >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if (
        item.extraction_confidence_score
        < config.extraction_confidence_block_floor
    ):
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif (
        item.extraction_confidence_score
        < config.extraction_confidence_watch_floor
    ):
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if quorum_signal_score < config.watch_quorum_signal_score:
        reasons.append(LOW_SCORE_BLOCK_REASON)
    elif quorum_signal_score < config.pass_quorum_signal_score:
        reasons.append(LOW_SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _source_authority_mix_score(
    item: ResearchSourceResolutionSignalQuorumDriftInput,
    total_source_count: Decimal,
    *,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> Decimal:
    authoritative_ratio = _bounded_ratio(
        item.authoritative_source_count,
        config.min_authoritative_source_count,
    )
    total_ratio = _bounded_ratio(total_source_count, config.min_total_source_count)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((authoritative_ratio + total_ratio) / TWO)


def _freshness_score(
    freshness_lag_seconds: Decimal,
    *,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> Decimal:
    if freshness_lag_seconds <= config.freshness_watch_lag_seconds:
        return ONE
    if freshness_lag_seconds >= config.freshness_block_lag_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = (
            config.freshness_block_lag_seconds
            - config.freshness_watch_lag_seconds
        )
        lag_fraction = (
            freshness_lag_seconds - config.freshness_watch_lag_seconds
        ) / span
        return _quantize(ONE - lag_fraction)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(numerator / denominator, ONE))


def _quorum_signal_score(
    *,
    source_authority_mix_score: Decimal,
    freshness_score: Decimal,
    corroboration_breadth_score: Decimal,
    contradiction_support_score: Decimal,
    extraction_confidence_support_score: Decimal,
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            source_authority_mix_score * config.authority_mix_weight
            + freshness_score * config.freshness_weight
            + corroboration_breadth_score * config.corroboration_breadth_weight
            + contradiction_support_score * config.contradiction_pressure_weight
            + extraction_confidence_support_score
            * config.extraction_confidence_weight
        )
        return _quantize(min(score, ONE))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...],
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
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...],
) -> tuple[ResearchSourceResolutionSignalQuorumDriftReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceResolutionSignalQuorumDriftReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceResolutionSignalQuorumDriftReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(
    row: ResearchSourceResolutionSignalQuorumDriftRow,
) -> tuple[Decimal, str]:
    return (-row.quorum_drift_score, row.analyst_bucket)


def _status_count(
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason in row.reason_codes for reason in reasons)
        ),
    )


def _validate_config(
    config: ResearchSourceResolutionSignalQuorumDriftConfig,
) -> None:
    if config.min_authoritative_source_count > config.min_total_source_count:
        raise ValueError(
            "min_authoritative_source_count must not exceed min_total_source_count",
        )
    if config.freshness_watch_lag_seconds >= config.freshness_block_lag_seconds:
        raise ValueError(
            "freshness_watch_lag_seconds must be less than "
            "freshness_block_lag_seconds",
        )
    if config.contradiction_watch_pressure >= config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must be less than "
            "contradiction_block_pressure",
        )
    if (
        config.extraction_confidence_block_floor
        >= config.extraction_confidence_watch_floor
    ):
        raise ValueError(
            "extraction_confidence_block_floor must be less than "
            "extraction_confidence_watch_floor",
        )
    if config.pass_quorum_signal_score <= config.watch_quorum_signal_score:
        raise ValueError(
            "pass_quorum_signal_score must be greater than "
            "watch_quorum_signal_score",
        )
    weights = (
        config.authority_mix_weight,
        config.freshness_weight,
        config.corroboration_breadth_weight,
        config.contradiction_pressure_weight,
        config.extraction_confidence_weight,
    )
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = _quantize(sum(weights, ZERO))
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchSourceResolutionSignalQuorumDriftRow) -> None:
    expected_total = _quantize(
        row.authoritative_source_count + row.supporting_source_count,
    )
    if row.total_source_count != expected_total:
        raise ValueError("total_source_count must match source counts")
    if row.contradiction_support_score != _quantize(
        ONE - row.contradiction_pressure_score,
    ):
        raise ValueError(
            "contradiction_support_score must match contradiction_pressure_score",
        )
    if (
        row.extraction_confidence_support_score
        != row.extraction_confidence_score
    ):
        raise ValueError(
            "extraction_confidence_support_score must match "
            "extraction_confidence_score",
        )
    if row.quorum_drift_score != _quantize(ONE - row.quorum_signal_score):
        raise ValueError("quorum_drift_score must match quorum_signal_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use the clear reason")


def _validate_report(
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> None:
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    for status, field_name in (
        ("pass", "pass_signal_count"),
        ("watch", "watch_signal_count"),
        ("block", "block_signal_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "weak_authority_mix_count",
            (WEAK_AUTHORITY_MIX_WATCH_REASON, WEAK_AUTHORITY_MIX_BLOCK_REASON),
        ),
        (
            "freshness_lag_count",
            (FRESHNESS_LAG_WATCH_REASON, FRESHNESS_LAG_BLOCK_REASON),
        ),
        (
            "thin_corroboration_count",
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (
                CONTRADICTION_PRESSURE_WATCH_REASON,
                CONTRADICTION_PRESSURE_BLOCK_REASON,
            ),
        ),
        (
            "low_extraction_confidence_count",
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    expected_values = (
        (
            "lowest_quorum_signal_score",
            min(
                (row.quorum_signal_score for row in report.rows),
                default=ZERO,
            ).quantize(QUANT),
        ),
        (
            "highest_quorum_drift_score",
            max(
                (row.quorum_drift_score for row in report.rows),
                default=ZERO,
            ).quantize(QUANT),
        ),
        (
            "highest_freshness_lag_seconds",
            max(
                (row.freshness_lag_seconds for row in report.rows),
                default=ZERO,
            ).quantize(QUANT),
        ),
        (
            "highest_contradiction_pressure_score",
            max(
                (row.contradiction_pressure_score for row in report.rows),
                default=ZERO,
            ).quantize(QUANT),
        ),
        (
            "lowest_extraction_confidence_score",
            min(
                (row.extraction_confidence_score for row in report.rows),
                default=ZERO,
            ).quantize(QUANT),
        ),
    )
    for field_name, expected in expected_values:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic quorum drift sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceResolutionSignalQuorumDriftRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows: list[ResearchSourceResolutionSignalQuorumDriftRow] = []
    seen: set[str] = set()
    for raw_row in value:
        row = _revalidate_row(raw_row)
        if row.analyst_bucket in seen:
            raise ValueError("rows must be unique by analyst_bucket")
        seen.add(row.analyst_bucket)
        rows.append(row)
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic quorum drift sort")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceResolutionSignalQuorumDriftReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts: list[ResearchSourceResolutionSignalQuorumDriftReasonCodeCount] = []
    seen: set[str] = set()
    for raw_count in value:
        item = _revalidate_reason_code_count(raw_count)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
        counts.append(item)
    expected_order = tuple(reason for reason in REPORT_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return tuple(counts)


def _revalidate_config(
    value: object,
) -> ResearchSourceResolutionSignalQuorumDriftConfig:
    if type(value) is not ResearchSourceResolutionSignalQuorumDriftConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionSignalQuorumDriftConfig",
        )
    return ResearchSourceResolutionSignalQuorumDriftConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_input(
    value: object,
) -> ResearchSourceResolutionSignalQuorumDriftInput:
    if type(value) is not ResearchSourceResolutionSignalQuorumDriftInput:
        raise ValueError(
            "inputs must contain ResearchSourceResolutionSignalQuorumDriftInput",
        )
    return ResearchSourceResolutionSignalQuorumDriftInput(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_row(
    value: object,
) -> ResearchSourceResolutionSignalQuorumDriftRow:
    if type(value) is not ResearchSourceResolutionSignalQuorumDriftRow:
        raise ValueError(
            "rows must contain ResearchSourceResolutionSignalQuorumDriftRow",
        )
    return ResearchSourceResolutionSignalQuorumDriftRow(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_reason_code_count(
    value: object,
) -> ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
    if type(value) is not ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchSourceResolutionSignalQuorumDriftReasonCodeCount",
        )
    return ResearchSourceResolutionSignalQuorumDriftReasonCodeCount(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_report(
    value: object,
) -> ResearchSourceResolutionSignalQuorumDriftReport:
    if type(value) is not ResearchSourceResolutionSignalQuorumDriftReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionSignalQuorumDriftReport",
        )
    return ResearchSourceResolutionSignalQuorumDriftReport(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("derived Decimal must fit the decimal context") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_STATUSES
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


def _require_supported_config_version(value: object) -> None:
    _require_canonical_string("config_version", value)
    if (
        value
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_public_bucket(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    allowed_chars = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789._-"
    )
    if len(value) > 128 or any(char not in allowed_chars for char in value):
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


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> None:
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
    report: ResearchSourceResolutionSignalQuorumDriftReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    _require_public_payload_hard_flags(payload)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.as_tuple().exponent != -6:
            raise ValueError("JSON Decimal value must use six decimal places")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
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
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


def _require_public_payload_hard_flags(
    value: object,
    *,
    path: str = "public payload",
) -> None:
    if isinstance(value, dict):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{path}.{flag_name} must be True")
        for key, item in value.items():
            if isinstance(item, (dict, list, tuple)):
                _require_public_payload_hard_flags(
                    item,
                    path=f"{path}.{key}",
                )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list, tuple)):
                _require_public_payload_hard_flags(
                    item,
                    path=f"{path}[{index}]",
                )


def _validate_public_payload_or_raise(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _require_exact_keys(
        "public payload",
        payload,
        REPORT_PUBLIC_PAYLOAD_KEYS,
    )
    _require_public_payload_hard_flags(payload)
    _require_sha256(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )

    raw_rows = payload["rows"]
    if type(raw_rows) is not list:
        raise ValueError("public payload.rows must be a list")
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(raw_rows)
    )

    raw_counts = payload["reason_code_counts"]
    if type(raw_counts) is not list:
        raise ValueError("public payload.reason_code_counts must be a list")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item, index=index)
        for index, item in enumerate(raw_counts)
    )

    report = ResearchSourceResolutionSignalQuorumDriftReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        signal_count=_decimal_from_public_payload(
            "signal_count",
            payload["signal_count"],
        ),
        pass_signal_count=_decimal_from_public_payload(
            "pass_signal_count",
            payload["pass_signal_count"],
        ),
        watch_signal_count=_decimal_from_public_payload(
            "watch_signal_count",
            payload["watch_signal_count"],
        ),
        block_signal_count=_decimal_from_public_payload(
            "block_signal_count",
            payload["block_signal_count"],
        ),
        weak_authority_mix_count=_decimal_from_public_payload(
            "weak_authority_mix_count",
            payload["weak_authority_mix_count"],
        ),
        freshness_lag_count=_decimal_from_public_payload(
            "freshness_lag_count",
            payload["freshness_lag_count"],
        ),
        thin_corroboration_count=_decimal_from_public_payload(
            "thin_corroboration_count",
            payload["thin_corroboration_count"],
        ),
        contradiction_pressure_count=_decimal_from_public_payload(
            "contradiction_pressure_count",
            payload["contradiction_pressure_count"],
        ),
        low_extraction_confidence_count=_decimal_from_public_payload(
            "low_extraction_confidence_count",
            payload["low_extraction_confidence_count"],
        ),
        lowest_quorum_signal_score=_decimal_from_public_payload(
            "lowest_quorum_signal_score",
            payload["lowest_quorum_signal_score"],
        ),
        highest_quorum_drift_score=_decimal_from_public_payload(
            "highest_quorum_drift_score",
            payload["highest_quorum_drift_score"],
        ),
        highest_freshness_lag_seconds=_decimal_from_public_payload(
            "highest_freshness_lag_seconds",
            payload["highest_freshness_lag_seconds"],
        ),
        highest_contradiction_pressure_score=_decimal_from_public_payload(
            "highest_contradiction_pressure_score",
            payload["highest_contradiction_pressure_score"],
        ),
        lowest_extraction_confidence_score=_decimal_from_public_payload(
            "lowest_extraction_confidence_score",
            payload["lowest_extraction_confidence_score"],
        ),
        status=_string_from_public_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_string_from_public_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_flag_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_flag_from_public_payload(
            "report_only",
            payload["report_only"],
        ),
        readonly=_flag_from_public_payload("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("public payload must use canonical values and ordering")


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchSourceResolutionSignalQuorumDriftRow:
    path = f"public payload.rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{path} must be a JSON object")
    _require_exact_keys(path, value, ROW_PUBLIC_PAYLOAD_KEYS)
    return ResearchSourceResolutionSignalQuorumDriftRow(
        analyst_bucket=_string_from_public_payload(
            f"{path}.analyst_bucket",
            value["analyst_bucket"],
        ),
        authoritative_source_count=_decimal_from_public_payload(
            f"{path}.authoritative_source_count",
            value["authoritative_source_count"],
        ),
        supporting_source_count=_decimal_from_public_payload(
            f"{path}.supporting_source_count",
            value["supporting_source_count"],
        ),
        total_source_count=_decimal_from_public_payload(
            f"{path}.total_source_count",
            value["total_source_count"],
        ),
        corroborating_source_count=_decimal_from_public_payload(
            f"{path}.corroborating_source_count",
            value["corroborating_source_count"],
        ),
        freshness_lag_seconds=_decimal_from_public_payload(
            f"{path}.freshness_lag_seconds",
            value["freshness_lag_seconds"],
        ),
        contradiction_pressure_score=_decimal_from_public_payload(
            f"{path}.contradiction_pressure_score",
            value["contradiction_pressure_score"],
        ),
        extraction_confidence_score=_decimal_from_public_payload(
            f"{path}.extraction_confidence_score",
            value["extraction_confidence_score"],
        ),
        source_authority_mix_score=_decimal_from_public_payload(
            f"{path}.source_authority_mix_score",
            value["source_authority_mix_score"],
        ),
        freshness_score=_decimal_from_public_payload(
            f"{path}.freshness_score",
            value["freshness_score"],
        ),
        corroboration_breadth_score=_decimal_from_public_payload(
            f"{path}.corroboration_breadth_score",
            value["corroboration_breadth_score"],
        ),
        contradiction_support_score=_decimal_from_public_payload(
            f"{path}.contradiction_support_score",
            value["contradiction_support_score"],
        ),
        extraction_confidence_support_score=_decimal_from_public_payload(
            f"{path}.extraction_confidence_support_score",
            value["extraction_confidence_support_score"],
        ),
        quorum_signal_score=_decimal_from_public_payload(
            f"{path}.quorum_signal_score",
            value["quorum_signal_score"],
        ),
        quorum_drift_score=_decimal_from_public_payload(
            f"{path}.quorum_drift_score",
            value["quorum_drift_score"],
        ),
        status=_string_from_public_payload(f"{path}.status", value["status"]),
        reason_codes=_reason_codes_from_public_payload(
            f"{path}.reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_flag_from_public_payload(
            f"{path}.paper_only",
            value["paper_only"],
        ),
        report_only=_flag_from_public_payload(
            f"{path}.report_only",
            value["report_only"],
        ),
        readonly=_flag_from_public_payload(
            f"{path}.readonly",
            value["readonly"],
        ),
    )


def _reason_code_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchSourceResolutionSignalQuorumDriftReasonCodeCount:
    path = f"public payload.reason_code_counts[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{path} must be a JSON object")
    _require_exact_keys(path, value, REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS)
    return ResearchSourceResolutionSignalQuorumDriftReasonCodeCount(
        reason_code=_string_from_public_payload(
            f"{path}.reason_code",
            value["reason_code"],
        ),
        count=_decimal_from_public_payload(f"{path}.count", value["count"]),
        paper_only=_flag_from_public_payload(
            f"{path}.paper_only",
            value["paper_only"],
        ),
        report_only=_flag_from_public_payload(
            f"{path}.report_only",
            value["report_only"],
        ),
        readonly=_flag_from_public_payload(
            f"{path}.readonly",
            value["readonly"],
        ),
    )


def _require_exact_keys(
    path: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(value) != set(expected_keys):
        raise ValueError(f"{path} must contain exactly the supported fields")


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a six-decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a six-decimal string") from exc
    normalized = _require_decimal(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical six-decimal string")
    return normalized


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _string_from_public_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _flag_from_public_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, value, allowed)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_SIGNAL_QUORUM_DRIFT_STATUSES",
    "ResearchSourceResolutionSignalQuorumDriftConfig",
    "ResearchSourceResolutionSignalQuorumDriftInput",
    "ResearchSourceResolutionSignalQuorumDriftReasonCodeCount",
    "ResearchSourceResolutionSignalQuorumDriftReport",
    "ResearchSourceResolutionSignalQuorumDriftRow",
    "build_research_source_resolution_signal_quorum_drift_report",
    "research_source_resolution_signal_quorum_drift_report_digest",
    "research_source_resolution_signal_quorum_drift_report_payload",
    "validate_research_source_resolution_signal_quorum_drift_public_payload",
    "validate_research_source_resolution_signal_quorum_drift_report_digest",
)
