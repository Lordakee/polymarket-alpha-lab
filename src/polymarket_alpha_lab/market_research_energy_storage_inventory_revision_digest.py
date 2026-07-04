"""Pure Phase 1 energy storage inventory revision digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION = (
    "market-research-energy-storage-inventory-revision-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REVISION_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
COMMODITY_FAMILIES = ("gas", "oil", "storage")

REASON_PREFIX = "market_research_energy_storage_inventory_revision_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
MATERIAL_REVISION_REASON = f"{REASON_PREFIX}material_revision"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
SURPRISE_CLUSTER_REASON = f"{REASON_PREFIX}surprise_cluster"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    MATERIAL_SURPRISE_REASON,
    SURPRISE_CLUSTER_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    PASS_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    MATERIAL_SURPRISE_REASON,
    SURPRISE_CLUSTER_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    PASS_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "allow_report_only_market_research_energy_storage_inventory_revision_digest",
    STATUS_WATCH: "watch_report_only_market_research_energy_storage_inventory_revision_digest",
    STATUS_BLOCKED: "block_report_only_market_research_energy_storage_inventory_revision_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
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
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyStorageInventoryRevisionDigestConfig",
    "MarketResearchEnergyStorageInventoryRevisionDigestInputRow",
    "MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount",
    "MarketResearchEnergyStorageInventoryRevisionDigestReport",
    "MarketResearchEnergyStorageInventoryRevisionDigestRow",
    "build_market_research_energy_storage_inventory_revision_digest",
    "market_research_energy_storage_inventory_revision_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyStorageInventoryRevisionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_revision_ratio: Decimal = Decimal("0.050000")
    blocked_revision_ratio: Decimal = Decimal("0.150000")
    watch_surprise_ratio: Decimal = Decimal("0.050000")
    blocked_surprise_ratio: Decimal = Decimal("0.150000")
    cluster_min_report_count: Decimal = Decimal("2.000000")
    probability_repricing_threshold: Decimal = Decimal("0.070000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyStorageInventoryRevisionDigestConfig:
            raise TypeError(
                "MarketResearchEnergyStorageInventoryRevisionDigestConfig does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyStorageInventoryRevisionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchEnergyStorageInventoryRevisionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_release_max_age_seconds",
            _require_positive_decimal(
                "fresh_release_max_age_seconds",
                self.fresh_release_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "watch_revision_ratio",
            "blocked_revision_ratio",
            "watch_surprise_ratio",
            "blocked_surprise_ratio",
            "probability_repricing_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_revision_ratio < self.watch_revision_ratio:
            raise ValueError("blocked_revision_ratio must be at least watch_revision_ratio")
        if self.blocked_surprise_ratio < self.watch_surprise_ratio:
            raise ValueError("blocked_surprise_ratio must be at least watch_surprise_ratio")
        object.__setattr__(
            self,
            "cluster_min_report_count",
            _require_positive_count_decimal(
                "cluster_min_report_count",
                self.cluster_min_report_count,
            ),
        )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _require_positive_decimal(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyStorageInventoryRevisionDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    inventory_report_key: str
    commodity_family: str
    inventory_report_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    initial_inventory_level: Decimal
    revised_inventory_level: Decimal
    expected_inventory_level: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyStorageInventoryRevisionDigestInputRow:
            raise TypeError(
                "MarketResearchEnergyStorageInventoryRevisionDigestInputRow does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyStorageInventoryRevisionDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchEnergyStorageInventoryRevisionDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("inventory_report_key", self.inventory_report_key)
        _require_commodity_family("commodity_family", self.commodity_family)
        _require_reference("inventory_report_reference", self.inventory_report_reference)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "initial_inventory_level",
            "revised_inventory_level",
            "expected_inventory_level",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyStorageInventoryRevisionDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    inventory_report_key: str
    commodity_family: str
    revision_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    initial_inventory_level: Decimal
    revised_inventory_level: Decimal
    expected_inventory_level: Decimal
    revision_delta: Decimal
    revision_abs: Decimal
    revision_abs_ratio: Decimal
    inventory_surprise: Decimal
    surprise_abs: Decimal
    surprise_abs_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_inventory_report_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyStorageInventoryRevisionDigestRow:
            raise TypeError(
                "MarketResearchEnergyStorageInventoryRevisionDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyStorageInventoryRevisionDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchEnergyStorageInventoryRevisionDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("inventory_report_key", self.inventory_report_key)
        _require_commodity_family("commodity_family", self.commodity_family)
        _require_revision_status("revision_status", self.revision_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "initial_inventory_level",
            "revised_inventory_level",
            "expected_inventory_level",
            "revision_abs",
            "surprise_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("revision_delta", "inventory_surprise"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "revision_abs_ratio",
            "surprise_abs_ratio",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "redacted_inventory_report_reference",
            _require_redacted_reference(
                "redacted_inventory_report_reference",
                self.redacted_inventory_report_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    report_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount
        ):
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "report_ratio",
            _require_ratio_decimal("report_ratio", self.report_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchEnergyStorageInventoryRevisionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    inventory_report_count: Decimal
    pass_report_count: Decimal
    watch_report_count: Decimal
    blocked_report_count: Decimal
    material_revision_count: Decimal
    material_surprise_count: Decimal
    surprise_cluster_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_revision_abs_ratio: Decimal
    max_revision_abs_ratio: Decimal
    max_surprise_abs_ratio: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchEnergyStorageInventoryRevisionDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEnergyStorageInventoryRevisionDigestReport:
            raise TypeError(
                "MarketResearchEnergyStorageInventoryRevisionDigestReport does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchEnergyStorageInventoryRevisionDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchEnergyStorageInventoryRevisionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_STORAGE_INVENTORY_REVISION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_revision_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "inventory_report_count",
            "pass_report_count",
            "watch_report_count",
            "blocked_report_count",
            "material_revision_count",
            "material_surprise_count",
            "surprise_cluster_count",
            "stale_release_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_revision_abs_ratio",
            "max_revision_abs_ratio",
            "max_surprise_abs_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _require_nonnegative_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "average_source_count",
            _require_nonnegative_decimal("average_source_count", self.average_source_count),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_storage_inventory_revision_digest(
    input_rows: list[MarketResearchEnergyStorageInventoryRevisionDigestInputRow]
    | tuple[MarketResearchEnergyStorageInventoryRevisionDigestInputRow, ...],
    *,
    config: MarketResearchEnergyStorageInventoryRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyStorageInventoryRevisionDigestReport:
    if type(config) is not MarketResearchEnergyStorageInventoryRevisionDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchEnergyStorageInventoryRevisionDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    clustered_families = _clustered_families(source_rows, config=config)
    rows = tuple(
        _build_row(
            row,
            config=config,
            generated_at=generated_at_utc,
            clustered_families=clustered_families,
        )
        for row in source_rows
    )
    ranked_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                report_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    inventory_report_count = _count(len(ranked_rows))
    pass_report_count = _count(
        sum(1 for row in ranked_rows if row.revision_status == STATUS_PASS),
    )
    watch_report_count = _count(
        sum(1 for row in ranked_rows if row.revision_status == STATUS_WATCH),
    )
    blocked_report_count = _count(
        sum(1 for row in ranked_rows if row.revision_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_report_count=blocked_report_count,
        watch_report_count=watch_report_count,
    )

    return MarketResearchEnergyStorageInventoryRevisionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        inventory_report_count=inventory_report_count,
        pass_report_count=pass_report_count,
        watch_report_count=watch_report_count,
        blocked_report_count=blocked_report_count,
        material_revision_count=_count(
            sum(1 for row in ranked_rows if MATERIAL_REVISION_REASON in row.reason_codes),
        ),
        material_surprise_count=_count(
            sum(1 for row in ranked_rows if MATERIAL_SURPRISE_REASON in row.reason_codes),
        ),
        surprise_cluster_count=_count(
            sum(1 for row in ranked_rows if SURPRISE_CLUSTER_REASON in row.reason_codes),
        ),
        stale_release_count=_count(
            sum(1 for row in ranked_rows if STALE_RELEASE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        missing_acknowledgement_count=_count(
            sum(
                1
                for row in ranked_rows
                if MISSING_ACKNOWLEDGEMENT_REASON in row.reason_codes
            ),
        ),
        slow_acknowledgement_count=_count(
            sum(1 for row in ranked_rows if SLOW_ACKNOWLEDGEMENT_REASON in row.reason_codes),
        ),
        probability_repricing_count=_count(
            sum(
                1
                for row in ranked_rows
                if PROBABILITY_REPRICING_REASON in row.reason_codes
            ),
        ),
        average_revision_abs_ratio=_ratio(
            _sum_decimal(row.revision_abs_ratio for row in ranked_rows),
            inventory_report_count,
        ),
        max_revision_abs_ratio=max(
            (row.revision_abs_ratio for row in ranked_rows),
            default=ZERO,
        ),
        max_surprise_abs_ratio=max(
            (row.surprise_abs_ratio for row in ranked_rows),
            default=ZERO,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ranked_rows),
            inventory_report_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_energy_storage_inventory_revision_digest_payload(
    report: MarketResearchEnergyStorageInventoryRevisionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyStorageInventoryRevisionDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchEnergyStorageInventoryRevisionDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchEnergyStorageInventoryRevisionDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchEnergyStorageInventoryRevisionDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchEnergyStorageInventoryRevisionDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        identity = (
            input_row.research_key,
            input_row.condition_id,
            input_row.inventory_report_key,
        )
        if identity in seen:
            raise ValueError("input rows must use unique research condition report keys")
        seen.add(identity)
        if input_row.released_at > generated_at:
            raise ValueError("released_at cannot be after generated_at")
        if input_row.acknowledged_at is not None:
            if input_row.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at cannot be after generated_at")
            if input_row.acknowledged_at < input_row.released_at:
                raise ValueError("acknowledged_at cannot be before released_at")
    return normalized


def _clustered_families(
    rows: tuple[MarketResearchEnergyStorageInventoryRevisionDigestInputRow, ...],
    *,
    config: MarketResearchEnergyStorageInventoryRevisionDigestConfig,
) -> frozenset[str]:
    counts: dict[str, int] = {}
    for row in rows:
        surprise_abs_ratio = _input_surprise_abs_ratio(row)
        if surprise_abs_ratio >= config.watch_surprise_ratio:
            counts[row.commodity_family] = counts[row.commodity_family] + 1 if (
                row.commodity_family in counts
            ) else 1
    return frozenset(
        family
        for family, count in counts.items()
        if _count(count) >= config.cluster_min_report_count
    )


def _build_row(
    input_row: MarketResearchEnergyStorageInventoryRevisionDigestInputRow,
    *,
    config: MarketResearchEnergyStorageInventoryRevisionDigestConfig,
    generated_at: datetime,
    clustered_families: frozenset[str],
) -> MarketResearchEnergyStorageInventoryRevisionDigestRow:
    release_age_seconds = _seconds_between(input_row.released_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.released_at, input_row.acknowledged_at)
    )
    revision_delta = _finite_decimal(
        input_row.revised_inventory_level - input_row.initial_inventory_level,
    )
    revision_abs = abs(revision_delta)
    revision_abs_ratio = _ratio(revision_abs, abs(input_row.initial_inventory_level))
    inventory_surprise = _finite_decimal(
        input_row.revised_inventory_level - input_row.expected_inventory_level,
    )
    surprise_abs = abs(inventory_surprise)
    surprise_abs_ratio = _ratio(surprise_abs, abs(input_row.expected_inventory_level))
    probability_delta = _probability_delta(
        input_row.market_probability_after - input_row.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        revision_abs_ratio=revision_abs_ratio,
        surprise_abs_ratio=surprise_abs_ratio,
        probability_delta=probability_delta,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        commodity_family=input_row.commodity_family,
        clustered_families=clustered_families,
        config=config,
    )
    return MarketResearchEnergyStorageInventoryRevisionDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        market_slug=input_row.market_slug,
        inventory_report_key=input_row.inventory_report_key,
        commodity_family=input_row.commodity_family,
        revision_status=_row_status(
            reason_codes=reason_codes,
            revision_abs_ratio=revision_abs_ratio,
            surprise_abs_ratio=surprise_abs_ratio,
            config=config,
        ),
        released_at=input_row.released_at,
        acknowledged_at=input_row.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        initial_inventory_level=input_row.initial_inventory_level,
        revised_inventory_level=input_row.revised_inventory_level,
        expected_inventory_level=input_row.expected_inventory_level,
        revision_delta=revision_delta,
        revision_abs=revision_abs,
        revision_abs_ratio=revision_abs_ratio,
        inventory_surprise=inventory_surprise,
        surprise_abs=surprise_abs,
        surprise_abs_ratio=surprise_abs_ratio,
        market_probability_before=input_row.market_probability_before,
        market_probability_after=input_row.market_probability_after,
        probability_delta=probability_delta,
        redacted_inventory_report_reference=_redacted_reference(
            input_row.inventory_report_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    revision_abs_ratio: Decimal,
    surprise_abs_ratio: Decimal,
    probability_delta: Decimal,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    commodity_family: str,
    clustered_families: frozenset[str],
    config: MarketResearchEnergyStorageInventoryRevisionDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if revision_abs_ratio >= config.watch_revision_ratio:
        reasons.append(MATERIAL_REVISION_REASON)
    if surprise_abs_ratio >= config.watch_surprise_ratio:
        reasons.append(MATERIAL_SURPRISE_REASON)
    if commodity_family in clustered_families:
        reasons.append(SURPRISE_CLUSTER_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        reasons.append(PROBABILITY_REPRICING_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    revision_abs_ratio: Decimal,
    surprise_abs_ratio: Decimal,
    config: MarketResearchEnergyStorageInventoryRevisionDigestConfig,
) -> str:
    if (
        MISSING_ACKNOWLEDGEMENT_REASON in reason_codes
        or revision_abs_ratio >= config.blocked_revision_ratio
        or surprise_abs_ratio >= config.blocked_surprise_ratio
    ):
        return STATUS_BLOCKED
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_report_count: Decimal,
    watch_report_count: Decimal,
) -> str:
    if not has_inputs or blocked_report_count > ZERO:
        return STATUS_BLOCKED
    if watch_report_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[MarketResearchEnergyStorageInventoryRevisionDigestRow, ...],
) -> tuple[MarketResearchEnergyStorageInventoryRevisionDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: MarketResearchEnergyStorageInventoryRevisionDigestRow,
) -> tuple[int, str, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.revision_status],
        row.commodity_family,
        row.inventory_report_key,
        row.market_slug,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchEnergyStorageInventoryRevisionDigestRow, ...],
) -> tuple[MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    report_count = _count(len(rows))
    return tuple(
        MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            report_ratio=_ratio(_count(counts[reason_code]), report_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchEnergyStorageInventoryRevisionDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str, str, str, str] | None = None
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchEnergyStorageInventoryRevisionDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEnergyStorageInventoryRevisionDigestRow values",
            )
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.inventory_report_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition report keys")
        seen.add(identity)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by unique status and report keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be sorted by unique reason_code")
        previous_rank = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_rank = rank
    if PASS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes pass cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_rank = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: MarketResearchEnergyStorageInventoryRevisionDigestRow) -> None:
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError(
                "acknowledgement_lag_seconds must be None when acknowledgement is "
                "missing",
            )
    elif row.acknowledgement_lag_seconds is None:
        raise ValueError(
            "acknowledgement_lag_seconds must be present when acknowledgement is "
            "present",
        )
    expected_revision_delta = _finite_decimal(
        row.revised_inventory_level - row.initial_inventory_level,
    )
    if row.revision_delta != expected_revision_delta:
        raise ValueError("revision_delta must match revised minus initial inventory")
    if row.revision_abs != abs(row.revision_delta):
        raise ValueError("revision_abs must match absolute revision_delta")
    if row.revision_abs_ratio != _ratio(row.revision_abs, abs(row.initial_inventory_level)):
        raise ValueError("revision_abs_ratio must match revision_abs and initial level")
    expected_inventory_surprise = _finite_decimal(
        row.revised_inventory_level - row.expected_inventory_level,
    )
    if row.inventory_surprise != expected_inventory_surprise:
        raise ValueError("inventory_surprise must match revised minus expected inventory")
    if row.surprise_abs != abs(row.inventory_surprise):
        raise ValueError("surprise_abs must match absolute inventory_surprise")
    if row.surprise_abs_ratio != _ratio(
        row.surprise_abs,
        abs(row.expected_inventory_level),
    ):
        raise ValueError("surprise_abs_ratio must match surprise_abs and expected level")
    expected_probability_delta = _probability_delta(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability fields")
    if row.reason_codes == (PASS_REASON,):
        if row.revision_status != STATUS_PASS:
            raise ValueError("revision_status must match pass reason_codes")
        return
    if row.revision_status == STATUS_PASS:
        raise ValueError("revision_status pass requires pass reason_codes")
    if (
        MISSING_ACKNOWLEDGEMENT_REASON in row.reason_codes
        and row.revision_status != STATUS_BLOCKED
    ):
        raise ValueError("revision_status must block missing acknowledgement")


def _validate_report(
    report: MarketResearchEnergyStorageInventoryRevisionDigestReport,
) -> None:
    if report.inventory_report_count != _count(len(report.rows)):
        raise ValueError("inventory_report_count must match rows")
    if report.pass_report_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_PASS),
    ):
        raise ValueError("pass_report_count must match rows")
    if report.watch_report_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_WATCH),
    ):
        raise ValueError("watch_report_count must match rows")
    if report.blocked_report_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_report_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchEnergyStorageInventoryRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                report_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_report_count=report.blocked_report_count,
        watch_report_count=report.watch_report_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    _validate_report_metric(report, "material_revision_count", MATERIAL_REVISION_REASON)
    _validate_report_metric(report, "material_surprise_count", MATERIAL_SURPRISE_REASON)
    _validate_report_metric(report, "surprise_cluster_count", SURPRISE_CLUSTER_REASON)
    _validate_report_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    _validate_report_metric(
        report,
        "missing_acknowledgement_count",
        MISSING_ACKNOWLEDGEMENT_REASON,
    )
    _validate_report_metric(report, "slow_acknowledgement_count", SLOW_ACKNOWLEDGEMENT_REASON)
    _validate_report_metric(report, "stale_release_count", STALE_RELEASE_REASON)
    _validate_report_metric(report, "thin_source_count", THIN_SOURCES_REASON)
    expected_average_revision_abs_ratio = _ratio(
        _sum_decimal(row.revision_abs_ratio for row in report.rows),
        report.inventory_report_count,
    )
    if report.average_revision_abs_ratio != expected_average_revision_abs_ratio:
        raise ValueError("average_revision_abs_ratio must match rows")
    if report.max_revision_abs_ratio != max(
        (row.revision_abs_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_revision_abs_ratio must match rows")
    if report.max_surprise_abs_ratio != max(
        (row.surprise_abs_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_surprise_abs_ratio must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    expected_average_source_count = _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.inventory_report_count,
    )
    if report.average_source_count != expected_average_source_count:
        raise ValueError("average_source_count must match rows")


def _validate_report_metric(
    report: MarketResearchEnergyStorageInventoryRevisionDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _count(sum(1 for row in report.rows if reason_code in row.reason_codes))
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _input_surprise_abs_ratio(
    row: MarketResearchEnergyStorageInventoryRevisionDigestInputRow,
) -> Decimal:
    surprise = _finite_decimal(row.revised_inventory_level - row.expected_inventory_level)
    return _ratio(abs(surprise), abs(row.expected_inventory_level))


def _require_commodity_family(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if text not in COMMODITY_FAMILIES:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_revision_status(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if text not in REVISION_STATUSES:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_reason_code(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if text not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return text


def _row_reason_code_rank(reason_code: str) -> int:
    if reason_code not in ROW_REASON_CODE_SEQUENCE:
        raise ValueError("reason_codes must be row reason codes")
    return ROW_REASON_CODE_SEQUENCE.index(reason_code)


def _reason_code_rank(reason_code: str) -> int:
    if reason_code not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    lowered = text.lower()
    if lowered != text:
        raise ValueError(f"{field_name} must be a public identifier")
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_text_fragment(lowered):
        raise ValueError(f"{field_name} must be a public identifier")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(character not in allowed for character in text):
        raise ValueError(f"{field_name} must be a public identifier")
    return text


def _require_market_slug(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if text.lower() != text or any(character not in allowed for character in text):
        raise ValueError(f"{field_name} must be a market slug")
    if "://" in text or "?" in text or _has_unsafe_public_text_fragment(text):
        raise ValueError(f"{field_name} must be a market slug")
    return text


def _require_reference(field_name: str, value: object) -> str:
    return _require_canonical_string(field_name, value)


def _redacted_reference(value: str) -> str:
    if _reference_needs_redaction(value):
        digest = sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if text.startswith("sha256:"):
        digest = text.removeprefix("sha256:")
        if len(digest) != 12 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"{field_name} must be redacted")
        return text
    if _reference_needs_redaction(text):
        raise ValueError(f"{field_name} must be redacted")
    return text


def _reference_needs_redaction(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or "?" in lowered or _has_unsafe_public_text_fragment(lowered)


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_positive_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_ratio_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    _require_whole_decimal(field_name, decimal_value)
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    _require_whole_decimal(field_name, decimal_value)
    return decimal_value


def _require_whole_decimal(field_name: str, value: Decimal) -> None:
    try:
        integral = value.to_integral_exact(rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be whole") from exc
    if value != integral:
        raise ValueError(f"{field_name} must be whole")


def _sum_decimal(values: object) -> Decimal:
    if type(values) not in (list, tuple):
        values = tuple(values)  # type: ignore[arg-type]
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if type(numerator) is not Decimal or type(denominator) is not Decimal:
        raise ValueError("ratio values must be Decimals")
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _finite_decimal(numerator / denominator)


def _finite_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _probability_delta(value: Decimal) -> Decimal:
    return _finite_decimal(value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days * 24 * 60 * 60 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("value must be a Decimal")
        if not value.is_finite():
            raise ValueError("value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("value must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError("value must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} requires {field_name}=True")
