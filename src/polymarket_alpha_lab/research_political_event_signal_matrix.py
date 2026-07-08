"""Pure report-only political event signal matrix for manual research routing."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION = (
    "research-political-event-signal-matrix-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
_SIGNAL_TYPES = frozenset(("polling", "schedule", "institution"))
_SIGNAL_STANCES = frozenset(("supporting", "neutral", "counter"))
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "polling_signal_present",
    "polling_signal_missing",
    "schedule_signal_present",
    "schedule_signal_missing",
    "institution_signal_present",
    "institution_signal_missing",
    "family_independence_met",
    "family_independence_low",
    "fresh_signal_context",
    "stale_signal_context",
    "no_counter_signal",
    "counter_signal_present",
    "counter_signal_hard_block",
    "political_event_signal_block",
    "political_event_signal_watch",
    "political_event_signal_pass",
)
_STATUS_REASON_CODES = frozenset(
    (
        "empty_input",
        "political_event_signal_block",
        "political_event_signal_watch",
        "political_event_signal_pass",
    ),
)
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "blocked",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class PoliticalEventSignalMatrixConfig:
    config_version: str = DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION
    fresh_signal_age_seconds: Decimal = Decimal("86400.000000")
    stale_signal_age_seconds: Decimal = Decimal("604800.000000")
    min_independent_family_count: Decimal = Decimal("2.000000")
    watch_priority_score: Decimal = Decimal("0.450000")
    pass_priority_score: Decimal = Decimal("0.750000")
    block_counter_signal_count: Decimal = Decimal("2.000000")
    confidence_weight: Decimal = Decimal("0.400000")
    coverage_weight: Decimal = Decimal("0.350000")
    independence_weight: Decimal = Decimal("0.250000")
    counter_signal_penalty: Decimal = Decimal("0.350000")
    stale_signal_penalty: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PoliticalEventSignalMatrixConfig:
            raise TypeError("PoliticalEventSignalMatrixConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PoliticalEventSignalMatrixConfig:
            raise ValueError("config must be exactly PoliticalEventSignalMatrixConfig")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_signal_age_seconds",
            "stale_signal_age_seconds",
            "min_independent_family_count",
            "block_counter_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_priority_score",
            "pass_priority_score",
            "confidence_weight",
            "coverage_weight",
            "independence_weight",
            "counter_signal_penalty",
            "stale_signal_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_signal_age_seconds > self.stale_signal_age_seconds:
            raise ValueError("fresh_signal_age_seconds must not exceed stale threshold")
        if self.min_independent_family_count <= _ZERO:
            raise ValueError("min_independent_family_count must be positive")
        if self.block_counter_signal_count <= _ZERO:
            raise ValueError("block_counter_signal_count must be positive")
        if self.watch_priority_score > self.pass_priority_score:
            raise ValueError("watch_priority_score must not exceed pass threshold")
        if (
            self.confidence_weight + self.coverage_weight + self.independence_weight
            != _ONE
        ):
            raise ValueError("priority score weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class PoliticalEventSignalMatrixObservation:
    event_key: str
    signal_key: str
    family_key: str
    signal_type: str
    signal_stance: str
    confidence_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PoliticalEventSignalMatrixObservation:
            raise TypeError(
                "PoliticalEventSignalMatrixObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PoliticalEventSignalMatrixObservation:
            raise ValueError(
                "observation must be exactly PoliticalEventSignalMatrixObservation",
            )
        for field_name in ("event_key", "signal_key", "family_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_signal_type("signal_type", self.signal_type)
        _require_signal_stance("signal_stance", self.signal_stance)
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class PoliticalEventSignalMatrixRow:
    event_key: str
    observation_count: Decimal
    family_count: Decimal
    polling_count: Decimal
    schedule_count: Decimal
    institution_count: Decimal
    counter_signal_count: Decimal
    stale_signal_count: Decimal
    average_confidence_score: Decimal
    coverage_score: Decimal
    independence_score: Decimal
    counter_penalty_score: Decimal
    stale_penalty_score: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PoliticalEventSignalMatrixRow:
            raise TypeError("PoliticalEventSignalMatrixRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PoliticalEventSignalMatrixRow:
            raise ValueError("row must be exactly PoliticalEventSignalMatrixRow")
        _require_public_identifier("event_key", self.event_key)
        for field_name in (
            "observation_count",
            "family_count",
            "polling_count",
            "schedule_count",
            "institution_count",
            "counter_signal_count",
            "stale_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_score",
            "coverage_score",
            "independence_score",
            "counter_penalty_score",
            "stale_penalty_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class PoliticalEventSignalMatrixReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PoliticalEventSignalMatrixReasonCodeCount:
            raise TypeError(
                "PoliticalEventSignalMatrixReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PoliticalEventSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason count must be exactly PoliticalEventSignalMatrixReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class PoliticalEventSignalMatrixReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PoliticalEventSignalMatrixReasonCodeCount, ...]
    rows: tuple[PoliticalEventSignalMatrixRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PoliticalEventSignalMatrixReport:
            raise TypeError("PoliticalEventSignalMatrixReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PoliticalEventSignalMatrixReport:
            raise ValueError("report must be exactly PoliticalEventSignalMatrixReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_status("status", self.status)
        for field_name in (
            "event_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_priority_score", "max_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_political_event_signal_matrix_payload(self)


def build_research_political_event_signal_matrix(
    observations: Sequence[PoliticalEventSignalMatrixObservation],
    *,
    generated_at: datetime,
    config: PoliticalEventSignalMatrixConfig | None = None,
) -> PoliticalEventSignalMatrixReport:
    """Build a deterministic paper-only public signal matrix report."""

    if config is None:
        config = PoliticalEventSignalMatrixConfig()
    if type(config) is not PoliticalEventSignalMatrixConfig:
        raise ValueError("config must be a PoliticalEventSignalMatrixConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = _build_rows(normalized, generated_at=generated_at, config=config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "event_count": _decimal_count(len(rows)),
        "input_count": _decimal_count(len(normalized)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_priority_score": _average_ratio(
            tuple(row.priority_score for row in rows),
        ),
        "max_priority_score": max((row.priority_score for row in rows), default=_ZERO),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(_report_reason_codes(rows)),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return PoliticalEventSignalMatrixReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_political_event_signal_matrix_payload(
    value: PoliticalEventSignalMatrixReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is PoliticalEventSignalMatrixReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a PoliticalEventSignalMatrixReport or dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    observations: tuple[PoliticalEventSignalMatrixObservation, ...],
    *,
    generated_at: datetime,
    config: PoliticalEventSignalMatrixConfig,
) -> tuple[PoliticalEventSignalMatrixRow, ...]:
    grouped: dict[str, list[PoliticalEventSignalMatrixObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.event_key, []).append(observation)
    return tuple(
        sorted(
            (
                _row_for_event(
                    event_key=event_key,
                    observations=tuple(event_observations),
                    generated_at=generated_at,
                    config=config,
                )
                for event_key, event_observations in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )


def _row_for_event(
    *,
    event_key: str,
    observations: tuple[PoliticalEventSignalMatrixObservation, ...],
    generated_at: datetime,
    config: PoliticalEventSignalMatrixConfig,
) -> PoliticalEventSignalMatrixRow:
    polling_count = _signal_type_count(observations, "polling")
    schedule_count = _signal_type_count(observations, "schedule")
    institution_count = _signal_type_count(observations, "institution")
    counter_signal_count = _stance_count(observations, "counter")
    stale_signal_count = _stale_signal_count(observations, generated_at, config)
    family_count = _decimal_count(len({observation.family_key for observation in observations}))
    coverage_score = _coverage_score(
        polling_count=polling_count,
        schedule_count=schedule_count,
        institution_count=institution_count,
    )
    independence_score = _clamp_ratio(family_count / config.min_independent_family_count)
    counter_penalty_score = _clamp_ratio(
        counter_signal_count * config.counter_signal_penalty,
    )
    stale_penalty_score = _clamp_ratio(stale_signal_count * config.stale_signal_penalty)
    average_confidence_score = _average_ratio(
        tuple(observation.confidence_score for observation in observations),
    )
    priority_score = _priority_score(
        average_confidence_score=average_confidence_score,
        coverage_score=coverage_score,
        independence_score=independence_score,
        counter_signal_count=counter_signal_count,
        counter_penalty_score=counter_penalty_score,
        stale_penalty_score=stale_penalty_score,
        config=config,
    )
    status = _row_status(
        priority_score=priority_score,
        coverage_score=coverage_score,
        independence_score=independence_score,
        counter_signal_count=counter_signal_count,
        config=config,
    )
    return PoliticalEventSignalMatrixRow(
        event_key=event_key,
        observation_count=_decimal_count(len(observations)),
        family_count=family_count,
        polling_count=polling_count,
        schedule_count=schedule_count,
        institution_count=institution_count,
        counter_signal_count=counter_signal_count,
        stale_signal_count=stale_signal_count,
        average_confidence_score=average_confidence_score,
        coverage_score=coverage_score,
        independence_score=independence_score,
        counter_penalty_score=counter_penalty_score,
        stale_penalty_score=stale_penalty_score,
        priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            polling_count=polling_count,
            schedule_count=schedule_count,
            institution_count=institution_count,
            family_count=family_count,
            stale_signal_count=stale_signal_count,
            counter_signal_count=counter_signal_count,
            status=status,
            config=config,
        ),
    )


def _priority_score(
    *,
    average_confidence_score: Decimal,
    coverage_score: Decimal,
    independence_score: Decimal,
    counter_signal_count: Decimal,
    counter_penalty_score: Decimal,
    stale_penalty_score: Decimal,
    config: PoliticalEventSignalMatrixConfig,
) -> Decimal:
    if counter_signal_count >= config.block_counter_signal_count:
        return _ZERO
    if (
        coverage_score == _ONE
        and independence_score == _ONE
        and counter_penalty_score == _ZERO
        and stale_penalty_score == _ZERO
    ):
        return _ONE
    base_score = (
        average_confidence_score * config.confidence_weight
        + coverage_score * config.coverage_weight
        + independence_score * config.independence_weight
    )
    return _clamp_ratio(base_score - counter_penalty_score - stale_penalty_score)


def _coverage_score(
    *,
    polling_count: Decimal,
    schedule_count: Decimal,
    institution_count: Decimal,
) -> Decimal:
    present = Decimal("0.000000")
    if polling_count > _ZERO:
        present += _ONE
    if schedule_count > _ZERO:
        present += _ONE
    if institution_count > _ZERO:
        present += _ONE
    return _clamp_ratio(present / Decimal("3.000000"))


def _row_status(
    *,
    priority_score: Decimal,
    coverage_score: Decimal,
    independence_score: Decimal,
    counter_signal_count: Decimal,
    config: PoliticalEventSignalMatrixConfig,
) -> str:
    if counter_signal_count >= config.block_counter_signal_count:
        return "block"
    if (
        priority_score >= config.pass_priority_score
        and coverage_score == _ONE
        and independence_score == _ONE
    ):
        return "pass"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    polling_count: Decimal,
    schedule_count: Decimal,
    institution_count: Decimal,
    family_count: Decimal,
    stale_signal_count: Decimal,
    counter_signal_count: Decimal,
    status: str,
    config: PoliticalEventSignalMatrixConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "polling_signal_present" if polling_count > _ZERO else "polling_signal_missing",
    )
    reason_codes.append(
        "schedule_signal_present"
        if schedule_count > _ZERO
        else "schedule_signal_missing",
    )
    reason_codes.append(
        "institution_signal_present"
        if institution_count > _ZERO
        else "institution_signal_missing",
    )
    reason_codes.append(
        "family_independence_met"
        if family_count >= config.min_independent_family_count
        else "family_independence_low",
    )
    reason_codes.append(
        "stale_signal_context" if stale_signal_count > _ZERO else "fresh_signal_context",
    )
    if counter_signal_count >= config.block_counter_signal_count:
        reason_codes.append("counter_signal_hard_block")
    elif counter_signal_count > _ZERO:
        reason_codes.append("counter_signal_present")
    else:
        reason_codes.append("no_counter_signal")
    reason_codes.append(f"political_event_signal_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(row: PoliticalEventSignalMatrixRow) -> None:
    if row.observation_count <= _ZERO:
        raise ValueError("observation_count must be positive for rows")
    if row.polling_count + row.schedule_count + row.institution_count < row.observation_count:
        raise ValueError("signal type counts must cover observations")
    if f"political_event_signal_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.counter_signal_count > _ZERO:
        if (
            "counter_signal_present" not in row.reason_codes
            and "counter_signal_hard_block" not in row.reason_codes
        ):
            raise ValueError("counter_signal_count must match reason_codes")
    elif "no_counter_signal" not in row.reason_codes:
        raise ValueError("counter_signal_count must match reason_codes")


def _validate_report_consistency(report: PoliticalEventSignalMatrixReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.input_count != sum(
        (row.observation_count for row in report.rows),
        _ZERO,
    ):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_priority_score != _average_ratio(
        tuple(row.priority_score for row in report.rows),
    ):
        raise ValueError("average_priority_score must match rows")
    if report.max_priority_score != max(
        (row.priority_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _report_status(rows: tuple[PoliticalEventSignalMatrixRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[PoliticalEventSignalMatrixRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if code in _STATUS_REASON_CODES and any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PoliticalEventSignalMatrixReasonCodeCount, ...]:
    return tuple(
        PoliticalEventSignalMatrixReasonCodeCount(
            reason_code=reason_code,
            count=_ONE,
        )
        for reason_code in reason_codes
    )


def _status_count(rows: tuple[PoliticalEventSignalMatrixRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.status == status))


def _signal_type_count(
    observations: tuple[PoliticalEventSignalMatrixObservation, ...],
    signal_type: str,
) -> Decimal:
    return _decimal_count(
        len(tuple(observation for observation in observations if observation.signal_type == signal_type)),
    )


def _stance_count(
    observations: tuple[PoliticalEventSignalMatrixObservation, ...],
    signal_stance: str,
) -> Decimal:
    return _decimal_count(
        len(
            tuple(
                observation
                for observation in observations
                if observation.signal_stance == signal_stance
            ),
        ),
    )


def _stale_signal_count(
    observations: tuple[PoliticalEventSignalMatrixObservation, ...],
    generated_at: datetime,
    config: PoliticalEventSignalMatrixConfig,
) -> Decimal:
    return _decimal_count(
        len(
            tuple(
                observation
                for observation in observations
                if _seconds_between(generated_at, observation.observed_at)
                > config.stale_signal_age_seconds
            ),
        ),
    )


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(whole_seconds + fractional_seconds)


def _normalize_observations(
    observations: Sequence[PoliticalEventSignalMatrixObservation],
) -> tuple[PoliticalEventSignalMatrixObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not PoliticalEventSignalMatrixObservation:
            raise ValueError(
                "observations items must be PoliticalEventSignalMatrixObservation",
            )
        _require_hard_flags("observation", observation)
    signal_keys = tuple(observation.signal_key for observation in normalized)
    if len(set(signal_keys)) != len(signal_keys):
        raise ValueError("signal_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[PoliticalEventSignalMatrixRow, ...],
) -> tuple[PoliticalEventSignalMatrixRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PoliticalEventSignalMatrixRow:
            raise ValueError("rows items must be PoliticalEventSignalMatrixRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic political signal ordering")
    event_keys = tuple(row.event_key for row in normalized)
    if len(set(event_keys)) != len(event_keys):
        raise ValueError("row event_key values must be unique")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[PoliticalEventSignalMatrixReasonCodeCount, ...],
) -> tuple[PoliticalEventSignalMatrixReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not PoliticalEventSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts items must be PoliticalEventSignalMatrixReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
    expected = tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    codes = tuple(count.reason_code for count in normalized)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(reason_codes)
    for reason_code in normalized:
        if reason_code not in _STATUS_REASON_CODES:
            raise ValueError("report reason_codes must contain report-level codes")
    return normalized


def _row_sort_key(row: PoliticalEventSignalMatrixRow) -> tuple[int, Decimal, str]:
    return (_STATUS_WEIGHT[row.status], -row.priority_score, row.event_key)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_signal_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SIGNAL_TYPES:
        raise ValueError(f"{field_name} must be a supported political signal type")


def _require_signal_stance(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SIGNAL_STANCES:
        raise ValueError(f"{field_name} must be a supported signal stance")


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    status: str,
    event_count: Decimal,
    input_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_priority_score: Decimal,
    max_priority_score: Decimal,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[PoliticalEventSignalMatrixReasonCodeCount, ...],
    rows: tuple[PoliticalEventSignalMatrixRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "status": status,
        "event_count": _json_ready(event_count),
        "input_count": _json_ready(input_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "average_priority_score": _json_ready(average_priority_score),
        "max_priority_score": _json_ready(max_priority_score),
        "reason_codes": list(reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(count) for count in reason_code_counts
        ],
        "rows": [_row_payload(row) for row in rows],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: PoliticalEventSignalMatrixRow) -> dict[str, object]:
    return {
        "event_key": row.event_key,
        "observation_count": _json_ready(row.observation_count),
        "family_count": _json_ready(row.family_count),
        "polling_count": _json_ready(row.polling_count),
        "schedule_count": _json_ready(row.schedule_count),
        "institution_count": _json_ready(row.institution_count),
        "counter_signal_count": _json_ready(row.counter_signal_count),
        "stale_signal_count": _json_ready(row.stale_signal_count),
        "average_confidence_score": _json_ready(row.average_confidence_score),
        "coverage_score": _json_ready(row.coverage_score),
        "independence_score": _json_ready(row.independence_score),
        "counter_penalty_score": _json_ready(row.counter_penalty_score),
        "stale_penalty_score": _json_ready(row.stale_penalty_score),
        "priority_score": _json_ready(row.priority_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    count: PoliticalEventSignalMatrixReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": count.reason_code,
        "count": _json_ready(count.count),
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


def _report_payload(report: PoliticalEventSignalMatrixReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        event_count=report.event_count,
        input_count=report.input_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_priority_score=report.average_priority_score,
        max_priority_score=report.max_priority_score,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: PoliticalEventSignalMatrixReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "event_count": report.event_count,
            "input_count": report.input_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_priority_score": report.average_priority_score,
            "max_priority_score": report.max_priority_score,
            "reason_codes": report.reason_codes,
            "reason_code_counts": report.reason_code_counts,
            "rows": report.rows,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        status=_require_mapping_value(values, "status", str),
        event_count=_require_mapping_value(values, "event_count", Decimal),
        input_count=_require_mapping_value(values, "input_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        average_priority_score=_require_mapping_value(
            values,
            "average_priority_score",
            Decimal,
        ),
        max_priority_score=_require_mapping_value(values, "max_priority_score", Decimal),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        reason_code_counts=_require_mapping_value(values, "reason_code_counts", tuple),
        rows=_require_mapping_value(values, "rows", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is PoliticalEventSignalMatrixReport:
        return _report_payload(value)
    if type(value) is PoliticalEventSignalMatrixRow:
        return _row_payload(value)
    if type(value) is PoliticalEventSignalMatrixReasonCodeCount:
        return _reason_code_count_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            PoliticalEventSignalMatrixConfig,
            PoliticalEventSignalMatrixObservation,
            PoliticalEventSignalMatrixRow,
            PoliticalEventSignalMatrixReasonCodeCount,
            PoliticalEventSignalMatrixReport,
        ):
            raise ValueError(f"{label} contains unsupported public dataclass")
        for field in fields(value):
            _reject_unsafe_public_fragment(f"{current_path}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} contains unsupported public mapping")
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_fragment(f"{current_path}.{key}", key)
            _reject_unsafe_public_payload(
                label,
                nested_value,
                f"{current_path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) in (list, tuple):
        for index, nested_value in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                nested_value,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_fragment(current_path, value)


def _reject_unsafe_public_fragment(field_name: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_POLITICAL_EVENT_SIGNAL_MATRIX_CONFIG_VERSION",
    "PoliticalEventSignalMatrixConfig",
    "PoliticalEventSignalMatrixObservation",
    "PoliticalEventSignalMatrixReasonCodeCount",
    "PoliticalEventSignalMatrixReport",
    "PoliticalEventSignalMatrixRow",
    "build_research_political_event_signal_matrix",
    "research_political_event_signal_matrix_payload",
)
