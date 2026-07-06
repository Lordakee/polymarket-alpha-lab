"""Phase 1 report-only resolution confidence blend reducer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_CONFIDENCE_BLEND_V2_CONFIG_VERSION = (
    "resolution-confidence-blend-v2"
)

_VALUE_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_ROW_STATUSES = frozenset(("ready", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wall" + "et",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "muta" + "tion",
    "b" + "uy",
    "se" + "ll",
    "tra" + "de",
)
_DIGEST_HEX_CHARS = frozenset("0123456789abcdef")


class _NoSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class StrategyRecommendationResolutionConfidenceBlendV2Config(_NoSubclass):
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_CONFIDENCE_BLEND_V2_CONFIG_VERSION
    )
    resolution_weight: Decimal = Decimal("0.600000")
    confidence_weight: Decimal = Decimal("0.400000")
    official_source_boost_weight: Decimal = Decimal("0.100000")
    ambiguity_penalty_weight: Decimal = Decimal("0.200000")
    ready_threshold: Decimal = Decimal("0.700000")
    watch_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "resolution_weight",
            "confidence_weight",
            "official_source_boost_weight",
            "ambiguity_penalty_weight",
            "ready_threshold",
            "watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.resolution_weight + self.confidence_weight != _ONE:
            raise ValueError("resolution_weight and confidence_weight must sum to 1.000000")
        if self.ready_threshold < self.watch_threshold:
            raise ValueError("ready_threshold must be at least watch_threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionConfidenceBlendV2Input(_NoSubclass):
    candidate_id: str
    market_slug: str
    resolution_evidence_score: Decimal
    confidence_score: Decimal
    official_source_ratio: Decimal
    ambiguity_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "resolution_evidence_score",
            "confidence_score",
            "official_source_ratio",
            "ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionConfidenceBlendV2Row(_NoSubclass):
    candidate_id: str
    market_slug: str
    resolution_evidence_score: Decimal
    confidence_score: Decimal
    official_source_ratio: Decimal
    ambiguity_score: Decimal
    weighted_resolution_score: Decimal
    weighted_confidence_score: Decimal
    official_source_boost: Decimal
    ambiguity_penalty: Decimal
    blended_resolution_confidence_score: Decimal
    paper_report_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "resolution_evidence_score",
            "confidence_score",
            "official_source_ratio",
            "ambiguity_score",
            "weighted_resolution_score",
            "weighted_confidence_score",
            "official_source_boost",
            "ambiguity_penalty",
            "blended_resolution_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("paper_report_status", self.paper_report_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionConfidenceBlendV2Report(_NoSubclass):
    generated_at: datetime
    config_version: str
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_blended_resolution_confidence_score: Decimal
    rows: tuple[StrategyRecommendationResolutionConfidenceBlendV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in ("row_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_blended_resolution_confidence_score",
            _normalize_ratio(
                "average_blended_resolution_confidence_score",
                self.average_blended_resolution_confidence_score,
            ),
        )
        _require_hard_flags(self)
        _validate_report_consistency(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derive_report_digest(self):
                raise ValueError("derived_validation_digest does not match report")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derive_report_digest(self),
            )


def build_strategy_recommendation_resolution_confidence_blend_v2(
    recommendations: Iterable[StrategyRecommendationResolutionConfidenceBlendV2Input],
    *,
    config: StrategyRecommendationResolutionConfidenceBlendV2Config,
    generated_at: datetime,
) -> StrategyRecommendationResolutionConfidenceBlendV2Report:
    if type(config) is not StrategyRecommendationResolutionConfidenceBlendV2Config:
        raise ValueError(
            "config must be StrategyRecommendationResolutionConfidenceBlendV2Config",
        )
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in _normalize_inputs(recommendations)),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationResolutionConfidenceBlendV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=_count(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_blended_resolution_confidence_score=_average_score(rows),
        rows=rows,
    )


def strategy_recommendation_resolution_confidence_blend_v2_payload(
    report: StrategyRecommendationResolutionConfidenceBlendV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyRecommendationResolutionConfidenceBlendV2Report:
        raise ValueError(
            "report must be StrategyRecommendationResolutionConfidenceBlendV2Report",
        )
    _require_hard_flags(report)
    _require_report_digest(report)
    _validate_report_consistency(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def validate_strategy_recommendation_resolution_confidence_blend_v2_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    _reject_unsafe_public_payload(payload)
    _reject_public_payload_numeric_types(payload)
    _require_payload_flags(payload)
    digest_value = payload.get("derived_validation_digest")
    if type(digest_value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest_value)
    if digest_value != _derive_payload_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return True


def _row_for_input(
    item: StrategyRecommendationResolutionConfidenceBlendV2Input,
    config: StrategyRecommendationResolutionConfidenceBlendV2Config,
) -> StrategyRecommendationResolutionConfidenceBlendV2Row:
    weighted_resolution_score = _multiply(
        item.resolution_evidence_score,
        config.resolution_weight,
    )
    weighted_confidence_score = _multiply(item.confidence_score, config.confidence_weight)
    official_source_boost = _multiply(
        item.official_source_ratio,
        config.official_source_boost_weight,
    )
    ambiguity_penalty = _multiply(item.ambiguity_score, config.ambiguity_penalty_weight)
    blended_score = _clamp_ratio(
        weighted_resolution_score
        + weighted_confidence_score
        + official_source_boost
        - ambiguity_penalty,
    )
    status = _status_for_score(blended_score, config)
    reasons = list(item.reason_codes)
    reasons.append(f"resolution_confidence_{status}")
    if official_source_boost > _ZERO:
        reasons.append("official_source_boost_applied")
    if ambiguity_penalty > _ZERO:
        reasons.append("ambiguity_penalty_applied")
    return StrategyRecommendationResolutionConfidenceBlendV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        resolution_evidence_score=item.resolution_evidence_score,
        confidence_score=item.confidence_score,
        official_source_ratio=item.official_source_ratio,
        ambiguity_score=item.ambiguity_score,
        weighted_resolution_score=weighted_resolution_score,
        weighted_confidence_score=weighted_confidence_score,
        official_source_boost=official_source_boost,
        ambiguity_penalty=ambiguity_penalty,
        blended_resolution_confidence_score=blended_score,
        paper_report_status=status,
        observed_at=item.observed_at,
        reason_codes=tuple(reasons),
    )


def _status_for_score(
    score: Decimal,
    config: StrategyRecommendationResolutionConfidenceBlendV2Config,
) -> str:
    if score >= config.ready_threshold:
        return "ready"
    if score >= config.watch_threshold:
        return "watch"
    return "blocked"


def _row_sort_key(
    row: StrategyRecommendationResolutionConfidenceBlendV2Row,
) -> tuple[Decimal, str, str]:
    return (-row.blended_resolution_confidence_score, row.candidate_id, row.market_slug)


def _normalize_inputs(
    recommendations: Iterable[StrategyRecommendationResolutionConfidenceBlendV2Input],
) -> tuple[StrategyRecommendationResolutionConfidenceBlendV2Input, ...]:
    if isinstance(recommendations, (str, bytes)) or not isinstance(recommendations, Iterable):
        raise ValueError("recommendations must be iterable")
    items = tuple(recommendations)
    for item in items:
        if type(item) is not StrategyRecommendationResolutionConfidenceBlendV2Input:
            raise ValueError(
                "recommendations must contain StrategyRecommendationResolutionConfidenceBlendV2Input",
            )
        _require_hard_flags(item)
    return items


def _normalize_rows(
    rows: Iterable[StrategyRecommendationResolutionConfidenceBlendV2Row],
) -> tuple[StrategyRecommendationResolutionConfidenceBlendV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be iterable")
    items = tuple(rows)
    for row in items:
        if type(row) is not StrategyRecommendationResolutionConfidenceBlendV2Row:
            raise ValueError(
                "rows must contain StrategyRecommendationResolutionConfidenceBlendV2Row",
            )
        _require_hard_flags(row)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    if len({row.candidate_id for row in items}) != len(items):
        raise ValueError("rows must not contain duplicate candidate_id values")
    return items


def _validate_report_consistency(
    report: StrategyRecommendationResolutionConfidenceBlendV2Report,
) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.ready_count + report.watch_count + report.blocked_count
        != report.row_count
    ):
        raise ValueError("row_count must match status counts")
    if report.average_blended_resolution_confidence_score != _average_score(report.rows):
        raise ValueError("average_blended_resolution_confidence_score must match rows")


def _status_count(
    rows: tuple[StrategyRecommendationResolutionConfidenceBlendV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.paper_report_status == status))


def _average_score(
    rows: tuple[StrategyRecommendationResolutionConfidenceBlendV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((row.blended_resolution_confidence_score for row in rows), _ZERO)
            / Decimal(len(rows)),
        )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_VALUE_QUANTUM)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(left * right)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize_decimal(value)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    _require_decimal("decimal value", value)
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_VALUE_QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be iterable")
    items = tuple(values)
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string("reason_code", item)
        if item != item.lower():
            raise ValueError("reason_code must be lowercase")
    return tuple(dict.fromkeys(items))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_public_term(value):
        raise ValueError("unsafe public surface")


def _require_hard_flags(value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")
    for field_name in _iter_field_names(value):
        _require_canonical_string("field_name", field_name)


def _iter_field_names(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        names: list[str] = []
        for item in fields(value):
            names.append(item.name)
            names.extend(_iter_field_names(getattr(value, item.name)))
        return tuple(names)
    if isinstance(value, Mapping):
        names = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public surface")
            names.append(key)
            names.extend(_iter_field_names(item))
        return tuple(names)
    if isinstance(value, (list, tuple)):
        names = []
        for item in value:
            names.extend(_iter_field_names(item))
        return tuple(names)
    return ()


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in _UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_quantize_decimal(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime value", value).isoformat()
    if type(value) is bool:
        return value
    if value is None:
        return None
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if type(value) is str:
        _require_canonical_string("payload value", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public surface")
            _require_canonical_string("payload field", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public surface")
            _require_canonical_string("payload field", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _require_canonical_string("payload value", value)


def _reject_public_payload_numeric_types(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must use Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_payload_numeric_types(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload_numeric_types(item)


def _require_payload_flags(payload: Mapping[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_digest(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if len(value) != 64 or any(char not in _DIGEST_HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")


def _require_report_digest(
    report: StrategyRecommendationResolutionConfidenceBlendV2Report,
) -> None:
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _derive_report_digest(report):
        raise ValueError("derived_validation_digest does not match report")


def _derive_report_digest(
    report: StrategyRecommendationResolutionConfidenceBlendV2Report,
) -> str:
    raw_payload = asdict(report)
    raw_payload.pop("derived_validation_digest", None)
    payload = _json_ready(raw_payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return _digest(payload)


def _derive_payload_digest(payload: Mapping[str, object]) -> str:
    payload_copy = dict(payload)
    payload_copy.pop("derived_validation_digest", None)
    return _digest(payload_copy)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8",
        ),
    ).hexdigest()


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_CONFIDENCE_BLEND_V2_CONFIG_VERSION",
    "StrategyRecommendationResolutionConfidenceBlendV2Config",
    "StrategyRecommendationResolutionConfidenceBlendV2Input",
    "StrategyRecommendationResolutionConfidenceBlendV2Row",
    "StrategyRecommendationResolutionConfidenceBlendV2Report",
    "build_strategy_recommendation_resolution_confidence_blend_v2",
    "strategy_recommendation_resolution_confidence_blend_v2_payload",
    "validate_strategy_recommendation_resolution_confidence_blend_v2_payload",
)
