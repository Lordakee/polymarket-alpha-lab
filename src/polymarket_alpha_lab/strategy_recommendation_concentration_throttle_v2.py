"""Phase 1 paper-only recommendation concentration throttle."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any


_VALUE_QUANTUM = Decimal("0.000001")
_THROTTLE_STATUSES = ("pass", "throttled")
_UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "auth",
        "buy",
        "database",
        "live",
        "mutation",
        "network",
        "order",
        "persist",
        "private_key",
        "sell",
        "signing",
        "trade",
        "wallet",
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationConcentrationThrottleV2Config:
    config_version: str
    max_recommendations_per_category: Decimal
    max_recommendations_per_event: Decimal
    max_recommendations_per_team: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "max_recommendations_per_category",
            "max_recommendations_per_event",
            "max_recommendations_per_team",
        ):
            object.__setattr__(self, field_name, _count(field_name, getattr(self, field_name)))
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationConcentrationThrottleV2Candidate:
    recommendation_id: str
    category_id: str
    event_id: str
    team_id: str
    market_slug: str
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "category_id",
            "event_id",
            "team_id",
            "market_slug",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recommendation_score",
            _decimal("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationConcentrationThrottleV2Row:
    recommendation_id: str
    category_id: str
    event_id: str
    team_id: str
    market_slug: str
    recommendation_score: Decimal
    throttle_rank: Decimal
    throttle_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "category_id",
            "event_id",
            "team_id",
            "market_slug",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recommendation_score",
            _decimal("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(self, "throttle_rank", _count("throttle_rank", self.throttle_rank))
        _require_member("throttle_status", self.throttle_status, _THROTTLE_STATUSES)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _validate_row_reason_codes(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyRecommendationConcentrationThrottleV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    throttled_count: Decimal
    rows: tuple[StrategyRecommendationConcentrationThrottleV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "throttled_count"):
            object.__setattr__(self, field_name, _count(field_name, getattr(self, field_name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report_counts(self)
        _validate_report_reason_codes(self)
        expected_digest = _derived_validation_digest(_report_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_concentration_throttle_v2_report(
    candidates: Iterable[StrategyRecommendationConcentrationThrottleV2Candidate],
    *,
    config: StrategyRecommendationConcentrationThrottleV2Config,
    generated_at: datetime,
) -> StrategyRecommendationConcentrationThrottleV2Report:
    if type(config) is not StrategyRecommendationConcentrationThrottleV2Config:
        raise ValueError("config must be StrategyRecommendationConcentrationThrottleV2Config")
    _require_hard_flags("config", config)
    normalized_candidates = _normalize_candidates(candidates)
    _reject_duplicate_recommendation_ids(normalized_candidates)

    category_pass_counts: dict[str, Decimal] = {}
    event_pass_counts: dict[str, Decimal] = {}
    team_pass_counts: dict[str, Decimal] = {}
    rows: list[StrategyRecommendationConcentrationThrottleV2Row] = []
    for index, item in enumerate(sorted(normalized_candidates, key=_candidate_sort_key), start=1):
        status = "pass"
        reasons = list(item.reason_codes)

        category_count = category_pass_counts.get(item.category_id, Decimal("0.000000"))
        event_count = event_pass_counts.get(item.event_id, Decimal("0.000000"))
        team_count = team_pass_counts.get(item.team_id, Decimal("0.000000"))

        if category_count >= config.max_recommendations_per_category:
            status = "throttled"
            reasons.append("category_concentration_throttle")
        else:
            reasons.append("category_concentration_inline")
        if event_count >= config.max_recommendations_per_event:
            status = "throttled"
            reasons.append("event_concentration_throttle")
        else:
            reasons.append("event_concentration_inline")
        if team_count >= config.max_recommendations_per_team:
            status = "throttled"
            reasons.append("team_concentration_throttle")
        else:
            reasons.append("team_concentration_inline")

        if status == "pass":
            category_pass_counts[item.category_id] = category_count + Decimal("1.000000")
            event_pass_counts[item.event_id] = event_count + Decimal("1.000000")
            team_pass_counts[item.team_id] = team_count + Decimal("1.000000")

        rows.append(
            StrategyRecommendationConcentrationThrottleV2Row(
                recommendation_id=item.recommendation_id,
                category_id=item.category_id,
                event_id=item.event_id,
                team_id=item.team_id,
                market_slug=item.market_slug,
                recommendation_score=item.recommendation_score,
                throttle_rank=_count("throttle_rank", Decimal(index)),
                throttle_status=status,
                reason_codes=tuple(reasons),
            ),
        )

    normalized_rows = tuple(rows)
    return StrategyRecommendationConcentrationThrottleV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count("candidate_count", Decimal(len(normalized_candidates))),
        pass_count=_status_count(normalized_rows, "pass"),
        throttled_count=_status_count(normalized_rows, "throttled"),
        rows=normalized_rows,
        reason_codes=_report_reason_codes(normalized_rows),
    )


def strategy_recommendation_concentration_throttle_v2_payload(
    report: StrategyRecommendationConcentrationThrottleV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationConcentrationThrottleV2Report:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        payload = _copy_payload(report)
        _require_payload_flags(payload)
        _reject_unsafe_public_payload("payload", payload)
        _require_payload_digest(payload)
    else:
        raise ValueError("report must be StrategyRecommendationConcentrationThrottleV2Report")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _normalize_candidates(
    candidates: Iterable[StrategyRecommendationConcentrationThrottleV2Candidate],
) -> tuple[StrategyRecommendationConcentrationThrottleV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be iterable")
    normalized = tuple(candidates)
    for item in normalized:
        if type(item) is not StrategyRecommendationConcentrationThrottleV2Candidate:
            raise ValueError("candidates must contain StrategyRecommendationConcentrationThrottleV2Candidate")
        _require_hard_flags("candidate", item)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyRecommendationConcentrationThrottleV2Row, ...],
) -> tuple[StrategyRecommendationConcentrationThrottleV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyRecommendationConcentrationThrottleV2Row:
            raise ValueError("rows must contain StrategyRecommendationConcentrationThrottleV2Row")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _reject_duplicate_recommendation_ids(
    candidates: tuple[StrategyRecommendationConcentrationThrottleV2Candidate, ...],
) -> None:
    seen: set[str] = set()
    for item in candidates:
        if item.recommendation_id in seen:
            raise ValueError("duplicate recommendation_id")
        seen.add(item.recommendation_id)


def _candidate_sort_key(
    candidate: StrategyRecommendationConcentrationThrottleV2Candidate,
) -> tuple[Decimal, str, str, str, str, str]:
    return (
        -candidate.recommendation_score,
        candidate.recommendation_id,
        candidate.category_id,
        candidate.event_id,
        candidate.team_id,
        candidate.market_slug,
    )


def _row_sort_key(
    row: StrategyRecommendationConcentrationThrottleV2Row,
) -> tuple[Decimal, str, str, str, str, str]:
    return (
        -row.recommendation_score,
        row.recommendation_id,
        row.category_id,
        row.event_id,
        row.team_id,
        row.market_slug,
    )


def _status_count(
    rows: tuple[StrategyRecommendationConcentrationThrottleV2Row, ...],
    throttle_status: str,
) -> Decimal:
    return _count(
        f"{throttle_status}_count",
        Decimal(sum(1 for row in rows if row.throttle_status == throttle_status)),
    )


def _report_reason_codes(
    rows: tuple[StrategyRecommendationConcentrationThrottleV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("concentration_throttle_empty",)
    present: list[str] = []
    for reason_code in (
        "category_concentration_throttle",
        "event_concentration_throttle",
        "team_concentration_throttle",
    ):
        if any(reason_code in row.reason_codes for row in rows):
            present.append(f"{reason_code}_present")
    if present:
        return tuple(present)
    return ("concentration_throttle_clear",)


def _validate_row_reason_codes(row: StrategyRecommendationConcentrationThrottleV2Row) -> None:
    has_throttle_reason = any(
        reason_code
        in {
            "category_concentration_throttle",
            "event_concentration_throttle",
            "team_concentration_throttle",
        }
        for reason_code in row.reason_codes
    )
    if row.throttle_status == "throttled" and not has_throttle_reason:
        raise ValueError("reason_codes must include a concentration throttle")
    if row.throttle_status == "pass" and has_throttle_reason:
        raise ValueError("pass rows must not include concentration throttle reason_codes")


def _validate_report_counts(report: StrategyRecommendationConcentrationThrottleV2Report) -> None:
    if report.candidate_count != _count("candidate_count", Decimal(len(report.rows))):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.throttled_count != _status_count(report.rows, "throttled"):
        raise ValueError("throttled_count must match rows")
    if report.candidate_count != report.pass_count + report.throttled_count:
        raise ValueError("candidate_count must reconcile with status counts")


def _validate_report_reason_codes(report: StrategyRecommendationConcentrationThrottleV2Report) -> None:
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_payload(
    report: StrategyRecommendationConcentrationThrottleV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "throttled_count": _decimal_payload(report.throttled_count),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: StrategyRecommendationConcentrationThrottleV2Row) -> dict[str, Any]:
    return {
        "recommendation_id": row.recommendation_id,
        "category_id": row.category_id,
        "event_id": row.event_id,
        "team_id": row.team_id,
        "market_slug": row.market_slug,
        "recommendation_score": _decimal_payload(row.recommendation_score),
        "throttle_rank": _decimal_payload(row.throttle_rank),
        "throttle_status": row.throttle_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _copy_payload(value: dict[str, Any]) -> dict[str, Any]:
    copied = _json_payload_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied


def _json_payload_value(value: Any) -> Any:
    if value is None:
        return None
    if type(value) in (str, bool):
        return value
    if type(value) is list:
        return [_json_payload_value(item) for item in value]
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _json_payload_value(item)
        return copied
    raise ValueError("payload must contain only JSON strings, booleans, lists, objects, or nulls")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest("derived_validation_digest", digest)
    expected = _derived_validation_digest(_payload_without_digest(payload))
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload contents")


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_VALUE_QUANTUM)


def _count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole Decimal")
    if value < Decimal("0.000000"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(_VALUE_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_decimal("payload decimal", value), "f")


def _require_public_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be text")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    _reject_unsafe_public_text(field_name, value)


def _reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain text")
        if reason_code != reason_code.lower() or reason_code.strip() != reason_code:
            raise ValueError("reason_codes must contain canonical values")
        _reject_unsafe_public_text("reason_codes", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_digest(field_name: str, value: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
    _reject_unsafe_public_payload(label, asdict(value) if is_dataclass(value) else value)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for text in _public_payload_text_values(value):
        if _has_unsafe_public_term(text):
            raise ValueError(f"unsafe public payload in {label}")


def _public_payload_text_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _public_payload_text_values(asdict(value))
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            values.append(key)
            values.extend(_public_payload_text_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_public_payload_text_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} must not contain unsafe public terms")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "StrategyRecommendationConcentrationThrottleV2Candidate",
    "StrategyRecommendationConcentrationThrottleV2Config",
    "StrategyRecommendationConcentrationThrottleV2Report",
    "StrategyRecommendationConcentrationThrottleV2Row",
    "build_strategy_recommendation_concentration_throttle_v2_report",
    "strategy_recommendation_concentration_throttle_v2_payload",
)
