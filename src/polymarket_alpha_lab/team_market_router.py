"""Paper-only deterministic market routing for specialist team workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_category_id, require_team_id


CONFIDENCE_QUANT = Decimal("0.000001")

CATEGORY_TO_PRIMARY_TEAM = {
    "politics": "politics",
    "finance.crypto.btc": "crypto_btc",
    "finance.crypto.eth": "crypto_eth",
    "finance.macro.rates": "macro_rates",
    "finance.equity.indices": "equity_indices",
    "finance.commodities.gold": "commodities_gold",
    "finance.commodities.oil": "commodities_oil",
    "sports.soccer": "sports_soccer",
    "sports.basketball": "sports_basketball",
    "sports.other": "sports_other",
}

DEFAULT_ROUTING_CONFIDENCE = Decimal("0.900000")
SPORTS_UNKNOWN_ROUTING_CONFIDENCE = Decimal("0.700000")


@dataclass(frozen=True)
class TeamMarketRouteConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamMarketRouteConfig", self)


@dataclass(frozen=True)
class TeamMarketRouteInput:
    condition_id: str
    market_slug: str
    question: str
    category_hint: str
    event_template: str
    routing_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("category_hint", self.category_hint)
        _require_canonical_string("event_template", self.event_template)
        object.__setattr__(
            self,
            "routing_reason_codes",
            _normalize_string_tuple(
                "routing_reason_codes",
                self.routing_reason_codes,
            ),
        )
        require_paper_only_flags("TeamMarketRouteInput", self)


@dataclass(frozen=True)
class TeamMarketRouteRow:
    condition_id: str
    market_slug: str
    question: str
    category_id: str
    event_template: str
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    routing_confidence: Decimal
    routing_reason_codes: tuple[str, ...]
    routing_corrected_team_id: str | None = None
    routing_correction_timestamp: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        object.__setattr__(
            self,
            "category_id",
            require_category_id("category_id", self.category_id),
        )
        _require_canonical_string("event_template", self.event_template)
        primary_team_id = require_team_id("primary_team_id", self.primary_team_id)
        object.__setattr__(self, "primary_team_id", primary_team_id)
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(
                self.secondary_team_ids,
                primary_team_id=primary_team_id,
            ),
        )
        object.__setattr__(
            self,
            "routing_confidence",
            _quantize_confidence(self.routing_confidence),
        )
        object.__setattr__(
            self,
            "routing_reason_codes",
            _normalize_string_tuple(
                "routing_reason_codes",
                self.routing_reason_codes,
            ),
        )
        _validate_routing_correction_metadata(self)
        require_paper_only_flags("TeamMarketRouteRow", self)


@dataclass(frozen=True)
class TeamMarketRouteReport:
    generated_at: datetime
    config_version: str
    route_count: int
    rows: tuple[TeamMarketRouteRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc(self.generated_at, field_name="generated_at"),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("route_count", self.route_count)
        object.__setattr__(self, "rows", _clone_rows(self.rows))
        if self.route_count != len(self.rows):
            raise ValueError("route_count must match rows")
        require_paper_only_flags("TeamMarketRouteReport", self)


def build_team_market_route_report(
    inputs: tuple[TeamMarketRouteInput, ...] | list[TeamMarketRouteInput],
    *,
    config: TeamMarketRouteConfig,
    generated_at: datetime,
) -> TeamMarketRouteReport:
    if type(config) is not TeamMarketRouteConfig:
        raise ValueError("config must be a TeamMarketRouteConfig")
    source_inputs = _normalize_inputs(inputs)
    generated_at_utc = _as_utc(generated_at, field_name="generated_at")
    rows = tuple(_row_from_input(route_input) for route_input in source_inputs)
    return TeamMarketRouteReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        route_count=len(rows),
        rows=rows,
    )


def _row_from_input(route_input: TeamMarketRouteInput) -> TeamMarketRouteRow:
    category_id, primary_team_id, confidence = _route_category_hint(
        route_input.category_hint,
    )
    return TeamMarketRouteRow(
        condition_id=route_input.condition_id,
        market_slug=route_input.market_slug,
        question=route_input.question,
        category_id=category_id,
        event_template=route_input.event_template,
        primary_team_id=primary_team_id,
        secondary_team_ids=(),
        routing_confidence=confidence,
        routing_reason_codes=route_input.routing_reason_codes,
    )


def _route_category_hint(category_hint: str) -> tuple[str, str, Decimal]:
    if category_hint in CATEGORY_TO_PRIMARY_TEAM:
        category_id = require_category_id("category_hint", category_hint)
        return (
            category_id,
            require_team_id("primary_team_id", CATEGORY_TO_PRIMARY_TEAM[category_id]),
            DEFAULT_ROUTING_CONFIDENCE,
        )
    if category_hint.startswith("sports.unknown"):
        return (
            "sports.other",
            "sports_other",
            SPORTS_UNKNOWN_ROUTING_CONFIDENCE,
        )
    raise ValueError("category_hint must be a known routable category")


def _normalize_inputs(
    inputs: tuple[TeamMarketRouteInput, ...] | list[TeamMarketRouteInput],
) -> tuple[TeamMarketRouteInput, ...]:
    if isinstance(inputs, (str, bytes)) or type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(inputs)
    for item in items:
        if type(item) is not TeamMarketRouteInput:
            raise ValueError("inputs must contain TeamMarketRouteInput values")
        require_paper_only_flags("TeamMarketRouteInput", item)
    return items


def _clone_rows(
    rows: tuple[TeamMarketRouteRow, ...],
) -> tuple[TeamMarketRouteRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not TeamMarketRouteRow:
            raise ValueError("rows must contain TeamMarketRouteRow values")
        require_paper_only_flags("TeamMarketRouteRow", item)
    return tuple(
        TeamMarketRouteRow(
            condition_id=row.condition_id,
            market_slug=row.market_slug,
            question=row.question,
            category_id=row.category_id,
            event_template=row.event_template,
            primary_team_id=row.primary_team_id,
            secondary_team_ids=row.secondary_team_ids,
            routing_confidence=row.routing_confidence,
            routing_reason_codes=row.routing_reason_codes,
            routing_corrected_team_id=row.routing_corrected_team_id,
            routing_correction_timestamp=row.routing_correction_timestamp,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
        for row in items
    )


def _validate_routing_correction_metadata(row: TeamMarketRouteRow) -> None:
    corrected_team_id = row.routing_corrected_team_id
    correction_timestamp = row.routing_correction_timestamp
    if corrected_team_id is None and correction_timestamp is None:
        return
    if corrected_team_id is None:
        raise ValueError("routing_corrected_team_id is required with routing_correction_timestamp")
    object.__setattr__(
        row,
        "routing_corrected_team_id",
        require_team_id("routing_corrected_team_id", corrected_team_id),
    )
    if correction_timestamp is None:
        raise ValueError("routing_correction_timestamp is required with routing_corrected_team_id")
    object.__setattr__(
        row,
        "routing_correction_timestamp",
        _as_utc(
            correction_timestamp,
            field_name="routing_correction_timestamp",
        ),
    )


def _normalize_secondary_team_ids(
    value: tuple[str, ...],
    *,
    primary_team_id: str,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("secondary_team_ids must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("secondary_team_ids must be an iterable") from exc
    normalized = tuple(require_team_id("secondary_team_ids", item) for item in items)
    if primary_team_id in normalized:
        raise ValueError("secondary_team_ids cannot contain primary_team_id")
    if len(set(normalized)) != len(normalized):
        raise ValueError("secondary_team_ids must be unique")
    return normalized


def _quantize_confidence(value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("routing_confidence must be a Decimal")
    if not value.is_finite():
        raise ValueError("routing_confidence must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError("routing_confidence must be between 0 and 1")
    return value.quantize(CONFIDENCE_QUANT)


def _as_utc(value: datetime, *, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
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


__all__ = (
    "CATEGORY_TO_PRIMARY_TEAM",
    "TeamMarketRouteConfig",
    "TeamMarketRouteInput",
    "TeamMarketRouteReport",
    "TeamMarketRouteRow",
    "build_team_market_route_report",
)
