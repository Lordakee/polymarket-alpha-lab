"""Pure Phase 1 Bitcoin halving supply-pressure digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_BITCOIN_HALVING_SUPPLY_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-bitcoin-halving-supply-pressure-digest-v0"
)

INPUT_REASON_CODES = (
    "bitcoin_halving_supply_cut_active",
    "bitcoin_miner_exchange_inflow_pressure",
    "bitcoin_miner_reserve_drawdown_pressure",
    "bitcoin_hashprice_drawdown_pressure",
    "bitcoin_difficulty_adjustment_window_near",
    "bitcoin_halving_supply_pressure_stable",
)
ROW_REASON_CODES = (
    "bitcoin_halving_blocked_supply_cut",
    "bitcoin_miner_exchange_inflow_pressure",
    "bitcoin_miner_reserve_drawdown_pressure",
    "bitcoin_hashprice_drawdown_pressure",
    "bitcoin_difficulty_adjustment_window_near",
    "bitcoin_halving_supply_pressure_watch",
    "bitcoin_halving_supply_pressure_stable",
)
REPORT_REASON_CODES = (
    "bitcoin_halving_supply_pressure_blocked_risk_present",
    "bitcoin_halving_supply_pressure_watch_risk_present",
    "bitcoin_halving_supply_pressure_digest_clear",
    "bitcoin_halving_supply_pressure_digest_empty",
)
PRESSURE_STATUSES = ("pass", "watch", "blocked")

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_WATCH_SUPPLY_CUT_RATIO = Decimal("0.025000")
DEFAULT_BLOCKED_SUPPLY_CUT_RATIO = Decimal("0.050000")
DEFAULT_WATCH_MINER_EXCHANGE_INFLOW_RATIO = Decimal("0.080000")
DEFAULT_BLOCKED_MINER_EXCHANGE_INFLOW_RATIO = Decimal("0.150000")
DEFAULT_WATCH_MINER_RESERVE_DRAWDOWN_RATIO = Decimal("0.050000")
DEFAULT_BLOCKED_MINER_RESERVE_DRAWDOWN_RATIO = Decimal("0.100000")
DEFAULT_WATCH_HASHPRICE_DRAWDOWN_RATIO = Decimal("0.150000")
DEFAULT_BLOCKED_HASHPRICE_DRAWDOWN_RATIO = Decimal("0.300000")
DEFAULT_NEAR_DIFFICULTY_ADJUSTMENT_HOURS = Decimal("72.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_BITCOIN_HALVING_SUPPLY_PRESSURE_DIGEST_CONFIG_VERSION",
    "BitcoinHalvingSupplyPressureDigestConfig",
    "BitcoinHalvingSupplyPressureObservation",
    "BitcoinHalvingSupplyPressureDigestRow",
    "BitcoinHalvingSupplyPressureReasonCodeCount",
    "BitcoinHalvingSupplyPressureDigestReport",
    "build_market_research_crypto_bitcoin_halving_supply_pressure_digest",
    "market_research_crypto_bitcoin_halving_supply_pressure_digest_payload",
)


@dataclass(frozen=True)
class BitcoinHalvingSupplyPressureDigestConfig:
    config_version: str = DEFAULT_BITCOIN_HALVING_SUPPLY_PRESSURE_DIGEST_CONFIG_VERSION
    watch_supply_cut_ratio: Decimal = DEFAULT_WATCH_SUPPLY_CUT_RATIO
    blocked_supply_cut_ratio: Decimal = DEFAULT_BLOCKED_SUPPLY_CUT_RATIO
    watch_miner_exchange_inflow_ratio: Decimal = (
        DEFAULT_WATCH_MINER_EXCHANGE_INFLOW_RATIO
    )
    blocked_miner_exchange_inflow_ratio: Decimal = (
        DEFAULT_BLOCKED_MINER_EXCHANGE_INFLOW_RATIO
    )
    watch_miner_reserve_drawdown_ratio: Decimal = (
        DEFAULT_WATCH_MINER_RESERVE_DRAWDOWN_RATIO
    )
    blocked_miner_reserve_drawdown_ratio: Decimal = (
        DEFAULT_BLOCKED_MINER_RESERVE_DRAWDOWN_RATIO
    )
    watch_hashprice_drawdown_ratio: Decimal = DEFAULT_WATCH_HASHPRICE_DRAWDOWN_RATIO
    blocked_hashprice_drawdown_ratio: Decimal = (
        DEFAULT_BLOCKED_HASHPRICE_DRAWDOWN_RATIO
    )
    near_difficulty_adjustment_hours: Decimal = (
        DEFAULT_NEAR_DIFFICULTY_ADJUSTMENT_HOURS
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BitcoinHalvingSupplyPressureDigestConfig:
            raise TypeError(
                "BitcoinHalvingSupplyPressureDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BitcoinHalvingSupplyPressureDigestConfig:
            raise ValueError(
                "config must be exactly BitcoinHalvingSupplyPressureDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BITCOIN_HALVING_SUPPLY_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_supply_cut_ratio",
            "blocked_supply_cut_ratio",
            "watch_miner_exchange_inflow_ratio",
            "blocked_miner_exchange_inflow_ratio",
            "watch_miner_reserve_drawdown_ratio",
            "blocked_miner_reserve_drawdown_ratio",
            "watch_hashprice_drawdown_ratio",
            "blocked_hashprice_drawdown_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_difficulty_adjustment_hours",
            _require_positive_decimal(
                "near_difficulty_adjustment_hours",
                self.near_difficulty_adjustment_hours,
            ),
        )
        if self.blocked_supply_cut_ratio < self.watch_supply_cut_ratio:
            raise ValueError("blocked_supply_cut_ratio must be at least watch threshold")
        if (
            self.blocked_miner_exchange_inflow_ratio
            < self.watch_miner_exchange_inflow_ratio
        ):
            raise ValueError(
                "blocked_miner_exchange_inflow_ratio must be at least watch threshold",
            )
        if (
            self.blocked_miner_reserve_drawdown_ratio
            < self.watch_miner_reserve_drawdown_ratio
        ):
            raise ValueError(
                "blocked_miner_reserve_drawdown_ratio must be at least watch threshold",
            )
        if self.blocked_hashprice_drawdown_ratio < self.watch_hashprice_drawdown_ratio:
            raise ValueError(
                "blocked_hashprice_drawdown_ratio must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class BitcoinHalvingSupplyPressureObservation:
    source_id: str
    miner_cohort_id: str
    market_slug: str
    miner_reserve_btc: Decimal
    supply_cut_ratio: Decimal
    miner_exchange_inflow_ratio: Decimal
    miner_reserve_drawdown_ratio: Decimal
    hashprice_drawdown_ratio: Decimal
    next_difficulty_adjustment_hours: Decimal
    source_row_count: Decimal
    observation_timestamp: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BitcoinHalvingSupplyPressureObservation:
            raise TypeError(
                "BitcoinHalvingSupplyPressureObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BitcoinHalvingSupplyPressureObservation:
            raise ValueError(
                "observation must be exactly BitcoinHalvingSupplyPressureObservation",
            )
        for field_name in ("source_id", "miner_cohort_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "miner_reserve_btc",
            _require_nonnegative_decimal("miner_reserve_btc", self.miner_reserve_btc),
        )
        for field_name in (
            "supply_cut_ratio",
            "miner_exchange_inflow_ratio",
            "miner_reserve_drawdown_ratio",
            "hashprice_drawdown_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "next_difficulty_adjustment_hours",
            _require_nonnegative_decimal(
                "next_difficulty_adjustment_hours",
                self.next_difficulty_adjustment_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_whole_nonnegative_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "observation_timestamp",
            _as_utc("observation_timestamp", self.observation_timestamp),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class BitcoinHalvingSupplyPressureDigestRow:
    source_id: str
    miner_cohort_id: str
    market_slug: str
    miner_reserve_btc: Decimal
    supply_cut_ratio: Decimal
    miner_exchange_inflow_ratio: Decimal
    miner_reserve_drawdown_ratio: Decimal
    hashprice_drawdown_ratio: Decimal
    next_difficulty_adjustment_hours: Decimal
    source_row_count: Decimal
    observation_timestamp: datetime
    pressure_score: Decimal
    pressure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BitcoinHalvingSupplyPressureDigestRow:
            raise TypeError(
                "BitcoinHalvingSupplyPressureDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BitcoinHalvingSupplyPressureDigestRow:
            raise ValueError("row must be exactly BitcoinHalvingSupplyPressureDigestRow")
        for field_name in ("source_id", "miner_cohort_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "miner_reserve_btc",
            _require_nonnegative_decimal("miner_reserve_btc", self.miner_reserve_btc),
        )
        for field_name in (
            "supply_cut_ratio",
            "miner_exchange_inflow_ratio",
            "miner_reserve_drawdown_ratio",
            "hashprice_drawdown_ratio",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "next_difficulty_adjustment_hours",
            _require_nonnegative_decimal(
                "next_difficulty_adjustment_hours",
                self.next_difficulty_adjustment_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _require_whole_nonnegative_decimal("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "observation_timestamp",
            _as_utc("observation_timestamp", self.observation_timestamp),
        )
        _require_member("pressure_status", self.pressure_status, PRESSURE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class BitcoinHalvingSupplyPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BitcoinHalvingSupplyPressureReasonCodeCount:
            raise TypeError(
                "BitcoinHalvingSupplyPressureReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BitcoinHalvingSupplyPressureReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "BitcoinHalvingSupplyPressureReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES + REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_whole_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class BitcoinHalvingSupplyPressureDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    blocked_segment_count: Decimal
    watch_segment_count: Decimal
    pass_segment_count: Decimal
    total_miner_reserve_btc: Decimal
    max_pressure_score: Decimal
    average_pressure_score: Decimal
    blocked_observation_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    segment_rows: tuple[BitcoinHalvingSupplyPressureDigestRow, ...]
    reason_code_counts: tuple[BitcoinHalvingSupplyPressureReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not BitcoinHalvingSupplyPressureDigestReport:
            raise TypeError(
                "BitcoinHalvingSupplyPressureDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not BitcoinHalvingSupplyPressureDigestReport:
            raise ValueError(
                "report must be exactly BitcoinHalvingSupplyPressureDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_BITCOIN_HALVING_SUPPLY_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "observation_count",
            "blocked_segment_count",
            "watch_segment_count",
            "pass_segment_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_miner_reserve_btc",
            _require_nonnegative_decimal(
                "total_miner_reserve_btc",
                self.total_miner_reserve_btc,
            ),
        )
        for field_name in (
            "max_pressure_score",
            "average_pressure_score",
            "blocked_observation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, PRESSURE_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "segment_rows", _normalize_rows(self.segment_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_bitcoin_halving_supply_pressure_digest(
    inputs: Iterable[BitcoinHalvingSupplyPressureObservation],
    *,
    config: BitcoinHalvingSupplyPressureDigestConfig,
    generated_at: datetime,
) -> BitcoinHalvingSupplyPressureDigestReport:
    if type(config) is not BitcoinHalvingSupplyPressureDigestConfig:
        raise ValueError("config must be exactly BitcoinHalvingSupplyPressureDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    for observation in observations:
        if observation.observation_timestamp > generated_at_utc:
            raise ValueError("observation_timestamp must not be after generated_at")
    rows = tuple(_row_for_observation(item, config=config) for item in observations)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(sorted_rows))
    blocked_count = _count_decimal(
        sum(1 for row in sorted_rows if row.pressure_status == "blocked"),
    )
    row_reason_codes = tuple(
        reason_code for row in sorted_rows for reason_code in row.reason_codes
    )
    digest_status = _digest_status(sorted_rows)

    return BitcoinHalvingSupplyPressureDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_sum_decimal(row.source_row_count for row in sorted_rows),
        observation_count=observation_count,
        blocked_segment_count=blocked_count,
        watch_segment_count=_count_decimal(
            sum(1 for row in sorted_rows if row.pressure_status == "watch"),
        ),
        pass_segment_count=_count_decimal(
            sum(1 for row in sorted_rows if row.pressure_status == "pass"),
        ),
        total_miner_reserve_btc=_sum_decimal(
            row.miner_reserve_btc for row in sorted_rows
        ),
        max_pressure_score=max((row.pressure_score for row in sorted_rows), default=ZERO),
        average_pressure_score=_ratio(
            _sum_decimal(row.pressure_score for row in sorted_rows),
            observation_count,
        ),
        blocked_observation_ratio=_ratio(blocked_count, observation_count),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        segment_rows=sorted_rows,
        reason_code_counts=_reason_code_counts(row_reason_codes, observation_count),
        reason_codes=_report_reason_codes(sorted_rows),
    )


def market_research_crypto_bitcoin_halving_supply_pressure_digest_payload(
    report: BitcoinHalvingSupplyPressureDigestReport,
) -> dict[str, Any]:
    if type(report) is not BitcoinHalvingSupplyPressureDigestReport:
        raise ValueError(
            "report must be exactly BitcoinHalvingSupplyPressureDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_observation(
    observation: BitcoinHalvingSupplyPressureObservation,
    *,
    config: BitcoinHalvingSupplyPressureDigestConfig,
) -> BitcoinHalvingSupplyPressureDigestRow:
    status = _pressure_status(observation, config=config)
    return BitcoinHalvingSupplyPressureDigestRow(
        source_id=observation.source_id,
        miner_cohort_id=observation.miner_cohort_id,
        market_slug=observation.market_slug,
        miner_reserve_btc=observation.miner_reserve_btc,
        supply_cut_ratio=observation.supply_cut_ratio,
        miner_exchange_inflow_ratio=observation.miner_exchange_inflow_ratio,
        miner_reserve_drawdown_ratio=observation.miner_reserve_drawdown_ratio,
        hashprice_drawdown_ratio=observation.hashprice_drawdown_ratio,
        next_difficulty_adjustment_hours=observation.next_difficulty_adjustment_hours,
        source_row_count=observation.source_row_count,
        observation_timestamp=observation.observation_timestamp,
        pressure_score=_pressure_score(observation, config=config, status=status),
        pressure_status=status,
        reason_codes=_row_reason_codes(observation, config=config, status=status),
    )


def _pressure_status(
    observation: BitcoinHalvingSupplyPressureObservation,
    *,
    config: BitcoinHalvingSupplyPressureDigestConfig,
) -> str:
    if (
        observation.supply_cut_ratio >= config.blocked_supply_cut_ratio
        or observation.miner_exchange_inflow_ratio
        >= config.blocked_miner_exchange_inflow_ratio
        or observation.miner_reserve_drawdown_ratio
        >= config.blocked_miner_reserve_drawdown_ratio
        or observation.hashprice_drawdown_ratio >= config.blocked_hashprice_drawdown_ratio
    ):
        return "blocked"
    if (
        observation.supply_cut_ratio >= config.watch_supply_cut_ratio
        or observation.miner_exchange_inflow_ratio >= config.watch_miner_exchange_inflow_ratio
        or observation.miner_reserve_drawdown_ratio
        >= config.watch_miner_reserve_drawdown_ratio
        or observation.hashprice_drawdown_ratio >= config.watch_hashprice_drawdown_ratio
        or observation.next_difficulty_adjustment_hours
        <= config.near_difficulty_adjustment_hours
    ):
        return "watch"
    return "pass"


def _pressure_score(
    observation: BitcoinHalvingSupplyPressureObservation,
    *,
    config: BitcoinHalvingSupplyPressureDigestConfig,
    status: str,
) -> Decimal:
    if status == "pass":
        return ZERO
    adjustment_score = ZERO
    if (
        observation.next_difficulty_adjustment_hours
        <= config.near_difficulty_adjustment_hours
    ):
        adjustment_score = _ratio(
            config.near_difficulty_adjustment_hours
            - observation.next_difficulty_adjustment_hours,
            config.near_difficulty_adjustment_hours,
        )
    return min(
        ONE,
        max(
            _ratio(observation.supply_cut_ratio, config.blocked_supply_cut_ratio),
            _ratio(
                observation.miner_exchange_inflow_ratio,
                config.blocked_miner_exchange_inflow_ratio,
            ),
            _ratio(
                observation.miner_reserve_drawdown_ratio,
                config.blocked_miner_reserve_drawdown_ratio,
            ),
            _ratio(
                observation.hashprice_drawdown_ratio,
                config.blocked_hashprice_drawdown_ratio,
            ),
            adjustment_score,
        ),
    )


def _row_reason_codes(
    observation: BitcoinHalvingSupplyPressureObservation,
    *,
    config: BitcoinHalvingSupplyPressureDigestConfig,
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        return ("bitcoin_halving_supply_pressure_stable",)
    reason_codes: list[str] = []
    if observation.supply_cut_ratio >= config.blocked_supply_cut_ratio:
        reason_codes.append("bitcoin_halving_blocked_supply_cut")
    elif observation.supply_cut_ratio >= config.watch_supply_cut_ratio:
        reason_codes.append("bitcoin_halving_supply_pressure_watch")
    if observation.miner_exchange_inflow_ratio >= config.watch_miner_exchange_inflow_ratio:
        reason_codes.append("bitcoin_miner_exchange_inflow_pressure")
    if (
        observation.miner_reserve_drawdown_ratio
        >= config.watch_miner_reserve_drawdown_ratio
    ):
        reason_codes.append("bitcoin_miner_reserve_drawdown_pressure")
    if observation.hashprice_drawdown_ratio >= config.watch_hashprice_drawdown_ratio:
        reason_codes.append("bitcoin_hashprice_drawdown_pressure")
    if (
        observation.next_difficulty_adjustment_hours
        <= config.near_difficulty_adjustment_hours
    ):
        reason_codes.append("bitcoin_difficulty_adjustment_window_near")
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes)


def _report_reason_codes(
    rows: tuple[BitcoinHalvingSupplyPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("bitcoin_halving_supply_pressure_digest_empty",)
    has_blocked = any(row.pressure_status == "blocked" for row in rows)
    has_watch = any(row.pressure_status == "watch" for row in rows)
    if has_blocked and has_watch:
        return (
            "bitcoin_halving_supply_pressure_blocked_risk_present",
            "bitcoin_halving_supply_pressure_watch_risk_present",
        )
    if has_blocked:
        return ("bitcoin_halving_supply_pressure_blocked_risk_present",)
    if has_watch:
        return ("bitcoin_halving_supply_pressure_watch_risk_present",)
    return ("bitcoin_halving_supply_pressure_digest_clear",)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    observation_count: Decimal,
) -> tuple[BitcoinHalvingSupplyPressureReasonCodeCount, ...]:
    if not reason_codes:
        return (
            BitcoinHalvingSupplyPressureReasonCodeCount(
                reason_code="bitcoin_halving_supply_pressure_digest_empty",
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    return tuple(
        BitcoinHalvingSupplyPressureReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
            observation_ratio=_ratio(
                _count_decimal(sum(1 for item in reason_codes if item == reason_code)),
                observation_count,
            ),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in reason_codes
    )


def _digest_status(rows: tuple[BitcoinHalvingSupplyPressureDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.pressure_status == "blocked" for row in rows):
        return "blocked"
    if any(row.pressure_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return (
            "allow_report_only_market_research_crypto_bitcoin_halving_"
            "supply_pressure_digest"
        )
    if status == "watch":
        return (
            "monitor_report_only_market_research_crypto_bitcoin_halving_"
            "supply_pressure_digest"
        )
    return (
        "block_report_only_market_research_crypto_bitcoin_halving_"
        "supply_pressure_digest"
    )


def _validate_observation(observation: BitcoinHalvingSupplyPressureObservation) -> None:
    if observation.reason_codes != _input_reason_codes(observation):
        raise ValueError("reason_codes must match Bitcoin halving supply pressure metrics")


def _input_reason_codes(
    observation: BitcoinHalvingSupplyPressureObservation,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.supply_cut_ratio >= DEFAULT_WATCH_SUPPLY_CUT_RATIO:
        reason_codes.append("bitcoin_halving_supply_cut_active")
    if (
        observation.miner_exchange_inflow_ratio
        >= DEFAULT_WATCH_MINER_EXCHANGE_INFLOW_RATIO
    ):
        reason_codes.append("bitcoin_miner_exchange_inflow_pressure")
    if (
        observation.miner_reserve_drawdown_ratio
        >= DEFAULT_WATCH_MINER_RESERVE_DRAWDOWN_RATIO
    ):
        reason_codes.append("bitcoin_miner_reserve_drawdown_pressure")
    if observation.hashprice_drawdown_ratio >= DEFAULT_WATCH_HASHPRICE_DRAWDOWN_RATIO:
        reason_codes.append("bitcoin_hashprice_drawdown_pressure")
    if (
        observation.next_difficulty_adjustment_hours
        <= DEFAULT_NEAR_DIFFICULTY_ADJUSTMENT_HOURS
    ):
        reason_codes.append("bitcoin_difficulty_adjustment_window_near")
    if not reason_codes:
        reason_codes.append("bitcoin_halving_supply_pressure_stable")
    return tuple(reason_code for reason_code in INPUT_REASON_CODES if reason_code in reason_codes)


def _validate_report(report: BitcoinHalvingSupplyPressureDigestReport) -> None:
    if report.source_row_count != _sum_decimal(row.source_row_count for row in report.segment_rows):
        raise ValueError("source_row_count must match rows")
    if report.observation_count != _count_decimal(len(report.segment_rows)):
        raise ValueError("observation_count must match rows")
    if report.blocked_segment_count != _count_decimal(
        sum(1 for row in report.segment_rows if row.pressure_status == "blocked"),
    ):
        raise ValueError("blocked_segment_count must match rows")
    if report.watch_segment_count != _count_decimal(
        sum(1 for row in report.segment_rows if row.pressure_status == "watch"),
    ):
        raise ValueError("watch_segment_count must match rows")
    if report.pass_segment_count != _count_decimal(
        sum(1 for row in report.segment_rows if row.pressure_status == "pass"),
    ):
        raise ValueError("pass_segment_count must match rows")
    if report.total_miner_reserve_btc != _sum_decimal(
        row.miner_reserve_btc for row in report.segment_rows
    ):
        raise ValueError("total_miner_reserve_btc must match rows")
    if report.max_pressure_score != max(
        (row.pressure_score for row in report.segment_rows),
        default=ZERO,
    ):
        raise ValueError("max_pressure_score must match rows")
    if report.average_pressure_score != _ratio(
        _sum_decimal(row.pressure_score for row in report.segment_rows),
        report.observation_count,
    ):
        raise ValueError("average_pressure_score must match rows")
    if report.blocked_observation_ratio != _ratio(
        report.blocked_segment_count,
        report.observation_count,
    ):
        raise ValueError("blocked_observation_ratio must match rows")
    if report.digest_status != _digest_status(report.segment_rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.segment_rows):
        raise ValueError("reason_codes must match rows")
    row_reason_codes = tuple(
        reason_code for row in report.segment_rows for reason_code in row.reason_codes
    )
    if report.reason_code_counts != _reason_code_counts(
        row_reason_codes,
        report.observation_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[BitcoinHalvingSupplyPressureObservation],
) -> tuple[BitcoinHalvingSupplyPressureObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError(
            "inputs must contain BitcoinHalvingSupplyPressureObservation values",
        )
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must contain BitcoinHalvingSupplyPressureObservation values",
        ) from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not BitcoinHalvingSupplyPressureObservation:
            raise ValueError(
                "inputs must contain BitcoinHalvingSupplyPressureObservation",
            )
        _require_hard_flags("observation", item)
        if item.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id values")
        seen.add(item.source_id)
    return normalized


def _normalize_rows(value: object) -> tuple[BitcoinHalvingSupplyPressureDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("segment_rows must contain Bitcoin halving pressure rows")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("segment_rows must contain Bitcoin halving pressure rows") from exc
    for row in rows:
        if type(row) is not BitcoinHalvingSupplyPressureDigestRow:
            raise ValueError(
                "segment_rows must contain BitcoinHalvingSupplyPressureDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("segment_rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("segment_rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[BitcoinHalvingSupplyPressureReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in counts:
        if type(item) is not BitcoinHalvingSupplyPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "BitcoinHalvingSupplyPressureReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    allowed = ROW_REASON_CODES + REPORT_REASON_CODES
    if counts != tuple(sorted(counts, key=lambda item: allowed.index(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if normalized != tuple(
        sorted(normalized, key=lambda reason_code: allowed.index(reason_code))
    ):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: BitcoinHalvingSupplyPressureDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.pressure_status],
        -row.pressure_score,
        row.miner_cohort_id,
        row.source_id,
    )


def _json_ready(value: object) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
