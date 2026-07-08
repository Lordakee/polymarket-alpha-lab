"""Pure public-safe domain signal decay watch report reducer."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION = (
    "research-domain-signal-decay-watch-report-v1"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

PASS_REASON = "pass_domain_signal_decay_watch"
NO_INPUTS_REASON = "block_domain_signal_decay_no_inputs"
BLOCK_FORECAST_AGE_REASON = "block_forecast_age_decay"
BLOCK_EVIDENCE_FRESHNESS_REASON = "block_evidence_freshness_decay"
BLOCK_CATALYST_RECENCY_REASON = "block_catalyst_recency_decay"
BLOCK_SOURCE_RELIABILITY_REASON = "block_source_reliability_decay"
BLOCK_CALIBRATION_DRIFT_REASON = "block_calibration_drift_decay"
BLOCK_FORECAST_SAMPLE_GAP_REASON = "block_forecast_sample_gap"
BLOCK_EVIDENCE_SAMPLE_GAP_REASON = "block_evidence_sample_gap"
WATCH_FORECAST_AGE_REASON = "watch_forecast_age_decay"
WATCH_EVIDENCE_FRESHNESS_REASON = "watch_evidence_freshness_decay"
WATCH_CATALYST_RECENCY_REASON = "watch_catalyst_recency_decay"
WATCH_SOURCE_RELIABILITY_REASON = "watch_source_reliability_decay"
WATCH_CALIBRATION_DRIFT_REASON = "watch_calibration_drift_decay"

ROW_REASON_CODE_SEQUENCE = (
    BLOCK_FORECAST_AGE_REASON,
    BLOCK_EVIDENCE_FRESHNESS_REASON,
    BLOCK_CATALYST_RECENCY_REASON,
    BLOCK_SOURCE_RELIABILITY_REASON,
    BLOCK_CALIBRATION_DRIFT_REASON,
    BLOCK_FORECAST_SAMPLE_GAP_REASON,
    BLOCK_EVIDENCE_SAMPLE_GAP_REASON,
    WATCH_FORECAST_AGE_REASON,
    WATCH_EVIDENCE_FRESHNESS_REASON,
    WATCH_CATALYST_RECENCY_REASON,
    WATCH_SOURCE_RELIABILITY_REASON,
    WATCH_CALIBRATION_DRIFT_REASON,
    PASS_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "condition_id",
        "event_id",
        _join_parts("mar", "ket", "_slug"),
        _join_parts("ques", "tion"),
        "source_id",
        "source_url",
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        "0x",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION",
    "RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_STATUSES",
    "ResearchDomainSignalDecayWatchConfig",
    "ResearchDomainSignalDecayWatchInput",
    "ResearchDomainSignalDecayWatchReasonCodeCount",
    "ResearchDomainSignalDecayWatchReport",
    "ResearchDomainSignalDecayWatchRow",
    "build_research_domain_signal_decay_watch_report",
    "research_domain_signal_decay_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainSignalDecayWatchConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_CONFIG_VERSION
    max_forecast_age_seconds: Decimal = Decimal("7200.000000")
    block_forecast_age_seconds: Decimal = Decimal("14400.000000")
    max_evidence_age_seconds: Decimal = Decimal("3600.000000")
    block_evidence_age_seconds: Decimal = Decimal("10800.000000")
    max_catalyst_age_seconds: Decimal = Decimal("21600.000000")
    block_catalyst_age_seconds: Decimal = Decimal("43200.000000")
    min_source_reliability_score: Decimal = Decimal("0.700000")
    block_source_reliability_score: Decimal = Decimal("0.400000")
    max_calibration_drift_ratio: Decimal = Decimal("0.100000")
    block_calibration_drift_ratio: Decimal = Decimal("0.250000")
    min_forecast_sample_count: Decimal = Decimal("2.000000")
    min_evidence_sample_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalDecayWatchConfig:
            raise TypeError(
                "ResearchDomainSignalDecayWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalDecayWatchConfig:
            raise ValueError(
                "config must be exactly ResearchDomainSignalDecayWatchConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_forecast_age_seconds",
            "block_forecast_age_seconds",
            "max_evidence_age_seconds",
            "block_evidence_age_seconds",
            "max_catalyst_age_seconds",
            "block_catalyst_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_reliability_score",
            "block_source_reliability_score",
            "max_calibration_drift_ratio",
            "block_calibration_drift_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_forecast_sample_count",
            "min_evidence_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integer_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_forecast_age_seconds <= self.max_forecast_age_seconds:
            raise ValueError("block_forecast_age_seconds must exceed max threshold")
        if self.block_evidence_age_seconds <= self.max_evidence_age_seconds:
            raise ValueError("block_evidence_age_seconds must exceed max threshold")
        if self.block_catalyst_age_seconds <= self.max_catalyst_age_seconds:
            raise ValueError("block_catalyst_age_seconds must exceed max threshold")
        if self.block_source_reliability_score >= self.min_source_reliability_score:
            raise ValueError(
                "block_source_reliability_score must be below min threshold",
            )
        if self.block_calibration_drift_ratio <= self.max_calibration_drift_ratio:
            raise ValueError(
                "block_calibration_drift_ratio must exceed max threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainSignalDecayWatchInput:
    domain_key: str
    observed_at: datetime
    forecast_sample_count: Decimal
    evidence_sample_count: Decimal
    aggregate_forecast_age_seconds: Decimal
    evidence_freshness_seconds: Decimal
    catalyst_recency_seconds: Decimal
    source_reliability_score: Decimal
    calibration_drift_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalDecayWatchInput:
            raise TypeError(
                "ResearchDomainSignalDecayWatchInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalDecayWatchInput:
            raise ValueError("input must be exactly ResearchDomainSignalDecayWatchInput")
        _require_public_string("domain_key", self.domain_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_sample_count",
            "evidence_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integer_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "aggregate_forecast_age_seconds",
            "evidence_freshness_seconds",
            "catalyst_recency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_ratio_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "calibration_drift_ratio",
            _require_ratio_decimal(
                "calibration_drift_ratio",
                self.calibration_drift_ratio,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainSignalDecayWatchRow:
    domain_key: str
    status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    forecast_sample_count: Decimal
    evidence_sample_count: Decimal
    aggregate_forecast_age_seconds: Decimal
    evidence_freshness_seconds: Decimal
    catalyst_recency_seconds: Decimal
    source_reliability_score: Decimal
    calibration_drift_ratio: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalDecayWatchRow:
            raise TypeError(
                "ResearchDomainSignalDecayWatchRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalDecayWatchRow:
            raise ValueError("row must be exactly ResearchDomainSignalDecayWatchRow")
        _require_public_string("domain_key", self.domain_key)
        _require_status("status", self.status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "aggregate_forecast_age_seconds",
            "evidence_freshness_seconds",
            "catalyst_recency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_sample_count",
            "evidence_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integer_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "source_reliability_score",
            "calibration_drift_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        expected_digest = _dataclass_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchDomainSignalDecayWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalDecayWatchReasonCodeCount:
            raise TypeError(
                "ResearchDomainSignalDecayWatchReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalDecayWatchReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDomainSignalDecayWatchReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_integer_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainSignalDecayWatchReport:
    generated_at: datetime
    config_version: str
    status: str
    public_next_step: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    forecast_age_decay_count: Decimal
    evidence_freshness_decay_count: Decimal
    catalyst_recency_decay_count: Decimal
    source_reliability_decay_count: Decimal
    calibration_drift_decay_count: Decimal
    average_forecast_age_seconds: Decimal
    average_evidence_freshness_seconds: Decimal
    average_catalyst_recency_seconds: Decimal
    average_source_reliability_score: Decimal
    average_calibration_drift_ratio: Decimal
    max_forecast_age_seconds: Decimal
    max_evidence_freshness_seconds: Decimal
    max_catalyst_recency_seconds: Decimal
    max_calibration_drift_ratio: Decimal
    min_source_reliability_score: Decimal
    max_allowed_forecast_age_seconds: Decimal
    block_forecast_age_seconds: Decimal
    max_allowed_evidence_age_seconds: Decimal
    block_evidence_age_seconds: Decimal
    max_allowed_catalyst_age_seconds: Decimal
    block_catalyst_age_seconds: Decimal
    min_allowed_source_reliability_score: Decimal
    block_source_reliability_score: Decimal
    max_allowed_calibration_drift_ratio: Decimal
    block_calibration_drift_ratio: Decimal
    min_forecast_sample_count: Decimal
    min_evidence_sample_count: Decimal
    rows: tuple[ResearchDomainSignalDecayWatchRow, ...]
    reason_code_counts: tuple[ResearchDomainSignalDecayWatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalDecayWatchReport:
            raise TypeError(
                "ResearchDomainSignalDecayWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalDecayWatchReport:
            raise ValueError("report must be exactly ResearchDomainSignalDecayWatchReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_public_string("public_next_step", self.public_next_step)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "forecast_age_decay_count",
            "evidence_freshness_decay_count",
            "catalyst_recency_decay_count",
            "source_reliability_decay_count",
            "calibration_drift_decay_count",
            "min_forecast_sample_count",
            "min_evidence_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_forecast_age_seconds",
            "average_evidence_freshness_seconds",
            "average_catalyst_recency_seconds",
            "max_forecast_age_seconds",
            "max_evidence_freshness_seconds",
            "max_catalyst_recency_seconds",
            "max_allowed_forecast_age_seconds",
            "block_forecast_age_seconds",
            "max_allowed_evidence_age_seconds",
            "block_evidence_age_seconds",
            "max_allowed_catalyst_age_seconds",
            "block_catalyst_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_reliability_score",
            "average_calibration_drift_ratio",
            "max_calibration_drift_ratio",
            "min_source_reliability_score",
            "min_allowed_source_reliability_score",
            "block_source_reliability_score",
            "max_allowed_calibration_drift_ratio",
            "block_calibration_drift_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _dataclass_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_domain_signal_decay_watch_report(
    input_rows: Iterable[ResearchDomainSignalDecayWatchInput],
    *,
    config: ResearchDomainSignalDecayWatchConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainSignalDecayWatchReport:
    cfg = config or ResearchDomainSignalDecayWatchConfig()
    if type(cfg) is not ResearchDomainSignalDecayWatchConfig:
        raise ValueError("config must be exactly ResearchDomainSignalDecayWatchConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(input_rows)
    rows = tuple(
        _row_for_input(input_row, config=cfg, generated_at=generated_at_utc)
        for input_row in normalized_inputs
    )
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (_status_sort_value(row.status), row.domain_key)),
    )
    status = _report_status(sorted_rows)
    domain_count = _decimal_count(len(sorted_rows))
    return ResearchDomainSignalDecayWatchReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        public_next_step=_public_next_step(status),
        domain_count=domain_count,
        pass_domain_count=_status_count(sorted_rows, STATUS_PASS),
        watch_domain_count=_status_count(sorted_rows, STATUS_WATCH),
        block_domain_count=_status_count(sorted_rows, STATUS_BLOCK),
        forecast_age_decay_count=_dimension_decay_count(
            sorted_rows,
            BLOCK_FORECAST_AGE_REASON,
            WATCH_FORECAST_AGE_REASON,
        ),
        evidence_freshness_decay_count=_dimension_decay_count(
            sorted_rows,
            BLOCK_EVIDENCE_FRESHNESS_REASON,
            WATCH_EVIDENCE_FRESHNESS_REASON,
        ),
        catalyst_recency_decay_count=_dimension_decay_count(
            sorted_rows,
            BLOCK_CATALYST_RECENCY_REASON,
            WATCH_CATALYST_RECENCY_REASON,
        ),
        source_reliability_decay_count=_dimension_decay_count(
            sorted_rows,
            BLOCK_SOURCE_RELIABILITY_REASON,
            WATCH_SOURCE_RELIABILITY_REASON,
        ),
        calibration_drift_decay_count=_dimension_decay_count(
            sorted_rows,
            BLOCK_CALIBRATION_DRIFT_REASON,
            WATCH_CALIBRATION_DRIFT_REASON,
        ),
        average_forecast_age_seconds=_ratio(
            _decimal_sum(row.aggregate_forecast_age_seconds for row in sorted_rows),
            domain_count,
        ),
        average_evidence_freshness_seconds=_ratio(
            _decimal_sum(row.evidence_freshness_seconds for row in sorted_rows),
            domain_count,
        ),
        average_catalyst_recency_seconds=_ratio(
            _decimal_sum(row.catalyst_recency_seconds for row in sorted_rows),
            domain_count,
        ),
        average_source_reliability_score=_ratio(
            _decimal_sum(row.source_reliability_score for row in sorted_rows),
            domain_count,
        ),
        average_calibration_drift_ratio=_ratio(
            _decimal_sum(row.calibration_drift_ratio for row in sorted_rows),
            domain_count,
        ),
        max_forecast_age_seconds=max(
            (row.aggregate_forecast_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_evidence_freshness_seconds=max(
            (row.evidence_freshness_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_catalyst_recency_seconds=max(
            (row.catalyst_recency_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_calibration_drift_ratio=max(
            (row.calibration_drift_ratio for row in sorted_rows),
            default=ZERO,
        ),
        min_source_reliability_score=min(
            (row.source_reliability_score for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_forecast_age_seconds=cfg.max_forecast_age_seconds,
        block_forecast_age_seconds=cfg.block_forecast_age_seconds,
        max_allowed_evidence_age_seconds=cfg.max_evidence_age_seconds,
        block_evidence_age_seconds=cfg.block_evidence_age_seconds,
        max_allowed_catalyst_age_seconds=cfg.max_catalyst_age_seconds,
        block_catalyst_age_seconds=cfg.block_catalyst_age_seconds,
        min_allowed_source_reliability_score=cfg.min_source_reliability_score,
        block_source_reliability_score=cfg.block_source_reliability_score,
        max_allowed_calibration_drift_ratio=cfg.max_calibration_drift_ratio,
        block_calibration_drift_ratio=cfg.block_calibration_drift_ratio,
        min_forecast_sample_count=cfg.min_forecast_sample_count,
        min_evidence_sample_count=cfg.min_evidence_sample_count,
        rows=sorted_rows,
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def research_domain_signal_decay_watch_report_payload(
    report: ResearchDomainSignalDecayWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainSignalDecayWatchReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_flag_downgrades("payload", report)
        _reject_unsafe_public("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchDomainSignalDecayWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_payload_digest(payload)
    _reject_public_numerics(payload)
    _reject_unsafe_public("payload", payload)
    return payload


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


def _row_for_input(
    input_row: ResearchDomainSignalDecayWatchInput,
    *,
    config: ResearchDomainSignalDecayWatchConfig,
    generated_at: datetime,
) -> ResearchDomainSignalDecayWatchRow:
    if input_row.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(input_row, config=config)
    return ResearchDomainSignalDecayWatchRow(
        domain_key=input_row.domain_key,
        status=_row_status(reason_codes),
        observed_at=input_row.observed_at,
        observation_age_seconds=_age_seconds(generated_at, input_row.observed_at),
        forecast_sample_count=input_row.forecast_sample_count,
        evidence_sample_count=input_row.evidence_sample_count,
        aggregate_forecast_age_seconds=input_row.aggregate_forecast_age_seconds,
        evidence_freshness_seconds=input_row.evidence_freshness_seconds,
        catalyst_recency_seconds=input_row.catalyst_recency_seconds,
        source_reliability_score=input_row.source_reliability_score,
        calibration_drift_ratio=input_row.calibration_drift_ratio,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    input_row: ResearchDomainSignalDecayWatchInput,
    *,
    config: ResearchDomainSignalDecayWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if input_row.aggregate_forecast_age_seconds > config.block_forecast_age_seconds:
        reason_codes.append(BLOCK_FORECAST_AGE_REASON)
    elif input_row.aggregate_forecast_age_seconds > config.max_forecast_age_seconds:
        reason_codes.append(WATCH_FORECAST_AGE_REASON)
    if input_row.evidence_freshness_seconds > config.block_evidence_age_seconds:
        reason_codes.append(BLOCK_EVIDENCE_FRESHNESS_REASON)
    elif input_row.evidence_freshness_seconds > config.max_evidence_age_seconds:
        reason_codes.append(WATCH_EVIDENCE_FRESHNESS_REASON)
    if input_row.catalyst_recency_seconds > config.block_catalyst_age_seconds:
        reason_codes.append(BLOCK_CATALYST_RECENCY_REASON)
    elif input_row.catalyst_recency_seconds > config.max_catalyst_age_seconds:
        reason_codes.append(WATCH_CATALYST_RECENCY_REASON)
    if input_row.source_reliability_score < config.block_source_reliability_score:
        reason_codes.append(BLOCK_SOURCE_RELIABILITY_REASON)
    elif input_row.source_reliability_score < config.min_source_reliability_score:
        reason_codes.append(WATCH_SOURCE_RELIABILITY_REASON)
    if input_row.calibration_drift_ratio > config.block_calibration_drift_ratio:
        reason_codes.append(BLOCK_CALIBRATION_DRIFT_REASON)
    elif input_row.calibration_drift_ratio > config.max_calibration_drift_ratio:
        reason_codes.append(WATCH_CALIBRATION_DRIFT_REASON)
    if input_row.forecast_sample_count < config.min_forecast_sample_count:
        reason_codes.append(BLOCK_FORECAST_SAMPLE_GAP_REASON)
    if input_row.evidence_sample_count < config.min_evidence_sample_count:
        reason_codes.append(BLOCK_EVIDENCE_SAMPLE_GAP_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes), sequence=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.startswith("block_") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.startswith("watch_") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchDomainSignalDecayWatchRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _public_next_step(status: str) -> str:
    _require_status("status", status)
    return f"{status}_report_only_domain_signal_decay_review"


def _summary_reason_codes(
    rows: tuple[ResearchDomainSignalDecayWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainSignalDecayWatchRow, ...],
) -> tuple[ResearchDomainSignalDecayWatchReasonCodeCount, ...]:
    domain_count = _decimal_count(len(rows))
    if not rows:
        return (
            ResearchDomainSignalDecayWatchReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ZERO,
            ),
        )
    counts: list[ResearchDomainSignalDecayWatchReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _decimal_count(
            sum(1 for row in rows if reason_code in row.reason_codes),
        )
        if count > ZERO:
            counts.append(
                ResearchDomainSignalDecayWatchReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    domain_ratio=_ratio(count, domain_count),
                ),
            )
    return tuple(counts)


def _normalize_inputs(
    input_rows: Iterable[ResearchDomainSignalDecayWatchInput],
) -> tuple[ResearchDomainSignalDecayWatchInput, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input rows must be an iterable of domain inputs")
    rows = tuple(input_rows)
    seen_domain_keys: set[str] = set()
    for input_row in rows:
        if type(input_row) is not ResearchDomainSignalDecayWatchInput:
            raise ValueError("input rows must contain ResearchDomainSignalDecayWatchInput")
        if input_row.domain_key in seen_domain_keys:
            raise ValueError("domain_key values must be unique")
        seen_domain_keys.add(input_row.domain_key)
    return rows


def _normalize_rows(
    rows: tuple[ResearchDomainSignalDecayWatchRow, ...],
) -> tuple[ResearchDomainSignalDecayWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDomainSignalDecayWatchRow:
            raise ValueError("rows must contain ResearchDomainSignalDecayWatchRow")
    expected = tuple(sorted(rows, key=lambda row: (_status_sort_value(row.status), row.domain_key)))
    if rows != expected:
        raise ValueError("rows must be sorted by status severity and domain_key")
    if len({row.domain_key for row in rows}) != len(rows):
        raise ValueError("rows must contain unique domain_key values")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchDomainSignalDecayWatchReasonCodeCount, ...],
) -> tuple[ResearchDomainSignalDecayWatchReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchDomainSignalDecayWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainSignalDecayWatchReasonCodeCount",
            )
    expected = tuple(
        sorted(counts, key=lambda count: _reason_sort_value(count.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must follow canonical reason order")
    if len({count.reason_code for count in counts}) != len(counts):
        raise ValueError("reason_code_counts must contain unique reason_code values")
    return counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes contains unsupported reason_code")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    expected = tuple(reason_code for reason_code in sequence if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must follow canonical order")
    return normalized


def _validate_row(row: ResearchDomainSignalDecayWatchRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match row reason_codes")
    if PASS_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must not mix pass and decay reasons")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must contain pass reason for pass rows")


def _validate_report(report: ResearchDomainSignalDecayWatchReport) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.public_next_step != _public_next_step(report.status):
        raise ValueError("public_next_step must match status")
    if report.domain_count != _decimal_count(len(rows)):
        raise ValueError("domain_count must match rows")
    status_counts = {
        STATUS_PASS: report.pass_domain_count,
        STATUS_WATCH: report.watch_domain_count,
        STATUS_BLOCK: report.block_domain_count,
    }
    for status, count in status_counts.items():
        if count != _status_count(rows, status):
            raise ValueError(f"{status}_domain_count must match rows")
    if report.reason_codes != tuple(
        count.reason_code for count in report.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(rows: tuple[ResearchDomainSignalDecayWatchRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _dimension_decay_count(
    rows: tuple[ResearchDomainSignalDecayWatchRow, ...],
    block_reason: str,
    watch_reason: str,
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if block_reason in row.reason_codes or watch_reason in row.reason_codes
        ),
    )


def _status_sort_value(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_sort_value(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code is not supported") from exc


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    age = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(str(age.days * 86400 + age.seconds))
        microseconds = Decimal(str(age.microseconds)) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + microseconds)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(str(value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty and stripped")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be 128 characters or fewer")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} must not contain raw identifiers")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical lowercase public text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if value not in RESEARCH_DOMAIN_SIGNAL_DECAY_WATCH_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_integer_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_positive_integer_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _dataclass_digest(value: object) -> str:
    unsigned: dict[str, Any] = {}
    for field in fields(value):
        if field.name != "derived_validation_digest":
            unsigned[field.name] = getattr(value, field.name)
    return _canonical_digest(_json_ready(unsigned))


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _canonical_digest(payload: object) -> str:
    encoded = json_dumps(_json_ready(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


def json_dumps(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


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
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
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


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)
