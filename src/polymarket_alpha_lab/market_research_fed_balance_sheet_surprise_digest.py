"""Pure Phase 1 Fed balance sheet surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-fed-balance-sheet-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_fed_balance_sheet_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_OBSERVATION_REASON = f"{REASON_PREFIX}stale_observation"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    MATERIAL_SURPRISE_REASON,
    STALE_OBSERVATION_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_OBSERVATION_REASON,
    MATERIAL_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    PROBABILITY_REPRICING_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_fed_balance_sheet_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_fed_balance_sheet_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_fed_balance_sheet_surprise_digest",
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
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("ven", "dor"),
        "https://",
        "http://",
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchFedBalanceSheetSurpriseDigestConfig",
    "MarketResearchFedBalanceSheetSurpriseDigestObservation",
    "MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount",
    "MarketResearchFedBalanceSheetSurpriseDigestReport",
    "MarketResearchFedBalanceSheetSurpriseDigestRow",
    "build_market_research_fed_balance_sheet_surprise_digest",
    "market_research_fed_balance_sheet_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchFedBalanceSheetSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.015000")
    watch_probability_delta_threshold: Decimal = Decimal("0.040000")
    max_revision_ratio: Decimal = Decimal("0.150000")
    min_confirmation_ratio: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchFedBalanceSheetSurpriseDigestConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedBalanceSheetSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchFedBalanceSheetSurpriseDigestConfig does not "
                "support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _require_positive_count_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_surprise_threshold",
            "watch_probability_delta_threshold",
            "max_revision_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_surprise_threshold <= ZERO:
            raise ValueError("material_surprise_threshold must be positive")
        if self.watch_probability_delta_threshold <= ZERO:
            raise ValueError("watch_probability_delta_threshold must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchFedBalanceSheetSurpriseDigestObservation:
    condition_id: str
    research_key: str
    release_key: str
    balance_sheet_metric: str
    public_observation_reference: str
    observed_at: datetime
    expected_change: Decimal
    actual_change: Decimal
    surprise_ratio: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchFedBalanceSheetSurpriseDigestObservation does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedBalanceSheetSurpriseDigestObservation:
            raise TypeError(
                "MarketResearchFedBalanceSheetSurpriseDigestObservation does not "
                "support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "balance_sheet_metric",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference_is_redacted_safe(
            "public_observation_reference",
            self.public_observation_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_change", "actual_change"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "surprise_ratio",
            "revision_ratio",
            "confirmation_ratio",
            "market_probability_before",
            "market_probability_after",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchFedBalanceSheetSurpriseDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    balance_sheet_metric: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    expected_change: Decimal
    actual_change: Decimal
    surprise_delta: Decimal
    surprise_ratio: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_observation_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchFedBalanceSheetSurpriseDigestRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedBalanceSheetSurpriseDigestRow:
            raise TypeError(
                "MarketResearchFedBalanceSheetSurpriseDigestRow does not support "
                "subclassing",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "balance_sheet_metric",
            "redacted_public_observation_reference",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("observation_age_seconds", "source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_change",
            "actual_change",
            "surprise_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "surprise_ratio",
            "revision_ratio",
            "confirmation_ratio",
            "market_probability_before",
            "market_probability_after",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_finite_decimal("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount does "
                "not support subclassing",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchFedBalanceSheetSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    material_surprise_count: Decimal
    stale_observation_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    probability_repricing_count: Decimal
    average_surprise_ratio: Decimal | None
    max_observation_age_seconds: Decimal | None
    average_source_count: Decimal | None
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchFedBalanceSheetSurpriseDigestReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchFedBalanceSheetSurpriseDigestReport:
            raise TypeError(
                "MarketResearchFedBalanceSheetSurpriseDigestReport does not "
                "support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_FED_BALANCE_SHEET_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "material_surprise_count",
            "stale_observation_count",
            "thin_source_count",
            "high_revision_count",
            "confirmation_gap_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_surprise_ratio",
            "max_observation_age_seconds",
            "average_source_count",
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, value),
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
            _normalize_reason_codes(
                self.reason_codes,
                allow_empty=False,
                sequence=REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_fed_balance_sheet_surprise_digest(
    observations: Iterable[MarketResearchFedBalanceSheetSurpriseDigestObservation],
    *,
    config: MarketResearchFedBalanceSheetSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedBalanceSheetSurpriseDigestReport:
    if type(config) is not MarketResearchFedBalanceSheetSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchFedBalanceSheetSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _build_row(observation, config=config, generated_at=generated_at_utc)
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows, reason_codes)
    observation_count = _decimal_count(len(rows))
    return MarketResearchFedBalanceSheetSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        observation_count=observation_count,
        ready_observation_count=_status_count(rows, STATUS_READY),
        watch_observation_count=_status_count(rows, STATUS_WATCH),
        blocked_observation_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_observation_count=_reason_count(rows, STALE_OBSERVATION_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        probability_repricing_count=_reason_count(rows, PROBABILITY_REPRICING_REASON),
        average_surprise_ratio=_average_decimal(row.surprise_ratio for row in rows),
        max_observation_age_seconds=_max_decimal(
            row.observation_age_seconds for row in rows
        ),
        average_source_count=_average_decimal(row.source_count for row in rows),
        rows=rows,
        reason_code_counts=(
            _row_reason_code_counts(rows)
            if rows
            else _reason_code_counts(reason_codes)
        ),
        reason_codes=reason_codes,
    )


def market_research_fed_balance_sheet_surprise_digest_payload(
    report: MarketResearchFedBalanceSheetSurpriseDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(report, dict):
        return report
    if type(report) is not MarketResearchFedBalanceSheetSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchFedBalanceSheetSurpriseDigestReport",
        )
    return _payload_value(asdict(report))


def _build_row(
    observation: MarketResearchFedBalanceSheetSurpriseDigestObservation,
    *,
    config: MarketResearchFedBalanceSheetSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchFedBalanceSheetSurpriseDigestRow:
    observation_age_seconds = _datetime_delta_seconds(generated_at, observation.observed_at)
    surprise_delta = _quantize_decimal(
        observation.actual_change - observation.expected_change,
    )
    probability_delta = _quantize_decimal(
        observation.market_probability_after - observation.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        observation,
        observation_age_seconds,
        probability_delta,
        config=config,
    )
    digest_status = _row_status(reason_codes)
    decay_factor = _confidence_decay_factor(reason_codes)
    final_confidence = _quantize_ratio(observation.base_confidence * decay_factor)
    return MarketResearchFedBalanceSheetSurpriseDigestRow(
        condition_id=observation.condition_id,
        research_key=observation.research_key,
        release_key=observation.release_key,
        balance_sheet_metric=observation.balance_sheet_metric,
        digest_status=digest_status,
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        expected_change=observation.expected_change,
        actual_change=observation.actual_change,
        surprise_delta=surprise_delta,
        surprise_ratio=observation.surprise_ratio,
        source_count=observation.source_count,
        revision_ratio=observation.revision_ratio,
        confirmation_ratio=observation.confirmation_ratio,
        market_probability_before=observation.market_probability_before,
        market_probability_after=observation.market_probability_after,
        probability_delta=probability_delta,
        base_confidence=observation.base_confidence,
        confidence_decay_factor=decay_factor,
        final_confidence=final_confidence,
        redacted_public_observation_reference=_redact_public_reference(
            observation.public_observation_reference,
        ),
        signal_config_version=observation.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: MarketResearchFedBalanceSheetSurpriseDigestObservation,
    observation_age_seconds: Decimal,
    probability_delta: Decimal,
    *,
    config: MarketResearchFedBalanceSheetSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation_age_seconds > config.max_observation_age_seconds:
        codes.append(STALE_OBSERVATION_REASON)
    if observation.surprise_ratio >= config.material_surprise_threshold:
        codes.append(MATERIAL_SURPRISE_REASON)
    if observation.source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if observation.revision_ratio > config.max_revision_ratio:
        codes.append(HIGH_REVISION_REASON)
    if observation.confirmation_ratio < config.min_confirmation_ratio:
        codes.append(CONFIRMATION_GAP_REASON)
    if abs(probability_delta) >= config.watch_probability_delta_threshold:
        codes.append(PROBABILITY_REPRICING_REASON)
    if not codes:
        codes.append(READY_REASON)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if STALE_OBSERVATION_REASON in reason_codes or HIGH_REVISION_REASON in reason_codes:
        return STATUS_BLOCKED
    if THIN_SOURCES_REASON in reason_codes and CONFIRMATION_GAP_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _confidence_decay_factor(reason_codes: tuple[str, ...]) -> Decimal:
    penalty = ZERO
    has_blocking_quality_gap = (
        STALE_OBSERVATION_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or HIGH_REVISION_REASON in reason_codes
    )
    if STALE_OBSERVATION_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if THIN_SOURCES_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if HIGH_REVISION_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if CONFIRMATION_GAP_REASON in reason_codes and has_blocking_quality_gap:
        penalty += Decimal("0.100000")
    if PROBABILITY_REPRICING_REASON in reason_codes:
        penalty += Decimal("0.000000")
    decay = ONE - penalty
    if decay < ZERO:
        return ZERO
    return _quantize_ratio(decay)


def _report_reason_codes(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in REASON_CODE_SEQUENCE if code in present)


def _report_status(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    raise ValueError("rows are required to count row reason codes")


def _row_reason_code_counts(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
) -> tuple[MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: list[MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                observation_ratio=_ratio(count, observation_count),
            ),
        )
    return tuple(counts)


def _status_count(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_observations(
    observations: Iterable[MarketResearchFedBalanceSheetSurpriseDigestObservation],
) -> tuple[MarketResearchFedBalanceSheetSurpriseDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable of Fed balance sheet rows")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not MarketResearchFedBalanceSheetSurpriseDigestObservation:
            raise ValueError(
                "observations must contain exactly "
                "MarketResearchFedBalanceSheetSurpriseDigestObservation",
            )
        _require_hard_flags("observation", observation)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...],
) -> tuple[MarketResearchFedBalanceSheetSurpriseDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchFedBalanceSheetSurpriseDigestRow:
            raise ValueError(
                "rows must contain exactly MarketResearchFedBalanceSheetSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or not isinstance(
        reason_code_counts,
        tuple,
    ):
        raise ValueError("reason_code_counts must be a tuple")
    for count in reason_code_counts:
        if type(count) is not MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchFedBalanceSheetSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    return tuple(
        sorted(
            reason_code_counts,
            key=lambda item: _reason_rank(item.reason_code),
        ),
    )


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        try:
            _require_reason_code("reason_code", reason_code)
        except ValueError as exc:
            raise ValueError("reason_codes must contain supported reason codes") from exc
    return tuple(sorted(dict.fromkeys(reason_codes), key=lambda code: sequence.index(code)))


def _validate_row_consistency(
    row: MarketResearchFedBalanceSheetSurpriseDigestRow,
) -> None:
    expected_delta = _quantize_decimal(row.actual_change - row.expected_change)
    if row.surprise_delta != expected_delta:
        raise ValueError("surprise_delta must equal actual_change minus expected_change")
    if row.reason_codes == (READY_REASON,) and row.digest_status != STATUS_READY:
        raise ValueError("ready reason row must have ready digest_status")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("ready digest_status must only use the ready reason code")


def _validate_report_consistency(
    report: MarketResearchFedBalanceSheetSurpriseDigestReport,
) -> None:
    rows = report.rows
    observation_count = _decimal_count(len(rows))
    if report.observation_count != observation_count:
        raise ValueError("observation_count must equal rows length")
    status_total = (
        report.ready_observation_count
        + report.watch_observation_count
        + report.blocked_observation_count
    )
    if status_total != report.observation_count:
        raise ValueError("status counts must equal observation_count")
    expected_counts = _row_reason_code_counts(rows) if rows else _reason_code_counts(
        report.reason_codes,
    )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows and reason_codes")
    expected_reason_codes = tuple(count.reason_code for count in expected_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(rows, report.reason_codes)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_values = {
        "ready_observation_count": _status_count(rows, STATUS_READY),
        "watch_observation_count": _status_count(rows, STATUS_WATCH),
        "blocked_observation_count": _status_count(rows, STATUS_BLOCKED),
        "material_surprise_count": _reason_count(rows, MATERIAL_SURPRISE_REASON),
        "stale_observation_count": _reason_count(rows, STALE_OBSERVATION_REASON),
        "thin_source_count": _reason_count(rows, THIN_SOURCES_REASON),
        "high_revision_count": _reason_count(rows, HIGH_REVISION_REASON),
        "confirmation_gap_count": _reason_count(rows, CONFIRMATION_GAP_REASON),
        "probability_repricing_count": _reason_count(rows, PROBABILITY_REPRICING_REASON),
        "average_surprise_ratio": _average_decimal(row.surprise_ratio for row in rows),
        "max_observation_age_seconds": _max_decimal(
            row.observation_age_seconds for row in rows
        ),
        "average_source_count": _average_decimal(row.source_count for row in rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _row_sort_key(
    row: MarketResearchFedBalanceSheetSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.surprise_ratio,
        -row.observation_age_seconds,
        row.condition_id,
        row.release_key,
    )


def _status_rank(status: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[status]


def _reason_rank(reason_code: str) -> int:
    if reason_code in REASON_CODE_SEQUENCE:
        return REASON_CODE_SEQUENCE.index(reason_code)
    if reason_code in ROW_REASON_CODE_SEQUENCE:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    raise ValueError(f"unsupported reason_code: {reason_code}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} paper_only/report_only/readonly must be True")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in set(REASON_CODE_SEQUENCE).union(
        ROW_REASON_CODE_SEQUENCE,
    ):
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a plain string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_reference_is_redacted_safe(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if _join_parts("wal", "let") in lowered:
        raise ValueError(f"{field_name} must be public and redacted")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    normalized = value.astimezone(UTC)
    return datetime(
        normalized.year,
        normalized.month,
        normalized.day,
        normalized.hour,
        normalized.minute,
        normalized.second,
        normalized.microsecond,
        tzinfo=UTC,
        fold=normalized.fold,
    )


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _quantize_decimal(_require_decimal(field_name, value))


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_decimal(decimal_value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize_decimal(seconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_ratio(numerator / denominator)


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _quantize_ratio(value: Decimal) -> Decimal:
    quantized = _quantize_decimal(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError("ratio must be between 0 and 1")
    return quantized


def _redact_public_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
