"""Readonly event resolution authority signal decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_SIGNAL_DECAY_CONFIG_VERSION = (
    "research-event-resolution-authority-signal-decay-v0"
)

SECOND_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "event_resolution_authority_signal_decay_empty"
PASS_REASON = "event_resolution_authority_signal_fresh"
WATCH_DECAY_REASON = "event_resolution_authority_signal_watch_decay"
BLOCK_DECAY_REASON = "event_resolution_authority_signal_block_decay"
CONFLICT_REASON = "event_resolution_authority_signal_conflict"
WATCH_LOW_SIGNAL_REASON = "event_resolution_authority_signal_watch_low_score"
BLOCK_LOW_SIGNAL_REASON = "event_resolution_authority_signal_block_low_score"

ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_DECAY_REASON,
    BLOCK_DECAY_REASON,
    CONFLICT_REASON,
    WATCH_LOW_SIGNAL_REASON,
    BLOCK_LOW_SIGNAL_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_DECAY_REASON,
    BLOCK_DECAY_REASON,
    CONFLICT_REASON,
    WATCH_LOW_SIGNAL_REASON,
    BLOCK_LOW_SIGNAL_REASON,
)
TRIGGER_REASON_CODES = tuple(
    reason_code
    for reason_code in REPORT_REASON_CODES
    if reason_code not in (EMPTY_REASON, PASS_REASON)
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "api_key",
        "auth_token",
        "authentication",
        "balance",
        "broker",
        "candidate_id",
        "cancel_order",
        "client_secret",
        "database",
        "db_password",
        "dsn",
        "exchange_mutation",
        "live_trading",
        "market_id",
        "market_slug",
        "network",
        "order",
        "persist",
        "place_order",
        "private_key",
        "question",
        "recommendation",
        "secret",
        "sign_order",
        "sizing",
        "source_text",
        "source_url",
        "submit_order",
        "table_name",
        "token",
        "trade",
        "trading",
        "wallet",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_SIGNAL_DECAY_CONFIG_VERSION",
    "ResearchEventResolutionAuthoritySignalDecayConfig",
    "ResearchEventResolutionAuthoritySignalObservation",
    "ResearchEventResolutionAuthoritySignalDecayRow",
    "ResearchEventResolutionAuthoritySignalDecayReport",
    "build_research_event_resolution_authority_signal_decay_report",
    "research_event_resolution_authority_signal_decay_report_payload",
    "validate_research_event_resolution_authority_signal_decay_public_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthoritySignalDecayConfig:
    watch_signal_age_seconds: Decimal = Decimal("3600.000000")
    block_signal_age_seconds: Decimal = Decimal("14400.000000")
    watch_signal_score_threshold: Decimal = Decimal("0.500000")
    block_signal_score_threshold: Decimal = Decimal("0.250000")
    blocking_conflict_threshold: Decimal = Decimal("0.750000")
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_SIGNAL_DECAY_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthoritySignalDecayConfig, "config")
        object.__setattr__(
            self,
            "watch_signal_age_seconds",
            _require_positive_decimal(
                "watch_signal_age_seconds",
                self.watch_signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "block_signal_age_seconds",
            _require_positive_decimal(
                "block_signal_age_seconds",
                self.block_signal_age_seconds,
            ),
        )
        if self.block_signal_age_seconds <= self.watch_signal_age_seconds:
            raise ValueError(
                "block_signal_age_seconds must be greater than watch_signal_age_seconds",
            )
        for field_name in (
            "watch_signal_score_threshold",
            "block_signal_score_threshold",
            "blocking_conflict_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.block_signal_score_threshold >= self.watch_signal_score_threshold:
            raise ValueError(
                "block_signal_score_threshold must be less than "
                "watch_signal_score_threshold",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthoritySignalObservation:
    raw_candidate_ref: str
    authority_family: str
    authority_observed_at: datetime
    authority_score: Decimal
    source_consensus_score: Decimal
    contradictory_resolution_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthoritySignalObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "raw_candidate_ref",
            _require_public_string("raw_candidate_ref", self.raw_candidate_ref),
        )
        object.__setattr__(
            self,
            "authority_family",
            _require_public_string("authority_family", self.authority_family),
        )
        object.__setattr__(
            self,
            "authority_observed_at",
            _as_utc("authority_observed_at", self.authority_observed_at),
        )
        for field_name in (
            "authority_score",
            "source_consensus_score",
            "contradictory_resolution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthoritySignalDecayRow:
    redacted_candidate_ref: str
    authority_family: str
    authority_observed_at: datetime
    signal_age_seconds: Decimal
    decay_score: Decimal
    authority_score: Decimal
    source_consensus_score: Decimal
    contradictory_resolution_score: Decimal
    authority_signal_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthoritySignalDecayRow,
            "row",
        )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_public_string("redacted_candidate_ref", self.redacted_candidate_ref),
        )
        object.__setattr__(
            self,
            "authority_family",
            _require_public_string("authority_family", self.authority_family),
        )
        object.__setattr__(
            self,
            "authority_observed_at",
            _as_utc("authority_observed_at", self.authority_observed_at),
        )
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        for field_name in (
            "decay_score",
            "authority_score",
            "source_consensus_score",
            "contradictory_resolution_score",
            "authority_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthoritySignalDecayReport:
    generated_at: datetime
    config_version: str
    watch_signal_age_seconds: Decimal
    block_signal_age_seconds: Decimal
    watch_signal_score_threshold: Decimal
    block_signal_score_threshold: Decimal
    blocking_conflict_threshold: Decimal
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_signal_score: Decimal | None
    max_signal_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthoritySignalDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_signal_age_seconds",
            "block_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_signal_score_threshold",
            "block_signal_score_threshold",
            "blocking_conflict_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_signal_score",
            _require_optional_probability(
                "average_authority_signal_score",
                self.average_authority_signal_score,
            ),
        )
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_nonnegative_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_event_resolution_authority_signal_decay_report(
    observations: list[ResearchEventResolutionAuthoritySignalObservation]
    | tuple[ResearchEventResolutionAuthoritySignalObservation, ...],
    *,
    config: ResearchEventResolutionAuthoritySignalDecayConfig,
    generated_at: datetime,
) -> ResearchEventResolutionAuthoritySignalDecayReport:
    if type(config) is not ResearchEventResolutionAuthoritySignalDecayConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthoritySignalDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in _normalize_observations(observations)
            ),
            key=_row_sort_key,
        ),
    )
    signal_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    return ResearchEventResolutionAuthoritySignalDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_signal_age_seconds=config.watch_signal_age_seconds,
        block_signal_age_seconds=config.block_signal_age_seconds,
        watch_signal_score_threshold=config.watch_signal_score_threshold,
        block_signal_score_threshold=config.block_signal_score_threshold,
        blocking_conflict_threshold=config.blocking_conflict_threshold,
        signal_count=signal_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_authority_signal_score=_average_score(rows),
        max_signal_age_seconds=_max_decimal(row.signal_age_seconds for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_resolution_authority_signal_decay_report_payload(
    report: ResearchEventResolutionAuthoritySignalDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionAuthoritySignalDecayReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthoritySignalDecayReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_resolution_authority_signal_decay_public_payload(payload)
    return payload


def validate_research_event_resolution_authority_signal_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _reject_flag_downgrades("public payload", payload)
    _validate_payload_statuses(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_observation(
    observation: ResearchEventResolutionAuthoritySignalObservation,
    *,
    config: ResearchEventResolutionAuthoritySignalDecayConfig,
    generated_at: datetime,
) -> ResearchEventResolutionAuthoritySignalDecayRow:
    if type(observation) is not ResearchEventResolutionAuthoritySignalObservation:
        raise ValueError(
            "observation must be a ResearchEventResolutionAuthoritySignalObservation",
        )
    _require_hard_flags("observation", observation)
    if observation.authority_observed_at > generated_at:
        raise ValueError("authority_observed_at must not be in the future")
    signal_age_seconds = _seconds_between(observation.authority_observed_at, generated_at)
    decay_score = _decay_score(signal_age_seconds, config.block_signal_age_seconds)
    authority_signal_score = _score(
        observation.authority_score
        * observation.source_consensus_score
        * decay_score
        * (ONE - observation.contradictory_resolution_score),
    )
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        authority_signal_score=authority_signal_score,
        contradictory_resolution_score=observation.contradictory_resolution_score,
        config=config,
    )
    return ResearchEventResolutionAuthoritySignalDecayRow(
        redacted_candidate_ref=_redact_candidate_ref(observation.raw_candidate_ref),
        authority_family=observation.authority_family,
        authority_observed_at=observation.authority_observed_at,
        signal_age_seconds=signal_age_seconds,
        decay_score=decay_score,
        authority_score=observation.authority_score,
        source_consensus_score=observation.source_consensus_score,
        contradictory_resolution_score=observation.contradictory_resolution_score,
        authority_signal_score=authority_signal_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    authority_signal_score: Decimal,
    contradictory_resolution_score: Decimal,
    config: ResearchEventResolutionAuthoritySignalDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal_age_seconds > config.block_signal_age_seconds:
        reasons.append(BLOCK_DECAY_REASON)
    elif signal_age_seconds > config.watch_signal_age_seconds:
        reasons.append(WATCH_DECAY_REASON)
    if contradictory_resolution_score >= config.blocking_conflict_threshold:
        reasons.append(CONFLICT_REASON)
    if not reasons and authority_signal_score <= config.block_signal_score_threshold:
        reasons.append(BLOCK_LOW_SIGNAL_REASON)
    elif not reasons and authority_signal_score <= config.watch_signal_score_threshold:
        reasons.append(WATCH_LOW_SIGNAL_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        BLOCK_DECAY_REASON in reason_codes
        or CONFLICT_REASON in reason_codes
        or BLOCK_LOW_SIGNAL_REASON in reason_codes
    ):
        return "block"
    if WATCH_DECAY_REASON in reason_codes or WATCH_LOW_SIGNAL_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in TRIGGER_REASON_CODES
    }
    if not found:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _row_sort_key(
    row: ResearchEventResolutionAuthoritySignalDecayRow,
) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.signal_age_seconds,
        row.authority_family,
        row.redacted_candidate_ref,
    )


def _normalize_observations(
    observations: list[ResearchEventResolutionAuthoritySignalObservation]
    | tuple[ResearchEventResolutionAuthoritySignalObservation, ...],
) -> tuple[ResearchEventResolutionAuthoritySignalObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized: list[ResearchEventResolutionAuthoritySignalObservation] = []
    for observation in observations:
        if type(observation) is not ResearchEventResolutionAuthoritySignalObservation:
            raise ValueError(
                "observation must be a ResearchEventResolutionAuthoritySignalObservation",
            )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: list[ResearchEventResolutionAuthoritySignalDecayRow]
    | tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...],
) -> tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized: list[ResearchEventResolutionAuthoritySignalDecayRow] = []
    for row in rows:
        if type(row) is not ResearchEventResolutionAuthoritySignalDecayRow:
            raise ValueError(
                "row must be a ResearchEventResolutionAuthoritySignalDecayRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _validate_report_consistency(
    report: ResearchEventResolutionAuthoritySignalDecayReport,
) -> None:
    rows = report.rows
    expected_values = {
        "signal_count": _count(len(rows)),
        "pass_count": _count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _count(sum(1 for row in rows if row.status == "watch")),
        "block_count": _count(sum(1 for row in rows if row.status == "block")),
        "average_authority_signal_score": _average_score(rows),
        "max_signal_age_seconds": _max_decimal(row.signal_age_seconds for row in rows),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort order")


def _derived_validation_digest(
    report: ResearchEventResolutionAuthoritySignalDecayReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: ResearchEventResolutionAuthoritySignalDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _score(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _decay_score(signal_age_seconds: Decimal, block_signal_age_seconds: Decimal) -> Decimal:
    if signal_age_seconds >= block_signal_age_seconds:
        return ZERO
    return _score(ONE - (signal_age_seconds / block_signal_age_seconds))


def _average_score(
    rows: tuple[ResearchEventResolutionAuthoritySignalDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    total = sum((row.authority_signal_score for row in rows), ZERO)
    return (total / _count(len(rows))).quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Any) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return maximum


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return (microseconds / MICROSECONDS_PER_SECOND).quantize(
        SECOND_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redact_candidate_ref(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
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


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


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


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status" and (type(item) is not str or item not in STATUSES):
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    if "://" in normalized or normalized.startswith("www."):
        return True
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
