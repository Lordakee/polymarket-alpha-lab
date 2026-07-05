"""Pure Phase 1 copper inventory squeeze risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_COMMODITY_COPPER_INVENTORY_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-commodity-copper-inventory-squeeze-digest-v0"
)

SQUEEZE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "commodity_copper_inventory_active_withdrawal",
    "commodity_copper_inventory_backwardation",
    "commodity_copper_inventory_inline",
    "commodity_copper_inventory_low_visible_inventory",
    "commodity_copper_inventory_open_interest_coverage_low",
    "commodity_copper_inventory_price_rally",
    "commodity_copper_inventory_squeeze_blocked",
    "commodity_copper_inventory_squeeze_watch",
)
REPORT_REASON_CODES = (
    "commodity_copper_inventory_squeeze_blocked_present",
    "commodity_copper_inventory_low_visible_inventory_present",
    "commodity_copper_inventory_active_withdrawal_present",
    "commodity_copper_inventory_backwardation_present",
    "commodity_copper_inventory_price_rally_present",
    "commodity_copper_inventory_squeeze_digest_clear",
    "commodity_copper_inventory_squeeze_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ONE_HUNDRED = Decimal("100.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_UNSAFE_PUBLIC_TEXT = (
    "api" + "_key",
    "au" + "th",
    "bear" + "er",
    "cred" + "ential",
    "pass" + "word",
    "sec" + "ret",
    "to" + "ken",
    "private" + "_key",
    "wall" + "et",
)


__all__ = (
    "DEFAULT_COMMODITY_COPPER_INVENTORY_SQUEEZE_DIGEST_CONFIG_VERSION",
    "CommodityCopperInventorySqueezeDigestConfig",
    "CommodityCopperInventorySqueezeObservation",
    "CommodityCopperInventorySqueezeDigestRow",
    "CommodityCopperInventorySqueezeReasonCodeCount",
    "CommodityCopperInventorySqueezeDigestReport",
    "build_market_research_commodity_copper_inventory_squeeze_digest",
    "market_research_commodity_copper_inventory_squeeze_digest_payload",
)


@dataclass(frozen=True)
class CommodityCopperInventorySqueezeDigestConfig:
    config_version: str = DEFAULT_COMMODITY_COPPER_INVENTORY_SQUEEZE_DIGEST_CONFIG_VERSION
    watch_inventory_percentile: Decimal = Decimal("0.200000")
    blocked_inventory_percentile: Decimal = Decimal("0.080000")
    watch_inventory_coverage_ratio: Decimal = Decimal("0.150000")
    blocked_inventory_coverage_ratio: Decimal = Decimal("0.080000")
    withdrawal_pressure_pct: Decimal = Decimal("5.000000")
    backwardation_confirmation_pct: Decimal = Decimal("0.500000")
    price_rally_confirmation_pct: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CommodityCopperInventorySqueezeDigestConfig:
            raise TypeError(
                "CommodityCopperInventorySqueezeDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CommodityCopperInventorySqueezeDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_COMMODITY_COPPER_INVENTORY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_inventory_percentile",
            "blocked_inventory_percentile",
            "watch_inventory_coverage_ratio",
            "blocked_inventory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "withdrawal_pressure_pct",
            "backwardation_confirmation_pct",
            "price_rally_confirmation_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_inventory_percentile > self.watch_inventory_percentile:
            raise ValueError(
                "blocked_inventory_percentile must not exceed "
                "watch_inventory_percentile",
            )
        if self.blocked_inventory_coverage_ratio > self.watch_inventory_coverage_ratio:
            raise ValueError(
                "blocked_inventory_coverage_ratio must not exceed "
                "watch_inventory_coverage_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CommodityCopperInventorySqueezeObservation:
    source_id: str
    event_key: str
    warehouse_region: str
    visible_inventory_tonnes: Decimal
    weekly_inventory_change_tonnes: Decimal
    open_interest_tonnes: Decimal
    inventory_percentile: Decimal
    cash_3m_spread_pct: Decimal
    weekly_copper_return_pct: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CommodityCopperInventorySqueezeObservation:
            raise TypeError(
                "CommodityCopperInventorySqueezeObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CommodityCopperInventorySqueezeObservation, "observation")
        for field_name in ("source_id", "event_key", "warehouse_region"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "visible_inventory_tonnes",
            _require_positive_decimal(
                "visible_inventory_tonnes",
                self.visible_inventory_tonnes,
            ),
        )
        object.__setattr__(
            self,
            "open_interest_tonnes",
            _require_positive_decimal("open_interest_tonnes", self.open_interest_tonnes),
        )
        for field_name in (
            "weekly_inventory_change_tonnes",
            "cash_3m_spread_pct",
            "weekly_copper_return_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "inventory_percentile",
            _require_ratio("inventory_percentile", self.inventory_percentile),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _require_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class CommodityCopperInventorySqueezeDigestRow:
    source_id: str
    event_key: str
    warehouse_region: str
    visible_inventory_tonnes: Decimal
    weekly_inventory_change_tonnes: Decimal
    open_interest_tonnes: Decimal
    inventory_coverage_ratio: Decimal
    inventory_percentile: Decimal
    withdrawal_pressure_pct: Decimal
    cash_3m_spread_pct: Decimal
    weekly_copper_return_pct: Decimal
    data_timestamp: datetime
    squeeze_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CommodityCopperInventorySqueezeDigestRow:
            raise TypeError(
                "CommodityCopperInventorySqueezeDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CommodityCopperInventorySqueezeDigestRow, "row")
        for field_name in ("source_id", "event_key", "warehouse_region"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "visible_inventory_tonnes",
            _require_positive_decimal(
                "visible_inventory_tonnes",
                self.visible_inventory_tonnes,
            ),
        )
        object.__setattr__(
            self,
            "open_interest_tonnes",
            _require_positive_decimal("open_interest_tonnes", self.open_interest_tonnes),
        )
        for field_name in (
            "weekly_inventory_change_tonnes",
            "cash_3m_spread_pct",
            "weekly_copper_return_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "inventory_coverage_ratio",
            _require_ratio("inventory_coverage_ratio", self.inventory_coverage_ratio),
        )
        object.__setattr__(
            self,
            "inventory_percentile",
            _require_ratio("inventory_percentile", self.inventory_percentile),
        )
        object.__setattr__(
            self,
            "withdrawal_pressure_pct",
            _require_nonnegative_decimal(
                "withdrawal_pressure_pct",
                self.withdrawal_pressure_pct,
            ),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("squeeze_status", self.squeeze_status, SQUEEZE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CommodityCopperInventorySqueezeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CommodityCopperInventorySqueezeReasonCodeCount:
            raise TypeError(
                "CommodityCopperInventorySqueezeReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CommodityCopperInventorySqueezeReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class CommodityCopperInventorySqueezeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    low_inventory_count: Decimal
    active_withdrawal_count: Decimal
    backwardation_count: Decimal
    price_rally_count: Decimal
    max_withdrawal_pressure_pct: Decimal
    min_inventory_coverage_ratio: Decimal
    average_inventory_coverage_ratio: Decimal
    squeeze_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...]
    reason_code_counts: tuple[CommodityCopperInventorySqueezeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CommodityCopperInventorySqueezeDigestReport:
            raise TypeError(
                "CommodityCopperInventorySqueezeDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CommodityCopperInventorySqueezeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_COMMODITY_COPPER_INVENTORY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "low_inventory_count",
            "active_withdrawal_count",
            "backwardation_count",
            "price_rally_count",
            "max_withdrawal_pressure_pct",
            "min_inventory_coverage_ratio",
            "average_inventory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "squeeze_risk_score",
            _require_ratio("squeeze_risk_score", self.squeeze_risk_score),
        )
        _require_member("digest_status", self.digest_status, SQUEEZE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = frozenset(
    (
        CommodityCopperInventorySqueezeDigestConfig,
        CommodityCopperInventorySqueezeObservation,
        CommodityCopperInventorySqueezeDigestRow,
        CommodityCopperInventorySqueezeReasonCodeCount,
        CommodityCopperInventorySqueezeDigestReport,
    ),
)


def build_market_research_commodity_copper_inventory_squeeze_digest(
    observations: Iterable[CommodityCopperInventorySqueezeObservation],
    *,
    config: CommodityCopperInventorySqueezeDigestConfig,
    generated_at: datetime,
) -> CommodityCopperInventorySqueezeDigestReport:
    if type(config) is not CommodityCopperInventorySqueezeDigestConfig:
        raise ValueError(
            "config must be exactly CommodityCopperInventorySqueezeDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_observations = _require_observations(observations)
    for observation in source_observations:
        if observation.data_timestamp > generated_at_utc:
            raise ValueError("data_timestamp must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in source_observations
            ),
            key=_row_sort_value,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    row_count = _count_decimal(len(rows))

    return CommodityCopperInventorySqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(source_observations)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        low_inventory_count=_reason_count(
            rows,
            "commodity_copper_inventory_low_visible_inventory",
        ),
        active_withdrawal_count=_reason_count(
            rows,
            "commodity_copper_inventory_active_withdrawal",
        ),
        backwardation_count=_reason_count(
            rows,
            "commodity_copper_inventory_backwardation",
        ),
        price_rally_count=_reason_count(
            rows,
            "commodity_copper_inventory_price_rally",
        ),
        max_withdrawal_pressure_pct=_max_row_decimal(rows, "withdrawal_pressure_pct"),
        min_inventory_coverage_ratio=_min_row_decimal(rows, "inventory_coverage_ratio"),
        average_inventory_coverage_ratio=_ratio(
            _sum_decimal(row.inventory_coverage_ratio for row in rows),
            row_count,
        ),
        squeeze_risk_score=_squeeze_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_commodity_copper_inventory_squeeze_digest_payload(
    report: CommodityCopperInventorySqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not CommodityCopperInventorySqueezeDigestReport:
        raise ValueError(
            "report must be exactly CommodityCopperInventorySqueezeDigestReport",
        )
    _reject_unsafe_public_payload("report", report)
    validated = _validated_report(report)
    ready = _payload_value(validated)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _reject_unsafe_public_payload("payload", ready)
    return ready


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


def _row_from_observation(
    observation: CommodityCopperInventorySqueezeObservation,
    *,
    config: CommodityCopperInventorySqueezeDigestConfig,
) -> CommodityCopperInventorySqueezeDigestRow:
    inventory_coverage_ratio = _ratio(
        observation.visible_inventory_tonnes,
        observation.open_interest_tonnes,
    )
    withdrawal_pressure_pct = _withdrawal_pressure_pct(observation)
    squeeze_status = _squeeze_status(
        observation,
        inventory_coverage_ratio=inventory_coverage_ratio,
        withdrawal_pressure_pct=withdrawal_pressure_pct,
        config=config,
    )
    return CommodityCopperInventorySqueezeDigestRow(
        source_id=observation.source_id,
        event_key=observation.event_key,
        warehouse_region=observation.warehouse_region,
        visible_inventory_tonnes=observation.visible_inventory_tonnes,
        weekly_inventory_change_tonnes=observation.weekly_inventory_change_tonnes,
        open_interest_tonnes=observation.open_interest_tonnes,
        inventory_coverage_ratio=inventory_coverage_ratio,
        inventory_percentile=observation.inventory_percentile,
        withdrawal_pressure_pct=withdrawal_pressure_pct,
        cash_3m_spread_pct=observation.cash_3m_spread_pct,
        weekly_copper_return_pct=observation.weekly_copper_return_pct,
        data_timestamp=observation.data_timestamp,
        squeeze_status=squeeze_status,
        reason_codes=_row_reason_codes(
            observation,
            squeeze_status=squeeze_status,
            inventory_coverage_ratio=inventory_coverage_ratio,
            withdrawal_pressure_pct=withdrawal_pressure_pct,
            config=config,
        ),
    )


def _squeeze_status(
    observation: CommodityCopperInventorySqueezeObservation,
    *,
    inventory_coverage_ratio: Decimal,
    withdrawal_pressure_pct: Decimal,
    config: CommodityCopperInventorySqueezeDigestConfig,
) -> str:
    low_inventory = _has_low_inventory(
        observation,
        inventory_coverage_ratio=inventory_coverage_ratio,
        config=config,
    )
    blocked_low_inventory = _has_blocked_low_inventory(
        observation,
        inventory_coverage_ratio=inventory_coverage_ratio,
        config=config,
    )
    active_withdrawal = withdrawal_pressure_pct >= config.withdrawal_pressure_pct
    backwardation = observation.cash_3m_spread_pct >= config.backwardation_confirmation_pct
    price_rally = observation.weekly_copper_return_pct >= config.price_rally_confirmation_pct
    if blocked_low_inventory and active_withdrawal and backwardation and price_rally:
        return "blocked"
    if low_inventory or (active_withdrawal and (backwardation or price_rally)):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: CommodityCopperInventorySqueezeObservation,
    *,
    squeeze_status: str,
    inventory_coverage_ratio: Decimal,
    withdrawal_pressure_pct: Decimal,
    config: CommodityCopperInventorySqueezeDigestConfig,
) -> tuple[str, ...]:
    if squeeze_status == "pass":
        return ("commodity_copper_inventory_inline",)

    reason_codes: list[str] = []
    if withdrawal_pressure_pct >= config.withdrawal_pressure_pct:
        reason_codes.append("commodity_copper_inventory_active_withdrawal")
    if observation.cash_3m_spread_pct >= config.backwardation_confirmation_pct:
        reason_codes.append("commodity_copper_inventory_backwardation")
    if _has_low_inventory(
        observation,
        inventory_coverage_ratio=inventory_coverage_ratio,
        config=config,
    ):
        reason_codes.append("commodity_copper_inventory_low_visible_inventory")
    if inventory_coverage_ratio <= config.blocked_inventory_coverage_ratio:
        reason_codes.append("commodity_copper_inventory_open_interest_coverage_low")
    if observation.weekly_copper_return_pct >= config.price_rally_confirmation_pct:
        reason_codes.append("commodity_copper_inventory_price_rally")
    if squeeze_status == "blocked":
        reason_codes.append("commodity_copper_inventory_squeeze_blocked")
    else:
        reason_codes.append("commodity_copper_inventory_squeeze_watch")
    return _canonical_reason_codes(tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("commodity_copper_inventory_squeeze_digest_empty",)
    reason_codes: list[str] = []
    if any(row.squeeze_status == "blocked" for row in rows):
        reason_codes.append("commodity_copper_inventory_squeeze_blocked_present")
    if _reason_count(rows, "commodity_copper_inventory_low_visible_inventory") > ZERO:
        reason_codes.append("commodity_copper_inventory_low_visible_inventory_present")
    if _reason_count(rows, "commodity_copper_inventory_active_withdrawal") > ZERO:
        reason_codes.append("commodity_copper_inventory_active_withdrawal_present")
    if _reason_count(rows, "commodity_copper_inventory_backwardation") > ZERO:
        reason_codes.append("commodity_copper_inventory_backwardation_present")
    if _reason_count(rows, "commodity_copper_inventory_price_rally") > ZERO:
        reason_codes.append("commodity_copper_inventory_price_rally_present")
    if not reason_codes:
        reason_codes.append("commodity_copper_inventory_squeeze_digest_clear")
    return _canonical_reason_codes(tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
) -> tuple[CommodityCopperInventorySqueezeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("commodity_copper_inventory_squeeze_digest_empty",):
        return (
            CommodityCopperInventorySqueezeReasonCodeCount(
                reason_code="commodity_copper_inventory_squeeze_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        CommodityCopperInventorySqueezeReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
) -> Decimal:
    if reason_code == "commodity_copper_inventory_squeeze_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "commodity_copper_inventory_low_visible_inventory_present":
        return _reason_count(rows, "commodity_copper_inventory_low_visible_inventory")
    if reason_code == "commodity_copper_inventory_active_withdrawal_present":
        return _reason_count(rows, "commodity_copper_inventory_active_withdrawal")
    if reason_code == "commodity_copper_inventory_backwardation_present":
        return _reason_count(rows, "commodity_copper_inventory_backwardation")
    if reason_code == "commodity_copper_inventory_price_rally_present":
        return _reason_count(rows, "commodity_copper_inventory_price_rally")
    return _reason_count(rows, "commodity_copper_inventory_inline")


def _digest_status(rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.squeeze_status == "blocked" for row in rows):
        return "blocked"
    if any(row.squeeze_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_commodity_copper_inventory_squeeze_screening"
    if status == "watch":
        return "monitor_report_only_commodity_copper_inventory_squeeze_screening"
    return "block_report_only_commodity_copper_inventory_squeeze_screening"


def _squeeze_risk_score(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows) == "blocked":
        return ONE
    if _digest_status(rows) == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _has_low_inventory(
    observation: CommodityCopperInventorySqueezeObservation,
    *,
    inventory_coverage_ratio: Decimal,
    config: CommodityCopperInventorySqueezeDigestConfig,
) -> bool:
    return (
        observation.inventory_percentile <= config.watch_inventory_percentile
        or inventory_coverage_ratio <= config.watch_inventory_coverage_ratio
    )


def _has_blocked_low_inventory(
    observation: CommodityCopperInventorySqueezeObservation,
    *,
    inventory_coverage_ratio: Decimal,
    config: CommodityCopperInventorySqueezeDigestConfig,
) -> bool:
    return (
        observation.inventory_percentile <= config.blocked_inventory_percentile
        or inventory_coverage_ratio <= config.blocked_inventory_coverage_ratio
    )


def _withdrawal_pressure_pct(
    observation: CommodityCopperInventorySqueezeObservation,
) -> Decimal:
    if observation.weekly_inventory_change_tonnes >= ZERO:
        return ZERO
    return _quantize_decimal(
        _ratio(
            -observation.weekly_inventory_change_tonnes,
            observation.visible_inventory_tonnes,
        )
        * ONE_HUNDRED,
    )


def _validate_row(row: CommodityCopperInventorySqueezeDigestRow) -> None:
    if row.inventory_coverage_ratio != _ratio(
        row.visible_inventory_tonnes,
        row.open_interest_tonnes,
    ):
        raise ValueError("inventory_coverage_ratio must match visible inventory")
    expected_withdrawal_pressure = ZERO
    if row.weekly_inventory_change_tonnes < ZERO:
        expected_withdrawal_pressure = (
            _ratio(-row.weekly_inventory_change_tonnes, row.visible_inventory_tonnes)
            * ONE_HUNDRED
        )
    if row.withdrawal_pressure_pct != _quantize_decimal(expected_withdrawal_pressure):
        raise ValueError("withdrawal_pressure_pct must match weekly inventory change")
    if row.squeeze_status == "pass":
        if row.reason_codes != ("commodity_copper_inventory_inline",):
            raise ValueError("reason_codes must match squeeze_status")
        return
    if row.squeeze_status == "watch":
        if "commodity_copper_inventory_squeeze_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "commodity_copper_inventory_squeeze_blocked" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
    if row.squeeze_status == "blocked":
        if "commodity_copper_inventory_squeeze_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "commodity_copper_inventory_squeeze_watch" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")


def _validate_report(report: CommodityCopperInventorySqueezeDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.low_inventory_count != _reason_count(
        report.rows,
        "commodity_copper_inventory_low_visible_inventory",
    ):
        raise ValueError("low_inventory_count must match rows")
    if report.active_withdrawal_count != _reason_count(
        report.rows,
        "commodity_copper_inventory_active_withdrawal",
    ):
        raise ValueError("active_withdrawal_count must match rows")
    if report.backwardation_count != _reason_count(
        report.rows,
        "commodity_copper_inventory_backwardation",
    ):
        raise ValueError("backwardation_count must match rows")
    if report.price_rally_count != _reason_count(
        report.rows,
        "commodity_copper_inventory_price_rally",
    ):
        raise ValueError("price_rally_count must match rows")
    if report.max_withdrawal_pressure_pct != _max_row_decimal(
        report.rows,
        "withdrawal_pressure_pct",
    ):
        raise ValueError("max_withdrawal_pressure_pct must match rows")
    if report.min_inventory_coverage_ratio != _min_row_decimal(
        report.rows,
        "inventory_coverage_ratio",
    ):
        raise ValueError("min_inventory_coverage_ratio must match rows")
    if report.average_inventory_coverage_ratio != _ratio(
        _sum_decimal(row.inventory_coverage_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_inventory_coverage_ratio must match rows")
    if report.squeeze_risk_score != _squeeze_risk_score(report.rows):
        raise ValueError("squeeze_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _require_observations(
    observations: Iterable[CommodityCopperInventorySqueezeObservation],
) -> tuple[CommodityCopperInventorySqueezeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain CommodityCopperInventorySqueezeObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not CommodityCopperInventorySqueezeObservation:
            raise ValueError(
                "observations must contain CommodityCopperInventorySqueezeObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _require_rows(
    rows: Iterable[CommodityCopperInventorySqueezeDigestRow],
) -> tuple[CommodityCopperInventorySqueezeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must contain CommodityCopperInventorySqueezeDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not CommodityCopperInventorySqueezeDigestRow:
            raise ValueError("rows must contain CommodityCopperInventorySqueezeDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_value)):
        raise ValueError("rows must be canonical")
    return normalized


def _require_reason_code_counts(
    values: Iterable[CommodityCopperInventorySqueezeReasonCodeCount],
) -> tuple[CommodityCopperInventorySqueezeReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not CommodityCopperInventorySqueezeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CommodityCopperInventorySqueezeReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_reason_codes.add(value.reason_code)
    canonical = tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )
    if normalized != canonical:
        raise ValueError("reason_code_counts must be canonical")
    return normalized


def _require_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_canonical_string("reason_code", value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != _canonical_reason_codes(normalized, allowed):
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _canonical_reason_codes(
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in allowed if reason_code in values)


def _row_sort_value(
    row: CommodityCopperInventorySqueezeDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.squeeze_status],
        row.inventory_percentile,
        row.event_key,
        row.source_id,
    )


def _status_count(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.squeeze_status == status))


def _reason_count(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[CommodityCopperInventorySqueezeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be six-decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must already be UTC for payload serialization")
    return value


ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _validated_report(
    report: CommodityCopperInventorySqueezeDigestReport,
) -> CommodityCopperInventorySqueezeDigestReport:
    _require_payload_utc_datetime("generated_at", report.generated_at)
    return CommodityCopperInventorySqueezeDigestReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_count=report.input_count,
        row_count=report.row_count,
        blocked_count=report.blocked_count,
        watch_count=report.watch_count,
        pass_count=report.pass_count,
        low_inventory_count=report.low_inventory_count,
        active_withdrawal_count=report.active_withdrawal_count,
        backwardation_count=report.backwardation_count,
        price_rally_count=report.price_rally_count,
        max_withdrawal_pressure_pct=report.max_withdrawal_pressure_pct,
        min_inventory_coverage_ratio=report.min_inventory_coverage_ratio,
        average_inventory_coverage_ratio=report.average_inventory_coverage_ratio,
        squeeze_risk_score=report.squeeze_risk_score,
        digest_status=report.digest_status,
        recommended_next_step=report.recommended_next_step,
        rows=_validated_rows(report.rows),
        reason_code_counts=_validated_reason_code_counts(report.reason_code_counts),
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _validated_rows(
    rows: object,
) -> tuple[CommodityCopperInventorySqueezeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    return tuple(_validated_row(row) for row in rows)


def _validated_row(row: object) -> CommodityCopperInventorySqueezeDigestRow:
    if type(row) is not CommodityCopperInventorySqueezeDigestRow:
        raise ValueError("rows must contain CommodityCopperInventorySqueezeDigestRow")
    _require_payload_utc_datetime("data_timestamp", row.data_timestamp)
    return CommodityCopperInventorySqueezeDigestRow(
        source_id=row.source_id,
        event_key=row.event_key,
        warehouse_region=row.warehouse_region,
        visible_inventory_tonnes=row.visible_inventory_tonnes,
        weekly_inventory_change_tonnes=row.weekly_inventory_change_tonnes,
        open_interest_tonnes=row.open_interest_tonnes,
        inventory_coverage_ratio=row.inventory_coverage_ratio,
        inventory_percentile=row.inventory_percentile,
        withdrawal_pressure_pct=row.withdrawal_pressure_pct,
        cash_3m_spread_pct=row.cash_3m_spread_pct,
        weekly_copper_return_pct=row.weekly_copper_return_pct,
        data_timestamp=row.data_timestamp,
        squeeze_status=row.squeeze_status,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _validated_reason_code_counts(
    counts: object,
) -> tuple[CommodityCopperInventorySqueezeReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    return tuple(_validated_reason_code_count(count) for count in counts)


def _validated_reason_code_count(
    count: object,
) -> CommodityCopperInventorySqueezeReasonCodeCount:
    if type(count) is not CommodityCopperInventorySqueezeReasonCodeCount:
        raise ValueError("reason_code_counts must contain reason count rows")
    return CommodityCopperInventorySqueezeReasonCodeCount(
        reason_code=count.reason_code,
        count=count.count,
        row_ratio=count.row_ratio,
        paper_only=count.paper_only,
        report_only=count.report_only,
        readonly=count.readonly,
    )


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        _require_decimal("payload decimal", value)
        return format(value, "f")
    if type(value) is datetime:
        return _require_payload_utc_datetime("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload must contain supported public dataclass values")
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT):
            raise ValueError(f"{label} contains unsafe public payload text")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload must contain supported public dataclass values")
        for field in fields(value):
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_payload(f"{label}.{key}", key)
            _reject_unsafe_public_payload(f"{label}.{key}", child)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", child)
