"""Pure report-only breaking-news sensitivity triage report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION = (
    "research-event-breaking-news-sensitivity-report-v0"
)
RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_STATUSES = ("pass", "watch", "block")

EMPTY_REPORT_REASON_CODE = "breaking_news_sensitivity_report_empty"
ROW_PASS_REASON_CODE = "breaking_news_sensitivity_pass"
ROW_REASON_CODES = (
    "update_velocity_block",
    "update_velocity_watch",
    "source_authority_mix_block",
    "source_authority_mix_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "probability_movement_block",
    "probability_movement_watch",
    "liquidity_reliability_block",
    "liquidity_reliability_watch",
    "resolution_proximity_block",
    "resolution_proximity_watch",
    ROW_PASS_REASON_CODE,
)
REPORT_REASON_CODES = (
    "update_velocity_review",
    "source_authority_mix_review",
    "contradiction_pressure_review",
    "probability_movement_review",
    "liquidity_reliability_review",
    "resolution_proximity_review",
    "breaking_news_sensitivity_report_block",
    "breaking_news_sensitivity_report_watch",
    "breaking_news_sensitivity_report_pass",
    EMPTY_REPORT_REASON_CODE,
)
REASON_CODES = ROW_REASON_CODES + REPORT_REASON_CODES

_REPORT_PUBLIC_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_sensitivity_score",
        "max_sensitivity_score",
        "mean_update_velocity_score",
        "mean_authority_mix_score",
        "mean_contradiction_pressure_ratio",
        "mean_liquidity_reliability_score",
        "max_resolution_proximity_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
_ROW_PUBLIC_KEYS = frozenset(
    (
        "observed_at",
        "update_count_1h",
        "update_velocity_score",
        "source_authority_mix_score",
        "contradiction_pressure_ratio",
        "probability_movement",
        "liquidity_reliability_score",
        "resolution_proximity_score",
        "breaking_news_sensitivity_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "row_number",
        "derived_validation_digest",
    ),
)
_REASON_CODE_COUNT_PUBLIC_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_PUBLIC_COUNT_FIELDS = ("input_count", "pass_count", "watch_count", "block_count")
_REPORT_PUBLIC_RATIO_FIELDS = (
    "mean_sensitivity_score",
    "max_sensitivity_score",
    "mean_update_velocity_score",
    "mean_authority_mix_score",
    "mean_contradiction_pressure_ratio",
    "mean_liquidity_reliability_score",
    "max_resolution_proximity_score",
)
_ROW_PUBLIC_RATIO_FIELDS = (
    "update_velocity_score",
    "source_authority_mix_score",
    "contradiction_pressure_ratio",
    "probability_movement",
    "liquidity_reliability_score",
    "resolution_proximity_score",
    "breaking_news_sensitivity_score",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX = Decimal("6.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "://",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "www.",
        "candidate",
        "credential",
        "condition_id",
        "database",
        "dsn",
        "endpoint",
        "http",
        "https",
        "live",
        "market_id",
        "market_slug",
        "private_key",
        "question",
        "raw",
        "recommendation",
        "secret",
        "session",
        "sizing",
        "slug",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION",
    "RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_STATUSES",
    "REASON_CODES",
    "ResearchEventBreakingNewsSensitivityConfig",
    "ResearchEventBreakingNewsSensitivityInput",
    "ResearchEventBreakingNewsSensitivityReasonCodeCount",
    "ResearchEventBreakingNewsSensitivityRow",
    "ResearchEventBreakingNewsSensitivityReport",
    "build_research_event_breaking_news_sensitivity_report",
    "research_event_breaking_news_sensitivity_report_digest",
    "research_event_breaking_news_sensitivity_report_payload",
    "validate_research_event_breaking_news_sensitivity_public_payload",
)


@dataclass(frozen=True)
class ResearchEventBreakingNewsSensitivityConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION
    pass_update_count_1h_ceiling: Decimal = Decimal("2.000000")
    watch_update_count_1h_ceiling: Decimal = Decimal("4.000000")
    pass_authority_mix_floor: Decimal = Decimal("0.750000")
    watch_authority_mix_floor: Decimal = Decimal("0.500000")
    pass_contradiction_pressure_ceiling: Decimal = Decimal("0.100000")
    watch_contradiction_pressure_ceiling: Decimal = Decimal("0.350000")
    pass_probability_movement_ceiling: Decimal = Decimal("0.050000")
    watch_probability_movement_ceiling: Decimal = Decimal("0.150000")
    pass_liquidity_reliability_floor: Decimal = Decimal("0.700000")
    watch_liquidity_reliability_floor: Decimal = Decimal("0.400000")
    pass_hours_to_resolution_floor: Decimal = Decimal("48.000000")
    watch_hours_to_resolution_floor: Decimal = Decimal("12.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventBreakingNewsSensitivityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventBreakingNewsSensitivityConfig:
            raise ValueError(
                "config must be exactly ResearchEventBreakingNewsSensitivityConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_update_count_1h_ceiling",
            "watch_update_count_1h_ceiling",
            "pass_hours_to_resolution_floor",
            "watch_hours_to_resolution_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_authority_mix_floor",
            "watch_authority_mix_floor",
            "pass_contradiction_pressure_ceiling",
            "watch_contradiction_pressure_ceiling",
            "pass_probability_movement_ceiling",
            "watch_probability_movement_ceiling",
            "pass_liquidity_reliability_floor",
            "watch_liquidity_reliability_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.pass_update_count_1h_ceiling > self.watch_update_count_1h_ceiling:
            raise ValueError("pass update velocity threshold cannot exceed watch threshold")
        if self.watch_authority_mix_floor > self.pass_authority_mix_floor:
            raise ValueError("watch authority mix floor cannot exceed pass floor")
        if self.pass_contradiction_pressure_ceiling > self.watch_contradiction_pressure_ceiling:
            raise ValueError("pass contradiction threshold cannot exceed watch threshold")
        if self.pass_probability_movement_ceiling > self.watch_probability_movement_ceiling:
            raise ValueError("pass probability movement threshold cannot exceed watch threshold")
        if self.watch_liquidity_reliability_floor > self.pass_liquidity_reliability_floor:
            raise ValueError("watch liquidity reliability floor cannot exceed pass floor")
        if self.watch_hours_to_resolution_floor > self.pass_hours_to_resolution_floor:
            raise ValueError("watch resolution floor cannot exceed pass floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventBreakingNewsSensitivityInput:
    event_ref: str
    observed_at: datetime
    update_count_1h: Decimal
    authoritative_source_count: Decimal
    total_source_count: Decimal
    contradiction_count: Decimal
    claim_count: Decimal
    probability_movement: Decimal
    liquidity_reliability: Decimal
    hours_to_resolution: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventBreakingNewsSensitivityInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventBreakingNewsSensitivityInput:
            raise ValueError(
                "input must be exactly ResearchEventBreakingNewsSensitivityInput",
            )
        _require_internal_ref("event_ref", self.event_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "update_count_1h",
            "authoritative_source_count",
            "total_source_count",
            "contradiction_count",
            "claim_count",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_movement", "liquidity_reliability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.total_source_count == ZERO:
            raise ValueError("total_source_count must be positive")
        if self.authoritative_source_count > self.total_source_count:
            raise ValueError("authoritative_source_count cannot exceed total_source_count")
        if self.claim_count == ZERO:
            raise ValueError("claim_count must be positive")
        if self.contradiction_count > self.claim_count:
            raise ValueError("contradiction_count cannot exceed claim_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventBreakingNewsSensitivityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventBreakingNewsSensitivityReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventBreakingNewsSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchEventBreakingNewsSensitivityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_ratio("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventBreakingNewsSensitivityRow:
    event_ref: str
    observed_at: datetime
    update_count_1h: Decimal
    update_velocity_score: Decimal
    source_authority_mix_score: Decimal
    contradiction_pressure_ratio: Decimal
    probability_movement: Decimal
    liquidity_reliability_score: Decimal
    resolution_proximity_score: Decimal
    breaking_news_sensitivity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventBreakingNewsSensitivityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventBreakingNewsSensitivityRow:
            raise ValueError("row must be exactly ResearchEventBreakingNewsSensitivityRow")
        _require_internal_ref("event_ref", self.event_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "update_count_1h",
            _normalize_nonnegative_decimal("update_count_1h", self.update_count_1h),
        )
        for field_name in (
            "update_velocity_score",
            "source_authority_mix_score",
            "contradiction_pressure_ratio",
            "probability_movement",
            "liquidity_reliability_score",
            "resolution_proximity_score",
            "breaking_news_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _row_digest(self))
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventBreakingNewsSensitivityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_sensitivity_score: Decimal
    max_sensitivity_score: Decimal
    mean_update_velocity_score: Decimal
    mean_authority_mix_score: Decimal
    mean_contradiction_pressure_ratio: Decimal
    mean_liquidity_reliability_score: Decimal
    max_resolution_proximity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventBreakingNewsSensitivityReasonCodeCount, ...]
    rows: tuple[ResearchEventBreakingNewsSensitivityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventBreakingNewsSensitivityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventBreakingNewsSensitivityReport:
            raise ValueError(
                "report must be exactly ResearchEventBreakingNewsSensitivityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_sensitivity_score",
            "max_sensitivity_score",
            "mean_update_velocity_score",
            "mean_authority_mix_score",
            "mean_contradiction_pressure_ratio",
            "mean_liquidity_reliability_score",
            "max_resolution_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)


def build_research_event_breaking_news_sensitivity_report(
    inputs: Iterable[object],
    *,
    config: ResearchEventBreakingNewsSensitivityConfig,
    generated_at: datetime,
) -> ResearchEventBreakingNewsSensitivityReport:
    """Build a deterministic report for events sensitive to breaking news."""

    if type(config) is not ResearchEventBreakingNewsSensitivityConfig:
        raise ValueError("config must be a ResearchEventBreakingNewsSensitivityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventBreakingNewsSensitivityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_sensitivity_score=_mean(tuple(row.breaking_news_sensitivity_score for row in rows)),
        max_sensitivity_score=_max_decimal(tuple(row.breaking_news_sensitivity_score for row in rows)),
        mean_update_velocity_score=_mean(tuple(row.update_velocity_score for row in rows)),
        mean_authority_mix_score=_mean(tuple(row.source_authority_mix_score for row in rows)),
        mean_contradiction_pressure_ratio=_mean(tuple(row.contradiction_pressure_ratio for row in rows)),
        mean_liquidity_reliability_score=_mean(tuple(row.liquidity_reliability_score for row in rows)),
        max_resolution_proximity_score=_max_decimal(tuple(row.resolution_proximity_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_event_breaking_news_sensitivity_report_payload(
    report: ResearchEventBreakingNewsSensitivityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventBreakingNewsSensitivityReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report, include_digest=True)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report, allow_mapping=True)
        _verify_public_payload_integrity(report)
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a ResearchEventBreakingNewsSensitivityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    return payload


def research_event_breaking_news_sensitivity_report_digest(
    report: ResearchEventBreakingNewsSensitivityReport,
) -> str:
    if type(report) is not ResearchEventBreakingNewsSensitivityReport:
        raise ValueError("report must be a ResearchEventBreakingNewsSensitivityReport")
    _verify_report_integrity(report)
    return report.derived_validation_digest


def validate_research_event_breaking_news_sensitivity_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
        _verify_public_payload_integrity(payload)
        if payload.get("status") not in RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_STATUSES:
            return False
        if type(payload.get("reason_codes")) is not list:
            return False
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_sensitivity_score",
            "max_sensitivity_score",
            "mean_update_velocity_score",
            "mean_authority_mix_score",
            "mean_contradiction_pressure_ratio",
            "mean_liquidity_reliability_score",
            "max_resolution_proximity_score",
        ):
            if type(payload.get(field_name)) is not str:
                return False
        return True
    except (TypeError, ValueError):
        return False


def _row_from_input(
    value: ResearchEventBreakingNewsSensitivityInput,
    *,
    config: ResearchEventBreakingNewsSensitivityConfig,
    generated_at: datetime,
) -> ResearchEventBreakingNewsSensitivityRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    source_authority_mix_score = _ratio(
        value.authoritative_source_count,
        value.total_source_count,
    )
    contradiction_pressure_ratio = _ratio(value.contradiction_count, value.claim_count)
    update_velocity_score = _clamped_ratio(
        _ratio(
            value.update_count_1h,
            config.pass_update_count_1h_ceiling + config.watch_update_count_1h_ceiling,
        ),
    )
    resolution_proximity_score = _clamped_ratio(
        ONE - _ratio(value.hours_to_resolution, config.pass_hours_to_resolution_floor),
    )
    breaking_news_sensitivity_score = _mean(
        (
            update_velocity_score,
            _clamped_ratio(ONE - source_authority_mix_score),
            contradiction_pressure_ratio,
            value.probability_movement,
            _clamped_ratio(ONE - value.liquidity_reliability),
            resolution_proximity_score,
        ),
    )
    component_statuses = {
        "update_velocity": _maximum_status(
            value.update_count_1h,
            pass_threshold=config.pass_update_count_1h_ceiling,
            watch_threshold=config.watch_update_count_1h_ceiling,
        ),
        "source_authority_mix": _minimum_status(
            source_authority_mix_score,
            pass_threshold=config.pass_authority_mix_floor,
            watch_threshold=config.watch_authority_mix_floor,
        ),
        "contradiction_pressure": _maximum_status(
            contradiction_pressure_ratio,
            pass_threshold=config.pass_contradiction_pressure_ceiling,
            watch_threshold=config.watch_contradiction_pressure_ceiling,
        ),
        "probability_movement": _maximum_status(
            value.probability_movement,
            pass_threshold=config.pass_probability_movement_ceiling,
            watch_threshold=config.watch_probability_movement_ceiling,
        ),
        "liquidity_reliability": _minimum_status(
            value.liquidity_reliability,
            pass_threshold=config.pass_liquidity_reliability_floor,
            watch_threshold=config.watch_liquidity_reliability_floor,
        ),
        "resolution_proximity": _minimum_status(
            value.hours_to_resolution,
            pass_threshold=config.pass_hours_to_resolution_floor,
            watch_threshold=config.watch_hours_to_resolution_floor,
        ),
    }
    return ResearchEventBreakingNewsSensitivityRow(
        event_ref=value.event_ref,
        observed_at=observed_at,
        update_count_1h=value.update_count_1h,
        update_velocity_score=update_velocity_score,
        source_authority_mix_score=source_authority_mix_score,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        probability_movement=value.probability_movement,
        liquidity_reliability_score=value.liquidity_reliability,
        resolution_proximity_score=resolution_proximity_score,
        breaking_news_sensitivity_score=breaking_news_sensitivity_score,
        status=_overall_status(component_statuses.values()),
        reason_codes=_row_reason_codes(component_statuses),
    )


def _row_reason_codes(component_statuses: Mapping[str, str]) -> tuple[str, ...]:
    codes: list[str] = []
    for prefix in (
        "update_velocity",
        "source_authority_mix",
        "contradiction_pressure",
        "probability_movement",
        "liquidity_reliability",
        "resolution_proximity",
    ):
        status = component_statuses[prefix]
        _require_status("component_status", status)
        if status != "pass":
            codes.append(f"{prefix}_{status}")
    if not codes:
        codes.append(ROW_PASS_REASON_CODE)
    return _normalize_row_reason_codes(tuple(codes))


def _report_status(rows: tuple[ResearchEventBreakingNewsSensitivityRow, ...]) -> str:
    if not rows:
        return "block"
    return _overall_status(row.status for row in rows)


def _report_reason_codes(
    rows: tuple[ResearchEventBreakingNewsSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes: list[str] = []
    for prefix in (
        "update_velocity",
        "source_authority_mix",
        "contradiction_pressure",
        "probability_movement",
        "liquidity_reliability",
        "resolution_proximity",
    ):
        if any(reason_code.startswith(f"{prefix}_") for reason_code in row_codes):
            codes.append(f"{prefix}_review")
    codes.append(f"breaking_news_sensitivity_report_{_report_status(rows)}")
    return _normalize_report_reason_codes(tuple(codes))


def _row_sort_key(
    row: ResearchEventBreakingNewsSensitivityRow,
) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        _quantize(ONE - row.breaking_news_sensitivity_score),
        row.event_ref,
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchEventBreakingNewsSensitivityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized: list[ResearchEventBreakingNewsSensitivityInput] = []
    seen_refs: set[str] = set()
    for value in values:
        if type(value) is not ResearchEventBreakingNewsSensitivityInput:
            raise ValueError(
                "inputs must contain ResearchEventBreakingNewsSensitivityInput values",
            )
        _require_hard_flags("input", value)
        if value.event_ref in seen_refs:
            raise ValueError("event_ref values must be unique")
        seen_refs.add(value.event_ref)
        normalized.append(value)
    return tuple(
        sorted(
            normalized,
            key=lambda value: (
                value.observed_at,
                value.event_ref,
                value.update_count_1h,
                value.probability_movement,
            ),
        ),
    )


def _normalize_rows(rows: object) -> tuple[ResearchEventBreakingNewsSensitivityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventBreakingNewsSensitivityRow:
            raise ValueError("rows must contain ResearchEventBreakingNewsSensitivityRow values")
        _require_hard_flags("row", value)
    return values


def _reason_code_counts_from_rows(
    rows: tuple[ResearchEventBreakingNewsSensitivityRow, ...],
) -> tuple[ResearchEventBreakingNewsSensitivityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventBreakingNewsSensitivityReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=ONE,
                input_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    input_count = _count(len(rows))
    return tuple(
        ResearchEventBreakingNewsSensitivityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            input_ratio=_ratio(_count(counts[reason_code]), input_count),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counts
    )


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchEventBreakingNewsSensitivityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventBreakingNewsSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventBreakingNewsSensitivityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    return values


def _status_count(
    rows: tuple[ResearchEventBreakingNewsSensitivityRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.status == status))


def _overall_status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    for status in values:
        _require_status("status", status)
    if "block" in values:
        return "block"
    if "watch" in values:
        return "watch"
    return "pass"


def _minimum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _maximum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _validate_row(row: ResearchEventBreakingNewsSensitivityRow) -> None:
    if row.breaking_news_sensitivity_score != _mean(
        (
            row.update_velocity_score,
            _clamped_ratio(ONE - row.source_authority_mix_score),
            row.contradiction_pressure_ratio,
            row.probability_movement,
            _clamped_ratio(ONE - row.liquidity_reliability_score),
            row.resolution_proximity_score,
        ),
    ):
        raise ValueError("breaking_news_sensitivity_score must match component scores")
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest does not match row payload")


def _validate_report(report: ResearchEventBreakingNewsSensitivityReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.mean_sensitivity_score != _mean(
        tuple(row.breaking_news_sensitivity_score for row in rows),
    ):
        raise ValueError("mean_sensitivity_score must match rows")
    if report.max_sensitivity_score != _max_decimal(
        tuple(row.breaking_news_sensitivity_score for row in rows),
    ):
        raise ValueError("max_sensitivity_score must match rows")
    if report.mean_update_velocity_score != _mean(
        tuple(row.update_velocity_score for row in rows),
    ):
        raise ValueError("mean_update_velocity_score must match rows")
    if report.mean_authority_mix_score != _mean(
        tuple(row.source_authority_mix_score for row in rows),
    ):
        raise ValueError("mean_authority_mix_score must match rows")
    if report.mean_contradiction_pressure_ratio != _mean(
        tuple(row.contradiction_pressure_ratio for row in rows),
    ):
        raise ValueError("mean_contradiction_pressure_ratio must match rows")
    if report.mean_liquidity_reliability_score != _mean(
        tuple(row.liquidity_reliability_score for row in rows),
    ):
        raise ValueError("mean_liquidity_reliability_score must match rows")
    if report.max_resolution_proximity_score != _max_decimal(
        tuple(row.resolution_proximity_score for row in rows),
    ):
        raise ValueError("max_resolution_proximity_score must match rows")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")


def _verify_report_integrity(report: ResearchEventBreakingNewsSensitivityReport) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")
    for row in report.rows:
        if row.derived_validation_digest != _row_digest(row):
            raise ValueError("derived_validation_digest does not match row payload")


def _public_report_payload(
    report: ResearchEventBreakingNewsSensitivityReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "input_count": _payload_value(report.input_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "mean_sensitivity_score": _payload_value(report.mean_sensitivity_score),
        "max_sensitivity_score": _payload_value(report.max_sensitivity_score),
        "mean_update_velocity_score": _payload_value(report.mean_update_velocity_score),
        "mean_authority_mix_score": _payload_value(report.mean_authority_mix_score),
        "mean_contradiction_pressure_ratio": _payload_value(
            report.mean_contradiction_pressure_ratio,
        ),
        "mean_liquidity_reliability_score": _payload_value(
            report.mean_liquidity_reliability_score,
        ),
        "max_resolution_proximity_score": _payload_value(
            report.max_resolution_proximity_score,
        ),
        "status": report.status,
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "rows": [
            _public_row_payload(index, row, include_digest=True)
            for index, row in enumerate(report.rows, start=1)
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _public_row_payload(
    row_number: int,
    row: ResearchEventBreakingNewsSensitivityRow,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _public_row_digest_payload(row)
    payload["row_number"] = _payload_value(_count(row_number))
    if include_digest:
        payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _public_row_digest_payload(
    row: ResearchEventBreakingNewsSensitivityRow,
) -> dict[str, Any]:
    return {
        "observed_at": _payload_value(row.observed_at),
        "update_count_1h": _payload_value(row.update_count_1h),
        "update_velocity_score": _payload_value(row.update_velocity_score),
        "source_authority_mix_score": _payload_value(row.source_authority_mix_score),
        "contradiction_pressure_ratio": _payload_value(row.contradiction_pressure_ratio),
        "probability_movement": _payload_value(row.probability_movement),
        "liquidity_reliability_score": _payload_value(row.liquidity_reliability_score),
        "resolution_proximity_score": _payload_value(row.resolution_proximity_score),
        "breaking_news_sensitivity_score": _payload_value(
            row.breaking_news_sensitivity_score,
        ),
        "status": row.status,
        "reason_codes": _payload_value(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchEventBreakingNewsSensitivityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "input_ratio": _payload_value(row.input_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is ResearchEventBreakingNewsSensitivityReasonCodeCount:
        return _reason_code_count_payload(value)
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in sorted(value.items())}
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _report_digest(report: ResearchEventBreakingNewsSensitivityReport) -> str:
    return _payload_digest(_public_report_payload(report, include_digest=False))


def _row_digest(row: ResearchEventBreakingNewsSensitivityRow) -> str:
    return _payload_digest(_public_row_digest_payload(row))


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    return sha256(
        json.dumps(
            _payload_value(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()


def _verify_public_payload_integrity(payload: Mapping[str, Any]) -> None:
    _validate_public_report_payload_schema(payload)
    digest = payload["derived_validation_digest"]
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _payload_digest(unsigned_payload):
        raise ValueError("derived_validation_digest does not match payload")
    for row in payload["rows"]:
        row_digest = row["derived_validation_digest"]
        row_unsigned = {
            key: value
            for key, value in row.items()
            if key not in {"derived_validation_digest", "row_number"}
        }
        if row_digest != _payload_digest(row_unsigned):
            raise ValueError("derived_validation_digest does not match row payload")


def _validate_public_report_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_public_keys("payload", payload, _REPORT_PUBLIC_KEYS)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in _REPORT_PUBLIC_COUNT_FIELDS:
        _require_public_nonnegative_decimal_string(field_name, payload[field_name])
    for field_name in _REPORT_PUBLIC_RATIO_FIELDS:
        _require_public_ratio_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _normalize_report_reason_codes(
        _require_public_string_list("reason_codes", payload["reason_codes"]),
    )
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for index, value in enumerate(payload["reason_code_counts"], start=1):
        _validate_public_reason_code_count_payload(
            f"reason_code_counts[{index}]",
            value,
        )
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for index, value in enumerate(payload["rows"], start=1):
        _validate_public_row_payload(f"rows[{index}]", value, index)
    _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )


def _validate_public_reason_code_count_payload(
    field_name: str,
    payload: object,
) -> None:
    _require_public_keys(field_name, payload, _REASON_CODE_COUNT_PUBLIC_KEYS)
    _require_hard_flags(field_name, _DictFlags(payload))
    _require_reason_code(f"{field_name}.reason_code", payload["reason_code"])
    _require_public_nonnegative_decimal_string(f"{field_name}.count", payload["count"])
    _require_public_ratio_decimal_string(f"{field_name}.input_ratio", payload["input_ratio"])


def _validate_public_row_payload(
    field_name: str,
    payload: object,
    expected_row_number: int,
) -> None:
    _require_public_keys(field_name, payload, _ROW_PUBLIC_KEYS)
    _require_hard_flags(field_name, _DictFlags(payload))
    _require_public_datetime_string(f"{field_name}.observed_at", payload["observed_at"])
    _require_public_nonnegative_decimal_string(
        f"{field_name}.update_count_1h",
        payload["update_count_1h"],
    )
    for ratio_field_name in _ROW_PUBLIC_RATIO_FIELDS:
        _require_public_ratio_decimal_string(
            f"{field_name}.{ratio_field_name}",
            payload[ratio_field_name],
        )
    _require_status(f"{field_name}.status", payload["status"])
    _normalize_row_reason_codes(
        _require_public_string_list(f"{field_name}.reason_codes", payload["reason_codes"]),
    )
    if payload["row_number"] != _payload_value(_count(expected_row_number)):
        raise ValueError(f"{field_name}.row_number must match row order")
    _require_sha256_digest(
        f"{field_name}.derived_validation_digest",
        payload["derived_validation_digest"],
    )


def _require_public_keys(
    field_name: str,
    payload: object,
    allowed_keys: frozenset[str],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    if set(payload) != allowed_keys:
        raise ValueError(f"{field_name} must contain only supported public keys")


def _require_public_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    values = tuple(value)
    for item in values:
        _require_public_string(field_name, item)
    return values


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    parsed_utc = _as_utc(field_name, parsed)
    if value != parsed_utc.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return parsed_utc


def _require_public_nonnegative_decimal_string(field_name: str, value: object) -> Decimal:
    parsed = _require_public_decimal_string(field_name, value)
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return parsed


def _require_public_ratio_decimal_string(field_name: str, value: object) -> Decimal:
    parsed = _require_public_decimal_string(field_name, value)
    if parsed < ZERO or parsed > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return parsed


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = _quantize(Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if value != format(parsed, "f"):
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return parsed


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("decimal values must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_internal_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_public_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in RESEARCH_EVENT_BREAKING_NEWS_SENSITIVITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain a supported reason code")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, ROW_REASON_CODES, "row reason_codes")


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, REPORT_REASON_CODES, "report reason_codes")


def _normalize_reason_codes(
    value: object,
    allowed_reason_codes: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{label} must be a tuple or list")
    values = tuple(value)
    if not values:
        raise ValueError(f"{label} must be non-empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{label} contains unsupported reason code")
    return values


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{field_name}.{flag_name} must be present")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be exactly True")


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
    *,
    allow_mapping: bool = False,
) -> None:
    if type(value) is str:
        _reject_unsafe_public_string(field_name, value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item, allow_mapping=allow_mapping)
        return
    if allow_mapping and isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_string(f"{field_name} key", str(key))
            _reject_unsafe_public_payload(field_name, item, allow_mapping=True)
        return
    if type(value) is ResearchEventBreakingNewsSensitivityConfig:
        for public_value in (
            value.config_version,
            value.pass_update_count_1h_ceiling,
            value.watch_update_count_1h_ceiling,
            value.pass_authority_mix_floor,
            value.watch_authority_mix_floor,
            value.pass_contradiction_pressure_ceiling,
            value.watch_contradiction_pressure_ceiling,
            value.pass_probability_movement_ceiling,
            value.watch_probability_movement_ceiling,
            value.pass_liquidity_reliability_floor,
            value.watch_liquidity_reliability_floor,
            value.pass_hours_to_resolution_floor,
            value.watch_hours_to_resolution_floor,
        ):
            _reject_unsafe_public_payload(field_name, public_value)
        return
    if type(value) is ResearchEventBreakingNewsSensitivityReport:
        _reject_unsafe_public_payload(
            field_name,
            _public_report_payload(value, include_digest=True),
            allow_mapping=True,
        )
        return
    raise ValueError(f"{field_name} contains unsupported public payload value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} must not expose unsafe public surface")
