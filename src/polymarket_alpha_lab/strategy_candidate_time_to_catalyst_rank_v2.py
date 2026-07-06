"""Readonly time-to-catalyst ranking for Phase 1 paper reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_TIME_TO_CATALYST_RANK_V2_CONFIG_VERSION = (
    "strategy-candidate-time-to-catalyst-rank-v2"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_VALUE_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")

_ROW_STATUSES = ("near_term", "scheduled", "stale", "out_of_window")
_REPORT_STATUSES = ("ranked", "empty")
_ROW_REASON_CODES = (
    "near_term_catalyst_boost",
    "future_catalyst_ranked",
    "stale_catalyst_penalty",
    "distant_catalyst_watch",
)
_REPORT_REASON_CODES = (
    "catalyst_candidates_ranked",
    "no_catalyst_candidates",
    "near_term_catalyst_boost",
    "stale_catalyst_penalty",
    "distant_catalyst_watch",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_TIME_TO_CATALYST_RANK_V2_CONFIG_VERSION",
    "StrategyCandidateTimeToCatalystRankV2Config",
    "StrategyCandidateTimeToCatalystRankV2Candidate",
    "StrategyCandidateTimeToCatalystRankV2Row",
    "StrategyCandidateTimeToCatalystRankV2Report",
    "build_strategy_candidate_time_to_catalyst_rank_v2",
    "strategy_candidate_time_to_catalyst_rank_v2_payload",
)


@dataclass(frozen=True)
class StrategyCandidateTimeToCatalystRankV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_TIME_TO_CATALYST_RANK_V2_CONFIG_VERSION
    )
    maximum_catalyst_window_days: Decimal = Decimal("30.000000")
    near_term_window_days: Decimal = Decimal("7.000000")
    base_score_weight: Decimal = Decimal("0.600000")
    relevance_score_weight: Decimal = Decimal("0.250000")
    timing_score_weight: Decimal = Decimal("0.150000")
    near_term_catalyst_boost: Decimal = Decimal("0.150000")
    stale_catalyst_penalty: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Config", self)
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        for field_name in (
            "maximum_catalyst_window_days",
            "near_term_window_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.maximum_catalyst_window_days <= _ZERO:
            raise ValueError("maximum_catalyst_window_days must be > 0.000000")
        if self.near_term_window_days > self.maximum_catalyst_window_days:
            raise ValueError("near_term_window_days must be <= maximum_catalyst_window_days")
        for field_name in (
            "base_score_weight",
            "relevance_score_weight",
            "timing_score_weight",
            "near_term_catalyst_boost",
            "stale_catalyst_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateTimeToCatalystRankV2Candidate:
    candidate_id: str
    market_slug: str
    event_id: str
    catalyst_reference: str
    observed_at: datetime
    catalyst_at: datetime
    base_research_score: Decimal
    catalyst_relevance_score: Decimal
    evidence_freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Candidate", self)
        for field_name in (
            "candidate_id",
            "market_slug",
            "event_id",
            "catalyst_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        for field_name in (
            "base_research_score",
            "catalyst_relevance_score",
            "evidence_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Candidate",
            self.payload,
        )

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Candidate.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


@dataclass(frozen=True)
class StrategyCandidateTimeToCatalystRankV2Row:
    candidate_id: str
    market_slug: str
    event_id: str
    catalyst_reference: str
    observed_at: datetime
    catalyst_at: datetime
    days_to_catalyst: Decimal
    timing_score: Decimal
    base_research_score: Decimal
    catalyst_relevance_score: Decimal
    evidence_freshness_score: Decimal
    near_term_boost: Decimal
    stale_penalty: Decimal
    catalyst_rank_score: Decimal
    catalyst_rank: Decimal
    catalyst_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Row", self)
        for field_name in (
            "candidate_id",
            "market_slug",
            "event_id",
            "catalyst_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        for field_name in (
            "timing_score",
            "base_research_score",
            "catalyst_relevance_score",
            "evidence_freshness_score",
            "near_term_boost",
            "stale_penalty",
            "catalyst_rank_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "days_to_catalyst",
            _normalize_decimal("days_to_catalyst", self.days_to_catalyst),
        )
        object.__setattr__(
            self,
            "catalyst_rank",
            _normalize_positive_integral_decimal("catalyst_rank", self.catalyst_rank),
        )
        _require_member("catalyst_status", self.catalyst_status, _ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row_reason_codes(self)
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateTimeToCatalystRankV2Report:
    generated_at: datetime
    config_version: str
    catalyst_rank_status: str
    candidate_count: Decimal
    near_term_candidate_count: Decimal
    stale_candidate_count: Decimal
    top_candidate_id: str | None
    top_catalyst_rank_score: Decimal | None
    average_days_to_catalyst: Decimal
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        _require_member("catalyst_rank_status", self.catalyst_rank_status, _REPORT_STATUSES)
        for field_name in (
            "candidate_count",
            "near_term_candidate_count",
            "stale_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            object.__setattr__(
                self,
                "top_candidate_id",
                _require_public_text("top_candidate_id", self.top_candidate_id),
            )
        if self.top_catalyst_rank_score is not None:
            object.__setattr__(
                self,
                "top_catalyst_rank_score",
                _normalize_ratio("top_catalyst_rank_score", self.top_catalyst_rank_score),
            )
        object.__setattr__(
            self,
            "average_days_to_catalyst",
            _normalize_decimal("average_days_to_catalyst", self.average_days_to_catalyst),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        expected_digest = _derived_validation_digest(asdict(self))
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Report",
            self.payload,
        )

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyCandidateTimeToCatalystRankV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_candidate_time_to_catalyst_rank_v2(
    candidates: object,
    *,
    config: StrategyCandidateTimeToCatalystRankV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateTimeToCatalystRankV2Report:
    if config is None:
        config = StrategyCandidateTimeToCatalystRankV2Config()
    if type(config) is not StrategyCandidateTimeToCatalystRankV2Config:
        raise ValueError("config must be StrategyCandidateTimeToCatalystRankV2Config")
    _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    unranked_rows = tuple(
        _row_from_candidate(candidate, config=config, generated_at=generated_at_utc)
        for candidate in normalized_candidates
    )
    rows = _ranked_rows(unranked_rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "catalyst_rank_status": "ranked" if rows else "empty",
        "candidate_count": _count(len(rows)),
        "near_term_candidate_count": _status_count(rows, "near_term"),
        "stale_candidate_count": _status_count(rows, "stale"),
        "top_candidate_id": rows[0].candidate_id if rows else None,
        "top_catalyst_rank_score": rows[0].catalyst_rank_score if rows else None,
        "average_days_to_catalyst": _average_days_to_catalyst(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyCandidateTimeToCatalystRankV2Report(**values)


def strategy_candidate_time_to_catalyst_rank_v2_payload(
    report: StrategyCandidateTimeToCatalystRankV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateTimeToCatalystRankV2Report:
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Report", report)
        return report.payload
    if type(report) is dict:
        payload = _copy_payload(report)
        _require_payload_flags(payload)
        _reject_unsafe_public_payload("payload", payload)
        _require_payload_digest(payload)
        return payload
    raise ValueError("report must be StrategyCandidateTimeToCatalystRankV2Report")


def _row_from_candidate(
    candidate: StrategyCandidateTimeToCatalystRankV2Candidate,
    *,
    config: StrategyCandidateTimeToCatalystRankV2Config,
    generated_at: datetime,
) -> StrategyCandidateTimeToCatalystRankV2Row:
    days_to_catalyst = _days_between(generated_at, candidate.catalyst_at)
    timing_score = _timing_score(days_to_catalyst, config.maximum_catalyst_window_days)
    near_term_boost = (
        config.near_term_catalyst_boost
        if _ZERO <= days_to_catalyst <= config.near_term_window_days
        else _ZERO
    )
    stale_penalty = config.stale_catalyst_penalty if days_to_catalyst < _ZERO else _ZERO
    catalyst_rank_score = _rank_score(
        candidate,
        config=config,
        timing_score=timing_score,
        near_term_boost=near_term_boost,
        stale_penalty=stale_penalty,
    )
    catalyst_status = _row_status(
        days_to_catalyst,
        maximum_window_days=config.maximum_catalyst_window_days,
        near_term_window_days=config.near_term_window_days,
    )
    return StrategyCandidateTimeToCatalystRankV2Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        event_id=candidate.event_id,
        catalyst_reference=candidate.catalyst_reference,
        observed_at=candidate.observed_at,
        catalyst_at=candidate.catalyst_at,
        days_to_catalyst=days_to_catalyst,
        timing_score=timing_score,
        base_research_score=candidate.base_research_score,
        catalyst_relevance_score=candidate.catalyst_relevance_score,
        evidence_freshness_score=candidate.evidence_freshness_score,
        near_term_boost=near_term_boost,
        stale_penalty=stale_penalty,
        catalyst_rank_score=catalyst_rank_score,
        catalyst_rank=Decimal("1"),
        catalyst_status=catalyst_status,
        reason_codes=_row_reason_codes(catalyst_status),
    )


def _ranked_rows(
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...],
) -> tuple[StrategyCandidateTimeToCatalystRankV2Row, ...]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.catalyst_rank_score,
            row.days_to_catalyst,
            row.candidate_id,
            row.market_slug,
        ),
    )
    return tuple(
        StrategyCandidateTimeToCatalystRankV2Row(
            candidate_id=row.candidate_id,
            market_slug=row.market_slug,
            event_id=row.event_id,
            catalyst_reference=row.catalyst_reference,
            observed_at=row.observed_at,
            catalyst_at=row.catalyst_at,
            days_to_catalyst=row.days_to_catalyst,
            timing_score=row.timing_score,
            base_research_score=row.base_research_score,
            catalyst_relevance_score=row.catalyst_relevance_score,
            evidence_freshness_score=row.evidence_freshness_score,
            near_term_boost=row.near_term_boost,
            stale_penalty=row.stale_penalty,
            catalyst_rank_score=row.catalyst_rank_score,
            catalyst_rank=_count(index),
            catalyst_status=row.catalyst_status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _rank_score(
    candidate: StrategyCandidateTimeToCatalystRankV2Candidate,
    *,
    config: StrategyCandidateTimeToCatalystRankV2Config,
    timing_score: Decimal,
    near_term_boost: Decimal,
    stale_penalty: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        raw_score = (
            candidate.base_research_score * config.base_score_weight
            + candidate.catalyst_relevance_score * config.relevance_score_weight
            + timing_score * config.timing_score_weight
            + candidate.evidence_freshness_score * Decimal("0.000000")
            + near_term_boost
            - stale_penalty
        )
    return _clamp_unit(raw_score)


def _days_between(start_at: datetime, end_at: datetime) -> Decimal:
    seconds = Decimal(str((end_at - start_at).total_seconds()))
    with localcontext(_DECIMAL_CONTEXT):
        return (seconds / _SECONDS_PER_DAY).quantize(_VALUE_QUANT)


def _timing_score(days_to_catalyst: Decimal, maximum_window_days: Decimal) -> Decimal:
    if days_to_catalyst < _ZERO or days_to_catalyst > maximum_window_days:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return ((maximum_window_days - days_to_catalyst) / maximum_window_days).quantize(
            _VALUE_QUANT,
        )


def _row_status(
    days_to_catalyst: Decimal,
    *,
    maximum_window_days: Decimal,
    near_term_window_days: Decimal,
) -> str:
    if days_to_catalyst < _ZERO:
        return "stale"
    if days_to_catalyst <= near_term_window_days:
        return "near_term"
    if days_to_catalyst <= maximum_window_days:
        return "scheduled"
    return "out_of_window"


def _row_reason_codes(catalyst_status: str) -> tuple[str, ...]:
    if catalyst_status == "near_term":
        return ("near_term_catalyst_boost", "future_catalyst_ranked")
    if catalyst_status == "stale":
        return ("stale_catalyst_penalty",)
    if catalyst_status == "out_of_window":
        return ("distant_catalyst_watch",)
    return ("future_catalyst_ranked",)


def _report_reason_codes(
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_catalyst_candidates",)
    reasons = ["catalyst_candidates_ranked"]
    for reason in (
        "near_term_catalyst_boost",
        "stale_catalyst_penalty",
        "distant_catalyst_watch",
    ):
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _status_count(
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.catalyst_status == status))


def _average_days_to_catalyst(
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (sum(row.days_to_catalyst for row in rows) / Decimal(len(rows))).quantize(
            _VALUE_QUANT,
        )


def _normalize_candidates(
    value: object,
) -> tuple[StrategyCandidateTimeToCatalystRankV2Candidate, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("candidates must be an iterable")
    candidates = tuple(value)
    for item in candidates:
        if type(item) is not StrategyCandidateTimeToCatalystRankV2Candidate:
            raise ValueError(
                "candidate items must be StrategyCandidateTimeToCatalystRankV2Candidate",
            )
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Candidate", item)
    keys = tuple(item.candidate_id for item in candidates)
    if len(set(keys)) != len(keys):
        raise ValueError("candidate items must not contain duplicate candidate_id values")
    return candidates


def _normalize_rows(value: object) -> tuple[StrategyCandidateTimeToCatalystRankV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not StrategyCandidateTimeToCatalystRankV2Row:
            raise ValueError("rows must contain StrategyCandidateTimeToCatalystRankV2Row")
        _require_hard_flags("StrategyCandidateTimeToCatalystRankV2Row", item)
    return value


def _validate_row_reason_codes(row: StrategyCandidateTimeToCatalystRankV2Row) -> None:
    if row.catalyst_status == "near_term":
        if "near_term_catalyst_boost" not in row.reason_codes:
            raise ValueError("near_term rows must include near_term_catalyst_boost")
    if row.catalyst_status == "stale":
        if row.reason_codes != ("stale_catalyst_penalty",):
            raise ValueError("stale rows must include stale_catalyst_penalty only")
    if row.catalyst_status == "out_of_window":
        if row.reason_codes != ("distant_catalyst_watch",):
            raise ValueError("out_of_window rows must include distant_catalyst_watch only")


def _validate_report_consistency(
    report: StrategyCandidateTimeToCatalystRankV2Report,
) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.near_term_candidate_count != _status_count(rows, "near_term"):
        raise ValueError("near_term_candidate_count must match rows")
    if report.stale_candidate_count != _status_count(rows, "stale"):
        raise ValueError("stale_candidate_count must match rows")
    if report.catalyst_rank_status != ("ranked" if rows else "empty"):
        raise ValueError("catalyst_rank_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.average_days_to_catalyst != _average_days_to_catalyst(rows):
        raise ValueError("average_days_to_catalyst must match rows")
    if rows:
        if report.top_candidate_id != rows[0].candidate_id:
            raise ValueError("top_candidate_id must match first row")
        if report.top_catalyst_rank_score != rows[0].catalyst_rank_score:
            raise ValueError("top_catalyst_rank_score must match first row")
    else:
        if report.top_candidate_id is not None:
            raise ValueError("top_candidate_id must be None for empty reports")
        if report.top_catalyst_rank_score is not None:
            raise ValueError("top_catalyst_rank_score must be None for empty reports")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.catalyst_rank for row in rows) != expected_ranks:
        raise ValueError("catalyst_rank values must be contiguous")
    if rows != _ranked_rows_without_rank_changes(rows):
        raise ValueError("rows must be sorted deterministically")


def _ranked_rows_without_rank_changes(
    rows: tuple[StrategyCandidateTimeToCatalystRankV2Row, ...],
) -> tuple[StrategyCandidateTimeToCatalystRankV2Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.catalyst_rank_score,
                row.days_to_catalyst,
                row.candidate_id,
                row.market_slug,
            ),
        ),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _mentions_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        code = _require_public_text(field_name, item)
        if code not in allowed:
            raise ValueError(f"{field_name} contains unknown reason code: {code}")
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized.quantize(_COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be > 0")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_VALUE_QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value.quantize(_VALUE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    for char in value:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be lowercase hex")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(_without_validation_digest(value))
    _reject_unsafe_public_payload("derived_validation_digest", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _without_validation_digest(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, tuple):
        return tuple(_without_validation_digest(item) for item in value)
    if isinstance(value, list):
        return [_without_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    return value


def _copy_payload(value: object) -> dict[str, Any]:
    copied = _copy_public_payload_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied


def _copy_public_payload_value(value: object) -> Any:
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_public_payload_value(item)
        return copied
    if type(value) is list:
        return [_copy_public_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError("public payload numeric values must be Decimal strings")
    raise ValueError("public payload values must be JSON scalars")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected_digest = _derived_validation_digest(payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _mentions_unsafe_text(str(key)):
                raise ValueError(f"{label} unsafe public key: {key}")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, str) and _mentions_unsafe_text(value):
        raise ValueError(f"{label} unsafe public value")


def _mentions_unsafe_text(value: str) -> bool:
    folded = value.lower()
    return any(fragment in folded for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS)
