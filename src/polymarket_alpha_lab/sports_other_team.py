"""Minimal supplied-input other sports team forecast workflow."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


TEAM_ID = "sports_other"
CATEGORY_ID = "sports.other"
PROMPT_VERSION = "sports-other-supplied-input-v0"
TEAM_REASON_CODE = "team_sports_other"
MEMORY_REFERENCES = ("sports_other_supplied_evidence_only",)
KNOWN_FAILURE_MODES = (
    "sport_specific_rule_mismatch",
    "thin_other_sports_market_liquidity",
    "late_availability_weather_news",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)


@dataclass(frozen=True)
class SportsOtherTeamConfig:
    config_version: str
    market_implied_probability_hint: Decimal = Decimal("0.500000")
    resolution_risk: Decimal = Decimal("0.120000")
    prompt_version: str = PROMPT_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("prompt_version", self.prompt_version)
        object.__setattr__(
            self,
            "market_implied_probability_hint",
            _normalize_probability(
                "market_implied_probability_hint",
                self.market_implied_probability_hint,
            ),
        )
        object.__setattr__(
            self,
            "resolution_risk",
            _normalize_probability("resolution_risk", self.resolution_risk),
        )
        require_paper_only_flags("sports other team config", self)


@dataclass(frozen=True)
class SportsOtherEvidenceInput:
    source_id: str
    source_type: str
    evidence_text: str
    data_timestamp: datetime
    data_freshness_seconds: int
    evidence_type: str
    weight: Decimal
    probability_impact: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "source_type",
            "evidence_text",
            "evidence_type",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_nonnegative_int(
            "data_freshness_seconds",
            self.data_freshness_seconds,
        )
        object.__setattr__(self, "weight", _normalize_probability("weight", self.weight))
        object.__setattr__(
            self,
            "probability_impact",
            _normalize_decimal("probability_impact", self.probability_impact),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("sports other evidence input", self)


def build_sports_other_team_forecast(
    *,
    condition_id: str,
    market_slug: str,
    question: str,
    event_template: str,
    evidence: Iterable[SportsOtherEvidenceInput],
    base_probability: Decimal,
    config: SportsOtherTeamConfig,
    generated_at: datetime,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    _require_canonical_string("condition_id", condition_id)
    _require_canonical_string("market_slug", market_slug)
    _require_canonical_string("question", question)
    _require_canonical_string("event_template", event_template)
    if type(config) is not SportsOtherTeamConfig:
        raise ValueError("config must be a SportsOtherTeamConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    require_paper_only_flags("sports other team config", config)

    evidence_items = _normalize_evidence(evidence)
    normalized_base_probability = _normalize_probability(
        "base_probability",
        base_probability,
    )
    market_implied_probability_hint = _normalize_probability(
        "market_implied_probability_hint",
        config.market_implied_probability_hint,
    )
    resolution_risk = _normalize_probability("resolution_risk", config.resolution_risk)

    forecast_probability = _forecast_probability(
        normalized_base_probability,
        evidence_items,
    )
    average_weight = _average_weight(evidence_items)
    selected_side = (
        "yes" if forecast_probability >= market_implied_probability_hint else "no"
    )
    evidence_rows = _build_evidence_packets(
        condition_id=condition_id,
        market_slug=market_slug,
        evidence=evidence_items,
    )

    forecast = TeamForecastPacket(
        forecast_id=f"{condition_id}:{TEAM_ID}",
        team_id=TEAM_ID,
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        category_id=CATEGORY_ID,
        event_template=event_template,
        selected_side=selected_side,
        forecast_probability=forecast_probability,
        confidence=average_weight,
        evidence_quality=average_weight,
        data_freshness_score=_data_freshness_score(evidence_items),
        resolution_risk=resolution_risk,
        base_rate=normalized_base_probability,
        market_implied_probability_observed=market_implied_probability_hint,
        reason_codes=_forecast_reason_codes(evidence_items),
        memory_references=MEMORY_REFERENCES,
        source_references=_source_references(evidence_items),
        known_failure_modes=KNOWN_FAILURE_MODES,
        config_version=config.config_version,
        prompt_version=config.prompt_version,
        generated_at=generated_at,
    )
    return forecast, evidence_rows


def _normalize_evidence(
    evidence: Iterable[SportsOtherEvidenceInput],
) -> tuple[SportsOtherEvidenceInput, ...]:
    if isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be an iterable of SportsOtherEvidenceInput values")
    try:
        items = tuple(evidence)
    except TypeError as exc:
        raise ValueError(
            "evidence must be an iterable of SportsOtherEvidenceInput values",
        ) from exc
    if not items:
        raise ValueError("evidence must contain at least one item")
    for item in items:
        if type(item) is not SportsOtherEvidenceInput:
            raise ValueError("evidence must contain only SportsOtherEvidenceInput values")
        require_paper_only_flags("sports other evidence input", item)
    return items


def _build_evidence_packets(
    *,
    condition_id: str,
    market_slug: str,
    evidence: tuple[SportsOtherEvidenceInput, ...],
) -> tuple[TeamForecastEvidencePacket, ...]:
    return tuple(
        TeamForecastEvidencePacket(
            evidence_id=f"{condition_id}:{item.source_id}",
            team_id=TEAM_ID,
            market_slug=market_slug,
            source_id=item.source_id,
            source_type=item.source_type,
            data_timestamp=item.data_timestamp,
            data_freshness_seconds=item.data_freshness_seconds,
            evidence_type=item.evidence_type,
            evidence_text=item.evidence_text,
            weight=item.weight,
            reason_codes=item.reason_codes,
        )
        for item in evidence
    )


def _forecast_probability(
    base_probability: Decimal,
    evidence: tuple[SportsOtherEvidenceInput, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = base_probability + sum(
            (item.probability_impact for item in evidence),
            ZERO,
        )
    return _clamp_probability(value)


def _average_weight(evidence: tuple[SportsOtherEvidenceInput, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        average = sum((item.weight for item in evidence), ZERO) / Decimal(len(evidence))
    return _clamp_probability(average)


def _data_freshness_score(evidence: tuple[SportsOtherEvidenceInput, ...]) -> Decimal:
    max_freshness_seconds = max(item.data_freshness_seconds for item in evidence)
    if max_freshness_seconds <= 900:
        return Decimal("1.000000")
    if max_freshness_seconds <= 7200:
        return Decimal("0.750000")
    if max_freshness_seconds <= 86400:
        return Decimal("0.500000")
    return Decimal("0.250000")


def _forecast_reason_codes(
    evidence: tuple[SportsOtherEvidenceInput, ...],
) -> tuple[str, ...]:
    reason_codes = [TEAM_REASON_CODE]
    for item in evidence:
        reason_codes.extend(item.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _source_references(
    evidence: tuple[SportsOtherEvidenceInput, ...],
) -> tuple[str, ...]:
    return tuple(sorted({item.source_id for item in evidence}))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return Decimal("0.000000")
    if value > ONE:
        return Decimal("1.000000")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    items = _normalize_string_tuple("reason_codes", value)
    return tuple(sorted(set(items)))


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "SportsOtherEvidenceInput",
    "SportsOtherTeamConfig",
    "build_sports_other_team_forecast",
)
