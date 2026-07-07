"""Phase 1 report-only price-limit safety bands for recommendations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROS_PER_SECOND = Decimal("1000000")
SIDES = ("yes", "no")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PRICE_STATUSES = (
    "price_limit_pass",
    "price_limit_abstain",
    "price_limit_reject",
)
SOURCE_STATUSES = ("source_fresh", "source_stale")
REPORT_STATUSES = (
    "paper_price_limit_pass",
    "paper_price_limit_watch",
    "paper_price_limit_abstain",
    "paper_price_limit_reject",
)
PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "recommendation_id",
    "market_slug",
    "target_side",
    "fair_probability",
    "side_fair_probability",
    "quoted_price",
    "fair_probability_observed_at",
    "source_age_seconds",
    "fee_slippage_buffer",
    "spread_buffer",
    "stale_source_penalty",
    "max_fair_probability_age_seconds",
    "abstain_band",
    "applied_stale_source_penalty",
    "total_safety_buffer",
    "max_acceptable_price",
    "min_acceptable_price",
    "price_edge_to_max",
    "price_distance_to_fair",
    "price_status",
    "source_status",
    "report_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
PUBLIC_PAYLOAD_FIELD_SET = frozenset(PUBLIC_PAYLOAD_FIELDS)
REASON_RANK = {
    "fee_slippage_buffer_applied": 0,
    "spread_buffer_applied": 1,
    "stale_source_penalty_applied": 2,
    "abstain_band_applied": 3,
    "source_fresh": 4,
    "price_at_or_below_max_acceptable": 5,
    "price_inside_abstain_band": 6,
    "price_above_min_acceptable": 7,
}
REASON_CODES = frozenset(REASON_RANK)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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


@dataclass(frozen=True)
class StrategyRecommendationPriceLimitSafetyBandV2Config:
    config_version: str
    fee_slippage_buffer: Decimal
    spread_buffer: Decimal
    stale_source_penalty: Decimal
    max_fair_probability_age_seconds: Decimal
    abstain_band: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationPriceLimitSafetyBandV2Config:
            raise ValueError(
                "config must be a StrategyRecommendationPriceLimitSafetyBandV2Config",
            )
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "fee_slippage_buffer",
            "spread_buffer",
            "stale_source_penalty",
            "abstain_band",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_fair_probability_age_seconds",
            _normalize_positive_decimal(
                "max_fair_probability_age_seconds",
                self.max_fair_probability_age_seconds,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationPriceLimitSafetyBandV2Recommendation:
    recommendation_id: str
    market_slug: str
    target_side: str
    fair_probability: Decimal
    quoted_price: Decimal
    fair_probability_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationPriceLimitSafetyBandV2Recommendation:
            raise ValueError(
                "recommendation must be a "
                "StrategyRecommendationPriceLimitSafetyBandV2Recommendation",
            )
        for field_name in ("recommendation_id", "market_slug"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side("target_side", self.target_side)
        object.__setattr__(
            self,
            "fair_probability",
            _normalize_ratio("fair_probability", self.fair_probability),
        )
        object.__setattr__(
            self,
            "quoted_price",
            _normalize_ratio("quoted_price", self.quoted_price),
        )
        object.__setattr__(
            self,
            "fair_probability_observed_at",
            _as_utc("fair_probability_observed_at", self.fair_probability_observed_at),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationPriceLimitSafetyBandV2Report:
    generated_at: datetime
    config_version: str
    recommendation_id: str
    market_slug: str
    target_side: str
    fair_probability: Decimal
    side_fair_probability: Decimal
    quoted_price: Decimal
    fair_probability_observed_at: datetime
    source_age_seconds: Decimal
    fee_slippage_buffer: Decimal
    spread_buffer: Decimal
    stale_source_penalty: Decimal
    max_fair_probability_age_seconds: Decimal
    abstain_band: Decimal
    applied_stale_source_penalty: Decimal
    total_safety_buffer: Decimal
    max_acceptable_price: Decimal
    min_acceptable_price: Decimal
    price_edge_to_max: Decimal
    price_distance_to_fair: Decimal
    price_status: str
    source_status: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationPriceLimitSafetyBandV2Report:
            raise ValueError("report must be a StrategyRecommendationPriceLimitSafetyBandV2Report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "recommendation_id", "market_slug"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side("target_side", self.target_side)
        object.__setattr__(
            self,
            "fair_probability_observed_at",
            _as_utc("fair_probability_observed_at", self.fair_probability_observed_at),
        )
        for field_name in (
            "fair_probability",
            "side_fair_probability",
            "quoted_price",
            "fee_slippage_buffer",
            "spread_buffer",
            "stale_source_penalty",
            "abstain_band",
            "applied_stale_source_penalty",
            "max_acceptable_price",
            "min_acceptable_price",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_seconds",
            "max_fair_probability_age_seconds",
            "total_safety_buffer",
            "price_distance_to_fair",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "price_edge_to_max",
            _normalize_decimal("price_edge_to_max", self.price_edge_to_max),
        )
        _require_choice("price_status", self.price_status, PRICE_STATUSES)
        _require_choice("source_status", self.source_status, SOURCE_STATUSES)
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_price_limit_safety_band_v2_report(
    recommendation: StrategyRecommendationPriceLimitSafetyBandV2Recommendation,
    *,
    config: StrategyRecommendationPriceLimitSafetyBandV2Config,
    generated_at: datetime,
) -> StrategyRecommendationPriceLimitSafetyBandV2Report:
    if type(recommendation) is not StrategyRecommendationPriceLimitSafetyBandV2Recommendation:
        raise ValueError(
            "recommendation must be a StrategyRecommendationPriceLimitSafetyBandV2Recommendation",
        )
    if type(config) is not StrategyRecommendationPriceLimitSafetyBandV2Config:
        raise ValueError("config must be a StrategyRecommendationPriceLimitSafetyBandV2Config")
    _require_hard_flags(recommendation)
    _require_hard_flags(config)
    stamp = _as_utc("generated_at", generated_at)
    source_age_seconds = _age_seconds(stamp, recommendation.fair_probability_observed_at)
    side_fair_probability = _side_fair_probability(
        recommendation.fair_probability,
        recommendation.target_side,
    )
    applied_stale_source_penalty = (
        config.stale_source_penalty
        if source_age_seconds > config.max_fair_probability_age_seconds
        else ZERO
    )
    total_safety_buffer = _normalize_nonnegative_decimal(
        "total_safety_buffer",
        (
            config.fee_slippage_buffer
            + config.spread_buffer
            + applied_stale_source_penalty
            + config.abstain_band
        ),
    )
    max_acceptable_price = _cap_probability(side_fair_probability - total_safety_buffer)
    min_acceptable_price = _cap_probability(side_fair_probability + total_safety_buffer)
    price_edge_to_max = _normalize_decimal(
        "price_edge_to_max",
        max_acceptable_price - recommendation.quoted_price,
    )
    price_distance_to_fair = _normalize_nonnegative_decimal(
        "price_distance_to_fair",
        abs(side_fair_probability - recommendation.quoted_price),
    )
    price_status = _price_status(
        recommendation.quoted_price,
        max_acceptable_price,
        min_acceptable_price,
    )
    source_status = (
        "source_stale" if applied_stale_source_penalty > ZERO else "source_fresh"
    )
    report_status = _report_status(
        price_status=price_status,
        source_status=source_status,
    )

    return StrategyRecommendationPriceLimitSafetyBandV2Report(
        generated_at=stamp,
        config_version=config.config_version,
        recommendation_id=recommendation.recommendation_id,
        market_slug=recommendation.market_slug,
        target_side=recommendation.target_side,
        fair_probability=recommendation.fair_probability,
        side_fair_probability=side_fair_probability,
        quoted_price=recommendation.quoted_price,
        fair_probability_observed_at=recommendation.fair_probability_observed_at,
        source_age_seconds=source_age_seconds,
        fee_slippage_buffer=config.fee_slippage_buffer,
        spread_buffer=config.spread_buffer,
        stale_source_penalty=config.stale_source_penalty,
        max_fair_probability_age_seconds=config.max_fair_probability_age_seconds,
        abstain_band=config.abstain_band,
        applied_stale_source_penalty=applied_stale_source_penalty,
        total_safety_buffer=total_safety_buffer,
        max_acceptable_price=max_acceptable_price,
        min_acceptable_price=min_acceptable_price,
        price_edge_to_max=price_edge_to_max,
        price_distance_to_fair=price_distance_to_fair,
        price_status=price_status,
        source_status=source_status,
        report_status=report_status,
        reason_codes=_reason_codes(
            fee_slippage_buffer=config.fee_slippage_buffer,
            spread_buffer=config.spread_buffer,
            applied_stale_source_penalty=applied_stale_source_penalty,
            abstain_band=config.abstain_band,
            source_status=source_status,
            price_status=price_status,
        ),
    )


def strategy_recommendation_price_limit_safety_band_v2_payload(
    value: StrategyRecommendationPriceLimitSafetyBandV2Report | Mapping[str, Any],
) -> dict[str, Any]:
    if type(value) is StrategyRecommendationPriceLimitSafetyBandV2Report:
        _require_hard_flags(value)
        _validate_report_consistency(value)
        expected_digest = _report_validation_digest(value)
        if value.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        payload = _report_payload_without_digest(value)
        payload["derived_validation_digest"] = value.derived_validation_digest
        return validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(
            payload,
        )
    return validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(value)


def validate_strategy_recommendation_price_limit_safety_band_v2_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    ready = _validate_public_payload_value(payload)
    if not isinstance(ready, dict):
        raise ValueError("public payload must be a JSON object")
    _require_payload_hard_flags(ready)
    if "derived_validation_digest" not in ready:
        raise ValueError("derived_validation_digest must be present")
    digest = ready["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256("derived_validation_digest", digest)
    _require_public_payload_fields(ready)
    digest_source = {
        key: item
        for key, item in ready.items()
        if key != "derived_validation_digest"
    }
    if digest != _public_payload_digest(digest_source):
        raise ValueError("derived_validation_digest mismatch")
    report = _report_from_public_payload(ready)
    canonical_payload = _report_payload_without_digest(report)
    canonical_payload["derived_validation_digest"] = report.derived_validation_digest
    if ready != canonical_payload:
        raise ValueError("public payload must be canonical")
    return ready


def _require_public_payload_fields(payload: Mapping[str, Any]) -> None:
    field_names = set(payload)
    missing = sorted(PUBLIC_PAYLOAD_FIELD_SET - field_names)
    if missing:
        raise ValueError(f"public payload missing required fields: {', '.join(missing)}")
    extra = sorted(field_names - PUBLIC_PAYLOAD_FIELD_SET)
    if extra:
        raise ValueError(f"public payload contains unknown fields: {', '.join(extra)}")


def _report_from_public_payload(
    payload: Mapping[str, Any],
) -> StrategyRecommendationPriceLimitSafetyBandV2Report:
    return StrategyRecommendationPriceLimitSafetyBandV2Report(
        generated_at=_payload_required_datetime(payload, "generated_at"),
        config_version=_payload_required_string(payload, "config_version"),
        recommendation_id=_payload_required_string(payload, "recommendation_id"),
        market_slug=_payload_required_string(payload, "market_slug"),
        target_side=_payload_required_string(payload, "target_side"),
        fair_probability=_payload_required_decimal(payload, "fair_probability"),
        side_fair_probability=_payload_required_decimal(payload, "side_fair_probability"),
        quoted_price=_payload_required_decimal(payload, "quoted_price"),
        fair_probability_observed_at=_payload_required_datetime(
            payload,
            "fair_probability_observed_at",
        ),
        source_age_seconds=_payload_required_decimal(payload, "source_age_seconds"),
        fee_slippage_buffer=_payload_required_decimal(payload, "fee_slippage_buffer"),
        spread_buffer=_payload_required_decimal(payload, "spread_buffer"),
        stale_source_penalty=_payload_required_decimal(payload, "stale_source_penalty"),
        max_fair_probability_age_seconds=_payload_required_decimal(
            payload,
            "max_fair_probability_age_seconds",
        ),
        abstain_band=_payload_required_decimal(payload, "abstain_band"),
        applied_stale_source_penalty=_payload_required_decimal(
            payload,
            "applied_stale_source_penalty",
        ),
        total_safety_buffer=_payload_required_decimal(payload, "total_safety_buffer"),
        max_acceptable_price=_payload_required_decimal(payload, "max_acceptable_price"),
        min_acceptable_price=_payload_required_decimal(payload, "min_acceptable_price"),
        price_edge_to_max=_payload_required_decimal(payload, "price_edge_to_max"),
        price_distance_to_fair=_payload_required_decimal(
            payload,
            "price_distance_to_fair",
        ),
        price_status=_payload_required_string(payload, "price_status"),
        source_status=_payload_required_string(payload, "source_status"),
        report_status=_payload_required_string(payload, "report_status"),
        reason_codes=_payload_required_reason_codes(payload, "reason_codes"),
        derived_validation_digest=_payload_required_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _validate_report_consistency(
    report: StrategyRecommendationPriceLimitSafetyBandV2Report,
) -> None:
    if report.fair_probability_observed_at > report.generated_at:
        raise ValueError("fair_probability_observed_at must not be in the future")
    expected_age = _age_seconds(report.generated_at, report.fair_probability_observed_at)
    if report.source_age_seconds != expected_age:
        raise ValueError("source_age_seconds must match timestamps")
    expected_side_fair_probability = _side_fair_probability(
        report.fair_probability,
        report.target_side,
    )
    if report.side_fair_probability != expected_side_fair_probability:
        raise ValueError("side_fair_probability must match target side")
    expected_applied_stale_source_penalty = (
        report.stale_source_penalty
        if report.source_age_seconds > report.max_fair_probability_age_seconds
        else ZERO
    )
    if report.applied_stale_source_penalty != expected_applied_stale_source_penalty:
        raise ValueError("applied_stale_source_penalty must match source age")
    expected_total_safety_buffer = _normalize_nonnegative_decimal(
        "total_safety_buffer",
        (
            report.fee_slippage_buffer
            + report.spread_buffer
            + report.applied_stale_source_penalty
            + report.abstain_band
        ),
    )
    if report.total_safety_buffer != expected_total_safety_buffer:
        raise ValueError("total_safety_buffer must match buffers")
    expected_max_acceptable_price = _cap_probability(
        report.side_fair_probability - report.total_safety_buffer,
    )
    expected_min_acceptable_price = _cap_probability(
        report.side_fair_probability + report.total_safety_buffer,
    )
    if report.max_acceptable_price != expected_max_acceptable_price:
        raise ValueError("max_acceptable_price must match safety band")
    if report.min_acceptable_price != expected_min_acceptable_price:
        raise ValueError("min_acceptable_price must match safety band")
    expected_price_edge_to_max = _normalize_decimal(
        "price_edge_to_max",
        report.max_acceptable_price - report.quoted_price,
    )
    if report.price_edge_to_max != expected_price_edge_to_max:
        raise ValueError("price_edge_to_max must match quoted price")
    expected_price_distance_to_fair = _normalize_nonnegative_decimal(
        "price_distance_to_fair",
        abs(report.side_fair_probability - report.quoted_price),
    )
    if report.price_distance_to_fair != expected_price_distance_to_fair:
        raise ValueError("price_distance_to_fair must match quoted price")
    expected_price_status = _price_status(
        report.quoted_price,
        report.max_acceptable_price,
        report.min_acceptable_price,
    )
    if report.price_status != expected_price_status:
        raise ValueError("price_status must match price limits")
    expected_source_status = (
        "source_stale"
        if report.applied_stale_source_penalty > ZERO
        else "source_fresh"
    )
    if report.source_status != expected_source_status:
        raise ValueError("source_status must match stale source penalty")
    expected_report_status = _report_status(
        price_status=report.price_status,
        source_status=report.source_status,
    )
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match component statuses")
    expected_reason_codes = _reason_codes(
        fee_slippage_buffer=report.fee_slippage_buffer,
        spread_buffer=report.spread_buffer,
        applied_stale_source_penalty=report.applied_stale_source_penalty,
        abstain_band=report.abstain_band,
        source_status=report.source_status,
        price_status=report.price_status,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match statuses and buffers")


def _report_status(*, price_status: str, source_status: str) -> str:
    if price_status == "price_limit_reject":
        return "paper_price_limit_reject"
    if price_status == "price_limit_abstain":
        return "paper_price_limit_abstain"
    if source_status == "source_stale":
        return "paper_price_limit_watch"
    return "paper_price_limit_pass"


def _price_status(
    quoted_price: Decimal,
    max_acceptable_price: Decimal,
    min_acceptable_price: Decimal,
) -> str:
    if quoted_price <= max_acceptable_price:
        return "price_limit_pass"
    if quoted_price < min_acceptable_price:
        return "price_limit_abstain"
    return "price_limit_reject"


def _reason_codes(
    *,
    fee_slippage_buffer: Decimal,
    spread_buffer: Decimal,
    applied_stale_source_penalty: Decimal,
    abstain_band: Decimal,
    source_status: str,
    price_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fee_slippage_buffer > ZERO:
        reasons.append("fee_slippage_buffer_applied")
    if spread_buffer > ZERO:
        reasons.append("spread_buffer_applied")
    if applied_stale_source_penalty > ZERO:
        reasons.append("stale_source_penalty_applied")
    if abstain_band > ZERO:
        reasons.append("abstain_band_applied")
    if source_status == "source_fresh":
        reasons.append("source_fresh")
    if price_status == "price_limit_pass":
        reasons.append("price_at_or_below_max_acceptable")
    elif price_status == "price_limit_abstain":
        reasons.append("price_inside_abstain_band")
    else:
        reasons.append("price_above_min_acceptable")
    return _sort_reason_codes(tuple(reasons))


def _report_payload_without_digest(
    report: StrategyRecommendationPriceLimitSafetyBandV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "recommendation_id": report.recommendation_id,
        "market_slug": report.market_slug,
        "target_side": report.target_side,
        "fair_probability": _payload_value(report.fair_probability),
        "side_fair_probability": _payload_value(report.side_fair_probability),
        "quoted_price": _payload_value(report.quoted_price),
        "fair_probability_observed_at": _payload_value(report.fair_probability_observed_at),
        "source_age_seconds": _payload_value(report.source_age_seconds),
        "fee_slippage_buffer": _payload_value(report.fee_slippage_buffer),
        "spread_buffer": _payload_value(report.spread_buffer),
        "stale_source_penalty": _payload_value(report.stale_source_penalty),
        "max_fair_probability_age_seconds": _payload_value(
            report.max_fair_probability_age_seconds,
        ),
        "abstain_band": _payload_value(report.abstain_band),
        "applied_stale_source_penalty": _payload_value(
            report.applied_stale_source_penalty,
        ),
        "total_safety_buffer": _payload_value(report.total_safety_buffer),
        "max_acceptable_price": _payload_value(report.max_acceptable_price),
        "min_acceptable_price": _payload_value(report.min_acceptable_price),
        "price_edge_to_max": _payload_value(report.price_edge_to_max),
        "price_distance_to_fair": _payload_value(report.price_distance_to_fair),
        "price_status": report.price_status,
        "source_status": report.source_status,
        "report_status": report.report_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_validation_digest(
    report: StrategyRecommendationPriceLimitSafetyBandV2Report,
) -> str:
    return _public_payload_digest(_report_payload_without_digest(report))


def _public_payload_digest(payload_without_digest: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return format(_normalize_decimal("payload decimal", value), "f")
    if type(value) is datetime:
        return _payload_datetime(value)
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _validate_public_payload_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload key must be a string")
            _require_canonical_public_string("public payload key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _validate_public_payload_value(item)
        return ready
    if isinstance(value, tuple):
        return [_validate_public_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_validate_public_payload_value(item) for item in value]
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if value is None:
        return None
    if isinstance(value, Decimal) or type(value) in (int, float):
        raise ValueError("public payload numeric values must be decimal strings")
    raise ValueError("public payload value is not JSON serializable")


def _payload_required_datetime(payload: Mapping[str, Any], field_name: str) -> datetime:
    text = _payload_required_string(payload, field_name)
    source = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    try:
        value = datetime.fromisoformat(source)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    return _as_utc(field_name, value)


def _payload_required_decimal(payload: Mapping[str, Any], field_name: str) -> Decimal:
    text = _payload_required_string(payload, field_name)
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite decimal string")
    return value


def _payload_required_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_canonical_public_string(field_name, value)
    return value


def _payload_required_reason_codes(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    values = payload[field_name]
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(values)


def _payload_datetime(value: datetime) -> str:
    text = _as_utc("payload datetime", value).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text


def _require_payload_hard_flags(payload: Mapping[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} must be True")
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one reason code")
    for item in items:
        _require_reason_code(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    sorted_items = _sort_reason_codes(items)
    if items != sorted_items:
        raise ValueError(f"{field_name} must be sorted")
    return items


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    for reason_code in unique:
        _require_reason_code("reason_codes", reason_code)
    return tuple(sorted(unique, key=lambda item: (REASON_RANK[item], item)))


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _side_fair_probability(fair_probability: Decimal, target_side: str) -> Decimal:
    _require_side("target_side", target_side)
    fair_probability = _normalize_ratio("fair_probability", fair_probability)
    if target_side == "yes":
        return fair_probability
    return _normalize_ratio("side_fair_probability", ONE - fair_probability)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at = _as_utc("generated_at", generated_at)
    observed_at = _as_utc("fair_probability_observed_at", observed_at)
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("fair_probability_observed_at must not be in the future")
    total = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROS_PER_SECOND
    )
    return _normalize_nonnegative_decimal("source_age_seconds", total)


def _cap_probability(value: Decimal) -> Decimal:
    value = _normalize_decimal("probability", value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = 28
        try:
            return value.quantize(DECIMAL_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must fit decimal scale") from exc


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_side(field_name: str, value: str) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_choice(field_name: str, value: str, choices: tuple[str, ...]) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "StrategyRecommendationPriceLimitSafetyBandV2Config",
    "StrategyRecommendationPriceLimitSafetyBandV2Recommendation",
    "StrategyRecommendationPriceLimitSafetyBandV2Report",
    "build_strategy_recommendation_price_limit_safety_band_v2_report",
    "strategy_recommendation_price_limit_safety_band_v2_payload",
    "validate_strategy_recommendation_price_limit_safety_band_v2_public_payload",
)
