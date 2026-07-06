"""Pure typed market rule change watch v9 report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-market-rule-change-watch-v9"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")

SOURCE_TIERS = (
    "official_rules",
    "exchange_polymarket_page",
    "primary_data_source",
    "secondary_news",
    "social_rumor",
)
TIER_RANK = {source_tier: rank for rank, source_tier in enumerate(SOURCE_TIERS)}

RULE_CHANGE_STATUSES = ("unchanged", "watch", "blocked")
REQUIRED_RESEARCH_ACTIONS = (
    "no_action",
    "refresh_market_rule_research",
    "escalate_rule_change_review",
)
STATUS_ACTIONS = {
    "unchanged": "no_action",
    "watch": "refresh_market_rule_research",
    "blocked": "escalate_rule_change_review",
}
STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "unchanged": 2}

EMPTY_REASON_CODE = "market_rule_change_watch_empty"
UNCHANGED_REASON_CODE = "market_rule_change_watch_unchanged"
REASON_CODES = tuple(
    sorted(
        (
            EMPTY_REASON_CODE,
            UNCHANGED_REASON_CODE,
            "resolution_rules_changed",
            "market_description_changed",
            "source_hierarchy_changed",
            "source_hierarchy_strengthened",
            "source_hierarchy_weakened",
            "close_time_changed",
            "close_time_moved_earlier",
            "close_time_moved_later",
            "dispute_indicators_changed",
            "dispute_indicators_added",
            "dispute_indicators_removed",
        ),
    ),
)


@dataclass(frozen=True)
class StrategyMarketRuleChangeWatchV9Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    material_close_time_change_seconds: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyMarketRuleChangeWatchV9Config:
            raise TypeError("StrategyMarketRuleChangeWatchV9Config does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketRuleChangeWatchV9Config, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "material_close_time_change_seconds",
            _require_nonnegative_decimal(
                "material_close_time_change_seconds",
                self.material_close_time_change_seconds,
            ),
        )
        reject_unsafe_surface_fields("strategy market rule change watch v9 config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketRuleChangeWatchV9Input:
    market_slug: str
    previous_resolution_rules: str
    current_resolution_rules: str
    previous_market_description: str
    current_market_description: str
    previous_best_source_tier: str
    current_best_source_tier: str
    previous_close_time: datetime
    current_close_time: datetime
    previous_dispute_indicators: tuple[str, ...]
    current_dispute_indicators: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyMarketRuleChangeWatchV9Input:
            raise TypeError("StrategyMarketRuleChangeWatchV9Input does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketRuleChangeWatchV9Input, "input")
        for field_name in (
            "market_slug",
            "previous_resolution_rules",
            "current_resolution_rules",
            "previous_market_description",
            "current_market_description",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_source_tier("previous_best_source_tier", self.previous_best_source_tier)
        _require_source_tier("current_best_source_tier", self.current_best_source_tier)
        object.__setattr__(
            self,
            "previous_close_time",
            _as_utc("previous_close_time", self.previous_close_time),
        )
        object.__setattr__(
            self,
            "current_close_time",
            _as_utc("current_close_time", self.current_close_time),
        )
        object.__setattr__(
            self,
            "previous_dispute_indicators",
            _normalize_dispute_indicators(
                "previous_dispute_indicators",
                self.previous_dispute_indicators,
            ),
        )
        object.__setattr__(
            self,
            "current_dispute_indicators",
            _normalize_dispute_indicators(
                "current_dispute_indicators",
                self.current_dispute_indicators,
            ),
        )
        reject_unsafe_surface_fields("strategy market rule change watch v9 input", self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketRuleChangeWatchV9Row:
    market_slug: str
    previous_resolution_rules: str
    current_resolution_rules: str
    previous_market_description: str
    current_market_description: str
    previous_best_source_tier: str
    current_best_source_tier: str
    previous_close_time: datetime
    current_close_time: datetime
    previous_dispute_indicators: tuple[str, ...]
    current_dispute_indicators: tuple[str, ...]
    resolution_rules_changed: bool
    market_description_changed: bool
    source_hierarchy_changed: bool
    close_time_changed: bool
    dispute_indicators_changed: bool
    close_time_delta_seconds: Decimal
    change_signal_count: Decimal
    rule_change_status: str
    required_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyMarketRuleChangeWatchV9Row:
            raise TypeError("StrategyMarketRuleChangeWatchV9Row does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketRuleChangeWatchV9Row, "row")
        for field_name in (
            "market_slug",
            "previous_resolution_rules",
            "current_resolution_rules",
            "previous_market_description",
            "current_market_description",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_source_tier("previous_best_source_tier", self.previous_best_source_tier)
        _require_source_tier("current_best_source_tier", self.current_best_source_tier)
        object.__setattr__(
            self,
            "previous_close_time",
            _as_utc("previous_close_time", self.previous_close_time),
        )
        object.__setattr__(
            self,
            "current_close_time",
            _as_utc("current_close_time", self.current_close_time),
        )
        object.__setattr__(
            self,
            "previous_dispute_indicators",
            _normalize_dispute_indicators(
                "previous_dispute_indicators",
                self.previous_dispute_indicators,
            ),
        )
        object.__setattr__(
            self,
            "current_dispute_indicators",
            _normalize_dispute_indicators(
                "current_dispute_indicators",
                self.current_dispute_indicators,
            ),
        )
        for field_name in (
            "resolution_rules_changed",
            "market_description_changed",
            "source_hierarchy_changed",
            "close_time_changed",
            "dispute_indicators_changed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "close_time_delta_seconds",
            _require_decimal("close_time_delta_seconds", self.close_time_delta_seconds),
        )
        object.__setattr__(
            self,
            "change_signal_count",
            _require_nonnegative_whole_decimal("change_signal_count", self.change_signal_count),
        )
        _require_rule_change_status("rule_change_status", self.rule_change_status)
        _require_research_action("required_research_action", self.required_research_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class StrategyMarketRuleChangeWatchV9Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    unchanged_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    rule_change_status: str
    required_research_action: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMarketRuleChangeWatchV9Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyMarketRuleChangeWatchV9Report:
            raise TypeError("StrategyMarketRuleChangeWatchV9Report does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketRuleChangeWatchV9Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("market_count", "unchanged_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_rule_change_status("rule_change_status", self.rule_change_status)
        _require_research_action("required_research_action", self.required_research_action)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)


def build_strategy_market_rule_change_watch_v9_report(
    markets: Iterable[object],
    *,
    config: StrategyMarketRuleChangeWatchV9Config,
    generated_at: datetime,
) -> StrategyMarketRuleChangeWatchV9Report:
    if type(config) is not StrategyMarketRuleChangeWatchV9Config:
        raise ValueError("config must be a StrategyMarketRuleChangeWatchV9Config")
    require_paper_only_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_input(input_row, config=config) for input_row in _normalize_inputs(markets)),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    return StrategyMarketRuleChangeWatchV9Report(
        generated_at=generated_at,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        unchanged_count=_status_count(rows, "unchanged"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        rule_change_status=report_status,
        required_research_action=STATUS_ACTIONS[report_status],
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_market_rule_change_watch_v9_report_payload(
    report: StrategyMarketRuleChangeWatchV9Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketRuleChangeWatchV9Report:
        raise ValueError("report must be a StrategyMarketRuleChangeWatchV9Report")
    return json_ready_no_floats(report)


def _row_from_input(
    input_row: StrategyMarketRuleChangeWatchV9Input,
    *,
    config: StrategyMarketRuleChangeWatchV9Config,
) -> StrategyMarketRuleChangeWatchV9Row:
    close_time_delta_seconds = _close_time_delta_seconds(
        input_row.previous_close_time,
        input_row.current_close_time,
    )
    close_time_changed = _close_time_changed(
        close_time_delta_seconds,
        config.material_close_time_change_seconds,
    )
    reason_codes = _row_reason_codes(
        previous_resolution_rules=input_row.previous_resolution_rules,
        current_resolution_rules=input_row.current_resolution_rules,
        previous_market_description=input_row.previous_market_description,
        current_market_description=input_row.current_market_description,
        previous_best_source_tier=input_row.previous_best_source_tier,
        current_best_source_tier=input_row.current_best_source_tier,
        close_time_delta_seconds=close_time_delta_seconds,
        close_time_changed=close_time_changed,
        previous_dispute_indicators=input_row.previous_dispute_indicators,
        current_dispute_indicators=input_row.current_dispute_indicators,
    )
    rule_change_status = _rule_change_status_from_reason_codes(reason_codes)
    return StrategyMarketRuleChangeWatchV9Row(
        market_slug=input_row.market_slug,
        previous_resolution_rules=input_row.previous_resolution_rules,
        current_resolution_rules=input_row.current_resolution_rules,
        previous_market_description=input_row.previous_market_description,
        current_market_description=input_row.current_market_description,
        previous_best_source_tier=input_row.previous_best_source_tier,
        current_best_source_tier=input_row.current_best_source_tier,
        previous_close_time=input_row.previous_close_time,
        current_close_time=input_row.current_close_time,
        previous_dispute_indicators=input_row.previous_dispute_indicators,
        current_dispute_indicators=input_row.current_dispute_indicators,
        resolution_rules_changed=input_row.previous_resolution_rules != input_row.current_resolution_rules,
        market_description_changed=(
            input_row.previous_market_description != input_row.current_market_description
        ),
        source_hierarchy_changed=input_row.previous_best_source_tier != input_row.current_best_source_tier,
        close_time_changed=close_time_changed,
        dispute_indicators_changed=(
            input_row.previous_dispute_indicators != input_row.current_dispute_indicators
        ),
        close_time_delta_seconds=close_time_delta_seconds,
        change_signal_count=_decimal_count(_change_signal_count_from_reason_codes(reason_codes)),
        rule_change_status=rule_change_status,
        required_research_action=STATUS_ACTIONS[rule_change_status],
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    markets: Iterable[object],
) -> tuple[StrategyMarketRuleChangeWatchV9Input, ...]:
    if isinstance(markets, (str, bytes)):
        raise ValueError("markets must be an iterable")
    try:
        items = tuple(markets)
    except TypeError as exc:
        raise ValueError("markets must be an iterable") from exc
    return tuple(_input_from_supplied_shape(item) for item in items)


def _input_from_supplied_shape(item: object) -> StrategyMarketRuleChangeWatchV9Input:
    if type(item) is StrategyMarketRuleChangeWatchV9Input:
        reject_unsafe_surface_fields("strategy market rule change watch v9 input", item)
        require_paper_only_flags("input", item)
        return item
    reject_unsafe_surface_fields("strategy market rule change watch v9 input", item)
    require_paper_only_flags("input", item)
    return StrategyMarketRuleChangeWatchV9Input(
        market_slug=_required_attr(item, "market_slug"),
        previous_resolution_rules=_required_attr(item, "previous_resolution_rules"),
        current_resolution_rules=_required_attr(item, "current_resolution_rules"),
        previous_market_description=_required_attr(item, "previous_market_description"),
        current_market_description=_required_attr(item, "current_market_description"),
        previous_best_source_tier=_required_attr(item, "previous_best_source_tier"),
        current_best_source_tier=_required_attr(item, "current_best_source_tier"),
        previous_close_time=_required_attr(item, "previous_close_time"),
        current_close_time=_required_attr(item, "current_close_time"),
        previous_dispute_indicators=_required_attr(item, "previous_dispute_indicators"),
        current_dispute_indicators=_required_attr(item, "current_dispute_indicators"),
    )


def _normalize_rows(
    rows: Iterable[StrategyMarketRuleChangeWatchV9Row],
) -> tuple[StrategyMarketRuleChangeWatchV9Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not StrategyMarketRuleChangeWatchV9Row:
            raise ValueError("rows must contain StrategyMarketRuleChangeWatchV9Row values")
        require_paper_only_flags("row", row)
    return items


def _row_reason_codes(
    *,
    previous_resolution_rules: str,
    current_resolution_rules: str,
    previous_market_description: str,
    current_market_description: str,
    previous_best_source_tier: str,
    current_best_source_tier: str,
    close_time_delta_seconds: Decimal,
    close_time_changed: bool,
    previous_dispute_indicators: tuple[str, ...],
    current_dispute_indicators: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if previous_resolution_rules != current_resolution_rules:
        reason_codes.add("resolution_rules_changed")
    if previous_market_description != current_market_description:
        reason_codes.add("market_description_changed")
    if previous_best_source_tier != current_best_source_tier:
        reason_codes.add("source_hierarchy_changed")
        if TIER_RANK[current_best_source_tier] < TIER_RANK[previous_best_source_tier]:
            reason_codes.add("source_hierarchy_strengthened")
        else:
            reason_codes.add("source_hierarchy_weakened")
    if close_time_changed:
        reason_codes.add("close_time_changed")
        if close_time_delta_seconds < ZERO:
            reason_codes.add("close_time_moved_earlier")
        else:
            reason_codes.add("close_time_moved_later")
    if previous_dispute_indicators != current_dispute_indicators:
        reason_codes.add("dispute_indicators_changed")
        previous = set(previous_dispute_indicators)
        current = set(current_dispute_indicators)
        if current - previous:
            reason_codes.add("dispute_indicators_added")
        if previous - current:
            reason_codes.add("dispute_indicators_removed")
    if not reason_codes:
        return (UNCHANGED_REASON_CODE,)
    return tuple(sorted(reason_codes))


def _change_signal_count_from_reason_codes(reason_codes: tuple[str, ...]) -> int:
    if reason_codes == (UNCHANGED_REASON_CODE,):
        return 0
    return sum(
        1
        for reason_code in (
            "resolution_rules_changed",
            "market_description_changed",
            "source_hierarchy_changed",
            "close_time_changed",
            "dispute_indicators_changed",
        )
        if reason_code in reason_codes
    )


def _rule_change_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (UNCHANGED_REASON_CODE,):
        return "unchanged"
    if any(
        reason_code in reason_codes
        for reason_code in (
            "resolution_rules_changed",
            "source_hierarchy_weakened",
            "close_time_changed",
            "dispute_indicators_changed",
        )
    ):
        return "blocked"
    return "watch"


def _close_time_delta_seconds(previous_close_time: datetime, current_close_time: datetime) -> Decimal:
    delta = current_close_time - previous_close_time
    total_microseconds = (
        (delta.days * 86_400 + delta.seconds) * 1_000_000
        + delta.microseconds
    )
    return (Decimal(total_microseconds) / Decimal("1000000")).quantize(QUANT)


def _close_time_changed(
    close_time_delta_seconds: Decimal,
    material_close_time_change_seconds: Decimal,
) -> bool:
    absolute_delta = abs(close_time_delta_seconds)
    return absolute_delta > ZERO and absolute_delta >= material_close_time_change_seconds


def _status_count(rows: tuple[StrategyMarketRuleChangeWatchV9Row, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.rule_change_status == status))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _report_status(rows: tuple[StrategyMarketRuleChangeWatchV9Row, ...]) -> str:
    if any(row.rule_change_status == "blocked" for row in rows):
        return "blocked"
    if any(row.rule_change_status == "watch" for row in rows):
        return "watch"
    return "unchanged"


def _report_reason_codes(rows: tuple[StrategyMarketRuleChangeWatchV9Row, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _row_sort_key(row: StrategyMarketRuleChangeWatchV9Row) -> tuple[int, str]:
    return STATUS_SORT_PRIORITY[row.rule_change_status], row.market_slug


def _validate_row_consistency(row: StrategyMarketRuleChangeWatchV9Row) -> None:
    if row.resolution_rules_changed != (row.previous_resolution_rules != row.current_resolution_rules):
        raise ValueError("resolution_rules_changed must match resolution rules")
    if row.market_description_changed != (
        row.previous_market_description != row.current_market_description
    ):
        raise ValueError("market_description_changed must match market description")
    if row.source_hierarchy_changed != (
        row.previous_best_source_tier != row.current_best_source_tier
    ):
        raise ValueError("source_hierarchy_changed must match source hierarchy")
    if row.dispute_indicators_changed != (
        row.previous_dispute_indicators != row.current_dispute_indicators
    ):
        raise ValueError("dispute_indicators_changed must match dispute indicators")
    if row.close_time_delta_seconds != _close_time_delta_seconds(
        row.previous_close_time,
        row.current_close_time,
    ):
        raise ValueError("close_time_delta_seconds must match close time")
    if row.close_time_changed and row.close_time_delta_seconds == ZERO:
        raise ValueError("close_time_changed must have a nonzero close_time_delta_seconds")
    expected_signal_count = _decimal_count(
        sum(
            1
            for value in (
                row.resolution_rules_changed,
                row.market_description_changed,
                row.source_hierarchy_changed,
                row.close_time_changed,
                row.dispute_indicators_changed,
            )
            if value
        ),
    )
    if row.change_signal_count != expected_signal_count:
        raise ValueError("change_signal_count must match changed fields")
    expected_reason_codes = _row_reason_codes(
        previous_resolution_rules=row.previous_resolution_rules,
        current_resolution_rules=row.current_resolution_rules,
        previous_market_description=row.previous_market_description,
        current_market_description=row.current_market_description,
        previous_best_source_tier=row.previous_best_source_tier,
        current_best_source_tier=row.current_best_source_tier,
        close_time_delta_seconds=row.close_time_delta_seconds,
        close_time_changed=row.close_time_changed,
        previous_dispute_indicators=row.previous_dispute_indicators,
        current_dispute_indicators=row.current_dispute_indicators,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match changed fields")
    expected_status = _rule_change_status_from_reason_codes(row.reason_codes)
    if row.rule_change_status != expected_status:
        raise ValueError("rule_change_status must match reason_codes")
    if row.required_research_action != STATUS_ACTIONS[row.rule_change_status]:
        raise ValueError("required_research_action must match rule_change_status")


def _validate_report_consistency(report: StrategyMarketRuleChangeWatchV9Report) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.unchanged_count != _status_count(report.rows, "unchanged"):
        raise ValueError("unchanged_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.market_count != report.unchanged_count + report.watch_count + report.blocked_count:
        raise ValueError("market_count must match status counts")
    expected_report_status = _report_status(report.rows)
    if report.rule_change_status != expected_report_status:
        raise ValueError("rule_change_status must match rows")
    if report.required_research_action != STATUS_ACTIONS[report.rule_change_status]:
        raise ValueError("required_research_action must match rule_change_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    market_slugs = tuple(row.market_slug for row in report.rows)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("rows must contain unique market_slug values")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_source_tier(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_TIERS:
        raise ValueError(f"{field_name} must be a known source tier")


def _require_rule_change_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RULE_CHANGE_STATUSES:
        raise ValueError(f"{field_name} must be unchanged, watch, or blocked")


def _require_research_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REQUIRED_RESEARCH_ACTIONS:
        raise ValueError(f"{field_name} must be a known required research action")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_dispute_indicators(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    indicators = tuple(value)
    for indicator in indicators:
        _require_canonical_string(field_name, indicator)
    if len(set(indicators)) != len(indicators):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(indicators))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "REASON_CODES",
    "REQUIRED_RESEARCH_ACTIONS",
    "RULE_CHANGE_STATUSES",
    "SOURCE_TIERS",
    "StrategyMarketRuleChangeWatchV9Config",
    "StrategyMarketRuleChangeWatchV9Input",
    "StrategyMarketRuleChangeWatchV9Report",
    "StrategyMarketRuleChangeWatchV9Row",
    "build_strategy_market_rule_change_watch_v9_report",
    "strategy_market_rule_change_watch_v9_report_payload",
)
