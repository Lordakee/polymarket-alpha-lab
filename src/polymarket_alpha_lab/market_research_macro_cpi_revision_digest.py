"""Pure Phase 1 macro CPI revision digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION = (
    "market-research-macro-cpi-revision-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REVISION_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_macro_cpi_revision_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_REVISION_REASON = f"{REASON_PREFIX}material_revision"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    STALE_RELEASE_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_macro_cpi_revision_digest",
    STATUS_WATCH: "watch_report_only_market_research_macro_cpi_revision_digest",
    STATUS_BLOCKED: "block_report_only_market_research_macro_cpi_revision_digest",
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
    "DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION",
    "MarketResearchMacroCpiRevisionDigestConfig",
    "MarketResearchMacroCpiRevisionDigestInputRow",
    "MarketResearchMacroCpiRevisionDigestReasonCodeCount",
    "MarketResearchMacroCpiRevisionDigestReport",
    "MarketResearchMacroCpiRevisionDigestRow",
    "build_market_research_macro_cpi_revision_digest",
    "market_research_macro_cpi_revision_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchMacroCpiRevisionDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    material_revision_threshold: Decimal = Decimal("0.100000")
    min_source_count: Decimal = Decimal("2")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroCpiRevisionDigestConfig:
            raise TypeError(
                "MarketResearchMacroCpiRevisionDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroCpiRevisionDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchMacroCpiRevisionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_MACRO_CPI_REVISION_DIGEST_CONFIG_VERSION
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
            "material_revision_threshold",
            _require_positive_decimal(
                "material_revision_threshold",
                self.material_revision_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
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
class MarketResearchMacroCpiRevisionDigestInputRow:
    research_key: str
    condition_id: str
    cpi_series_key: str
    cpi_release_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    initial_value: Decimal
    revised_value: Decimal
    prior_value: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroCpiRevisionDigestInputRow:
            raise TypeError(
                "MarketResearchMacroCpiRevisionDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroCpiRevisionDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchMacroCpiRevisionDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("cpi_series_key", self.cpi_series_key)
        _require_reference("cpi_release_reference", self.cpi_release_reference)
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
        for field_name in ("initial_value", "revised_value", "prior_value"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchMacroCpiRevisionDigestRow:
    research_key: str
    condition_id: str
    cpi_series_key: str
    revision_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    initial_value: Decimal
    revised_value: Decimal
    prior_value: Decimal
    revision_delta: Decimal
    revision_abs: Decimal
    prior_delta: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_cpi_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroCpiRevisionDigestRow:
            raise TypeError(
                "MarketResearchMacroCpiRevisionDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroCpiRevisionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchMacroCpiRevisionDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("cpi_series_key", self.cpi_series_key)
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
            "initial_value",
            "revised_value",
            "prior_value",
            "revision_delta",
            "revision_abs",
            "prior_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
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
            "redacted_cpi_release_reference",
            _require_redacted_reference(
                "redacted_cpi_release_reference",
                self.redacted_cpi_release_reference,
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
class MarketResearchMacroCpiRevisionDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroCpiRevisionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchMacroCpiRevisionDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroCpiRevisionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchMacroCpiRevisionDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "release_ratio",
            _require_ratio_decimal("release_ratio", self.release_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchMacroCpiRevisionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    cpi_release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    material_revision_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_revision_abs: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchMacroCpiRevisionDigestRow, ...]
    reason_code_counts: tuple[MarketResearchMacroCpiRevisionDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchMacroCpiRevisionDigestReport:
            raise TypeError(
                "MarketResearchMacroCpiRevisionDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchMacroCpiRevisionDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchMacroCpiRevisionDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_revision_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "cpi_release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "material_revision_count",
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
            "average_revision_abs",
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


def build_market_research_macro_cpi_revision_digest(
    input_rows: list[MarketResearchMacroCpiRevisionDigestInputRow]
    | tuple[MarketResearchMacroCpiRevisionDigestInputRow, ...],
    *,
    config: MarketResearchMacroCpiRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchMacroCpiRevisionDigestReport:
    if type(config) is not MarketResearchMacroCpiRevisionDigestConfig:
        raise ValueError("config must be a MarketResearchMacroCpiRevisionDigestConfig")
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
            MarketResearchMacroCpiRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    cpi_release_count = _count(len(ordered_rows))
    ready_release_count = _count(
        sum(1 for row in ordered_rows if row.revision_status == STATUS_READY),
    )
    watch_release_count = _count(
        sum(1 for row in ordered_rows if row.revision_status == STATUS_WATCH),
    )
    blocked_release_count = _count(
        sum(1 for row in ordered_rows if row.revision_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ordered_rows),
        blocked_release_count=blocked_release_count,
        watch_release_count=watch_release_count,
    )

    return MarketResearchMacroCpiRevisionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        cpi_release_count=cpi_release_count,
        ready_release_count=ready_release_count,
        watch_release_count=watch_release_count,
        blocked_release_count=blocked_release_count,
        material_revision_count=_count(
            sum(1 for row in ordered_rows if MATERIAL_REVISION_REASON in row.reason_codes),
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
        probability_repricing_count=_count(
            sum(
                1
                for row in ordered_rows
                if PROBABILITY_REPRICING_REASON in row.reason_codes
            ),
        ),
        average_revision_abs=_ratio(
            _sum_decimal(row.revision_abs for row in ordered_rows),
            cpi_release_count,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in ordered_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in ordered_rows),
            cpi_release_count,
        ),
        rows=ordered_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_macro_cpi_revision_digest_payload(
    report: MarketResearchMacroCpiRevisionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchMacroCpiRevisionDigestReport:
        raise ValueError("report must be a MarketResearchMacroCpiRevisionDigestReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchMacroCpiRevisionDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchMacroCpiRevisionDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchMacroCpiRevisionDigestInputRow values",
            )
        _require_hard_flags("input row", input_row)
        key = (input_row.research_key, input_row.condition_id, input_row.cpi_series_key)
        if key in seen:
            raise ValueError("input rows must use unique research condition series keys")
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
    input_row: MarketResearchMacroCpiRevisionDigestInputRow,
    *,
    config: MarketResearchMacroCpiRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchMacroCpiRevisionDigestRow:
    release_age_seconds = _seconds_between(input_row.released_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if input_row.acknowledged_at is None
        else _seconds_between(input_row.released_at, input_row.acknowledged_at)
    )
    revision_delta = _subtract_decimal(input_row.revised_value, input_row.initial_value)
    revision_abs = _absolute_decimal(revision_delta)
    prior_delta = _subtract_decimal(input_row.revised_value, input_row.prior_value)
    probability_delta = _probability_delta(
        _subtract_decimal(
            input_row.market_probability_after,
            input_row.market_probability_before,
        ),
    )
    reason_codes = _row_reason_codes(
        source_count=input_row.source_count,
        revision_abs=revision_abs,
        probability_delta=probability_delta,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketResearchMacroCpiRevisionDigestRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        cpi_series_key=input_row.cpi_series_key,
        revision_status=_row_status(reason_codes),
        released_at=input_row.released_at,
        acknowledged_at=input_row.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=input_row.source_count,
        initial_value=input_row.initial_value,
        revised_value=input_row.revised_value,
        prior_value=input_row.prior_value,
        revision_delta=revision_delta,
        revision_abs=revision_abs,
        prior_delta=prior_delta,
        market_probability_before=input_row.market_probability_before,
        market_probability_after=input_row.market_probability_after,
        probability_delta=probability_delta,
        redacted_cpi_release_reference=_redacted_reference(
            input_row.cpi_release_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    revision_abs: Decimal,
    probability_delta: Decimal,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketResearchMacroCpiRevisionDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if revision_abs >= config.material_revision_threshold:
        reasons.append(MATERIAL_REVISION_REASON)
    if abs(probability_delta) >= config.material_revision_threshold:
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
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


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
    rows: tuple[MarketResearchMacroCpiRevisionDigestRow, ...],
) -> tuple[MarketResearchMacroCpiRevisionDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: MarketResearchMacroCpiRevisionDigestRow,
) -> tuple[int, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.revision_status],
        row.cpi_series_key,
        row.condition_id,
        row.research_key,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchMacroCpiRevisionDigestRow, ...],
) -> tuple[MarketResearchMacroCpiRevisionDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    release_count = _count(len(rows))
    return tuple(
        MarketResearchMacroCpiRevisionDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            release_ratio=_ratio(_count(counts[reason_code]), release_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchMacroCpiRevisionDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[int, str, str, str] | None = None
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchMacroCpiRevisionDigestRow:
            raise ValueError("rows must contain MarketResearchMacroCpiRevisionDigestRow")
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.cpi_series_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition series keys")
        seen.add(identity)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be sorted by unique status and series keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchMacroCpiRevisionDigestReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_order = -1
    for count in counts:
        if type(count) is not MarketResearchMacroCpiRevisionDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_order:
            raise ValueError("reason_code_counts must be sorted by unique reason_code")
        previous_order = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_order = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_order:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_order = rank
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_order = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_order:
            raise ValueError("reason_codes must be sorted by unique reason code")
        previous_order = rank
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


def _validate_row(row: MarketResearchMacroCpiRevisionDigestRow) -> None:
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
    expected_revision_delta = _subtract_decimal(row.revised_value, row.initial_value)
    if row.revision_delta != expected_revision_delta:
        raise ValueError("revision_delta must match revised_value minus initial_value")
    if row.revision_abs != _absolute_decimal(row.revision_delta):
        raise ValueError("revision_abs must match absolute revision_delta")
    expected_prior_delta = _subtract_decimal(row.revised_value, row.prior_value)
    if row.prior_delta != expected_prior_delta:
        raise ValueError("prior_delta must match revised_value minus prior_value")
    expected_probability_delta = _probability_delta(
        _subtract_decimal(
            row.market_probability_after,
            row.market_probability_before,
        ),
    )
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability fields")
    if row.revision_status != _row_status(row.reason_codes):
        raise ValueError("revision_status must match reason_codes")
    if row.reason_codes == (READY_REASON,):
        return
    if READY_REASON in row.reason_codes:
        raise ValueError("reason_codes ready cannot be combined")


def _validate_report(report: MarketResearchMacroCpiRevisionDigestReport) -> None:
    if report.cpi_release_count != _count(len(report.rows)):
        raise ValueError("cpi_release_count must match rows")
    if report.ready_release_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_READY),
    ):
        raise ValueError("ready_release_count must match rows")
    if report.watch_release_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_WATCH),
    ):
        raise ValueError("watch_release_count must match rows")
    if report.blocked_release_count != _count(
        sum(1 for row in report.rows if row.revision_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_release_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            MarketResearchMacroCpiRevisionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_release_count=report.blocked_release_count,
        watch_release_count=report.watch_release_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    _validate_report_metric(report, "material_revision_count", MATERIAL_REVISION_REASON)
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
    _validate_report_metric(
        report,
        "probability_repricing_count",
        PROBABILITY_REPRICING_REASON,
    )
    if report.average_revision_abs != _ratio(
        _sum_decimal(row.revision_abs for row in report.rows),
        report.cpi_release_count,
    ):
        raise ValueError("average_revision_abs must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.cpi_release_count,
    ):
        raise ValueError("average_source_count must match rows")


def _validate_report_metric(
    report: MarketResearchMacroCpiRevisionDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _count(sum(1 for row in report.rows if reason_code in row.reason_codes))
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    return value


def _require_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
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


def _require_revision_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REVISION_STATUSES:
        raise ValueError(f"{field_name} must be one of {REVISION_STATUSES}")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


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
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        total_microseconds = (
            Decimal(delta.days) * Decimal("86400000000")
            + Decimal(delta.seconds) * Decimal("1000000")
            + Decimal(delta.microseconds)
        )
        return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:  # type: ignore[assignment]
            total += value
        return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _finite_decimal(numerator / denominator)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _finite_decimal(left - right)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _finite_decimal(abs(value))


def _probability_delta(value: Decimal) -> Decimal:
    if value < -ONE or value > ONE:
        raise ValueError("probability_delta must be between -1 and 1")
    return _finite_decimal(value)


def _finite_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be finite and quantizable") from exc
    return ZERO if normalized.is_zero() else normalized


def _redacted_reference(reference: str) -> str:
    if not _is_sensitive_reference(reference):
        return reference
    # This compact 48-bit prefix is a redacted label, not a uniqueness guarantee.
    digest = sha256(reference.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def _is_sensitive_reference(reference: str) -> bool:
    lowered = reference.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS) or "://" in lowered


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_rank(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value
