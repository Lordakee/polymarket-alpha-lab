"""Pure Phase 1 building-permits surprise digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-building-permits-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SURPRISE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_building_permits_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    HIGH_REVISION_REASON,
    STALE_RELEASE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    HIGH_REVISION_REASON,
    STALE_RELEASE_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_building_permits_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_building_permits_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_building_permits_surprise_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("api", "_", "key"),
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("can", "cel"),
        _join_parts("data", "base"),
        _join_parts("ex", "change"),
        _join_parts("li", "ve"),
        _join_parts("mut", "ation"),
        _join_parts("net", "work"),
        _join_parts("or", "der"),
        _join_parts("per", "sist"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("sub", "mit"),
        _join_parts("tok", "en"),
        _join_parts("tra", "de"),
        _join_parts("wal", "let"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchBuildingPermitsSurpriseDigestConfig",
    "MarketResearchBuildingPermitsSurpriseDigestInputRow",
    "MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount",
    "MarketResearchBuildingPermitsSurpriseDigestReport",
    "MarketResearchBuildingPermitsSurpriseDigestRow",
    "build_market_research_building_permits_surprise_digest",
    "market_research_building_permits_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBuildingPermitsSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_ratio: Decimal = Decimal("0.050000")
    max_revision_ratio: Decimal = Decimal("0.100000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBuildingPermitsSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchBuildingPermitsSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBuildingPermitsSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchBuildingPermitsSurpriseDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _require_positive_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "material_surprise_ratio",
            _require_ratio_decimal("material_surprise_ratio", self.material_surprise_ratio),
        )
        if self.material_surprise_ratio <= ZERO:
            raise ValueError("material_surprise_ratio must be positive")
        object.__setattr__(
            self,
            "max_revision_ratio",
            _require_ratio_decimal("max_revision_ratio", self.max_revision_ratio),
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
class MarketResearchBuildingPermitsSurpriseDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    permit_release_key: str
    permit_region: str
    public_release_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    forecast_permit_count: Decimal
    actual_permit_count: Decimal
    prior_permit_count: Decimal
    revised_prior_permit_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBuildingPermitsSurpriseDigestInputRow:
            raise TypeError(
                "MarketResearchBuildingPermitsSurpriseDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBuildingPermitsSurpriseDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchBuildingPermitsSurpriseDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "permit_release_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("permit_region", self.permit_region)
        _require_public_reference(
            "public_release_reference",
            self.public_release_reference,
        )
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
        object.__setattr__(
            self,
            "forecast_permit_count",
            _require_positive_count_decimal(
                "forecast_permit_count",
                self.forecast_permit_count,
            ),
        )
        object.__setattr__(
            self,
            "actual_permit_count",
            _require_nonnegative_count_decimal(
                "actual_permit_count",
                self.actual_permit_count,
            ),
        )
        object.__setattr__(
            self,
            "prior_permit_count",
            _require_positive_count_decimal(
                "prior_permit_count",
                self.prior_permit_count,
            ),
        )
        object.__setattr__(
            self,
            "revised_prior_permit_count",
            _require_nonnegative_count_decimal(
                "revised_prior_permit_count",
                self.revised_prior_permit_count,
            ),
        )
        if self.acknowledged_at is not None and self.acknowledged_at < self.released_at:
            raise ValueError("acknowledged_at cannot be before released_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchBuildingPermitsSurpriseDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    permit_release_key: str
    permit_region: str
    public_release_reference: str
    surprise_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    forecast_permit_count: Decimal
    actual_permit_count: Decimal
    prior_permit_count: Decimal
    revised_prior_permit_count: Decimal
    building_permits_surprise_count: Decimal
    abs_surprise_ratio: Decimal
    prior_revision_count: Decimal
    revision_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBuildingPermitsSurpriseDigestRow:
            raise TypeError(
                "MarketResearchBuildingPermitsSurpriseDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBuildingPermitsSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchBuildingPermitsSurpriseDigestRow",
            )
        for field_name in ("research_key", "condition_id", "permit_release_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("permit_region", self.permit_region)
        _require_public_reference(
            "public_release_reference",
            self.public_release_reference,
        )
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
        for field_name in (
            "source_count",
            "forecast_permit_count",
            "actual_permit_count",
            "prior_permit_count",
            "revised_prior_permit_count",
        ):
            normalizer = (
                _require_positive_count_decimal
                if field_name in {"forecast_permit_count", "prior_permit_count"}
                else _require_nonnegative_count_decimal
            )
            object.__setattr__(self, field_name, normalizer(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "building_permits_surprise_count",
            _require_signed_count_decimal(
                "building_permits_surprise_count",
                self.building_permits_surprise_count,
            ),
        )
        object.__setattr__(
            self,
            "abs_surprise_ratio",
            _require_ratio_decimal("abs_surprise_ratio", self.abs_surprise_ratio),
        )
        object.__setattr__(
            self,
            "prior_revision_count",
            _require_signed_count_decimal(
                "prior_revision_count",
                self.prior_revision_count,
            ),
        )
        object.__setattr__(
            self,
            "revision_ratio",
            _require_ratio_decimal("revision_ratio", self.revision_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount",
            )
        _require_report_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchBuildingPermitsSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    permit_release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    material_surprise_count: Decimal
    high_revision_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_abs_surprise_ratio: Decimal
    max_abs_surprise_ratio: Decimal
    average_revision_ratio: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchBuildingPermitsSurpriseDigestReport:
            raise TypeError(
                "MarketResearchBuildingPermitsSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBuildingPermitsSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchBuildingPermitsSurpriseDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BUILDING_PERMITS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_surprise_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "permit_release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "material_surprise_count",
            "high_revision_count",
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
            "average_abs_surprise_ratio",
            "max_abs_surprise_ratio",
            "average_revision_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_count",
            _require_nonnegative_decimal(
                "average_source_count",
                self.average_source_count,
            ),
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


def build_market_research_building_permits_surprise_digest(
    input_rows: Iterable[MarketResearchBuildingPermitsSurpriseDigestInputRow],
    *,
    config: MarketResearchBuildingPermitsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchBuildingPermitsSurpriseDigestReport:
    if type(config) is not MarketResearchBuildingPermitsSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBuildingPermitsSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(input_row, config=config, generated_at=generated_at_utc)
        for input_row in source_rows
    )
    ranked_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    permit_release_count = _count(len(ranked_rows))
    ready_release_count = _status_count(ranked_rows, STATUS_READY)
    watch_release_count = _status_count(ranked_rows, STATUS_WATCH)
    blocked_release_count = _status_count(ranked_rows, STATUS_BLOCKED)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_release_count=blocked_release_count,
        watch_release_count=watch_release_count,
    )

    return MarketResearchBuildingPermitsSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        permit_release_count=permit_release_count,
        ready_release_count=ready_release_count,
        watch_release_count=watch_release_count,
        blocked_release_count=blocked_release_count,
        material_surprise_count=_reason_row_count(ranked_rows, MATERIAL_SURPRISE_REASON),
        high_revision_count=_reason_row_count(ranked_rows, HIGH_REVISION_REASON),
        stale_release_count=_reason_row_count(ranked_rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_row_count(ranked_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_row_count(
            ranked_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_row_count(
            ranked_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        average_abs_surprise_ratio=_ratio(
            _sum_decimal(row.abs_surprise_ratio for row in ranked_rows),
            permit_release_count,
        ),
        max_abs_surprise_ratio=max(
            (row.abs_surprise_ratio for row in ranked_rows),
            default=ZERO,
        ),
        average_revision_ratio=_ratio(
            _sum_decimal(row.revision_ratio for row in ranked_rows),
            permit_release_count,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ranked_rows),
            permit_release_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_building_permits_surprise_digest_payload(
    report: MarketResearchBuildingPermitsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBuildingPermitsSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchBuildingPermitsSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchBuildingPermitsSurpriseDigestInputRow],
    generated_at: datetime,
) -> tuple[MarketResearchBuildingPermitsSurpriseDigestInputRow, ...]:
    if isinstance(input_rows, (str, bytes)):
        raise ValueError("input rows must contain building permits rows")
    try:
        normalized = tuple(input_rows)
    except TypeError as exc:
        raise ValueError("input rows must contain building permits rows") from exc
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchBuildingPermitsSurpriseDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchBuildingPermitsSurpriseDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (input_row.research_key, input_row.condition_id, input_row.permit_release_key)
        if key in seen:
            raise ValueError("input rows must use unique research condition release keys")
        seen.add(key)
        if input_row.released_at > generated_at:
            raise ValueError("released_at cannot be after generated_at")
        if input_row.acknowledged_at is not None and input_row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at cannot be after generated_at")
    return normalized


def _build_row(
    input_row: MarketResearchBuildingPermitsSurpriseDigestInputRow,
    *,
    config: MarketResearchBuildingPermitsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchBuildingPermitsSurpriseDigestRow:
    release_age_seconds = _seconds_between(input_row.released_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.released_at, input_row.acknowledged_at)
    )
    surprise_count = _finite_decimal(
        input_row.actual_permit_count - input_row.forecast_permit_count,
    )
    prior_revision_count = _finite_decimal(
        input_row.revised_prior_permit_count - input_row.prior_permit_count,
    )
    abs_surprise_ratio = _ratio(abs(surprise_count), input_row.forecast_permit_count)
    revision_ratio = _ratio(abs(prior_revision_count), input_row.prior_permit_count)
    reason_codes = _row_reason_codes(
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        abs_surprise_ratio=abs_surprise_ratio,
        revision_ratio=revision_ratio,
        config=config,
    )

    return MarketResearchBuildingPermitsSurpriseDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        market_slug=input_row.market_slug,
        permit_release_key=input_row.permit_release_key,
        permit_region=input_row.permit_region,
        public_release_reference=input_row.public_release_reference,
        surprise_status=_row_status(reason_codes),
        released_at=input_row.released_at,
        acknowledged_at=input_row.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        forecast_permit_count=input_row.forecast_permit_count,
        actual_permit_count=input_row.actual_permit_count,
        prior_permit_count=input_row.prior_permit_count,
        revised_prior_permit_count=input_row.revised_prior_permit_count,
        building_permits_surprise_count=surprise_count,
        abs_surprise_ratio=abs_surprise_ratio,
        prior_revision_count=prior_revision_count,
        revision_ratio=revision_ratio,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_count: Decimal,
    abs_surprise_ratio: Decimal,
    revision_ratio: Decimal,
    config: MarketResearchBuildingPermitsSurpriseDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if abs_surprise_ratio >= config.material_surprise_ratio:
        reasons.append(MATERIAL_SURPRISE_REASON)
    if revision_ratio > config.max_revision_ratio:
        reasons.append(HIGH_REVISION_REASON)
    if release_age_seconds > config.max_release_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        MISSING_ACKNOWLEDGEMENT_REASON in reason_codes
        or STALE_RELEASE_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _ranked_rows(
    rows: tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...],
) -> tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: MarketResearchBuildingPermitsSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str, str, str]:
    return (
        _status_rank(row.surprise_status),
        -row.abs_surprise_ratio,
        -row.release_age_seconds,
        row.market_slug,
        row.permit_release_key,
        row.condition_id,
        row.research_key,
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _reason_code_counts(
    rows: tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...],
) -> tuple[MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    total = _count(len(rows))
    counts: list[MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount] = []
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        count = _reason_row_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                row_ratio=_ratio(count, total),
            ),
        )
    return tuple(counts)


def _reason_row_count(
    rows: tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.surprise_status == status))


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


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchBuildingPermitsSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBuildingPermitsSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBuildingPermitsSurpriseDigestRow values",
            )
        _require_hard_flags("row", row)
        key = (row.research_key, row.condition_id, row.permit_release_key)
        if key in seen:
            raise ValueError("rows must use unique research condition release keys")
        seen.add(key)
    if rows != _ranked_rows(rows):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    items: object,
) -> tuple[MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBuildingPermitsSurpriseDigestReasonCodeCount values",
            )
        _require_hard_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must use unique reason codes")
        seen.add(item.reason_code)
    canonical = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if tuple(item.reason_code for item in items) != canonical:
        raise ValueError("reason_code_counts must use canonical sequence")
    return items


def _normalize_row_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_row_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must use unique reason codes")
        seen.add(reason_code)
    canonical = tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in seen)
    if normalized != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    if READY_REASON in seen and len(seen) != 1:
        raise ValueError("reason_codes ready must be exclusive")
    return normalized


def _normalize_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_report_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must use unique reason codes")
        seen.add(reason_code)
    canonical = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if normalized != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    if NO_INPUTS_REASON in seen and len(seen) != 1:
        raise ValueError("reason_codes no_inputs must be exclusive")
    return normalized


def _validate_row(row: MarketResearchBuildingPermitsSurpriseDigestRow) -> None:
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError(
                "acknowledgement_lag_seconds must be None when acknowledgement is missing",
            )
    elif row.acknowledgement_lag_seconds is None:
        raise ValueError(
            "acknowledgement_lag_seconds must be present when acknowledgement is present",
        )
    elif row.acknowledged_at < row.released_at:
        raise ValueError(
            "acknowledgement_lag_seconds must match acknowledged_at minus released_at",
        )
    elif row.acknowledgement_lag_seconds != _seconds_between(
        row.released_at,
        row.acknowledged_at,
    ):
        raise ValueError(
            "acknowledgement_lag_seconds must match acknowledged_at minus released_at",
        )
    if row.building_permits_surprise_count != _finite_decimal(
        row.actual_permit_count - row.forecast_permit_count,
    ):
        raise ValueError(
            "building_permits_surprise_count must match actual minus forecast",
        )
    if row.abs_surprise_ratio != _ratio(
        abs(row.building_permits_surprise_count),
        row.forecast_permit_count,
    ):
        raise ValueError("abs_surprise_ratio must match permit counts")
    if row.prior_revision_count != _finite_decimal(
        row.revised_prior_permit_count - row.prior_permit_count,
    ):
        raise ValueError("prior_revision_count must match prior permit counts")
    if row.revision_ratio != _ratio(abs(row.prior_revision_count), row.prior_permit_count):
        raise ValueError("revision_ratio must match prior permit counts")
    if row.surprise_status != _row_status(row.reason_codes):
        raise ValueError("surprise_status must match reason_codes")


def _validate_report(report: MarketResearchBuildingPermitsSurpriseDigestReport) -> None:
    if report.permit_release_count != _count(len(report.rows)):
        raise ValueError("permit_release_count must match rows")
    for status, field_name in (
        (STATUS_READY, "ready_release_count"),
        (STATUS_WATCH, "watch_release_count"),
        (STATUS_BLOCKED, "blocked_release_count"),
    ):
        expected = _status_count(report.rows, status)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    for reason_code, field_name in (
        (MATERIAL_SURPRISE_REASON, "material_surprise_count"),
        (HIGH_REVISION_REASON, "high_revision_count"),
        (STALE_RELEASE_REASON, "stale_release_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (MISSING_ACKNOWLEDGEMENT_REASON, "missing_acknowledgement_count"),
        (SLOW_ACKNOWLEDGEMENT_REASON, "slow_acknowledgement_count"),
    ):
        expected = _reason_row_count(report.rows, reason_code)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_abs_surprise_ratio != _ratio(
        _sum_decimal(row.abs_surprise_ratio for row in report.rows),
        report.permit_release_count,
    ):
        raise ValueError("average_abs_surprise_ratio must match rows")
    if report.max_abs_surprise_ratio != max(
        (row.abs_surprise_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_abs_surprise_ratio must match rows")
    if report.average_revision_ratio != _ratio(
        _sum_decimal(row.revision_ratio for row in report.rows),
        report.permit_release_count,
    ):
        raise ValueError("average_revision_ratio must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.permit_release_count,
    ):
        raise ValueError("average_source_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_release_count=report.blocked_release_count,
        watch_release_count=report.watch_release_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


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


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _finite_decimal(seconds + microseconds)


def _require_public_reference(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    lowered = value.lower()
    if any(marker in lowered for marker in ("://", "@", "?", "=")):
        raise ValueError(f"{field_name} must be a public reference")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain restricted text")
    return value


def _require_market_slug(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a lowercase slug")
    return value


def _require_surprise_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")
    return value


def _require_row_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in ROW_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known row reason codes")
    return value


def _require_report_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_count_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_signed_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(field_name, value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return _finite_decimal(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _finite_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total = _finite_decimal(total + value)
    return total


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(nested) for nested in value]
    if isinstance(value, list):
        return [_json_ready(nested) for nested in value]
    if type(value) in (float, int):
        raise ValueError("JSON value must use Decimal strings")
    return value
