"""Pure report-only probability review trigger report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_PROBABILITY_UPDATE_TRIGGER_CONFIG_VERSION = (
    "research-event-probability-update-trigger-report-v0"
)

PROBABILITY_UPDATE_TRIGGER_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "probability_update_trigger_pass"
REASON_CODES = (
    PASS_REASON_CODE,
    "new_evidence_watch",
    "new_evidence_block",
    "source_freshness_change_watch",
    "source_freshness_change_block",
    "contradiction_change_watch",
    "contradiction_change_block",
    "observed_probability_move_watch",
    "observed_probability_move_block",
    "fresh_probability_review_watch",
    "fresh_probability_review_block",
)
BLOCK_REASON_CODES = frozenset(
    (
        "new_evidence_block",
        "source_freshness_change_block",
        "contradiction_change_block",
        "observed_probability_move_block",
        "fresh_probability_review_block",
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "://",
        "www.",
        "api_key",
        "auth",
        "broker",
        "candidate",
        "condition_id",
        "credential",
        "database",
        "dsn",
        "live",
        "market",
        "network",
        "order",
        "private_key",
        "question",
        "raw",
        "recommendation",
        "secret",
        "sizing",
        "slug",
        "source_id",
        "source_text",
        "source_url",
        "submit",
        "table",
        "token",
        "trade",
        "trading",
        "url",
        "wallet",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_PROBABILITY_UPDATE_TRIGGER_CONFIG_VERSION",
    "PROBABILITY_UPDATE_TRIGGER_STATUSES",
    "REASON_CODES",
    "ResearchEventProbabilityUpdateTriggerConfig",
    "ResearchEventProbabilityUpdateTriggerObservation",
    "ResearchEventProbabilityUpdateTriggerReasonCodeCount",
    "ResearchEventProbabilityUpdateTriggerReport",
    "ResearchEventProbabilityUpdateTriggerRow",
    "build_research_event_probability_update_trigger_report",
    "research_event_probability_update_trigger_report_digest",
    "research_event_probability_update_trigger_report_payload",
    "validate_research_event_probability_update_trigger_public_payload",
)


@dataclass(frozen=True)
class ResearchEventProbabilityUpdateTriggerConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_PROBABILITY_UPDATE_TRIGGER_CONFIG_VERSION
    watch_new_evidence_count: Decimal = Decimal("1.000000")
    block_new_evidence_count: Decimal = Decimal("3.000000")
    watch_source_freshness_change_seconds: Decimal = Decimal("1800.000000")
    block_source_freshness_change_seconds: Decimal = Decimal("7200.000000")
    watch_contradiction_change_abs: Decimal = Decimal("0.050000")
    block_contradiction_change_abs: Decimal = Decimal("0.200000")
    watch_observed_probability_move_abs: Decimal = Decimal("0.020000")
    block_observed_probability_move_abs: Decimal = Decimal("0.080000")
    watch_review_trigger_score: Decimal = Decimal("0.250000")
    block_review_trigger_score: Decimal = Decimal("0.750000")
    new_evidence_weight: Decimal = Decimal("0.250000")
    source_freshness_weight: Decimal = Decimal("0.250000")
    contradiction_change_weight: Decimal = Decimal("0.250000")
    observed_probability_move_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventProbabilityUpdateTriggerConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventProbabilityUpdateTriggerConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_new_evidence_count",
            "block_new_evidence_count",
            "watch_source_freshness_change_seconds",
            "block_source_freshness_change_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_contradiction_change_abs",
            "block_contradiction_change_abs",
            "watch_observed_probability_move_abs",
            "block_observed_probability_move_abs",
            "watch_review_trigger_score",
            "block_review_trigger_score",
            "new_evidence_weight",
            "source_freshness_weight",
            "contradiction_change_weight",
            "observed_probability_move_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_new_evidence_count",
            self.watch_new_evidence_count,
            "block_new_evidence_count",
            self.block_new_evidence_count,
        )
        _require_less_than(
            "watch_source_freshness_change_seconds",
            self.watch_source_freshness_change_seconds,
            "block_source_freshness_change_seconds",
            self.block_source_freshness_change_seconds,
        )
        _require_less_than(
            "watch_contradiction_change_abs",
            self.watch_contradiction_change_abs,
            "block_contradiction_change_abs",
            self.block_contradiction_change_abs,
        )
        _require_less_than(
            "watch_observed_probability_move_abs",
            self.watch_observed_probability_move_abs,
            "block_observed_probability_move_abs",
            self.block_observed_probability_move_abs,
        )
        _require_less_than(
            "watch_review_trigger_score",
            self.watch_review_trigger_score,
            "block_review_trigger_score",
            self.block_review_trigger_score,
        )
        _require_weight_sum(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventProbabilityUpdateTriggerObservation:
    review_key: str
    latest_observed_at: datetime
    new_evidence_count: Decimal
    source_freshness_change_seconds_abs: Decimal
    contradiction_change_abs: Decimal
    observed_probability_move_abs: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventProbabilityUpdateTriggerObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventProbabilityUpdateTriggerObservation,
            "observation",
        )
        _require_public_string("review_key", self.review_key)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "new_evidence_count",
            "source_freshness_change_seconds_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_change_abs",
            "observed_probability_move_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventProbabilityUpdateTriggerReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventProbabilityUpdateTriggerReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventProbabilityUpdateTriggerReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventProbabilityUpdateTriggerRow:
    review_key: str
    latest_observed_at: datetime
    new_evidence_count: Decimal
    source_freshness_change_seconds_abs: Decimal
    contradiction_change_abs: Decimal
    observed_probability_move_abs: Decimal
    new_evidence_pressure: Decimal
    source_freshness_change_pressure: Decimal
    contradiction_change_pressure: Decimal
    observed_probability_move_pressure: Decimal
    trigger_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventProbabilityUpdateTriggerRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventProbabilityUpdateTriggerRow, "row")
        _require_public_string("review_key", self.review_key)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "new_evidence_count",
            "source_freshness_change_seconds_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_change_abs",
            "observed_probability_move_abs",
            "new_evidence_pressure",
            "source_freshness_change_pressure",
            "contradiction_change_pressure",
            "observed_probability_move_pressure",
            "trigger_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventProbabilityUpdateTriggerReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_new_evidence_count: Decimal
    max_trigger_score: Decimal
    average_trigger_score: Decimal
    max_source_freshness_change_seconds_abs: Decimal
    max_contradiction_change_abs: Decimal
    max_observed_probability_move_abs: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventProbabilityUpdateTriggerReasonCodeCount, ...]
    rows: tuple[ResearchEventProbabilityUpdateTriggerRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventProbabilityUpdateTriggerReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventProbabilityUpdateTriggerReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_new_evidence_count",
            "max_source_freshness_change_seconds_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_trigger_score",
            "average_trigger_score",
            "max_contradiction_change_abs",
            "max_observed_probability_move_abs",
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
        _reject_unsafe_public_payload("report", self)
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
        return research_event_probability_update_trigger_report_payload(self)


def build_research_event_probability_update_trigger_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchEventProbabilityUpdateTriggerConfig | None = None,
) -> ResearchEventProbabilityUpdateTriggerReport:
    """Build a deterministic report identifying analyst probability refresh triggers."""

    if config is None:
        config = ResearchEventProbabilityUpdateTriggerConfig()
    if type(config) is not ResearchEventProbabilityUpdateTriggerConfig:
        raise ValueError(
            "config must be a ResearchEventProbabilityUpdateTriggerConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventProbabilityUpdateTriggerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        row_count=_count(len(rows)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        total_new_evidence_count=sum(
            (row.new_evidence_count for row in rows),
            ZERO,
        ),
        max_trigger_score=max((row.trigger_score for row in rows), default=ZERO),
        average_trigger_score=_average_decimal(row.trigger_score for row in rows),
        max_source_freshness_change_seconds_abs=max(
            (row.source_freshness_change_seconds_abs for row in rows),
            default=ZERO,
        ),
        max_contradiction_change_abs=max(
            (row.contradiction_change_abs for row in rows),
            default=ZERO,
        ),
        max_observed_probability_move_abs=max(
            (row.observed_probability_move_abs for row in rows),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_event_probability_update_trigger_report_payload(
    report: ResearchEventProbabilityUpdateTriggerReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventProbabilityUpdateTriggerReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchEventProbabilityUpdateTriggerReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_event_probability_update_trigger_report_digest(
    report: ResearchEventProbabilityUpdateTriggerReport,
) -> str:
    if type(report) is not ResearchEventProbabilityUpdateTriggerReport:
        raise ValueError(
            "report must be a ResearchEventProbabilityUpdateTriggerReport",
        )
    _require_hard_flags("report", report)
    digest = _report_derived_validation_digest(report)
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_event_probability_update_trigger_public_payload(
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
        if digest != _payload_digest(unsigned_payload):
            return False
        if payload.get("status") not in PROBABILITY_UPDATE_TRIGGER_STATUSES:
            return False
        rows = payload.get("rows")
        if type(rows) is not list:
            return False
        for row in rows:
            if (
                type(row) is not dict
                or row.get("status") not in PROBABILITY_UPDATE_TRIGGER_STATUSES
            ):
                return False
        return True
    except (TypeError, ValueError):
        return False


def _row_from_observation(
    observation: ResearchEventProbabilityUpdateTriggerObservation,
    *,
    config: ResearchEventProbabilityUpdateTriggerConfig,
) -> ResearchEventProbabilityUpdateTriggerRow:
    new_evidence_pressure = _threshold_pressure(
        observation.new_evidence_count,
        config.block_new_evidence_count,
    )
    source_freshness_change_pressure = _threshold_pressure(
        observation.source_freshness_change_seconds_abs,
        config.block_source_freshness_change_seconds,
    )
    contradiction_change_pressure = _threshold_pressure(
        observation.contradiction_change_abs,
        config.block_contradiction_change_abs,
    )
    observed_probability_move_pressure = _threshold_pressure(
        observation.observed_probability_move_abs,
        config.block_observed_probability_move_abs,
    )
    trigger_score = _trigger_score(
        new_evidence_pressure=new_evidence_pressure,
        source_freshness_change_pressure=source_freshness_change_pressure,
        contradiction_change_pressure=contradiction_change_pressure,
        observed_probability_move_pressure=observed_probability_move_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        trigger_score=trigger_score,
        config=config,
    )
    return ResearchEventProbabilityUpdateTriggerRow(
        review_key=observation.review_key,
        latest_observed_at=observation.latest_observed_at,
        new_evidence_count=observation.new_evidence_count,
        source_freshness_change_seconds_abs=(
            observation.source_freshness_change_seconds_abs
        ),
        contradiction_change_abs=observation.contradiction_change_abs,
        observed_probability_move_abs=observation.observed_probability_move_abs,
        new_evidence_pressure=new_evidence_pressure,
        source_freshness_change_pressure=source_freshness_change_pressure,
        contradiction_change_pressure=contradiction_change_pressure,
        observed_probability_move_pressure=observed_probability_move_pressure,
        trigger_score=trigger_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _threshold_pressure(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _ratio(value, block_threshold)


def _trigger_score(
    *,
    new_evidence_pressure: Decimal,
    source_freshness_change_pressure: Decimal,
    contradiction_change_pressure: Decimal,
    observed_probability_move_pressure: Decimal,
    config: ResearchEventProbabilityUpdateTriggerConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(
            (new_evidence_pressure * config.new_evidence_weight)
            + (source_freshness_change_pressure * config.source_freshness_weight)
            + (contradiction_change_pressure * config.contradiction_change_weight)
            + (
                observed_probability_move_pressure
                * config.observed_probability_move_weight
            ),
        )


def _row_reason_codes(
    *,
    observation: ResearchEventProbabilityUpdateTriggerObservation,
    trigger_score: Decimal,
    config: ResearchEventProbabilityUpdateTriggerConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if observation.new_evidence_count >= config.block_new_evidence_count:
        values.append("new_evidence_block")
    elif observation.new_evidence_count >= config.watch_new_evidence_count:
        values.append("new_evidence_watch")
    if (
        observation.source_freshness_change_seconds_abs
        >= config.block_source_freshness_change_seconds
    ):
        values.append("source_freshness_change_block")
    elif (
        observation.source_freshness_change_seconds_abs
        >= config.watch_source_freshness_change_seconds
    ):
        values.append("source_freshness_change_watch")
    if observation.contradiction_change_abs >= config.block_contradiction_change_abs:
        values.append("contradiction_change_block")
    elif observation.contradiction_change_abs >= config.watch_contradiction_change_abs:
        values.append("contradiction_change_watch")
    if (
        observation.observed_probability_move_abs
        >= config.block_observed_probability_move_abs
    ):
        values.append("observed_probability_move_block")
    elif (
        observation.observed_probability_move_abs
        >= config.watch_observed_probability_move_abs
    ):
        values.append("observed_probability_move_watch")
    if trigger_score >= config.block_review_trigger_score:
        values.append("fresh_probability_review_block")
    elif trigger_score >= config.watch_review_trigger_score:
        values.append("fresh_probability_review_watch")
    if not values:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes != (PASS_REASON_CODE,):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventProbabilityUpdateTriggerRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventProbabilityUpdateTriggerRow, ...],
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
    rows: tuple[ResearchEventProbabilityUpdateTriggerRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventProbabilityUpdateTriggerReasonCodeCount, ...]:
    if reason_codes == (PASS_REASON_CODE,):
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(
            reason_code
            for reason_code in row.reason_codes
            if reason_code != PASS_REASON_CODE
        )
    return tuple(
        ResearchEventProbabilityUpdateTriggerReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REASON_CODES
        if reason_code != PASS_REASON_CODE and counts[reason_code] > 0
    )


def _row_status_count(
    rows: tuple[ResearchEventProbabilityUpdateTriggerRow, ...],
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


def _row_sort_key(row: ResearchEventProbabilityUpdateTriggerRow) -> tuple[int, str]:
    return ({"block": 0, "watch": 1, "pass": 2}[row.status], row.review_key)


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchEventProbabilityUpdateTriggerObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchEventProbabilityUpdateTriggerObservation] = []
    for value in values:
        if type(value) is not ResearchEventProbabilityUpdateTriggerObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventProbabilityUpdateTriggerObservation values",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(normalized)


def _reject_future_observations(
    observations: tuple[ResearchEventProbabilityUpdateTriggerObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.latest_observed_at > generated_at:
            raise ValueError("latest_observed_at must not be after generated_at")


def _normalize_rows(
    rows: Iterable[ResearchEventProbabilityUpdateTriggerRow],
) -> tuple[ResearchEventProbabilityUpdateTriggerRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchEventProbabilityUpdateTriggerRow:
            raise ValueError(
                "rows must contain ResearchEventProbabilityUpdateTriggerRow values",
            )
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchEventProbabilityUpdateTriggerReasonCodeCount],
) -> tuple[ResearchEventProbabilityUpdateTriggerReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in values:
        if type(row) is not ResearchEventProbabilityUpdateTriggerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventProbabilityUpdateTriggerReasonCodeCount values",
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


def _validate_row(row: ResearchEventProbabilityUpdateTriggerRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventProbabilityUpdateTriggerReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_new_evidence_count != sum(
        (row.new_evidence_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("total_new_evidence_count must match rows")
    if report.max_trigger_score != max(
        (row.trigger_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_trigger_score must match rows")
    if report.average_trigger_score != _average_decimal(
        (row.trigger_score for row in report.rows),
    ):
        raise ValueError("average_trigger_score must match rows")
    if report.max_source_freshness_change_seconds_abs != max(
        (row.source_freshness_change_seconds_abs for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_freshness_change_seconds_abs must match rows")
    if report.max_contradiction_change_abs != max(
        (row.contradiction_change_abs for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_change_abs must match rows")
    if report.max_observed_probability_move_abs != max(
        (row.observed_probability_move_abs for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_probability_move_abs must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _report_payload(
    report: ResearchEventProbabilityUpdateTriggerReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "row_count": _payload_value(report.row_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "total_new_evidence_count": _payload_value(report.total_new_evidence_count),
        "max_trigger_score": _payload_value(report.max_trigger_score),
        "average_trigger_score": _payload_value(report.average_trigger_score),
        "max_source_freshness_change_seconds_abs": _payload_value(
            report.max_source_freshness_change_seconds_abs,
        ),
        "max_contradiction_change_abs": _payload_value(
            report.max_contradiction_change_abs,
        ),
        "max_observed_probability_move_abs": _payload_value(
            report.max_observed_probability_move_abs,
        ),
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


def _row_payload(row: ResearchEventProbabilityUpdateTriggerRow) -> dict[str, Any]:
    return {
        "review_key": row.review_key,
        "latest_observed_at": _payload_value(row.latest_observed_at),
        "new_evidence_count": _payload_value(row.new_evidence_count),
        "source_freshness_change_seconds_abs": _payload_value(
            row.source_freshness_change_seconds_abs,
        ),
        "contradiction_change_abs": _payload_value(row.contradiction_change_abs),
        "observed_probability_move_abs": _payload_value(
            row.observed_probability_move_abs,
        ),
        "new_evidence_pressure": _payload_value(row.new_evidence_pressure),
        "source_freshness_change_pressure": _payload_value(
            row.source_freshness_change_pressure,
        ),
        "contradiction_change_pressure": _payload_value(
            row.contradiction_change_pressure,
        ),
        "observed_probability_move_pressure": _payload_value(
            row.observed_probability_move_pressure,
        ),
        "trigger_score": _payload_value(row.trigger_score),
        "status": row.status,
        "reason_codes": _payload_value(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchEventProbabilityUpdateTriggerReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is ResearchEventProbabilityUpdateTriggerRow:
        return _row_payload(value)
    if type(value) is ResearchEventProbabilityUpdateTriggerReasonCodeCount:
        return _reason_code_count_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("payload values must not be float")
    if type(value) is int:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_derived_validation_digest(
    report: ResearchEventProbabilityUpdateTriggerReport,
) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_decimal(decimal_value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_less_than(
    lower_field_name: str,
    lower_value: Decimal,
    upper_field_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_field_name} must be less than {upper_field_name}")


def _require_weight_sum(config: ResearchEventProbabilityUpdateTriggerConfig) -> None:
    total = _quantize_decimal(
        config.new_evidence_weight
        + config.source_freshness_weight
        + config.contradiction_change_weight
        + config.observed_probability_move_weight,
    )
    if total != ONE:
        raise ValueError("weights must sum to one")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have non-None utcoffset")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty normalized string")
    if any(ord(char) < 32 or ord(char) > 126 for char in value):
        raise ValueError(f"{field_name} must be printable ASCII")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public surface")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PROBABILITY_UPDATE_TRIGGER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} has unsupported reason code")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        field_value = getattr(value, field_name, None)
        _require_bool(field_name, field_value)
        if field_value is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            {field.name: getattr(value, field.name) for field in fields(value)},
        )
        return
    if type(value) in (float, int):
        raise ValueError(f"{label} must not contain public numeric primitives")
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{label} has unsafe public surface")
        return
    if isinstance(value, datetime):
        return
    if isinstance(value, Decimal):
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


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
