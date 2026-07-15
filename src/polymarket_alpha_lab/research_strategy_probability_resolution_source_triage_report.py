"""Pure report-only probability resolution-source triage risk reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-resolution-source-triage-report-v0"
)
RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "probability_resolution_source_triage_no_inputs"
PASS_REASON = "probability_resolution_source_triage_pass"
FORECAST_CONFIDENCE_BLOCK_REASON = "forecast_confidence_block"
SOURCE_FRESHNESS_BLOCK_REASON = "source_freshness_block"
AUTHORITY_COVERAGE_BLOCK_REASON = "authority_coverage_block"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
RESOLUTION_CLOCK_BLOCK_REASON = "resolution_clock_proximity_block"
TRIAGE_RISK_BLOCK_REASON = "triage_risk_score_block"
FORECAST_CONFIDENCE_WATCH_REASON = "forecast_confidence_watch"
SOURCE_FRESHNESS_WATCH_REASON = "source_freshness_watch"
AUTHORITY_COVERAGE_WATCH_REASON = "authority_coverage_watch"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
RESOLUTION_CLOCK_WATCH_REASON = "resolution_clock_proximity_watch"
TRIAGE_RISK_WATCH_REASON = "triage_risk_score_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    FORECAST_CONFIDENCE_BLOCK_REASON,
    SOURCE_FRESHNESS_BLOCK_REASON,
    AUTHORITY_COVERAGE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    RESOLUTION_CLOCK_BLOCK_REASON,
    TRIAGE_RISK_BLOCK_REASON,
    FORECAST_CONFIDENCE_WATCH_REASON,
    SOURCE_FRESHNESS_WATCH_REASON,
    AUTHORITY_COVERAGE_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    RESOLUTION_CLOCK_WATCH_REASON,
    TRIAGE_RISK_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    (
        FORECAST_CONFIDENCE_BLOCK_REASON,
        SOURCE_FRESHNESS_BLOCK_REASON,
        AUTHORITY_COVERAGE_BLOCK_REASON,
        CONTRADICTION_PRESSURE_BLOCK_REASON,
        RESOLUTION_CLOCK_BLOCK_REASON,
        TRIAGE_RISK_BLOCK_REASON,
    ),
)

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
CANONICAL_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "wallet",
    "authentication",
    "authorization",
    "auth_token",
    "credential",
    "secret",
    "token",
    "order",
    "trade",
    "execution",
    "recommend",
    "sizing",
    "notional",
    "stake",
    "database",
    "dsn",
    "table",
    "file_path",
    "persist",
    "network",
    "http://",
    "https://",
    "www.",
    "buy",
    "sell",
    "live trading",
)
HARD_FLAG_FIELD_NAMES = ("paper_only", "report_only", "readonly")

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_STATUSES",
    "ResearchStrategyProbabilityResolutionSourceTriageConfig",
    "ResearchStrategyProbabilityResolutionSourceTriageInput",
    "ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount",
    "ResearchStrategyProbabilityResolutionSourceTriageReport",
    "ResearchStrategyProbabilityResolutionSourceTriageRow",
    "build_research_strategy_probability_resolution_source_triage_report",
    "research_strategy_probability_resolution_source_triage_report_digest",
    "research_strategy_probability_resolution_source_triage_report_payload",
    "validate_research_strategy_probability_resolution_source_triage_public_payload",
    "validate_research_strategy_probability_resolution_source_triage_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityResolutionSourceTriageConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_REPORT_CONFIG_VERSION
    )
    forecast_confidence_watch_threshold: Decimal = Decimal("0.700000")
    forecast_confidence_block_threshold: Decimal = Decimal("0.400000")
    fresh_source_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    authority_coverage_watch_threshold: Decimal = Decimal("0.750000")
    authority_coverage_block_threshold: Decimal = Decimal("0.400000")
    contradiction_watch_pressure: Decimal = Decimal("0.250000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    resolution_clock_watch_seconds: Decimal = Decimal("21600.000000")
    resolution_clock_block_seconds: Decimal = Decimal("1800.000000")
    triage_risk_watch_threshold: Decimal = Decimal("0.250000")
    triage_risk_block_threshold: Decimal = Decimal("0.650000")
    forecast_confidence_weight: Decimal = Decimal("0.200000")
    source_freshness_weight: Decimal = Decimal("0.200000")
    authority_coverage_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    resolution_clock_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityResolutionSourceTriageConfig:
            raise TypeError(
                "ResearchStrategyProbabilityResolutionSourceTriageConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategyProbabilityResolutionSourceTriageConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        ratio_fields = (
            "forecast_confidence_watch_threshold",
            "forecast_confidence_block_threshold",
            "authority_coverage_watch_threshold",
            "authority_coverage_block_threshold",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "triage_risk_watch_threshold",
            "triage_risk_block_threshold",
            "forecast_confidence_weight",
            "source_freshness_weight",
            "authority_coverage_weight",
            "contradiction_pressure_weight",
            "resolution_clock_weight",
        )
        for field_name in ratio_fields:
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "resolution_clock_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_clock_block_seconds",
            _require_nonnegative_decimal(
                "resolution_clock_block_seconds",
                self.resolution_clock_block_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityResolutionSourceTriageInput:
    forecast_digest: str
    forecast_confidence: Decimal
    source_age_seconds: Decimal
    authority_coverage: Decimal
    contradiction_pressure: Decimal
    seconds_until_resolution: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityResolutionSourceTriageInput:
            raise TypeError(
                "ResearchStrategyProbabilityResolutionSourceTriageInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchStrategyProbabilityResolutionSourceTriageInput,
        )
        _require_sha256_digest("forecast_digest", self.forecast_digest)
        for field_name in (
            "forecast_confidence",
            "authority_coverage",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_age_seconds", "seconds_until_resolution"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityResolutionSourceTriageRow:
    rank: Decimal
    forecast_digest: str
    forecast_confidence: Decimal
    source_age_seconds: Decimal
    authority_coverage: Decimal
    contradiction_pressure: Decimal
    seconds_until_resolution: Decimal
    forecast_confidence_risk: Decimal
    source_freshness_risk: Decimal
    authority_coverage_risk: Decimal
    contradiction_pressure_risk: Decimal
    resolution_clock_risk: Decimal
    triage_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_config: InitVar[
        ResearchStrategyProbabilityResolutionSourceTriageConfig | None
    ] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityResolutionSourceTriageRow:
            raise TypeError(
                "ResearchStrategyProbabilityResolutionSourceTriageRow "
                "does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchStrategyProbabilityResolutionSourceTriageConfig
        | None,
    ) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchStrategyProbabilityResolutionSourceTriageRow,
        )
        object.__setattr__(
            self,
            "rank",
            _require_positive_whole_decimal("rank", self.rank),
        )
        _require_sha256_digest("forecast_digest", self.forecast_digest)
        for field_name in (
            "forecast_confidence",
            "authority_coverage",
            "contradiction_pressure",
            "forecast_confidence_risk",
            "source_freshness_risk",
            "authority_coverage_risk",
            "contradiction_pressure_risk",
            "resolution_clock_risk",
            "triage_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_age_seconds", "seconds_until_resolution"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(
            self,
            config=_row_validation_config(validation_config),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount:
            raise TypeError(
                "ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityResolutionSourceTriageReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig
    status: str
    forecast_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_triage_risk_score: Decimal
    highest_triage_risk_score: Decimal
    rows: tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyProbabilityResolutionSourceTriageReport:
            raise TypeError(
                "ResearchStrategyProbabilityResolutionSourceTriageReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategyProbabilityResolutionSourceTriageReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if type(self.config) is not ResearchStrategyProbabilityResolutionSourceTriageConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyProbabilityResolutionSourceTriageConfig",
            )
        object.__setattr__(self, "config", _rebuild_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for field_name in (
            "forecast_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_triage_risk_score",
            "highest_triage_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rows",
            _normalize_rows(self.rows, config=self.config),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                expected_digest,
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest must match report fields",
                )

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_probability_resolution_source_triage_report_payload(
            self,
        )


def build_research_strategy_probability_resolution_source_triage_report(
    inputs: Sequence[ResearchStrategyProbabilityResolutionSourceTriageInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig | None = None,
) -> ResearchStrategyProbabilityResolutionSourceTriageReport:
    """Build a deterministic report-only probability source-triage snapshot."""

    if config is None:
        config = ResearchStrategyProbabilityResolutionSourceTriageConfig()
    if type(config) is not ResearchStrategyProbabilityResolutionSourceTriageConfig:
        raise ValueError(
            "config must be exactly "
            "ResearchStrategyProbabilityResolutionSourceTriageConfig",
        )
    config = _rebuild_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    values = tuple(_row_values(item, config=config) for item in normalized_inputs)
    ranked_values = tuple(
        sorted(
            values,
            key=_row_value_order_key,
        ),
    )
    rows = tuple(
        ResearchStrategyProbabilityResolutionSourceTriageRow(
            rank=_count(index),
            validation_config=config,
            **value,
        )
        for index, value in enumerate(ranked_values, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyProbabilityResolutionSourceTriageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        status=_report_status(rows),
        forecast_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_triage_risk_score=_average(
            tuple(row.triage_risk_score for row in rows),
        ),
        highest_triage_risk_score=max(
            (row.triage_risk_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_strategy_probability_resolution_source_triage_report_payload(
    report: ResearchStrategyProbabilityResolutionSourceTriageReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityResolutionSourceTriageReport:
        raise ValueError(
            "report must be exactly "
            "ResearchStrategyProbabilityResolutionSourceTriageReport",
        )
    _rebuild_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if not validate_research_strategy_probability_resolution_source_triage_report_payload(
        payload,
    ):
        raise ValueError("report payload failed canonical validation")
    return payload


def research_strategy_probability_resolution_source_triage_report_digest(
    report: ResearchStrategyProbabilityResolutionSourceTriageReport,
) -> str:
    payload = research_strategy_probability_resolution_source_triage_report_payload(
        report,
    )
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_strategy_probability_resolution_source_triage_report_payload(
    payload: dict[str, Any],
) -> bool:
    try:
        normalized_report = _report_from_public_payload(payload)
        normalized_payload = _json_ready(normalized_report)
        if normalized_payload != payload:
            return False
        return (
            normalized_report.derived_validation_digest
            == _canonical_payload_digest(payload)
        )
    except (InvalidOperation, KeyError, TypeError, ValueError):
        return False


def validate_research_strategy_probability_resolution_source_triage_public_payload(
    payload: dict[str, Any],
) -> bool:
    return validate_research_strategy_probability_resolution_source_triage_report_payload(
        payload,
    )


def _row_values(
    item: ResearchStrategyProbabilityResolutionSourceTriageInput,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> dict[str, Any]:
    with localcontext(DECIMAL_CONTEXT):
        forecast_confidence_risk = _quantize(ONE - item.forecast_confidence)
        authority_coverage_risk = _quantize(ONE - item.authority_coverage)
    source_freshness_risk = _source_freshness_risk(
        item.source_age_seconds,
        config=config,
    )
    contradiction_pressure_risk = item.contradiction_pressure
    resolution_clock_risk = _resolution_clock_risk(
        item.seconds_until_resolution,
        config=config,
    )
    triage_risk_score = _triage_risk_score(
        forecast_confidence_risk=forecast_confidence_risk,
        source_freshness_risk=source_freshness_risk,
        authority_coverage_risk=authority_coverage_risk,
        contradiction_pressure_risk=contradiction_pressure_risk,
        resolution_clock_risk=resolution_clock_risk,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        triage_risk_score=triage_risk_score,
        config=config,
    )
    return {
        "forecast_digest": item.forecast_digest,
        "forecast_confidence": item.forecast_confidence,
        "source_age_seconds": item.source_age_seconds,
        "authority_coverage": item.authority_coverage,
        "contradiction_pressure": item.contradiction_pressure,
        "seconds_until_resolution": item.seconds_until_resolution,
        "forecast_confidence_risk": forecast_confidence_risk,
        "source_freshness_risk": source_freshness_risk,
        "authority_coverage_risk": authority_coverage_risk,
        "contradiction_pressure_risk": contradiction_pressure_risk,
        "resolution_clock_risk": resolution_clock_risk,
        "triage_risk_score": triage_risk_score,
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_freshness_risk(
    source_age_seconds: Decimal,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> Decimal:
    if source_age_seconds <= config.fresh_source_age_seconds:
        return ZERO
    if source_age_seconds >= config.stale_source_age_seconds:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (source_age_seconds - config.fresh_source_age_seconds)
            / (config.stale_source_age_seconds - config.fresh_source_age_seconds),
        )


def _resolution_clock_risk(
    seconds_until_resolution: Decimal,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> Decimal:
    if seconds_until_resolution >= config.resolution_clock_watch_seconds:
        return ZERO
    if seconds_until_resolution <= config.resolution_clock_block_seconds:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                config.resolution_clock_watch_seconds
                - seconds_until_resolution
            )
            / (
                config.resolution_clock_watch_seconds
                - config.resolution_clock_block_seconds
            ),
        )


def _triage_risk_score(
    *,
    forecast_confidence_risk: Decimal,
    source_freshness_risk: Decimal,
    authority_coverage_risk: Decimal,
    contradiction_pressure_risk: Decimal,
    resolution_clock_risk: Decimal,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            forecast_confidence_risk * config.forecast_confidence_weight
            + source_freshness_risk * config.source_freshness_weight
            + authority_coverage_risk * config.authority_coverage_weight
            + contradiction_pressure_risk * config.contradiction_pressure_weight
            + resolution_clock_risk * config.resolution_clock_weight,
        )


def _row_reason_codes(
    item: ResearchStrategyProbabilityResolutionSourceTriageInput,
    *,
    triage_risk_score: Decimal,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.forecast_confidence <= config.forecast_confidence_block_threshold:
        reasons.append(FORECAST_CONFIDENCE_BLOCK_REASON)
    elif item.forecast_confidence < config.forecast_confidence_watch_threshold:
        reasons.append(FORECAST_CONFIDENCE_WATCH_REASON)
    if item.source_age_seconds >= config.stale_source_age_seconds:
        reasons.append(SOURCE_FRESHNESS_BLOCK_REASON)
    elif item.source_age_seconds > config.fresh_source_age_seconds:
        reasons.append(SOURCE_FRESHNESS_WATCH_REASON)
    if item.authority_coverage <= config.authority_coverage_block_threshold:
        reasons.append(AUTHORITY_COVERAGE_BLOCK_REASON)
    elif item.authority_coverage < config.authority_coverage_watch_threshold:
        reasons.append(AUTHORITY_COVERAGE_WATCH_REASON)
    if item.contradiction_pressure >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif item.contradiction_pressure >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if item.seconds_until_resolution <= config.resolution_clock_block_seconds:
        reasons.append(RESOLUTION_CLOCK_BLOCK_REASON)
    elif item.seconds_until_resolution <= config.resolution_clock_watch_seconds:
        reasons.append(RESOLUTION_CLOCK_WATCH_REASON)
    if triage_risk_score >= config.triage_risk_block_threshold:
        reasons.append(TRIAGE_RISK_BLOCK_REASON)
    elif triage_risk_score >= config.triage_risk_watch_threshold:
        reasons.append(TRIAGE_RISK_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _row_status(reason_codes: Sequence[str]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if tuple(reason_codes) == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    return _normalize_reason_codes("reason_codes", reasons)


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount, ...]:
    counts = (
        Counter(reason_code for row in rows for reason_code in row.reason_codes)
        if rows
        else Counter(reason_codes)
    )
    return tuple(
        ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyProbabilityResolutionSourceTriageInput],
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchStrategyProbabilityResolutionSourceTriageInput] = []
    seen: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchStrategyProbabilityResolutionSourceTriageInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategyProbabilityResolutionSourceTriageInput",
            )
        rebuilt = _rebuild_input(item)
        if rebuilt.forecast_digest in seen:
            raise ValueError("forecast_digest values must be unique")
        seen.add(rebuilt.forecast_digest)
        normalized.append(rebuilt)
    return tuple(sorted(normalized, key=lambda item: item.forecast_digest))


def _normalize_rows(
    rows: Sequence[ResearchStrategyProbabilityResolutionSourceTriageRow],
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyProbabilityResolutionSourceTriageRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityResolutionSourceTriageRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategyProbabilityResolutionSourceTriageRow",
            )
        rebuilt = _rebuild_row(row, config=config)
        if rebuilt.forecast_digest in seen:
            raise ValueError("row forecast_digest values must be unique")
        seen.add(rebuilt.forecast_digest)
        normalized.append(rebuilt)
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: Sequence[
        ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount
    ],
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[
        ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount
    ] = []
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount",
            )
        rebuilt = _rebuild_reason_code_count(item)
        if rebuilt.reason_code in seen:
            raise ValueError("reason_code_counts must use unique reason codes")
        seen.add(rebuilt.reason_code)
        normalized.append(rebuilt)
    normalized_tuple = tuple(normalized)
    expected = tuple(
        sorted(
            normalized_tuple,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if normalized_tuple != expected:
        raise ValueError("reason_code_counts must use canonical reason order")
    return normalized_tuple


def _validate_config(
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> None:
    if (
        config.forecast_confidence_block_threshold
        > config.forecast_confidence_watch_threshold
    ):
        raise ValueError(
            "forecast_confidence_block_threshold must not exceed "
            "forecast_confidence_watch_threshold",
        )
    if config.fresh_source_age_seconds >= config.stale_source_age_seconds:
        raise ValueError(
            "fresh_source_age_seconds must be below stale_source_age_seconds",
        )
    if (
        config.authority_coverage_block_threshold
        > config.authority_coverage_watch_threshold
    ):
        raise ValueError(
            "authority_coverage_block_threshold must not exceed "
            "authority_coverage_watch_threshold",
        )
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed "
            "contradiction_block_pressure",
        )
    if (
        config.resolution_clock_block_seconds
        >= config.resolution_clock_watch_seconds
    ):
        raise ValueError(
            "resolution_clock_block_seconds must be below "
            "resolution_clock_watch_seconds",
        )
    if config.triage_risk_watch_threshold > config.triage_risk_block_threshold:
        raise ValueError(
            "triage_risk_watch_threshold must not exceed "
            "triage_risk_block_threshold",
        )
    with localcontext(DECIMAL_CONTEXT):
        weights = (
            config.forecast_confidence_weight
            + config.source_freshness_weight
            + config.authority_coverage_weight
            + config.contradiction_pressure_weight
            + config.resolution_clock_weight
        )
    if weights != ONE:
        raise ValueError("triage risk weights must sum to one")


def _validate_row(
    row: ResearchStrategyProbabilityResolutionSourceTriageRow,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_confidence_risk = _quantize(ONE - row.forecast_confidence)
        expected_authority_risk = _quantize(ONE - row.authority_coverage)
    if row.forecast_confidence_risk != expected_confidence_risk:
        raise ValueError("forecast_confidence_risk must match forecast_confidence")
    expected_freshness_risk = _source_freshness_risk(
        row.source_age_seconds,
        config=config,
    )
    if row.source_freshness_risk != expected_freshness_risk:
        raise ValueError("source_freshness_risk must match source_age_seconds")
    if row.authority_coverage_risk != expected_authority_risk:
        raise ValueError("authority_coverage_risk must match authority_coverage")
    if row.contradiction_pressure_risk != row.contradiction_pressure:
        raise ValueError(
            "contradiction_pressure_risk must match contradiction_pressure",
        )
    expected_clock_risk = _resolution_clock_risk(
        row.seconds_until_resolution,
        config=config,
    )
    if row.resolution_clock_risk != expected_clock_risk:
        raise ValueError(
            "resolution_clock_risk must match seconds_until_resolution",
        )
    expected_score = _triage_risk_score(
        forecast_confidence_risk=expected_confidence_risk,
        source_freshness_risk=expected_freshness_risk,
        authority_coverage_risk=expected_authority_risk,
        contradiction_pressure_risk=row.contradiction_pressure,
        resolution_clock_risk=expected_clock_risk,
        config=config,
    )
    if row.triage_risk_score != expected_score:
        raise ValueError("triage_risk_score must match row components")
    expected_reasons = _row_reason_codes(
        ResearchStrategyProbabilityResolutionSourceTriageInput(
            forecast_digest=row.forecast_digest,
            forecast_confidence=row.forecast_confidence,
            source_age_seconds=row.source_age_seconds,
            authority_coverage=row.authority_coverage,
            contradiction_pressure=row.contradiction_pressure,
            seconds_until_resolution=row.seconds_until_resolution,
        ),
        triage_risk_score=expected_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row components")
    expected_status = _row_status(expected_reasons)
    if row.status != expected_status:
        raise ValueError("status must match row components")


def _validate_report(
    report: ResearchStrategyProbabilityResolutionSourceTriageReport,
) -> None:
    config = report.config
    _validate_config(config)
    expected_rows = tuple(
        sorted(
            report.rows,
            key=_row_order_key,
        ),
    )
    if report.rows != expected_rows:
        raise ValueError("rows must use deterministic triage risk order")
    for index, row in enumerate(report.rows, start=1):
        _validate_row(row, config=config)
        if row.rank != _count(index):
            raise ValueError("row rank must match deterministic order")
    if report.forecast_count != _count(len(report.rows)):
        raise ValueError("forecast_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_average = _average(
        tuple(row.triage_risk_score for row in report.rows),
    )
    if report.average_triage_risk_score != expected_average:
        raise ValueError("average_triage_risk_score must match rows")
    expected_highest = max(
        (row.triage_risk_score for row in report.rows),
        default=ZERO,
    )
    if report.highest_triage_risk_score != expected_highest:
        raise ValueError("highest_triage_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        expected_reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _row_validation_config(
    value: ResearchStrategyProbabilityResolutionSourceTriageConfig | None,
) -> ResearchStrategyProbabilityResolutionSourceTriageConfig:
    if value is None:
        return ResearchStrategyProbabilityResolutionSourceTriageConfig()
    if type(value) is not ResearchStrategyProbabilityResolutionSourceTriageConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchStrategyProbabilityResolutionSourceTriageConfig",
        )
    return _rebuild_config(value)


def _status_count(
    rows: tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _count(len(values)))


def _row_value_order_key(value: Mapping[str, Any]) -> tuple[Decimal, str]:
    with localcontext(DECIMAL_CONTEXT):
        return (-value["triage_risk_score"], value["forecast_digest"])


def _row_order_key(
    row: ResearchStrategyProbabilityResolutionSourceTriageRow,
) -> tuple[Decimal, str]:
    with localcontext(DECIMAL_CONTEXT):
        return (-row.triage_risk_score, row.forecast_digest)


def _rebuild_report(
    report: ResearchStrategyProbabilityResolutionSourceTriageReport,
) -> None:
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    ResearchStrategyProbabilityResolutionSourceTriageReport(**values)


def _rebuild_config(
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> ResearchStrategyProbabilityResolutionSourceTriageConfig:
    values = {field.name: getattr(config, field.name) for field in fields(config)}
    return ResearchStrategyProbabilityResolutionSourceTriageConfig(**values)


def _rebuild_input(
    item: ResearchStrategyProbabilityResolutionSourceTriageInput,
) -> ResearchStrategyProbabilityResolutionSourceTriageInput:
    values = {field.name: getattr(item, field.name) for field in fields(item)}
    return ResearchStrategyProbabilityResolutionSourceTriageInput(**values)


def _rebuild_row(
    row: ResearchStrategyProbabilityResolutionSourceTriageRow,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> ResearchStrategyProbabilityResolutionSourceTriageRow:
    values = {field.name: getattr(row, field.name) for field in fields(row)}
    return ResearchStrategyProbabilityResolutionSourceTriageRow(
        validation_config=config,
        **values,
    )


def _rebuild_reason_code_count(
    item: ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount,
) -> ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount:
    values = {field.name: getattr(item, field.name) for field in fields(item)}
    return ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount(**values)


def _report_digest(
    report: ResearchStrategyProbabilityResolutionSourceTriageReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _canonical_payload_digest(payload)


def _canonical_payload_digest(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(unsigned)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_from_public_payload(
    value: object,
) -> ResearchStrategyProbabilityResolutionSourceTriageReport:
    payload = _require_exact_public_fields(
        "public payload",
        value,
        ResearchStrategyProbabilityResolutionSourceTriageReport,
    )
    _reject_public_numeric_scalars(payload)
    _reject_unsafe_public_payload(payload)
    config = _config_from_public_payload(payload["config"])
    rows = _rows_from_public_payload(payload["rows"], config=config)
    reason_code_counts = _reason_code_counts_from_public_payload(
        payload["reason_code_counts"],
    )
    return ResearchStrategyProbabilityResolutionSourceTriageReport(
        generated_at=_parse_public_datetime(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_parse_public_string(
            "config_version",
            payload["config_version"],
        ),
        config=config,
        status=_parse_public_string("status", payload["status"]),
        forecast_count=_parse_public_decimal(
            "forecast_count",
            payload["forecast_count"],
        ),
        pass_count=_parse_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_parse_public_decimal("watch_count", payload["watch_count"]),
        block_count=_parse_public_decimal("block_count", payload["block_count"]),
        average_triage_risk_score=_parse_public_decimal(
            "average_triage_risk_score",
            payload["average_triage_risk_score"],
        ),
        highest_triage_risk_score=_parse_public_decimal(
            "highest_triage_risk_score",
            payload["highest_triage_risk_score"],
        ),
        rows=rows,
        reason_codes=_parse_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=reason_code_counts,
        derived_validation_digest=_parse_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_parse_true_flag("paper_only", payload["paper_only"]),
        report_only=_parse_true_flag("report_only", payload["report_only"]),
        readonly=_parse_true_flag("readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyProbabilityResolutionSourceTriageConfig:
    payload = _require_exact_public_fields(
        "config",
        value,
        ResearchStrategyProbabilityResolutionSourceTriageConfig,
    )
    decimal_fields = (
        "forecast_confidence_watch_threshold",
        "forecast_confidence_block_threshold",
        "fresh_source_age_seconds",
        "stale_source_age_seconds",
        "authority_coverage_watch_threshold",
        "authority_coverage_block_threshold",
        "contradiction_watch_pressure",
        "contradiction_block_pressure",
        "resolution_clock_watch_seconds",
        "resolution_clock_block_seconds",
        "triage_risk_watch_threshold",
        "triage_risk_block_threshold",
        "forecast_confidence_weight",
        "source_freshness_weight",
        "authority_coverage_weight",
        "contradiction_pressure_weight",
        "resolution_clock_weight",
    )
    values: dict[str, Any] = {
        "config_version": _parse_public_string(
            "config.config_version",
            payload["config_version"],
        ),
        "paper_only": _parse_true_flag(
            "config.paper_only",
            payload["paper_only"],
        ),
        "report_only": _parse_true_flag(
            "config.report_only",
            payload["report_only"],
        ),
        "readonly": _parse_true_flag(
            "config.readonly",
            payload["readonly"],
        ),
    }
    for field_name in decimal_fields:
        values[field_name] = _parse_public_decimal(
            f"config.{field_name}",
            payload[field_name],
        )
    return ResearchStrategyProbabilityResolutionSourceTriageConfig(**values)


def _rows_from_public_payload(
    value: object,
    *,
    config: ResearchStrategyProbabilityResolutionSourceTriageConfig,
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[ResearchStrategyProbabilityResolutionSourceTriageRow] = []
    for item in value:
        payload = _require_exact_public_fields(
            "row",
            item,
            ResearchStrategyProbabilityResolutionSourceTriageRow,
        )
        rows.append(
            ResearchStrategyProbabilityResolutionSourceTriageRow(
                rank=_parse_public_decimal("row.rank", payload["rank"]),
                forecast_digest=_parse_public_digest(
                    "row.forecast_digest",
                    payload["forecast_digest"],
                ),
                forecast_confidence=_parse_public_decimal(
                    "row.forecast_confidence",
                    payload["forecast_confidence"],
                ),
                source_age_seconds=_parse_public_decimal(
                    "row.source_age_seconds",
                    payload["source_age_seconds"],
                ),
                authority_coverage=_parse_public_decimal(
                    "row.authority_coverage",
                    payload["authority_coverage"],
                ),
                contradiction_pressure=_parse_public_decimal(
                    "row.contradiction_pressure",
                    payload["contradiction_pressure"],
                ),
                seconds_until_resolution=_parse_public_decimal(
                    "row.seconds_until_resolution",
                    payload["seconds_until_resolution"],
                ),
                forecast_confidence_risk=_parse_public_decimal(
                    "row.forecast_confidence_risk",
                    payload["forecast_confidence_risk"],
                ),
                source_freshness_risk=_parse_public_decimal(
                    "row.source_freshness_risk",
                    payload["source_freshness_risk"],
                ),
                authority_coverage_risk=_parse_public_decimal(
                    "row.authority_coverage_risk",
                    payload["authority_coverage_risk"],
                ),
                contradiction_pressure_risk=_parse_public_decimal(
                    "row.contradiction_pressure_risk",
                    payload["contradiction_pressure_risk"],
                ),
                resolution_clock_risk=_parse_public_decimal(
                    "row.resolution_clock_risk",
                    payload["resolution_clock_risk"],
                ),
                triage_risk_score=_parse_public_decimal(
                    "row.triage_risk_score",
                    payload["triage_risk_score"],
                ),
                status=_parse_public_string("row.status", payload["status"]),
                reason_codes=_parse_public_reason_codes(
                    "row.reason_codes",
                    payload["reason_codes"],
                ),
                validation_config=config,
                paper_only=_parse_true_flag(
                    "row.paper_only",
                    payload["paper_only"],
                ),
                report_only=_parse_true_flag(
                    "row.report_only",
                    payload["report_only"],
                ),
                readonly=_parse_true_flag(
                    "row.readonly",
                    payload["readonly"],
                ),
            ),
        )
    return tuple(rows)


def _reason_code_counts_from_public_payload(
    value: object,
) -> tuple[ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    result: list[
        ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount
    ] = []
    for item in value:
        payload = _require_exact_public_fields(
            "reason_code_count",
            item,
            ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount,
        )
        result.append(
            ResearchStrategyProbabilityResolutionSourceTriageReasonCodeCount(
                reason_code=_parse_public_string(
                    "reason_code_count.reason_code",
                    payload["reason_code"],
                ),
                count=_parse_public_decimal(
                    "reason_code_count.count",
                    payload["count"],
                ),
                paper_only=_parse_true_flag(
                    "reason_code_count.paper_only",
                    payload["paper_only"],
                ),
                report_only=_parse_true_flag(
                    "reason_code_count.report_only",
                    payload["report_only"],
                ),
                readonly=_parse_true_flag(
                    "reason_code_count.readonly",
                    payload["readonly"],
                ),
            ),
        )
    return tuple(result)


def _require_exact_public_fields(
    label: str,
    value: object,
    dataclass_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if not is_dataclass(dataclass_type):
        raise ValueError("public schema type must be a dataclass")
    expected = tuple(field.name for field in fields(dataclass_type))
    actual = tuple(value)
    if actual != expected:
        raise ValueError(
            f"{label} fields must exactly match canonical schema order",
        )
    return value


def _parse_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not CANONICAL_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    normalized = _require_nonnegative_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _parse_public_datetime(field_name: str, value: object) -> datetime:
    string_value = _parse_public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(string_value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != string_value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _parse_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _parse_public_digest(field_name: str, value: object) -> str:
    string_value = _parse_public_string(field_name, value)
    _require_sha256_digest(field_name, string_value)
    return string_value


def _parse_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    normalized = _normalize_reason_codes(field_name, tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical reason order")
    return normalized


def _parse_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _reject_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_scalars(item)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw > Decimal(1):
        raise ValueError(f"{field_name} must be between 0 and 1")
    normalized = _require_nonnegative_decimal(field_name, value)
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= Decimal(0):
        raise ValueError(f"{field_name} must be positive")
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < Decimal(0):
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < Decimal(0):
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = raw == raw.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw)


def _require_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _contains_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_STATUSES
    ):
        raise ValueError(
            f"{field_name} must be one of "
            f"{RESEARCH_STRATEGY_PROBABILITY_RESOLUTION_SOURCE_TRIAGE_STATUSES}",
        )


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    field_name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    seen: set[str] = set()
    for value in values:
        _require_reason_code(field_name, value)
        seen.add(value)
    if not seen:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELD_NAMES:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(label: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _contains_unsafe_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _contains_unsafe_fragment(key):
                raise ValueError("public payload contains unsafe key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _contains_unsafe_fragment(value):
        raise ValueError("public payload contains unsafe value")
