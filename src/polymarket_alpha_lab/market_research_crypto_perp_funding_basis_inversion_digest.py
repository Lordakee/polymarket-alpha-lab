"""Pure Phase 1 crypto perp funding basis inversion market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_FUNDING_BASIS_INVERSION_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-perp-funding-basis-inversion-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
PERP_FUNDING_BASIS_INVERSION_DIGEST_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCKED,
)

PASS_REASON = "market_research_crypto_perp_funding_basis_inversion_digest_pass"
NO_INPUTS_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_no_inputs"
)
INVERSION_PRESSURE_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_inversion_pressure"
)
PERP_FUNDING_RATE_PRESSURE_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_"
    "perp_funding_rate_pressure"
)
SPOT_PERP_BASIS_PRESSURE_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_"
    "spot_perp_basis_pressure"
)
OPEN_INTEREST_ACCELERATION_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_"
    "open_interest_acceleration"
)
LIQUIDATION_PRESSURE_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_liquidation_pressure"
)
BORROW_STABLECOIN_FUNDING_STRESS_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_"
    "borrow_stablecoin_funding_stress"
)
UPSTREAM_REASON_SIGNAL_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_upstream_reason_signal"
)
STALE_SOURCE_TIMESTAMP_REASON = (
    "market_research_crypto_perp_funding_basis_inversion_digest_stale_source_timestamp"
)

REASON_CODE_SEQUENCE = (
    INVERSION_PRESSURE_REASON,
    PERP_FUNDING_RATE_PRESSURE_REASON,
    SPOT_PERP_BASIS_PRESSURE_REASON,
    OPEN_INTEREST_ACCELERATION_REASON,
    LIQUIDATION_PRESSURE_REASON,
    BORROW_STABLECOIN_FUNDING_STRESS_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    STALE_SOURCE_TIMESTAMP_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    INVERSION_PRESSURE_REASON,
    PERP_FUNDING_RATE_PRESSURE_REASON,
    SPOT_PERP_BASIS_PRESSURE_REASON,
    OPEN_INTEREST_ACCELERATION_REASON,
    LIQUIDATION_PRESSURE_REASON,
    BORROW_STABLECOIN_FUNDING_STRESS_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    STALE_SOURCE_TIMESTAMP_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

INVERSION_RISK_WEIGHT = Decimal("0.300000")
PERP_FUNDING_RATE_RISK_WEIGHT = Decimal("0.200000")
SPOT_PERP_BASIS_RISK_WEIGHT = Decimal("0.150000")
OPEN_INTEREST_CHANGE_RISK_WEIGHT = Decimal("0.150000")
LIQUIDATION_PRESSURE_RISK_WEIGHT = Decimal("0.100000")
BORROW_STRESS_RISK_WEIGHT = Decimal("0.100000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("wa", "llet"),
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("tr", "ade"),
        _join_parts("tra", "ding"),
        _join_parts("bro", "ker"),
        _join_parts("sign", "ing"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_FUNDING_BASIS_INVERSION_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoPerpFundingBasisInversionDigestConfig",
    "MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount",
    "MarketResearchCryptoPerpFundingBasisInversionDigestReport",
    "MarketResearchCryptoPerpFundingBasisInversionDigestRow",
    "MarketResearchCryptoPerpFundingBasisInversionSnapshot",
    "build_market_research_crypto_perp_funding_basis_inversion_digest",
    "market_research_crypto_perp_funding_basis_inversion_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoPerpFundingBasisInversionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_FUNDING_BASIS_INVERSION_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    watch_perp_funding_rate_abs: Decimal = Decimal("0.000500")
    blocked_perp_funding_rate_abs: Decimal = Decimal("0.002000")
    watch_spot_perp_basis_abs: Decimal = Decimal("0.002500")
    blocked_spot_perp_basis_abs: Decimal = Decimal("0.010000")
    watch_open_interest_change_abs: Decimal = Decimal("0.080000")
    blocked_open_interest_change_abs: Decimal = Decimal("0.200000")
    watch_liquidation_pressure: Decimal = Decimal("0.300000")
    blocked_liquidation_pressure: Decimal = Decimal("0.600000")
    watch_borrow_stablecoin_funding_stress: Decimal = Decimal("0.250000")
    blocked_borrow_stablecoin_funding_stress: Decimal = Decimal("0.500000")
    watch_risk_score: Decimal = Decimal("0.350000")
    blocked_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpFundingBasisInversionDigestConfig:
            raise TypeError(
                "MarketResearchCryptoPerpFundingBasisInversionDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoPerpFundingBasisInversionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoPerpFundingBasisInversionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_snapshot_age_seconds",
            _require_positive_count_decimal(
                "max_snapshot_age_seconds",
                self.max_snapshot_age_seconds,
            ),
        )
        for field_name in (
            "watch_perp_funding_rate_abs",
            "blocked_perp_funding_rate_abs",
            "watch_spot_perp_basis_abs",
            "blocked_spot_perp_basis_abs",
            "watch_open_interest_change_abs",
            "blocked_open_interest_change_abs",
            "watch_liquidation_pressure",
            "blocked_liquidation_pressure",
            "watch_borrow_stablecoin_funding_stress",
            "blocked_borrow_stablecoin_funding_stress",
            "watch_risk_score",
            "blocked_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "watch_perp_funding_rate_abs",
            self.watch_perp_funding_rate_abs,
            "blocked_perp_funding_rate_abs",
            self.blocked_perp_funding_rate_abs,
        )
        _require_ordered_thresholds(
            "watch_spot_perp_basis_abs",
            self.watch_spot_perp_basis_abs,
            "blocked_spot_perp_basis_abs",
            self.blocked_spot_perp_basis_abs,
        )
        _require_ordered_thresholds(
            "watch_open_interest_change_abs",
            self.watch_open_interest_change_abs,
            "blocked_open_interest_change_abs",
            self.blocked_open_interest_change_abs,
        )
        _require_ordered_thresholds(
            "watch_liquidation_pressure",
            self.watch_liquidation_pressure,
            "blocked_liquidation_pressure",
            self.blocked_liquidation_pressure,
        )
        _require_ordered_thresholds(
            "watch_borrow_stablecoin_funding_stress",
            self.watch_borrow_stablecoin_funding_stress,
            "blocked_borrow_stablecoin_funding_stress",
            self.blocked_borrow_stablecoin_funding_stress,
        )
        _require_ordered_thresholds(
            "watch_risk_score",
            self.watch_risk_score,
            "blocked_risk_score",
            self.blocked_risk_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoPerpFundingBasisInversionSnapshot:
    exchange: str
    asset_symbol: str
    market_slug: str
    source_timestamp: datetime
    perp_funding_rate: Decimal
    spot_perp_basis: Decimal
    open_interest_change_ratio: Decimal
    liquidation_pressure_ratio: Decimal
    borrow_stablecoin_funding_stress: Decimal
    upstream_reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpFundingBasisInversionSnapshot:
            raise TypeError(
                "MarketResearchCryptoPerpFundingBasisInversionSnapshot does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoPerpFundingBasisInversionSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoPerpFundingBasisInversionSnapshot",
            )
        for field_name in (
            "exchange",
            "asset_symbol",
            "market_slug",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        for field_name in (
            "perp_funding_rate",
            "spot_perp_basis",
            "open_interest_change_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidation_pressure_ratio",
            "borrow_stablecoin_funding_stress",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoPerpFundingBasisInversionDigestRow:
    exchange: str
    asset_symbol: str
    market_slug: str
    digest_status: str
    source_timestamp: datetime
    snapshot_age_seconds: Decimal
    perp_funding_rate: Decimal
    perp_funding_rate_abs: Decimal
    spot_perp_basis: Decimal
    spot_perp_basis_abs: Decimal
    funding_basis_inverted: bool
    open_interest_change_ratio: Decimal
    open_interest_change_abs: Decimal
    liquidation_pressure_ratio: Decimal
    borrow_stablecoin_funding_stress: Decimal
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpFundingBasisInversionDigestRow:
            raise TypeError(
                "MarketResearchCryptoPerpFundingBasisInversionDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoPerpFundingBasisInversionDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoPerpFundingBasisInversionDigestRow",
            )
        for field_name in ("exchange", "asset_symbol", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_count_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        for field_name in (
            "perp_funding_rate",
            "spot_perp_basis",
            "open_interest_change_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "perp_funding_rate_abs",
            "spot_perp_basis_abs",
            "open_interest_change_abs",
            "liquidation_pressure_ratio",
            "borrow_stablecoin_funding_stress",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.funding_basis_inverted) is not bool:
            raise ValueError("funding_basis_inverted must be a bool")
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoPerpFundingBasisInversionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    pass_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    inversion_snapshot_count: Decimal
    perp_funding_rate_pressure_snapshot_count: Decimal
    spot_perp_basis_pressure_snapshot_count: Decimal
    open_interest_acceleration_snapshot_count: Decimal
    liquidation_pressure_snapshot_count: Decimal
    borrow_stablecoin_funding_stress_snapshot_count: Decimal
    upstream_reason_signal_snapshot_count: Decimal
    stale_source_timestamp_snapshot_count: Decimal
    average_perp_funding_rate: Decimal
    average_spot_perp_basis: Decimal
    average_open_interest_change_ratio: Decimal
    average_liquidation_pressure_ratio: Decimal
    average_borrow_stablecoin_funding_stress: Decimal
    average_risk_score: Decimal
    max_risk_score: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    watch_perp_funding_rate_abs: Decimal
    blocked_perp_funding_rate_abs: Decimal
    watch_spot_perp_basis_abs: Decimal
    blocked_spot_perp_basis_abs: Decimal
    watch_open_interest_change_abs: Decimal
    blocked_open_interest_change_abs: Decimal
    watch_liquidation_pressure: Decimal
    blocked_liquidation_pressure: Decimal
    watch_borrow_stablecoin_funding_stress: Decimal
    blocked_borrow_stablecoin_funding_stress: Decimal
    watch_risk_score: Decimal
    blocked_risk_score: Decimal
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...]
    source_config_versions: tuple[tuple[tuple[str, str, str], str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpFundingBasisInversionDigestReport:
            raise TypeError(
                "MarketResearchCryptoPerpFundingBasisInversionDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoPerpFundingBasisInversionDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoPerpFundingBasisInversionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "pass_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "inversion_snapshot_count",
            "perp_funding_rate_pressure_snapshot_count",
            "spot_perp_basis_pressure_snapshot_count",
            "open_interest_acceleration_snapshot_count",
            "liquidation_pressure_snapshot_count",
            "borrow_stablecoin_funding_stress_snapshot_count",
            "upstream_reason_signal_snapshot_count",
            "stale_source_timestamp_snapshot_count",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_perp_funding_rate",
            "average_spot_perp_basis",
            "average_open_interest_change_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_liquidation_pressure_ratio",
            "average_borrow_stablecoin_funding_stress",
            "average_risk_score",
            "max_risk_score",
            "watch_perp_funding_rate_abs",
            "blocked_perp_funding_rate_abs",
            "watch_spot_perp_basis_abs",
            "blocked_spot_perp_basis_abs",
            "watch_open_interest_change_abs",
            "blocked_open_interest_change_abs",
            "watch_liquidation_pressure",
            "blocked_liquidation_pressure",
            "watch_borrow_stablecoin_funding_stress",
            "blocked_borrow_stablecoin_funding_stress",
            "watch_risk_score",
            "blocked_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_perp_funding_basis_inversion_digest(
    snapshots: Iterable[MarketResearchCryptoPerpFundingBasisInversionSnapshot],
    *,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoPerpFundingBasisInversionDigestReport:
    cfg = config or MarketResearchCryptoPerpFundingBasisInversionDigestConfig()
    if type(cfg) is not MarketResearchCryptoPerpFundingBasisInversionDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoPerpFundingBasisInversionDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        _row_for_snapshot(snapshot, config=cfg, generated_at=generated_at_utc)
        for snapshot in normalized_snapshots
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.exchange,
                row.asset_symbol,
                row.market_slug,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoPerpFundingBasisInversionDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        pass_snapshot_count=_status_count(sorted_rows, STATUS_PASS),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        inversion_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            INVERSION_PRESSURE_REASON,
        ),
        perp_funding_rate_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PERP_FUNDING_RATE_PRESSURE_REASON,
        ),
        spot_perp_basis_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SPOT_PERP_BASIS_PRESSURE_REASON,
        ),
        open_interest_acceleration_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            OPEN_INTEREST_ACCELERATION_REASON,
        ),
        liquidation_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            LIQUIDATION_PRESSURE_REASON,
        ),
        borrow_stablecoin_funding_stress_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            BORROW_STABLECOIN_FUNDING_STRESS_REASON,
        ),
        upstream_reason_signal_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            UPSTREAM_REASON_SIGNAL_REASON,
        ),
        stale_source_timestamp_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            STALE_SOURCE_TIMESTAMP_REASON,
        ),
        average_perp_funding_rate=_ratio(
            _decimal_sum(row.perp_funding_rate for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_spot_perp_basis=_ratio(
            _decimal_sum(row.spot_perp_basis for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_open_interest_change_ratio=_ratio(
            _decimal_sum(row.open_interest_change_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_liquidation_pressure_ratio=_ratio(
            _decimal_sum(row.liquidation_pressure_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_borrow_stablecoin_funding_stress=_ratio(
            _decimal_sum(row.borrow_stablecoin_funding_stress for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_risk_score=_ratio(
            _decimal_sum(row.risk_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_risk_score=max((row.risk_score for row in sorted_rows), default=ZERO),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        watch_perp_funding_rate_abs=cfg.watch_perp_funding_rate_abs,
        blocked_perp_funding_rate_abs=cfg.blocked_perp_funding_rate_abs,
        watch_spot_perp_basis_abs=cfg.watch_spot_perp_basis_abs,
        blocked_spot_perp_basis_abs=cfg.blocked_spot_perp_basis_abs,
        watch_open_interest_change_abs=cfg.watch_open_interest_change_abs,
        blocked_open_interest_change_abs=cfg.blocked_open_interest_change_abs,
        watch_liquidation_pressure=cfg.watch_liquidation_pressure,
        blocked_liquidation_pressure=cfg.blocked_liquidation_pressure,
        watch_borrow_stablecoin_funding_stress=(
            cfg.watch_borrow_stablecoin_funding_stress
        ),
        blocked_borrow_stablecoin_funding_stress=(
            cfg.blocked_borrow_stablecoin_funding_stress
        ),
        watch_risk_score=cfg.watch_risk_score,
        blocked_risk_score=cfg.blocked_risk_score,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (
                    (snapshot.exchange, snapshot.asset_symbol, snapshot.market_slug),
                    snapshot.source_config_version,
                )
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_perp_funding_basis_inversion_digest_payload(
    report: MarketResearchCryptoPerpFundingBasisInversionDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoPerpFundingBasisInversionDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoPerpFundingBasisInversionDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoPerpFundingBasisInversionSnapshot,
    *,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoPerpFundingBasisInversionDigestRow:
    if snapshot.source_timestamp > generated_at:
        raise ValueError("source_timestamp must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.source_timestamp)
    perp_funding_rate_abs = _ratio_abs(snapshot.perp_funding_rate)
    spot_perp_basis_abs = _ratio_abs(snapshot.spot_perp_basis)
    open_interest_change_abs = _ratio_abs(snapshot.open_interest_change_ratio)
    funding_basis_inverted = _signs_inverted(
        snapshot.perp_funding_rate,
        snapshot.spot_perp_basis,
    )
    inversion_pressure = funding_basis_inverted and (
        perp_funding_rate_abs >= config.watch_perp_funding_rate_abs
        and spot_perp_basis_abs >= config.watch_spot_perp_basis_abs
    )
    risk_score = _risk_score(
        snapshot=snapshot,
        config=config,
        funding_basis_inverted=inversion_pressure,
        perp_funding_rate_abs=perp_funding_rate_abs,
        spot_perp_basis_abs=spot_perp_basis_abs,
        open_interest_change_abs=open_interest_change_abs,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        funding_basis_inverted=inversion_pressure,
        perp_funding_rate_abs=perp_funding_rate_abs,
        spot_perp_basis_abs=spot_perp_basis_abs,
        open_interest_change_abs=open_interest_change_abs,
    )
    return MarketResearchCryptoPerpFundingBasisInversionDigestRow(
        exchange=snapshot.exchange,
        asset_symbol=snapshot.asset_symbol,
        market_slug=snapshot.market_slug,
        digest_status=_row_status(reason_codes, risk_score, config=config),
        source_timestamp=snapshot.source_timestamp,
        snapshot_age_seconds=snapshot_age_seconds,
        perp_funding_rate=snapshot.perp_funding_rate,
        perp_funding_rate_abs=perp_funding_rate_abs,
        spot_perp_basis=snapshot.spot_perp_basis,
        spot_perp_basis_abs=spot_perp_basis_abs,
        funding_basis_inverted=funding_basis_inverted,
        open_interest_change_ratio=snapshot.open_interest_change_ratio,
        open_interest_change_abs=open_interest_change_abs,
        liquidation_pressure_ratio=snapshot.liquidation_pressure_ratio,
        borrow_stablecoin_funding_stress=snapshot.borrow_stablecoin_funding_stress,
        risk_score=risk_score,
        upstream_reason_codes=snapshot.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoPerpFundingBasisInversionSnapshot,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig,
    snapshot_age_seconds: Decimal,
    funding_basis_inverted: bool,
    perp_funding_rate_abs: Decimal,
    spot_perp_basis_abs: Decimal,
    open_interest_change_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if funding_basis_inverted:
        reasons.append(INVERSION_PRESSURE_REASON)
    if perp_funding_rate_abs >= config.watch_perp_funding_rate_abs:
        reasons.append(PERP_FUNDING_RATE_PRESSURE_REASON)
    if spot_perp_basis_abs >= config.watch_spot_perp_basis_abs:
        reasons.append(SPOT_PERP_BASIS_PRESSURE_REASON)
    if open_interest_change_abs >= config.watch_open_interest_change_abs:
        reasons.append(OPEN_INTEREST_ACCELERATION_REASON)
    if snapshot.liquidation_pressure_ratio >= config.watch_liquidation_pressure:
        reasons.append(LIQUIDATION_PRESSURE_REASON)
    if (
        snapshot.borrow_stablecoin_funding_stress
        >= config.watch_borrow_stablecoin_funding_stress
    ):
        reasons.append(BORROW_STABLECOIN_FUNDING_STRESS_REASON)
    if snapshot.upstream_reason_codes:
        reasons.append(UPSTREAM_REASON_SIGNAL_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(STALE_SOURCE_TIMESTAMP_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _risk_score(
    *,
    snapshot: MarketResearchCryptoPerpFundingBasisInversionSnapshot,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig,
    funding_basis_inverted: bool,
    perp_funding_rate_abs: Decimal,
    spot_perp_basis_abs: Decimal,
    open_interest_change_abs: Decimal,
) -> Decimal:
    score = INVERSION_RISK_WEIGHT if funding_basis_inverted else ZERO
    score = _quantize(
        score
        + _weighted_ratio(
            perp_funding_rate_abs,
            config.blocked_perp_funding_rate_abs,
            PERP_FUNDING_RATE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            spot_perp_basis_abs,
            config.blocked_spot_perp_basis_abs,
            SPOT_PERP_BASIS_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            open_interest_change_abs,
            config.blocked_open_interest_change_abs,
            OPEN_INTEREST_CHANGE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            snapshot.liquidation_pressure_ratio,
            config.blocked_liquidation_pressure,
            LIQUIDATION_PRESSURE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            snapshot.borrow_stablecoin_funding_stress,
            config.blocked_borrow_stablecoin_funding_stress,
            BORROW_STRESS_RISK_WEIGHT,
        ),
    )
    if score > ONE:
        return ONE
    return score


def _weighted_ratio(value: Decimal, denominator: Decimal, weight: Decimal) -> Decimal:
    return _quantize(_capped_ratio(value, denominator) * weight)


def _capped_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    ratio = _ratio(value, denominator)
    if ratio > ONE:
        return ONE
    return ratio


def _signs_inverted(first: Decimal, second: Decimal) -> bool:
    return (first < ZERO and second > ZERO) or (first > ZERO and second < ZERO)


def _row_status(
    reason_codes: tuple[str, ...],
    risk_score: Decimal,
    *,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig,
) -> str:
    if STALE_SOURCE_TIMESTAMP_REASON in reason_codes or risk_score >= config.blocked_risk_score:
        return STATUS_BLOCKED
    if risk_score >= config.watch_risk_score or reason_codes != (PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_value(
    row: MarketResearchCryptoPerpFundingBasisInversionDigestRow,
) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[row.digest_status]
    return (status_rank, -row.risk_score)


def _report_status(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_perp_funding_basis_inversion_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_perp_funding_basis_inversion_digest"
    return "allow_report_only_market_research_crypto_perp_funding_basis_inversion_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
) -> tuple[MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and PASS_REASON in seen:
        seen.remove(PASS_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoPerpFundingBasisInversionDigestRow) -> None:
    if row.perp_funding_rate_abs != _ratio_abs(row.perp_funding_rate):
        raise ValueError("perp_funding_rate_abs does not match perp_funding_rate")
    if row.spot_perp_basis_abs != _ratio_abs(row.spot_perp_basis):
        raise ValueError("spot_perp_basis_abs does not match spot_perp_basis")
    if row.open_interest_change_abs != _ratio_abs(row.open_interest_change_ratio):
        raise ValueError("open_interest_change_abs does not match open_interest_change_ratio")
    if row.funding_basis_inverted != _signs_inverted(
        row.perp_funding_rate,
        row.spot_perp_basis,
    ):
        raise ValueError("funding_basis_inverted does not match funding and basis signs")


def _validate_report(
    report: MarketResearchCryptoPerpFundingBasisInversionDigestReport,
) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.pass_snapshot_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (INVERSION_PRESSURE_REASON, report.inversion_snapshot_count),
        (
            PERP_FUNDING_RATE_PRESSURE_REASON,
            report.perp_funding_rate_pressure_snapshot_count,
        ),
        (
            SPOT_PERP_BASIS_PRESSURE_REASON,
            report.spot_perp_basis_pressure_snapshot_count,
        ),
        (
            OPEN_INTEREST_ACCELERATION_REASON,
            report.open_interest_acceleration_snapshot_count,
        ),
        (LIQUIDATION_PRESSURE_REASON, report.liquidation_pressure_snapshot_count),
        (
            BORROW_STABLECOIN_FUNDING_STRESS_REASON,
            report.borrow_stablecoin_funding_stress_snapshot_count,
        ),
        (UPSTREAM_REASON_SIGNAL_REASON, report.upstream_reason_signal_snapshot_count),
        (
            STALE_SOURCE_TIMESTAMP_REASON,
            report.stale_source_timestamp_snapshot_count,
        ),
    )
    for reason_code, count in expected_counts:
        if count != _reason_snapshot_count(report.rows, reason_code):
            raise ValueError("reason snapshot count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_perp_funding_rate != _ratio(
        _decimal_sum(row.perp_funding_rate for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_perp_funding_rate does not match rows")
    if report.average_spot_perp_basis != _ratio(
        _decimal_sum(row.spot_perp_basis for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_spot_perp_basis does not match rows")
    if report.average_open_interest_change_ratio != _ratio(
        _decimal_sum(row.open_interest_change_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_open_interest_change_ratio does not match rows")
    if report.average_liquidation_pressure_ratio != _ratio(
        _decimal_sum(row.liquidation_pressure_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_liquidation_pressure_ratio does not match rows")
    if report.average_borrow_stablecoin_funding_stress != _ratio(
        _decimal_sum(row.borrow_stablecoin_funding_stress for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_borrow_stablecoin_funding_stress does not match rows")
    if report.average_risk_score != _ratio(
        _decimal_sum(row.risk_score for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_risk_score does not match rows")
    if report.max_risk_score != max((row.risk_score for row in report.rows), default=ZERO):
        raise ValueError("max_risk_score does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoPerpFundingBasisInversionSnapshot],
) -> tuple[MarketResearchCryptoPerpFundingBasisInversionSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_keys: set[tuple[str, str, str]] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoPerpFundingBasisInversionSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoPerpFundingBasisInversionSnapshot",
            )
        snapshot_key = (snapshot.exchange, snapshot.asset_symbol, snapshot.market_slug)
        if snapshot_key in seen_keys:
            raise ValueError("snapshot exchange asset_symbol market_slug values must be unique")
        seen_keys.add(snapshot_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...],
) -> tuple[MarketResearchCryptoPerpFundingBasisInversionDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoPerpFundingBasisInversionDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchCryptoPerpFundingBasisInversionDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.exchange,
                row.asset_symbol,
                row.market_slug,
            ),
        ),
    ):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if (
            type(item)
            is not MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount
        ):
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", item)
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[tuple[str, str, str], str], ...],
) -> tuple[tuple[tuple[str, str, str], str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[tuple[str, str, str], str]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        snapshot_key, source_config_version = item
        if type(snapshot_key) is not tuple or len(snapshot_key) != 3:
            raise ValueError("source_config_versions must contain snapshot keys")
        exchange, asset_symbol, market_slug = snapshot_key
        _require_public_string("exchange", exchange)
        _require_public_string("asset_symbol", asset_symbol)
        _require_public_string("market_slug", market_slug)
        _require_public_string("source_config_version", source_config_version)
        if snapshot_key in seen_keys:
            raise ValueError("source_config_versions snapshot keys must be unique")
        seen_keys.add(snapshot_key)
        pairs.append((snapshot_key, source_config_version))
    normalized = tuple(sorted(pairs))
    if normalized != value:
        raise ValueError("source_config_versions must be deterministic")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("upstream_reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_string("upstream_reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("upstream_reason_codes must be unique")
        seen.add(reason_code)
    return tuple(sorted(seen))


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in PERP_FUNDING_BASIS_INVERSION_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _require_public_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_ordered_thresholds(
    watch_field_name: str,
    watch_value: Decimal,
    blocked_field_name: str,
    blocked_value: Decimal,
) -> None:
    if watch_value >= blocked_value:
        raise ValueError(f"{watch_field_name} must be less than {blocked_field_name}")


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_ratio_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, source_timestamp: datetime) -> Decimal:
    delta = generated_at - source_timestamp
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        return {str(item_key): _json_ready(item_value) for item_key, item_value in value.items()}
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {item_key: _freeze(item_value) for item_key, item_value in value.items()},
        )
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
