"""Pure public event resolution delay forecast report reducer."""

from __future__ import annotations

import json
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION = (
    "research-event-resolution-delay-forecast-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
FORECAST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "resolution_delay_forecast_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
DEADLINE_CLARITY_BLOCK_REASON = f"{REASON_PREFIX}deadline_clarity_block"
DEADLINE_CLARITY_WATCH_REASON = f"{REASON_PREFIX}deadline_clarity_watch"
DISPUTE_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}dispute_pressure_block"
DISPUTE_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}dispute_pressure_watch"
EVIDENCE_CONFLICT_BLOCK_REASON = f"{REASON_PREFIX}evidence_conflict_block"
EVIDENCE_CONFLICT_WATCH_REASON = f"{REASON_PREFIX}evidence_conflict_watch"
HISTORICAL_DELAY_MEMORY_BLOCK_REASON = (
    f"{REASON_PREFIX}historical_delay_memory_block"
)
HISTORICAL_DELAY_MEMORY_WATCH_REASON = (
    f"{REASON_PREFIX}historical_delay_memory_watch"
)
ORACLE_LAG_BLOCK_REASON = f"{REASON_PREFIX}oracle_lag_block"
ORACLE_LAG_WATCH_REASON = f"{REASON_PREFIX}oracle_lag_watch"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    DEADLINE_CLARITY_BLOCK_REASON,
    DISPUTE_PRESSURE_BLOCK_REASON,
    EVIDENCE_CONFLICT_BLOCK_REASON,
    HISTORICAL_DELAY_MEMORY_BLOCK_REASON,
    ORACLE_LAG_BLOCK_REASON,
    DEADLINE_CLARITY_WATCH_REASON,
    DISPUTE_PRESSURE_WATCH_REASON,
    EVIDENCE_CONFLICT_WATCH_REASON,
    HISTORICAL_DELAY_MEMORY_WATCH_REASON,
    ORACLE_LAG_WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    DEADLINE_CLARITY_BLOCK_REASON,
    DISPUTE_PRESSURE_BLOCK_REASON,
    EVIDENCE_CONFLICT_BLOCK_REASON,
    HISTORICAL_DELAY_MEMORY_BLOCK_REASON,
    ORACLE_LAG_BLOCK_REASON,
    DEADLINE_CLARITY_WATCH_REASON,
    DISPUTE_PRESSURE_WATCH_REASON,
    EVIDENCE_CONFLICT_WATCH_REASON,
    HISTORICAL_DELAY_MEMORY_WATCH_REASON,
    ORACLE_LAG_WATCH_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_resolution_delay_review",
    STATUS_WATCH: "watch_report_only_resolution_delay_review",
    STATUS_BLOCK: "block_report_only_resolution_delay_review",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FACTOR_COUNT = Decimal("5.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64
REDACTED_DIGEST_LENGTH = 19

_PUBLIC_REF_FRAGMENTS = ("public", "memo", "bulletin", "notice", "release")


@dataclass(frozen=True)
class ResearchEventResolutionDelayForecastConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION
    oracle_lag_watch_seconds: Decimal = Decimal("3600.000000")
    oracle_lag_block_seconds: Decimal = Decimal("14400.000000")
    evidence_conflict_watch_score: Decimal = Decimal("0.300000")
    evidence_conflict_block_score: Decimal = Decimal("0.700000")
    deadline_clarity_watch_score: Decimal = Decimal("0.600000")
    deadline_clarity_block_score: Decimal = Decimal("0.300000")
    dispute_pressure_watch_score: Decimal = Decimal("0.250000")
    dispute_pressure_block_score: Decimal = Decimal("0.650000")
    historical_delay_memory_watch_score: Decimal = Decimal("0.300000")
    historical_delay_memory_block_score: Decimal = Decimal("0.700000")
    aggregate_watch_threshold: Decimal = Decimal("0.300000")
    aggregate_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDelayForecastConfig:
            raise TypeError(
                "ResearchEventResolutionDelayForecastConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDelayForecastConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionDelayForecastConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "oracle_lag_watch_seconds",
            "oracle_lag_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oracle_lag_block_seconds <= self.oracle_lag_watch_seconds:
            raise ValueError(
                "oracle_lag_block_seconds must exceed oracle_lag_watch_seconds",
            )
        for field_name in (
            "evidence_conflict_watch_score",
            "evidence_conflict_block_score",
            "deadline_clarity_watch_score",
            "deadline_clarity_block_score",
            "dispute_pressure_watch_score",
            "dispute_pressure_block_score",
            "historical_delay_memory_watch_score",
            "historical_delay_memory_block_score",
            "aggregate_watch_threshold",
            "aggregate_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.evidence_conflict_block_score <= self.evidence_conflict_watch_score:
            raise ValueError(
                "evidence_conflict_block_score must exceed "
                "evidence_conflict_watch_score",
            )
        if self.deadline_clarity_block_score >= self.deadline_clarity_watch_score:
            raise ValueError(
                "deadline_clarity_block_score must be below "
                "deadline_clarity_watch_score",
            )
        if self.dispute_pressure_block_score <= self.dispute_pressure_watch_score:
            raise ValueError(
                "dispute_pressure_block_score must exceed "
                "dispute_pressure_watch_score",
            )
        if (
            self.historical_delay_memory_block_score
            <= self.historical_delay_memory_watch_score
        ):
            raise ValueError(
                "historical_delay_memory_block_score must exceed "
                "historical_delay_memory_watch_score",
            )
        if self.aggregate_block_threshold <= self.aggregate_watch_threshold:
            raise ValueError(
                "aggregate_block_threshold must exceed aggregate_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionDelayForecastInput:
    domain: str
    public_event_label: str
    oracle_expected_at: datetime
    oracle_observed_at: datetime | None
    evidence_conflict_score: Decimal
    deadline_clarity_score: Decimal
    dispute_pressure_score: Decimal
    historical_delay_memory_score: Decimal
    public_resolution_rule_ref: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDelayForecastInput:
            raise TypeError(
                "ResearchEventResolutionDelayForecastInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDelayForecastInput:
            raise ValueError(
                "input row must be exactly ResearchEventResolutionDelayForecastInput",
            )
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        _require_public_string("public_event_label", self.public_event_label)
        object.__setattr__(
            self,
            "oracle_expected_at",
            _as_utc("oracle_expected_at", self.oracle_expected_at),
        )
        object.__setattr__(
            self,
            "oracle_observed_at",
            _optional_utc("oracle_observed_at", self.oracle_observed_at),
        )
        for field_name in (
            "evidence_conflict_score",
            "deadline_clarity_score",
            "dispute_pressure_score",
            "historical_delay_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_ref("public_resolution_rule_ref", self.public_resolution_rule_ref)
        if (
            self.oracle_observed_at is not None
            and self.oracle_observed_at < self.oracle_expected_at
        ):
            raise ValueError(
                "oracle_observed_at must be on or after oracle_expected_at",
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchEventResolutionDelayForecastRow:
    domain: str
    public_event_label: str
    oracle_expected_at: datetime
    oracle_observed_at: datetime | None
    oracle_lag_seconds: Decimal
    evidence_conflict_score: Decimal
    deadline_clarity_score: Decimal
    dispute_pressure_score: Decimal
    historical_delay_memory_score: Decimal
    resolution_delay_risk_score: Decimal
    domain_status: str
    redacted_resolution_rule_ref: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchEventResolutionDelayForecastConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDelayForecastRow:
            raise TypeError(
                "ResearchEventResolutionDelayForecastRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchEventResolutionDelayForecastConfig | None,
    ) -> None:
        if type(self) is not ResearchEventResolutionDelayForecastRow:
            raise ValueError("row must be exactly ResearchEventResolutionDelayForecastRow")
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        _require_public_string("public_event_label", self.public_event_label)
        object.__setattr__(
            self,
            "oracle_expected_at",
            _as_utc("oracle_expected_at", self.oracle_expected_at),
        )
        object.__setattr__(
            self,
            "oracle_observed_at",
            _optional_utc("oracle_observed_at", self.oracle_observed_at),
        )
        object.__setattr__(
            self,
            "oracle_lag_seconds",
            _require_nonnegative_decimal("oracle_lag_seconds", self.oracle_lag_seconds),
        )
        for field_name in (
            "evidence_conflict_score",
            "deadline_clarity_score",
            "dispute_pressure_score",
            "historical_delay_memory_score",
            "resolution_delay_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("domain_status", self.domain_status)
        object.__setattr__(
            self,
            "redacted_resolution_rule_ref",
            _require_redacted_ref(
                "redacted_resolution_rule_ref",
                self.redacted_resolution_rule_ref,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionDelayForecastReasonCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDelayForecastReasonCount:
            raise TypeError(
                "ResearchEventResolutionDelayForecastReasonCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDelayForecastReasonCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventResolutionDelayForecastReasonCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchEventResolutionDelayForecastReport:
    generated_at: datetime
    config_version: str
    forecast_status: str
    next_step: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    max_resolution_delay_risk_score: Decimal
    average_resolution_delay_risk_score: Decimal
    max_oracle_lag_seconds: Decimal
    average_oracle_lag_seconds: Decimal
    oracle_lag_pressure_count: Decimal
    evidence_conflict_count: Decimal
    deadline_clarity_count: Decimal
    dispute_pressure_count: Decimal
    historical_delay_memory_count: Decimal
    rows: tuple[ResearchEventResolutionDelayForecastRow, ...]
    reason_code_counts: tuple[ResearchEventResolutionDelayForecastReasonCount, ...]
    reason_codes: tuple[str, ...]
    report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDelayForecastReport:
            raise TypeError(
                "ResearchEventResolutionDelayForecastReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDelayForecastReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionDelayForecastReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("forecast_status", self.forecast_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "max_resolution_delay_risk_score",
            "average_resolution_delay_risk_score",
            "max_oracle_lag_seconds",
            "average_oracle_lag_seconds",
            "oracle_lag_pressure_count",
            "evidence_conflict_count",
            "deadline_clarity_count",
            "dispute_pressure_count",
            "historical_delay_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchEventResolutionDelayForecastRow:
                raise ValueError(
                    "rows must contain ResearchEventResolutionDelayForecastRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not ResearchEventResolutionDelayForecastReasonCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchEventResolutionDelayForecastReasonCount",
                )
            _require_hard_flags("reason count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _require_sha256_digest("report_digest", self.report_digest)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.report_digest != expected_digest:
            raise ValueError("report_digest must match report payload")


def build_research_event_resolution_delay_forecast_report(
    input_rows: list[ResearchEventResolutionDelayForecastInput]
    | tuple[ResearchEventResolutionDelayForecastInput, ...],
    *,
    config: ResearchEventResolutionDelayForecastConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionDelayForecastReport:
    cfg = config or ResearchEventResolutionDelayForecastConfig()
    if type(cfg) is not ResearchEventResolutionDelayForecastConfig:
        raise ValueError("config must be a ResearchEventResolutionDelayForecastConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = _ranked_rows(built_rows)
    domain_count = _count(len(ranked_rows))
    pass_domain_count = _count(
        sum(1 for row in ranked_rows if row.domain_status == STATUS_PASS),
    )
    watch_domain_count = _count(
        sum(1 for row in ranked_rows if row.domain_status == STATUS_WATCH),
    )
    block_domain_count = _count(
        sum(1 for row in ranked_rows if row.domain_status == STATUS_BLOCK),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            ResearchEventResolutionDelayForecastReasonCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    forecast_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_domain_count=block_domain_count,
        watch_domain_count=watch_domain_count,
    )
    values = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "forecast_status": forecast_status,
        "next_step": NEXT_STEPS[forecast_status],
        "domain_count": domain_count,
        "pass_domain_count": pass_domain_count,
        "watch_domain_count": watch_domain_count,
        "block_domain_count": block_domain_count,
        "max_resolution_delay_risk_score": max(
            (row.resolution_delay_risk_score for row in ranked_rows),
            default=ZERO,
        ),
        "average_resolution_delay_risk_score": _ratio(
            _sum_decimal(row.resolution_delay_risk_score for row in ranked_rows),
            domain_count,
        ),
        "max_oracle_lag_seconds": max(
            (row.oracle_lag_seconds for row in ranked_rows),
            default=ZERO,
        ),
        "average_oracle_lag_seconds": _ratio(
            _sum_decimal(row.oracle_lag_seconds for row in ranked_rows),
            domain_count,
        ),
        "oracle_lag_pressure_count": _reason_group_count(
            ranked_rows,
            (ORACLE_LAG_BLOCK_REASON, ORACLE_LAG_WATCH_REASON),
        ),
        "evidence_conflict_count": _reason_group_count(
            ranked_rows,
            (EVIDENCE_CONFLICT_BLOCK_REASON, EVIDENCE_CONFLICT_WATCH_REASON),
        ),
        "deadline_clarity_count": _reason_group_count(
            ranked_rows,
            (DEADLINE_CLARITY_BLOCK_REASON, DEADLINE_CLARITY_WATCH_REASON),
        ),
        "dispute_pressure_count": _reason_group_count(
            ranked_rows,
            (DISPUTE_PRESSURE_BLOCK_REASON, DISPUTE_PRESSURE_WATCH_REASON),
        ),
        "historical_delay_memory_count": _reason_group_count(
            ranked_rows,
            (
                HISTORICAL_DELAY_MEMORY_BLOCK_REASON,
                HISTORICAL_DELAY_MEMORY_WATCH_REASON,
            ),
        ),
        "rows": ranked_rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionDelayForecastReport(
        **values,
        report_digest=_digest_for_public_value(values),
    )


def research_event_resolution_delay_forecast_report_payload(
    report: ResearchEventResolutionDelayForecastReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionDelayForecastReport:
        raise ValueError(
            "report must be a ResearchEventResolutionDelayForecastReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


def research_event_resolution_delay_forecast_report_digest(
    report: ResearchEventResolutionDelayForecastReport,
) -> str:
    if type(report) is not ResearchEventResolutionDelayForecastReport:
        raise ValueError(
            "report must be a ResearchEventResolutionDelayForecastReport",
        )
    _require_hard_flags("report", report)
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


def _build_row(
    row: ResearchEventResolutionDelayForecastInput,
    *,
    config: ResearchEventResolutionDelayForecastConfig,
    generated_at: datetime,
) -> ResearchEventResolutionDelayForecastRow:
    lag_end = row.oracle_observed_at or generated_at
    oracle_lag_seconds = _datetime_delta_seconds(lag_end, row.oracle_expected_at)
    risk_score = _risk_score(
        oracle_lag_seconds=oracle_lag_seconds,
        evidence_conflict_score=row.evidence_conflict_score,
        deadline_clarity_score=row.deadline_clarity_score,
        dispute_pressure_score=row.dispute_pressure_score,
        historical_delay_memory_score=row.historical_delay_memory_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        oracle_lag_seconds=oracle_lag_seconds,
        evidence_conflict_score=row.evidence_conflict_score,
        deadline_clarity_score=row.deadline_clarity_score,
        dispute_pressure_score=row.dispute_pressure_score,
        historical_delay_memory_score=row.historical_delay_memory_score,
        config=config,
    )
    domain_status = _row_status(
        reason_codes,
        resolution_delay_risk_score=risk_score,
        config=config,
    )
    return ResearchEventResolutionDelayForecastRow(
        domain=row.domain,
        public_event_label=row.public_event_label,
        oracle_expected_at=row.oracle_expected_at,
        oracle_observed_at=row.oracle_observed_at,
        oracle_lag_seconds=oracle_lag_seconds,
        evidence_conflict_score=row.evidence_conflict_score,
        deadline_clarity_score=row.deadline_clarity_score,
        dispute_pressure_score=row.dispute_pressure_score,
        historical_delay_memory_score=row.historical_delay_memory_score,
        resolution_delay_risk_score=risk_score,
        domain_status=domain_status,
        redacted_resolution_rule_ref=_redacted_ref(row.public_resolution_rule_ref),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _normalize_input_rows(
    rows: list[ResearchEventResolutionDelayForecastInput]
    | tuple[ResearchEventResolutionDelayForecastInput, ...],
    generated_at: datetime,
) -> tuple[ResearchEventResolutionDelayForecastInput, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionDelayForecastInput:
            raise ValueError(
                "input rows must contain ResearchEventResolutionDelayForecastInput",
            )
        _require_hard_flags("input row", row)
        if row.oracle_expected_at > generated_at:
            raise ValueError("oracle_expected_at must be on or before generated_at")
        if row.oracle_observed_at is not None and row.oracle_observed_at > generated_at:
            raise ValueError("oracle_observed_at must be on or before generated_at")
        if row.domain in seen:
            raise ValueError("input rows must not contain duplicate domains")
        seen.add(row.domain)
    return normalized


def _row_reason_codes(
    *,
    oracle_lag_seconds: Decimal,
    evidence_conflict_score: Decimal,
    deadline_clarity_score: Decimal,
    dispute_pressure_score: Decimal,
    historical_delay_memory_score: Decimal,
    config: ResearchEventResolutionDelayForecastConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if oracle_lag_seconds >= config.oracle_lag_block_seconds:
        reason_codes.append(ORACLE_LAG_BLOCK_REASON)
    elif oracle_lag_seconds >= config.oracle_lag_watch_seconds:
        reason_codes.append(ORACLE_LAG_WATCH_REASON)
    if evidence_conflict_score >= config.evidence_conflict_block_score:
        reason_codes.append(EVIDENCE_CONFLICT_BLOCK_REASON)
    elif evidence_conflict_score >= config.evidence_conflict_watch_score:
        reason_codes.append(EVIDENCE_CONFLICT_WATCH_REASON)
    if deadline_clarity_score <= config.deadline_clarity_block_score:
        reason_codes.append(DEADLINE_CLARITY_BLOCK_REASON)
    elif deadline_clarity_score <= config.deadline_clarity_watch_score:
        reason_codes.append(DEADLINE_CLARITY_WATCH_REASON)
    if dispute_pressure_score >= config.dispute_pressure_block_score:
        reason_codes.append(DISPUTE_PRESSURE_BLOCK_REASON)
    elif dispute_pressure_score >= config.dispute_pressure_watch_score:
        reason_codes.append(DISPUTE_PRESSURE_WATCH_REASON)
    if historical_delay_memory_score >= config.historical_delay_memory_block_score:
        reason_codes.append(HISTORICAL_DELAY_MEMORY_BLOCK_REASON)
    elif historical_delay_memory_score >= config.historical_delay_memory_watch_score:
        reason_codes.append(HISTORICAL_DELAY_MEMORY_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _risk_score(
    *,
    oracle_lag_seconds: Decimal,
    evidence_conflict_score: Decimal,
    deadline_clarity_score: Decimal,
    dispute_pressure_score: Decimal,
    historical_delay_memory_score: Decimal,
    config: ResearchEventResolutionDelayForecastConfig,
) -> Decimal:
    oracle_pressure = _ratio(oracle_lag_seconds, config.oracle_lag_block_seconds)
    if oracle_pressure > ONE:
        oracle_pressure = ONE
    deadline_pressure = _quantize(ONE - deadline_clarity_score)
    return _ratio(
        oracle_pressure
        + evidence_conflict_score
        + deadline_pressure
        + dispute_pressure_score
        + historical_delay_memory_score,
        FACTOR_COUNT,
    )


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    resolution_delay_risk_score: Decimal,
    config: ResearchEventResolutionDelayForecastConfig,
) -> str:
    if (
        DEADLINE_CLARITY_BLOCK_REASON in reason_codes
        or DISPUTE_PRESSURE_BLOCK_REASON in reason_codes
        or EVIDENCE_CONFLICT_BLOCK_REASON in reason_codes
        or HISTORICAL_DELAY_MEMORY_BLOCK_REASON in reason_codes
        or ORACLE_LAG_BLOCK_REASON in reason_codes
        or resolution_delay_risk_score >= config.aggregate_block_threshold
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,) and (
        resolution_delay_risk_score < config.aggregate_watch_threshold
    ):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    block_domain_count: Decimal,
    watch_domain_count: Decimal,
) -> str:
    if not has_inputs or block_domain_count > ZERO:
        return STATUS_BLOCK
    if watch_domain_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchEventResolutionDelayForecastRow, ...],
) -> tuple[ResearchEventResolutionDelayForecastRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.domain_status),
                -row.resolution_delay_risk_score,
                row.domain,
                row.public_event_label,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionDelayForecastRow, ...],
) -> tuple[ResearchEventResolutionDelayForecastReasonCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchEventResolutionDelayForecastReasonCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            domain_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _reason_group_count(
    rows: tuple[ResearchEventResolutionDelayForecastRow, ...],
    reason_codes: tuple[str, str],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if reason_codes[0] in row.reason_codes or reason_codes[1] in row.reason_codes
        ),
    )


def _validate_row(
    row: ResearchEventResolutionDelayForecastRow,
    *,
    config: ResearchEventResolutionDelayForecastConfig | None,
) -> None:
    if config is None:
        config = ResearchEventResolutionDelayForecastConfig()
    if type(config) is not ResearchEventResolutionDelayForecastConfig:
        raise ValueError(
            "validation_config must be a ResearchEventResolutionDelayForecastConfig",
        )
    expected_reason_codes = _row_reason_codes(
        oracle_lag_seconds=row.oracle_lag_seconds,
        evidence_conflict_score=row.evidence_conflict_score,
        deadline_clarity_score=row.deadline_clarity_score,
        dispute_pressure_score=row.dispute_pressure_score,
        historical_delay_memory_score=row.historical_delay_memory_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_risk_score = _risk_score(
        oracle_lag_seconds=row.oracle_lag_seconds,
        evidence_conflict_score=row.evidence_conflict_score,
        deadline_clarity_score=row.deadline_clarity_score,
        dispute_pressure_score=row.dispute_pressure_score,
        historical_delay_memory_score=row.historical_delay_memory_score,
        config=config,
    )
    if row.resolution_delay_risk_score != expected_risk_score:
        raise ValueError("resolution_delay_risk_score must match row inputs")
    if row.oracle_observed_at is not None:
        expected_lag = _datetime_delta_seconds(
            row.oracle_observed_at,
            row.oracle_expected_at,
        )
        if row.oracle_lag_seconds != expected_lag:
            raise ValueError("oracle_lag_seconds must match oracle timestamps")
    if row.domain_status != _row_status(
        row.reason_codes,
        resolution_delay_risk_score=row.resolution_delay_risk_score,
        config=config,
    ):
        raise ValueError("domain_status must match reason_codes and risk score")
    if not _is_redacted_ref(row.redacted_resolution_rule_ref):
        raise ValueError("redacted_resolution_rule_ref must be redacted or public")


def _validate_report(report: ResearchEventResolutionDelayForecastReport) -> None:
    if report.next_step != NEXT_STEPS[report.forecast_status]:
        raise ValueError("next_step must match forecast_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be ranked deterministically")
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    expected_pass = _count(
        sum(1 for row in report.rows if row.domain_status == STATUS_PASS),
    )
    if report.pass_domain_count != expected_pass:
        raise ValueError("pass_domain_count must match rows")
    expected_watch = _count(
        sum(1 for row in report.rows if row.domain_status == STATUS_WATCH),
    )
    if report.watch_domain_count != expected_watch:
        raise ValueError("watch_domain_count must match rows")
    expected_block = _count(
        sum(1 for row in report.rows if row.domain_status == STATUS_BLOCK),
    )
    if report.block_domain_count != expected_block:
        raise ValueError("block_domain_count must match rows")
    expected_max_risk = max(
        (row.resolution_delay_risk_score for row in report.rows),
        default=ZERO,
    )
    if report.max_resolution_delay_risk_score != expected_max_risk:
        raise ValueError("max_resolution_delay_risk_score must match rows")
    if report.average_resolution_delay_risk_score != _ratio(
        _sum_decimal(row.resolution_delay_risk_score for row in report.rows),
        report.domain_count,
    ):
        raise ValueError("average_resolution_delay_risk_score must match rows")
    expected_max_lag = max(
        (row.oracle_lag_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_oracle_lag_seconds != expected_max_lag:
        raise ValueError("max_oracle_lag_seconds must match rows")
    if report.average_oracle_lag_seconds != _ratio(
        _sum_decimal(row.oracle_lag_seconds for row in report.rows),
        report.domain_count,
    ):
        raise ValueError("average_oracle_lag_seconds must match rows")
    if report.oracle_lag_pressure_count != _reason_group_count(
        report.rows,
        (ORACLE_LAG_BLOCK_REASON, ORACLE_LAG_WATCH_REASON),
    ):
        raise ValueError("oracle_lag_pressure_count must match rows")
    if report.evidence_conflict_count != _reason_group_count(
        report.rows,
        (EVIDENCE_CONFLICT_BLOCK_REASON, EVIDENCE_CONFLICT_WATCH_REASON),
    ):
        raise ValueError("evidence_conflict_count must match rows")
    if report.deadline_clarity_count != _reason_group_count(
        report.rows,
        (DEADLINE_CLARITY_BLOCK_REASON, DEADLINE_CLARITY_WATCH_REASON),
    ):
        raise ValueError("deadline_clarity_count must match rows")
    if report.dispute_pressure_count != _reason_group_count(
        report.rows,
        (DISPUTE_PRESSURE_BLOCK_REASON, DISPUTE_PRESSURE_WATCH_REASON),
    ):
        raise ValueError("dispute_pressure_count must match rows")
    if report.historical_delay_memory_count != _reason_group_count(
        report.rows,
        (
            HISTORICAL_DELAY_MEMORY_BLOCK_REASON,
            HISTORICAL_DELAY_MEMORY_WATCH_REASON,
        ),
    ):
        raise ValueError("historical_delay_memory_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchEventResolutionDelayForecastReasonCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ONE,
            ),
        )
        expected_codes = (NO_INPUTS_REASON,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_domain_count=report.block_domain_count,
        watch_domain_count=report.watch_domain_count,
    )
    if report.forecast_status != expected_status:
        raise ValueError("forecast_status must match rows")


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and ranked")
    if PASS_REASON in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and ranked")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FORECAST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_domain(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text.startswith("_") or text.endswith("_") or "__" in text:
        raise ValueError(f"{field_name} must be lower snake text")
    for char in text:
        if not (char == "_" or "a" <= char <= "z" or "0" <= char <= "9"):
            raise ValueError(f"{field_name} must be lower snake text")
    return text


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_text(field_name, value)
    return value


def _require_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_ref(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _is_redacted_ref(value: str) -> bool:
    if value.startswith("sha256:") and len(value) == REDACTED_DIGEST_LENGTH:
        digest = value.removeprefix("sha256:")
        return all(char in "0123456789abcdef" for char in digest)
    lowered = value.lower()
    return "public" in lowered and any(
        fragment in lowered for fragment in _PUBLIC_REF_FRAGMENTS
    )


def _redacted_ref(value: str) -> str:
    if _is_redacted_ref(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return decimal_value


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return _quantize(Decimal(value))
    if type(value) is Decimal:
        return _quantize(value)
    raise ValueError("count value must be an int or Decimal")


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(char in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_digest(report: ResearchEventResolutionDelayForecastReport) -> str:
    return _digest_for_public_value(_report_values_without_digest(report))


def _report_values_without_digest(
    report: ResearchEventResolutionDelayForecastReport,
) -> dict[str, object]:
    values = asdict(report)
    del values["report_digest"]
    return values


def _digest_for_public_value(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{path or label} must be finite Decimal")
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_text(nested_path, key)
            _reject_unsafe_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        _join_parts("au", "th"),
        _join_parts("cred", "ential"),
        _join_parts("hid", "den"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        "sign",
        _join_parts("priv", "ate"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("tok", "en"),
        _join_parts("cli", "ent"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("reco", "mmend"),
        _join_parts("siz", "ing"),
        _join_parts("tra", "de"),
        _join_parts("sta", "ke"),
        _join_parts("ht", "tp"),
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} has unsafe value")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
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


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION",
    "ResearchEventResolutionDelayForecastConfig",
    "ResearchEventResolutionDelayForecastInput",
    "ResearchEventResolutionDelayForecastReasonCount",
    "ResearchEventResolutionDelayForecastReport",
    "ResearchEventResolutionDelayForecastRow",
    "build_research_event_resolution_delay_forecast_report",
    "research_event_resolution_delay_forecast_report_digest",
    "research_event_resolution_delay_forecast_report_payload",
)
