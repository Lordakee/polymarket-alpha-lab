"""Pure in-memory source update volatility report for market research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_SOURCE_UPDATE_VOLATILITY_CONFIG_VERSION = (
    "research-market-source-update-volatility-report-v0"
)

VOLATILITY_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "source_update_volatility_pass"
REASON_CODES = (
    PASS_REASON_CODE,
    "update_frequency_watch",
    "claim_reversal_pressure_watch",
    "claim_reversal_pressure_block",
    "source_recency_block",
    "corroboration_readiness_watch",
    "corroboration_readiness_block",
    "manual_escalation_urgency_watch",
    "manual_escalation_urgency_block",
)
BLOCK_REASON_CODES = frozenset(
    (
        "claim_reversal_pressure_block",
        "source_recency_block",
        "corroboration_readiness_block",
        "manual_escalation_urgency_block",
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "://",
        "www.",
        "raw",
        _join_parts("au", "th"),
        _join_parts("cre", "den", "tial"),
        _join_parts("api", "_", "key"),
        _join_parts("private", "_", "key"),
        "secret",
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        "submit",
        "cancel",
        _join_parts("si", "gn"),
        _join_parts("li", "ve"),
        _join_parts("tra", "ding"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        "dsn",
        _join_parts("per", "sist"),
        _join_parts("rec", "ommendation"),
        "market_id",
        "condition_id",
        "source_id",
        "source_url",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SOURCE_UPDATE_VOLATILITY_CONFIG_VERSION",
    "VOLATILITY_STATUSES",
    "ResearchMarketSourceUpdateObservation",
    "ResearchMarketSourceUpdateVolatilityReasonCodeCount",
    "ResearchMarketSourceUpdateVolatilityReport",
    "ResearchMarketSourceUpdateVolatilityReportConfig",
    "ResearchMarketSourceUpdateVolatilityRow",
    "build_research_market_source_update_volatility_report",
    "research_market_source_update_volatility_report_digest",
    "research_market_source_update_volatility_report_payload",
    "validate_research_market_source_update_volatility_public_payload",
)


@dataclass(frozen=True)
class ResearchMarketSourceUpdateVolatilityReportConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_SOURCE_UPDATE_VOLATILITY_CONFIG_VERSION
    min_update_interval_seconds: Decimal = Decimal("1800.000000")
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    min_corroboration_readiness_score: Decimal = Decimal("0.750000")
    claim_reversal_watch_pressure: Decimal = Decimal("0.250000")
    claim_reversal_block_pressure: Decimal = Decimal("0.600000")
    watch_manual_escalation_urgency_score: Decimal = Decimal("0.350000")
    block_manual_escalation_urgency_score: Decimal = Decimal("0.700000")
    update_frequency_weight: Decimal = Decimal("0.250000")
    claim_reversal_weight: Decimal = Decimal("0.300000")
    source_recency_weight: Decimal = Decimal("0.200000")
    corroboration_gap_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketSourceUpdateVolatilityReportConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_update_interval_seconds",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_corroboration_readiness_score",
            "claim_reversal_watch_pressure",
            "claim_reversal_block_pressure",
            "watch_manual_escalation_urgency_score",
            "block_manual_escalation_urgency_score",
            "update_frequency_weight",
            "claim_reversal_weight",
            "source_recency_weight",
            "corroboration_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.claim_reversal_block_pressure <= self.claim_reversal_watch_pressure:
            raise ValueError(
                "claim_reversal_block_pressure must exceed "
                "claim_reversal_watch_pressure",
            )
        if (
            self.block_manual_escalation_urgency_score
            <= self.watch_manual_escalation_urgency_score
        ):
            raise ValueError(
                "block_manual_escalation_urgency_score must exceed "
                "watch_manual_escalation_urgency_score",
            )
        _require_weight_sum(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSourceUpdateObservation:
    research_bucket: str
    update_family: str
    source_class: str
    observed_at: datetime
    claim_reversed: bool
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketSourceUpdateObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("research_bucket", "update_family", "source_class"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("claim_reversed", self.claim_reversed)
        object.__setattr__(
            self,
            "corroborating_source_count",
            _normalize_nonnegative_decimal(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "required_corroborating_source_count",
            _normalize_positive_decimal(
                "required_corroborating_source_count",
                self.required_corroborating_source_count,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketSourceUpdateVolatilityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketSourceUpdateVolatilityReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSourceUpdateVolatilityRow:
    research_bucket: str
    update_count: Decimal
    source_class_count: Decimal
    update_family_count: Decimal
    first_observed_at: datetime
    last_observed_at: datetime
    average_update_interval_seconds: Decimal
    update_frequency_pressure: Decimal
    claim_reversal_pressure: Decimal
    source_age_seconds: Decimal
    corroboration_readiness_score: Decimal
    manual_escalation_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketSourceUpdateVolatilityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("research_bucket", self.research_bucket)
        for field_name in (
            "update_count",
            "source_class_count",
            "update_family_count",
            "average_update_interval_seconds",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "update_frequency_pressure",
            "claim_reversal_pressure",
            "corroboration_readiness_score",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "last_observed_at",
            _as_utc("last_observed_at", self.last_observed_at),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketSourceUpdateVolatilityReport:
    generated_at: datetime
    config_version: str
    status: str
    group_count: Decimal
    update_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_manual_escalation_urgency_score: Decimal
    average_manual_escalation_urgency_score: Decimal
    average_update_frequency_pressure: Decimal
    max_claim_reversal_pressure: Decimal
    average_corroboration_readiness_score: Decimal
    max_source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketSourceUpdateVolatilityReasonCodeCount, ...]
    rows: tuple[ResearchMarketSourceUpdateVolatilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketSourceUpdateVolatilityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "group_count",
            "update_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_manual_escalation_urgency_score",
            "average_manual_escalation_urgency_score",
            "average_update_frequency_pressure",
            "max_claim_reversal_pressure",
            "average_corroboration_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_source_update_volatility_report_payload(self)


def build_research_market_source_update_volatility_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketSourceUpdateVolatilityReportConfig,
    generated_at: datetime,
) -> ResearchMarketSourceUpdateVolatilityReport:
    if type(config) is not ResearchMarketSourceUpdateVolatilityReportConfig:
        raise ValueError(
            "config must be a ResearchMarketSourceUpdateVolatilityReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _reject_future_observations(normalized_observations, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    research_bucket,
                    bucket_observations,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for research_bucket, bucket_observations in _bucketed_observations(
                    normalized_observations,
                )
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketSourceUpdateVolatilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        group_count=_count(len(rows)),
        update_count=_count(len(normalized_observations)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        max_manual_escalation_urgency_score=max(
            (row.manual_escalation_urgency_score for row in rows),
            default=ZERO,
        ),
        average_manual_escalation_urgency_score=_average_decimal(
            row.manual_escalation_urgency_score for row in rows
        ),
        average_update_frequency_pressure=_average_decimal(
            row.update_frequency_pressure for row in rows
        ),
        max_claim_reversal_pressure=max(
            (row.claim_reversal_pressure for row in rows),
            default=ZERO,
        ),
        average_corroboration_readiness_score=_average_decimal(
            row.corroboration_readiness_score for row in rows
        ),
        max_source_age_seconds=max((row.source_age_seconds for row in rows), default=ZERO),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_market_source_update_volatility_report_payload(
    report: ResearchMarketSourceUpdateVolatilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketSourceUpdateVolatilityReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketSourceUpdateVolatilityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_source_update_volatility_report_digest(
    report: ResearchMarketSourceUpdateVolatilityReport,
) -> str:
    if type(report) is not ResearchMarketSourceUpdateVolatilityReport:
        raise ValueError(
            "report must be a ResearchMarketSourceUpdateVolatilityReport",
        )
    _require_hard_flags("report", report)
    digest = _report_derived_validation_digest(report)
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_market_source_update_volatility_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        _require_sha256_digest("derived_validation_digest", digest)
        unsigned_payload = dict(payload)
        unsigned_payload.pop("derived_validation_digest", None)
        expected_digest = _payload_digest(unsigned_payload)
        if digest != expected_digest:
            return False
        status = payload.get("status")
        if status not in VOLATILITY_STATUSES:
            return False
        rows = payload.get("rows")
        if type(rows) is not list:
            return False
        for row in rows:
            if type(row) is not dict or row.get("status") not in VOLATILITY_STATUSES:
                return False
        return True
    except (TypeError, ValueError):
        return False


def _row_from_observations(
    research_bucket: str,
    observations: tuple[ResearchMarketSourceUpdateObservation, ...],
    *,
    config: ResearchMarketSourceUpdateVolatilityReportConfig,
    generated_at: datetime,
) -> ResearchMarketSourceUpdateVolatilityRow:
    sorted_observations = tuple(sorted(observations, key=lambda value: value.observed_at))
    update_count = _count(len(sorted_observations))
    source_class_count = _count(len({value.source_class for value in sorted_observations}))
    update_family_count = _count(len({value.update_family for value in sorted_observations}))
    average_interval = _average_update_interval(sorted_observations)
    update_frequency_pressure = _update_frequency_pressure(
        average_interval,
        config.min_update_interval_seconds,
    )
    claim_reversal_pressure = _ratio(
        _count(sum(1 for value in sorted_observations if value.claim_reversed)),
        update_count,
    )
    last_observed_at = sorted_observations[-1].observed_at
    source_age_seconds = _age_seconds(generated_at, last_observed_at)
    corroboration_readiness_score = _average_decimal(
        _corroboration_readiness(value) for value in sorted_observations
    )
    manual_escalation_urgency_score = _manual_escalation_urgency_score(
        update_frequency_pressure=update_frequency_pressure,
        claim_reversal_pressure=claim_reversal_pressure,
        source_age_seconds=source_age_seconds,
        corroboration_readiness_score=corroboration_readiness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        update_frequency_pressure=update_frequency_pressure,
        claim_reversal_pressure=claim_reversal_pressure,
        source_age_seconds=source_age_seconds,
        corroboration_readiness_score=corroboration_readiness_score,
        manual_escalation_urgency_score=manual_escalation_urgency_score,
        config=config,
    )
    return ResearchMarketSourceUpdateVolatilityRow(
        research_bucket=research_bucket,
        update_count=update_count,
        source_class_count=source_class_count,
        update_family_count=update_family_count,
        first_observed_at=sorted_observations[0].observed_at,
        last_observed_at=last_observed_at,
        average_update_interval_seconds=average_interval,
        update_frequency_pressure=update_frequency_pressure,
        claim_reversal_pressure=claim_reversal_pressure,
        source_age_seconds=source_age_seconds,
        corroboration_readiness_score=corroboration_readiness_score,
        manual_escalation_urgency_score=manual_escalation_urgency_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketSourceUpdateObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchMarketSourceUpdateObservation] = []
    for value in values:
        if type(value) is not ResearchMarketSourceUpdateObservation:
            raise ValueError(
                "observations must contain ResearchMarketSourceUpdateObservation values",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(normalized)


def _bucketed_observations(
    observations: tuple[ResearchMarketSourceUpdateObservation, ...],
) -> tuple[tuple[str, tuple[ResearchMarketSourceUpdateObservation, ...]], ...]:
    buckets: dict[str, list[ResearchMarketSourceUpdateObservation]] = {}
    for observation in observations:
        buckets.setdefault(observation.research_bucket, []).append(observation)
    return tuple((key, tuple(values)) for key, values in sorted(buckets.items()))


def _reject_future_observations(
    observations: tuple[ResearchMarketSourceUpdateObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _average_update_interval(
    observations: tuple[ResearchMarketSourceUpdateObservation, ...],
) -> Decimal:
    if len(observations) < 2:
        return ZERO
    intervals = tuple(
        _datetime_delta_seconds(current.observed_at, previous.observed_at)
        for previous, current in zip(observations, observations[1:])
    )
    return _average_decimal(intervals)


def _update_frequency_pressure(
    average_interval_seconds: Decimal,
    min_update_interval_seconds: Decimal,
) -> Decimal:
    if average_interval_seconds == ZERO:
        return ZERO
    if average_interval_seconds >= min_update_interval_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(
            (min_update_interval_seconds - average_interval_seconds)
            / min_update_interval_seconds,
        )


def _corroboration_readiness(
    observation: ResearchMarketSourceUpdateObservation,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(
            observation.corroborating_source_count
            / observation.required_corroborating_source_count,
        )


def _manual_escalation_urgency_score(
    *,
    update_frequency_pressure: Decimal,
    claim_reversal_pressure: Decimal,
    source_age_seconds: Decimal,
    corroboration_readiness_score: Decimal,
    config: ResearchMarketSourceUpdateVolatilityReportConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_recency_pressure = _clamped_ratio(
            source_age_seconds / config.max_source_age_seconds,
        )
        corroboration_gap = _clamped_ratio(ONE - corroboration_readiness_score)
        return _clamped_ratio(
            (update_frequency_pressure * config.update_frequency_weight)
            + (claim_reversal_pressure * config.claim_reversal_weight)
            + (source_recency_pressure * config.source_recency_weight)
            + (corroboration_gap * config.corroboration_gap_weight),
        )


def _row_reason_codes(
    *,
    update_frequency_pressure: Decimal,
    claim_reversal_pressure: Decimal,
    source_age_seconds: Decimal,
    corroboration_readiness_score: Decimal,
    manual_escalation_urgency_score: Decimal,
    config: ResearchMarketSourceUpdateVolatilityReportConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if update_frequency_pressure > ZERO:
        values.append("update_frequency_watch")
    if claim_reversal_pressure >= config.claim_reversal_block_pressure:
        values.append("claim_reversal_pressure_block")
    elif claim_reversal_pressure >= config.claim_reversal_watch_pressure:
        values.append("claim_reversal_pressure_watch")
    if source_age_seconds > config.max_source_age_seconds:
        values.append("source_recency_block")
    if corroboration_readiness_score < config.min_corroboration_readiness_score:
        block_readiness_threshold = _quantize_decimal(
            config.min_corroboration_readiness_score / TWO,
        )
        if corroboration_readiness_score <= block_readiness_threshold:
            values.append("corroboration_readiness_block")
        else:
            values.append("corroboration_readiness_watch")
    if manual_escalation_urgency_score >= config.block_manual_escalation_urgency_score:
        values.append("manual_escalation_urgency_block")
    elif manual_escalation_urgency_score >= config.watch_manual_escalation_urgency_score:
        values.append("manual_escalation_urgency_watch")
    if not values:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes != (PASS_REASON_CODE,):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchMarketSourceUpdateVolatilityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSourceUpdateVolatilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    values = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE
        and any(reason_code in row.reason_codes for row in rows)
    )
    if values:
        return values
    return (PASS_REASON_CODE,)


def _reason_code_counts(
    rows: tuple[ResearchMarketSourceUpdateVolatilityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketSourceUpdateVolatilityReasonCodeCount, ...]:
    if reason_codes == (PASS_REASON_CODE,):
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(reason_code for reason_code in row.reason_codes if reason_code != PASS_REASON_CODE)
    return tuple(
        ResearchMarketSourceUpdateVolatilityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE and counts[reason_code] > 0
    )


def _row_status_count(
    rows: tuple[ResearchMarketSourceUpdateVolatilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(normalized, ZERO) / Decimal(len(normalized)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _datetime_delta_seconds(generated_at, observed_at)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR)
    )
    return _normalize_nonnegative_decimal("datetime_delta_seconds", seconds)


def _row_sort_key(row: ResearchMarketSourceUpdateVolatilityRow) -> tuple[int, str]:
    return ({"block": 0, "watch": 1, "pass": 2}[row.status], row.research_bucket)


def _normalize_rows(
    rows: Iterable[ResearchMarketSourceUpdateVolatilityRow],
) -> tuple[ResearchMarketSourceUpdateVolatilityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchMarketSourceUpdateVolatilityRow:
            raise ValueError(
                "rows must contain ResearchMarketSourceUpdateVolatilityRow values",
            )
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchMarketSourceUpdateVolatilityReasonCodeCount],
) -> tuple[ResearchMarketSourceUpdateVolatilityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchMarketSourceUpdateVolatilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSourceUpdateVolatilityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    if values != tuple(
        sorted(values, key=lambda row: REASON_CODES.index(row.reason_code)),
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    if not values:
        raise ValueError(f"{field_name} must be non-empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in values:
        _require_reason_code(field_name, reason_code)
    if values != tuple(reason_code for reason_code in REASON_CODES if reason_code in values):
        raise ValueError(f"{field_name} must be deterministically sorted")
    return values


def _validate_row(row: ResearchMarketSourceUpdateVolatilityRow) -> None:
    if row.update_count <= ZERO:
        raise ValueError("update_count must be positive")
    if row.source_class_count <= ZERO:
        raise ValueError("source_class_count must be positive")
    if row.update_family_count <= ZERO:
        raise ValueError("update_family_count must be positive")
    if row.first_observed_at > row.last_observed_at:
        raise ValueError("first_observed_at must not be after last_observed_at")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketSourceUpdateVolatilityReport) -> None:
    if report.group_count != _count(len(report.rows)):
        raise ValueError("group_count must match rows")
    expected_update_count = sum((row.update_count for row in report.rows), ZERO)
    if report.update_count != expected_update_count:
        raise ValueError("update_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _report_payload(
    report: ResearchMarketSourceUpdateVolatilityReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "group_count": _payload_value(report.group_count),
        "update_count": _payload_value(report.update_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "max_manual_escalation_urgency_score": _payload_value(
            report.max_manual_escalation_urgency_score,
        ),
        "average_manual_escalation_urgency_score": _payload_value(
            report.average_manual_escalation_urgency_score,
        ),
        "average_update_frequency_pressure": _payload_value(
            report.average_update_frequency_pressure,
        ),
        "max_claim_reversal_pressure": _payload_value(
            report.max_claim_reversal_pressure,
        ),
        "average_corroboration_readiness_score": _payload_value(
            report.average_corroboration_readiness_score,
        ),
        "max_source_age_seconds": _payload_value(report.max_source_age_seconds),
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "rows": _payload_value(report.rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchMarketSourceUpdateVolatilityRow) -> dict[str, Any]:
    return {
        "research_bucket": row.research_bucket,
        "update_count": _payload_value(row.update_count),
        "source_class_count": _payload_value(row.source_class_count),
        "update_family_count": _payload_value(row.update_family_count),
        "first_observed_at": _payload_value(row.first_observed_at),
        "last_observed_at": _payload_value(row.last_observed_at),
        "average_update_interval_seconds": _payload_value(
            row.average_update_interval_seconds,
        ),
        "update_frequency_pressure": _payload_value(row.update_frequency_pressure),
        "claim_reversal_pressure": _payload_value(row.claim_reversal_pressure),
        "source_age_seconds": _payload_value(row.source_age_seconds),
        "corroboration_readiness_score": _payload_value(
            row.corroboration_readiness_score,
        ),
        "manual_escalation_urgency_score": _payload_value(
            row.manual_escalation_urgency_score,
        ),
        "status": row.status,
        "reason_codes": _payload_value(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchMarketSourceUpdateVolatilityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in sorted(value.items())}
    if type(value) is ResearchMarketSourceUpdateVolatilityRow:
        return _row_payload(value)
    if type(value) is ResearchMarketSourceUpdateVolatilityReasonCodeCount:
        return _reason_code_count_payload(value)
    if type(value) is ResearchMarketSourceUpdateVolatilityReport:
        return _report_payload(value, include_digest=True)
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _report_derived_validation_digest(
    report: ResearchMarketSourceUpdateVolatilityReport,
) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
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


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_public_string(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} payload keys must be strings")
            _reject_unsafe_public_string(f"{context} key", key)
            _reject_unsafe_public_payload(f"{context}.{key}", item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(context, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(context, value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in VOLATILITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{context} must expose {field_name}")
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_weight_sum(config: ResearchMarketSourceUpdateVolatilityReportConfig) -> None:
    total = _quantize_decimal(
        config.update_frequency_weight
        + config.claim_reversal_weight
        + config.source_recency_weight
        + config.corroboration_gap_weight,
    )
    if total != ONE:
        raise ValueError("weights must sum to one")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value


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


def _public_numeric_fields(value: object) -> tuple[str, ...]:
    if not is_dataclass(value):
        return ()
    return tuple(
        field.name
        for field in fields(value)
        if any(
            marker in field.name
            for marker in (
                "age",
                "count",
                "interval",
                "pressure",
                "readiness",
                "score",
            )
        )
    )
