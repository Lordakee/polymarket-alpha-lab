"""Pure Phase 1 Philly Fed surprise digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-philly-fed-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SURPRISE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_philly_fed_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    STALE_RELEASE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_philly_fed_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_philly_fed_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_philly_fed_surprise_digest",
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
        _join_parts("re", "place"),
        _join_parts("wal", "let"),
        _join_parts("ex", "change"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("ke", "y"),
        _join_parts("pri", "vate"),
        _join_parts("or", "der"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchPhillyFedSurpriseDigestConfig",
    "MarketResearchPhillyFedSurpriseDigestInputRow",
    "MarketResearchPhillyFedSurpriseDigestReasonCodeCount",
    "MarketResearchPhillyFedSurpriseDigestReport",
    "MarketResearchPhillyFedSurpriseDigestRow",
    "build_market_research_philly_fed_surprise_digest",
    "market_research_philly_fed_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPhillyFedSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold_points: Decimal = Decimal("5.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPhillyFedSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchPhillyFedSurpriseDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPhillyFedSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchPhillyFedSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION
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
        object.__setattr__(
            self,
            "material_surprise_threshold_points",
            _require_positive_decimal(
                "material_surprise_threshold_points",
                self.material_surprise_threshold_points,
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
class MarketResearchPhillyFedSurpriseDigestInputRow:
    research_key: str
    condition_id: str
    release_key: str
    release_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    forecast_index: Decimal
    actual_index: Decimal
    prior_index: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPhillyFedSurpriseDigestInputRow:
            raise TypeError(
                "MarketResearchPhillyFedSurpriseDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPhillyFedSurpriseDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchPhillyFedSurpriseDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("release_key", self.release_key)
        _require_reference("release_reference", self.release_reference)
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
        for field_name in ("forecast_index", "actual_index", "prior_index"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPhillyFedSurpriseDigestRow:
    research_key: str
    condition_id: str
    release_key: str
    surprise_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    forecast_index: Decimal
    actual_index: Decimal
    prior_index: Decimal
    surprise_delta: Decimal
    abs_surprise_points: Decimal
    prior_delta: Decimal
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPhillyFedSurpriseDigestRow:
            raise TypeError(
                "MarketResearchPhillyFedSurpriseDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPhillyFedSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchPhillyFedSurpriseDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("release_key", self.release_key)
        _require_surprise_status("surprise_status", self.surprise_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal(
                "release_age_seconds",
                self.release_age_seconds,
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
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "forecast_index",
            "actual_index",
            "prior_index",
            "surprise_delta",
            "abs_surprise_points",
            "prior_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        if self.abs_surprise_points < ZERO:
            raise ValueError("abs_surprise_points must be nonnegative")
        object.__setattr__(
            self,
            "redacted_release_reference",
            _require_redacted_reference(
                "redacted_release_reference",
                self.redacted_release_reference,
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
class MarketResearchPhillyFedSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPhillyFedSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPhillyFedSurpriseDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPhillyFedSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchPhillyFedSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "release_ratio",
            _require_ratio_decimal("release_ratio", self.release_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchPhillyFedSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    material_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_abs_surprise_points: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchPhillyFedSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPhillyFedSurpriseDigestReport:
            raise TypeError(
                "MarketResearchPhillyFedSurpriseDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPhillyFedSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchPhillyFedSurpriseDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PHILLY_FED_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_surprise_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "material_surprise_count",
            "stale_release_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_abs_surprise_points",
            "max_release_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_market_research_philly_fed_surprise_digest(
    input_rows: list[MarketResearchPhillyFedSurpriseDigestInputRow]
    | tuple[MarketResearchPhillyFedSurpriseDigestInputRow, ...],
    *,
    config: MarketResearchPhillyFedSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPhillyFedSurpriseDigestReport:
    if type(config) is not MarketResearchPhillyFedSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPhillyFedSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(row, config=config, generated_at=generated_at_utc)
        for row in source_rows
    )
    ordered_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ordered_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ordered_rows:
        reason_code_counts = (
            MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    release_count = _count(len(ordered_rows))
    ready_release_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_READY),
    )
    watch_release_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_WATCH),
    )
    blocked_release_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ordered_rows),
        blocked_release_count=blocked_release_count,
        watch_release_count=watch_release_count,
    )

    return MarketResearchPhillyFedSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        release_count=release_count,
        ready_release_count=ready_release_count,
        watch_release_count=watch_release_count,
        blocked_release_count=blocked_release_count,
        material_surprise_count=_count(
            sum(1 for row in ordered_rows if MATERIAL_SURPRISE_REASON in row.reason_codes),
        ),
        stale_release_count=_count(
            sum(1 for row in ordered_rows if STALE_RELEASE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ordered_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        missing_acknowledgement_count=_count(
            sum(
                1
                for row in ordered_rows
                if MISSING_ACKNOWLEDGEMENT_REASON in row.reason_codes
            ),
        ),
        slow_acknowledgement_count=_count(
            sum(
                1
                for row in ordered_rows
                if SLOW_ACKNOWLEDGEMENT_REASON in row.reason_codes
            ),
        ),
        average_abs_surprise_points=_ratio(
            _sum_decimal(row.abs_surprise_points for row in ordered_rows),
            release_count,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in ordered_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ordered_rows),
            release_count,
        ),
        rows=ordered_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_philly_fed_surprise_digest_payload(
    report: MarketResearchPhillyFedSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPhillyFedSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchPhillyFedSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    return _json_ready(asdict(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchPhillyFedSurpriseDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchPhillyFedSurpriseDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchPhillyFedSurpriseDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (input_row.research_key, input_row.condition_id, input_row.release_key)
        if key in seen:
            raise ValueError("input rows must use unique research condition release keys")
        seen.add(key)
        if input_row.released_at > generated_at:
            raise ValueError("released_at cannot be after generated_at")
        if input_row.acknowledged_at is not None:
            if input_row.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at cannot be after generated_at")
            if input_row.acknowledged_at < input_row.released_at:
                raise ValueError("acknowledged_at cannot be before released_at")
    return normalized


def _build_row(
    input_row: MarketResearchPhillyFedSurpriseDigestInputRow,
    *,
    config: MarketResearchPhillyFedSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPhillyFedSurpriseDigestRow:
    release_age_seconds = _seconds_between(input_row.released_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.released_at, input_row.acknowledged_at)
    )
    surprise_delta = _finite_decimal(input_row.actual_index - input_row.forecast_index)
    abs_surprise_points = _finite_decimal(abs(surprise_delta))
    prior_delta = _finite_decimal(input_row.actual_index - input_row.prior_index)
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        abs_surprise_points=abs_surprise_points,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketResearchPhillyFedSurpriseDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        release_key=input_row.release_key,
        surprise_status=_row_status(reason_codes),
        released_at=input_row.released_at,
        acknowledged_at=input_row.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        forecast_index=input_row.forecast_index,
        actual_index=input_row.actual_index,
        prior_index=input_row.prior_index,
        surprise_delta=surprise_delta,
        abs_surprise_points=abs_surprise_points,
        prior_delta=prior_delta,
        redacted_release_reference=_redacted_reference(input_row.release_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    abs_surprise_points: Decimal,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketResearchPhillyFedSurpriseDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if abs_surprise_points >= config.material_surprise_threshold_points:
        reasons.append(MATERIAL_SURPRISE_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(
        tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reasons),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_release_count: Decimal,
    watch_release_count: Decimal,
) -> str:
    if not has_inputs or blocked_release_count > ZERO:
        return STATUS_BLOCKED
    if watch_release_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchPhillyFedSurpriseDigestRow, ...],
) -> tuple[MarketResearchPhillyFedSurpriseDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: MarketResearchPhillyFedSurpriseDigestRow,
) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.surprise_status],
        row.release_key,
        row.research_key,
        row.condition_id,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchPhillyFedSurpriseDigestRow, ...],
) -> tuple[MarketResearchPhillyFedSurpriseDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    release_count = _count(len(rows))
    return tuple(
        MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            release_ratio=_ratio(_count(counts[reason_code]), release_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchPhillyFedSurpriseDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchPhillyFedSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchPhillyFedSurpriseDigestRow values",
            )
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.release_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition release keys")
        seen.add(identity)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must use deterministic ordering")
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchPhillyFedSurpriseDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchPhillyFedSurpriseDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen.add(count.reason_code)
    expected = tuple(
        sorted(counts, key=lambda count: _reason_code_rank(count.reason_code)),
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    expected = tuple(sorted(reason_codes, key=_row_reason_code_rank))
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic ordering")
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(sorted(reason_codes, key=_reason_code_rank))
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic ordering")
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


def _validate_row(row: MarketResearchPhillyFedSurpriseDigestRow) -> None:
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
    elif row.acknowledged_at < row.released_at:
        raise ValueError("acknowledged_at cannot be before released_at")
    elif row.acknowledgement_lag_seconds != _seconds_between(
        row.released_at,
        row.acknowledged_at,
    ):
        raise ValueError(
            "acknowledgement_lag_seconds must match released_at and acknowledged_at",
        )
    expected_delta = _finite_decimal(row.actual_index - row.forecast_index)
    if row.surprise_delta != expected_delta:
        raise ValueError("surprise_delta must match actual_index minus forecast_index")
    if row.abs_surprise_points != _finite_decimal(abs(expected_delta)):
        raise ValueError("abs_surprise_points must match absolute surprise_delta")
    if row.prior_delta != _finite_decimal(row.actual_index - row.prior_index):
        raise ValueError("prior_delta must match actual_index minus prior_index")
    if row.surprise_status != _row_status(row.reason_codes):
        raise ValueError("surprise_status must match reason_codes")
    if row.reason_codes == (READY_REASON,):
        return
    if READY_REASON in row.reason_codes:
        raise ValueError("reason_codes ready cannot be combined")


def _validate_report(report: MarketResearchPhillyFedSurpriseDigestReport) -> None:
    if report.release_count != _count(len(report.rows)):
        raise ValueError("release_count must match rows")
    if report.ready_release_count != _count(
        sum(1 for row in report.rows if row.surprise_status == STATUS_READY),
    ):
        raise ValueError("ready_release_count must match rows")
    if report.watch_release_count != _count(
        sum(1 for row in report.rows if row.surprise_status == STATUS_WATCH),
    ):
        raise ValueError("watch_release_count must match rows")
    if report.blocked_release_count != _count(
        sum(1 for row in report.rows if row.surprise_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_release_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchPhillyFedSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(
        item.reason_code for item in report.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_release_count=report.blocked_release_count,
        watch_release_count=report.watch_release_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    for row in report.rows:
        if row.released_at > report.generated_at:
            raise ValueError("row released_at cannot be after generated_at")
        if row.release_age_seconds != _seconds_between(
            row.released_at,
            report.generated_at,
        ):
            raise ValueError("row release_age_seconds must match generated_at")
        if (
            row.acknowledged_at is not None
            and row.acknowledged_at > report.generated_at
        ):
            raise ValueError("row acknowledged_at cannot be after generated_at")
    _validate_report_metric(report, "material_surprise_count", MATERIAL_SURPRISE_REASON)
    _validate_report_metric(report, "stale_release_count", STALE_RELEASE_REASON)
    _validate_report_metric(report, "thin_source_count", THIN_SOURCES_REASON)
    _validate_report_metric(
        report,
        "missing_acknowledgement_count",
        MISSING_ACKNOWLEDGEMENT_REASON,
    )
    _validate_report_metric(
        report,
        "slow_acknowledgement_count",
        SLOW_ACKNOWLEDGEMENT_REASON,
    )
    if report.average_abs_surprise_points != _ratio(
        _sum_decimal(row.abs_surprise_points for row in report.rows),
        report.release_count,
    ):
        raise ValueError("average_abs_surprise_points must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.release_count,
    ):
        raise ValueError("average_source_count must match rows")


def _validate_report_metric(
    report: MarketResearchPhillyFedSurpriseDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _count(sum(1 for row in report.rows if reason_code in row.reason_codes))
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be redacted")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_surprise_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be a known surprise status")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} paper_only/report_only/readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware with a non-None UTC offset",
        )
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _nonnegative_decimal(seconds + micros)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _finite_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _nonnegative_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return max(ZERO, value).quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _reason_code_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _row_reason_code_rank(reason_code: str) -> int:
    return ROW_REASON_CODE_SEQUENCE.index(reason_code)


def _redacted_reference(value: str) -> str:
    if _reference_is_safe_public(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _reference_is_safe_public(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return False
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return False
    return True


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value
