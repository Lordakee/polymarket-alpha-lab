"""Pure Phase 1 energy refinery crack spread shock digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-energy-refinery-crack-spread-shock-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
STATUS_RANK = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}

REASON_PREFIX = "market_research_energy_refinery_crack_spread_shock_digest_"
MATERIAL_CRACK_SPREAD_MOVE_REASON = f"{REASON_PREFIX}material_crack_spread_move"
MARGIN_COMPRESSION_REASON = f"{REASON_PREFIX}margin_compression"
MARGIN_EXPANSION_REASON = f"{REASON_PREFIX}margin_expansion"
HIGH_UTILIZATION_REASON = f"{REASON_PREFIX}high_utilization"
FEEDSTOCK_DISLOCATION_REASON = f"{REASON_PREFIX}feedstock_dislocation"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
READY_REASON = f"{REASON_PREFIX}ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

REASON_CODE_SEQUENCE = (
    MATERIAL_CRACK_SPREAD_MOVE_REASON,
    MARGIN_COMPRESSION_REASON,
    MARGIN_EXPANSION_REASON,
    HIGH_UTILIZATION_REASON,
    FEEDSTOCK_DISLOCATION_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code != NO_INPUTS_REASON
)

NEXT_STEPS = {
    STATUS_READY: (
        "allow_report_only_market_research_energy_refinery_crack_spread_shock_digest"
    ),
    STATUS_WATCH: (
        "watch_report_only_market_research_energy_refinery_crack_spread_shock_digest"
    ),
    STATUS_BLOCKED: (
        "block_report_only_market_research_energy_refinery_crack_spread_shock_digest"
    ),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
NEGATIVE_ONE = Decimal("-1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("inter", "nal"),
        _join_parts("or", "der"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyRefineryCrackSpreadShockDigestConfig",
    "MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow",
    "MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount",
    "MarketResearchEnergyRefineryCrackSpreadShockDigestReport",
    "MarketResearchEnergyRefineryCrackSpreadShockDigestRow",
    "build_market_research_energy_refinery_crack_spread_shock_digest",
    "market_research_energy_refinery_crack_spread_shock_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryCrackSpreadShockDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("3600.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_crack_spread_move_usd_per_bbl: Decimal = Decimal("5.000000")
    material_crack_spread_move_ratio: Decimal = Decimal("0.080000")
    high_utilization_rate: Decimal = Decimal("0.920000")
    max_feedstock_dislocation_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryCrackSpreadShockDigestConfig:
            raise TypeError(
                "MarketResearchEnergyRefineryCrackSpreadShockDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryCrackSpreadShockDigestConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
            "material_crack_spread_move_usd_per_bbl",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_crack_spread_move_ratio",
            _require_positive_probability_decimal(
                "material_crack_spread_move_ratio",
                self.material_crack_spread_move_ratio,
            ),
        )
        object.__setattr__(
            self,
            "high_utilization_rate",
            _require_positive_probability_decimal(
                "high_utilization_rate",
                self.high_utilization_rate,
            ),
        )
        object.__setattr__(
            self,
            "max_feedstock_dislocation_score",
            _require_probability_decimal(
                "max_feedstock_dislocation_score",
                self.max_feedstock_dislocation_score,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    refinery_region: str
    product_group: str
    public_crack_spread_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    baseline_crack_spread_usd_per_bbl: Decimal
    observed_crack_spread_usd_per_bbl: Decimal
    intraday_crack_spread_move_ratio: Decimal
    refinery_utilization_rate: Decimal
    feedstock_dislocation_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow:
            raise TypeError(
                "MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow,
            "input row",
        )
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "refinery_region",
            "product_group",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference(
            "public_crack_spread_reference",
            self.public_crack_spread_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_whole_nonnegative_decimal("source_count", self.source_count),
        )
        for field_name in (
            "baseline_crack_spread_usd_per_bbl",
            "observed_crack_spread_usd_per_bbl",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "intraday_crack_spread_move_ratio",
            _require_signed_ratio_decimal(
                "intraday_crack_spread_move_ratio",
                self.intraday_crack_spread_move_ratio,
            ),
        )
        for field_name in ("refinery_utilization_rate", "feedstock_dislocation_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryCrackSpreadShockDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    refinery_region: str
    product_group: str
    shock_status: str
    observation_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    source_gap_count: Decimal
    baseline_crack_spread_usd_per_bbl: Decimal
    observed_crack_spread_usd_per_bbl: Decimal
    crack_spread_change_usd_per_bbl: Decimal
    crack_spread_move_ratio: Decimal
    intraday_crack_spread_move_ratio: Decimal
    refinery_utilization_rate: Decimal
    feedstock_dislocation_score: Decimal
    redacted_public_crack_spread_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryCrackSpreadShockDigestRow:
            raise TypeError(
                "MarketResearchEnergyRefineryCrackSpreadShockDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchEnergyRefineryCrackSpreadShockDigestRow, "row")
        for field_name in (
            "research_key",
            "condition_id",
            "market_slug",
            "refinery_region",
            "product_group",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("shock_status", self.shock_status, STATUSES)
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "source_gap_count"):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "baseline_crack_spread_usd_per_bbl",
            "observed_crack_spread_usd_per_bbl",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "crack_spread_change_usd_per_bbl",
            _require_decimal(
                "crack_spread_change_usd_per_bbl",
                self.crack_spread_change_usd_per_bbl,
            ),
        )
        object.__setattr__(
            self,
            "crack_spread_move_ratio",
            _require_decimal("crack_spread_move_ratio", self.crack_spread_move_ratio),
        )
        object.__setattr__(
            self,
            "intraday_crack_spread_move_ratio",
            _require_signed_ratio_decimal(
                "intraday_crack_spread_move_ratio",
                self.intraday_crack_spread_move_ratio,
            ),
        )
        for field_name in ("refinery_utilization_rate", "feedstock_dislocation_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_crack_spread_reference",
            self.redacted_public_crack_spread_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    shock_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_whole_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "shock_ratio",
            _require_probability_decimal("shock_ratio", self.shock_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyRefineryCrackSpreadShockDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    crack_spread_shock_count: Decimal
    ready_shock_count: Decimal
    watch_shock_count: Decimal
    blocked_shock_count: Decimal
    material_crack_spread_move_count: Decimal
    margin_compression_count: Decimal
    margin_expansion_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    high_utilization_count: Decimal
    feedstock_dislocation_count: Decimal
    average_abs_crack_spread_change_usd_per_bbl: Decimal
    max_abs_crack_spread_change_usd_per_bbl: Decimal
    average_abs_crack_spread_move_ratio: Decimal
    max_observation_age_seconds: Decimal
    average_source_count: Decimal
    fresh_observation_max_age_seconds: Decimal
    max_acknowledgement_lag_seconds: Decimal
    min_source_count: Decimal
    material_crack_spread_move_usd_per_bbl: Decimal
    material_crack_spread_move_ratio: Decimal
    high_utilization_rate: Decimal
    max_feedstock_dislocation_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount,
        ...,
    ]
    source_config_versions: tuple[tuple[str, str], ...]
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyRefineryCrackSpreadShockDigestReport:
            raise TypeError(
                "MarketResearchEnergyRefineryCrackSpreadShockDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyRefineryCrackSpreadShockDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_REFINERY_CRACK_SPREAD_SHOCK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "crack_spread_shock_count",
            "ready_shock_count",
            "watch_shock_count",
            "blocked_shock_count",
            "material_crack_spread_move_count",
            "margin_compression_count",
            "margin_expansion_count",
            "stale_observation_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "high_utilization_count",
            "feedstock_dislocation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_abs_crack_spread_change_usd_per_bbl",
            "max_abs_crack_spread_change_usd_per_bbl",
            "average_abs_crack_spread_move_ratio",
            "max_observation_age_seconds",
            "average_source_count",
            "fresh_observation_max_age_seconds",
            "max_acknowledgement_lag_seconds",
            "material_crack_spread_move_usd_per_bbl",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_whole_nonnegative_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_crack_spread_move_ratio",
            "high_utilization_rate",
            "max_feedstock_dislocation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_refinery_crack_spread_shock_digest(
    rows: Iterable[MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow],
    *,
    config: MarketResearchEnergyRefineryCrackSpreadShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyRefineryCrackSpreadShockDigestReport:
    if type(config) is not MarketResearchEnergyRefineryCrackSpreadShockDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchEnergyRefineryCrackSpreadShockDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    output_rows = tuple(
        sorted(
            (
                _row_from_input(row, config=config, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    shock_count = _count_decimal(len(output_rows))
    reason_code_counts = _reason_code_counts(output_rows, shock_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    digest_status = _digest_status(output_rows)

    return MarketResearchEnergyRefineryCrackSpreadShockDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        crack_spread_shock_count=shock_count,
        ready_shock_count=_status_count(output_rows, STATUS_READY),
        watch_shock_count=_status_count(output_rows, STATUS_WATCH),
        blocked_shock_count=_status_count(output_rows, STATUS_BLOCKED),
        material_crack_spread_move_count=_row_reason_count(
            output_rows,
            MATERIAL_CRACK_SPREAD_MOVE_REASON,
        ),
        margin_compression_count=_row_reason_count(
            output_rows,
            MARGIN_COMPRESSION_REASON,
        ),
        margin_expansion_count=_row_reason_count(output_rows, MARGIN_EXPANSION_REASON),
        stale_observation_count=_row_reason_count(output_rows, STALE_OBSERVATION_REASON),
        thin_source_count=_row_reason_count(output_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_row_reason_count(
            output_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_row_reason_count(
            output_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        high_utilization_count=_row_reason_count(output_rows, HIGH_UTILIZATION_REASON),
        feedstock_dislocation_count=_row_reason_count(
            output_rows,
            FEEDSTOCK_DISLOCATION_REASON,
        ),
        average_abs_crack_spread_change_usd_per_bbl=_average_decimal(
            _abs_decimal(row.crack_spread_change_usd_per_bbl) for row in output_rows
        ),
        max_abs_crack_spread_change_usd_per_bbl=max(
            (
                _abs_decimal(row.crack_spread_change_usd_per_bbl)
                for row in output_rows
            ),
            default=ZERO,
        ),
        average_abs_crack_spread_move_ratio=_average_decimal(
            _abs_decimal(row.crack_spread_move_ratio) for row in output_rows
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in output_rows),
            default=ZERO,
        ),
        average_source_count=_average_decimal(row.source_count for row in output_rows),
        fresh_observation_max_age_seconds=config.fresh_observation_max_age_seconds,
        max_acknowledgement_lag_seconds=config.max_acknowledgement_lag_seconds,
        min_source_count=config.min_source_count,
        material_crack_spread_move_usd_per_bbl=(
            config.material_crack_spread_move_usd_per_bbl
        ),
        material_crack_spread_move_ratio=config.material_crack_spread_move_ratio,
        high_utilization_rate=config.high_utilization_rate,
        max_feedstock_dislocation_score=config.max_feedstock_dislocation_score,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        source_config_versions=_source_config_versions(input_rows),
        rows=output_rows,
    )


def market_research_energy_refinery_crack_spread_shock_digest_payload(
    report: MarketResearchEnergyRefineryCrackSpreadShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyRefineryCrackSpreadShockDigestReport:
        raise ValueError(
            "report must be a MarketResearchEnergyRefineryCrackSpreadShockDigestReport",
        )
    return _json_ready(report)


def _row_from_input(
    row: MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow,
    *,
    config: MarketResearchEnergyRefineryCrackSpreadShockDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyRefineryCrackSpreadShockDigestRow:
    if row.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.acknowledged_at is not None and row.acknowledged_at < row.observed_at:
        raise ValueError("acknowledged_at must not precede observed_at")
    observation_age_seconds = _seconds_between(generated_at, row.observed_at)
    acknowledgement_lag_seconds = (
        None
        if row.acknowledged_at is None
        else _seconds_between(row.acknowledged_at, row.observed_at)
    )
    source_gap_count = _count_gap(config.min_source_count, row.source_count)
    crack_spread_change = _quantize(
        row.observed_crack_spread_usd_per_bbl
        - row.baseline_crack_spread_usd_per_bbl,
    )
    crack_spread_move_ratio = _ratio(
        crack_spread_change,
        row.baseline_crack_spread_usd_per_bbl,
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        observation_age_seconds=observation_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_gap_count=source_gap_count,
        crack_spread_change_usd_per_bbl=crack_spread_change,
        crack_spread_move_ratio=crack_spread_move_ratio,
    )
    return MarketResearchEnergyRefineryCrackSpreadShockDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        market_slug=row.market_slug,
        refinery_region=row.refinery_region,
        product_group=row.product_group,
        shock_status=_row_status(reason_codes),
        observation_age_seconds=observation_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        source_gap_count=source_gap_count,
        baseline_crack_spread_usd_per_bbl=row.baseline_crack_spread_usd_per_bbl,
        observed_crack_spread_usd_per_bbl=row.observed_crack_spread_usd_per_bbl,
        crack_spread_change_usd_per_bbl=crack_spread_change,
        crack_spread_move_ratio=crack_spread_move_ratio,
        intraday_crack_spread_move_ratio=row.intraday_crack_spread_move_ratio,
        refinery_utilization_rate=row.refinery_utilization_rate,
        feedstock_dislocation_score=row.feedstock_dislocation_score,
        redacted_public_crack_spread_reference=_redacted_public_reference(
            row.public_crack_spread_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow,
    *,
    config: MarketResearchEnergyRefineryCrackSpreadShockDigestConfig,
    observation_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_gap_count: Decimal,
    crack_spread_change_usd_per_bbl: Decimal,
    crack_spread_move_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    material_move = (
        _abs_decimal(crack_spread_change_usd_per_bbl)
        >= config.material_crack_spread_move_usd_per_bbl
        or _abs_decimal(crack_spread_move_ratio)
        >= config.material_crack_spread_move_ratio
    )
    if material_move:
        reason_codes.append(MATERIAL_CRACK_SPREAD_MOVE_REASON)
        if crack_spread_change_usd_per_bbl < ZERO:
            reason_codes.append(MARGIN_COMPRESSION_REASON)
        elif crack_spread_change_usd_per_bbl > ZERO:
            reason_codes.append(MARGIN_EXPANSION_REASON)
    if row.refinery_utilization_rate >= config.high_utilization_rate:
        reason_codes.append(HIGH_UTILIZATION_REASON)
    if row.feedstock_dislocation_score > config.max_feedstock_dislocation_score:
        reason_codes.append(FEEDSTOCK_DISLOCATION_REASON)
    if acknowledgement_lag_seconds is None:
        reason_codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reason_codes.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if observation_age_seconds > config.fresh_observation_max_age_seconds:
        reason_codes.append(STALE_OBSERVATION_REASON)
    if source_gap_count > ZERO:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODE_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        MISSING_ACKNOWLEDGEMENT_REASON in reason_codes
        or STALE_OBSERVATION_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _digest_status(
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...],
) -> str:
    if any(row.shock_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.shock_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    if rows:
        return STATUS_READY
    return STATUS_BLOCKED


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...],
    shock_count: Decimal,
) -> tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                shock_ratio=ZERO,
            ),
        )
    counts = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code == NO_INPUTS_REASON:
            continue
        count = _row_reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    shock_ratio=_ratio(count, shock_count),
                ),
            )
    return tuple(counts)


def _row_reason_count(
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.shock_status == status))


def _source_config_versions(
    rows: tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((row.market_slug, row.source_config_version) for row in rows))


def _normalize_input_rows(
    rows: Iterable[MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow],
) -> tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("input rows must contain refinery crack spread shock rows")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "input rows must contain refinery crack spread shock rows",
        ) from exc
    research_keys: set[str] = set()
    condition_ids: set[str] = set()
    market_slugs: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchEnergyRefineryCrackSpreadShockDigestInputRow",
            )
        if row.research_key in research_keys:
            raise ValueError("research_key values must be unique")
        if row.condition_id in condition_ids:
            raise ValueError("condition_id values must be unique")
        if row.market_slug in market_slugs:
            raise ValueError("market_slug values must be unique")
        research_keys.add(row.research_key)
        condition_ids.add(row.condition_id)
        market_slugs.add(row.market_slug)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEnergyRefineryCrackSpreadShockDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEnergyRefineryCrackSpreadShockDigestRow",
            )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.research_key for row in rows}) != len(rows):
        raise ValueError("rows must contain unique research_key values")
    if len({row.condition_id for row in rows}) != len(rows):
        raise ValueError("rows must contain unique condition_id values")
    if len({row.market_slug for row in rows}) != len(rows):
        raise ValueError("rows must contain unique market_slug values")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyRefineryCrackSpreadShockDigestReasonCodeCount",
            )
    expected = tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code)))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({item.reason_code for item in counts}) != len(counts):
        raise ValueError("reason_code_counts must contain unique reason_code values")
    return counts


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, tuple):
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        market_slug, source_config_version = item
        normalized.append(
            (
                _require_public_string("market_slug", market_slug),
                _require_public_string("source_config_version", source_config_version),
            ),
        )
    as_tuple = tuple(normalized)
    if as_tuple != tuple(sorted(as_tuple)):
        raise ValueError("source_config_versions must be sorted deterministically")
    if len({item[0] for item in as_tuple}) != len(as_tuple):
        raise ValueError("source_config_versions must contain unique market_slug values")
    return as_tuple


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in value:
        _require_member("reason_code", reason_code, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    normalized = tuple(value)
    if normalized != tuple(sorted(normalized, key=lambda reason: allowed.index(reason))):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: MarketResearchEnergyRefineryCrackSpreadShockDigestRow,
) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_RANK[row.shock_status],
        -_abs_decimal(row.crack_spread_move_ratio),
        row.market_slug,
        row.research_key,
    )


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _validate_row(row: MarketResearchEnergyRefineryCrackSpreadShockDigestRow) -> None:
    expected_change = _quantize(
        row.observed_crack_spread_usd_per_bbl
        - row.baseline_crack_spread_usd_per_bbl,
    )
    if row.crack_spread_change_usd_per_bbl != expected_change:
        raise ValueError("crack_spread_change_usd_per_bbl must match spread inputs")
    expected_ratio = _ratio(
        row.crack_spread_change_usd_per_bbl,
        row.baseline_crack_spread_usd_per_bbl,
    )
    if row.crack_spread_move_ratio != expected_ratio:
        raise ValueError("crack_spread_move_ratio must match spread inputs")
    if row.shock_status != _row_status(row.reason_codes):
        raise ValueError("shock_status must match reason_codes")
    if row.redacted_public_crack_spread_reference != _redacted_public_reference(
        row.redacted_public_crack_spread_reference,
    ):
        raise ValueError("redacted_public_crack_spread_reference must be redacted")


def _validate_report(
    report: MarketResearchEnergyRefineryCrackSpreadShockDigestReport,
) -> None:
    checks = (
        ("crack_spread_shock_count", _count_decimal(len(report.rows))),
        ("ready_shock_count", _status_count(report.rows, STATUS_READY)),
        ("watch_shock_count", _status_count(report.rows, STATUS_WATCH)),
        ("blocked_shock_count", _status_count(report.rows, STATUS_BLOCKED)),
        (
            "material_crack_spread_move_count",
            _row_reason_count(report.rows, MATERIAL_CRACK_SPREAD_MOVE_REASON),
        ),
        (
            "margin_compression_count",
            _row_reason_count(report.rows, MARGIN_COMPRESSION_REASON),
        ),
        (
            "margin_expansion_count",
            _row_reason_count(report.rows, MARGIN_EXPANSION_REASON),
        ),
        (
            "stale_observation_count",
            _row_reason_count(report.rows, STALE_OBSERVATION_REASON),
        ),
        ("thin_source_count", _row_reason_count(report.rows, THIN_SOURCES_REASON)),
        (
            "missing_acknowledgement_count",
            _row_reason_count(report.rows, MISSING_ACKNOWLEDGEMENT_REASON),
        ),
        (
            "slow_acknowledgement_count",
            _row_reason_count(report.rows, SLOW_ACKNOWLEDGEMENT_REASON),
        ),
        (
            "high_utilization_count",
            _row_reason_count(report.rows, HIGH_UTILIZATION_REASON),
        ),
        (
            "feedstock_dislocation_count",
            _row_reason_count(report.rows, FEEDSTOCK_DISLOCATION_REASON),
        ),
        (
            "average_abs_crack_spread_change_usd_per_bbl",
            _average_decimal(
                _abs_decimal(row.crack_spread_change_usd_per_bbl)
                for row in report.rows
            ),
        ),
        (
            "max_abs_crack_spread_change_usd_per_bbl",
            max(
                (
                    _abs_decimal(row.crack_spread_change_usd_per_bbl)
                    for row in report.rows
                ),
                default=ZERO,
            ),
        ),
        (
            "average_abs_crack_spread_move_ratio",
            _average_decimal(_abs_decimal(row.crack_spread_move_ratio) for row in report.rows),
        ),
        (
            "max_observation_age_seconds",
            max((row.observation_age_seconds for row in report.rows), default=ZERO),
        ),
        (
            "average_source_count",
            _average_decimal(row.source_count for row in report.rows),
        ),
    )
    for field_name, expected in checks:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_counts = _reason_code_counts(
        report.rows,
        report.crack_spread_shock_count,
    )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized != normalized.lower() or any(character.isspace() for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase public identifier")
    if _contains_unsafe_text(normalized):
        raise ValueError(f"{field_name} must not contain unsafe text")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized or normalized != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return normalized


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_whole_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < NEGATIVE_ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_gap(required_count: Decimal, actual_count: Decimal) -> Decimal:
    if actual_count >= required_count:
        return ZERO
    return _quantize(required_count - actual_count)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (_sum_decimal(items) / Decimal(len(items))).quantize(QUANT)


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _redacted_public_reference(value: str) -> str:
    if value.startswith("sha256:") and len(value) == 19:
        return value
    if _contains_unsafe_text(value):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _require_redacted_reference(field_name: str, value: object) -> None:
    normalized = _require_canonical_string(field_name, value)
    if _contains_unsafe_text(normalized):
        raise ValueError(f"{field_name} must be redacted")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "public_crack_spread_reference"
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} requires {field_name}=True")
