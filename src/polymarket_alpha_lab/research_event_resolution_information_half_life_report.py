"""Report-only event resolution information half-life triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION = (
    "research-event-resolution-information-half-life-report-v1"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "information_half_life_clear",
    "information_half_life_expired",
    "information_half_life_near_expiry",
    "information_half_life_low_independence",
    "information_half_life_contradiction_pressure",
    "information_half_life_unresolved_claim_pressure",
    "information_half_life_deadline_pressure",
)
REPORT_REASON_CODES = (
    "information_half_life_empty",
    "information_half_life_clear",
    "information_half_life_expired",
    "information_half_life_near_expiry",
    "information_half_life_low_independence",
    "information_half_life_contradiction_pressure",
    "information_half_life_unresolved_claim_pressure",
    "information_half_life_deadline_pressure",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_QUANTIZED = Decimal("0.000000")
ONE_QUANTIZED = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
PUBLIC_SURFACE_FRAGMENTS = (
    "raw_",
    "_id",
    "id_",
    "condition",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "http",
    "text",
    "dsn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
)

REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "event_count",
    "pass_count",
    "watch_count",
    "block_count",
    "half_life_pressure_count",
    "low_independence_count",
    "contradiction_pressure_count",
    "unresolved_claim_pressure_count",
    "deadline_pressure_count",
    "min_half_life_remaining_seconds",
    "max_age_to_half_life_ratio",
    "average_half_life_remaining_seconds",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "information_age_seconds",
    "information_half_life_seconds",
    "half_life_remaining_seconds",
    "age_to_half_life_ratio",
    "independent_signal_count",
    "contradiction_pressure",
    "unresolved_claim_count",
    "deadline_proximity_seconds",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DIGEST_KEYS = tuple(
    key for key in REPORT_PAYLOAD_KEYS if key != "derived_validation_digest"
)
ROW_PAYLOAD_KEYS = (
    "public_event_key",
    "status",
    "latest_information_at",
    "resolution_deadline_at",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchEventResolutionInformationHalfLifeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION
    )
    watch_age_to_half_life_ratio: Decimal = Decimal("0.500000")
    block_age_to_half_life_ratio: Decimal = Decimal("1.000000")
    minimum_independent_signal_count: Decimal = Decimal("2")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.700000")
    unresolved_claim_watch_threshold: Decimal = Decimal("2")
    unresolved_claim_block_threshold: Decimal = Decimal("4")
    deadline_watch_seconds: Decimal = Decimal("7200.000000")
    deadline_block_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionInformationHalfLifeConfig,
            "config",
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "watch_age_to_half_life_ratio",
            "block_age_to_half_life_ratio",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_independent_signal_count",
            "unresolved_claim_watch_threshold",
            "unresolved_claim_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("deadline_watch_seconds", "deadline_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_age_to_half_life_ratio < self.watch_age_to_half_life_ratio:
            raise ValueError(
                "block_age_to_half_life_ratio must be at least watch_age_to_half_life_ratio",
            )
        if self.contradiction_block_threshold < self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction_block_threshold must be at least contradiction_watch_threshold",
            )
        if self.unresolved_claim_block_threshold < self.unresolved_claim_watch_threshold:
            raise ValueError(
                "unresolved_claim_block_threshold must be at least "
                "unresolved_claim_watch_threshold",
            )
        if self.deadline_block_seconds > self.deadline_watch_seconds:
            raise ValueError("deadline_block_seconds must not exceed deadline_watch_seconds")
        require_paper_only_flags("information half life config", self)
        _reject_public_payload("information half life config", self)


@dataclass(frozen=True)
class ResearchEventResolutionInformationHalfLifeObservation:
    public_event_key: str
    latest_information_at: datetime
    resolution_deadline_at: datetime
    information_half_life_seconds: Decimal
    independent_signal_count: Decimal
    contradiction_pressure: Decimal = Decimal("0.000000")
    unresolved_claim_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionInformationHalfLifeObservation,
            "observation",
        )
        _require_public_string("public_event_key", self.public_event_key)
        object.__setattr__(
            self,
            "latest_information_at",
            _as_utc("latest_information_at", self.latest_information_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        object.__setattr__(
            self,
            "information_half_life_seconds",
            _require_positive_seconds_decimal(
                "information_half_life_seconds",
                self.information_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "independent_signal_count",
            _require_nonnegative_count_decimal(
                "independent_signal_count",
                self.independent_signal_count,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        object.__setattr__(
            self,
            "unresolved_claim_count",
            _require_nonnegative_count_decimal(
                "unresolved_claim_count",
                self.unresolved_claim_count,
            ),
        )
        require_paper_only_flags("information half life observation", self)
        _reject_public_payload("information half life observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionInformationHalfLifeRow:
    public_event_key: str
    status: str
    latest_information_at: datetime
    resolution_deadline_at: datetime
    information_age_seconds: Decimal
    information_half_life_seconds: Decimal
    half_life_remaining_seconds: Decimal
    age_to_half_life_ratio: Decimal
    independent_signal_count: Decimal
    contradiction_pressure: Decimal
    unresolved_claim_count: Decimal
    deadline_proximity_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionInformationHalfLifeRow, "row")
        _require_public_string("public_event_key", self.public_event_key)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "latest_information_at",
            _as_utc("latest_information_at", self.latest_information_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "information_age_seconds",
            "half_life_remaining_seconds",
            "deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "information_half_life_seconds",
            _require_positive_seconds_decimal(
                "information_half_life_seconds",
                self.information_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "age_to_half_life_ratio",
            _require_nonnegative_decimal(
                "age_to_half_life_ratio",
                self.age_to_half_life_ratio,
            ),
        )
        for field_name in ("independent_signal_count", "unresolved_claim_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("information half life row", self)
        _reject_public_payload("information half life row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventResolutionInformationHalfLifeReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    half_life_pressure_count: Decimal
    low_independence_count: Decimal
    contradiction_pressure_count: Decimal
    unresolved_claim_pressure_count: Decimal
    deadline_pressure_count: Decimal
    min_half_life_remaining_seconds: Decimal
    max_age_to_half_life_ratio: Decimal
    average_half_life_remaining_seconds: Decimal
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionInformationHalfLifeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "half_life_pressure_count",
            "low_independence_count",
            "contradiction_pressure_count",
            "unresolved_claim_pressure_count",
            "deadline_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_half_life_remaining_seconds",
            "average_half_life_remaining_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_age_to_half_life_ratio",
            _require_nonnegative_decimal(
                "max_age_to_half_life_ratio",
                self.max_age_to_half_life_ratio,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("information half life report", self)
        _reject_public_payload("information half life report", self)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_information_half_life_report_to_payload(self)


def build_research_event_resolution_information_half_life_report(
    observations: Iterable[ResearchEventResolutionInformationHalfLifeObservation],
    *,
    config: ResearchEventResolutionInformationHalfLifeConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionInformationHalfLifeReport:
    if config is None:
        config = ResearchEventResolutionInformationHalfLifeConfig()
    if type(config) is not ResearchEventResolutionInformationHalfLifeConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionInformationHalfLifeConfig",
        )
    require_paper_only_flags("information half life config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _validate_observation_times(normalized_observations, generated_at_utc)

    rows = _sort_rows(
        tuple(
            _row_from_observation(
                observation,
                config=config,
                generated_at=generated_at_utc,
            )
            for observation in normalized_observations
        ),
    )
    remaining_values = tuple(row.half_life_remaining_seconds for row in rows)
    ratio_values = tuple(row.age_to_half_life_ratio for row in rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "half_life_pressure_count": _half_life_pressure_count(rows),
        "low_independence_count": _reason_count(
            rows,
            "information_half_life_low_independence",
        ),
        "contradiction_pressure_count": _reason_count(
            rows,
            "information_half_life_contradiction_pressure",
        ),
        "unresolved_claim_pressure_count": _reason_count(
            rows,
            "information_half_life_unresolved_claim_pressure",
        ),
        "deadline_pressure_count": _reason_count(
            rows,
            "information_half_life_deadline_pressure",
        ),
        "min_half_life_remaining_seconds": min(
            remaining_values,
            default=ZERO_QUANTIZED,
        ),
        "max_age_to_half_life_ratio": max(ratio_values, default=ZERO_QUANTIZED),
        "average_half_life_remaining_seconds": _average_seconds(remaining_values),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionInformationHalfLifeReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_information_half_life_report_to_payload(
    report: ResearchEventResolutionInformationHalfLifeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionInformationHalfLifeReport:
        raise ValueError(
            "report must be a ResearchEventResolutionInformationHalfLifeReport",
        )
    require_paper_only_flags("information half life report", report)
    _reject_public_payload("information half life report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("information half life report payload must be a JSON object")
    validate_research_event_resolution_information_half_life_public_payload(payload)
    return payload


def validate_research_event_resolution_information_half_life_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_public_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row_payload in payload["rows"]:
        _validate_public_row_payload(row_payload)
    _normalize_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        allowed=REPORT_REASON_CODES,
        allow_empty=False,
    )
    _require_sha256_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _reject_public_numerics(payload)
    expected_digest = _payload_digest_without_validation(payload)
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    _reject_public_payload("information half life public payload", payload)


def _row_from_observation(
    observation: ResearchEventResolutionInformationHalfLifeObservation,
    *,
    config: ResearchEventResolutionInformationHalfLifeConfig,
    generated_at: datetime,
) -> ResearchEventResolutionInformationHalfLifeRow:
    age_seconds = _duration_seconds(observation.latest_information_at, generated_at)
    remaining_seconds = _half_life_remaining_seconds(
        information_half_life_seconds=observation.information_half_life_seconds,
        information_age_seconds=age_seconds,
    )
    age_ratio = _age_to_half_life_ratio(
        information_age_seconds=age_seconds,
        information_half_life_seconds=observation.information_half_life_seconds,
    )
    deadline_seconds = _deadline_proximity_seconds(
        generated_at,
        observation.resolution_deadline_at,
    )
    reason_codes = _row_reason_codes(
        age_to_half_life_ratio=age_ratio,
        independent_signal_count=observation.independent_signal_count,
        contradiction_pressure=observation.contradiction_pressure,
        unresolved_claim_count=observation.unresolved_claim_count,
        deadline_proximity_seconds=deadline_seconds,
        config=config,
    )
    return ResearchEventResolutionInformationHalfLifeRow(
        public_event_key=observation.public_event_key,
        status=_row_status(
            reason_codes=reason_codes,
            age_to_half_life_ratio=age_ratio,
            contradiction_pressure=observation.contradiction_pressure,
            unresolved_claim_count=observation.unresolved_claim_count,
            deadline_proximity_seconds=deadline_seconds,
            config=config,
        ),
        latest_information_at=observation.latest_information_at,
        resolution_deadline_at=observation.resolution_deadline_at,
        information_age_seconds=age_seconds,
        information_half_life_seconds=observation.information_half_life_seconds,
        half_life_remaining_seconds=remaining_seconds,
        age_to_half_life_ratio=age_ratio,
        independent_signal_count=observation.independent_signal_count,
        contradiction_pressure=observation.contradiction_pressure,
        unresolved_claim_count=observation.unresolved_claim_count,
        deadline_proximity_seconds=deadline_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    age_to_half_life_ratio: Decimal,
    independent_signal_count: Decimal,
    contradiction_pressure: Decimal,
    unresolved_claim_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchEventResolutionInformationHalfLifeConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if age_to_half_life_ratio >= config.block_age_to_half_life_ratio:
        reasons.append("information_half_life_expired")
    elif age_to_half_life_ratio >= config.watch_age_to_half_life_ratio:
        reasons.append("information_half_life_near_expiry")
    if independent_signal_count < config.minimum_independent_signal_count:
        reasons.append("information_half_life_low_independence")
    if contradiction_pressure >= config.contradiction_watch_threshold:
        reasons.append("information_half_life_contradiction_pressure")
    if unresolved_claim_count >= config.unresolved_claim_watch_threshold:
        reasons.append("information_half_life_unresolved_claim_pressure")
    if deadline_proximity_seconds <= config.deadline_watch_seconds:
        reasons.append("information_half_life_deadline_pressure")
    if not reasons:
        return ("information_half_life_clear",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        allowed=ROW_REASON_CODES,
        allow_empty=False,
    )


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    age_to_half_life_ratio: Decimal,
    contradiction_pressure: Decimal,
    unresolved_claim_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchEventResolutionInformationHalfLifeConfig,
) -> str:
    if (
        age_to_half_life_ratio >= config.block_age_to_half_life_ratio
        or contradiction_pressure >= config.contradiction_block_threshold
        or unresolved_claim_count >= config.unresolved_claim_block_threshold
        or deadline_proximity_seconds <= config.deadline_block_seconds
    ):
        return "block"
    if reason_codes != ("information_half_life_clear",):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("information_half_life_empty",)
    issue_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code
        not in (
            "information_half_life_empty",
            "information_half_life_clear",
        )
        and any(reason_code in row.reason_codes for row in rows)
    )
    if issue_codes:
        return issue_codes
    return ("information_half_life_clear",)


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionInformationHalfLifeObservation],
) -> tuple[ResearchEventResolutionInformationHalfLifeObservation, ...]:
    if isinstance(observations, str | bytes):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchEventResolutionInformationHalfLifeObservation:
            raise ValueError("observations must contain exact observation values")
        require_paper_only_flags("information half life observation", observation)
        if observation.public_event_key in seen:
            raise ValueError("public_event_key values must be unique")
        seen.add(observation.public_event_key)
    return tuple(
        sorted(
            normalized,
            key=lambda observation: (
                observation.public_event_key,
                observation.latest_information_at,
                observation.resolution_deadline_at,
            ),
        ),
    )


def _validate_observation_times(
    observations: tuple[ResearchEventResolutionInformationHalfLifeObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.latest_information_at > generated_at:
            raise ValueError("latest_information_at must be <= generated_at")


def _sort_rows(
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...],
) -> tuple[ResearchEventResolutionInformationHalfLifeRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventResolutionInformationHalfLifeRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.deadline_proximity_seconds,
        -row.age_to_half_life_ratio,
        row.public_event_key,
    )


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionInformationHalfLifeRow],
) -> tuple[ResearchEventResolutionInformationHalfLifeRow, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionInformationHalfLifeRow:
            raise ValueError("rows must contain exact information half life rows")
        require_paper_only_flags("information half life row", row)
        if row.public_event_key in seen:
            raise ValueError("rows public_event_key values must be unique")
        seen.add(row.public_event_key)
    if normalized != _sort_rows(normalized):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _validate_row(row: ResearchEventResolutionInformationHalfLifeRow) -> None:
    if row.status == "pass" and row.reason_codes != ("information_half_life_clear",):
        raise ValueError("pass rows must have the clear reason code")
    if row.status != "pass" and row.reason_codes == ("information_half_life_clear",):
        raise ValueError("non-pass rows must not have the clear reason code")
    expected_remaining = _half_life_remaining_seconds(
        information_half_life_seconds=row.information_half_life_seconds,
        information_age_seconds=row.information_age_seconds,
    )
    if row.half_life_remaining_seconds != expected_remaining:
        raise ValueError("half_life_remaining_seconds must match row values")
    expected_ratio = _age_to_half_life_ratio(
        information_age_seconds=row.information_age_seconds,
        information_half_life_seconds=row.information_half_life_seconds,
    )
    if row.age_to_half_life_ratio != expected_ratio:
        raise ValueError("age_to_half_life_ratio must match row values")


def _validate_report(report: ResearchEventResolutionInformationHalfLifeReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    for status in STATUSES:
        field_name = f"{status}_count"
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_count_fields = {
        "low_independence_count": "information_half_life_low_independence",
        "contradiction_pressure_count": "information_half_life_contradiction_pressure",
        "unresolved_claim_pressure_count": (
            "information_half_life_unresolved_claim_pressure"
        ),
        "deadline_pressure_count": "information_half_life_deadline_pressure",
    }
    for field_name, reason_code in expected_reason_count_fields.items():
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.half_life_pressure_count != _half_life_pressure_count(report.rows):
        raise ValueError("half_life_pressure_count must match rows")
    remaining_values = tuple(row.half_life_remaining_seconds for row in report.rows)
    ratio_values = tuple(row.age_to_half_life_ratio for row in report.rows)
    if report.min_half_life_remaining_seconds != min(
        remaining_values,
        default=ZERO_QUANTIZED,
    ):
        raise ValueError("min_half_life_remaining_seconds must match rows")
    if report.max_age_to_half_life_ratio != max(ratio_values, default=ZERO_QUANTIZED):
        raise ValueError("max_age_to_half_life_ratio must match rows")
    if report.average_half_life_remaining_seconds != _average_seconds(remaining_values):
        raise ValueError("average_half_life_remaining_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _reject_unknown_payload_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_public_string("public_event_key", value["public_event_key"])
    _require_status("status", value["status"])
    _require_public_string("latest_information_at", value["latest_information_at"])
    _require_public_string(
        "resolution_deadline_at",
        value["resolution_deadline_at"],
    )
    for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    _normalize_reason_codes(
        "reason_codes",
        value["reason_codes"],
        allowed=ROW_REASON_CODES,
        allow_empty=False,
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _reject_public_payload("information half life row payload", value)


def _status_count(
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _half_life_pressure_count(
    rows: tuple[ResearchEventResolutionInformationHalfLifeRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if (
                "information_half_life_expired" in row.reason_codes
                or "information_half_life_near_expiry" in row.reason_codes
            )
        ),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_seconds(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_QUANTIZED
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_QUANTIZED) / Decimal(len(values))).quantize(QUANTUM)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO_QUANTIZED:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(QUANTUM)


def _deadline_proximity_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    if deadline_at <= generated_at:
        return ZERO_QUANTIZED
    return _duration_seconds(generated_at, deadline_at)


def _half_life_remaining_seconds(
    *,
    information_half_life_seconds: Decimal,
    information_age_seconds: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        remaining = information_half_life_seconds - information_age_seconds
    if remaining <= ZERO_QUANTIZED:
        return ZERO_QUANTIZED
    return remaining.quantize(QUANTUM)


def _age_to_half_life_ratio(
    *,
    information_age_seconds: Decimal,
    information_half_life_seconds: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (information_age_seconds / information_half_life_seconds).quantize(QUANTUM)


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_seconds_decimal(field_name, value)
    if decimal_value <= ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        quantized = decimal_value.quantize(QUANTUM)
    if quantized < ZERO_QUANTIZED or quantized > ONE_QUANTIZED:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(reason_code for reason_code in allowed if reason_code in reason_codes) != (
        reason_codes
    ):
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_fragment(field_name, value)
    return value


def _require_supported_config_version(value: object) -> None:
    _require_public_string("config_version", value)
    if (
        value
        != DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exact")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


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


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _report_values_without_digest(
    report: ResearchEventResolutionInformationHalfLifeReport,
) -> dict[str, object]:
    return {key: getattr(report, key) for key in REPORT_DIGEST_KEYS}


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _canonical_digest(json_ready_no_floats(values))


def _payload_digest_without_validation(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return _canonical_digest(unsigned)


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionInformationHalfLifeConfig",
    "ResearchEventResolutionInformationHalfLifeObservation",
    "ResearchEventResolutionInformationHalfLifeReport",
    "ResearchEventResolutionInformationHalfLifeRow",
    "build_research_event_resolution_information_half_life_report",
    "research_event_resolution_information_half_life_report_to_payload",
    "validate_research_event_resolution_information_half_life_public_payload",
)
