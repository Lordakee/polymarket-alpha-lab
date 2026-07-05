"""Pure Phase 1 Empire State manufacturing surprise research reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_EMPIRE_STATE_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-empire-state-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SURPRISE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
STATUS_RANK = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}

REASON_PREFIX = "market_research_empire_state_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_empire_state_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_empire_state_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_empire_state_surprise_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SAFE_REFERENCE_PREFIXES = ("official-", "public-", "fred/", "nyfed/")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("api", "_", "key"),
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("ex", "change"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_EMPIRE_STATE_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchEmpireStateSurpriseDigestConfig",
    "MarketResearchEmpireStateSurpriseDigestInputRow",
    "MarketResearchEmpireStateSurpriseDigestReasonCodeCount",
    "MarketResearchEmpireStateSurpriseDigestReport",
    "MarketResearchEmpireStateSurpriseDigestRow",
    "build_market_research_empire_state_surprise_digest",
    "market_research_empire_state_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEmpireStateSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EMPIRE_STATE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold_points: Decimal = Decimal("6.000000")
    max_prior_revision_points: Decimal = Decimal("4.000000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchEmpireStateSurpriseDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEmpireStateSurpriseDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EMPIRE_STATE_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_release_age_seconds",
            "material_surprise_threshold_points",
            "max_prior_revision_points",
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
            "min_confirmation_ratio",
            _require_ratio_decimal("min_confirmation_ratio", self.min_confirmation_ratio),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEmpireStateSurpriseDigestInputRow:
    research_key: str
    condition_id: str
    release_key: str
    release_reference: str
    released_at: datetime
    source_count: Decimal
    forecast_index: Decimal
    actual_index: Decimal
    previous_prior_index: Decimal
    revised_prior_index: Decimal
    confirmation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchEmpireStateSurpriseDigestInputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEmpireStateSurpriseDigestInputRow,
            "input row",
        )
        for field_name in ("research_key", "condition_id", "release_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("release_reference", self.release_reference)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "forecast_index",
            "actual_index",
            "previous_prior_index",
            "revised_prior_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmation_ratio",
            _require_ratio_decimal("confirmation_ratio", self.confirmation_ratio),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEmpireStateSurpriseDigestRow:
    research_key: str
    condition_id: str
    release_key: str
    surprise_status: str
    released_at: datetime
    release_age_seconds: Decimal
    source_count: Decimal
    forecast_index: Decimal
    actual_index: Decimal
    previous_prior_index: Decimal
    revised_prior_index: Decimal
    surprise_delta: Decimal
    abs_surprise_points: Decimal
    prior_revision_points: Decimal
    abs_prior_revision_points: Decimal
    confirmation_ratio: Decimal
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchEmpireStateSurpriseDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchEmpireStateSurpriseDigestRow, "row")
        for field_name in ("research_key", "condition_id", "release_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_surprise_status("surprise_status", self.surprise_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "forecast_index",
            "actual_index",
            "previous_prior_index",
            "revised_prior_index",
            "surprise_delta",
            "abs_surprise_points",
            "prior_revision_points",
            "abs_prior_revision_points",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        if self.abs_surprise_points < ZERO:
            raise ValueError("abs_surprise_points must be nonnegative")
        if self.abs_prior_revision_points < ZERO:
            raise ValueError("abs_prior_revision_points must be nonnegative")
        object.__setattr__(
            self,
            "confirmation_ratio",
            _require_ratio_decimal("confirmation_ratio", self.confirmation_ratio),
        )
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
class MarketResearchEmpireStateSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchEmpireStateSurpriseDigestReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEmpireStateSurpriseDigestReasonCodeCount,
            "reason count",
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
class MarketResearchEmpireStateSurpriseDigestReport:
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
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_abs_surprise_points: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    average_abs_prior_revision_points: Decimal
    rows: tuple[MarketResearchEmpireStateSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchEmpireStateSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchEmpireStateSurpriseDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchEmpireStateSurpriseDigestReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EMPIRE_STATE_SURPRISE_DIGEST_CONFIG_VERSION
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
            "high_revision_count",
            "confirmation_gap_count",
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
            "average_abs_prior_revision_points",
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


def build_market_research_empire_state_surprise_digest(
    input_rows: list[MarketResearchEmpireStateSurpriseDigestInputRow]
    | tuple[MarketResearchEmpireStateSurpriseDigestInputRow, ...],
    *,
    config: MarketResearchEmpireStateSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchEmpireStateSurpriseDigestReport:
    if type(config) is not MarketResearchEmpireStateSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEmpireStateSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(row, config=config, generated_at=generated_at_utc)
                for row in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    release_count = _count(len(rows))
    ready_count = _status_count(rows, STATUS_READY)
    watch_count = _status_count(rows, STATUS_WATCH)
    blocked_count = _status_count(rows, STATUS_BLOCKED)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchEmpireStateSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        release_count=release_count,
        ready_release_count=ready_count,
        watch_release_count=watch_count,
        blocked_release_count=blocked_count,
        material_surprise_count=_reason_release_count(rows, MATERIAL_SURPRISE_REASON),
        stale_release_count=_reason_release_count(rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_release_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_release_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_release_count(rows, CONFIRMATION_GAP_REASON),
        average_abs_surprise_points=_average_decimal(
            tuple(row.abs_surprise_points for row in rows),
            denominator=release_count,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in rows),
            default=ZERO,
        ),
        average_source_count=_average_decimal(
            tuple(row.source_count for row in rows),
            denominator=release_count,
        ),
        average_abs_prior_revision_points=_average_decimal(
            tuple(row.abs_prior_revision_points for row in rows),
            denominator=release_count,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_empire_state_surprise_digest_payload(
    report: MarketResearchEmpireStateSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEmpireStateSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchEmpireStateSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(asdict(report))
    assert type(payload) is dict
    return payload


def _normalize_input_rows(
    input_rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchEmpireStateSurpriseDigestInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(input_rows)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchEmpireStateSurpriseDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchEmpireStateSurpriseDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        identity = (row.research_key, row.condition_id, row.release_key)
        if identity in seen:
            raise ValueError("duplicate input row identity")
        seen.add(identity)
        if row.released_at > generated_at:
            raise ValueError("released_at cannot be after generated_at")
    return rows


def _build_row(
    row: MarketResearchEmpireStateSurpriseDigestInputRow,
    *,
    config: MarketResearchEmpireStateSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchEmpireStateSurpriseDigestRow:
    release_age_seconds = _seconds_between(row.released_at, generated_at)
    surprise_delta = _finite_decimal(row.actual_index - row.forecast_index)
    abs_surprise_points = _finite_decimal(abs(surprise_delta))
    prior_revision_points = _finite_decimal(
        row.revised_prior_index - row.previous_prior_index,
    )
    abs_prior_revision_points = _finite_decimal(abs(prior_revision_points))
    reason_codes = _row_reason_codes(
        source_count=row.source_count,
        abs_surprise_points=abs_surprise_points,
        abs_prior_revision_points=abs_prior_revision_points,
        confirmation_ratio=row.confirmation_ratio,
        release_age_seconds=release_age_seconds,
        config=config,
    )
    return MarketResearchEmpireStateSurpriseDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        release_key=row.release_key,
        surprise_status=_row_status(reason_codes),
        released_at=row.released_at,
        release_age_seconds=release_age_seconds,
        source_count=row.source_count,
        forecast_index=row.forecast_index,
        actual_index=row.actual_index,
        previous_prior_index=row.previous_prior_index,
        revised_prior_index=row.revised_prior_index,
        surprise_delta=surprise_delta,
        abs_surprise_points=abs_surprise_points,
        prior_revision_points=prior_revision_points,
        abs_prior_revision_points=abs_prior_revision_points,
        confirmation_ratio=row.confirmation_ratio,
        redacted_release_reference=_redacted_reference(row.release_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    abs_surprise_points: Decimal,
    abs_prior_revision_points: Decimal,
    confirmation_ratio: Decimal,
    release_age_seconds: Decimal,
    config: MarketResearchEmpireStateSurpriseDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if abs_surprise_points >= config.material_surprise_threshold_points:
        reasons.append(MATERIAL_SURPRISE_REASON)
    if release_age_seconds > config.max_release_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if abs_prior_revision_points > config.max_prior_revision_points:
        reasons.append(HIGH_REVISION_REASON)
    if confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        STALE_RELEASE_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or HIGH_REVISION_REASON in reason_codes
        or CONFIRMATION_GAP_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(rows: tuple[MarketResearchEmpireStateSurpriseDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.surprise_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.surprise_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _status_count(
    rows: tuple[MarketResearchEmpireStateSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.surprise_status == status))


def _reason_release_count(
    rows: tuple[MarketResearchEmpireStateSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchEmpireStateSurpriseDigestRow, ...],
) -> tuple[MarketResearchEmpireStateSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchEmpireStateSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ZERO,
            ),
        )
    release_count = _count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    return tuple(
        MarketResearchEmpireStateSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            release_ratio=_ratio(_count(counts[reason_code]), release_count),
        )
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchEmpireStateSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchEmpireStateSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEmpireStateSurpriseDigestRow values",
            )
        _require_hard_flags("row", row)
        identity = (row.research_key, row.condition_id, row.release_key)
        if identity in seen:
            raise ValueError("rows must use unique research condition release identities")
        seen.add(identity)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[MarketResearchEmpireStateSurpriseDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not MarketResearchEmpireStateSurpriseDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(value.reason_code)
    expected = tuple(sorted(values, key=lambda item: _reason_code_rank(item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return values


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    if READY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes ready cannot be combined")
    expected = tuple(
        reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    expected = tuple(
        reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_row(row: MarketResearchEmpireStateSurpriseDigestRow) -> None:
    surprise_delta = _finite_decimal(row.actual_index - row.forecast_index)
    if row.surprise_delta != surprise_delta:
        raise ValueError("surprise_delta must match actual_index minus forecast_index")
    if row.abs_surprise_points != _finite_decimal(abs(surprise_delta)):
        raise ValueError("abs_surprise_points must match absolute surprise_delta")
    prior_revision_points = _finite_decimal(
        row.revised_prior_index - row.previous_prior_index,
    )
    if row.prior_revision_points != prior_revision_points:
        raise ValueError(
            "prior_revision_points must match revised minus previous prior index",
        )
    if row.abs_prior_revision_points != _finite_decimal(abs(prior_revision_points)):
        raise ValueError(
            "abs_prior_revision_points must match absolute prior_revision_points",
        )
    if row.surprise_status != _row_status(row.reason_codes):
        raise ValueError("surprise_status must match reason_codes")


def _validate_report(report: MarketResearchEmpireStateSurpriseDigestReport) -> None:
    if report.release_count != _count(len(report.rows)):
        raise ValueError("release_count must match rows")
    expected_status_counts = (
        ("ready_release_count", _status_count(report.rows, STATUS_READY)),
        ("watch_release_count", _status_count(report.rows, STATUS_WATCH)),
        ("blocked_release_count", _status_count(report.rows, STATUS_BLOCKED)),
    )
    for field_name, expected in expected_status_counts:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(report.rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    for row in report.rows:
        if row.released_at > report.generated_at:
            raise ValueError("row released_at cannot be after generated_at")
        if row.release_age_seconds != _seconds_between(
            row.released_at,
            report.generated_at,
        ):
            raise ValueError("row release_age_seconds must match generated_at")
    _validate_report_metric(report, "material_surprise_count", MATERIAL_SURPRISE_REASON)
    _validate_report_metric(report, "stale_release_count", STALE_RELEASE_REASON)
    _validate_report_metric(report, "thin_source_count", THIN_SOURCES_REASON)
    _validate_report_metric(report, "high_revision_count", HIGH_REVISION_REASON)
    _validate_report_metric(report, "confirmation_gap_count", CONFIRMATION_GAP_REASON)
    release_count = report.release_count
    if report.average_abs_surprise_points != _average_decimal(
        tuple(row.abs_surprise_points for row in report.rows),
        denominator=release_count,
    ):
        raise ValueError("average_abs_surprise_points must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_source_count != _average_decimal(
        tuple(row.source_count for row in report.rows),
        denominator=release_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.average_abs_prior_revision_points != _average_decimal(
        tuple(row.abs_prior_revision_points for row in report.rows),
        denominator=release_count,
    ):
        raise ValueError("average_abs_prior_revision_points must match rows")


def _validate_report_metric(
    report: MarketResearchEmpireStateSurpriseDigestReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_release_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _row_sort_key(
    row: MarketResearchEmpireStateSurpriseDigestRow,
) -> tuple[int, str, str, str]:
    return (
        STATUS_RANK[row.surprise_status],
        row.release_key,
        row.research_key,
        row.condition_id,
    )


def _reason_code_rank(reason_code: str) -> int:
    return REPORT_REASON_CODE_SEQUENCE.index(reason_code)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} paper_only/report_only/readonly must be True")


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if any(fragment in text.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public identifier")
    return text


def _require_reference(field_name: str, value: object) -> str:
    return _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if _looks_like_redacted_hash(text):
        return text
    if _reference_is_safe_public(text):
        return text
    raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_surprise_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be a known surprise status")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware with a non-None UTC offset",
        )
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("seconds", seconds + micros)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _finite_decimal(decimal_value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _finite_decimal(decimal_value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


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
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    normalized = _finite_decimal(decimal_value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    return _finite_decimal(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


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


def _average_decimal(values: tuple[Decimal, ...], *, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / denominator).quantize(QUANT)


def _redacted_reference(value: str) -> str:
    if _reference_is_safe_public(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _reference_is_safe_public(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "=" in lowered:
        return False
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        return False
    return value.startswith(SAFE_REFERENCE_PREFIXES)


def _looks_like_redacted_hash(value: str) -> bool:
    prefix = "sha256:"
    if not value.startswith(prefix) or len(value) != len(prefix) + 12:
        return False
    digest = value[len(prefix) :]
    return all(character in "0123456789abcdef" for character in digest)


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
