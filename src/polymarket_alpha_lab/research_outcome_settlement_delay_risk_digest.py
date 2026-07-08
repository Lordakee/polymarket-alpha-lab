"""Deterministic paper-only digest for outcome and settlement delay tracking."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-outcome-settlement-delay-risk-digest-v0"

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"

_PASS_STATUS = "pass"
_WATCH_STATUS = "watch"
_BLOCK_STATUS = "block"
_PUBLIC_STATUSES = (_PASS_STATUS, _WATCH_STATUS, _BLOCK_STATUS)
_STATUS_RANK = {_BLOCK_STATUS: 0, _WATCH_STATUS: 1, _PASS_STATUS: 2}

_MANUAL_BLOCK_REASON = "manual_block"
_HARD_DELAY_REASON = "hard_delay_flag"
_RESULT_BLOCK_REASON = "result_confirmation_block"
_RESULT_WATCH_REASON = "result_confirmation_watch"
_SETTLEMENT_BLOCK_REASON = "settlement_completion_block"
_SETTLEMENT_WATCH_REASON = "settlement_completion_watch"
_OBSERVATION_STALE_REASON = "observation_stale"
_PASS_REASON = "settlement_delay_pass"

_REASON_CODES = (
    _MANUAL_BLOCK_REASON,
    _HARD_DELAY_REASON,
    _RESULT_BLOCK_REASON,
    _SETTLEMENT_BLOCK_REASON,
    _RESULT_WATCH_REASON,
    _SETTLEMENT_WATCH_REASON,
    _OBSERVATION_STALE_REASON,
    _PASS_REASON,
)
_REASON_RANK = {reason_code: index for index, reason_code in enumerate(_REASON_CODES)}

_SURFACE_FRAGMENTS = (
    "candidateid",
    "candidate",
    "marketid",
    "marketslug",
    "marketquestion",
    "slug",
    "question",
    "sourceref",
    "sourceurl",
    "sourcetext",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "".join(("wall", "et")),
    "".join(("au", "th")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "".join(("pos", "ition")),
    "buy",
    "sell",
    "".join(("reco", "mmend")),
)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchOutcomeSettlementDelayRiskConfig",
    "ResearchOutcomeSettlementDelayRiskObservation",
    "ResearchOutcomeSettlementDelayRiskReport",
    "ResearchOutcomeSettlementDelayRiskRow",
    "build_research_outcome_settlement_delay_risk_report",
    "research_outcome_settlement_delay_risk_digest",
    "research_outcome_settlement_delay_risk_report_payload",
    "validate_research_outcome_settlement_delay_risk_report_payload",
)


@dataclass(frozen=True)
class ResearchOutcomeSettlementDelayRiskConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    result_watch_after_seconds: Decimal = Decimal("3600.000000")
    result_block_after_seconds: Decimal = Decimal("21600.000000")
    settlement_watch_after_seconds: Decimal = Decimal("7200.000000")
    settlement_block_after_seconds: Decimal = Decimal("86400.000000")
    stale_observation_after_seconds: Decimal = Decimal("3600.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchOutcomeSettlementDelayRiskConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "result_watch_after_seconds",
            "result_block_after_seconds",
            "settlement_watch_after_seconds",
            "settlement_block_after_seconds",
            "stale_observation_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.result_block_after_seconds <= self.result_watch_after_seconds:
            raise ValueError(
                "result_block_after_seconds must be greater than "
                "result_watch_after_seconds",
            )
        if self.settlement_block_after_seconds <= self.settlement_watch_after_seconds:
            raise ValueError(
                "settlement_block_after_seconds must be greater than "
                "settlement_watch_after_seconds",
            )
        _require_hard_flags(self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchOutcomeSettlementDelayRiskObservation:
    private_candidate_id: str
    private_event_id: str
    private_event_slug: str
    private_event_question: str
    private_reference: str | None
    private_locator: str | None
    private_excerpt: str | None
    observed_at: datetime
    event_ended_at: datetime
    result_confirmed_at: datetime | None = None
    settlement_completed_at: datetime | None = None
    manual_block: bool = False
    hard_delay_flag: bool = False
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchOutcomeSettlementDelayRiskObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "private_candidate_id",
            "private_event_id",
            "private_event_slug",
            "private_event_question",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "private_reference",
            "private_locator",
            "private_excerpt",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_canonical_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observed_at",
            "event_ended_at",
            "result_confirmed_at",
            "settlement_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_as_utc(field_name, getattr(self, field_name))
                if getattr(self, field_name) is None
                else _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("manual_block", "hard_delay_flag"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _validate_observation_times(self)
        _require_hard_flags(self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchOutcomeSettlementDelayRiskRow:
    public_tracking_key: str
    observed_age_seconds: Decimal
    event_age_seconds: Decimal
    result_delay_seconds: Decimal
    settlement_delay_seconds: Decimal | None
    result_confirmed: bool
    settlement_completed: bool
    public_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchOutcomeSettlementDelayRiskRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_sha256_hex("public_tracking_key", self.public_tracking_key)
        for field_name in (
            "observed_age_seconds",
            "event_age_seconds",
            "result_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_seconds",
            _normalize_optional_nonnegative_decimal(
                "settlement_delay_seconds",
                self.settlement_delay_seconds,
            ),
        )
        for field_name in ("result_confirmed", "settlement_completed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_public_status("public_status", self.public_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchOutcomeSettlementDelayRiskReport:
    generated_at: datetime
    config_version: str
    public_status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    stale_observation_count: Decimal
    average_result_delay_seconds: Decimal | None
    average_settlement_delay_seconds: Decimal | None
    rows: tuple[ResearchOutcomeSettlementDelayRiskRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchOutcomeSettlementDelayRiskReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "stale_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_result_delay_seconds",
            "average_settlement_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)
        _validate_report_payload_shape(self)


def build_research_outcome_settlement_delay_risk_report(
    observations: Iterable[ResearchOutcomeSettlementDelayRiskObservation],
    *,
    config: ResearchOutcomeSettlementDelayRiskConfig,
    generated_at: datetime,
) -> ResearchOutcomeSettlementDelayRiskReport:
    if type(config) is not ResearchOutcomeSettlementDelayRiskConfig:
        raise ValueError("config must be a ResearchOutcomeSettlementDelayRiskConfig")
    _require_hard_flags(config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations, generated_at=generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at,
                )
                for observation in values
            ),
            key=_row_sort_key,
        ),
    )

    return ResearchOutcomeSettlementDelayRiskReport(
        generated_at=generated_at,
        config_version=config.config_version,
        public_status=_report_public_status(rows),
        observation_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, _PASS_STATUS),
        watch_count=_status_count(rows, _WATCH_STATUS),
        block_count=_status_count(rows, _BLOCK_STATUS),
        hard_flag_count=_reason_count(rows, _MANUAL_BLOCK_REASON)
        + _reason_count(rows, _HARD_DELAY_REASON),
        stale_observation_count=_reason_count(rows, _OBSERVATION_STALE_REASON),
        average_result_delay_seconds=_average_optional(
            tuple(row.result_delay_seconds for row in rows),
        ),
        average_settlement_delay_seconds=_average_optional(
            tuple(
                row.settlement_delay_seconds
                for row in rows
                if row.settlement_delay_seconds is not None
            ),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_outcome_settlement_delay_risk_report_payload(
    report: ResearchOutcomeSettlementDelayRiskReport,
) -> dict[str, Any]:
    if type(report) is not ResearchOutcomeSettlementDelayRiskReport:
        raise ValueError("report must be a ResearchOutcomeSettlementDelayRiskReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_outcome_settlement_delay_risk_report_payload(payload)
    return payload


def research_outcome_settlement_delay_risk_digest(
    report: ResearchOutcomeSettlementDelayRiskReport,
) -> str:
    if type(report) is not ResearchOutcomeSettlementDelayRiskReport:
        raise ValueError("report must be a ResearchOutcomeSettlementDelayRiskReport")
    return research_outcome_settlement_delay_risk_report_payload(report)[_DIGEST_FIELD]


def validate_research_outcome_settlement_delay_risk_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_observation(
    value: ResearchOutcomeSettlementDelayRiskObservation,
    *,
    config: ResearchOutcomeSettlementDelayRiskConfig,
    generated_at: datetime,
) -> ResearchOutcomeSettlementDelayRiskRow:
    observed_age_seconds = _seconds_between(value.observed_at, generated_at)
    event_age_seconds = _seconds_between(value.event_ended_at, generated_at)
    if value.result_confirmed_at is None:
        result_delay_seconds = event_age_seconds
        settlement_delay_seconds = None
    else:
        result_delay_seconds = _seconds_between(
            value.event_ended_at,
            value.result_confirmed_at,
        )
        settlement_delay_seconds = (
            _seconds_between(value.result_confirmed_at, value.settlement_completed_at)
            if value.settlement_completed_at is not None
            else _seconds_between(value.result_confirmed_at, generated_at)
        )
    reason_codes = _row_reason_codes(
        value=value,
        observed_age_seconds=observed_age_seconds,
        result_delay_seconds=result_delay_seconds,
        settlement_delay_seconds=settlement_delay_seconds,
        config=config,
    )

    return ResearchOutcomeSettlementDelayRiskRow(
        public_tracking_key=_public_tracking_key(value),
        observed_age_seconds=observed_age_seconds,
        event_age_seconds=event_age_seconds,
        result_delay_seconds=result_delay_seconds,
        settlement_delay_seconds=settlement_delay_seconds,
        result_confirmed=value.result_confirmed_at is not None,
        settlement_completed=value.settlement_completed_at is not None,
        public_status=_row_public_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    value: ResearchOutcomeSettlementDelayRiskObservation,
    observed_age_seconds: Decimal,
    result_delay_seconds: Decimal,
    settlement_delay_seconds: Decimal | None,
    config: ResearchOutcomeSettlementDelayRiskConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if value.manual_block:
        reason_codes.append(_MANUAL_BLOCK_REASON)
    if value.hard_delay_flag:
        reason_codes.append(_HARD_DELAY_REASON)
    if value.result_confirmed_at is None:
        if result_delay_seconds > config.result_block_after_seconds:
            reason_codes.append(_RESULT_BLOCK_REASON)
        elif result_delay_seconds > config.result_watch_after_seconds:
            reason_codes.append(_RESULT_WATCH_REASON)
    elif value.settlement_completed_at is None and settlement_delay_seconds is not None:
        if settlement_delay_seconds > config.settlement_block_after_seconds:
            reason_codes.append(_SETTLEMENT_BLOCK_REASON)
        elif settlement_delay_seconds > config.settlement_watch_after_seconds:
            reason_codes.append(_SETTLEMENT_WATCH_REASON)
    if observed_age_seconds > config.stale_observation_after_seconds:
        reason_codes.append(_OBSERVATION_STALE_REASON)
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in reason_codes)


def _row_public_status(reason_codes: tuple[str, ...]) -> str:
    if (
        _MANUAL_BLOCK_REASON in reason_codes
        or _HARD_DELAY_REASON in reason_codes
        or _RESULT_BLOCK_REASON in reason_codes
        or _SETTLEMENT_BLOCK_REASON in reason_codes
    ):
        return _BLOCK_STATUS
    if (
        _RESULT_WATCH_REASON in reason_codes
        or _SETTLEMENT_WATCH_REASON in reason_codes
        or _OBSERVATION_STALE_REASON in reason_codes
    ):
        return _WATCH_STATUS
    return _PASS_STATUS


def _report_public_status(
    rows: tuple[ResearchOutcomeSettlementDelayRiskRow, ...],
) -> str:
    if not rows:
        return _WATCH_STATUS
    return min((row.public_status for row in rows), key=lambda status: _STATUS_RANK[status])


def _report_reason_codes(
    rows: tuple[ResearchOutcomeSettlementDelayRiskRow, ...],
) -> tuple[str, ...]:
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _PASS_REASON
    }
    if not reason_codes:
        return (_PASS_REASON,)
    return tuple(reason_code for reason_code in _REASON_CODES if reason_code in reason_codes)


def _normalize_observations(
    values: Iterable[ResearchOutcomeSettlementDelayRiskObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchOutcomeSettlementDelayRiskObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in observations:
        if type(value) is not ResearchOutcomeSettlementDelayRiskObservation:
            raise ValueError(
                "observations must contain "
                "ResearchOutcomeSettlementDelayRiskObservation values",
            )
        _require_hard_flags(value)
        _require_or_set_digest(value)
        _validate_known_times(value, generated_at)
        public_key = _public_tracking_key(value)
        if public_key in seen_keys:
            raise ValueError("observations must be unique")
        seen_keys.add(public_key)
    return observations


def _validate_observation_times(
    value: ResearchOutcomeSettlementDelayRiskObservation,
) -> None:
    if value.result_confirmed_at is not None and value.result_confirmed_at < value.event_ended_at:
        raise ValueError("result_confirmed_at must be at or after event_ended_at")
    if value.settlement_completed_at is not None:
        if value.result_confirmed_at is None:
            raise ValueError("result_confirmed_at is required with settlement_completed_at")
        if value.settlement_completed_at < value.result_confirmed_at:
            raise ValueError(
                "settlement_completed_at must be at or after result_confirmed_at",
            )


def _validate_known_times(
    value: ResearchOutcomeSettlementDelayRiskObservation,
    generated_at: datetime,
) -> None:
    for field_name in (
        "observed_at",
        "event_ended_at",
        "result_confirmed_at",
        "settlement_completed_at",
    ):
        known_at = getattr(value, field_name)
        if known_at is not None and known_at > generated_at:
            raise ValueError(f"{field_name} must be at or before generated_at")


def _normalize_rows(
    values: Iterable[ResearchOutcomeSettlementDelayRiskRow],
) -> tuple[ResearchOutcomeSettlementDelayRiskRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchOutcomeSettlementDelayRiskRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain ResearchOutcomeSettlementDelayRiskRow values") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchOutcomeSettlementDelayRiskRow:
            raise ValueError("rows must contain ResearchOutcomeSettlementDelayRiskRow values")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
        if row.public_tracking_key in seen_keys:
            raise ValueError("rows must be unique")
        seen_keys.add(row.public_tracking_key)
    return rows


def _validate_row_consistency(row: ResearchOutcomeSettlementDelayRiskRow) -> None:
    if row.public_status != _row_public_status(row.reason_codes):
        raise ValueError("reason_codes must match public_status")
    if row.public_status == _PASS_STATUS and row.reason_codes != (_PASS_REASON,):
        raise ValueError("reason_codes must use pass reason for pass rows")
    if _PASS_REASON in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("reason_codes must not mix pass with delay reasons")
    if row.settlement_completed and not row.result_confirmed:
        raise ValueError("result_confirmed must be true with settlement_completed")
    if row.settlement_completed and row.settlement_delay_seconds is None:
        raise ValueError("settlement_delay_seconds is required with settlement_completed")


def _validate_report_consistency(
    report: ResearchOutcomeSettlementDelayRiskReport,
) -> None:
    rows = report.rows
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _status_count(rows, _PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, _WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, _BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    hard_count = _reason_count(rows, _MANUAL_BLOCK_REASON) + _reason_count(
        rows,
        _HARD_DELAY_REASON,
    )
    if report.hard_flag_count != hard_count:
        raise ValueError("hard_flag_count must match rows")
    if report.stale_observation_count != _reason_count(rows, _OBSERVATION_STALE_REASON):
        raise ValueError("stale_observation_count must match rows")
    if report.average_result_delay_seconds != _average_optional(
        tuple(row.result_delay_seconds for row in rows),
    ):
        raise ValueError("average_result_delay_seconds must match rows")
    if report.average_settlement_delay_seconds != _average_optional(
        tuple(
            row.settlement_delay_seconds
            for row in rows
            if row.settlement_delay_seconds is not None
        ),
    ):
        raise ValueError("average_settlement_delay_seconds must match rows")
    if report.public_status != _report_public_status(rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_payload_shape(
    report: ResearchOutcomeSettlementDelayRiskReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("payload rows must use deterministic sort")


def _row_sort_key(row: ResearchOutcomeSettlementDelayRiskRow) -> tuple[int, int, str]:
    return (
        _STATUS_RANK[row.public_status],
        _primary_reason_rank(row.reason_codes),
        row.public_tracking_key,
    )


def _primary_reason_rank(reason_codes: tuple[str, ...]) -> int:
    return min(_REASON_RANK[reason_code] for reason_code in reason_codes)


def _status_count(
    rows: tuple[ResearchOutcomeSettlementDelayRiskRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.public_status == status))


def _reason_count(
    rows: tuple[ResearchOutcomeSettlementDelayRiskRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta < timedelta(0):
        raise ValueError("datetime range must be nonnegative")
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_RANK:
            raise ValueError("reason_codes must contain known values")
    expected = tuple(reason_code for reason_code in _REASON_CODES if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_sha256_hex(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")


def _public_tracking_key(
    value: ResearchOutcomeSettlementDelayRiskObservation,
) -> str:
    return _digest_json(
        {
            "private_candidate_id": value.private_candidate_id,
            "private_event_id": value.private_event_id,
            "private_event_slug": value.private_event_slug,
            "private_event_question": value.private_event_question,
        },
    )


def _payload_value(value: object, *, include_digest: bool = True) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
            for field in fields(value)
            if include_digest or field.name != _DIGEST_FIELD
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    expected = _payload_digest(_payload_value(value, include_digest=False))
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")


def _payload_digest(value: object) -> str:
    return _digest_json(_strip_digest_fields(value))


def _digest_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != _DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str or current != _payload_digest(value):
                raise ValueError("derived_validation_digest payload mismatch")
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_surface_fragment(key):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name.startswith("private_"):
                continue
            if _contains_surface_fragment(field.name):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is str and _contains_surface_fragment(value):
        raise ValueError(f"{label} contains unsafe public value")


def _contains_surface_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


def _require_public_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            if key.endswith("status") and item not in _PUBLIC_STATUSES:
                raise ValueError("public status must be pass, watch, or block")
            _require_public_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError("public payload contains an unsupported value")
