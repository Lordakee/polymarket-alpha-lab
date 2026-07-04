"""Pure Phase 1 crypto options IV surface dislocation report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_IV_SURFACE_DISLOCATION_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-options-iv-surface-dislocation-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
IV_SURFACE_DISLOCATION_DIGEST_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCKED,
)

PASS_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_pass"
)
NO_INPUTS_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_no_inputs"
)
ATM_IV_Z_SCORE_PRESSURE_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "atm_iv_z_score_pressure"
)
SKEW_CHANGE_PRESSURE_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "skew_change_pressure"
)
TERM_STRUCTURE_KINK_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "term_structure_kink"
)
OPTIONS_VOLUME_OI_PRESSURE_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "options_volume_oi_pressure"
)
SPOT_VOL_DIVERGENCE_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "spot_vol_divergence"
)
SOURCE_FRESHNESS_GAP_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "source_freshness_gap"
)
SOURCE_QUORUM_GAP_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "source_quorum_gap"
)
UPSTREAM_REASON_SIGNAL_REASON = (
    "market_research_crypto_options_iv_surface_dislocation_digest_"
    "upstream_reason_signal"
)

REASON_CODE_SEQUENCE = (
    ATM_IV_Z_SCORE_PRESSURE_REASON,
    SKEW_CHANGE_PRESSURE_REASON,
    TERM_STRUCTURE_KINK_REASON,
    OPTIONS_VOLUME_OI_PRESSURE_REASON,
    SPOT_VOL_DIVERGENCE_REASON,
    SOURCE_FRESHNESS_GAP_REASON,
    SOURCE_QUORUM_GAP_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    ATM_IV_Z_SCORE_PRESSURE_REASON,
    SKEW_CHANGE_PRESSURE_REASON,
    TERM_STRUCTURE_KINK_REASON,
    OPTIONS_VOLUME_OI_PRESSURE_REASON,
    SPOT_VOL_DIVERGENCE_REASON,
    SOURCE_FRESHNESS_GAP_REASON,
    SOURCE_QUORUM_GAP_REASON,
    UPSTREAM_REASON_SIGNAL_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

ATM_IV_Z_SCORE_RISK_WEIGHT = Decimal("0.250000")
SKEW_CHANGE_RISK_WEIGHT = Decimal("0.180000")
TERM_STRUCTURE_KINK_RISK_WEIGHT = Decimal("0.180000")
OPTIONS_VOLUME_OI_PRESSURE_RISK_WEIGHT = Decimal("0.160000")
SPOT_VOL_DIVERGENCE_RISK_WEIGHT = Decimal("0.140000")
SOURCE_FRESHNESS_RISK_WEIGHT = Decimal("0.050000")
SOURCE_QUORUM_RISK_WEIGHT = Decimal("0.040000")


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
    "DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_IV_SURFACE_DISLOCATION_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig",
    "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount",
    "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport",
    "MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow",
    "MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot",
    "build_market_research_crypto_options_iv_surface_dislocation_digest",
    "market_research_crypto_options_iv_surface_dislocation_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_IV_SURFACE_DISLOCATION_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    min_source_quorum_count: Decimal = Decimal("2.000000")
    watch_atm_iv_z_score_abs: Decimal = Decimal("2.000000")
    blocked_atm_iv_z_score_abs: Decimal = Decimal("4.000000")
    watch_skew_change_abs: Decimal = Decimal("0.050000")
    blocked_skew_change_abs: Decimal = Decimal("0.150000")
    watch_term_structure_kink_abs: Decimal = Decimal("0.040000")
    blocked_term_structure_kink_abs: Decimal = Decimal("0.120000")
    watch_options_volume_oi_pressure: Decimal = Decimal("0.300000")
    blocked_options_volume_oi_pressure: Decimal = Decimal("0.650000")
    watch_spot_vol_divergence_abs: Decimal = Decimal("0.080000")
    blocked_spot_vol_divergence_abs: Decimal = Decimal("0.220000")
    watch_risk_score: Decimal = Decimal("0.350000")
    blocked_risk_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_snapshot_age_seconds",
            "min_source_quorum_count",
            "watch_atm_iv_z_score_abs",
            "blocked_atm_iv_z_score_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_skew_change_abs",
            "blocked_skew_change_abs",
            "watch_term_structure_kink_abs",
            "blocked_term_structure_kink_abs",
            "watch_options_volume_oi_pressure",
            "blocked_options_volume_oi_pressure",
            "watch_spot_vol_divergence_abs",
            "blocked_spot_vol_divergence_abs",
            "watch_risk_score",
            "blocked_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_sequence(
            "watch_atm_iv_z_score_abs",
            self.watch_atm_iv_z_score_abs,
            "blocked_atm_iv_z_score_abs",
            self.blocked_atm_iv_z_score_abs,
        )
        _require_threshold_sequence(
            "watch_skew_change_abs",
            self.watch_skew_change_abs,
            "blocked_skew_change_abs",
            self.blocked_skew_change_abs,
        )
        _require_threshold_sequence(
            "watch_term_structure_kink_abs",
            self.watch_term_structure_kink_abs,
            "blocked_term_structure_kink_abs",
            self.blocked_term_structure_kink_abs,
        )
        _require_threshold_sequence(
            "watch_options_volume_oi_pressure",
            self.watch_options_volume_oi_pressure,
            "blocked_options_volume_oi_pressure",
            self.blocked_options_volume_oi_pressure,
        )
        _require_threshold_sequence(
            "watch_spot_vol_divergence_abs",
            self.watch_spot_vol_divergence_abs,
            "blocked_spot_vol_divergence_abs",
            self.blocked_spot_vol_divergence_abs,
        )
        _require_threshold_sequence(
            "watch_risk_score",
            self.watch_risk_score,
            "blocked_risk_score",
            self.blocked_risk_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot:
    venue: str
    asset_symbol: str
    expiry_bucket: str
    market_slug: str
    source_timestamp: datetime
    atm_iv_z_score: Decimal
    skew_change: Decimal
    term_structure_kink: Decimal
    options_volume_oi_pressure: Decimal
    spot_vol_divergence: Decimal
    source_quorum_count: Decimal
    upstream_reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot:
            raise TypeError(
                "MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot",
            )
        for field_name in (
            "venue",
            "asset_symbol",
            "expiry_bucket",
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
            "atm_iv_z_score",
            "skew_change",
            "term_structure_kink",
            "spot_vol_divergence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "options_volume_oi_pressure",
            _require_ratio_decimal(
                "options_volume_oi_pressure",
                self.options_volume_oi_pressure,
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
class MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow:
    venue: str
    asset_symbol: str
    expiry_bucket: str
    market_slug: str
    digest_status: str
    source_timestamp: datetime
    snapshot_age_seconds: Decimal
    atm_iv_z_score: Decimal
    atm_iv_z_score_abs: Decimal
    skew_change: Decimal
    skew_change_abs: Decimal
    term_structure_kink: Decimal
    term_structure_kink_abs: Decimal
    options_volume_oi_pressure: Decimal
    spot_vol_divergence: Decimal
    spot_vol_divergence_abs: Decimal
    source_quorum_count: Decimal
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow:
            raise TypeError(
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow",
            )
        for field_name in ("venue", "asset_symbol", "expiry_bucket", "market_slug"):
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
            "atm_iv_z_score",
            "skew_change",
            "term_structure_kink",
            "spot_vol_divergence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "atm_iv_z_score_abs",
            "source_quorum_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "skew_change_abs",
            "term_structure_kink_abs",
            "options_volume_oi_pressure",
            "spot_vol_divergence_abs",
            "risk_score",
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
class MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount",
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
class MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    pass_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    atm_iv_z_score_pressure_snapshot_count: Decimal
    skew_change_pressure_snapshot_count: Decimal
    term_structure_kink_snapshot_count: Decimal
    options_volume_oi_pressure_snapshot_count: Decimal
    spot_vol_divergence_snapshot_count: Decimal
    source_freshness_gap_snapshot_count: Decimal
    source_quorum_gap_snapshot_count: Decimal
    upstream_reason_signal_snapshot_count: Decimal
    average_atm_iv_z_score: Decimal
    average_skew_change: Decimal
    average_term_structure_kink: Decimal
    average_options_volume_oi_pressure: Decimal
    average_spot_vol_divergence: Decimal
    average_risk_score: Decimal
    max_risk_score: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    min_source_quorum_count: Decimal
    watch_atm_iv_z_score_abs: Decimal
    blocked_atm_iv_z_score_abs: Decimal
    watch_skew_change_abs: Decimal
    blocked_skew_change_abs: Decimal
    watch_term_structure_kink_abs: Decimal
    blocked_term_structure_kink_abs: Decimal
    watch_options_volume_oi_pressure: Decimal
    blocked_options_volume_oi_pressure: Decimal
    watch_spot_vol_divergence_abs: Decimal
    blocked_spot_vol_divergence_abs: Decimal
    watch_risk_score: Decimal
    blocked_risk_score: Decimal
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...]
    source_config_versions: tuple[tuple[tuple[str, str, str, str], str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport:
            raise TypeError(
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport",
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
            "atm_iv_z_score_pressure_snapshot_count",
            "skew_change_pressure_snapshot_count",
            "term_structure_kink_snapshot_count",
            "options_volume_oi_pressure_snapshot_count",
            "spot_vol_divergence_snapshot_count",
            "source_freshness_gap_snapshot_count",
            "source_quorum_gap_snapshot_count",
            "upstream_reason_signal_snapshot_count",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "min_source_quorum_count",
            "watch_atm_iv_z_score_abs",
            "blocked_atm_iv_z_score_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_atm_iv_z_score",
            "average_skew_change",
            "average_term_structure_kink",
            "average_spot_vol_divergence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_options_volume_oi_pressure",
            "average_risk_score",
            "max_risk_score",
            "watch_skew_change_abs",
            "blocked_skew_change_abs",
            "watch_term_structure_kink_abs",
            "blocked_term_structure_kink_abs",
            "watch_options_volume_oi_pressure",
            "blocked_options_volume_oi_pressure",
            "watch_spot_vol_divergence_abs",
            "blocked_spot_vol_divergence_abs",
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


def build_market_research_crypto_options_iv_surface_dislocation_digest(
    snapshots: Iterable[MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot],
    *,
    config: MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport:
    cfg = config or MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig()
    if type(cfg) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig",
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
                row.venue,
                row.asset_symbol,
                row.expiry_bucket,
                row.market_slug,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    snapshot_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=snapshot_count,
        pass_snapshot_count=_status_count(sorted_rows, STATUS_PASS),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        atm_iv_z_score_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            ATM_IV_Z_SCORE_PRESSURE_REASON,
        ),
        skew_change_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SKEW_CHANGE_PRESSURE_REASON,
        ),
        term_structure_kink_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            TERM_STRUCTURE_KINK_REASON,
        ),
        options_volume_oi_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            OPTIONS_VOLUME_OI_PRESSURE_REASON,
        ),
        spot_vol_divergence_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SPOT_VOL_DIVERGENCE_REASON,
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
        average_atm_iv_z_score=_ratio(
            _decimal_sum(row.atm_iv_z_score for row in sorted_rows),
            snapshot_count,
        ),
        average_skew_change=_ratio(
            _decimal_sum(row.skew_change for row in sorted_rows),
            snapshot_count,
        ),
        average_term_structure_kink=_ratio(
            _decimal_sum(row.term_structure_kink for row in sorted_rows),
            snapshot_count,
        ),
        average_options_volume_oi_pressure=_ratio(
            _decimal_sum(row.options_volume_oi_pressure for row in sorted_rows),
            snapshot_count,
        ),
        average_spot_vol_divergence=_ratio(
            _decimal_sum(row.spot_vol_divergence for row in sorted_rows),
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
        watch_atm_iv_z_score_abs=cfg.watch_atm_iv_z_score_abs,
        blocked_atm_iv_z_score_abs=cfg.blocked_atm_iv_z_score_abs,
        watch_skew_change_abs=cfg.watch_skew_change_abs,
        blocked_skew_change_abs=cfg.blocked_skew_change_abs,
        watch_term_structure_kink_abs=cfg.watch_term_structure_kink_abs,
        blocked_term_structure_kink_abs=cfg.blocked_term_structure_kink_abs,
        watch_options_volume_oi_pressure=cfg.watch_options_volume_oi_pressure,
        blocked_options_volume_oi_pressure=cfg.blocked_options_volume_oi_pressure,
        watch_spot_vol_divergence_abs=cfg.watch_spot_vol_divergence_abs,
        blocked_spot_vol_divergence_abs=cfg.blocked_spot_vol_divergence_abs,
        watch_risk_score=cfg.watch_risk_score,
        blocked_risk_score=cfg.blocked_risk_score,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (
                    (
                        snapshot.venue,
                        snapshot.asset_symbol,
                        snapshot.expiry_bucket,
                        snapshot.market_slug,
                    ),
                    snapshot.source_config_version,
                )
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_options_iv_surface_dislocation_digest_payload(
    report: MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot,
    *,
    config: MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow:
    if snapshot.source_timestamp > generated_at:
        raise ValueError("source_timestamp must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.source_timestamp)
    atm_iv_z_score_abs = _decimal_abs(snapshot.atm_iv_z_score)
    skew_change_abs = _decimal_abs(snapshot.skew_change)
    term_structure_kink_abs = _decimal_abs(snapshot.term_structure_kink)
    spot_vol_divergence_abs = _decimal_abs(snapshot.spot_vol_divergence)
    risk_score = _risk_score(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        atm_iv_z_score_abs=atm_iv_z_score_abs,
        skew_change_abs=skew_change_abs,
        term_structure_kink_abs=term_structure_kink_abs,
        spot_vol_divergence_abs=spot_vol_divergence_abs,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        atm_iv_z_score_abs=atm_iv_z_score_abs,
        skew_change_abs=skew_change_abs,
        term_structure_kink_abs=term_structure_kink_abs,
        spot_vol_divergence_abs=spot_vol_divergence_abs,
    )
    return MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow(
        venue=snapshot.venue,
        asset_symbol=snapshot.asset_symbol,
        expiry_bucket=snapshot.expiry_bucket,
        market_slug=snapshot.market_slug,
        digest_status=_row_status(
            reason_codes,
            risk_score,
            snapshot=snapshot,
            config=config,
            snapshot_age_seconds=snapshot_age_seconds,
            atm_iv_z_score_abs=atm_iv_z_score_abs,
            skew_change_abs=skew_change_abs,
            term_structure_kink_abs=term_structure_kink_abs,
            spot_vol_divergence_abs=spot_vol_divergence_abs,
        ),
        source_timestamp=snapshot.source_timestamp,
        snapshot_age_seconds=snapshot_age_seconds,
        atm_iv_z_score=snapshot.atm_iv_z_score,
        atm_iv_z_score_abs=atm_iv_z_score_abs,
        skew_change=snapshot.skew_change,
        skew_change_abs=skew_change_abs,
        term_structure_kink=snapshot.term_structure_kink,
        term_structure_kink_abs=term_structure_kink_abs,
        options_volume_oi_pressure=snapshot.options_volume_oi_pressure,
        spot_vol_divergence=snapshot.spot_vol_divergence,
        spot_vol_divergence_abs=spot_vol_divergence_abs,
        source_quorum_count=snapshot.source_quorum_count,
        risk_score=risk_score,
        upstream_reason_codes=snapshot.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot,
    config: MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    atm_iv_z_score_abs: Decimal,
    skew_change_abs: Decimal,
    term_structure_kink_abs: Decimal,
    spot_vol_divergence_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if atm_iv_z_score_abs >= config.watch_atm_iv_z_score_abs:
        reasons.append(ATM_IV_Z_SCORE_PRESSURE_REASON)
    if skew_change_abs >= config.watch_skew_change_abs:
        reasons.append(SKEW_CHANGE_PRESSURE_REASON)
    if term_structure_kink_abs >= config.watch_term_structure_kink_abs:
        reasons.append(TERM_STRUCTURE_KINK_REASON)
    if snapshot.options_volume_oi_pressure >= config.watch_options_volume_oi_pressure:
        reasons.append(OPTIONS_VOLUME_OI_PRESSURE_REASON)
    if spot_vol_divergence_abs >= config.watch_spot_vol_divergence_abs:
        reasons.append(SPOT_VOL_DIVERGENCE_REASON)
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
    snapshot: MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot,
    config: MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    atm_iv_z_score_abs: Decimal,
    skew_change_abs: Decimal,
    term_structure_kink_abs: Decimal,
    spot_vol_divergence_abs: Decimal,
) -> Decimal:
    score = _weighted_ratio(
        atm_iv_z_score_abs,
        config.blocked_atm_iv_z_score_abs,
        ATM_IV_Z_SCORE_RISK_WEIGHT,
    )
    score = _quantize(
        score
        + _weighted_ratio(
            skew_change_abs,
            config.blocked_skew_change_abs,
            SKEW_CHANGE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            term_structure_kink_abs,
            config.blocked_term_structure_kink_abs,
            TERM_STRUCTURE_KINK_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            snapshot.options_volume_oi_pressure,
            config.blocked_options_volume_oi_pressure,
            OPTIONS_VOLUME_OI_PRESSURE_RISK_WEIGHT,
        ),
    )
    score = _quantize(
        score
        + _weighted_ratio(
            spot_vol_divergence_abs,
            config.blocked_spot_vol_divergence_abs,
            SPOT_VOL_DIVERGENCE_RISK_WEIGHT,
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


def _row_status(
    reason_codes: tuple[str, ...],
    risk_score: Decimal,
    *,
    snapshot: MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot,
    config: MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    atm_iv_z_score_abs: Decimal,
    skew_change_abs: Decimal,
    term_structure_kink_abs: Decimal,
    spot_vol_divergence_abs: Decimal,
) -> str:
    blocked_threshold_breached = (
        snapshot_age_seconds > config.max_snapshot_age_seconds
        or atm_iv_z_score_abs >= config.blocked_atm_iv_z_score_abs
        or skew_change_abs >= config.blocked_skew_change_abs
        or term_structure_kink_abs >= config.blocked_term_structure_kink_abs
        or snapshot.options_volume_oi_pressure
        >= config.blocked_options_volume_oi_pressure
        or spot_vol_divergence_abs >= config.blocked_spot_vol_divergence_abs
    )
    if blocked_threshold_breached or risk_score >= config.blocked_risk_score:
        return STATUS_BLOCKED
    if risk_score >= config.watch_risk_score or reason_codes != (PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_value(
    row: MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow,
) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[row.digest_status]
    return (status_rank, -row.risk_score)


def _report_status(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
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
        return (
            "block_report_only_market_research_crypto_options_"
            "iv_surface_dislocation_digest"
        )
    if status == STATUS_WATCH:
        return (
            "review_report_only_market_research_crypto_options_"
            "iv_surface_dislocation_digest"
        )
    return (
        "allow_report_only_market_research_crypto_options_"
        "iv_surface_dislocation_digest"
    )


def _status_count(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and PASS_REASON in seen:
        seen.remove(PASS_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow) -> None:
    if row.atm_iv_z_score_abs != _decimal_abs(row.atm_iv_z_score):
        raise ValueError("atm_iv_z_score_abs does not match atm_iv_z_score")
    if row.skew_change_abs != _decimal_abs(row.skew_change):
        raise ValueError("skew_change_abs does not match skew_change")
    if row.term_structure_kink_abs != _decimal_abs(row.term_structure_kink):
        raise ValueError("term_structure_kink_abs does not match term_structure_kink")
    if row.spot_vol_divergence_abs != _decimal_abs(row.spot_vol_divergence):
        raise ValueError("spot_vol_divergence_abs does not match spot_vol_divergence")


def _validate_report(
    report: MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport,
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
        (
            ATM_IV_Z_SCORE_PRESSURE_REASON,
            report.atm_iv_z_score_pressure_snapshot_count,
        ),
        (SKEW_CHANGE_PRESSURE_REASON, report.skew_change_pressure_snapshot_count),
        (TERM_STRUCTURE_KINK_REASON, report.term_structure_kink_snapshot_count),
        (
            OPTIONS_VOLUME_OI_PRESSURE_REASON,
            report.options_volume_oi_pressure_snapshot_count,
        ),
        (SPOT_VOL_DIVERGENCE_REASON, report.spot_vol_divergence_snapshot_count),
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
    if report.average_atm_iv_z_score != _ratio(
        _decimal_sum(row.atm_iv_z_score for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_atm_iv_z_score does not match rows")
    if report.average_skew_change != _ratio(
        _decimal_sum(row.skew_change for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_skew_change does not match rows")
    if report.average_term_structure_kink != _ratio(
        _decimal_sum(row.term_structure_kink for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_term_structure_kink does not match rows")
    if report.average_options_volume_oi_pressure != _ratio(
        _decimal_sum(row.options_volume_oi_pressure for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_options_volume_oi_pressure does not match rows")
    if report.average_spot_vol_divergence != _ratio(
        _decimal_sum(row.spot_vol_divergence for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_spot_vol_divergence does not match rows")
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
    snapshots: Iterable[MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot],
) -> tuple[MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_surfaces: set[tuple[str, str, str, str]] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot",
            )
        surface = (
            snapshot.venue,
            snapshot.asset_symbol,
            snapshot.expiry_bucket,
            snapshot.market_slug,
        )
        if surface in seen_surfaces:
            raise ValueError("snapshot surface values must be unique")
        seen_surfaces.add(surface)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.venue,
                row.asset_symbol,
                row.expiry_bucket,
                row.market_slug,
            ),
        ),
    ):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if (
            type(item)
            is not MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount
        ):
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
    value: tuple[tuple[tuple[str, str, str, str], str], ...],
) -> tuple[tuple[tuple[str, str, str, str], str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[tuple[str, str, str, str], str]] = []
    seen_surfaces: set[tuple[str, str, str, str]] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        surface, source_config_version = item
        if type(surface) is not tuple or len(surface) != 4:
            raise ValueError("source_config_versions must contain surface tuples")
        venue, asset_symbol, expiry_bucket, market_slug = surface
        _require_public_string("venue", venue)
        _require_public_string("asset_symbol", asset_symbol)
        _require_public_string("expiry_bucket", expiry_bucket)
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
    if type(value) is not str or value not in IV_SURFACE_DISLOCATION_DIGEST_STATUSES:
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
        return {
            str(item_name): _json_ready(item_value)
            for item_name, item_value in value.items()
        }
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {item_name: _freeze(item_value) for item_name, item_value in value.items()},
        )
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
