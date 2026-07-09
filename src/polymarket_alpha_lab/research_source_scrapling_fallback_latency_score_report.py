"""Report-only Scrapling fallback latency score reducer.

Callers provide already-collected local fallback latency telemetry. This module
performs no database, network, wallet, auth, order, sizing, recommendation, or
live trading operations. It only reduces typed local inputs into a deterministic
public report with redacted row labels, Decimal-only numerics, and SHA-256
payload validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_LATENCY_SCORE_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-fallback-latency-score-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")

NO_INPUTS_REASON = "scrapling_fallback_latency_no_inputs"
PASS_REASON = "scrapling_fallback_latency_score_pass"
WATCH_REASON = "scrapling_fallback_latency_score_watch"
BLOCK_REASON = "scrapling_fallback_latency_score_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "fallback_latency_above_watch_threshold",
    "fallback_success_below_watch_threshold",
    "latency_improvement_below_watch_threshold",
    "fallback_latency_score_below_watch_threshold",
    "fallback_latency_above_pass_threshold",
    "fallback_success_below_pass_threshold",
    "latency_improvement_below_pass_threshold",
    "fallback_latency_score_below_pass_threshold",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in REASON_CODE_SEQUENCE
    if reason_code.endswith("_watch_threshold")
)

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw_text",
    "raw text",
    "url",
    "http://",
    "https://",
    "://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
    "auth",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_LATENCY_SCORE_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingFallbackLatencyScoreConfig",
    "ResearchSourceScraplingFallbackLatencyScoreInput",
    "ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount",
    "ResearchSourceScraplingFallbackLatencyScoreReport",
    "ResearchSourceScraplingFallbackLatencyScoreRow",
    "STATUSES",
    "build_research_source_scrapling_fallback_latency_score_report",
    "research_source_scrapling_fallback_latency_score_report_digest",
    "research_source_scrapling_fallback_latency_score_report_payload",
    "validate_research_source_scrapling_fallback_latency_score_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackLatencyScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_LATENCY_SCORE_REPORT_CONFIG_VERSION
    )
    max_fallback_latency_pass_seconds: Decimal = Decimal("60.000000")
    max_fallback_latency_watch_seconds: Decimal = Decimal("180.000000")
    min_fallback_success_pass_ratio: Decimal = Decimal("0.900000")
    min_fallback_success_watch_ratio: Decimal = Decimal("0.600000")
    min_latency_improvement_pass_ratio: Decimal = Decimal("0.500000")
    min_latency_improvement_watch_ratio: Decimal = Decimal("0.200000")
    min_fallback_latency_score_pass: Decimal = Decimal("0.800000")
    min_fallback_latency_score_watch: Decimal = Decimal("0.500000")
    fallback_latency_weight: Decimal = Decimal("0.400000")
    fallback_success_weight: Decimal = Decimal("0.350000")
    latency_improvement_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackLatencyScoreConfig:
            raise TypeError(
                "ResearchSourceScraplingFallbackLatencyScoreConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingFallbackLatencyScoreConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_LATENCY_SCORE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_fallback_latency_pass_seconds",
            "max_fallback_latency_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_fallback_latency_pass_seconds >= self.max_fallback_latency_watch_seconds:
            raise ValueError(
                "max_fallback_latency_pass_seconds must be below "
                "max_fallback_latency_watch_seconds",
            )
        for field_name in (
            "min_fallback_success_pass_ratio",
            "min_fallback_success_watch_ratio",
            "min_latency_improvement_pass_ratio",
            "min_latency_improvement_watch_ratio",
            "min_fallback_latency_score_pass",
            "min_fallback_latency_score_watch",
            "fallback_latency_weight",
            "fallback_success_weight",
            "latency_improvement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ordered_floor(
            "fallback success",
            self.min_fallback_success_watch_ratio,
            self.min_fallback_success_pass_ratio,
        )
        _require_ordered_floor(
            "latency improvement",
            self.min_latency_improvement_watch_ratio,
            self.min_latency_improvement_pass_ratio,
        )
        _require_ordered_floor(
            "fallback latency score",
            self.min_fallback_latency_score_watch,
            self.min_fallback_latency_score_pass,
        )
        weight_sum = _quantize(
            self.fallback_latency_weight
            + self.fallback_success_weight
            + self.latency_improvement_weight,
        )
        if weight_sum != ONE:
            raise ValueError("fallback latency score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackLatencyScoreInput:
    private_capture_ref: str
    observed_at: datetime
    scrapling_latency_seconds: Decimal
    fallback_latency_seconds: Decimal
    fallback_success_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackLatencyScoreInput:
            raise TypeError(
                "ResearchSourceScraplingFallbackLatencyScoreInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingFallbackLatencyScoreInput, "input")
        _require_private_string("private_capture_ref", self.private_capture_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scrapling_latency_seconds",
            _normalize_nonnegative_decimal(
                "scrapling_latency_seconds",
                self.scrapling_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "fallback_latency_seconds",
            _normalize_nonnegative_decimal(
                "fallback_latency_seconds",
                self.fallback_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "fallback_success_ratio",
            _normalize_probability("fallback_success_ratio", self.fallback_success_ratio),
        )
        if self.fallback_latency_seconds > self.scrapling_latency_seconds:
            raise ValueError(
                "fallback_latency_seconds must not exceed scrapling_latency_seconds",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackLatencyScoreRow:
    row_label: str
    observed_at: datetime
    scrapling_latency_seconds: Decimal
    fallback_latency_seconds: Decimal
    fallback_latency_quality_score: Decimal
    fallback_success_ratio: Decimal
    latency_improvement_ratio: Decimal
    fallback_latency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackLatencyScoreRow:
            raise TypeError(
                "ResearchSourceScraplingFallbackLatencyScoreRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingFallbackLatencyScoreRow, "row")
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("scrapling_latency_seconds", "fallback_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fallback_latency_quality_score",
            "fallback_success_ratio",
            "latency_improvement_ratio",
            "fallback_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("row status must match reason_codes")
        if self.fallback_latency_seconds > self.scrapling_latency_seconds:
            raise ValueError(
                "fallback_latency_seconds must not exceed scrapling_latency_seconds",
            )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFallbackLatencyScoreReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_scrapling_latency_seconds: Decimal
    max_fallback_latency_seconds: Decimal
    average_fallback_latency_seconds: Decimal
    average_fallback_latency_quality_score: Decimal
    average_fallback_success_ratio: Decimal
    average_latency_improvement_ratio: Decimal
    average_fallback_latency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFallbackLatencyScoreReport:
            raise TypeError(
                "ResearchSourceScraplingFallbackLatencyScoreReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingFallbackLatencyScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FALLBACK_LATENCY_SCORE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_scrapling_latency_seconds",
            "max_fallback_latency_seconds",
            "average_fallback_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_fallback_latency_quality_score",
            "average_fallback_success_ratio",
            "average_latency_improvement_ratio",
            "average_fallback_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_payload(
            _json_ready(_report_values_without_digest(self)),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_fallback_latency_score_report_payload(self)


def build_research_source_scrapling_fallback_latency_score_report(
    inputs: Iterable[ResearchSourceScraplingFallbackLatencyScoreInput],
    *,
    config: ResearchSourceScraplingFallbackLatencyScoreConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceScraplingFallbackLatencyScoreReport:
    cfg = (
        ResearchSourceScraplingFallbackLatencyScoreConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = tuple(
        _row_from_input(
            item=item,
            row_number=index,
            config=cfg,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)

    return ResearchSourceScraplingFallbackLatencyScoreReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        input_count=_decimal_from_int(len(normalized_inputs)),
        row_count=_decimal_from_int(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_scrapling_latency_seconds=max(
            (row.scrapling_latency_seconds for row in rows),
            default=ZERO,
        ),
        max_fallback_latency_seconds=max(
            (row.fallback_latency_seconds for row in rows),
            default=ZERO,
        ),
        average_fallback_latency_seconds=_average_decimal(
            (row.fallback_latency_seconds for row in rows),
        ),
        average_fallback_latency_quality_score=_average_probability(
            (row.fallback_latency_quality_score for row in rows),
        ),
        average_fallback_success_ratio=_average_probability(
            (row.fallback_success_ratio for row in rows),
        ),
        average_latency_improvement_ratio=_average_probability(
            (row.latency_improvement_ratio for row in rows),
        ),
        average_fallback_latency_score=_average_probability(
            (row.fallback_latency_score for row in rows),
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scrapling_fallback_latency_score_report_payload(
    value: ResearchSourceScraplingFallbackLatencyScoreReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingFallbackLatencyScoreReport:
        _require_hard_flags("report", value)
        _validate_report_digest(value)
        payload = _json_ready(asdict(value))
    elif isinstance(value, Mapping):
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingFallbackLatencyScoreReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def research_source_scrapling_fallback_latency_score_report_digest(
    report: ResearchSourceScraplingFallbackLatencyScoreReport,
) -> str:
    _require_exact_type(report, ResearchSourceScraplingFallbackLatencyScoreReport, "report")
    _require_hard_flags("report", report)
    return _report_digest_from_payload(_json_ready(_report_values_without_digest(report)))


def validate_research_source_scrapling_fallback_latency_score_report_payload(
    payload: Mapping[str, object],
) -> bool:
    try:
        research_source_scrapling_fallback_latency_score_report_payload(payload)
    except ValueError:
        return False
    return True


def _require_config(
    config: ResearchSourceScraplingFallbackLatencyScoreConfig,
) -> ResearchSourceScraplingFallbackLatencyScoreConfig:
    _require_exact_type(config, ResearchSourceScraplingFallbackLatencyScoreConfig, "config")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    return config


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraplingFallbackLatencyScoreInput],
) -> tuple[ResearchSourceScraplingFallbackLatencyScoreInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of fallback latency inputs")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of fallback latency inputs") from exc
    for item in normalized:
        _require_exact_type(item, ResearchSourceScraplingFallbackLatencyScoreInput, "input")
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraplingFallbackLatencyScoreInput,
) -> tuple[str, Decimal, Decimal, Decimal]:
    return (
        item.observed_at.isoformat(),
        item.scrapling_latency_seconds,
        item.fallback_latency_seconds,
        item.fallback_success_ratio,
    )


def _row_from_input(
    *,
    item: ResearchSourceScraplingFallbackLatencyScoreInput,
    row_number: int,
    config: ResearchSourceScraplingFallbackLatencyScoreConfig,
) -> ResearchSourceScraplingFallbackLatencyScoreRow:
    fallback_latency_quality_score = _fallback_latency_quality_score(
        item.fallback_latency_seconds,
        config,
    )
    latency_improvement_ratio = _latency_improvement_ratio(
        scrapling_latency_seconds=item.scrapling_latency_seconds,
        fallback_latency_seconds=item.fallback_latency_seconds,
    )
    fallback_latency_score = _fallback_latency_score(
        fallback_latency_quality_score=fallback_latency_quality_score,
        fallback_success_ratio=item.fallback_success_ratio,
        latency_improvement_ratio=latency_improvement_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        fallback_latency_seconds=item.fallback_latency_seconds,
        fallback_success_ratio=item.fallback_success_ratio,
        latency_improvement_ratio=latency_improvement_ratio,
        fallback_latency_score=fallback_latency_score,
        config=config,
    )
    return ResearchSourceScraplingFallbackLatencyScoreRow(
        row_label=f"redacted-scrapling-fallback-latency-{row_number:06d}",
        observed_at=item.observed_at,
        scrapling_latency_seconds=item.scrapling_latency_seconds,
        fallback_latency_seconds=item.fallback_latency_seconds,
        fallback_latency_quality_score=fallback_latency_quality_score,
        fallback_success_ratio=item.fallback_success_ratio,
        latency_improvement_ratio=latency_improvement_ratio,
        fallback_latency_score=fallback_latency_score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _fallback_latency_quality_score(
    fallback_latency_seconds: Decimal,
    config: ResearchSourceScraplingFallbackLatencyScoreConfig,
) -> Decimal:
    if fallback_latency_seconds <= config.max_fallback_latency_pass_seconds:
        return ONE
    if fallback_latency_seconds >= config.max_fallback_latency_watch_seconds:
        return ZERO
    watch_window = (
        config.max_fallback_latency_watch_seconds
        - config.max_fallback_latency_pass_seconds
    )
    watch_progress = _safe_ratio(
        fallback_latency_seconds - config.max_fallback_latency_pass_seconds,
        watch_window,
    )
    return _normalize_probability("fallback_latency_quality_score", ONE - watch_progress)


def _latency_improvement_ratio(
    *,
    scrapling_latency_seconds: Decimal,
    fallback_latency_seconds: Decimal,
) -> Decimal:
    if scrapling_latency_seconds == ZERO:
        return ZERO
    return _normalize_probability(
        "latency_improvement_ratio",
        max(
            ZERO,
            _safe_ratio(
                scrapling_latency_seconds - fallback_latency_seconds,
                scrapling_latency_seconds,
            ),
        ),
    )


def _fallback_latency_score(
    *,
    fallback_latency_quality_score: Decimal,
    fallback_success_ratio: Decimal,
    latency_improvement_ratio: Decimal,
    config: ResearchSourceScraplingFallbackLatencyScoreConfig,
) -> Decimal:
    return _normalize_probability(
        "fallback_latency_score",
        fallback_latency_quality_score * config.fallback_latency_weight
        + fallback_success_ratio * config.fallback_success_weight
        + latency_improvement_ratio * config.latency_improvement_weight,
    )


def _row_reason_codes(
    *,
    fallback_latency_seconds: Decimal,
    fallback_success_ratio: Decimal,
    latency_improvement_ratio: Decimal,
    fallback_latency_score: Decimal,
    config: ResearchSourceScraplingFallbackLatencyScoreConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if fallback_latency_seconds > config.max_fallback_latency_watch_seconds:
        block_reasons.append("fallback_latency_above_watch_threshold")
    if fallback_success_ratio < config.min_fallback_success_watch_ratio:
        block_reasons.append("fallback_success_below_watch_threshold")
    if latency_improvement_ratio < config.min_latency_improvement_watch_ratio:
        block_reasons.append("latency_improvement_below_watch_threshold")
    if fallback_latency_score < config.min_fallback_latency_score_watch:
        block_reasons.append("fallback_latency_score_below_watch_threshold")
    if block_reasons:
        return _normalize_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if fallback_latency_seconds > config.max_fallback_latency_pass_seconds:
        watch_reasons.append("fallback_latency_above_pass_threshold")
    if fallback_success_ratio < config.min_fallback_success_pass_ratio:
        watch_reasons.append("fallback_success_below_pass_threshold")
    if latency_improvement_ratio < config.min_latency_improvement_pass_ratio:
        watch_reasons.append("latency_improvement_below_pass_threshold")
    if fallback_latency_score < config.min_fallback_latency_score_pass:
        watch_reasons.append("fallback_latency_score_below_pass_threshold")
    return _normalize_reason_codes(tuple(watch_reasons))


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    detail_reasons: list[str] = []
    for row in rows:
        detail_reasons.extend(row.reason_codes)
    if detail_reasons:
        return _normalize_reason_codes(tuple(detail_reasons))
    return (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...],
) -> tuple[ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=Decimal("1.000000"),
            ),
        )
    report_reasons = _report_reason_codes(rows)
    counts = Counter(report_reasons)
    return tuple(
        ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingFallbackLatencyScoreReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must equal row_count")
    if report.row_count != _decimal_from_int(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("report status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("report reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.max_scrapling_latency_seconds != max(
        (row.scrapling_latency_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_scrapling_latency_seconds must match rows")
    if report.max_fallback_latency_seconds != max(
        (row.fallback_latency_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_fallback_latency_seconds must match rows")
    if report.average_fallback_latency_seconds != _average_decimal(
        (row.fallback_latency_seconds for row in report.rows),
    ):
        raise ValueError("average_fallback_latency_seconds must match rows")
    if report.average_fallback_latency_quality_score != _average_probability(
        (row.fallback_latency_quality_score for row in report.rows),
    ):
        raise ValueError("average_fallback_latency_quality_score must match rows")
    if report.average_fallback_success_ratio != _average_probability(
        (row.fallback_success_ratio for row in report.rows),
    ):
        raise ValueError("average_fallback_success_ratio must match rows")
    if report.average_latency_improvement_ratio != _average_probability(
        (row.latency_improvement_ratio for row in report.rows),
    ):
        raise ValueError("average_latency_improvement_ratio must match rows")
    if report.average_fallback_latency_score != _average_probability(
        (row.fallback_latency_score for row in report.rows),
    ):
        raise ValueError("average_fallback_latency_score must match rows")


def _status_count(
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / _decimal_from_int(len(normalized)))


def _average_probability(values: Iterable[Decimal]) -> Decimal:
    return _normalize_probability("average", _average_decimal(values))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_from_int(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return _quantize(decimal_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return _quantize(decimal_value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize(decimal_value)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_ordered_floor(
    label: str,
    watch_value: Decimal,
    pass_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must be <= 2048 characters")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not supported")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _normalize_reason_code("reason_code", reason_code)
    ordered = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in frozenset(normalized)
    )
    if len(ordered) != len(frozenset(normalized)):
        raise ValueError("reason_codes must not contain duplicates")
    return ordered


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount, ...],
) -> tuple[ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes, dict)):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    for item in normalized:
        _require_exact_type(
            item,
            ResearchSourceScraplingFallbackLatencyScoreReasonCodeCount,
            "reason_code_count",
        )
    return tuple(sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)))


def _normalize_rows(
    rows: tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...],
) -> tuple[ResearchSourceScraplingFallbackLatencyScoreRow, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for item in normalized:
        _require_exact_type(item, ResearchSourceScraplingFallbackLatencyScoreRow, "row")
        _require_hard_flags("row", item)
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass/watch/block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name == "derived_validation_digest" and item == "":
                continue
            _reject_unsafe_public_string(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", item)
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain dict values")
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.key", key, allow_json_containers=True)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain list values")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.casefold()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe public fragment")


def _report_values_without_digest(
    report: ResearchSourceScraplingFallbackLatencyScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_payload(payload_without_digest: object) -> str:
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _validate_report_digest(
    report: ResearchSourceScraplingFallbackLatencyScoreReport,
) -> None:
    expected_digest = _report_digest_from_payload(
        _json_ready(_report_values_without_digest(report)),
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if _report_digest_from_payload(unsigned) != digest:
        raise ValueError("derived_validation_digest must match payload")


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, Any]:
    try:
        copied = json.loads(json.dumps(value, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must be JSON serializable") from exc
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied
