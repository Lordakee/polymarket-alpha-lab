"""Pure paper-only information edge scoring for Polymarket event markets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_INFORMATION_EDGE_SCORE_V10_CONFIG_VERSION = (
    "strategy-information-edge-score-v10"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
LOWER_HEX_DIGITS = frozenset("0123456789abcdef")

HIGH_EDGE_TIER = "high"
MEDIUM_EDGE_TIER = "medium"
LOW_EDGE_TIER = "low"
BLOCKED_EDGE_TIER = "blocked"
EDGE_TIERS = (HIGH_EDGE_TIER, MEDIUM_EDGE_TIER, LOW_EDGE_TIER, BLOCKED_EDGE_TIER)
RESEARCH_PRIORITIES = ("urgent", "high", "monitor", "blocked")

REASON_CODES = (
    "coverage_quorum_met",
    "coverage_quorum_missed",
    "forecast_dispersion_material",
    "forecast_dispersion_thin",
    "information_edge_high",
    "information_edge_medium",
    "information_edge_low",
    "information_edge_blocked",
    "market_stale",
    "market_recent",
    "resolution_clear",
    "resolution_ambiguity_high",
    "source_fresh",
    "source_aging",
    "source_reliable",
    "source_reliability_low",
)

SENSITIVE_TEXT_FRAGMENTS = (
    "://",
    "li" + "ve",
    "sec" + "ret",
    "tok" + "en=",
    "api" + "_key=",
    "priv" + "ate",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)
UNSAFE_FIELD_FRAGMENTS = (
    "li" + "ve",
    "aut" + "h",
    "wal" + "let",
    "account",
    "balance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)


@dataclass(frozen=True)
class StrategyInformationEdgeScoreV10Config:
    config_version: str = DEFAULT_STRATEGY_INFORMATION_EDGE_SCORE_V10_CONFIG_VERSION
    max_source_freshness_hours: Decimal = Decimal("24.000000")
    min_source_reliability: Decimal = Decimal("0.700000")
    min_coverage_quorum_ratio: Decimal = Decimal("0.800000")
    target_forecast_dispersion: Decimal = Decimal("0.150000")
    target_market_staleness_hours: Decimal = Decimal("6.000000")
    max_resolution_ambiguity: Decimal = Decimal("0.250000")
    high_edge_score: Decimal = Decimal("0.750000")
    medium_edge_score: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.200000")
    reliability_weight: Decimal = Decimal("0.200000")
    coverage_quorum_weight: Decimal = Decimal("0.150000")
    forecast_dispersion_weight: Decimal = Decimal("0.150000")
    market_staleness_weight: Decimal = Decimal("0.200000")
    resolution_clarity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_freshness_hours",
            _normalize_positive_value(
                "max_source_freshness_hours",
                self.max_source_freshness_hours,
            ),
        )
        object.__setattr__(
            self,
            "target_market_staleness_hours",
            _normalize_positive_value(
                "target_market_staleness_hours",
                self.target_market_staleness_hours,
            ),
        )
        for field_name in (
            "min_source_reliability",
            "min_coverage_quorum_ratio",
            "target_forecast_dispersion",
            "max_resolution_ambiguity",
            "high_edge_score",
            "medium_edge_score",
            "freshness_weight",
            "reliability_weight",
            "coverage_quorum_weight",
            "forecast_dispersion_weight",
            "market_staleness_weight",
            "resolution_clarity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.target_forecast_dispersion == ZERO:
            raise ValueError("target_forecast_dispersion must be above zero")
        if self.min_coverage_quorum_ratio == ZERO:
            raise ValueError("min_coverage_quorum_ratio must be above zero")
        if self.high_edge_score < self.medium_edge_score:
            raise ValueError("high_edge_score must be at least medium_edge_score")
        weight_sum = _q(
            self.freshness_weight
            + self.reliability_weight
            + self.coverage_quorum_weight
            + self.forecast_dispersion_weight
            + self.market_staleness_weight
            + self.resolution_clarity_weight,
        )
        if weight_sum != ONE:
            raise ValueError("config weights must sum to 1.000000")
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyInformationEdgeScoreV10Input:
    market_slug: str
    event_slug: str
    source_observed_at: datetime
    source_freshness_hours: Decimal
    source_reliability: Decimal
    coverage_source_count: Decimal
    required_coverage_source_count: Decimal
    forecast_dispersion: Decimal
    market_staleness_hours: Decimal
    resolution_ambiguity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("event_slug", self.event_slug)
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "source_freshness_hours",
            _normalize_nonnegative_value(
                "source_freshness_hours",
                self.source_freshness_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_probability("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "coverage_source_count",
            _normalize_nonnegative_count(
                "coverage_source_count",
                self.coverage_source_count,
            ),
        )
        object.__setattr__(
            self,
            "required_coverage_source_count",
            _normalize_positive_count(
                "required_coverage_source_count",
                self.required_coverage_source_count,
            ),
        )
        object.__setattr__(
            self,
            "forecast_dispersion",
            _normalize_probability("forecast_dispersion", self.forecast_dispersion),
        )
        object.__setattr__(
            self,
            "market_staleness_hours",
            _normalize_nonnegative_value(
                "market_staleness_hours",
                self.market_staleness_hours,
            ),
        )
        object.__setattr__(
            self,
            "resolution_ambiguity",
            _normalize_probability("resolution_ambiguity", self.resolution_ambiguity),
        )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyInformationEdgeScoreV10Report:
    config_version: str
    generated_at: datetime
    market_slug: str
    event_slug: str
    source_observed_at: datetime
    source_freshness_hours: Decimal
    source_reliability: Decimal
    coverage_source_count: Decimal
    required_coverage_source_count: Decimal
    coverage_quorum_ratio: Decimal
    forecast_dispersion: Decimal
    market_staleness_hours: Decimal
    resolution_ambiguity: Decimal
    source_freshness_score: Decimal
    source_reliability_score: Decimal
    coverage_quorum_score: Decimal
    forecast_dispersion_score: Decimal
    market_staleness_score: Decimal
    resolution_clarity_score: Decimal
    edge_score: Decimal
    edge_tier: str
    research_priority: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("event_slug", self.event_slug)
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "source_freshness_hours",
            "market_staleness_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability",
            "coverage_quorum_ratio",
            "forecast_dispersion",
            "resolution_ambiguity",
            "source_freshness_score",
            "source_reliability_score",
            "coverage_quorum_score",
            "forecast_dispersion_score",
            "market_staleness_score",
            "resolution_clarity_score",
            "edge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "coverage_source_count",
            _normalize_nonnegative_count(
                "coverage_source_count",
                self.coverage_source_count,
            ),
        )
        object.__setattr__(
            self,
            "required_coverage_source_count",
            _normalize_positive_count(
                "required_coverage_source_count",
                self.required_coverage_source_count,
            ),
        )
        object.__setattr__(
            self,
            "edge_tier",
            _normalize_choice("edge_tier", self.edge_tier, EDGE_TIERS),
        )
        object.__setattr__(
            self,
            "research_priority",
            _normalize_choice(
                "research_priority",
                self.research_priority,
                RESEARCH_PRIORITIES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            DERIVED_VALIDATION_DIGEST_FIELD,
            _normalize_digest(
                DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            ),
        )
        if self.reason_codes != _reason_codes_for_tier(
            self.edge_tier,
            source_is_fresh=self.source_freshness_score > ZERO,
            source_is_reliable="source_reliability_low" not in self.reason_codes,
            coverage_is_met="coverage_quorum_missed" not in self.reason_codes,
            dispersion_is_material=(
                "forecast_dispersion_material" in self.reason_codes
            ),
            market_is_stale="market_stale" in self.reason_codes,
            resolution_is_clear="resolution_clear" in self.reason_codes,
        ):
            raise ValueError("report reason_codes must match")
        if _priority_for_tier(self.edge_tier) != self.research_priority:
            raise ValueError("report research_priority must match")
        _require_paper_flags("report", self)
        _validate_report_derived_values(self)
        _validate_report_derived_digest(self)


def score_strategy_information_edge_v10(
    input_row: StrategyInformationEdgeScoreV10Input,
    *,
    config: StrategyInformationEdgeScoreV10Config | None = None,
    generated_at: datetime,
) -> StrategyInformationEdgeScoreV10Report:
    if type(input_row) is not StrategyInformationEdgeScoreV10Input:
        raise ValueError("input_row must be a StrategyInformationEdgeScoreV10Input")
    cfg = config or StrategyInformationEdgeScoreV10Config()
    if type(cfg) is not StrategyInformationEdgeScoreV10Config:
        raise ValueError("config must be a StrategyInformationEdgeScoreV10Config")

    normalized_generated_at = _as_utc("generated_at", generated_at)
    coverage_quorum_ratio = _bounded_ratio(
        input_row.coverage_source_count,
        input_row.required_coverage_source_count,
    )
    source_freshness_score = _q(
        ONE
        - _bounded_ratio(input_row.source_freshness_hours, cfg.max_source_freshness_hours),
    )
    source_reliability_score = input_row.source_reliability
    coverage_quorum_score = coverage_quorum_ratio
    forecast_dispersion_score = _bounded_ratio(
        input_row.forecast_dispersion,
        cfg.target_forecast_dispersion,
    )
    market_staleness_score = _bounded_ratio(
        input_row.market_staleness_hours,
        cfg.target_market_staleness_hours,
    )
    resolution_clarity_score = _q(ONE - input_row.resolution_ambiguity)
    edge_score = _q(
        (source_freshness_score * cfg.freshness_weight)
        + (source_reliability_score * cfg.reliability_weight)
        + (coverage_quorum_score * cfg.coverage_quorum_weight)
        + (forecast_dispersion_score * cfg.forecast_dispersion_weight)
        + (market_staleness_score * cfg.market_staleness_weight)
        + (resolution_clarity_score * cfg.resolution_clarity_weight),
    )

    source_is_reliable = input_row.source_reliability >= cfg.min_source_reliability
    coverage_is_met = coverage_quorum_ratio >= cfg.min_coverage_quorum_ratio
    dispersion_is_material = input_row.forecast_dispersion >= cfg.target_forecast_dispersion
    market_is_stale = input_row.market_staleness_hours >= cfg.target_market_staleness_hours
    resolution_is_clear = input_row.resolution_ambiguity <= cfg.max_resolution_ambiguity
    source_is_fresh = input_row.source_freshness_hours < cfg.max_source_freshness_hours
    edge_tier = _edge_tier(
        edge_score,
        cfg,
        source_is_reliable=source_is_reliable,
        coverage_is_met=coverage_is_met,
        resolution_is_clear=resolution_is_clear,
    )

    report_values: dict[str, Any] = {
        "config_version": cfg.config_version,
        "generated_at": normalized_generated_at,
        "market_slug": input_row.market_slug,
        "event_slug": input_row.event_slug,
        "source_observed_at": input_row.source_observed_at,
        "source_freshness_hours": input_row.source_freshness_hours,
        "source_reliability": input_row.source_reliability,
        "coverage_source_count": input_row.coverage_source_count,
        "required_coverage_source_count": input_row.required_coverage_source_count,
        "coverage_quorum_ratio": coverage_quorum_ratio,
        "forecast_dispersion": input_row.forecast_dispersion,
        "market_staleness_hours": input_row.market_staleness_hours,
        "resolution_ambiguity": input_row.resolution_ambiguity,
        "source_freshness_score": source_freshness_score,
        "source_reliability_score": source_reliability_score,
        "coverage_quorum_score": coverage_quorum_score,
        "forecast_dispersion_score": forecast_dispersion_score,
        "market_staleness_score": market_staleness_score,
        "resolution_clarity_score": resolution_clarity_score,
        "edge_score": edge_score,
        "edge_tier": edge_tier,
        "research_priority": _priority_for_tier(edge_tier),
        "reason_codes": _reason_codes_for_tier(
            edge_tier,
            source_is_fresh=source_is_fresh,
            source_is_reliable=source_is_reliable,
            coverage_is_met=coverage_is_met,
            dispersion_is_material=dispersion_is_material,
            market_is_stale=market_is_stale,
            resolution_is_clear=resolution_is_clear,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyInformationEdgeScoreV10Report(
        **report_values,
        derived_validation_digest=_derived_validation_digest(report_values),
    )


def strategy_information_edge_score_v10_payload(
    report: StrategyInformationEdgeScoreV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyInformationEdgeScoreV10Report:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_decimal_strings(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyInformationEdgeScoreV10Report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_derived_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _edge_tier(
    edge_score: Decimal,
    config: StrategyInformationEdgeScoreV10Config,
    *,
    source_is_reliable: bool,
    coverage_is_met: bool,
    resolution_is_clear: bool,
) -> str:
    if not (source_is_reliable and coverage_is_met and resolution_is_clear):
        return BLOCKED_EDGE_TIER
    if edge_score >= config.high_edge_score:
        return HIGH_EDGE_TIER
    if edge_score >= config.medium_edge_score:
        return MEDIUM_EDGE_TIER
    return LOW_EDGE_TIER


def _priority_for_tier(edge_tier: str) -> str:
    if edge_tier == HIGH_EDGE_TIER:
        return "urgent"
    if edge_tier == MEDIUM_EDGE_TIER:
        return "high"
    if edge_tier == LOW_EDGE_TIER:
        return "monitor"
    if edge_tier == BLOCKED_EDGE_TIER:
        return "blocked"
    raise ValueError("edge_tier is not supported")


PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "generated_at",
    "market_slug",
    "event_slug",
    "source_observed_at",
    "source_freshness_hours",
    "source_reliability",
    "coverage_source_count",
    "required_coverage_source_count",
    "coverage_quorum_ratio",
    "forecast_dispersion",
    "market_staleness_hours",
    "resolution_ambiguity",
    "source_freshness_score",
    "source_reliability_score",
    "coverage_quorum_score",
    "forecast_dispersion_score",
    "market_staleness_score",
    "resolution_clarity_score",
    "edge_score",
    "edge_tier",
    "research_priority",
    "reason_codes",
    DERIVED_VALIDATION_DIGEST_FIELD,
    "paper_only",
    "report_only",
    "readonly",
)

PUBLIC_VALUE_DECIMAL_STRING_FIELDS = frozenset(
    (
        "source_freshness_hours",
        "market_staleness_hours",
    ),
)
PUBLIC_COUNT_DECIMAL_STRING_FIELDS = frozenset(
    (
        "coverage_source_count",
        "required_coverage_source_count",
    ),
)
PUBLIC_PROBABILITY_DECIMAL_STRING_FIELDS = frozenset(
    (
        "source_reliability",
        "coverage_quorum_ratio",
        "forecast_dispersion",
        "resolution_ambiguity",
        "source_freshness_score",
        "source_reliability_score",
        "coverage_quorum_score",
        "forecast_dispersion_score",
        "market_staleness_score",
        "resolution_clarity_score",
        "edge_score",
    ),
)


def _validate_report_derived_values(
    report: StrategyInformationEdgeScoreV10Report,
) -> None:
    if report.coverage_quorum_ratio != _bounded_ratio(
        report.coverage_source_count,
        report.required_coverage_source_count,
    ):
        raise ValueError("report derived validation failed")
    if report.coverage_quorum_score != report.coverage_quorum_ratio:
        raise ValueError("report derived validation failed")
    if report.source_reliability_score != report.source_reliability:
        raise ValueError("report derived validation failed")
    if report.resolution_clarity_score != _q(ONE - report.resolution_ambiguity):
        raise ValueError("report derived validation failed")


def _validate_report_derived_digest(
    report: StrategyInformationEdgeScoreV10Report,
) -> None:
    expected_digest = _derived_validation_digest(_report_digest_values(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("report derived_validation_digest must match")


def _validate_public_payload_derived_digest(payload: dict[str, Any]) -> None:
    if frozenset(payload) != frozenset(PUBLIC_PAYLOAD_FIELDS):
        raise ValueError("payload fields must match")
    provided_digest = _normalize_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("payload derived validation failed")


def _validate_public_payload_decimal_strings(payload: dict[str, Any]) -> None:
    for field_name in PUBLIC_VALUE_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            _require_decimal_string(
                field_name,
                payload[field_name],
                VALUE_QUANTUM,
            )
    for field_name in PUBLIC_PROBABILITY_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            normalized = _require_decimal_string(
                field_name,
                payload[field_name],
                VALUE_QUANTUM,
            )
            if normalized < ZERO or normalized > ONE:
                raise ValueError(f"{field_name} Decimal-string must be between zero and one")
    for field_name in PUBLIC_COUNT_DECIMAL_STRING_FIELDS:
        if field_name in payload:
            _require_decimal_string(
                field_name,
                payload[field_name],
                COUNT_QUANTUM,
            )


def _require_decimal_string(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-string") from exc
    normalized = _normalize_decimal(field_name, decimal_value, quantum)
    if str(normalized) != value:
        raise ValueError(f"{field_name} Decimal-string precision must match")
    return normalized


def _report_digest_values(report: StrategyInformationEdgeScoreV10Report) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "generated_at": report.generated_at,
        "market_slug": report.market_slug,
        "event_slug": report.event_slug,
        "source_observed_at": report.source_observed_at,
        "source_freshness_hours": report.source_freshness_hours,
        "source_reliability": report.source_reliability,
        "coverage_source_count": report.coverage_source_count,
        "required_coverage_source_count": report.required_coverage_source_count,
        "coverage_quorum_ratio": report.coverage_quorum_ratio,
        "forecast_dispersion": report.forecast_dispersion,
        "market_staleness_hours": report.market_staleness_hours,
        "resolution_ambiguity": report.resolution_ambiguity,
        "source_freshness_score": report.source_freshness_score,
        "source_reliability_score": report.source_reliability_score,
        "coverage_quorum_score": report.coverage_quorum_score,
        "forecast_dispersion_score": report.forecast_dispersion_score,
        "market_staleness_score": report.market_staleness_score,
        "resolution_clarity_score": report.resolution_clarity_score,
        "edge_score": report.edge_score,
        "edge_tier": report.edge_tier,
        "research_priority": report.research_priority,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derived_validation_digest(value: dict[str, Any]) -> str:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("derived validation values must be a JSON object")
    digest_values = {
        key: ready[key]
        for key in PUBLIC_PAYLOAD_FIELDS
        if key != DERIVED_VALIDATION_DIGEST_FIELD
    }
    encoded = json.dumps(
        digest_values,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reason_codes_for_tier(
    edge_tier: str,
    *,
    source_is_fresh: bool,
    source_is_reliable: bool,
    coverage_is_met: bool,
    dispersion_is_material: bool,
    market_is_stale: bool,
    resolution_is_clear: bool,
) -> tuple[str, ...]:
    codes = (
        "coverage_quorum_met" if coverage_is_met else "coverage_quorum_missed",
        (
            "forecast_dispersion_material"
            if dispersion_is_material
            else "forecast_dispersion_thin"
        ),
        f"information_edge_{edge_tier}",
        "market_stale" if market_is_stale else "market_recent",
        "resolution_clear" if resolution_is_clear else "resolution_ambiguity_high",
        "source_fresh" if source_is_fresh else "source_aging",
        "source_reliable" if source_is_reliable else "source_reliability_low",
    )
    return tuple(sorted(codes))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be above zero")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return _q(ratio)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, VALUE_QUANTUM)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_choice(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        return value
    if len(value) != 64 or any(character not in LOWER_HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        normalized.append(item)
    if tuple(sorted(normalized)) != tuple(normalized):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_sensitive_text(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has sensitive or unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in SENSITIVE_TEXT_FRAGMENTS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_FIELD_FRAGMENTS)


__all__ = (
    "DEFAULT_STRATEGY_INFORMATION_EDGE_SCORE_V10_CONFIG_VERSION",
    "StrategyInformationEdgeScoreV10Config",
    "StrategyInformationEdgeScoreV10Input",
    "StrategyInformationEdgeScoreV10Report",
    "score_strategy_information_edge_v10",
    "strategy_information_edge_score_v10_payload",
)
