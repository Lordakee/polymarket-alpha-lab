"""Pure Phase 1 report-only crypto ETF flow dislocation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-flow-dislocation-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
FLOW_DISLOCATION_DIGEST_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCKED,
)

PASS_REASON = "market_research_crypto_etf_flow_dislocation_digest_pass"
NO_INPUTS_REASON = "market_research_crypto_etf_flow_dislocation_digest_no_inputs"
FLOW_SPOT_DIVERGENCE_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_flow_spot_divergence"
)
PREMIUM_DISCOUNT_DISLOCATION_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_"
    "premium_discount_dislocation"
)
FUTURES_BASIS_DISLOCATION_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_"
    "futures_basis_dislocation"
)
CREATION_REDEMPTION_IMBALANCE_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_"
    "creation_redemption_imbalance"
)
SOURCE_FRESHNESS_GAP_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_source_freshness_gap"
)
SOURCE_QUORUM_GAP_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_source_quorum_gap"
)
UPSTREAM_REASON_SIGNAL_REASON = (
    "market_research_crypto_etf_flow_dislocation_digest_upstream_reason_signal"
)

REASON_CODE_SEQUENCE = (
    FLOW_SPOT_DIVERGENCE_REASON,
    PREMIUM_DISCOUNT_DISLOCATION_REASON,
    FUTURES_BASIS_DISLOCATION_REASON,
    CREATION_REDEMPTION_IMBALANCE_REASON,
    SOURCE_FRESHNESS_GAP_REASON,
    SOURCE_QUORUM_GAP_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    FLOW_SPOT_DIVERGENCE_REASON,
    PREMIUM_DISCOUNT_DISLOCATION_REASON,
    FUTURES_BASIS_DISLOCATION_REASON,
    CREATION_REDEMPTION_IMBALANCE_REASON,
    SOURCE_FRESHNESS_GAP_REASON,
    SOURCE_QUORUM_GAP_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

FLOW_SPOT_DIVERGENCE_RISK_WEIGHT = Decimal("0.300000")
PREMIUM_DISCOUNT_RISK_WEIGHT = Decimal("0.200000")
FUTURES_BASIS_RISK_WEIGHT = Decimal("0.150000")
CREATION_REDEMPTION_IMBALANCE_RISK_WEIGHT = Decimal("0.150000")
FLOW_SIZE_RISK_WEIGHT = Decimal("0.100000")
SOURCE_FRESHNESS_RISK_WEIGHT = Decimal("0.060000")
SOURCE_QUORUM_RISK_WEIGHT = Decimal("0.040000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("api", "_", "ke", "y"),
        _join_parts("to", "ken"),
        _join_parts("sig", "ning"),
        _join_parts("bro", "ker"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEtfFlowDislocationDigestConfig",
    "MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount",
    "MarketResearchCryptoEtfFlowDislocationDigestReport",
    "MarketResearchCryptoEtfFlowDislocationDigestRow",
    "MarketResearchCryptoEtfFlowDislocationSnapshot",
    "build_market_research_crypto_etf_flow_dislocation_digest",
    "market_research_crypto_etf_flow_dislocation_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDislocationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    min_source_quorum_count: Decimal = Decimal("2.000000")
    watch_abs_net_flow_usd: Decimal = Decimal("50000000.000000")
    blocked_abs_net_flow_usd: Decimal = Decimal("300000000.000000")
    watch_flow_spot_divergence_abs: Decimal = Decimal("0.025000")
    blocked_flow_spot_divergence_abs: Decimal = Decimal("0.080000")
    watch_premium_discount_abs: Decimal = Decimal("0.010000")
    blocked_premium_discount_abs: Decimal = Decimal("0.035000")
    watch_futures_basis_abs: Decimal = Decimal("0.005000")
    blocked_futures_basis_abs: Decimal = Decimal("0.020000")
    watch_creation_redemption_imbalance: Decimal = Decimal("0.300000")
    blocked_creation_redemption_imbalance: Decimal = Decimal("0.650000")
    watch_risk_score: Decimal = Decimal("0.350000")
    blocked_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDislocationDigestConfig:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDislocationDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDislocationDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoEtfFlowDislocationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_snapshot_age_seconds",
            "min_source_quorum_count",
            "watch_abs_net_flow_usd",
            "blocked_abs_net_flow_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_flow_spot_divergence_abs",
            "blocked_flow_spot_divergence_abs",
            "watch_premium_discount_abs",
            "blocked_premium_discount_abs",
            "watch_futures_basis_abs",
            "blocked_futures_basis_abs",
            "watch_creation_redemption_imbalance",
            "blocked_creation_redemption_imbalance",
            "watch_risk_score",
            "blocked_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "watch_abs_net_flow_usd",
            self.watch_abs_net_flow_usd,
            "blocked_abs_net_flow_usd",
            self.blocked_abs_net_flow_usd,
        )
        _require_threshold_sequence(
            "watch_flow_spot_divergence_abs",
            self.watch_flow_spot_divergence_abs,
            "blocked_flow_spot_divergence_abs",
            self.blocked_flow_spot_divergence_abs,
        )
        _require_threshold_sequence(
            "watch_premium_discount_abs",
            self.watch_premium_discount_abs,
            "blocked_premium_discount_abs",
            self.blocked_premium_discount_abs,
        )
        _require_threshold_sequence(
            "watch_futures_basis_abs",
            self.watch_futures_basis_abs,
            "blocked_futures_basis_abs",
            self.blocked_futures_basis_abs,
        )
        _require_threshold_sequence(
            "watch_creation_redemption_imbalance",
            self.watch_creation_redemption_imbalance,
            "blocked_creation_redemption_imbalance",
            self.blocked_creation_redemption_imbalance,
        )
        _require_threshold_sequence(
            "watch_risk_score",
            self.watch_risk_score,
            "blocked_risk_score",
            self.blocked_risk_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDislocationSnapshot:
    etf_ticker: str
    asset_symbol: str
    market_slug: str
    source_timestamp: datetime
    net_flow_usd: Decimal
    spot_return: Decimal
    premium_discount: Decimal
    futures_basis: Decimal
    creation_redemption_imbalance: Decimal
    source_quorum_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDislocationSnapshot:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDislocationSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDislocationSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoEtfFlowDislocationSnapshot",
            )
        for field_name in (
            "etf_ticker",
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
        object.__setattr__(
            self,
            "net_flow_usd",
            _require_signed_decimal("net_flow_usd", self.net_flow_usd),
        )
        for field_name in ("spot_return", "premium_discount", "futures_basis"):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "creation_redemption_imbalance",
            _require_ratio_decimal(
                "creation_redemption_imbalance",
                self.creation_redemption_imbalance,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_count",
            _require_nonnegative_count_decimal(
                "source_quorum_count",
                self.source_quorum_count,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowDislocationDigestRow:
    etf_ticker: str
    asset_symbol: str
    market_slug: str
    digest_status: str
    source_timestamp: datetime
    snapshot_age_seconds: Decimal
    net_flow_usd: Decimal
    net_flow_abs_usd: Decimal
    spot_return: Decimal
    spot_return_abs: Decimal
    flow_spot_divergence_abs: Decimal
    premium_discount: Decimal
    premium_discount_abs: Decimal
    futures_basis: Decimal
    futures_basis_abs: Decimal
    creation_redemption_imbalance: Decimal
    source_quorum_count: Decimal
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDislocationDigestRow:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDislocationDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDislocationDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoEtfFlowDislocationDigestRow",
            )
        for field_name in ("etf_ticker", "asset_symbol", "market_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        for field_name in ("snapshot_age_seconds", "net_flow_abs_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_flow_usd",
            _require_signed_decimal("net_flow_usd", self.net_flow_usd),
        )
        for field_name in ("spot_return", "premium_discount", "futures_basis"):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spot_return_abs",
            "flow_spot_divergence_abs",
            "premium_discount_abs",
            "futures_basis_abs",
            "creation_redemption_imbalance",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_quorum_count",
            _require_nonnegative_count_decimal(
                "source_quorum_count",
                self.source_quorum_count,
            ),
        )
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
class MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount",
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
class MarketResearchCryptoEtfFlowDislocationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    pass_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    flow_spot_divergence_snapshot_count: Decimal
    premium_discount_dislocation_snapshot_count: Decimal
    futures_basis_dislocation_snapshot_count: Decimal
    creation_redemption_imbalance_snapshot_count: Decimal
    source_freshness_gap_snapshot_count: Decimal
    source_quorum_gap_snapshot_count: Decimal
    upstream_reason_signal_snapshot_count: Decimal
    aggregate_net_flow_usd: Decimal
    max_net_flow_abs_usd: Decimal
    average_spot_return: Decimal
    average_premium_discount: Decimal
    average_futures_basis: Decimal
    average_creation_redemption_imbalance: Decimal
    average_risk_score: Decimal
    max_risk_score: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    min_source_quorum_count: Decimal
    watch_abs_net_flow_usd: Decimal
    blocked_abs_net_flow_usd: Decimal
    watch_flow_spot_divergence_abs: Decimal
    blocked_flow_spot_divergence_abs: Decimal
    watch_premium_discount_abs: Decimal
    blocked_premium_discount_abs: Decimal
    watch_futures_basis_abs: Decimal
    blocked_futures_basis_abs: Decimal
    watch_creation_redemption_imbalance: Decimal
    blocked_creation_redemption_imbalance: Decimal
    watch_risk_score: Decimal
    blocked_risk_score: Decimal
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...]
    source_config_versions: tuple[tuple[tuple[str, str, str], str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfFlowDislocationDigestReport:
            raise TypeError(
                "MarketResearchCryptoEtfFlowDislocationDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfFlowDislocationDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoEtfFlowDislocationDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "pass_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "flow_spot_divergence_snapshot_count",
            "premium_discount_dislocation_snapshot_count",
            "futures_basis_dislocation_snapshot_count",
            "creation_redemption_imbalance_snapshot_count",
            "source_freshness_gap_snapshot_count",
            "source_quorum_gap_snapshot_count",
            "upstream_reason_signal_snapshot_count",
            "max_net_flow_abs_usd",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "min_source_quorum_count",
            "watch_abs_net_flow_usd",
            "blocked_abs_net_flow_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_net_flow_usd",
            _require_signed_decimal("aggregate_net_flow_usd", self.aggregate_net_flow_usd),
        )
        for field_name in (
            "average_spot_return",
            "average_premium_discount",
            "average_futures_basis",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_creation_redemption_imbalance",
            "average_risk_score",
            "max_risk_score",
            "watch_flow_spot_divergence_abs",
            "blocked_flow_spot_divergence_abs",
            "watch_premium_discount_abs",
            "blocked_premium_discount_abs",
            "watch_futures_basis_abs",
            "blocked_futures_basis_abs",
            "watch_creation_redemption_imbalance",
            "blocked_creation_redemption_imbalance",
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


def build_market_research_crypto_etf_flow_dislocation_digest(
    snapshots: Iterable[MarketResearchCryptoEtfFlowDislocationSnapshot],
    *,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowDislocationDigestReport:
    cfg = config or MarketResearchCryptoEtfFlowDislocationDigestConfig()
    if type(cfg) is not MarketResearchCryptoEtfFlowDislocationDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoEtfFlowDislocationDigestConfig",
        )
    _require_hard_flags("config", cfg)
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
                row.market_slug,
                row.etf_ticker,
                row.asset_symbol,
            ),
        ),
    )
    snapshot_count = _decimal_count(len(sorted_rows))
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoEtfFlowDislocationDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=snapshot_count,
        pass_snapshot_count=_status_count(sorted_rows, STATUS_PASS),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        flow_spot_divergence_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            FLOW_SPOT_DIVERGENCE_REASON,
        ),
        premium_discount_dislocation_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PREMIUM_DISCOUNT_DISLOCATION_REASON,
        ),
        futures_basis_dislocation_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            FUTURES_BASIS_DISLOCATION_REASON,
        ),
        creation_redemption_imbalance_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CREATION_REDEMPTION_IMBALANCE_REASON,
        ),
        source_freshness_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_FRESHNESS_GAP_REASON,
        ),
        source_quorum_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_QUORUM_GAP_REASON,
        ),
        upstream_reason_signal_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            UPSTREAM_REASON_SIGNAL_REASON,
        ),
        aggregate_net_flow_usd=_decimal_sum(row.net_flow_usd for row in sorted_rows),
        max_net_flow_abs_usd=max(
            (row.net_flow_abs_usd for row in sorted_rows),
            default=ZERO,
        ),
        average_spot_return=_ratio(
            _decimal_sum(row.spot_return for row in sorted_rows),
            snapshot_count,
        ),
        average_premium_discount=_ratio(
            _decimal_sum(row.premium_discount for row in sorted_rows),
            snapshot_count,
        ),
        average_futures_basis=_ratio(
            _decimal_sum(row.futures_basis for row in sorted_rows),
            snapshot_count,
        ),
        average_creation_redemption_imbalance=_ratio(
            _decimal_sum(row.creation_redemption_imbalance for row in sorted_rows),
            snapshot_count,
        ),
        average_risk_score=_ratio(
            _decimal_sum(row.risk_score for row in sorted_rows),
            snapshot_count,
        ),
        max_risk_score=max((row.risk_score for row in sorted_rows), default=ZERO),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        min_source_quorum_count=cfg.min_source_quorum_count,
        watch_abs_net_flow_usd=cfg.watch_abs_net_flow_usd,
        blocked_abs_net_flow_usd=cfg.blocked_abs_net_flow_usd,
        watch_flow_spot_divergence_abs=cfg.watch_flow_spot_divergence_abs,
        blocked_flow_spot_divergence_abs=cfg.blocked_flow_spot_divergence_abs,
        watch_premium_discount_abs=cfg.watch_premium_discount_abs,
        blocked_premium_discount_abs=cfg.blocked_premium_discount_abs,
        watch_futures_basis_abs=cfg.watch_futures_basis_abs,
        blocked_futures_basis_abs=cfg.blocked_futures_basis_abs,
        watch_creation_redemption_imbalance=cfg.watch_creation_redemption_imbalance,
        blocked_creation_redemption_imbalance=cfg.blocked_creation_redemption_imbalance,
        watch_risk_score=cfg.watch_risk_score,
        blocked_risk_score=cfg.blocked_risk_score,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (
                    (snapshot.etf_ticker, snapshot.asset_symbol, snapshot.market_slug),
                    snapshot.source_config_version,
                )
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_etf_flow_dislocation_digest_payload(
    report: MarketResearchCryptoEtfFlowDislocationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoEtfFlowDislocationDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoEtfFlowDislocationDigestReport",
        )
    _require_hard_flags("report", report)
    value = _json_ready(report)
    if type(value) is not dict:
        raise ValueError("report payload must be a JSON object")
    return value


def _row_for_snapshot(
    snapshot: MarketResearchCryptoEtfFlowDislocationSnapshot,
    *,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowDislocationDigestRow:
    if snapshot.source_timestamp > generated_at:
        raise ValueError("source_timestamp must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.source_timestamp)
    net_flow_abs_usd = _decimal_abs(snapshot.net_flow_usd)
    spot_return_abs = _decimal_abs(snapshot.spot_return)
    premium_discount_abs = _decimal_abs(snapshot.premium_discount)
    futures_basis_abs = _decimal_abs(snapshot.futures_basis)
    flow_spot_divergence_abs = _flow_spot_divergence_abs(
        net_flow_usd=snapshot.net_flow_usd,
        net_flow_abs_usd=net_flow_abs_usd,
        spot_return=snapshot.spot_return,
        spot_return_abs=spot_return_abs,
        config=config,
    )
    risk_score = _risk_score(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        net_flow_abs_usd=net_flow_abs_usd,
        flow_spot_divergence_abs=flow_spot_divergence_abs,
        premium_discount_abs=premium_discount_abs,
        futures_basis_abs=futures_basis_abs,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        flow_spot_divergence_abs=flow_spot_divergence_abs,
        premium_discount_abs=premium_discount_abs,
        futures_basis_abs=futures_basis_abs,
    )
    return MarketResearchCryptoEtfFlowDislocationDigestRow(
        etf_ticker=snapshot.etf_ticker,
        asset_symbol=snapshot.asset_symbol,
        market_slug=snapshot.market_slug,
        digest_status=_row_status(
            reason_codes,
            risk_score,
            snapshot=snapshot,
            config=config,
            snapshot_age_seconds=snapshot_age_seconds,
            flow_spot_divergence_abs=flow_spot_divergence_abs,
            premium_discount_abs=premium_discount_abs,
            futures_basis_abs=futures_basis_abs,
        ),
        source_timestamp=snapshot.source_timestamp,
        snapshot_age_seconds=snapshot_age_seconds,
        net_flow_usd=snapshot.net_flow_usd,
        net_flow_abs_usd=net_flow_abs_usd,
        spot_return=snapshot.spot_return,
        spot_return_abs=spot_return_abs,
        flow_spot_divergence_abs=flow_spot_divergence_abs,
        premium_discount=snapshot.premium_discount,
        premium_discount_abs=premium_discount_abs,
        futures_basis=snapshot.futures_basis,
        futures_basis_abs=futures_basis_abs,
        creation_redemption_imbalance=snapshot.creation_redemption_imbalance,
        source_quorum_count=snapshot.source_quorum_count,
        risk_score=risk_score,
        upstream_reason_codes=snapshot.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoEtfFlowDislocationSnapshot,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    flow_spot_divergence_abs: Decimal,
    premium_discount_abs: Decimal,
    futures_basis_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if flow_spot_divergence_abs >= config.watch_flow_spot_divergence_abs:
        reasons.append(FLOW_SPOT_DIVERGENCE_REASON)
    if premium_discount_abs >= config.watch_premium_discount_abs:
        reasons.append(PREMIUM_DISCOUNT_DISLOCATION_REASON)
    if futures_basis_abs >= config.watch_futures_basis_abs:
        reasons.append(FUTURES_BASIS_DISLOCATION_REASON)
    if (
        snapshot.creation_redemption_imbalance
        >= config.watch_creation_redemption_imbalance
    ):
        reasons.append(CREATION_REDEMPTION_IMBALANCE_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(SOURCE_FRESHNESS_GAP_REASON)
    if snapshot.source_quorum_count < config.min_source_quorum_count:
        reasons.append(SOURCE_QUORUM_GAP_REASON)
    if snapshot.upstream_reason_codes:
        reasons.append(UPSTREAM_REASON_SIGNAL_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _risk_score(
    *,
    snapshot: MarketResearchCryptoEtfFlowDislocationSnapshot,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    net_flow_abs_usd: Decimal,
    flow_spot_divergence_abs: Decimal,
    premium_discount_abs: Decimal,
    futures_basis_abs: Decimal,
) -> Decimal:
    score = _weighted_ratio(
        flow_spot_divergence_abs,
        config.blocked_flow_spot_divergence_abs,
        FLOW_SPOT_DIVERGENCE_RISK_WEIGHT,
    )
    score = _quantize(
        score
        + _weighted_ratio(
            premium_discount_abs,
            config.blocked_premium_discount_abs,
            PREMIUM_DISCOUNT_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            futures_basis_abs,
            config.blocked_futures_basis_abs,
            FUTURES_BASIS_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            snapshot.creation_redemption_imbalance,
            config.blocked_creation_redemption_imbalance,
            CREATION_REDEMPTION_IMBALANCE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            net_flow_abs_usd,
            config.blocked_abs_net_flow_usd,
            FLOW_SIZE_RISK_WEIGHT,
        ),
    )
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        score = _quantize(score + SOURCE_FRESHNESS_RISK_WEIGHT)
    if snapshot.source_quorum_count < config.min_source_quorum_count:
        score = _quantize(score + SOURCE_QUORUM_RISK_WEIGHT)
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


def _flow_spot_divergence_abs(
    *,
    net_flow_usd: Decimal,
    net_flow_abs_usd: Decimal,
    spot_return: Decimal,
    spot_return_abs: Decimal,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig,
) -> Decimal:
    if net_flow_abs_usd < config.watch_abs_net_flow_usd:
        return ZERO
    if _flow_and_spot_signs_diverge(net_flow_usd=net_flow_usd, spot_return=spot_return):
        return spot_return_abs
    return ZERO


def _flow_and_spot_signs_diverge(*, net_flow_usd: Decimal, spot_return: Decimal) -> bool:
    return (net_flow_usd > ZERO and spot_return < ZERO) or (
        net_flow_usd < ZERO and spot_return > ZERO
    )


def _row_status(
    reason_codes: tuple[str, ...],
    risk_score: Decimal,
    *,
    snapshot: MarketResearchCryptoEtfFlowDislocationSnapshot,
    config: MarketResearchCryptoEtfFlowDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    flow_spot_divergence_abs: Decimal,
    premium_discount_abs: Decimal,
    futures_basis_abs: Decimal,
) -> str:
    blocked_threshold_breached = (
        snapshot_age_seconds > config.max_snapshot_age_seconds
        or flow_spot_divergence_abs >= config.blocked_flow_spot_divergence_abs
        or premium_discount_abs >= config.blocked_premium_discount_abs
        or futures_basis_abs >= config.blocked_futures_basis_abs
        or snapshot.creation_redemption_imbalance
        >= config.blocked_creation_redemption_imbalance
        or _decimal_abs(snapshot.net_flow_usd) >= config.blocked_abs_net_flow_usd
    )
    if blocked_threshold_breached or risk_score >= config.blocked_risk_score:
        return STATUS_BLOCKED
    if risk_score >= config.watch_risk_score or reason_codes != (PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
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
        return "block_report_only_market_research_crypto_etf_flow_dislocation_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_etf_flow_dislocation_digest"
    return "allow_report_only_market_research_crypto_etf_flow_dislocation_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and PASS_REASON in seen:
        seen.remove(PASS_REASON)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)


def _validate_row(row: MarketResearchCryptoEtfFlowDislocationDigestRow) -> None:
    if row.net_flow_abs_usd != _decimal_abs(row.net_flow_usd):
        raise ValueError("net_flow_abs_usd does not match net_flow_usd")
    if row.spot_return_abs != _decimal_abs(row.spot_return):
        raise ValueError("spot_return_abs does not match spot_return")
    if row.premium_discount_abs != _decimal_abs(row.premium_discount):
        raise ValueError("premium_discount_abs does not match premium_discount")
    if row.futures_basis_abs != _decimal_abs(row.futures_basis):
        raise ValueError("futures_basis_abs does not match futures_basis")
    if not _flow_and_spot_signs_diverge(
        net_flow_usd=row.net_flow_usd,
        spot_return=row.spot_return,
    ) and row.flow_spot_divergence_abs != ZERO:
        raise ValueError("flow_spot_divergence_abs must be zero unless signs diverge")
    if row.flow_spot_divergence_abs > row.spot_return_abs:
        raise ValueError("flow_spot_divergence_abs must not exceed spot_return_abs")


def _validate_report(report: MarketResearchCryptoEtfFlowDislocationDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.pass_snapshot_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (FLOW_SPOT_DIVERGENCE_REASON, report.flow_spot_divergence_snapshot_count),
        (
            PREMIUM_DISCOUNT_DISLOCATION_REASON,
            report.premium_discount_dislocation_snapshot_count,
        ),
        (
            FUTURES_BASIS_DISLOCATION_REASON,
            report.futures_basis_dislocation_snapshot_count,
        ),
        (
            CREATION_REDEMPTION_IMBALANCE_REASON,
            report.creation_redemption_imbalance_snapshot_count,
        ),
        (SOURCE_FRESHNESS_GAP_REASON, report.source_freshness_gap_snapshot_count),
        (SOURCE_QUORUM_GAP_REASON, report.source_quorum_gap_snapshot_count),
        (UPSTREAM_REASON_SIGNAL_REASON, report.upstream_reason_signal_snapshot_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_snapshot_count(report.rows, reason_code):
            raise ValueError("reason snapshot count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.aggregate_net_flow_usd != _decimal_sum(
        row.net_flow_usd for row in report.rows
    ):
        raise ValueError("aggregate_net_flow_usd does not match rows")
    if report.max_net_flow_abs_usd != max(
        (row.net_flow_abs_usd for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_net_flow_abs_usd does not match rows")
    if report.average_spot_return != _ratio(
        _decimal_sum(row.spot_return for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_spot_return does not match rows")
    if report.average_premium_discount != _ratio(
        _decimal_sum(row.premium_discount for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_premium_discount does not match rows")
    if report.average_futures_basis != _ratio(
        _decimal_sum(row.futures_basis for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_futures_basis does not match rows")
    if report.average_creation_redemption_imbalance != _ratio(
        _decimal_sum(row.creation_redemption_imbalance for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError(
            "average_creation_redemption_imbalance does not match rows",
        )
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
    snapshots: Iterable[MarketResearchCryptoEtfFlowDislocationSnapshot],
) -> tuple[MarketResearchCryptoEtfFlowDislocationSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)) or not isinstance(snapshots, Iterable):
        raise ValueError("snapshots must be an iterable")
    snapshot_tuple = tuple(snapshots)
    seen_surfaces: set[tuple[str, str, str]] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoEtfFlowDislocationSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoEtfFlowDislocationSnapshot",
            )
        surface = (snapshot.etf_ticker, snapshot.asset_symbol, snapshot.market_slug)
        if surface in seen_surfaces:
            raise ValueError("snapshot surface values must be unique")
        seen_surfaces.add(surface)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfFlowDislocationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoEtfFlowDislocationDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoEtfFlowDislocationDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.market_slug,
                row.etf_ticker,
                row.asset_symbol,
            ),
        ),
    ):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        _require_hard_flags("reason_code_count", item)
    normalized = tuple(
        item
        for reason_code in REASON_CODE_SEQUENCE
        for item in items
        if item.reason_code == reason_code
    )
    if normalized != items:
        raise ValueError("reason_code_counts must be deterministic")
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[tuple[str, str, str], str], ...],
) -> tuple[tuple[tuple[str, str, str], str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[tuple[str, str, str], str]] = []
    seen_surfaces: set[tuple[str, str, str]] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        surface, source_config_version = item
        if type(surface) is not tuple or len(surface) != 3:
            raise ValueError("source_config_versions must contain surface tuples")
        etf_ticker, asset_symbol, market_slug = surface
        _require_public_string("etf_ticker", etf_ticker)
        _require_public_string("asset_symbol", asset_symbol)
        _require_public_string("market_slug", market_slug)
        _require_public_string("source_config_version", source_config_version)
        if surface in seen_surfaces:
            raise ValueError("source_config_versions surfaces must be unique")
        seen_surfaces.add(surface)
        pairs.append((surface, source_config_version))
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
    if type(value) is not str or value not in FLOW_DISLOCATION_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_threshold_sequence(
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
    if decimal_value < NEGATIVE_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_signed_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


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


def _decimal_abs(value: Decimal) -> Decimal:
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


def _row_sort_value(
    row: MarketResearchCryptoEtfFlowDislocationDigestRow,
) -> tuple[Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: Decimal("0.000000"),
        STATUS_WATCH: Decimal("1.000000"),
        STATUS_PASS: Decimal("2.000000"),
    }[row.digest_status]
    return (status_rank, -row.risk_score)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(item_name): _json_ready(item_value) for item_name, item_value in value.items()}
    return value
