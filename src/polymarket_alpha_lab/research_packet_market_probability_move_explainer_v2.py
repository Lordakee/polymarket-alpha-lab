"""Pure in-memory Phase 1 market probability move explainer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_MARKET_PROBABILITY_MOVE_EXPLAINER_V2_CONFIG_VERSION = (
    "research-packet-market-probability-move-explainer-v2"
)

Q = Decimal("0.000001")
COUNT_Q = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
COUNT_ONE = Decimal("1")

OFFICIAL_CONFIRMATION_STATUSES = frozenset(("confirmed", "unconfirmed", "denied"))
CONTRADICTION_STATUSES = frozenset(("none", "minor", "material"))
MOVE_DIRECTIONS = frozenset(("up", "down", "flat"))
MOVE_BANDS = frozenset(("large", "medium", "small"))
LIQUIDITY_CONTEXTS = frozenset(("thin", "normal", "deep"))
FRESHNESS_STATUSES = frozenset(("fresh", "watch", "stale"))
REASON_PRIORITY = {
    "move_large": 0,
    "move_medium": 1,
    "move_small": 2,
    "move_up": 3,
    "move_down": 4,
    "move_flat": 5,
    "sources_multiple": 6,
    "sources_single": 7,
    "official_confirmed": 8,
    "official_unconfirmed": 9,
    "official_denied": 10,
    "contradiction_material": 11,
    "contradiction_minor": 12,
    "contradiction_none": 13,
    "liquidity_thin": 14,
    "liquidity_normal": 15,
    "liquidity_deep": 16,
    "freshness_fresh": 17,
    "freshness_watch": 18,
    "freshness_stale": 19,
}
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "market_count",
        "confirmed_count",
        "contradicted_count",
        "stale_count",
        "largest_move_magnitude",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "rank",
        "market_id",
        "market_title",
        "before_price",
        "after_price",
        "move_magnitude",
        "move_direction",
        "move_band",
        "source_events",
        "source_event_count",
        "official_confirmation_status",
        "contradiction_status",
        "liquidity_depth_usd",
        "liquidity_context",
        "latest_source_age_hours",
        "freshness_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "sign" + "ing",
        "b" + "uy",
        "se" + "ll",
        "tra" + "de",
    ),
)


@dataclass(frozen=True)
class ResearchPacketMarketProbabilityMoveExplainerV2Config:
    config_version: str
    fresh_source_hours: Decimal
    stale_source_hours: Decimal
    thin_liquidity_depth_usd: Decimal
    deep_liquidity_depth_usd: Decimal
    large_move_threshold: Decimal
    medium_move_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        for name in (
            "fresh_source_hours",
            "stale_source_hours",
            "thin_liquidity_depth_usd",
            "deep_liquidity_depth_usd",
        ):
            object.__setattr__(self, name, _dec_positive(name, getattr(self, name)))
        for name in ("large_move_threshold", "medium_move_threshold"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        if self.fresh_source_hours > self.stale_source_hours:
            raise ValueError("fresh_source_hours must not exceed stale_source_hours")
        if self.thin_liquidity_depth_usd > self.deep_liquidity_depth_usd:
            raise ValueError("thin_liquidity_depth_usd must not exceed deep_liquidity_depth_usd")
        if self.medium_move_threshold > self.large_move_threshold:
            raise ValueError("medium_move_threshold must not exceed large_move_threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketMarketProbabilityMoveExplainerV2Input:
    market_id: str
    market_title: str
    before_price: Decimal
    after_price: Decimal
    latest_source_age_hours: Decimal
    source_events: tuple[str, ...]
    official_confirmation_status: str
    contradiction_status: str
    liquidity_depth_usd: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _safe_text("market_id", self.market_id)
        _safe_text("market_title", self.market_title)
        for name in ("before_price", "after_price"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "latest_source_age_hours",
            _dec_nonnegative("latest_source_age_hours", self.latest_source_age_hours),
        )
        object.__setattr__(
            self,
            "source_events",
            _source_events(self.source_events),
        )
        _member(
            "official_confirmation_status",
            self.official_confirmation_status,
            OFFICIAL_CONFIRMATION_STATUSES,
        )
        _member("contradiction_status", self.contradiction_status, CONTRADICTION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _dec_nonnegative("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchPacketMarketProbabilityMoveExplainerV2Row:
    rank: Decimal
    market_id: str
    market_title: str
    before_price: Decimal
    after_price: Decimal
    move_magnitude: Decimal
    move_direction: str
    move_band: str
    source_events: tuple[str, ...]
    source_event_count: Decimal
    official_confirmation_status: str
    contradiction_status: str
    liquidity_depth_usd: Decimal
    liquidity_context: str
    latest_source_age_hours: Decimal
    freshness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _count_positive("rank", self.rank))
        _safe_text("market_id", self.market_id)
        _safe_text("market_title", self.market_title)
        for name in ("before_price", "after_price"):
            object.__setattr__(self, name, _ratio(name, getattr(self, name)))
        object.__setattr__(
            self,
            "move_magnitude",
            _ratio("move_magnitude", self.move_magnitude),
        )
        _member("move_direction", self.move_direction, MOVE_DIRECTIONS)
        _member("move_band", self.move_band, MOVE_BANDS)
        object.__setattr__(self, "source_events", _source_events(self.source_events))
        object.__setattr__(
            self,
            "source_event_count",
            _count("source_event_count", self.source_event_count),
        )
        _member(
            "official_confirmation_status",
            self.official_confirmation_status,
            OFFICIAL_CONFIRMATION_STATUSES,
        )
        _member("contradiction_status", self.contradiction_status, CONTRADICTION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _dec_nonnegative("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        _member("liquidity_context", self.liquidity_context, LIQUIDITY_CONTEXTS)
        object.__setattr__(
            self,
            "latest_source_age_hours",
            _dec_nonnegative("latest_source_age_hours", self.latest_source_age_hours),
        )
        _member("freshness_status", self.freshness_status, FRESHNESS_STATUSES)
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketMarketProbabilityMoveExplainerV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    confirmed_count: Decimal
    contradicted_count: Decimal
    stale_count: Decimal
    largest_move_magnitude: Decimal
    rows: tuple[ResearchPacketMarketProbabilityMoveExplainerV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        for name in (
            "market_count",
            "confirmed_count",
            "contradicted_count",
            "stale_count",
        ):
            object.__setattr__(self, name, _count(name, getattr(self, name)))
        object.__setattr__(
            self,
            "largest_move_magnitude",
            _ratio("largest_move_magnitude", self.largest_move_magnitude),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _hex_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_digest(self)
        _report_matches(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_market_probability_move_explainer_v2_payload(self)


def build_research_packet_market_probability_move_explainer_v2(
    inputs: Iterable[ResearchPacketMarketProbabilityMoveExplainerV2Input],
    *,
    config: ResearchPacketMarketProbabilityMoveExplainerV2Config,
    generated_at: datetime,
) -> ResearchPacketMarketProbabilityMoveExplainerV2Report:
    if type(config) is not ResearchPacketMarketProbabilityMoveExplainerV2Config:
        raise ValueError("config must be a market probability move explainer config")
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    built_rows = _ranked_rows(tuple(_row(item, config) for item in input_rows))
    report_values = {
        "generated_at": stamp,
        "config_version": config.config_version,
        "market_count": Decimal(len(built_rows)),
        "confirmed_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.official_confirmation_status == "confirmed"),
        ),
        "contradicted_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.contradiction_status != "none"),
        ),
        "stale_count": Decimal(
            sum(COUNT_ONE for row in built_rows if row.freshness_status == "stale"),
        ),
        "largest_move_magnitude": max(
            (row.move_magnitude for row in built_rows),
            default=ZERO,
        ),
        "rows": built_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _derive_digest_from_public_payload(_payload(report_values))
    return ResearchPacketMarketProbabilityMoveExplainerV2Report(
        **report_values,
        derived_validation_digest=digest,
    )


def research_packet_market_probability_move_explainer_v2_payload(
    report: ResearchPacketMarketProbabilityMoveExplainerV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketMarketProbabilityMoveExplainerV2Report:
        _require_hard_flags("report", report)
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a market probability move explainer report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _require_payload_digest(payload)
    return payload


def derive_research_packet_market_probability_move_explainer_v2_digest(
    report: ResearchPacketMarketProbabilityMoveExplainerV2Report | dict[str, Any],
) -> str:
    if type(report) is ResearchPacketMarketProbabilityMoveExplainerV2Report:
        payload = _payload(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a market probability move explainer report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_hard_flags("payload", _DictFlags(payload))
    return _derive_digest_from_public_payload(payload)


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


def _row(
    item: ResearchPacketMarketProbabilityMoveExplainerV2Input,
    config: ResearchPacketMarketProbabilityMoveExplainerV2Config,
) -> ResearchPacketMarketProbabilityMoveExplainerV2Row:
    magnitude = _move_magnitude(item.before_price, item.after_price)
    direction = _move_direction(item.before_price, item.after_price)
    band = _move_band(magnitude, config)
    liquidity = _liquidity_context(item.liquidity_depth_usd, config)
    freshness = _freshness_status(item.latest_source_age_hours, config)
    return ResearchPacketMarketProbabilityMoveExplainerV2Row(
        rank=COUNT_ONE,
        market_id=item.market_id,
        market_title=item.market_title,
        before_price=item.before_price,
        after_price=item.after_price,
        move_magnitude=magnitude,
        move_direction=direction,
        move_band=band,
        source_events=item.source_events,
        source_event_count=Decimal(len(item.source_events)),
        official_confirmation_status=item.official_confirmation_status,
        contradiction_status=item.contradiction_status,
        liquidity_depth_usd=item.liquidity_depth_usd,
        liquidity_context=liquidity,
        latest_source_age_hours=item.latest_source_age_hours,
        freshness_status=freshness,
        reason_codes=_dedupe(
            (
                f"move_{band}",
                f"move_{direction}",
                _source_event_reason(item.source_events),
                f"official_{item.official_confirmation_status}",
                f"contradiction_{item.contradiction_status}",
                f"liquidity_{liquidity}",
                f"freshness_{freshness}",
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[ResearchPacketMarketProbabilityMoveExplainerV2Row, ...],
) -> tuple[ResearchPacketMarketProbabilityMoveExplainerV2Row, ...]:
    ranked = []
    for index, row in enumerate(sorted(rows, key=_row_key), start=1):
        ranked.append(
            ResearchPacketMarketProbabilityMoveExplainerV2Row(
                rank=Decimal(index),
                market_id=row.market_id,
                market_title=row.market_title,
                before_price=row.before_price,
                after_price=row.after_price,
                move_magnitude=row.move_magnitude,
                move_direction=row.move_direction,
                move_band=row.move_band,
                source_events=row.source_events,
                source_event_count=row.source_event_count,
                official_confirmation_status=row.official_confirmation_status,
                contradiction_status=row.contradiction_status,
                liquidity_depth_usd=row.liquidity_depth_usd,
                liquidity_context=row.liquidity_context,
                latest_source_age_hours=row.latest_source_age_hours,
                freshness_status=row.freshness_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_key(row: ResearchPacketMarketProbabilityMoveExplainerV2Row) -> tuple[Decimal, Decimal, str]:
    return (-row.move_magnitude, row.latest_source_age_hours, row.market_id)


def _move_magnitude(before_price: Decimal, after_price: Decimal) -> Decimal:
    return _q(abs(after_price - before_price))


def _move_direction(before_price: Decimal, after_price: Decimal) -> str:
    if after_price > before_price:
        return "up"
    if after_price < before_price:
        return "down"
    return "flat"


def _move_band(
    move_magnitude: Decimal,
    config: ResearchPacketMarketProbabilityMoveExplainerV2Config,
) -> str:
    if move_magnitude >= config.large_move_threshold:
        return "large"
    if move_magnitude >= config.medium_move_threshold:
        return "medium"
    return "small"


def _liquidity_context(
    liquidity_depth_usd: Decimal,
    config: ResearchPacketMarketProbabilityMoveExplainerV2Config,
) -> str:
    if liquidity_depth_usd < config.thin_liquidity_depth_usd:
        return "thin"
    if liquidity_depth_usd >= config.deep_liquidity_depth_usd:
        return "deep"
    return "normal"


def _freshness_status(
    latest_source_age_hours: Decimal,
    config: ResearchPacketMarketProbabilityMoveExplainerV2Config,
) -> str:
    if latest_source_age_hours <= config.fresh_source_hours:
        return "fresh"
    if latest_source_age_hours <= config.stale_source_hours:
        return "watch"
    return "stale"


def _source_event_reason(source_events: tuple[str, ...]) -> str:
    if len(source_events) > 1:
        return "sources_multiple"
    return "sources_single"


def _validate_row(row: ResearchPacketMarketProbabilityMoveExplainerV2Row) -> None:
    if row.move_magnitude != _move_magnitude(row.before_price, row.after_price):
        raise ValueError("move_magnitude must match before_price and after_price")
    if row.move_direction != _move_direction(row.before_price, row.after_price):
        raise ValueError("move_direction must match before_price and after_price")
    if row.source_event_count != Decimal(len(row.source_events)):
        raise ValueError("source_event_count must match source_events")
    required_reasons = (
        f"move_{row.move_band}",
        f"move_{row.move_direction}",
        _source_event_reason(row.source_events),
        f"official_{row.official_confirmation_status}",
        f"contradiction_{row.contradiction_status}",
        f"liquidity_{row.liquidity_context}",
        f"freshness_{row.freshness_status}",
    )
    if any(reason not in row.reason_codes for reason in required_reasons):
        raise ValueError("reason_codes must explain the row")


def _report_matches(report: ResearchPacketMarketProbabilityMoveExplainerV2Report) -> None:
    rows = report.rows
    if report.market_count != Decimal(len(rows)):
        raise ValueError("market_count must match rows")
    if report.confirmed_count != Decimal(
        sum(COUNT_ONE for row in rows if row.official_confirmation_status == "confirmed"),
    ):
        raise ValueError("confirmed_count must match rows")
    if report.contradicted_count != Decimal(
        sum(COUNT_ONE for row in rows if row.contradiction_status != "none"),
    ):
        raise ValueError("contradicted_count must match rows")
    if report.stale_count != Decimal(
        sum(COUNT_ONE for row in rows if row.freshness_status == "stale"),
    ):
        raise ValueError("stale_count must match rows")
    if report.largest_move_magnitude != max(
        (row.move_magnitude for row in rows),
        default=ZERO,
    ):
        raise ValueError("largest_move_magnitude must match rows")
    expected_ranks = tuple(Decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("row ranks must be sequential")


def _validate_digest(report: ResearchPacketMarketProbabilityMoveExplainerV2Report) -> None:
    if report.derived_validation_digest != _derive_digest_from_public_payload(_payload(report)):
        raise ValueError("derived_validation_digest must match report payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _hex_digest("derived_validation_digest", digest)
    if digest != _derive_digest_from_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _derive_digest_from_public_payload(payload: dict[str, Any]) -> str:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name in {
            "rank",
            "market_count",
            "confirmed_count",
            "contradicted_count",
            "stale_count",
            "source_event_count",
        } and value == value.to_integral_value():
            return str(value.quantize(COUNT_Q))
        return str(value)
    if type(value) is datetime:
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text[:-6] + "Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload(item) for item in value]
    if isinstance(value, list):
        return [_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _payload(item, field_name=key)
            for key, item in value.items()
        }
    return value


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must use exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is bool or type(value) is str or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool = True,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    if digest_required and "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest must be present")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        _require_hard_flags("row payload", _DictFlags(row))


def _normalize_inputs(
    inputs: Iterable[ResearchPacketMarketProbabilityMoveExplainerV2Input],
) -> tuple[ResearchPacketMarketProbabilityMoveExplainerV2Input, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchPacketMarketProbabilityMoveExplainerV2Input:
            raise ValueError("inputs must contain market probability move explainer inputs")
        _require_hard_flags("input", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchPacketMarketProbabilityMoveExplainerV2Row, ...],
) -> tuple[ResearchPacketMarketProbabilityMoveExplainerV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPacketMarketProbabilityMoveExplainerV2Row:
            raise ValueError("rows must contain market probability move explainer row values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _source_events(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("source_events must be a tuple")
    if not values:
        raise ValueError("source_events must not be empty")
    normalized = tuple(_checked_source_event(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("source_events must be unique")
    return tuple(sorted(normalized))


def _checked_source_event(value: str) -> str:
    _safe_text("source_events", value)
    return value


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_checked_reason(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _checked_reason(value: str) -> str:
    if type(value) is not str or value not in REASON_PRIORITY:
        raise ValueError("reason_codes must be supported")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")
    return value


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        _checked_reason(value)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(sorted(result, key=lambda item: REASON_PRIORITY[item]))


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_text(name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{name} must not have outer whitespace")
    if _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _config_version(value: str) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_PACKET_MARKET_PROBABILITY_MOVE_EXPLAINER_V2_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _hex_digest(name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _member(name: str, value: str, allowed: frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} is not supported")


def _dec(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _dec_nonnegative(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _dec_positive(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio(name: str, value: Decimal) -> Decimal:
    result = _dec_nonnegative(name, value)
    if result > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return result


def _count(name: str, value: Decimal) -> Decimal:
    result = _dec(name, value)
    if result < COUNT_ZERO or result != result.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return result


def _count_positive(name: str, value: Decimal) -> Decimal:
    result = _count(name, value)
    if result <= COUNT_ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_MARKET_PROBABILITY_MOVE_EXPLAINER_V2_CONFIG_VERSION",
    "ResearchPacketMarketProbabilityMoveExplainerV2Config",
    "ResearchPacketMarketProbabilityMoveExplainerV2Input",
    "ResearchPacketMarketProbabilityMoveExplainerV2Report",
    "ResearchPacketMarketProbabilityMoveExplainerV2Row",
    "build_research_packet_market_probability_move_explainer_v2",
    "derive_research_packet_market_probability_move_explainer_v2_digest",
    "research_packet_market_probability_move_explainer_v2_payload",
)
