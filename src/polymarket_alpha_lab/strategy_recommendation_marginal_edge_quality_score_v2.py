"""Decimal-only paper report for marginal edge quality scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIDES = ("yes", "no")
_STATUSES = ("blocked", "watch", "qualified")
_STATUS_RANK = {"qualified": 0, "watch": 1, "blocked": 2}
_EMPTY_REASON = "empty_marginal_edge_quality"
_OWNED_REASON_CODES = frozenset(
    (
        "marginal_edge_quality_qualified",
        "marginal_edge_quality_watch",
        "marginal_edge_quality_blocked",
        "positive_net_marginal_edge",
        "nonpositive_net_marginal_edge",
        "fee_spread_damping_passed",
        "fee_spread_damping_watch",
        "confidence_boost_applied",
        "confidence_boost_not_applied",
        _EMPTY_REASON,
    ),
)
_REASON_RANK = {
    "marginal_edge_quality_blocked": 0,
    "marginal_edge_quality_qualified": 1,
    "marginal_edge_quality_watch": 2,
    "nonpositive_net_marginal_edge": 3,
    "positive_net_marginal_edge": 4,
    "fee_spread_damping_watch": 5,
    "fee_spread_damping_passed": 6,
    "confidence_boost_applied": 7,
    "confidence_boost_not_applied": 8,
    _EMPTY_REASON: 9,
}
_REPORT_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "qualified_count",
    "watch_count",
    "blocked_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_KEYS = (
    "candidate_id",
    "market_slug",
    "recommendation_side",
    "forecast_probability",
    "implied_probability",
    "confidence",
    "fee_drag",
    "spread",
    "observed_at",
    "raw_marginal_edge",
    "net_marginal_edge",
    "edge_quality_score",
    "fee_spread_damping_score",
    "confidence_boost_score",
    "marginal_edge_quality_score",
    "quality_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("per", "sist"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationMarginalEdgeQualityScoreV2Config:
    config_version: str
    target_marginal_edge: Decimal
    min_quality_score: Decimal
    watch_quality_score: Decimal
    max_fee_drag: Decimal
    max_spread: Decimal
    confidence_boost_multiplier: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_marginal_edge",
            _normalize_positive_decimal("target_marginal_edge", self.target_marginal_edge),
        )
        for field_name in (
            "min_quality_score",
            "watch_quality_score",
            "max_fee_drag",
            "max_spread",
            "confidence_boost_multiplier",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_quality_score > self.min_quality_score:
            raise ValueError("watch_quality_score must not exceed min_quality_score")
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationMarginalEdgeQualityScoreV2Input:
    candidate_id: str
    market_slug: str
    recommendation_side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    fee_drag: Decimal
    spread: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "fee_drag",
            "spread",
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
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationMarginalEdgeQualityScoreV2Row:
    candidate_id: str
    market_slug: str
    recommendation_side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    fee_drag: Decimal
    spread: Decimal
    observed_at: datetime
    raw_marginal_edge: Decimal
    net_marginal_edge: Decimal
    edge_quality_score: Decimal
    fee_spread_damping_score: Decimal
    confidence_boost_score: Decimal
    marginal_edge_quality_score: Decimal
    quality_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "fee_drag",
            "spread",
            "edge_quality_score",
            "fee_spread_damping_score",
            "confidence_boost_score",
            "marginal_edge_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("raw_marginal_edge", "net_marginal_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("quality_status", self.quality_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyRecommendationMarginalEdgeQualityScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    qualified_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "qualified_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_marginal_edge_quality_score_v2_report(
    candidates: object,
    *,
    config: StrategyRecommendationMarginalEdgeQualityScoreV2Config,
    generated_at: datetime,
) -> StrategyRecommendationMarginalEdgeQualityScoreV2Report:
    if type(config) is not StrategyRecommendationMarginalEdgeQualityScoreV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationMarginalEdgeQualityScoreV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_candidates(candidates)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(sorted((_candidate_row(item, config=config) for item in items), key=_row_key))
    return StrategyRecommendationMarginalEdgeQualityScoreV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        qualified_count=_status_count(rows, "qualified"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_marginal_edge_quality_score_v2_payload(
    report: StrategyRecommendationMarginalEdgeQualityScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationMarginalEdgeQualityScoreV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a StrategyRecommendationMarginalEdgeQualityScoreV2Report")


def _candidate_row(
    item: StrategyRecommendationMarginalEdgeQualityScoreV2Input,
    *,
    config: StrategyRecommendationMarginalEdgeQualityScoreV2Config,
) -> StrategyRecommendationMarginalEdgeQualityScoreV2Row:
    raw_edge = _normalize_decimal(
        "raw_marginal_edge",
        item.forecast_probability - item.implied_probability,
    )
    net_edge = _normalize_decimal(
        "net_marginal_edge",
        raw_edge - item.fee_drag - item.spread,
    )
    edge_quality_score = _clamp_ratio(net_edge / config.target_marginal_edge)
    damping_score = _clamp_ratio(
        _ONE - ((item.fee_drag + item.spread) / (config.max_fee_drag + config.max_spread)),
    )
    confidence_boost_score = _clamp_ratio(
        item.confidence + (edge_quality_score * config.confidence_boost_multiplier),
    )
    quality_score = _normalize_ratio(
        "marginal_edge_quality_score",
        (edge_quality_score * Decimal("0.500000"))
        + (damping_score * Decimal("0.200000"))
        + (confidence_boost_score * Decimal("0.300000")),
    )
    status = _status_from_score(net_edge, quality_score, config)
    reason_codes = _row_reason_codes(
        quality_status=status,
        net_marginal_edge=net_edge,
        fee_spread_damping_score=damping_score,
        confidence_boost_score=confidence_boost_score,
        confidence=item.confidence,
        config=config,
    )
    return StrategyRecommendationMarginalEdgeQualityScoreV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        recommendation_side=item.recommendation_side,
        forecast_probability=item.forecast_probability,
        implied_probability=item.implied_probability,
        confidence=item.confidence,
        fee_drag=item.fee_drag,
        spread=item.spread,
        observed_at=item.observed_at,
        raw_marginal_edge=raw_edge,
        net_marginal_edge=net_edge,
        edge_quality_score=edge_quality_score,
        fee_spread_damping_score=damping_score,
        confidence_boost_score=confidence_boost_score,
        marginal_edge_quality_score=quality_score,
        quality_status=status,
        reason_codes=reason_codes,
    )


def _status_from_score(
    net_marginal_edge: Decimal,
    marginal_edge_quality_score: Decimal,
    config: StrategyRecommendationMarginalEdgeQualityScoreV2Config,
) -> str:
    if net_marginal_edge <= _ZERO:
        return "blocked"
    if marginal_edge_quality_score >= config.min_quality_score:
        return "qualified"
    if marginal_edge_quality_score >= config.watch_quality_score:
        return "watch"
    return "blocked"


def _row_reason_codes(
    *,
    quality_status: str,
    net_marginal_edge: Decimal,
    fee_spread_damping_score: Decimal,
    confidence_boost_score: Decimal,
    confidence: Decimal,
    config: StrategyRecommendationMarginalEdgeQualityScoreV2Config,
) -> tuple[str, ...]:
    reason_codes = [f"marginal_edge_quality_{quality_status}"]
    if net_marginal_edge > _ZERO:
        reason_codes.append("positive_net_marginal_edge")
    else:
        reason_codes.append("nonpositive_net_marginal_edge")
    if fee_spread_damping_score >= config.min_quality_score:
        reason_codes.append("fee_spread_damping_passed")
    else:
        reason_codes.append("fee_spread_damping_watch")
    if confidence_boost_score > confidence:
        reason_codes.append("confidence_boost_applied")
    else:
        reason_codes.append("confidence_boost_not_applied")
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: object,
) -> tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of input rows")
    try:
        items = tuple(candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of input rows") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationMarginalEdgeQualityScoreV2Input:
            raise ValueError(
                "candidates must contain StrategyRecommendationMarginalEdgeQualityScoreV2Input",
            )
        _require_flags("candidate", item)
        if item.candidate_id in seen:
            raise ValueError("candidate_id values must be unique; duplicate candidate_id found")
        seen.add(item.candidate_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of report rows")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of report rows") from exc
    seen: set[str] = set()
    for row in items:
        if type(row) is not StrategyRecommendationMarginalEdgeQualityScoreV2Row:
            raise ValueError("rows must contain StrategyRecommendationMarginalEdgeQualityScoreV2Row")
        _require_flags("row", row)
        _require_row_digest(row)
        if row.candidate_id in seen:
            raise ValueError("rows must have unique candidate_id values")
        seen.add(row.candidate_id)
    return tuple(sorted(items, key=_row_key))


def _row_key(row: StrategyRecommendationMarginalEdgeQualityScoreV2Row) -> tuple[int, Decimal, str]:
    return (
        _STATUS_RANK[row.quality_status],
        -row.marginal_edge_quality_score,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quality_status == status))


def _report_status(rows: tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Row, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.quality_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quality_status == "watch" for row in rows):
        return "watch"
    return "qualified"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationMarginalEdgeQualityScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    status_codes = {f"marginal_edge_quality_{row.quality_status}" for row in rows}
    return tuple(sorted(status_codes, key=lambda value: _REASON_RANK[value]))


def _check_row(row: StrategyRecommendationMarginalEdgeQualityScoreV2Row) -> None:
    expected_raw = _normalize_decimal(
        "raw_marginal_edge",
        row.forecast_probability - row.implied_probability,
    )
    expected_net = _normalize_decimal(
        "net_marginal_edge",
        row.raw_marginal_edge - row.fee_drag - row.spread,
    )
    if row.raw_marginal_edge != expected_raw:
        raise ValueError("raw_marginal_edge must match probabilities")
    if row.net_marginal_edge != expected_net:
        raise ValueError("net_marginal_edge must match raw edge and costs")
    if row.reason_codes[0] != f"marginal_edge_quality_{row.quality_status}":
        raise ValueError("reason_codes must match quality_status")


def _check_report(report: StrategyRecommendationMarginalEdgeQualityScoreV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.qualified_count != _status_count(report.rows, "qualified"):
        raise ValueError("qualified_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.qualified_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must reconcile with status counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_row_digest(row: StrategyRecommendationMarginalEdgeQualityScoreV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyRecommendationMarginalEdgeQualityScoreV2Report) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _row_digest(row: StrategyRecommendationMarginalEdgeQualityScoreV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyRecommendationMarginalEdgeQualityScoreV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_KEYS)
    _require_payload_flags("payload", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, _ROW_KEYS)
    _require_payload_flags(label, payload)
    for field_name in (
        "forecast_probability",
        "implied_probability",
        "confidence",
        "fee_drag",
        "spread",
        "raw_marginal_edge",
        "net_marginal_edge",
        "edge_quality_score",
        "fee_spread_damping_score",
        "confidence_boost_score",
        "marginal_edge_quality_score",
    ):
        _require_decimal_string(f"{label}.{field_name}", payload[field_name])
    _require_status(f"{label}.quality_status", payload["quality_status"])
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(label: str, payload: dict[str, Any], expected: tuple[str, ...]) -> None:
    actual = tuple(payload)
    if set(actual) != set(expected):
        raise ValueError(f"{label} must contain exactly the expected public fields")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON values must not be floats")
    if type(value) is str:
        _require_text("JSON string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_text("JSON object key", key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyRecommendationMarginalEdgeQualityScoreV2Config,
            StrategyRecommendationMarginalEdgeQualityScoreV2Input,
            StrategyRecommendationMarginalEdgeQualityScoreV2Row,
            StrategyRecommendationMarginalEdgeQualityScoreV2Report,
        ):
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError(f"{label} JSON Decimal values must be strings")
    if isinstance(value, float):
        raise ValueError(f"{label} JSON values must not be floats")
    if type(value) is int:
        raise ValueError(f"{label} JSON numeric values must be Decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} has unsafe public text")


def _require_status(name: str, value: object) -> None:
    if value not in _STATUSES:
        raise ValueError(f"{name} must be blocked, watch, or qualified")


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be an ordered tuple of strings")
    return _normalize_reason_codes("reason_codes", value)


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicate values")
    for item in items:
        _require_text(name, item)
    owned = [item for item in items if item in _OWNED_REASON_CODES]
    if owned != sorted(owned, key=lambda item: _REASON_RANK[item]):
        raise ValueError(f"{name} owned reason codes must match report semantics")
    return items


def _require_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    parsed = _normalize_decimal(name, parsed)
    if str(parsed) != value:
        raise ValueError(f"{name} must be a six-place Decimal string")
    return parsed


def _normalize_ratio(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("ratio", value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
