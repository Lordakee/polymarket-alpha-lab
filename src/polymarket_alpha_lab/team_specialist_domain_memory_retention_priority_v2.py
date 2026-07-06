"""Pure Phase 1 specialist domain memory retention priority report v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
DOMAIN_AGE_REFERENCE_DAYS = Decimal("60")
FORECAST_ERROR_REFERENCE_BPS = Decimal("500.000000")
EVENT_RECURRENCE_REFERENCE_COUNT_30D = Decimal("5")
EVENT_RECURRENCE_MAX_PRIORITY_BPS = Decimal("75.000000")
OPEN_EXPOSURE_MAX_PRIORITY_BPS = Decimal("125.000000")
SCORE_STATUSES = ("candidate", "watch", "blocked")
SCORE_DECISIONS = ("paper_candidate", "manual_review", "reject")
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "team_id",
    "specialist_id",
    "domain_id",
    "domain_age_days",
    "forecast_error_bps",
    "source_decay_ratio",
    "event_recurrence_count_30d",
    "open_market_exposure_usd",
    "exposure_reference_usd",
    "domain_age_priority_bps",
    "forecast_error_priority_bps",
    "source_decay_priority_bps",
    "event_recurrence_priority_bps",
    "open_market_exposure_priority_bps",
    "paper_score_bps",
    "minimum_actionable_score",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryRetentionPriorityV2Input:
    team_id: str
    specialist_id: str
    domain_id: str
    domain_age_days: Decimal
    forecast_error_bps: Decimal
    source_decay_ratio: Decimal
    event_recurrence_count_30d: Decimal
    open_market_exposure_usd: Decimal
    exposure_reference_usd: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("domain_id", self.domain_id)
        for field_name in (
            "domain_age_days",
            "forecast_error_bps",
            "open_market_exposure_usd",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_decay_ratio",
            _normalize_ratio("source_decay_ratio", self.source_decay_ratio),
        )
        object.__setattr__(
            self,
            "event_recurrence_count_30d",
            _normalize_count(
                "event_recurrence_count_30d",
                self.event_recurrence_count_30d,
            ),
        )
        object.__setattr__(
            self,
            "exposure_reference_usd",
            _normalize_positive_decimal(
                "exposure_reference_usd",
                self.exposure_reference_usd,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
            "specialist domain memory retention priority input",
            self,
        )
        _require_paper_flags("specialist domain memory retention priority input", self)


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryRetentionPriorityV2Result:
    team_id: str
    specialist_id: str
    domain_id: str
    domain_age_days: Decimal
    forecast_error_bps: Decimal
    source_decay_ratio: Decimal
    event_recurrence_count_30d: Decimal
    open_market_exposure_usd: Decimal
    exposure_reference_usd: Decimal
    domain_age_priority_bps: Decimal
    forecast_error_priority_bps: Decimal
    source_decay_priority_bps: Decimal
    event_recurrence_priority_bps: Decimal
    open_market_exposure_priority_bps: Decimal
    paper_score_bps: Decimal
    minimum_actionable_score: Decimal
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("domain_id", self.domain_id)
        for field_name in (
            "domain_age_days",
            "forecast_error_bps",
            "open_market_exposure_usd",
            "domain_age_priority_bps",
            "forecast_error_priority_bps",
            "source_decay_priority_bps",
            "event_recurrence_priority_bps",
            "open_market_exposure_priority_bps",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_decay_ratio",
            _normalize_ratio("source_decay_ratio", self.source_decay_ratio),
        )
        object.__setattr__(
            self,
            "event_recurrence_count_30d",
            _normalize_count(
                "event_recurrence_count_30d",
                self.event_recurrence_count_30d,
            ),
        )
        object.__setattr__(
            self,
            "exposure_reference_usd",
            _normalize_positive_decimal(
                "exposure_reference_usd",
                self.exposure_reference_usd,
            ),
        )
        object.__setattr__(
            self,
            "paper_score_bps",
            _normalize_decimal("paper_score_bps", self.paper_score_bps),
        )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
            "specialist domain memory retention priority result",
            self,
        )
        _require_paper_flags("specialist domain memory retention priority result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_domain_memory_retention_priority_v2_payload(self)


def estimate_team_specialist_domain_memory_retention_priority_v2(
    score_input: TeamSpecialistDomainMemoryRetentionPriorityV2Input,
) -> TeamSpecialistDomainMemoryRetentionPriorityV2Result:
    if type(score_input) is not TeamSpecialistDomainMemoryRetentionPriorityV2Input:
        raise ValueError(
            "score_input must be a TeamSpecialistDomainMemoryRetentionPriorityV2Input",
        )
    reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
        "specialist domain memory retention priority input",
        score_input,
    )
    _require_paper_flags("specialist domain memory retention priority input", score_input)

    domain_age_priority_bps = _domain_age_priority_bps(score_input.domain_age_days)
    forecast_error_priority_bps = _forecast_error_priority_bps(
        score_input.forecast_error_bps,
    )
    source_decay_priority_bps = _source_decay_priority_bps(
        score_input.source_decay_ratio,
    )
    event_recurrence_priority_bps = _event_recurrence_priority_bps(
        score_input.event_recurrence_count_30d,
    )
    open_market_exposure_priority_bps = _open_market_exposure_priority_bps(
        score_input.open_market_exposure_usd,
        score_input.exposure_reference_usd,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        domain_age_priority_bps
        + forecast_error_priority_bps
        + source_decay_priority_bps
        + event_recurrence_priority_bps
        + open_market_exposure_priority_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return TeamSpecialistDomainMemoryRetentionPriorityV2Result(
        team_id=score_input.team_id,
        specialist_id=score_input.specialist_id,
        domain_id=score_input.domain_id,
        domain_age_days=score_input.domain_age_days,
        forecast_error_bps=score_input.forecast_error_bps,
        source_decay_ratio=score_input.source_decay_ratio,
        event_recurrence_count_30d=score_input.event_recurrence_count_30d,
        open_market_exposure_usd=score_input.open_market_exposure_usd,
        exposure_reference_usd=score_input.exposure_reference_usd,
        domain_age_priority_bps=domain_age_priority_bps,
        forecast_error_priority_bps=forecast_error_priority_bps,
        source_decay_priority_bps=source_decay_priority_bps,
        event_recurrence_priority_bps=event_recurrence_priority_bps,
        open_market_exposure_priority_bps=open_market_exposure_priority_bps,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            domain_age_priority_bps=domain_age_priority_bps,
            forecast_error_priority_bps=forecast_error_priority_bps,
            source_decay_priority_bps=source_decay_priority_bps,
            event_recurrence_priority_bps=event_recurrence_priority_bps,
            open_market_exposure_priority_bps=open_market_exposure_priority_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def team_specialist_domain_memory_retention_priority_v2_payload(
    result: TeamSpecialistDomainMemoryRetentionPriorityV2Result,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistDomainMemoryRetentionPriorityV2Result:
        raise ValueError(
            "result must be a TeamSpecialistDomainMemoryRetentionPriorityV2Result",
        )
    _require_paper_flags("specialist domain memory retention priority result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
        "specialist domain memory retention priority result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _domain_age_priority_bps(domain_age_days: Decimal) -> Decimal:
    return _capped_priority_bps(
        "domain_age_priority_bps",
        domain_age_days,
        DOMAIN_AGE_REFERENCE_DAYS,
        HUNDRED,
    )


def _forecast_error_priority_bps(forecast_error_bps: Decimal) -> Decimal:
    return _capped_priority_bps(
        "forecast_error_priority_bps",
        forecast_error_bps,
        FORECAST_ERROR_REFERENCE_BPS,
        HUNDRED,
    )


def _source_decay_priority_bps(source_decay_ratio: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_decay_priority_bps",
        source_decay_ratio * HUNDRED,
    )


def _event_recurrence_priority_bps(event_recurrence_count_30d: Decimal) -> Decimal:
    return _capped_priority_bps(
        "event_recurrence_priority_bps",
        event_recurrence_count_30d,
        EVENT_RECURRENCE_REFERENCE_COUNT_30D,
        EVENT_RECURRENCE_MAX_PRIORITY_BPS,
    )


def _open_market_exposure_priority_bps(
    open_market_exposure_usd: Decimal,
    exposure_reference_usd: Decimal,
) -> Decimal:
    return _capped_priority_bps(
        "open_market_exposure_priority_bps",
        open_market_exposure_usd,
        exposure_reference_usd,
        OPEN_EXPOSURE_MAX_PRIORITY_BPS,
    )


def _capped_priority_bps(
    field_name: str,
    numerator: Decimal,
    denominator: Decimal,
    maximum_priority_bps: Decimal,
) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator >= denominator:
        return maximum_priority_bps
    return _normalize_nonnegative_decimal(
        field_name,
        numerator / denominator * maximum_priority_bps,
    )


def _score_status(paper_score_bps: Decimal, minimum_actionable_score: Decimal) -> str:
    if paper_score_bps <= ZERO:
        return "blocked"
    if paper_score_bps < minimum_actionable_score:
        return "watch"
    return "candidate"


def _score_decision(score_status: str) -> str:
    if score_status == "candidate":
        return "paper_candidate"
    if score_status == "watch":
        return "manual_review"
    if score_status == "blocked":
        return "reject"
    raise ValueError("score_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    domain_age_priority_bps: Decimal,
    forecast_error_priority_bps: Decimal,
    source_decay_priority_bps: Decimal,
    event_recurrence_priority_bps: Decimal,
    open_market_exposure_priority_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "team_specialist_domain_memory_retention_priority_v2",
        f"score_{score_status}",
    ]
    if domain_age_priority_bps > ZERO:
        additions.append("domain_age_pressure_present")
    if forecast_error_priority_bps > ZERO:
        additions.append("forecast_error_present")
    if source_decay_priority_bps > ZERO:
        additions.append("source_decay_present")
    if event_recurrence_priority_bps > ZERO:
        additions.append("event_recurrence_present")
    if open_market_exposure_priority_bps > ZERO:
        additions.append("open_market_exposure_present")
    if paper_score_bps <= ZERO:
        additions.append("score_below_zero")
    elif paper_score_bps < minimum_actionable_score:
        additions.append("score_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(
    result: TeamSpecialistDomainMemoryRetentionPriorityV2Result,
) -> None:
    if result.domain_age_priority_bps != _domain_age_priority_bps(
        result.domain_age_days,
    ):
        raise ValueError("domain_age_priority_bps must match domain_age_days")
    if result.forecast_error_priority_bps != _forecast_error_priority_bps(
        result.forecast_error_bps,
    ):
        raise ValueError("forecast_error_priority_bps must match forecast_error_bps")
    if result.source_decay_priority_bps != _source_decay_priority_bps(
        result.source_decay_ratio,
    ):
        raise ValueError("source_decay_priority_bps must match source_decay_ratio")
    if result.event_recurrence_priority_bps != _event_recurrence_priority_bps(
        result.event_recurrence_count_30d,
    ):
        raise ValueError(
            "event_recurrence_priority_bps must match event_recurrence_count_30d",
        )
    if result.open_market_exposure_priority_bps != _open_market_exposure_priority_bps(
        result.open_market_exposure_usd,
        result.exposure_reference_usd,
    ):
        raise ValueError(
            "open_market_exposure_priority_bps must match exposure inputs",
        )
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.domain_age_priority_bps
        + result.forecast_error_priority_bps
        + result.source_decay_priority_bps
        + result.event_recurrence_priority_bps
        + result.open_market_exposure_priority_bps,
    ):
        raise ValueError("paper_score_bps must match priority components")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: TeamSpecialistDomainMemoryRetentionPriorityV2Result,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
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


__all__ = (
    "SCORE_STATUSES",
    "SCORE_DECISIONS",
    "TeamSpecialistDomainMemoryRetentionPriorityV2Input",
    "TeamSpecialistDomainMemoryRetentionPriorityV2Result",
    "estimate_team_specialist_domain_memory_retention_priority_v2",
    "team_specialist_domain_memory_retention_priority_v2_payload",
    "reject_team_specialist_domain_memory_retention_priority_v2_unsafe_payload",
)
