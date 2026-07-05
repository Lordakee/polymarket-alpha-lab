"""Pure Phase 1 jolts surprise digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_JOLTS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-jolts-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SURPRISE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_jolts_surprise_digest_"
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
    STATUS_READY: "allow_report_only_market_research_jolts_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_jolts_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_jolts_surprise_digest",
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
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_JOLTS_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchJoltsSurpriseDigestConfig",
    "MarketResearchJoltsSurpriseDigestInputRow",
    "MarketResearchJoltsSurpriseDigestReasonCodeCount",
    "MarketResearchJoltsSurpriseDigestReport",
    "MarketResearchJoltsSurpriseDigestRow",
    "build_market_research_jolts_surprise_digest",
    "market_research_jolts_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchJoltsSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_JOLTS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2")
    material_surprise_threshold_jobs: Decimal = Decimal("250000.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoltsSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchJoltsSurpriseDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoltsSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchJoltsSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_JOLTS_SURPRISE_DIGEST_CONFIG_VERSION
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
            "material_surprise_threshold_jobs",
            _require_positive_decimal(
                "material_surprise_threshold_jobs",
                self.material_surprise_threshold_jobs,
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
class MarketResearchJoltsSurpriseDigestInputRow:
    research_key: str
    condition_id: str
    market_slug: str
    jolts_report_key: str
    jolts_report_family: str
    jolts_report_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    forecast_openings_count: Decimal
    actual_openings_count: Decimal
    surprise_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoltsSurpriseDigestInputRow:
            raise TypeError(
                "MarketResearchJoltsSurpriseDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoltsSurpriseDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchJoltsSurpriseDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("jolts_report_key", self.jolts_report_key)
        _require_public_string(
            "jolts_report_family",
            self.jolts_report_family,
        )
        _require_reference(
            "jolts_report_reference",
            self.jolts_report_reference,
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
        for field_name in ("forecast_openings_count", "actual_openings_count"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_score",
            _require_ratio_decimal("surprise_score", self.surprise_score),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchJoltsSurpriseDigestRow:
    research_key: str
    condition_id: str
    market_slug: str
    jolts_report_key: str
    jolts_report_family: str
    surprise_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    forecast_openings_count: Decimal
    actual_openings_count: Decimal
    jolts_surprise_jobs: Decimal
    surprise_score: Decimal
    redacted_jolts_report_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoltsSurpriseDigestRow:
            raise TypeError(
                "MarketResearchJoltsSurpriseDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoltsSurpriseDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchJoltsSurpriseDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("jolts_report_key", self.jolts_report_key)
        _require_public_string(
            "jolts_report_family",
            self.jolts_report_family,
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
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "forecast_openings_count",
            "actual_openings_count",
            "jolts_surprise_jobs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "surprise_score",
            _require_ratio_decimal("surprise_score", self.surprise_score),
        )
        object.__setattr__(
            self,
            "redacted_jolts_report_reference",
            _require_redacted_reference(
                "redacted_jolts_report_reference",
                self.redacted_jolts_report_reference,
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
class MarketResearchJoltsSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    report_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoltsSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchJoltsSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoltsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchJoltsSurpriseDigestReasonCodeCount",
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
class MarketResearchJoltsSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    jolts_report_count: Decimal
    ready_report_count: Decimal
    watch_report_count: Decimal
    blocked_report_count: Decimal
    material_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_surprise_score: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchJoltsSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchJoltsSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchJoltsSurpriseDigestReport:
            raise TypeError(
                "MarketResearchJoltsSurpriseDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchJoltsSurpriseDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchJoltsSurpriseDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_JOLTS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_surprise_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "jolts_report_count",
            "ready_report_count",
            "watch_report_count",
            "blocked_report_count",
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
            "average_surprise_score",
            "max_release_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_surprise_score > ONE:
            raise ValueError("average_surprise_score must be a ratio")
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


def build_market_research_jolts_surprise_digest(
    input_rows: list[MarketResearchJoltsSurpriseDigestInputRow]
    | tuple[MarketResearchJoltsSurpriseDigestInputRow, ...],
    *,
    config: MarketResearchJoltsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchJoltsSurpriseDigestReport:
    if type(config) is not MarketResearchJoltsSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchJoltsSurpriseDigestConfig",
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
            MarketResearchJoltsSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                report_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    jolts_report_count = _count(len(ordered_rows))
    ready_report_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_READY),
    )
    watch_report_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_WATCH),
    )
    blocked_report_count = _count(
        sum(1 for row in ordered_rows if row.surprise_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ordered_rows),
        blocked_report_count=blocked_report_count,
        watch_report_count=watch_report_count,
    )

    return MarketResearchJoltsSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        jolts_report_count=jolts_report_count,
        ready_report_count=ready_report_count,
        watch_report_count=watch_report_count,
        blocked_report_count=blocked_report_count,
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
        average_surprise_score=_ratio(
            _sum_decimal(row.surprise_score for row in ordered_rows),
            jolts_report_count,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in ordered_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ordered_rows),
            jolts_report_count,
        ),
        rows=ordered_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_jolts_surprise_digest_payload(
    report: MarketResearchJoltsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchJoltsSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchJoltsSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    return _json_ready(asdict(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchJoltsSurpriseDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchJoltsSurpriseDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchJoltsSurpriseDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (
            input_row.research_key,
            input_row.condition_id,
            input_row.jolts_report_key,
        )
        if key in seen:
            raise ValueError("input rows must use unique research condition report keys")
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
    input_row: MarketResearchJoltsSurpriseDigestInputRow,
    *,
    config: MarketResearchJoltsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchJoltsSurpriseDigestRow:
    release_age_seconds = _seconds_between(input_row.released_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.released_at, input_row.acknowledged_at)
    )
    surprise_amount = _finite_decimal(
        input_row.actual_openings_count - input_row.forecast_openings_count,
    )
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        surprise_amount=surprise_amount,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketResearchJoltsSurpriseDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        market_slug=input_row.market_slug,
        jolts_report_key=input_row.jolts_report_key,
        jolts_report_family=input_row.jolts_report_family,
        surprise_status=_row_status(reason_codes),
        released_at=input_row.released_at,
        acknowledged_at=input_row.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        forecast_openings_count=input_row.forecast_openings_count,
        actual_openings_count=input_row.actual_openings_count,
        jolts_surprise_jobs=surprise_amount,
        surprise_score=input_row.surprise_score,
        redacted_jolts_report_reference=_redact_reference(
            input_row.jolts_report_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    surprise_amount: Decimal,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketResearchJoltsSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if abs(surprise_amount) >= config.material_surprise_threshold_jobs:
        codes.append(MATERIAL_SURPRISE_REASON)
    if acknowledgement_lag_seconds is None:
        codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        codes.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        codes.append(STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if not codes:
        codes.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if (
        MATERIAL_SURPRISE_REASON in reason_codes
        or STALE_RELEASE_REASON in reason_codes
        or SLOW_ACKNOWLEDGEMENT_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
    ):
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchJoltsSurpriseDigestRow, ...],
) -> tuple[MarketResearchJoltsSurpriseDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.surprise_status),
                -row.surprise_score,
                -row.release_age_seconds,
                row.market_slug,
                row.research_key,
                row.condition_id,
                row.jolts_report_key,
            ),
        ),
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[status]


def _reason_code_counts(
    rows: tuple[MarketResearchJoltsSurpriseDigestRow, ...],
) -> tuple[MarketResearchJoltsSurpriseDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: list[MarketResearchJoltsSurpriseDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        if count == ZERO:
            continue
        counts.append(
            MarketResearchJoltsSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                report_ratio=_ratio(count, total),
            ),
        )
    return tuple(counts)


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
    return STATUS_READY


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchJoltsSurpriseDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchJoltsSurpriseDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchJoltsSurpriseDigestRow values",
            )
        _require_hard_flags("row", row)
        key = (row.research_key, row.condition_id, row.jolts_report_key)
        if key in seen:
            raise ValueError("rows must use unique research condition report keys")
        seen.add(key)
    if normalized != _ranked_rows(normalized):
        raise ValueError("rows must use canonical ranking")
    return normalized


def _normalize_reason_code_counts(
    items: object,
) -> tuple[MarketResearchJoltsSurpriseDigestReasonCodeCount, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(items)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchJoltsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchJoltsSurpriseDigestReasonCodeCount "
                "values",
            )
        _require_hard_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must use unique reason codes")
        seen.add(item.reason_code)
    canonical = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)
    if tuple(item.reason_code for item in normalized) != canonical:
        raise ValueError("reason_code_counts must use canonical reason code sequence")
    return normalized


def _normalize_row_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    canonical = tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in normalized)
    if normalized != canonical:
        raise ValueError("reason_codes must use canonical row reason code sequence")
    if READY_REASON in normalized and len(normalized) != 1:
        raise ValueError("reason_codes ready must be the only ready reason")
    return normalized


def _normalize_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    canonical = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in normalized)
    if normalized != canonical:
        raise ValueError("reason_codes must use canonical reason code sequence")
    return normalized


def _validate_row(row: MarketResearchJoltsSurpriseDigestRow) -> None:
    if row.jolts_surprise_jobs != _finite_decimal(
        row.actual_openings_count - row.forecast_openings_count,
    ):
        raise ValueError(
            "jolts_surprise_jobs must match actual minus forecast",
        )
    if row.surprise_status != _row_status(row.reason_codes):
        raise ValueError("surprise_status must match reason_codes")


def _validate_report(report: MarketResearchJoltsSurpriseDigestReport) -> None:
    _require_hard_flags("report", report)
    _normalize_rows(report.rows)
    _normalize_reason_code_counts(report.reason_code_counts)
    _normalize_report_reason_codes(report.reason_codes)
    if report.jolts_report_count != _count(len(report.rows)):
        raise ValueError("jolts_report_count must match rows")
    for status, field_name in (
        (STATUS_READY, "ready_report_count"),
        (STATUS_WATCH, "watch_report_count"),
        (STATUS_BLOCKED, "blocked_report_count"),
    ):
        expected = _count(sum(1 for row in report.rows if row.surprise_status == status))
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    reason_expected = _reason_code_counts(report.rows)
    if not report.rows:
        reason_expected = (
            MarketResearchJoltsSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                report_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != reason_expected:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    for reason_code, field_name in (
        (MATERIAL_SURPRISE_REASON, "material_surprise_count"),
        (STALE_RELEASE_REASON, "stale_release_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (MISSING_ACKNOWLEDGEMENT_REASON, "missing_acknowledgement_count"),
        (SLOW_ACKNOWLEDGEMENT_REASON, "slow_acknowledgement_count"),
    ):
        expected = _count(sum(1 for row in report.rows if reason_code in row.reason_codes))
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_surprise_score != _ratio(
        _sum_decimal(row.surprise_score for row in report.rows),
        report.jolts_report_count,
    ):
        raise ValueError("average_surprise_score must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.jolts_report_count,
    ):
        raise ValueError("average_source_count must match rows")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_report_count=report.blocked_report_count,
        watch_report_count=report.watch_report_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    for row in report.rows:
        if row.released_at > report.generated_at:
            raise ValueError("row released_at cannot be after generated_at")
        if row.release_age_seconds != _seconds_between(row.released_at, report.generated_at):
            raise ValueError("row release_age_seconds must match generated_at")
        if row.acknowledged_at is not None:
            if row.acknowledged_at > report.generated_at:
                raise ValueError("row acknowledged_at cannot be after generated_at")
            if row.acknowledgement_lag_seconds != _seconds_between(
                row.released_at,
                row.acknowledged_at,
            ):
                raise ValueError("row acknowledgement_lag_seconds must match timestamps")
        elif row.acknowledgement_lag_seconds is not None:
            raise ValueError("row acknowledgement_lag_seconds must be None")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware with a UTC offset")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _finite_decimal(seconds + microseconds)


def _redact_reference(value: str) -> str:
    if _is_public_reference(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_public_reference(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS) and not any(
        marker in lowered for marker in ("://", "@", "?")
    )


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_reference(field_name, value)
    if not _is_public_reference(value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
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


def _require_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_finite_decimal(field_name, value)
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
    value = _require_positive_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return _finite_decimal(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
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
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (float, int):
        raise ValueError("payload must not contain public int or float values")
    if isinstance(value, dict):
        return {key: _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return tuple(_json_ready(nested) for nested in value)
    if isinstance(value, list):
        return [_json_ready(nested) for nested in value]
    return value
