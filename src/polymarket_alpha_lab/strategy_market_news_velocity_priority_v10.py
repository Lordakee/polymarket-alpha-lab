"""Pure read-only market news velocity research priority model v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-market-news-velocity-priority-v10"
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ONE_HUNDRED = Decimal("100.000000")
NEW_SOURCE_SCORE_CAP = Decimal("5")
PROBABILITY_MOVE_SCORE_CAP_BPS = Decimal("1000.000000")
IMMEDIATE_RESOLUTION_MINUTES = Decimal("60.000000")
ACCELERATED_RESOLUTION_MINUTES = Decimal("360.000000")

PRIORITY_TIERS = ("research_now", "accelerated_recheck", "monitor")
REASON_CODES = (
    "no_new_sources",
    "new_source_count_present",
    "new_source_count_high",
    "high_reliability_source_share_low",
    "high_reliability_source_share_medium",
    "high_reliability_source_share_high",
    "probability_move_small",
    "probability_move_medium",
    "probability_move_large",
    "source_contradiction_low",
    "source_contradiction_medium",
    "source_contradiction_high",
    "time_sensitive_low",
    "time_sensitive_accelerated",
    "time_sensitive_immediate",
    "priority_tier_research_now",
    "priority_tier_accelerated_recheck",
    "priority_tier_monitor",
)


@dataclass(frozen=True)
class StrategyMarketNewsVelocityPriorityV10Market:
    market_id: str
    market_slug: str
    new_source_count: Decimal
    high_reliability_source_share: Decimal
    probability_move_bps: Decimal
    source_contradiction_score: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "new_source_count",
            _normalize_nonnegative_count("new_source_count", self.new_source_count),
        )
        object.__setattr__(
            self,
            "high_reliability_source_share",
            _normalize_probability(
                "high_reliability_source_share",
                self.high_reliability_source_share,
            ),
        )
        object.__setattr__(
            self,
            "probability_move_bps",
            _normalize_nonnegative_decimal(
                "probability_move_bps",
                self.probability_move_bps,
            ),
        )
        object.__setattr__(
            self,
            "source_contradiction_score",
            _normalize_probability(
                "source_contradiction_score",
                self.source_contradiction_score,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        reject_unsafe_surface_fields("market news velocity priority market", self)
        require_paper_only_flags("market news velocity priority market", self)


@dataclass(frozen=True)
class StrategyMarketNewsVelocityPriorityV10Row:
    research_rank: Decimal
    market_id: str
    market_slug: str
    new_source_count: Decimal
    high_reliability_source_share: Decimal
    probability_move_bps: Decimal
    source_contradiction_score: Decimal
    time_to_resolution_minutes: Decimal
    priority_score: Decimal
    priority_tier: str
    research_cadence: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "research_rank",
            _normalize_positive_count("research_rank", self.research_rank),
        )
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "new_source_count",
            _normalize_nonnegative_count("new_source_count", self.new_source_count),
        )
        object.__setattr__(
            self,
            "high_reliability_source_share",
            _normalize_probability(
                "high_reliability_source_share",
                self.high_reliability_source_share,
            ),
        )
        object.__setattr__(
            self,
            "probability_move_bps",
            _normalize_nonnegative_decimal(
                "probability_move_bps",
                self.probability_move_bps,
            ),
        )
        object.__setattr__(
            self,
            "source_contradiction_score",
            _normalize_probability(
                "source_contradiction_score",
                self.source_contradiction_score,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "priority_score",
            _normalize_score("priority_score", self.priority_score),
        )
        _require_member("priority_tier", self.priority_tier, PRIORITY_TIERS)
        _require_member(
            "research_cadence",
            self.research_cadence,
            ("now", "within_60_minutes", "next_cycle"),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("market news velocity priority row", self)
        require_paper_only_flags("market news velocity priority row", self)


@dataclass(frozen=True)
class StrategyMarketNewsVelocityPriorityV10Report:
    config_version: str
    market_count: Decimal
    research_now_count: Decimal
    accelerated_recheck_count: Decimal
    top_market_id: str | None
    rows: tuple[StrategyMarketNewsVelocityPriorityV10Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_count("market_count", self.market_count),
        )
        object.__setattr__(
            self,
            "research_now_count",
            _normalize_nonnegative_count(
                "research_now_count",
                self.research_now_count,
            ),
        )
        object.__setattr__(
            self,
            "accelerated_recheck_count",
            _normalize_nonnegative_count(
                "accelerated_recheck_count",
                self.accelerated_recheck_count,
            ),
        )
        if self.top_market_id is not None:
            _require_canonical_string("top_market_id", self.top_market_id)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("market news velocity priority report", self)
        require_paper_only_flags("market news velocity priority report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_news_velocity_priority_v10_payload(self)


def build_strategy_market_news_velocity_priority_v10(
    markets: object,
) -> StrategyMarketNewsVelocityPriorityV10Report:
    normalized_markets = _normalize_markets(markets)
    rows = _ranked_rows(normalized_markets)
    return StrategyMarketNewsVelocityPriorityV10Report(
        config_version=DEFAULT_CONFIG_VERSION,
        market_count=_decimal_count(normalized_markets),
        research_now_count=_decimal_count(
            row for row in rows if row.priority_tier == "research_now"
        ),
        accelerated_recheck_count=_decimal_count(
            row for row in rows if row.priority_tier == "accelerated_recheck"
        ),
        top_market_id=rows[0].market_id if rows else None,
        rows=rows,
    )


def strategy_market_news_velocity_priority_v10_payload(
    report: StrategyMarketNewsVelocityPriorityV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyMarketNewsVelocityPriorityV10Report:
        _reject_unsafe_public_payload("market news velocity priority report", report)
        require_paper_only_flags("market news velocity priority report", report)
        payload = _json_ready_public(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("market news velocity priority payload", report)
        payload = _json_ready_public(report)
    else:
        raise ValueError(
            "report must be a StrategyMarketNewsVelocityPriorityV10Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    _reject_unsafe_public_payload("market news velocity priority payload", payload)
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


REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "market_count",
        "research_now_count",
        "accelerated_recheck_count",
        "top_market_id",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "research_rank",
        "market_id",
        "market_slug",
        "new_source_count",
        "high_reliability_source_share",
        "probability_move_bps",
        "source_contradiction_score",
        "time_to_resolution_minutes",
        "priority_score",
        "priority_tier",
        "research_cadence",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _validate_public_payload(payload: dict[str, Any]) -> None:
    require_paper_only_flags("market news velocity priority payload", _DictFlags(payload))
    _require_exact_payload_keys("payload", payload, REPORT_PAYLOAD_FIELDS)
    rows_payload = payload["rows"]
    if type(rows_payload) is not list:
        raise ValueError("rows must be a JSON list")

    rows = tuple(
        _row_from_public_payload(row_payload, row_index)
        for row_index, row_payload in enumerate(rows_payload)
    )
    report = StrategyMarketNewsVelocityPriorityV10Report(
        config_version=payload["config_version"],
        market_count=_decimal_from_public_payload("market_count", payload["market_count"]),
        research_now_count=_decimal_from_public_payload(
            "research_now_count",
            payload["research_now_count"],
        ),
        accelerated_recheck_count=_decimal_from_public_payload(
            "accelerated_recheck_count",
            payload["accelerated_recheck_count"],
        ),
        top_market_id=payload["top_market_id"],
        rows=rows,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    canonical_payload = _json_ready_public(report)
    if canonical_payload != payload:
        raise ValueError("payload must match canonical derived report fields")


def _row_from_public_payload(
    row_payload: object,
    row_index: int,
) -> StrategyMarketNewsVelocityPriorityV10Row:
    if type(row_payload) is not dict:
        raise ValueError("rows must contain JSON objects")
    require_paper_only_flags(
        f"market news velocity priority payload rows[{row_index}]",
        _DictFlags(row_payload),
    )
    _require_exact_payload_keys(f"rows[{row_index}]", row_payload, ROW_PAYLOAD_FIELDS)
    return StrategyMarketNewsVelocityPriorityV10Row(
        research_rank=_decimal_from_public_payload(
            "research_rank",
            row_payload["research_rank"],
        ),
        market_id=row_payload["market_id"],
        market_slug=row_payload["market_slug"],
        new_source_count=_decimal_from_public_payload(
            "new_source_count",
            row_payload["new_source_count"],
        ),
        high_reliability_source_share=_decimal_from_public_payload(
            "high_reliability_source_share",
            row_payload["high_reliability_source_share"],
        ),
        probability_move_bps=_decimal_from_public_payload(
            "probability_move_bps",
            row_payload["probability_move_bps"],
        ),
        source_contradiction_score=_decimal_from_public_payload(
            "source_contradiction_score",
            row_payload["source_contradiction_score"],
        ),
        time_to_resolution_minutes=_decimal_from_public_payload(
            "time_to_resolution_minutes",
            row_payload["time_to_resolution_minutes"],
        ),
        priority_score=_decimal_from_public_payload(
            "priority_score",
            row_payload["priority_score"],
        ),
        priority_tier=row_payload["priority_tier"],
        research_cadence=row_payload["research_cadence"],
        reason_codes=row_payload["reason_codes"],
        paper_only=row_payload["paper_only"],
        report_only=row_payload["report_only"],
        readonly=row_payload["readonly"],
    )


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(payload)
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"{label} missing required fields: {missing}")
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        extra = ", ".join(sorted(extra_keys))
        raise ValueError(f"{label} contains unsupported fields: {extra}")


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    reject_unsafe_surface_fields(label, value)
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface value in {path or label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
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
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _json_ready_public(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_public(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _rank_markets(
    markets: tuple[StrategyMarketNewsVelocityPriorityV10Market, ...],
) -> tuple[StrategyMarketNewsVelocityPriorityV10Market, ...]:
    return tuple(
        sorted(
            markets,
            key=lambda market: (
                -_priority_score(market),
                market.time_to_resolution_minutes,
                market.market_id,
            ),
        ),
    )


def _ranked_rows(
    markets: tuple[StrategyMarketNewsVelocityPriorityV10Market, ...],
) -> tuple[StrategyMarketNewsVelocityPriorityV10Row, ...]:
    rows: list[StrategyMarketNewsVelocityPriorityV10Row] = []
    rank = ZERO
    for market in _rank_markets(markets):
        rank += COUNT_QUANT
        priority_score = _priority_score(market)
        priority_tier = _priority_tier(priority_score)
        rows.append(
            StrategyMarketNewsVelocityPriorityV10Row(
                research_rank=rank,
                market_id=market.market_id,
                market_slug=market.market_slug,
                new_source_count=market.new_source_count,
                high_reliability_source_share=market.high_reliability_source_share,
                probability_move_bps=market.probability_move_bps,
                source_contradiction_score=market.source_contradiction_score,
                time_to_resolution_minutes=market.time_to_resolution_minutes,
                priority_score=priority_score,
                priority_tier=priority_tier,
                research_cadence=_research_cadence(priority_tier),
                reason_codes=_reason_codes(market, priority_tier),
            ),
        )
    return tuple(rows)


def _priority_score(market: StrategyMarketNewsVelocityPriorityV10Market) -> Decimal:
    new_source_score = _ratio_score(
        min(market.new_source_count, NEW_SOURCE_SCORE_CAP),
        NEW_SOURCE_SCORE_CAP,
    )
    probability_move_score = _ratio_score(
        min(market.probability_move_bps, PROBABILITY_MOVE_SCORE_CAP_BPS),
        PROBABILITY_MOVE_SCORE_CAP_BPS,
    )
    score = (
        (new_source_score * Decimal("0.300000"))
        + (market.high_reliability_source_share * ONE_HUNDRED * Decimal("0.200000"))
        + (probability_move_score * Decimal("0.250000"))
        + (market.source_contradiction_score * ONE_HUNDRED * Decimal("0.150000"))
        + (_time_sensitivity_score(market.time_to_resolution_minutes) * Decimal("0.100000"))
    )
    return score.quantize(SCORE_QUANT)


def _ratio_score(value: Decimal, denominator: Decimal) -> Decimal:
    return ((value / denominator) * ONE_HUNDRED).quantize(SCORE_QUANT)


def _time_sensitivity_score(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= IMMEDIATE_RESOLUTION_MINUTES:
        return ONE_HUNDRED
    if time_to_resolution_minutes <= ACCELERATED_RESOLUTION_MINUTES:
        return Decimal("50.000000")
    return ZERO


def _priority_tier(priority_score: Decimal) -> str:
    if priority_score >= Decimal("70.000000"):
        return "research_now"
    if priority_score >= Decimal("35.000000"):
        return "accelerated_recheck"
    return "monitor"


def _research_cadence(priority_tier: str) -> str:
    if priority_tier == "research_now":
        return "now"
    if priority_tier == "accelerated_recheck":
        return "within_60_minutes"
    return "next_cycle"


def _reason_codes(
    market: StrategyMarketNewsVelocityPriorityV10Market,
    priority_tier: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if market.new_source_count >= Decimal("5"):
        codes.append("new_source_count_high")
    elif market.new_source_count > ZERO:
        codes.append("new_source_count_present")
    else:
        codes.append("no_new_sources")

    if market.high_reliability_source_share >= Decimal("0.700000"):
        codes.append("high_reliability_source_share_high")
    elif market.high_reliability_source_share >= Decimal("0.400000"):
        codes.append("high_reliability_source_share_medium")
    else:
        codes.append("high_reliability_source_share_low")

    if market.probability_move_bps >= Decimal("500.000000"):
        codes.append("probability_move_large")
    elif market.probability_move_bps >= Decimal("100.000000"):
        codes.append("probability_move_medium")
    else:
        codes.append("probability_move_small")

    if market.source_contradiction_score >= Decimal("0.600000"):
        codes.append("source_contradiction_high")
    elif market.source_contradiction_score >= Decimal("0.300000"):
        codes.append("source_contradiction_medium")
    else:
        codes.append("source_contradiction_low")

    if market.time_to_resolution_minutes <= IMMEDIATE_RESOLUTION_MINUTES:
        codes.append("time_sensitive_immediate")
    elif market.time_to_resolution_minutes <= ACCELERATED_RESOLUTION_MINUTES:
        codes.append("time_sensitive_accelerated")
    else:
        codes.append("time_sensitive_low")

    codes.append(f"priority_tier_{priority_tier}")
    return _normalize_reason_codes(tuple(codes))


def _validate_row(row: StrategyMarketNewsVelocityPriorityV10Row) -> None:
    market = StrategyMarketNewsVelocityPriorityV10Market(
        market_id=row.market_id,
        market_slug=row.market_slug,
        new_source_count=row.new_source_count,
        high_reliability_source_share=row.high_reliability_source_share,
        probability_move_bps=row.probability_move_bps,
        source_contradiction_score=row.source_contradiction_score,
        time_to_resolution_minutes=row.time_to_resolution_minutes,
    )
    priority_score = _priority_score(market)
    priority_tier = _priority_tier(priority_score)
    if row.priority_score != priority_score:
        raise ValueError("priority_score must match market fields")
    if row.priority_tier != priority_tier:
        raise ValueError("priority_tier must match priority_score")
    if row.research_cadence != _research_cadence(priority_tier):
        raise ValueError("research_cadence must match priority_tier")
    if row.reason_codes != _reason_codes(market, priority_tier):
        raise ValueError("reason_codes must match market fields")


def _validate_report(report: StrategyMarketNewsVelocityPriorityV10Report) -> None:
    if report.market_count != _decimal_count(report.rows):
        raise ValueError("market_count must match rows")
    if report.research_now_count != _decimal_count(
        row for row in report.rows if row.priority_tier == "research_now"
    ):
        raise ValueError("research_now_count must match rows")
    if report.accelerated_recheck_count != _decimal_count(
        row for row in report.rows if row.priority_tier == "accelerated_recheck"
    ):
        raise ValueError("accelerated_recheck_count must match rows")
    top_market_id = report.rows[0].market_id if report.rows else None
    if report.top_market_id != top_market_id:
        raise ValueError("top_market_id must match rows")
    for expected_rank, row in enumerate(report.rows, start=1):
        if row.research_rank != Decimal(str(expected_rank)):
            raise ValueError("research_rank must be sequential")


def _decimal_count(values: object) -> Decimal:
    count = ZERO
    for _value in values:  # type: ignore[union-attr]
        count += COUNT_QUANT
    return count


def _normalize_markets(
    markets: object,
) -> tuple[StrategyMarketNewsVelocityPriorityV10Market, ...]:
    if isinstance(markets, (str, bytes)):
        raise ValueError(
            "markets must contain StrategyMarketNewsVelocityPriorityV10Market values",
        )
    try:
        values = tuple(markets)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "markets must contain StrategyMarketNewsVelocityPriorityV10Market values",
        ) from exc
    for market in values:
        if type(market) is not StrategyMarketNewsVelocityPriorityV10Market:
            raise ValueError(
                "markets must contain StrategyMarketNewsVelocityPriorityV10Market values",
            )
        reject_unsafe_surface_fields("market news velocity priority market", market)
        require_paper_only_flags("market news velocity priority market", market)
    return values


def _normalize_rows(
    rows: object,
) -> tuple[StrategyMarketNewsVelocityPriorityV10Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain StrategyMarketNewsVelocityPriorityV10Row values")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain StrategyMarketNewsVelocityPriorityV10Row values",
        ) from exc
    for row in values:
        if type(row) is not StrategyMarketNewsVelocityPriorityV10Row:
            raise ValueError(
                "rows must contain StrategyMarketNewsVelocityPriorityV10Row values",
            )
    return values


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE_HUNDRED:
        raise ValueError(f"{field_name} must be between 0.000000 and 100.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(SCORE_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


__all__ = (
    "PRIORITY_TIERS",
    "REASON_CODES",
    "StrategyMarketNewsVelocityPriorityV10Market",
    "StrategyMarketNewsVelocityPriorityV10Row",
    "StrategyMarketNewsVelocityPriorityV10Report",
    "build_strategy_market_news_velocity_priority_v10",
    "strategy_market_news_velocity_priority_v10_payload",
)
