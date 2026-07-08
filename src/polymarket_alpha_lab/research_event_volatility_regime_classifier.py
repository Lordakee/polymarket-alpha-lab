"""Pure local event volatility regime classifier for human research review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION",
    "ResearchEventVolatilityRegimeClassifierConfig",
    "ResearchEventVolatilityRegimeClassifierObservation",
    "ResearchEventVolatilityRegimeClassifierReasonCodeCount",
    "ResearchEventVolatilityRegimeClassifierReport",
    "ResearchEventVolatilityRegimeClassifierRow",
    "build_research_event_volatility_regime_classifier_report",
    "research_event_volatility_regime_classifier_payload",
)


DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION = (
    "research-event-volatility-regime-classifier-v0"
)
DIGEST_PREFIX = "event-volatility-regime-classifier-v0:"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
VOLATILITY_REGIMES = ("baseline", "elevated", "stress")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "event_volatility_regime_classifier_no_inputs"


@dataclass(frozen=True)
class ResearchEventVolatilityRegimeClassifierConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION
    )
    event_information_weight: Decimal = Decimal("0.350000")
    liquidity_weight: Decimal = Decimal("0.250000")
    time_window_weight: Decimal = Decimal("0.200000")
    historical_volatility_weight: Decimal = Decimal("0.200000")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.650000")
    event_information_watch: Decimal = Decimal("0.550000")
    event_information_block: Decimal = Decimal("0.850000")
    liquidity_watch: Decimal = Decimal("0.550000")
    liquidity_block: Decimal = Decimal("0.850000")
    time_window_watch: Decimal = Decimal("0.600000")
    time_window_block: Decimal = Decimal("0.900000")
    historical_volatility_watch: Decimal = Decimal("0.500000")
    historical_volatility_block: Decimal = Decimal("0.800000")
    fresh_information_max_age_seconds: Decimal = Decimal("7200.000000")
    stale_information_block_age_seconds: Decimal = Decimal("43200.000000")
    watch_confidence_cap: Decimal = Decimal("0.750000")
    block_confidence_cap: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventVolatilityRegimeClassifierConfig:
            raise TypeError(
                "ResearchEventVolatilityRegimeClassifierConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventVolatilityRegimeClassifierConfig:
            raise ValueError(
                "config must be exactly ResearchEventVolatilityRegimeClassifierConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_information_weight",
            "liquidity_weight",
            "time_window_weight",
            "historical_volatility_weight",
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "event_information_watch",
            "event_information_block",
            "liquidity_watch",
            "liquidity_block",
            "time_window_watch",
            "time_window_block",
            "historical_volatility_watch",
            "historical_volatility_block",
            "watch_confidence_cap",
            "block_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_information_max_age_seconds",
            "stale_information_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "watch_pressure_threshold",
            self.watch_pressure_threshold,
            self.block_pressure_threshold,
        )
        _require_at_most(
            "event_information_watch",
            self.event_information_watch,
            self.event_information_block,
        )
        _require_at_most("liquidity_watch", self.liquidity_watch, self.liquidity_block)
        _require_at_most(
            "time_window_watch",
            self.time_window_watch,
            self.time_window_block,
        )
        _require_at_most(
            "historical_volatility_watch",
            self.historical_volatility_watch,
            self.historical_volatility_block,
        )
        if (
            self.fresh_information_max_age_seconds
            >= self.stale_information_block_age_seconds
        ):
            raise ValueError(
                "stale_information_block_age_seconds must exceed "
                "fresh_information_max_age_seconds",
            )
        if self.block_confidence_cap > self.watch_confidence_cap:
            raise ValueError("block_confidence_cap must not exceed watch_confidence_cap")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventVolatilityRegimeClassifierObservation:
    event_reference: str
    event_family: str
    observed_at: datetime
    event_information_shock_score: Decimal
    liquidity_stress_score: Decimal
    time_window_urgency_score: Decimal
    historical_volatility_score: Decimal
    base_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventVolatilityRegimeClassifierObservation:
            raise TypeError(
                "ResearchEventVolatilityRegimeClassifierObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventVolatilityRegimeClassifierObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchEventVolatilityRegimeClassifierObservation",
            )
        _require_private_reference("event_reference", self.event_reference)
        _require_public_string("event_family", self.event_family)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "event_information_shock_score",
            "liquidity_stress_score",
            "time_window_urgency_score",
            "historical_volatility_score",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventVolatilityRegimeClassifierRow:
    event_family: str
    observed_at: datetime
    information_age_seconds: Decimal
    event_information_shock_score: Decimal
    liquidity_stress_score: Decimal
    time_window_urgency_score: Decimal
    historical_volatility_score: Decimal
    base_confidence: Decimal
    freshness_score: Decimal
    volatility_pressure_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    volatility_regime: str
    status: str
    public_status: str
    human_review_state: str
    hard_flag: bool
    reason_codes: tuple[str, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventVolatilityRegimeClassifierRow:
            raise TypeError(
                "ResearchEventVolatilityRegimeClassifierRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventVolatilityRegimeClassifierRow:
            raise ValueError(
                "row must be exactly ResearchEventVolatilityRegimeClassifierRow",
            )
        _require_public_string("event_family", self.event_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "event_information_shock_score",
            "liquidity_stress_score",
            "time_window_urgency_score",
            "historical_volatility_score",
            "base_confidence",
            "freshness_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "information_age_seconds",
            "volatility_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("volatility_regime", self.volatility_regime, VOLATILITY_REGIMES)
        _require_status("status", self.status)
        _require_status("public_status", self.public_status)
        _require_status("human_review_state", self.human_review_state)
        if self.status != self.public_status or self.status != self.human_review_state:
            raise ValueError("public and human review statuses must match status")
        if type(self.hard_flag) is not bool:
            raise ValueError("hard_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("row digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


@dataclass(frozen=True)
class ResearchEventVolatilityRegimeClassifierReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventVolatilityRegimeClassifierReasonCodeCount:
            raise TypeError(
                "ResearchEventVolatilityRegimeClassifierReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventVolatilityRegimeClassifierReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchEventVolatilityRegimeClassifierReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventVolatilityRegimeClassifierReport:
    generated_at: datetime
    config_version: str
    subject_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    stale_information_count: Decimal
    event_information_shock_count: Decimal
    liquidity_stress_count: Decimal
    urgent_window_count: Decimal
    historical_volatility_count: Decimal
    average_volatility_pressure_score: Decimal
    max_volatility_pressure_score: Decimal
    average_information_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventVolatilityRegimeClassifierReasonCodeCount, ...]
    rows: tuple[ResearchEventVolatilityRegimeClassifierRow, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventVolatilityRegimeClassifierReport:
            raise TypeError(
                "ResearchEventVolatilityRegimeClassifierReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventVolatilityRegimeClassifierReport:
            raise ValueError(
                "report must be exactly ResearchEventVolatilityRegimeClassifierReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "subject_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "stale_information_count",
            "event_information_shock_count",
            "liquidity_stress_count",
            "urgent_window_count",
            "historical_volatility_count",
            "average_volatility_pressure_score",
            "max_volatility_pressure_score",
            "average_information_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("report digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


_PUBLIC_DATACLASS_TYPES = (
    ResearchEventVolatilityRegimeClassifierConfig,
    ResearchEventVolatilityRegimeClassifierReasonCodeCount,
    ResearchEventVolatilityRegimeClassifierReport,
    ResearchEventVolatilityRegimeClassifierRow,
)


def build_research_event_volatility_regime_classifier_report(
    observations: Iterable[ResearchEventVolatilityRegimeClassifierObservation],
    *,
    config: ResearchEventVolatilityRegimeClassifierConfig,
    generated_at: datetime,
) -> ResearchEventVolatilityRegimeClassifierReport:
    if type(config) is not ResearchEventVolatilityRegimeClassifierConfig:
        raise ValueError(
            "config must be a ResearchEventVolatilityRegimeClassifierConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _build_row(row, config=config, generated_at=generated_at_utc)
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventVolatilityRegimeClassifierReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        subject_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_flag_count=_count(sum(1 for row in rows if row.hard_flag)),
        stale_information_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "information_age_")),
        ),
        event_information_shock_count=_count(
            sum(
                1
                for row in rows
                if _has_reason_prefix(row, "event_information_shock_")
                and not _has_reason(row, "event_information_shock_clear")
            ),
        ),
        liquidity_stress_count=_count(
            sum(
                1
                for row in rows
                if _has_reason_prefix(row, "liquidity_stress_")
                and not _has_reason(row, "liquidity_stress_clear")
            ),
        ),
        urgent_window_count=_count(
            sum(
                1
                for row in rows
                if _has_reason_prefix(row, "time_window_")
                and not _has_reason(row, "time_window_clear")
            ),
        ),
        historical_volatility_count=_count(
            sum(1 for row in rows if _has_reason_prefix(row, "historical_volatility_")),
        ),
        average_volatility_pressure_score=_mean(
            tuple(row.volatility_pressure_score for row in rows),
        ),
        max_volatility_pressure_score=_max_decimal(
            tuple(row.volatility_pressure_score for row in rows),
        ),
        average_information_age_seconds=_mean(
            tuple(row.information_age_seconds for row in rows),
        ),
        status=_rollup_status(tuple(row.status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_event_volatility_regime_classifier_payload(
    report: ResearchEventVolatilityRegimeClassifierReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventVolatilityRegimeClassifierReport:
        raise ValueError(
            "report must be a ResearchEventVolatilityRegimeClassifierReport",
        )
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _build_row(
    observation: ResearchEventVolatilityRegimeClassifierObservation,
    *,
    config: ResearchEventVolatilityRegimeClassifierConfig,
    generated_at: datetime,
) -> ResearchEventVolatilityRegimeClassifierRow:
    information_age_seconds = _information_age_seconds(observation.observed_at, generated_at)
    freshness_score = _freshness_score(information_age_seconds, config)
    volatility_pressure_score = _volatility_pressure_score(observation, config=config)
    hard_flag = _hard_flag(
        observation,
        information_age_seconds=information_age_seconds,
        config=config,
    )
    status = _row_status(
        observation,
        information_age_seconds=information_age_seconds,
        volatility_pressure_score=volatility_pressure_score,
        hard_flag=hard_flag,
        config=config,
    )
    return ResearchEventVolatilityRegimeClassifierRow(
        event_family=observation.event_family,
        observed_at=observation.observed_at,
        information_age_seconds=information_age_seconds,
        event_information_shock_score=observation.event_information_shock_score,
        liquidity_stress_score=observation.liquidity_stress_score,
        time_window_urgency_score=observation.time_window_urgency_score,
        historical_volatility_score=observation.historical_volatility_score,
        base_confidence=observation.base_confidence,
        freshness_score=freshness_score,
        volatility_pressure_score=volatility_pressure_score,
        confidence_cap=_confidence_cap(status, config=config),
        capped_confidence=min(
            observation.base_confidence,
            _confidence_cap(status, config=config),
        ),
        volatility_regime=_volatility_regime(status),
        status=status,
        public_status=status,
        human_review_state=status,
        hard_flag=hard_flag,
        reason_codes=_row_reason_codes(
            observation,
            information_age_seconds=information_age_seconds,
            status=status,
            config=config,
        ),
    )


def _volatility_pressure_score(
    observation: ResearchEventVolatilityRegimeClassifierObservation,
    *,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> Decimal:
    return _quantize(
        observation.event_information_shock_score * config.event_information_weight
        + observation.liquidity_stress_score * config.liquidity_weight
        + observation.time_window_urgency_score * config.time_window_weight
        + observation.historical_volatility_score
        * config.historical_volatility_weight,
    )


def _freshness_score(
    information_age_seconds: Decimal,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> Decimal:
    if information_age_seconds <= config.fresh_information_max_age_seconds:
        return ONE
    if information_age_seconds >= config.stale_information_block_age_seconds:
        return ZERO
    stale_range = _quantize(
        config.stale_information_block_age_seconds
        - config.fresh_information_max_age_seconds,
    )
    stale_delta = _quantize(
        information_age_seconds - config.fresh_information_max_age_seconds,
    )
    return _quantize(ONE - stale_delta / stale_range)


def _hard_flag(
    observation: ResearchEventVolatilityRegimeClassifierObservation,
    *,
    information_age_seconds: Decimal,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> bool:
    return (
        observation.event_information_shock_score >= config.event_information_block
        or observation.liquidity_stress_score >= config.liquidity_block
        or observation.time_window_urgency_score >= config.time_window_block
        or observation.historical_volatility_score >= config.historical_volatility_block
        or information_age_seconds >= config.stale_information_block_age_seconds
    )


def _row_status(
    observation: ResearchEventVolatilityRegimeClassifierObservation,
    *,
    information_age_seconds: Decimal,
    volatility_pressure_score: Decimal,
    hard_flag: bool,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> str:
    if hard_flag or volatility_pressure_score >= config.block_pressure_threshold:
        return "block"
    if (
        volatility_pressure_score >= config.watch_pressure_threshold
        or observation.event_information_shock_score >= config.event_information_watch
        or observation.liquidity_stress_score >= config.liquidity_watch
        or observation.time_window_urgency_score >= config.time_window_watch
        or observation.historical_volatility_score >= config.historical_volatility_watch
        or information_age_seconds > config.fresh_information_max_age_seconds
    ):
        return "watch"
    return "pass"


def _confidence_cap(
    status: str,
    *,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> Decimal:
    if status == "block":
        return config.block_confidence_cap
    if status == "watch":
        return config.watch_confidence_cap
    return ONE


def _volatility_regime(status: str) -> str:
    if status == "block":
        return "stress"
    if status == "watch":
        return "elevated"
    return "baseline"


def _row_reason_codes(
    observation: ResearchEventVolatilityRegimeClassifierObservation,
    *,
    information_age_seconds: Decimal,
    status: str,
    config: ResearchEventVolatilityRegimeClassifierConfig,
) -> tuple[str, ...]:
    reason_codes = list(observation.reason_codes)
    if information_age_seconds >= config.stale_information_block_age_seconds:
        reason_codes.append("information_age_block")
    elif information_age_seconds > config.fresh_information_max_age_seconds:
        reason_codes.append("information_age_watch")
    else:
        reason_codes.append("fresh_information")
    if observation.event_information_shock_score >= config.event_information_block:
        reason_codes.append("event_information_shock_block")
    elif observation.event_information_shock_score >= config.event_information_watch:
        reason_codes.append("event_information_shock_watch")
    else:
        reason_codes.append("event_information_shock_clear")
    if observation.liquidity_stress_score >= config.liquidity_block:
        reason_codes.append("liquidity_stress_block")
    elif observation.liquidity_stress_score >= config.liquidity_watch:
        reason_codes.append("liquidity_stress_watch")
    else:
        reason_codes.append("liquidity_stress_clear")
    if observation.time_window_urgency_score >= config.time_window_block:
        reason_codes.append("time_window_block")
    elif observation.time_window_urgency_score >= config.time_window_watch:
        reason_codes.append("time_window_watch")
    else:
        reason_codes.append("time_window_clear")
    if observation.historical_volatility_score >= config.historical_volatility_block:
        reason_codes.append("historical_volatility_block")
    elif observation.historical_volatility_score >= config.historical_volatility_watch:
        reason_codes.append("historical_volatility_watch")
    else:
        reason_codes.append("historical_volatility_clear")
    reason_codes.append(f"event_volatility_regime_classifier_{status}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))))


def _information_age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - _as_utc("observed_at", observed_at)).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    observations: Iterable[ResearchEventVolatilityRegimeClassifierObservation],
) -> tuple[ResearchEventVolatilityRegimeClassifierObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_references: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventVolatilityRegimeClassifierObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventVolatilityRegimeClassifierObservation values",
            )
        _require_hard_flags("observation", row)
        if row.event_reference in seen_references:
            raise ValueError("observations must not contain duplicate event_reference values")
        seen_references.add(row.event_reference)
    return tuple(sorted(rows, key=lambda row: row.event_reference))


def _normalize_rows(
    rows: Iterable[ResearchEventVolatilityRegimeClassifierRow],
) -> tuple[ResearchEventVolatilityRegimeClassifierRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchEventVolatilityRegimeClassifierRow:
            raise ValueError(
                "rows must contain ResearchEventVolatilityRegimeClassifierRow values",
            )
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchEventVolatilityRegimeClassifierReasonCodeCount],
) -> tuple[ResearchEventVolatilityRegimeClassifierReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchEventVolatilityRegimeClassifierReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventVolatilityRegimeClassifierReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: ResearchEventVolatilityRegimeClassifierRow,
) -> tuple[Decimal, Decimal, str, datetime, tuple[str, ...]]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.volatility_pressure_score,
        row.event_family,
        row.observed_at,
        row.reason_codes,
    )


def _status_count(
    rows: tuple[ResearchEventVolatilityRegimeClassifierRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ResearchEventVolatilityRegimeClassifierRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"event_volatility_regime_classifier_{status}"]
    row_reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    for reason_code in (
        "information_age_block",
        "information_age_watch",
        "event_information_shock_block",
        "event_information_shock_watch",
        "liquidity_stress_block",
        "liquidity_stress_watch",
        "time_window_block",
        "time_window_watch",
        "historical_volatility_block",
        "historical_volatility_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventVolatilityRegimeClassifierRow, ...],
) -> tuple[ResearchEventVolatilityRegimeClassifierReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventVolatilityRegimeClassifierReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchEventVolatilityRegimeClassifierReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_row(row: ResearchEventVolatilityRegimeClassifierRow) -> None:
    expected_score = _quantize(
        row.event_information_shock_score * Decimal("0.350000")
        + row.liquidity_stress_score * Decimal("0.250000")
        + row.time_window_urgency_score * Decimal("0.200000")
        + row.historical_volatility_score * Decimal("0.200000"),
    )
    if row.volatility_pressure_score != expected_score:
        raise ValueError("volatility_pressure_score must match row signals")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    if row.capped_confidence > row.base_confidence:
        raise ValueError("capped_confidence must not exceed base_confidence")
    if row.volatility_regime != _volatility_regime(row.status):
        raise ValueError("volatility_regime must match status")
    if f"event_volatility_regime_classifier_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventVolatilityRegimeClassifierReport) -> None:
    rows = report.rows
    if report.subject_count != _count(len(rows)):
        raise ValueError("subject_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.hard_flag_count != _count(sum(1 for row in rows if row.hard_flag)):
        raise ValueError("hard_flag_count must match rows")
    if report.stale_information_count != _count(
        sum(1 for row in rows if _has_reason_prefix(row, "information_age_")),
    ):
        raise ValueError("stale_information_count must match rows")
    if report.event_information_shock_count != _count(
        sum(
            1
            for row in rows
            if _has_reason_prefix(row, "event_information_shock_")
            and not _has_reason(row, "event_information_shock_clear")
        ),
    ):
        raise ValueError("event_information_shock_count must match rows")
    if report.liquidity_stress_count != _count(
        sum(
            1
            for row in rows
            if _has_reason_prefix(row, "liquidity_stress_")
            and not _has_reason(row, "liquidity_stress_clear")
        ),
    ):
        raise ValueError("liquidity_stress_count must match rows")
    if report.urgent_window_count != _count(
        sum(
            1
            for row in rows
            if _has_reason_prefix(row, "time_window_")
            and not _has_reason(row, "time_window_clear")
        ),
    ):
        raise ValueError("urgent_window_count must match rows")
    if report.historical_volatility_count != _count(
        sum(1 for row in rows if _has_reason_prefix(row, "historical_volatility_")),
    ):
        raise ValueError("historical_volatility_count must match rows")
    if report.average_volatility_pressure_score != _mean(
        tuple(row.volatility_pressure_score for row in rows),
    ):
        raise ValueError("average_volatility_pressure_score must match rows")
    if report.max_volatility_pressure_score != _max_decimal(
        tuple(row.volatility_pressure_score for row in rows),
    ):
        raise ValueError("max_volatility_pressure_score must match rows")
    if report.average_information_age_seconds != _mean(
        tuple(row.information_age_seconds for row in rows),
    ):
        raise ValueError("average_information_age_seconds must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _has_reason(row: ResearchEventVolatilityRegimeClassifierRow, reason_code: str) -> bool:
    return reason_code in row.reason_codes


def _has_reason_prefix(
    row: ResearchEventVolatilityRegimeClassifierRow,
    reason_prefix: str,
) -> bool:
    return any(reason_code.startswith(reason_prefix) for reason_code in row.reason_codes)


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation: {exc}") from exc


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _row_digest(row: ResearchEventVolatilityRegimeClassifierRow) -> str:
    return _digest_from_public_value(row)


def _report_digest(report: ResearchEventVolatilityRegimeClassifierReport) -> str:
    return _digest_from_public_value(report)


def _digest_from_public_value(value: object) -> str:
    canonical_payload = _digest_ready(value)
    encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return f"{DIGEST_PREFIX}{sha256(encoded.encode('utf-8')).hexdigest()}"


def _digest_ready(value: object) -> object:
    if type(value) is Decimal:
        _require_six_decimal_decimal("digest Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("digest datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("digest value contains unsupported dataclass")
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "digest"
        }
    if type(value) is tuple:
        return [_digest_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("value is not digest serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe or sensitive value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe or sensitive field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "raw" + "_" + "candidate",
        "raw" + " " + "candidate",
        "candidate" + "_" + "id",
        "candidate" + " " + "id",
        "market" + "_" + "id",
        "market" + " " + "id",
        "market" + "_" + "slug",
        "market" + " " + "slug",
        "ques" + "tion",
        "source" + "_" + "ref",
        "source" + " " + "ref",
        "source" + "_" + "url",
        "source" + " " + "url",
        "source" + "_" + "text",
        "source" + " " + "text",
        "d" + "sn",
        "tab" + "le",
        "tok" + "en",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tr" + "ade",
        "pos" + "ition",
        "b" + "uy",
        "se" + "ll",
        "recom" + "mendation",
        "://",
        "www.",
    )


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _unsafe_fragments())


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_private_reference(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe or sensitive value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _require_digest(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if not value.startswith(DIGEST_PREFIX) or len(value) != len(DIGEST_PREFIX) + 64:
        raise ValueError(f"{field_name} must use the digest format")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
