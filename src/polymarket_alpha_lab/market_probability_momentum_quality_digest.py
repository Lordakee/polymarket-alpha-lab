"""In-memory market probability momentum quality digest."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


CONFIG_VERSION = "market_probability_momentum_quality_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

QUALITY_STABLE_CONFIRMED = "stable_confirmed"
QUALITY_REVERSAL_RISK = "reversal_risk"
QUALITY_UNCONFIRMED_MOVE = "unconfirmed_move"
QUALITY_HIGH_DISPERSION = "high_dispersion"
QUALITY_STALE_CONTEXT = "stale_context"

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "row_count",
        "market_count",
        "category_count",
        "high_reversal_risk_count",
        "unconfirmed_move_count",
        "high_dispersion_count",
        "stale_context_count",
        "rows",
        "category_rollups",
        "reason_code_counts",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "market_id",
        "category",
        "observed_at",
        "start_probability",
        "end_probability",
        "previous_probability",
        "momentum_size",
        "reversal_size",
        "reversal_risk_score",
        "source_confirmed_move",
        "forecast_count",
        "forecast_dispersion",
        "last_context_at",
        "context_age_hours",
        "stale_context_pressure",
        "quality_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROLLUP_PAYLOAD_FIELDS = frozenset(
    (
        "category",
        "row_count",
        "average_momentum_size",
        "average_reversal_risk_score",
        "source_confirmed_ratio",
        "average_forecast_dispersion",
        "average_stale_context_pressure",
        "high_reversal_risk_count",
        "unconfirmed_move_count",
        "high_dispersion_count",
        "stale_context_count",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_COUNT_PAYLOAD_FIELDS = (
    "row_count",
    "market_count",
    "category_count",
    "high_reversal_risk_count",
    "unconfirmed_move_count",
    "high_dispersion_count",
    "stale_context_count",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "start_probability",
    "end_probability",
    "momentum_size",
    "reversal_size",
    "reversal_risk_score",
    "forecast_dispersion",
    "stale_context_pressure",
)
ROLLUP_DECIMAL_PAYLOAD_FIELDS = (
    "average_momentum_size",
    "average_reversal_risk_score",
    "source_confirmed_ratio",
    "average_forecast_dispersion",
    "average_stale_context_pressure",
)
ROLLUP_COUNT_PAYLOAD_FIELDS = (
    "row_count",
    "high_reversal_risk_count",
    "unconfirmed_move_count",
    "high_dispersion_count",
    "stale_context_count",
)
ROW_PROBABILITY_PAYLOAD_FIELDS = (
    "start_probability",
    "end_probability",
    "previous_probability",
)
ROW_COUNT_PAYLOAD_FIELDS = ("forecast_count",)
ROW_STATUS_VALUES = frozenset(
    (
        QUALITY_STABLE_CONFIRMED,
        QUALITY_REVERSAL_RISK,
        QUALITY_UNCONFIRMED_MOVE,
        QUALITY_HIGH_DISPERSION,
        QUALITY_STALE_CONTEXT,
    ),
)


@dataclass(frozen=True)
class MarketProbabilityMomentumQualityConfig:
    config_version: str = CONFIG_VERSION
    reversal_risk_threshold: Decimal = Decimal("0.5000")
    unconfirmed_move_threshold: Decimal = Decimal("0.0500")
    dispersion_threshold: Decimal = Decimal("0.2500")
    stale_context_after_hours: Decimal = Decimal("24")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumQualityConfig:
            raise TypeError(
                "MarketProbabilityMomentumQualityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumQualityConfig:
            raise ValueError(
                "config must be exactly MarketProbabilityMomentumQualityConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "reversal_risk_threshold",
            "unconfirmed_move_threshold",
            "dispersion_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_context_after_hours",
            _normalize_positive_decimal(
                "stale_context_after_hours",
                self.stale_context_after_hours,
            ),
        )
        require_paper_only_flags("market probability momentum quality config", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumQualityInput:
    market_id: str
    category: str
    observed_at: datetime
    start_probability: Decimal
    end_probability: Decimal
    previous_probability: Decimal | None
    source_confirmed: bool
    forecast_probabilities: tuple[Decimal, ...]
    last_context_at: datetime | None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumQualityInput:
            raise TypeError(
                "MarketProbabilityMomentumQualityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumQualityInput:
            raise ValueError(
                "input must be exactly MarketProbabilityMomentumQualityInput",
            )
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("start_probability", "end_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.previous_probability is not None:
            object.__setattr__(
                self,
                "previous_probability",
                _normalize_probability("previous_probability", self.previous_probability),
            )
        if type(self.source_confirmed) is not bool:
            raise ValueError("source_confirmed must be a bool")
        object.__setattr__(
            self,
            "forecast_probabilities",
            _normalize_forecast_probabilities(self.forecast_probabilities),
        )
        if self.last_context_at is not None:
            object.__setattr__(
                self,
                "last_context_at",
                _as_utc("last_context_at", self.last_context_at),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("market probability momentum quality input", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumQualityRow:
    market_id: str
    category: str
    observed_at: datetime
    start_probability: Decimal
    end_probability: Decimal
    previous_probability: Decimal | None
    momentum_size: Decimal
    reversal_size: Decimal
    reversal_risk_score: Decimal
    source_confirmed_move: bool
    forecast_count: Decimal
    forecast_dispersion: Decimal
    last_context_at: datetime | None
    context_age_hours: Decimal | None
    stale_context_pressure: Decimal
    quality_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumQualityRow:
            raise TypeError(
                "MarketProbabilityMomentumQualityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumQualityRow:
            raise ValueError("row must be exactly MarketProbabilityMomentumQualityRow")
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("start_probability", "end_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.previous_probability is not None:
            object.__setattr__(
                self,
                "previous_probability",
                _normalize_probability("previous_probability", self.previous_probability),
            )
        for field_name in (
            "momentum_size",
            "reversal_size",
            "reversal_risk_score",
            "forecast_dispersion",
            "stale_context_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_finite_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.source_confirmed_move) is not bool:
            raise ValueError("source_confirmed_move must be a bool")
        object.__setattr__(
            self,
            "forecast_count",
            _normalize_count_decimal("forecast_count", self.forecast_count),
        )
        if self.last_context_at is not None:
            object.__setattr__(
                self,
                "last_context_at",
                _as_utc("last_context_at", self.last_context_at),
            )
        if self.context_age_hours is not None:
            object.__setattr__(
                self,
                "context_age_hours",
                _normalize_nonnegative_decimal(
                    "context_age_hours",
                    self.context_age_hours,
                ),
            )
        if self.quality_status not in (
            QUALITY_STABLE_CONFIRMED,
            QUALITY_REVERSAL_RISK,
            QUALITY_UNCONFIRMED_MOVE,
            QUALITY_HIGH_DISPERSION,
            QUALITY_STALE_CONTEXT,
        ):
            raise ValueError("quality_status must be known")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("market probability momentum quality row", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumQualityCategoryRollup:
    category: str
    row_count: Decimal
    average_momentum_size: Decimal
    average_reversal_risk_score: Decimal
    source_confirmed_ratio: Decimal
    average_forecast_dispersion: Decimal
    average_stale_context_pressure: Decimal
    high_reversal_risk_count: Decimal
    unconfirmed_move_count: Decimal
    high_dispersion_count: Decimal
    stale_context_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumQualityCategoryRollup:
            raise TypeError(
                "MarketProbabilityMomentumQualityCategoryRollup "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumQualityCategoryRollup:
            raise ValueError(
                "category rollup must be exactly "
                "MarketProbabilityMomentumQualityCategoryRollup",
            )
        _require_canonical_string("category", self.category)
        for field_name in (
            "row_count",
            "high_reversal_risk_count",
            "unconfirmed_move_count",
            "high_dispersion_count",
            "stale_context_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_momentum_size",
            "average_reversal_risk_score",
            "source_confirmed_ratio",
            "average_forecast_dispersion",
            "average_stale_context_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("market probability momentum quality category rollup", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumQualityReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    market_count: Decimal
    category_count: Decimal
    high_reversal_risk_count: Decimal
    unconfirmed_move_count: Decimal
    high_dispersion_count: Decimal
    stale_context_count: Decimal
    rows: tuple[MarketProbabilityMomentumQualityRow, ...]
    category_rollups: tuple[MarketProbabilityMomentumQualityCategoryRollup, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketProbabilityMomentumQualityReport:
            raise TypeError(
                "MarketProbabilityMomentumQualityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketProbabilityMomentumQualityReport:
            raise ValueError(
                "report must be exactly MarketProbabilityMomentumQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "market_count",
            "category_count",
            "high_reversal_risk_count",
            "unconfirmed_move_count",
            "high_dispersion_count",
            "stale_context_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        require_paper_only_flags("market probability momentum quality report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "market probability momentum quality report",
            _payload_value(asdict(self)),
        )


def build_market_probability_momentum_quality_digest(
    observations: tuple[MarketProbabilityMomentumQualityInput, ...],
    *,
    generated_at: datetime,
    config: MarketProbabilityMomentumQualityConfig,
) -> MarketProbabilityMomentumQualityReport:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    if type(config) is not MarketProbabilityMomentumQualityConfig:
        raise ValueError("config must be a MarketProbabilityMomentumQualityConfig")
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(
                    observation=observation,
                    generated_at=normalized_generated_at,
                    config=config,
                )
                for observation in observations
            ),
            key=lambda row: (row.category, row.market_id, row.observed_at),
        ),
    )
    category_rollups = _build_category_rollups(rows)
    reason_code_counts = _reason_code_counts(rows)
    return MarketProbabilityMomentumQualityReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        market_count=Decimal(len({row.market_id for row in rows})),
        category_count=Decimal(len({row.category for row in rows})),
        high_reversal_risk_count=_count_status(rows, QUALITY_REVERSAL_RISK),
        unconfirmed_move_count=_count_status(rows, QUALITY_UNCONFIRMED_MOVE),
        high_dispersion_count=_count_status(rows, QUALITY_HIGH_DISPERSION),
        stale_context_count=_count_status(rows, QUALITY_STALE_CONTEXT),
        rows=rows,
        category_rollups=category_rollups,
        reason_code_counts=reason_code_counts,
    )


def market_probability_momentum_quality_payload(
    report: MarketProbabilityMomentumQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketProbabilityMomentumQualityReport:
        require_paper_only_flags("market probability momentum quality report", report)
        _require_report_validation_digest(report)
        _validate_report_consistency(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a MarketProbabilityMomentumQualityReport or object")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    observation: MarketProbabilityMomentumQualityInput,
    generated_at: datetime,
    config: MarketProbabilityMomentumQualityConfig,
) -> MarketProbabilityMomentumQualityRow:
    if not isinstance(observation, MarketProbabilityMomentumQualityInput):
        raise ValueError("observations must contain MarketProbabilityMomentumQualityInput rows")
    momentum_size = _quantize(observation.end_probability - observation.start_probability)
    prior_momentum = (
        None
        if observation.previous_probability is None
        else _quantize(observation.start_probability - observation.previous_probability)
    )
    reversal_size = _reversal_size(momentum_size, prior_momentum)
    reversal_risk_score = (
        ZERO
        if prior_momentum in (None, ZERO)
        else _safe_ratio(reversal_size, abs(prior_momentum))
    )
    forecast_dispersion = _forecast_dispersion(observation.forecast_probabilities)
    context_age_hours = _context_age_hours(generated_at, observation.last_context_at)
    stale_context_pressure = _stale_context_pressure(
        context_age_hours,
        config.stale_context_after_hours,
    )
    source_confirmed_move = observation.source_confirmed
    quality_status = _quality_status(
        reversal_risk_score=reversal_risk_score,
        source_confirmed_move=source_confirmed_move,
        momentum_size=momentum_size,
        forecast_dispersion=forecast_dispersion,
        stale_context_pressure=stale_context_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        observation.reason_codes,
        quality_status=quality_status,
        reversal_risk_score=reversal_risk_score,
        forecast_dispersion=forecast_dispersion,
        stale_context_pressure=stale_context_pressure,
        source_confirmed_move=source_confirmed_move,
        momentum_size=momentum_size,
        config=config,
    )
    return MarketProbabilityMomentumQualityRow(
        market_id=observation.market_id,
        category=observation.category,
        observed_at=observation.observed_at,
        start_probability=observation.start_probability,
        end_probability=observation.end_probability,
        previous_probability=observation.previous_probability,
        momentum_size=momentum_size,
        reversal_size=reversal_size,
        reversal_risk_score=reversal_risk_score,
        source_confirmed_move=source_confirmed_move,
        forecast_count=Decimal(len(observation.forecast_probabilities)),
        forecast_dispersion=forecast_dispersion,
        last_context_at=observation.last_context_at,
        context_age_hours=context_age_hours,
        stale_context_pressure=stale_context_pressure,
        quality_status=quality_status,
        reason_codes=reason_codes,
    )


def _reversal_size(momentum_size: Decimal, prior_momentum: Decimal | None) -> Decimal:
    if prior_momentum is None:
        return ZERO
    if momentum_size == ZERO or prior_momentum == ZERO:
        return ZERO
    if (momentum_size > ZERO > prior_momentum) or (momentum_size < ZERO < prior_momentum):
        return abs(momentum_size)
    return ZERO


def _forecast_dispersion(probabilities: tuple[Decimal, ...]) -> Decimal:
    if not probabilities:
        return ZERO
    return _quantize(max(probabilities) - min(probabilities))


def _context_age_hours(generated_at: datetime, last_context_at: datetime | None) -> Decimal | None:
    if last_context_at is None:
        return None
    delta = generated_at - last_context_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if seconds < ZERO:
        return ZERO
    return _quantize(seconds / Decimal("3600"))


def _stale_context_pressure(
    context_age_hours: Decimal | None,
    stale_context_after_hours: Decimal,
) -> Decimal:
    if context_age_hours is None:
        return ONE
    if context_age_hours <= stale_context_after_hours:
        return ZERO
    return ONE


def _quality_status(
    *,
    reversal_risk_score: Decimal,
    source_confirmed_move: bool,
    momentum_size: Decimal,
    forecast_dispersion: Decimal,
    stale_context_pressure: Decimal,
    config: MarketProbabilityMomentumQualityConfig,
) -> str:
    if (not source_confirmed_move) and abs(momentum_size) >= config.unconfirmed_move_threshold:
        return QUALITY_UNCONFIRMED_MOVE
    if reversal_risk_score >= config.reversal_risk_threshold and reversal_risk_score > ZERO:
        return QUALITY_REVERSAL_RISK
    if forecast_dispersion >= config.dispersion_threshold:
        return QUALITY_HIGH_DISPERSION
    if stale_context_pressure > ZERO:
        return QUALITY_STALE_CONTEXT
    return QUALITY_STABLE_CONFIRMED


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    quality_status: str,
    reversal_risk_score: Decimal,
    forecast_dispersion: Decimal,
    stale_context_pressure: Decimal,
    source_confirmed_move: bool,
    momentum_size: Decimal,
    config: MarketProbabilityMomentumQualityConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(quality_status)
    if reversal_risk_score >= config.reversal_risk_threshold and reversal_risk_score > ZERO:
        codes.add(QUALITY_REVERSAL_RISK)
    if forecast_dispersion >= config.dispersion_threshold:
        codes.add(QUALITY_HIGH_DISPERSION)
    if stale_context_pressure > ZERO:
        codes.add(QUALITY_STALE_CONTEXT)
    if (
        source_confirmed_move
        and abs(momentum_size) > ZERO
        and quality_status == QUALITY_STABLE_CONFIRMED
    ):
        codes.add("source_confirmed_move")
    if (not source_confirmed_move) and abs(momentum_size) >= config.unconfirmed_move_threshold:
        codes.add(QUALITY_UNCONFIRMED_MOVE)
    return tuple(sorted(codes))


def _build_category_rollups(
    rows: tuple[MarketProbabilityMomentumQualityRow, ...],
) -> tuple[MarketProbabilityMomentumQualityCategoryRollup, ...]:
    categories = sorted({row.category for row in rows})
    return tuple(_category_rollup(category, rows) for category in categories)


def _category_rollup(
    category: str,
    rows: tuple[MarketProbabilityMomentumQualityRow, ...],
) -> MarketProbabilityMomentumQualityCategoryRollup:
    category_rows = tuple(row for row in rows if row.category == category)
    row_count = Decimal(len(category_rows))
    reason_codes = tuple(sorted({code for row in category_rows for code in row.reason_codes}))
    return MarketProbabilityMomentumQualityCategoryRollup(
        category=category,
        row_count=row_count,
        average_momentum_size=_average(row.momentum_size for row in category_rows),
        average_reversal_risk_score=_average(
            (row.reversal_risk_score for row in category_rows),
        ),
        source_confirmed_ratio=_safe_ratio(
            Decimal(sum(1 for row in category_rows if row.source_confirmed_move)),
            row_count,
        ),
        average_forecast_dispersion=_average(row.forecast_dispersion for row in category_rows),
        average_stale_context_pressure=_average(
            (row.stale_context_pressure for row in category_rows),
        ),
        high_reversal_risk_count=_count_status(category_rows, QUALITY_REVERSAL_RISK),
        unconfirmed_move_count=_count_status(category_rows, QUALITY_UNCONFIRMED_MOVE),
        high_dispersion_count=_count_status(category_rows, QUALITY_HIGH_DISPERSION),
        stale_context_count=_count_status(category_rows, QUALITY_STALE_CONTEXT),
        reason_codes=reason_codes,
    )


def _reason_code_counts(
    rows: tuple[MarketProbabilityMomentumQualityRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in sorted(counter))


def _count_status(rows: tuple[MarketProbabilityMomentumQualityRow, ...], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.quality_status == status))


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _normalize_rows(
    value: object,
) -> tuple[MarketProbabilityMomentumQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is MarketProbabilityMomentumQualityRow for row in rows):
        raise ValueError("rows must contain MarketProbabilityMomentumQualityRow values")
    if rows != tuple(sorted(rows, key=lambda row: (row.category, row.market_id, row.observed_at))):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_category_rollups(
    value: object,
) -> tuple[MarketProbabilityMomentumQualityCategoryRollup, ...]:
    if type(value) is not tuple:
        raise ValueError("category_rollups must be a tuple")
    rollups = tuple(value)
    if not all(type(row) is MarketProbabilityMomentumQualityCategoryRollup for row in rollups):
        raise ValueError("category_rollups must contain category rollup values")
    if rollups != tuple(sorted(rollups, key=lambda row: row.category)):
        raise ValueError("category_rollups must be sorted")
    return rollups


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_canonical_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_forecast_probabilities(value: object) -> tuple[Decimal, ...]:
    if type(value) is not tuple:
        raise ValueError("forecast_probabilities must be a tuple")
    return tuple(
        _normalize_probability("forecast_probabilities", probability)
        for probability in value
    )


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_canonical_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_report_consistency(report: MarketProbabilityMomentumQualityReport) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.market_count != Decimal(len({row.market_id for row in report.rows})):
        raise ValueError("market_count must match rows")
    if report.category_count != Decimal(len({row.category for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.high_reversal_risk_count != _count_status(
        report.rows,
        QUALITY_REVERSAL_RISK,
    ):
        raise ValueError("high_reversal_risk_count must match rows")
    if report.unconfirmed_move_count != _count_status(
        report.rows,
        QUALITY_UNCONFIRMED_MOVE,
    ):
        raise ValueError("unconfirmed_move_count must match rows")
    if report.high_dispersion_count != _count_status(report.rows, QUALITY_HIGH_DISPERSION):
        raise ValueError("high_dispersion_count must match rows")
    if report.stale_context_count != _count_status(report.rows, QUALITY_STALE_CONTEXT):
        raise ValueError("stale_context_count must match rows")
    if report.category_rollups != _build_category_rollups(report.rows):
        raise ValueError("category_rollups must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_validation_digest(report: MarketProbabilityMomentumQualityReport) -> str:
    return _derived_validation_digest(asdict(report))


def _require_report_validation_digest(
    report: MarketProbabilityMomentumQualityReport,
) -> None:
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _payload_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            _require_canonical_string("payload key", key)
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type) and type(value).__module__ == __name__:
        return _payload_value(asdict(value))
    raise ValueError("public payload contains unsupported value")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("market probability momentum quality payload", payload)
    _validate_report_payload_shape(payload)
    _require_public_payload_flags("market probability momentum quality payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    _validate_payload_consistency(payload)


def _validate_report_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_fields("payload", payload, REPORT_PAYLOAD_FIELDS)
    _require_datetime_payload("generated_at", payload["generated_at"])
    _require_string_payload("config_version", payload["config_version"])
    for field_name in REPORT_COUNT_PAYLOAD_FIELDS:
        _require_count_payload(field_name, payload[field_name])
    _validate_rows_payload(payload["rows"])
    _validate_category_rollups_payload(payload["category_rollups"])
    _validate_reason_code_counts_payload(payload["reason_code_counts"])


def _validate_rows_payload(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain object values")
        _require_payload_fields("rows", row, ROW_PAYLOAD_FIELDS)
        _require_string_payload("market_id", row["market_id"])
        _require_string_payload("category", row["category"])
        _require_datetime_payload("observed_at", row["observed_at"])
        _require_optional_datetime_payload("last_context_at", row["last_context_at"])
        _require_optional_probability_payload(
            "previous_probability",
            row["previous_probability"],
        )
        _require_optional_decimal_payload("context_age_hours", row["context_age_hours"])
        for field_name in ROW_PROBABILITY_PAYLOAD_FIELDS:
            if field_name != "previous_probability":
                _require_probability_payload(field_name, row[field_name])
        for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
            if field_name in ROW_PROBABILITY_PAYLOAD_FIELDS:
                continue
            _require_decimal_payload(field_name, row[field_name])
        for field_name in ROW_COUNT_PAYLOAD_FIELDS:
            _require_count_payload(field_name, row[field_name])
        if type(row["source_confirmed_move"]) is not bool:
            raise ValueError("source_confirmed_move must be a bool")
        _require_member_payload("quality_status", row["quality_status"], ROW_STATUS_VALUES)
        _require_string_list_payload("reason_codes", row["reason_codes"])


def _validate_category_rollups_payload(value: object) -> None:
    if type(value) is not list:
        raise ValueError("category_rollups must be a list")
    for rollup in value:
        if type(rollup) is not dict:
            raise ValueError("category_rollups must contain object values")
        _require_payload_fields("category_rollups", rollup, ROLLUP_PAYLOAD_FIELDS)
        _require_string_payload("category", rollup["category"])
        for field_name in ROLLUP_DECIMAL_PAYLOAD_FIELDS:
            _require_decimal_payload(field_name, rollup[field_name])
        for field_name in ROLLUP_COUNT_PAYLOAD_FIELDS:
            _require_count_payload(field_name, rollup[field_name])
        _require_string_list_payload("reason_codes", rollup["reason_codes"])


def _validate_reason_code_counts_payload(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    previous: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts must contain pair lists")
        reason_code, count = item
        _require_string_payload("reason_code_counts", reason_code)
        if previous is not None and previous > reason_code:
            raise ValueError("reason_code_counts must be sorted")
        _require_count_payload("reason_code_counts", count)
        previous = reason_code


def _validate_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    category_rollups = payload["category_rollups"]
    if type(category_rollups) is not list:
        raise ValueError("category_rollups must be a list")
    if _require_decimal_payload("row_count", payload["row_count"]) != Decimal(len(rows)):
        raise ValueError("row_count must match rows")
    market_ids = {
        row["market_id"]
        for row in rows
        if type(row) is dict and type(row.get("market_id")) is str
    }
    if _require_decimal_payload("market_count", payload["market_count"]) != Decimal(
        len(market_ids),
    ):
        raise ValueError("market_count must match rows")
    categories = {
        row["category"]
        for row in rows
        if type(row) is dict and type(row.get("category")) is str
    }
    if _require_decimal_payload("category_count", payload["category_count"]) != Decimal(
        len(categories),
    ):
        raise ValueError("category_count must match rows")
    _require_payload_status_count(
        payload,
        "high_reversal_risk_count",
        QUALITY_REVERSAL_RISK,
    )
    _require_payload_status_count(
        payload,
        "unconfirmed_move_count",
        QUALITY_UNCONFIRMED_MOVE,
    )
    _require_payload_status_count(
        payload,
        "high_dispersion_count",
        QUALITY_HIGH_DISPERSION,
    )
    _require_payload_status_count(
        payload,
        "stale_context_count",
        QUALITY_STALE_CONTEXT,
    )
    expected_reason_code_counts = _payload_reason_code_counts(rows)
    if payload["reason_code_counts"] != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_categories = sorted(categories)
    actual_categories = [
        rollup["category"]
        for rollup in category_rollups
        if type(rollup) is dict and type(rollup.get("category")) is str
    ]
    if actual_categories != expected_categories:
        raise ValueError("category_rollups must match rows")
    if category_rollups != _payload_category_rollups(rows):
        raise ValueError("category_rollups must match rows")


def _require_payload_status_count(
    payload: dict[str, Any],
    field_name: str,
    status: str,
) -> None:
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    expected = Decimal(
        sum(
            1
            for row in rows
            if type(row) is dict and row.get("quality_status") == status
        ),
    )
    if _require_decimal_payload(field_name, payload[field_name]) != expected:
        raise ValueError(f"{field_name} must match rows")


def _payload_reason_code_counts(rows: list[Any]) -> list[list[str]]:
    counter: Counter[str] = Counter()
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain object values")
        reason_codes = row["reason_codes"]
        if type(reason_codes) is not list:
            raise ValueError("reason_codes must be a list")
        counter.update(reason_codes)
    return [[code, format(_quantize(Decimal(counter[code])), "f")] for code in sorted(counter)]


def _payload_category_rollups(rows: list[Any]) -> list[dict[str, object]]:
    categories = sorted(
        {
            row["category"]
            for row in rows
            if type(row) is dict and type(row.get("category")) is str
        },
    )
    return [_payload_category_rollup(category, rows) for category in categories]


def _payload_category_rollup(category: str, rows: list[Any]) -> dict[str, object]:
    category_rows = [
        row
        for row in rows
        if type(row) is dict and row.get("category") == category
    ]
    row_count = Decimal(len(category_rows))
    reason_codes = sorted(
        {
            code
            for row in category_rows
            if type(row.get("reason_codes")) is list
            for code in row["reason_codes"]
        },
    )
    return {
        "category": category,
        "row_count": _decimal_payload(row_count),
        "average_momentum_size": _decimal_payload(
            _payload_average(row["momentum_size"] for row in category_rows),
        ),
        "average_reversal_risk_score": _decimal_payload(
            _payload_average(row["reversal_risk_score"] for row in category_rows),
        ),
        "source_confirmed_ratio": _decimal_payload(
            _safe_ratio(
                Decimal(
                    sum(
                        1
                        for row in category_rows
                        if row.get("source_confirmed_move") is True
                    ),
                ),
                row_count,
            ),
        ),
        "average_forecast_dispersion": _decimal_payload(
            _payload_average(row["forecast_dispersion"] for row in category_rows),
        ),
        "average_stale_context_pressure": _decimal_payload(
            _payload_average(row["stale_context_pressure"] for row in category_rows),
        ),
        "high_reversal_risk_count": _decimal_payload(
            _payload_status_count(category_rows, QUALITY_REVERSAL_RISK),
        ),
        "unconfirmed_move_count": _decimal_payload(
            _payload_status_count(category_rows, QUALITY_UNCONFIRMED_MOVE),
        ),
        "high_dispersion_count": _decimal_payload(
            _payload_status_count(category_rows, QUALITY_HIGH_DISPERSION),
        ),
        "stale_context_count": _decimal_payload(
            _payload_status_count(category_rows, QUALITY_STALE_CONTEXT),
        ),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_average(values: Any) -> Decimal:
    items = tuple(_require_decimal_payload("category_rollups", value) for value in values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _payload_status_count(rows: list[dict[str, Any]], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.get("quality_status") == status))


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = frozenset(payload)
    missing = expected_fields - actual_fields
    if missing:
        raise ValueError(f"{label} missing required field {sorted(missing)[0]}")
    extra = actual_fields - expected_fields
    if extra:
        raise ValueError(f"{label} contains unexpected field {sorted(extra)[0]}")


def _require_string_payload(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_member_payload(
    field_name: str,
    value: object,
    allowed_values: frozenset[str],
) -> None:
    _require_string_payload(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _require_string_list_payload(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_string_payload(field_name, item)
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        previous = item


def _require_decimal_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal-derived string")
    if format(_quantize(decimal_value), "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return decimal_value


def _require_probability_payload(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal_payload(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_count_payload(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal_payload(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal-derived string")
    return decimal_value


def _require_optional_decimal_payload(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal_payload(field_name, value)


def _require_optional_probability_payload(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_payload(field_name, value)


def _require_datetime_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_optional_datetime_payload(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _require_datetime_payload(field_name, value)


def _require_public_payload_flags(label: str, value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{label} {field_name} must be True")
        for child in value.values():
            _require_public_payload_flags(label, child)
        return
    if type(value) is list:
        for child in value:
            _require_public_payload_flags(label, child)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} must use safe serialized scalars")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    unsafe_fragments = tuple(UNSAFE_SURFACE_FIELD_FRAGMENTS) + (
        "li" + "ve",
        "net" + "work",
        "data" + "base",
        "per" + "sist",
        "credential",
        "secret",
        "token",
        "private" + "_" + "key",
        "0x",
    )
    if type(value) is dict:
        for key, child in value.items():
            _require_canonical_string("payload key", key)
            if any(fragment in key.lower() for fragment in unsafe_fragments):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(label, child)
        return
    if type(value) is list:
        for child in value:
            _reject_unsafe_public_payload(label, child)
        return
    if type(value) is str:
        _require_canonical_string("payload value", value)
        if any(fragment in value.lower() for fragment in unsafe_fragments):
            raise ValueError(f"{label} contains unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{label} contains unsafe public value")


__all__ = (
    "MarketProbabilityMomentumQualityCategoryRollup",
    "MarketProbabilityMomentumQualityConfig",
    "MarketProbabilityMomentumQualityInput",
    "MarketProbabilityMomentumQualityReport",
    "MarketProbabilityMomentumQualityRow",
    "build_market_probability_momentum_quality_digest",
    "market_probability_momentum_quality_payload",
)
