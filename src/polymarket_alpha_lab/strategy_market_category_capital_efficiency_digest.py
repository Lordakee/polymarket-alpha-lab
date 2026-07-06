"""Paper-only market category capital efficiency digest."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_MARKET_CATEGORY_CAPITAL_EFFICIENCY_DIGEST_CONFIG_VERSION = (
    "strategy-market-category-capital-efficiency-digest-v0"
)
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
DAYS_PER_YEAR = Decimal("365")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_REASON_CODES = (
    "positive_net_edge",
    "capital_efficiency_pass",
    "capital_efficiency_watch",
    "capital_efficiency_blocked",
    "fee_drag_exceeds_edge",
    "holding_period_extended",
    "forecast_confidence_low",
    "liquidity_capacity_exhausted",
    "unresolved_exposure_high",
    "learning_value_high",
)
EMPTY_REASON_CODE = "strategy_market_category_capital_efficiency_digest_empty"
REPORT_REASON_CODES = tuple(sorted((*ROW_REASON_CODES, EMPTY_REASON_CODE)))
SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "token=",
    "api_key=",
    "secret",
    "private",
    "wallet:",
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
    "broker",
    "database",
    "live_trading",
    "network",
    "persist",
    "trade",
)


@dataclass(frozen=True)
class StrategyMarketCategoryCapitalEfficiencyDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_MARKET_CATEGORY_CAPITAL_EFFICIENCY_DIGEST_CONFIG_VERSION
    )
    target_liquidity_capacity: Decimal = Decimal("1000.000000")
    pass_efficiency_score: Decimal = Decimal("0.050000")
    watch_efficiency_score: Decimal = Decimal("0.010000")
    max_holding_period_days: Decimal = Decimal("30")
    low_forecast_confidence: Decimal = Decimal("0.500000")
    high_unresolved_exposure_ratio: Decimal = Decimal("0.750000")
    high_learning_value: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_liquidity_capacity",
            _normalize_positive_value(
                "target_liquidity_capacity",
                self.target_liquidity_capacity,
            ),
        )
        for field_name in ("pass_efficiency_score", "watch_efficiency_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        if self.pass_efficiency_score < self.watch_efficiency_score:
            raise ValueError("pass_efficiency_score must be at least watch_efficiency_score")
        object.__setattr__(
            self,
            "max_holding_period_days",
            _normalize_positive_days(
                "max_holding_period_days",
                self.max_holding_period_days,
            ),
        )
        for field_name in (
            "low_forecast_confidence",
            "high_unresolved_exposure_ratio",
            "high_learning_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketCategoryCapitalEfficiencyInput:
    category: str
    expected_edge: Decimal
    holding_period_days: Decimal
    fee_drag: Decimal
    liquidity_capacity: Decimal
    forecast_confidence: Decimal
    unresolved_exposure: Decimal
    learning_value: Decimal
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "expected_edge",
            _normalize_value("expected_edge", self.expected_edge),
        )
        object.__setattr__(
            self,
            "holding_period_days",
            _normalize_positive_days("holding_period_days", self.holding_period_days),
        )
        for field_name in ("fee_drag", "liquidity_capacity", "unresolved_exposure"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in ("forecast_confidence", "learning_value"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_canonical_string("source_reference", self.source_reference)
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketCategoryCapitalEfficiencyDigestRow:
    rank: Decimal
    category: str
    expected_edge: Decimal
    holding_period_days: Decimal
    fee_drag: Decimal
    net_expected_edge: Decimal
    liquidity_capacity: Decimal
    unresolved_exposure: Decimal
    available_liquidity_capacity: Decimal
    liquidity_capacity_score: Decimal
    forecast_confidence: Decimal
    learning_value: Decimal
    annualized_net_edge: Decimal
    confidence_adjusted_edge: Decimal
    learning_adjusted_edge: Decimal
    efficiency_score: Decimal
    capital_efficiency_status: str
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category", self.category)
        for field_name in (
            "expected_edge",
            "net_expected_edge",
            "annualized_net_edge",
            "confidence_adjusted_edge",
            "learning_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "holding_period_days",
            _normalize_positive_days("holding_period_days", self.holding_period_days),
        )
        for field_name in (
            "fee_drag",
            "liquidity_capacity",
            "unresolved_exposure",
            "available_liquidity_capacity",
            "efficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_capacity_score",
            "forecast_confidence",
            "learning_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("capital_efficiency_status", self.capital_efficiency_status, STATUSES)
        _require_canonical_string(
            "redacted_source_reference",
            self.redacted_source_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _row_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_row(self)
        _require_paper_flags("row", self)


@dataclass(frozen=True)
class StrategyMarketCategoryCapitalEfficiencyDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    top_category: str | None
    max_efficiency_score: Decimal
    min_efficiency_score: Decimal
    average_efficiency_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.top_category is not None:
            _require_canonical_string("top_category", self.top_category)
        for field_name in (
            "max_efficiency_score",
            "min_efficiency_score",
            "average_efficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _report_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_report(self)
        _require_paper_flags("report", self)


def build_strategy_market_category_capital_efficiency_digest(
    categories: Iterable[StrategyMarketCategoryCapitalEfficiencyInput],
    *,
    config: StrategyMarketCategoryCapitalEfficiencyDigestConfig,
    generated_at: datetime,
) -> StrategyMarketCategoryCapitalEfficiencyDigestReport:
    if type(config) is not StrategyMarketCategoryCapitalEfficiencyDigestConfig:
        raise ValueError(
            "config must be a StrategyMarketCategoryCapitalEfficiencyDigestConfig",
        )
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(categories)
    ranked_rows = _rank_rows(
        tuple(_unranked_row(row, config) for row in source_rows),
    )
    reason_codes = _report_reason_codes(ranked_rows)

    return StrategyMarketCategoryCapitalEfficiencyDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(ranked_rows)),
        pass_count=_count(_status_count(ranked_rows, PASS_STATUS)),
        watch_count=_count(_status_count(ranked_rows, WATCH_STATUS)),
        blocked_count=_count(_status_count(ranked_rows, BLOCKED_STATUS)),
        top_category=ranked_rows[0].category if ranked_rows else None,
        max_efficiency_score=_max_efficiency_score(ranked_rows),
        min_efficiency_score=_min_efficiency_score(ranked_rows),
        average_efficiency_score=_average_efficiency_score(ranked_rows),
        digest_status=_digest_status(ranked_rows),
        reason_codes=reason_codes,
        rows=ranked_rows,
    )


def strategy_market_category_capital_efficiency_digest_payload(
    report: StrategyMarketCategoryCapitalEfficiencyDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyMarketCategoryCapitalEfficiencyDigestReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        validate_strategy_market_category_capital_efficiency_digest_public_payload(
            payload,
        )
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_paper_flags("payload", _DictFlags(payload))
        validate_strategy_market_category_capital_efficiency_digest_public_payload(
            payload,
        )
        return payload
    raise ValueError(
        "report must be a StrategyMarketCategoryCapitalEfficiencyDigestReport",
    )


def validate_strategy_market_category_capital_efficiency_digest_public_payload(
    payload: object,
) -> None:
    _reject_unsafe_surface_fields("payload", payload)
    _require_safe_public_payload("payload", payload)


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


def _unranked_row(
    row: StrategyMarketCategoryCapitalEfficiencyInput,
    config: StrategyMarketCategoryCapitalEfficiencyDigestConfig,
) -> StrategyMarketCategoryCapitalEfficiencyDigestRow:
    net_expected_edge = _q(row.expected_edge - row.fee_drag)
    available_liquidity_capacity = _q(
        max(row.liquidity_capacity - row.unresolved_exposure, ZERO),
    )
    liquidity_capacity_score = _ratio(
        min(available_liquidity_capacity, config.target_liquidity_capacity),
        config.target_liquidity_capacity,
    )
    annualized_net_edge = _q(
        max(net_expected_edge, ZERO) * DAYS_PER_YEAR / row.holding_period_days,
    )
    confidence_adjusted_edge = _q(annualized_net_edge * row.forecast_confidence)
    learning_adjusted_edge = _q(confidence_adjusted_edge * (ONE + row.learning_value))
    efficiency_score = _q(learning_adjusted_edge * liquidity_capacity_score)
    status = _row_status(
        net_expected_edge=net_expected_edge,
        liquidity_capacity_score=liquidity_capacity_score,
        efficiency_score=efficiency_score,
        config=config,
    )
    return StrategyMarketCategoryCapitalEfficiencyDigestRow(
        rank=Decimal("1"),
        category=row.category,
        expected_edge=row.expected_edge,
        holding_period_days=row.holding_period_days,
        fee_drag=row.fee_drag,
        net_expected_edge=net_expected_edge,
        liquidity_capacity=row.liquidity_capacity,
        unresolved_exposure=row.unresolved_exposure,
        available_liquidity_capacity=available_liquidity_capacity,
        liquidity_capacity_score=liquidity_capacity_score,
        forecast_confidence=row.forecast_confidence,
        learning_value=row.learning_value,
        annualized_net_edge=annualized_net_edge,
        confidence_adjusted_edge=confidence_adjusted_edge,
        learning_adjusted_edge=learning_adjusted_edge,
        efficiency_score=efficiency_score,
        capital_efficiency_status=status,
        redacted_source_reference=_redact_source_reference(row.source_reference),
        reason_codes=_row_reason_codes(
            row,
            net_expected_edge=net_expected_edge,
            liquidity_capacity_score=liquidity_capacity_score,
            status=status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.efficiency_score,
            _status_sort_value(row.capital_efficiency_status),
            row.category,
        ),
    )
    return tuple(
        StrategyMarketCategoryCapitalEfficiencyDigestRow(
            rank=_count(index),
            category=row.category,
            expected_edge=row.expected_edge,
            holding_period_days=row.holding_period_days,
            fee_drag=row.fee_drag,
            net_expected_edge=row.net_expected_edge,
            liquidity_capacity=row.liquidity_capacity,
            unresolved_exposure=row.unresolved_exposure,
            available_liquidity_capacity=row.available_liquidity_capacity,
            liquidity_capacity_score=row.liquidity_capacity_score,
            forecast_confidence=row.forecast_confidence,
            learning_value=row.learning_value,
            annualized_net_edge=row.annualized_net_edge,
            confidence_adjusted_edge=row.confidence_adjusted_edge,
            learning_adjusted_edge=row.learning_adjusted_edge,
            efficiency_score=row.efficiency_score,
            capital_efficiency_status=row.capital_efficiency_status,
            redacted_source_reference=row.redacted_source_reference,
            reason_codes=row.reason_codes,
            derived_validation_digest="",
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_status(
    *,
    net_expected_edge: Decimal,
    liquidity_capacity_score: Decimal,
    efficiency_score: Decimal,
    config: StrategyMarketCategoryCapitalEfficiencyDigestConfig,
) -> str:
    if net_expected_edge <= ZERO or liquidity_capacity_score <= ZERO:
        return BLOCKED_STATUS
    if efficiency_score >= config.pass_efficiency_score:
        return PASS_STATUS
    if efficiency_score >= config.watch_efficiency_score:
        return WATCH_STATUS
    return BLOCKED_STATUS


def _row_reason_codes(
    row: StrategyMarketCategoryCapitalEfficiencyInput,
    *,
    net_expected_edge: Decimal,
    liquidity_capacity_score: Decimal,
    status: str,
    config: StrategyMarketCategoryCapitalEfficiencyDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if net_expected_edge > ZERO:
        reason_codes.append("positive_net_edge")
    else:
        reason_codes.append("fee_drag_exceeds_edge")
    if row.holding_period_days > config.max_holding_period_days:
        reason_codes.append("holding_period_extended")
    if row.forecast_confidence < config.low_forecast_confidence:
        reason_codes.append("forecast_confidence_low")
    if liquidity_capacity_score <= ZERO:
        reason_codes.append("liquidity_capacity_exhausted")
    if _ratio(row.unresolved_exposure, row.liquidity_capacity) >= (
        config.high_unresolved_exposure_ratio
    ):
        reason_codes.append("unresolved_exposure_high")
    if row.learning_value >= config.high_learning_value and status != BLOCKED_STATUS:
        reason_codes.append("learning_value_high")
    if status == PASS_STATUS:
        reason_codes.append("capital_efficiency_pass")
    elif status == WATCH_STATUS:
        reason_codes.append("capital_efficiency_watch")
    elif not reason_codes:
        reason_codes.append("capital_efficiency_blocked")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _digest_status(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> str:
    if not rows:
        return BLOCKED_STATUS
    if all(row.capital_efficiency_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.capital_efficiency_status != PASS_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.capital_efficiency_status == status)


def _max_efficiency_score(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(max(row.efficiency_score for row in rows))


def _min_efficiency_score(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(min(row.efficiency_score for row in rows))


def _average_efficiency_score(
    rows: tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(sum(row.efficiency_score for row in rows) / Decimal(len(rows)))


def _validate_row(row: StrategyMarketCategoryCapitalEfficiencyDigestRow) -> None:
    if row.net_expected_edge != _q(row.expected_edge - row.fee_drag):
        raise ValueError("net_expected_edge must match expected_edge less fee_drag")
    if row.available_liquidity_capacity != _q(
        max(row.liquidity_capacity - row.unresolved_exposure, ZERO),
    ):
        raise ValueError("available_liquidity_capacity must match category inputs")
    if row.efficiency_score != _q(row.learning_adjusted_edge * row.liquidity_capacity_score):
        raise ValueError("efficiency_score must match adjusted edge and capacity score")
    expected_digest = _row_derived_validation_digest(row)
    if row.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyMarketCategoryCapitalEfficiencyDigestReport) -> None:
    for row in report.rows:
        _require_paper_flags("row", row)
        _validate_row(row)
    if report.category_count != _count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(_status_count(report.rows, BLOCKED_STATUS)):
        raise ValueError("blocked_count must match rows")
    expected_top_category = report.rows[0].category if report.rows else None
    if report.top_category != expected_top_category:
        raise ValueError("top_category must match highest-ranked row")
    if report.max_efficiency_score != _max_efficiency_score(report.rows):
        raise ValueError("max_efficiency_score must match rows")
    if report.min_efficiency_score != _min_efficiency_score(report.rows):
        raise ValueError("min_efficiency_score must match rows")
    if report.average_efficiency_score != _average_efficiency_score(report.rows):
        raise ValueError("average_efficiency_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_digest = _report_derived_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_inputs(
    value: Iterable[StrategyMarketCategoryCapitalEfficiencyInput],
) -> tuple[StrategyMarketCategoryCapitalEfficiencyInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("categories must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("categories must be an iterable") from exc
    categories: set[str] = set()
    for row in rows:
        if type(row) is not StrategyMarketCategoryCapitalEfficiencyInput:
            raise ValueError("categories must contain exact input rows")
        _require_paper_flags("input", row)
        if row.category in categories:
            raise ValueError("categories must be unique")
        categories.add(row.category)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyMarketCategoryCapitalEfficiencyDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("digest report rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyMarketCategoryCapitalEfficiencyDigestRow:
            raise ValueError("digest report must contain exact rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if tuple(rows) != tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.efficiency_score,
                _status_sort_value(row.capital_efficiency_status),
                row.category,
            ),
        ),
    ):
        raise ValueError("rows must be sorted by efficiency score and category")
    return rows


def _status_sort_value(status: str) -> Decimal:
    return {
        PASS_STATUS: Decimal("0"),
        WATCH_STATUS: Decimal("1"),
        BLOCKED_STATUS: Decimal("2"),
    }[status]


def _redact_source_reference(source_reference: str) -> str:
    lowered = source_reference.lower()
    if any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS):
        return "<redacted>"
    return source_reference


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_surface_fields(label, payload)
    _reject_payload_values(label, payload)


def _reject_unsafe_surface_fields(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_surface_fields(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_surface_fields(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_surface_fields(label, item)


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is str:
        normalized = value.lower()
        if any(marker in normalized for marker in SENSITIVE_REFERENCE_MARKERS):
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)


def _require_safe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None:
        return
    if type(value) is bool:
        return
    if type(value) is str:
        normalized = value.lower()
        if any(marker in normalized for marker in SENSITIVE_REFERENCE_MARKERS):
            raise ValueError(f"{path or label} has unsafe value")
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) in (Decimal, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    raise ValueError(f"{path or label} contains unsupported value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
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
        return {
            key: _json_ready(nested_value)
            for key, nested_value in asdict(value).items()
            if key != "source_reference"
        }
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_value(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _q(value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be at least zero")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_positive_days(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be at least zero")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unknown reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _row_derived_validation_digest(
    row: StrategyMarketCategoryCapitalEfficiencyDigestRow,
) -> str:
    return _sha256(
        (
            "strategy_market_category_capital_efficiency_digest_row",
            f"rank={row.rank}",
            f"category={row.category}",
            f"expected_edge={row.expected_edge}",
            f"holding_period_days={row.holding_period_days}",
            f"fee_drag={row.fee_drag}",
            f"net_expected_edge={row.net_expected_edge}",
            f"liquidity_capacity={row.liquidity_capacity}",
            f"unresolved_exposure={row.unresolved_exposure}",
            f"available_liquidity_capacity={row.available_liquidity_capacity}",
            f"liquidity_capacity_score={row.liquidity_capacity_score}",
            f"forecast_confidence={row.forecast_confidence}",
            f"learning_value={row.learning_value}",
            f"annualized_net_edge={row.annualized_net_edge}",
            f"confidence_adjusted_edge={row.confidence_adjusted_edge}",
            f"learning_adjusted_edge={row.learning_adjusted_edge}",
            f"efficiency_score={row.efficiency_score}",
            f"capital_efficiency_status={row.capital_efficiency_status}",
            f"redacted_source_reference={row.redacted_source_reference}",
            f"reason_codes={','.join(row.reason_codes)}",
            f"paper_only={row.paper_only}",
            f"report_only={row.report_only}",
            f"readonly={row.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: StrategyMarketCategoryCapitalEfficiencyDigestReport,
) -> str:
    top_category = "<none>" if report.top_category is None else report.top_category
    return _sha256(
        (
            "strategy_market_category_capital_efficiency_digest_report",
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"category_count={report.category_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"blocked_count={report.blocked_count}",
            f"top_category={top_category}",
            f"max_efficiency_score={report.max_efficiency_score}",
            f"min_efficiency_score={report.min_efficiency_score}",
            f"average_efficiency_score={report.average_efficiency_score}",
            f"digest_status={report.digest_status}",
            f"reason_codes={','.join(report.reason_codes)}",
            "row_digests="
            + ",".join(row.derived_validation_digest for row in report.rows),
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    normalized = value.strip()
    if normalized != value or len(normalized) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return normalized


def _sha256(values: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(character if character.isalnum() else "_" for character in lowered)
        .split("_")
        if part
    )
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _q(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _q(numerator / denominator)


__all__ = (
    "DEFAULT_STRATEGY_MARKET_CATEGORY_CAPITAL_EFFICIENCY_DIGEST_CONFIG_VERSION",
    "StrategyMarketCategoryCapitalEfficiencyDigestConfig",
    "StrategyMarketCategoryCapitalEfficiencyInput",
    "StrategyMarketCategoryCapitalEfficiencyDigestRow",
    "StrategyMarketCategoryCapitalEfficiencyDigestReport",
    "build_strategy_market_category_capital_efficiency_digest",
    "strategy_market_category_capital_efficiency_digest_payload",
    "validate_strategy_market_category_capital_efficiency_digest_public_payload",
)
