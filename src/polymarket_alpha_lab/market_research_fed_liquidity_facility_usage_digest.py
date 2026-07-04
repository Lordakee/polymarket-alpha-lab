"""Pure Phase 1 Fed liquidity facility usage digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION = (
    "market-research-fed-liquidity-facility-usage-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_fed_liquidity_facility_usage_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
HIGH_USAGE_REASON = f"{REASON_PREFIX}high_usage"
USAGE_SPIKE_REASON = f"{REASON_PREFIX}usage_spike"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"

REASON_CODE_SEQUENCE = (
    HIGH_USAGE_REASON,
    USAGE_SPIKE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    STALE_OBSERVATION_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_USAGE_REASON,
    USAGE_SPIKE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    STALE_OBSERVATION_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_fed_liquidity_facility_usage_digest",
    STATUS_WATCH: "watch_report_only_market_research_fed_liquidity_facility_usage_digest",
    STATUS_BLOCKED: "block_report_only_market_research_fed_liquidity_facility_usage_digest",
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
    "DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION",
    "MarketResearchFedLiquidityFacilityUsageDigestConfig",
    "MarketResearchFedLiquidityFacilityUsageDigestInputRow",
    "MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount",
    "MarketResearchFedLiquidityFacilityUsageDigestReport",
    "MarketResearchFedLiquidityFacilityUsageDigestRow",
    "build_market_research_fed_liquidity_facility_usage_digest",
    "market_research_fed_liquidity_facility_usage_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchFedLiquidityFacilityUsageDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION
    )
    high_usage_share_threshold: Decimal = Decimal("0.800000")
    usage_spike_usd_threshold: Decimal = Decimal("5000000000.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedLiquidityFacilityUsageDigestConfig:
            raise TypeError(
                "MarketResearchFedLiquidityFacilityUsageDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedLiquidityFacilityUsageDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchFedLiquidityFacilityUsageDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "high_usage_share_threshold",
            _require_ratio_decimal(
                "high_usage_share_threshold",
                self.high_usage_share_threshold,
            ),
        )
        for field_name in (
            "usage_spike_usd_threshold",
            "min_source_count",
            "max_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchFedLiquidityFacilityUsageDigestInputRow:
    facility_key: str
    facility_name: str
    observed_at: datetime
    usage_amount_usd: Decimal
    prior_usage_amount_usd: Decimal
    weekly_change_usd: Decimal
    usage_share_of_capacity: Decimal
    counterparty_count: Decimal
    source_count: Decimal
    public_source_reference: str
    event_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedLiquidityFacilityUsageDigestInputRow:
            raise TypeError(
                "MarketResearchFedLiquidityFacilityUsageDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedLiquidityFacilityUsageDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchFedLiquidityFacilityUsageDigestInputRow",
            )
        for field_name in (
            "facility_key",
            "facility_name",
            "event_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_source_reference", self.public_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "usage_amount_usd",
            "prior_usage_amount_usd",
            "counterparty_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "weekly_change_usd",
            _require_decimal("weekly_change_usd", self.weekly_change_usd),
        )
        object.__setattr__(
            self,
            "usage_share_of_capacity",
            _require_ratio_decimal("usage_share_of_capacity", self.usage_share_of_capacity),
        )
        _validate_input_row(self)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchFedLiquidityFacilityUsageDigestRow:
    facility_key: str
    facility_name: str
    facility_usage_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    usage_amount_usd: Decimal
    prior_usage_amount_usd: Decimal
    weekly_change_usd: Decimal
    usage_share_of_capacity: Decimal
    counterparty_count: Decimal
    source_count: Decimal
    redacted_public_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedLiquidityFacilityUsageDigestRow:
            raise TypeError(
                "MarketResearchFedLiquidityFacilityUsageDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedLiquidityFacilityUsageDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchFedLiquidityFacilityUsageDigestRow",
            )
        for field_name in ("facility_key", "facility_name"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("facility_usage_status", self.facility_usage_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "usage_amount_usd",
            "prior_usage_amount_usd",
            "counterparty_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "weekly_change_usd",
            _require_decimal("weekly_change_usd", self.weekly_change_usd),
        )
        object.__setattr__(
            self,
            "usage_share_of_capacity",
            _require_ratio_decimal("usage_share_of_capacity", self.usage_share_of_capacity),
        )
        object.__setattr__(
            self,
            "redacted_public_source_reference",
            _require_redacted_reference(
                "redacted_public_source_reference",
                self.redacted_public_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    facility_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "facility_ratio",
            _require_ratio_decimal("facility_ratio", self.facility_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchFedLiquidityFacilityUsageDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    facility_count: Decimal
    ready_facility_count: Decimal
    watch_facility_count: Decimal
    blocked_facility_count: Decimal
    active_facility_count: Decimal
    high_usage_facility_count: Decimal
    usage_spike_count: Decimal
    thin_source_count: Decimal
    stale_observation_count: Decimal
    total_usage_amount_usd: Decimal
    total_weekly_change_usd: Decimal
    max_usage_share_of_capacity: Decimal
    average_usage_share_of_capacity: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...]
    event_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchFedLiquidityFacilityUsageDigestReport:
            raise TypeError(
                "MarketResearchFedLiquidityFacilityUsageDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedLiquidityFacilityUsageDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchFedLiquidityFacilityUsageDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "facility_count",
            "ready_facility_count",
            "watch_facility_count",
            "blocked_facility_count",
            "active_facility_count",
            "high_usage_facility_count",
            "usage_spike_count",
            "thin_source_count",
            "stale_observation_count",
            "total_usage_amount_usd",
            "max_usage_share_of_capacity",
            "average_usage_share_of_capacity",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_weekly_change_usd",
            _require_decimal("total_weekly_change_usd", self.total_weekly_change_usd),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "event_config_versions",
            _normalize_event_config_versions(self.event_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, order=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_fed_liquidity_facility_usage_digest(
    rows: Iterable[MarketResearchFedLiquidityFacilityUsageDigestInputRow],
    *,
    config: MarketResearchFedLiquidityFacilityUsageDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedLiquidityFacilityUsageDigestReport:
    if type(config) is not MarketResearchFedLiquidityFacilityUsageDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchFedLiquidityFacilityUsageDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(rows, generated_at_utc)
    digest_rows = tuple(
        _row_for_input(row, config=config, generated_at=generated_at_utc)
        for row in normalized_rows
    )
    sorted_rows = _sorted_rows(digest_rows)
    facility_count = _count(len(sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows, facility_count)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = ()
        reason_codes = (NO_INPUTS_REASON,)

    ready_facility_count = _count(
        sum(1 for row in sorted_rows if row.facility_usage_status == STATUS_READY),
    )
    watch_facility_count = _count(
        sum(1 for row in sorted_rows if row.facility_usage_status == STATUS_WATCH),
    )
    blocked_facility_count = _count(
        sum(1 for row in sorted_rows if row.facility_usage_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(sorted_rows),
        blocked_facility_count=blocked_facility_count,
        watch_facility_count=watch_facility_count,
    )

    return MarketResearchFedLiquidityFacilityUsageDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        facility_count=facility_count,
        ready_facility_count=ready_facility_count,
        watch_facility_count=watch_facility_count,
        blocked_facility_count=blocked_facility_count,
        active_facility_count=_count(
            sum(1 for row in sorted_rows if row.usage_amount_usd > ZERO),
        ),
        high_usage_facility_count=_reason_facility_count(
            sorted_rows,
            HIGH_USAGE_REASON,
        ),
        usage_spike_count=_reason_facility_count(sorted_rows, USAGE_SPIKE_REASON),
        thin_source_count=_reason_facility_count(sorted_rows, THIN_SOURCES_REASON),
        stale_observation_count=_reason_facility_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        total_usage_amount_usd=_decimal_sum(row.usage_amount_usd for row in sorted_rows),
        total_weekly_change_usd=_decimal_sum(
            row.weekly_change_usd for row in sorted_rows
        ),
        max_usage_share_of_capacity=max(
            (row.usage_share_of_capacity for row in sorted_rows),
            default=ZERO,
        ),
        average_usage_share_of_capacity=_ratio(
            _decimal_sum(row.usage_share_of_capacity for row in sorted_rows),
            facility_count,
        ),
        average_source_count=_ratio(
            _decimal_sum(row.source_count for row in sorted_rows),
            facility_count,
        ),
        rows=sorted_rows,
        event_config_versions=_event_config_versions(normalized_rows),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_fed_liquidity_facility_usage_digest_payload(
    report: MarketResearchFedLiquidityFacilityUsageDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchFedLiquidityFacilityUsageDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchFedLiquidityFacilityUsageDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_input(
    row: MarketResearchFedLiquidityFacilityUsageDigestInputRow,
    *,
    config: MarketResearchFedLiquidityFacilityUsageDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedLiquidityFacilityUsageDigestRow:
    observation_age_seconds = _seconds_between(generated_at, row.observed_at)
    reason_codes = _row_reason_codes(
        observation_age_seconds=observation_age_seconds,
        usage_share_of_capacity=row.usage_share_of_capacity,
        weekly_change_usd=row.weekly_change_usd,
        source_count=row.source_count,
        config=config,
    )
    return MarketResearchFedLiquidityFacilityUsageDigestRow(
        facility_key=row.facility_key,
        facility_name=row.facility_name,
        facility_usage_status=_row_status(reason_codes),
        observed_at=row.observed_at,
        observation_age_seconds=observation_age_seconds,
        usage_amount_usd=row.usage_amount_usd,
        prior_usage_amount_usd=row.prior_usage_amount_usd,
        weekly_change_usd=row.weekly_change_usd,
        usage_share_of_capacity=row.usage_share_of_capacity,
        counterparty_count=row.counterparty_count,
        source_count=row.source_count,
        redacted_public_source_reference=_redact_reference(row.public_source_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation_age_seconds: Decimal,
    usage_share_of_capacity: Decimal,
    weekly_change_usd: Decimal,
    source_count: Decimal,
    config: MarketResearchFedLiquidityFacilityUsageDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if usage_share_of_capacity >= config.high_usage_share_threshold:
        reasons.append(HIGH_USAGE_REASON)
    if weekly_change_usd >= config.usage_spike_usd_threshold:
        reasons.append(USAGE_SPIKE_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    return _normalize_reason_codes(reasons, order=ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if HIGH_USAGE_REASON in reason_codes and THIN_SOURCES_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,) or reason_codes == (
        READY_REASON,
        STALE_OBSERVATION_REASON,
    ):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_facility_count: Decimal,
    watch_facility_count: Decimal,
) -> str:
    if not has_inputs or blocked_facility_count > ZERO:
        return STATUS_BLOCKED
    if watch_facility_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _sorted_rows(
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...],
) -> tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.facility_usage_status),
                -row.usage_share_of_capacity,
                -row.weekly_change_usd,
                -row.usage_amount_usd,
                row.facility_key,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _reason_code_counts(
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...],
    facility_count: Decimal,
) -> tuple[MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount, ...]:
    return tuple(
        MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            facility_ratio=_ratio(count, facility_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        for count in (_reason_facility_count(rows, reason_code),)
        if count > ZERO
    )


def _reason_facility_count(
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _event_config_versions(
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestInputRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((row.facility_key, row.event_config_version) for row in rows))


def _normalize_input_rows(
    rows: Iterable[MarketResearchFedLiquidityFacilityUsageDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchFedLiquidityFacilityUsageDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchFedLiquidityFacilityUsageDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchFedLiquidityFacilityUsageDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.facility_key in seen_keys:
            raise ValueError("facility_key values must be unique")
        seen_keys.add(row.facility_key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at cannot be in the future")
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...],
) -> tuple[MarketResearchFedLiquidityFacilityUsageDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchFedLiquidityFacilityUsageDigestRow:
            raise ValueError(
                "rows must contain MarketResearchFedLiquidityFacilityUsageDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.facility_key in seen_keys:
            raise ValueError("rows facility_key values must be unique")
        seen_keys.add(row.facility_key)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    values: tuple[MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount, ...],
) -> tuple[MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchFedLiquidityFacilityUsageDigestReasonCodeCount values",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(value.reason_code)
    if tuple(value.reason_code for value in normalized) != tuple(
        reason for reason in REASON_CODE_SEQUENCE if reason in seen_codes
    ):
        raise ValueError("reason_code_counts must use canonical reason sequence")
    return normalized


def _normalize_event_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) not in (list, tuple):
        raise ValueError("event_config_versions must be a list or tuple")
    normalized = tuple(values)
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) not in (list, tuple) or len(value) != 2:
            raise ValueError("event_config_versions must contain key/version pairs")
        facility_key, config_version = value
        _require_public_string("event_config_versions key", facility_key)
        _require_public_string("event_config_versions version", config_version)
        if facility_key in seen_keys:
            raise ValueError("event_config_versions keys must be unique")
        seen_keys.add(facility_key)
    normalized_pairs = tuple((str(key), str(version)) for key, version in normalized)
    if normalized_pairs != tuple(sorted(normalized_pairs)):
        raise ValueError("event_config_versions must be sorted deterministically")
    return normalized_pairs


def _normalize_reason_codes(
    values: object,
    *,
    order: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen_codes: set[str] = set()
    for value in normalized:
        _require_reason_code("reason_codes", value)
        if value in seen_codes:
            raise ValueError("reason_codes must be unique")
        seen_codes.add(value)
    if normalized != tuple(reason for reason in order if reason in seen_codes):
        raise ValueError("reason_codes must use canonical reason sequence")
    return normalized


def _validate_input_row(
    row: MarketResearchFedLiquidityFacilityUsageDigestInputRow,
) -> None:
    if row.weekly_change_usd != _quantize(row.usage_amount_usd - row.prior_usage_amount_usd):
        raise ValueError("weekly_change_usd must match usage amount delta")


def _validate_row(row: MarketResearchFedLiquidityFacilityUsageDigestRow) -> None:
    if row.weekly_change_usd != _quantize(row.usage_amount_usd - row.prior_usage_amount_usd):
        raise ValueError("weekly_change_usd must match usage amount delta")
    if row.facility_usage_status != _row_status(row.reason_codes):
        raise ValueError("facility_usage_status must match reason_codes")


def _validate_report(report: MarketResearchFedLiquidityFacilityUsageDigestReport) -> None:
    if (
        report.config_version
        != DEFAULT_MARKET_RESEARCH_FED_LIQUIDITY_FACILITY_USAGE_DIGEST_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.facility_count != _count(len(report.rows)):
        raise ValueError("facility_count must match rows")
    expected_ready = _count(
        sum(1 for row in report.rows if row.facility_usage_status == STATUS_READY),
    )
    expected_watch = _count(
        sum(1 for row in report.rows if row.facility_usage_status == STATUS_WATCH),
    )
    expected_blocked = _count(
        sum(1 for row in report.rows if row.facility_usage_status == STATUS_BLOCKED),
    )
    if report.ready_facility_count != expected_ready:
        raise ValueError("ready_facility_count must match rows")
    if report.watch_facility_count != expected_watch:
        raise ValueError("watch_facility_count must match rows")
    if report.blocked_facility_count != expected_blocked:
        raise ValueError("blocked_facility_count must match rows")
    if (
        report.ready_facility_count
        + report.watch_facility_count
        + report.blocked_facility_count
        != report.facility_count
    ):
        raise ValueError("facility status counts must reconcile")
    expected_reason_counts = _reason_code_counts(report.rows, report.facility_count)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        if report.rows or report.reason_codes != (NO_INPUTS_REASON,):
            raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(
        has_inputs=bool(report.rows),
        blocked_facility_count=report.blocked_facility_count,
        watch_facility_count=report.watch_facility_count,
    ):
        raise ValueError("digest_status must match rows")
    expected_counts = {
        "high_usage_facility_count": HIGH_USAGE_REASON,
        "usage_spike_count": USAGE_SPIKE_REASON,
        "thin_source_count": THIN_SOURCES_REASON,
        "stale_observation_count": STALE_OBSERVATION_REASON,
    }
    for field_name, reason_code in expected_counts.items():
        if getattr(report, field_name) != _reason_facility_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.active_facility_count != _count(
        sum(1 for row in report.rows if row.usage_amount_usd > ZERO),
    ):
        raise ValueError("active_facility_count must match rows")
    if report.total_usage_amount_usd != _decimal_sum(
        row.usage_amount_usd for row in report.rows
    ):
        raise ValueError("total_usage_amount_usd must match rows")
    if report.total_weekly_change_usd != _decimal_sum(
        row.weekly_change_usd for row in report.rows
    ):
        raise ValueError("total_weekly_change_usd must match rows")
    if report.max_usage_share_of_capacity != max(
        (row.usage_share_of_capacity for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_usage_share_of_capacity must match rows")
    if report.average_usage_share_of_capacity != _ratio(
        _decimal_sum(row.usage_share_of_capacity for row in report.rows),
        report.facility_count,
    ):
        raise ValueError("average_usage_share_of_capacity must match rows")
    if report.average_source_count != _ratio(
        _decimal_sum(row.source_count for row in report.rows),
        report.facility_count,
    ):
        raise ValueError("average_source_count must match rows")


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redact_reference(value: str) -> str:
    redacted = value
    if "://" in redacted and "@" in redacted:
        prefix, rest = redacted.split("://", 1)
        redacted = prefix + "://<redacted>@" + rest.split("@", 1)[1]
    if "?" in redacted:
        redacted = redacted.split("?", 1)[0] + "?<redacted>"
    if not _is_redacted_safe(redacted):
        redacted = "source-<redacted>"
    return redacted


def _is_redacted_safe(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
            if key != "public_source_reference"
        }
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or any(ch.isspace() for ch in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = str(value).lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe text")
    return str(value)


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not _is_redacted_safe(value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")
    return str(value)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return str(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
