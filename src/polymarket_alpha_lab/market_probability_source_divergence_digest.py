"""Pure Phase 1 reducer for market probability source divergence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_PROBABILITY_SOURCE_DIVERGENCE_DIGEST_CONFIG_VERSION = (
    "market-probability-source-divergence-digest-v0"
)

ROW_STATUSES = ("clear", "watch", "blocked")
REPORT_REASON_CODES = (
    "market_probability_source_divergence_clear",
    "market_probability_source_divergence_watch",
    "market_probability_source_divergence_blocked",
    "market_source_family_disagreement_present",
    "market_forecast_recency_degraded",
    "market_confidence_dispersion_present",
    "empty_market_probability_source_divergence_inputs",
)
ROW_REASON_CODES = (
    "market_probability_aligned",
    "market_probability_source_gap_watch",
    "market_probability_source_gap_blocked",
    "source_family_disagreement_watch",
    "source_family_disagreement_blocked",
    "forecast_recency_degraded",
    "confidence_dispersion_watch",
    "confidence_dispersion_blocked",
)
SOURCE_REASON_CODES = (
    "team_forecast",
    "source_forecast",
    "model_forecast",
    "market_context_forecast",
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "market_count",
    "clear_market_count",
    "watch_market_count",
    "blocked_market_count",
    "divergent_market_count",
    "divergent_market_ratio",
    "status",
    "reason_codes",
    "rows",
    "reason_rollups",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (
    *PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_ROW_FIELDS = (
    "market_id",
    "status",
    "market_implied_probability",
    "recency_weighted_forecast_probability",
    "probability_gap",
    "source_count",
    "source_family_count",
    "stale_source_count",
    "source_family_disagreement",
    "confidence_dispersion",
    "latest_observed_at",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROLLUP_FIELDS = (
    "reason_code",
    "market_count",
    "market_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "api_key",
    "au" + "thor" + "ization",
    "credential",
    "private" + "_key",
    "secret",
    "token",
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
    "account",
    "au" + "th",
    "balance",
    "bro" + "ker",
    "can" + "cel",
    "credential",
    "data" + "base",
    "li" + "ve",
    "net" + "work",
    "or" + "der",
    "per" + "sist",
    "secret",
    "sign",
    "sub" + "mit",
    "token",
    "tra" + "de",
    "wal" + "let",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
STATUS_WEIGHT = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "clear": Decimal("2"),
}


@dataclass(frozen=True)
class MarketProbabilitySourceDivergenceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_PROBABILITY_SOURCE_DIVERGENCE_DIGEST_CONFIG_VERSION
    )
    watch_probability_gap: Decimal = Decimal("0.050000")
    blocked_probability_gap: Decimal = Decimal("0.150000")
    watch_family_disagreement: Decimal = Decimal("0.080000")
    blocked_family_disagreement: Decimal = Decimal("0.180000")
    watch_confidence_dispersion: Decimal = Decimal("0.200000")
    blocked_confidence_dispersion: Decimal = Decimal("0.400000")
    recency_half_life_seconds: Decimal = Decimal("86400.000000")
    stale_after_seconds: Decimal = Decimal("172800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "MarketProbabilitySourceDivergenceDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_probability_gap",
            "blocked_probability_gap",
            "watch_family_disagreement",
            "blocked_family_disagreement",
            "watch_confidence_dispersion",
            "blocked_confidence_dispersion",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_delta(field_name, getattr(self, field_name)),
            )
        for field_name in ("recency_half_life_seconds", "stale_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_probability_gap > self.blocked_probability_gap:
            raise ValueError("watch_probability_gap must not exceed blocked_probability_gap")
        if self.watch_family_disagreement > self.blocked_family_disagreement:
            raise ValueError(
                "watch_family_disagreement must not exceed blocked_family_disagreement",
            )
        if self.watch_confidence_dispersion > self.blocked_confidence_dispersion:
            raise ValueError(
                "watch_confidence_dispersion must not exceed "
                "blocked_confidence_dispersion",
            )
        require_paper_only_flags(
            "MarketProbabilitySourceDivergenceDigestConfig",
            self,
        )
        reject_unsafe_surface_fields(
            "market probability source divergence digest config",
            self,
        )


@dataclass(frozen=True)
class MarketProbabilitySourceForecast:
    market_id: str
    source_id: str
    source_family: str
    forecast_probability: Decimal
    confidence: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("MarketProbabilitySourceForecast does not support subclassing")

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("source_id", self.source_id)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_probability("confidence", self.confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                SOURCE_REASON_CODES,
            ),
        )
        reject_unsafe_surface_fields("market probability source forecast", self)
        require_paper_only_flags("MarketProbabilitySourceForecast", self)


@dataclass(frozen=True)
class MarketProbabilitySourceDivergenceInput:
    market_id: str
    market_implied_probability: Decimal
    forecasts: tuple[MarketProbabilitySourceForecast, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "MarketProbabilitySourceDivergenceInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "market_implied_probability",
            _normalize_probability(
                "market_implied_probability",
                self.market_implied_probability,
            ),
        )
        object.__setattr__(self, "forecasts", _normalize_forecasts(self.forecasts))
        for forecast in self.forecasts:
            if forecast.market_id != self.market_id:
                raise ValueError("forecast market_id must match input market_id")
        reject_unsafe_surface_fields("market probability source divergence input", self)
        require_paper_only_flags("MarketProbabilitySourceDivergenceInput", self)


@dataclass(frozen=True)
class MarketProbabilitySourceDivergenceRow:
    market_id: str
    status: str
    market_implied_probability: Decimal
    recency_weighted_forecast_probability: Decimal | None
    probability_gap: Decimal | None
    source_count: Decimal
    source_family_count: Decimal
    stale_source_count: Decimal
    source_family_disagreement: Decimal | None
    confidence_dispersion: Decimal | None
    latest_observed_at: datetime | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "MarketProbabilitySourceDivergenceRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "market_implied_probability",
            _normalize_probability(
                "market_implied_probability",
                self.market_implied_probability,
            ),
        )
        for field_name in ("recency_weighted_forecast_probability", "probability_gap"):
            if getattr(self, field_name) is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_probability(field_name, getattr(self, field_name)),
                )
        for field_name in ("source_count", "source_family_count", "stale_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_family_disagreement", "confidence_dispersion"):
            if getattr(self, field_name) is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_probability_delta(field_name, getattr(self, field_name)),
                )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("market probability source divergence row", self)
        require_paper_only_flags("MarketProbabilitySourceDivergenceRow", self)


@dataclass(frozen=True)
class MarketProbabilitySourceReasonRollup:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "MarketProbabilitySourceReasonRollup does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_count("market_count", self.market_count),
        )
        if self.market_ratio is not None:
            object.__setattr__(
                self,
                "market_ratio",
                _normalize_probability("market_ratio", self.market_ratio),
            )
        reject_unsafe_surface_fields("market probability source reason rollup", self)
        require_paper_only_flags("MarketProbabilitySourceReasonRollup", self)


@dataclass(frozen=True)
class MarketProbabilitySourceDivergenceDigestReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    divergent_market_count: Decimal
    divergent_market_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketProbabilitySourceDivergenceRow, ...]
    reason_rollups: tuple[MarketProbabilitySourceReasonRollup, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "MarketProbabilitySourceDivergenceDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "clear_market_count",
            "watch_market_count",
            "blocked_market_count",
            "divergent_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.divergent_market_ratio is not None:
            object.__setattr__(
                self,
                "divergent_market_ratio",
                _normalize_probability(
                    "divergent_market_ratio",
                    self.divergent_market_ratio,
                ),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_rollups",
            _normalize_rollups(self.reason_rollups),
        )
        _validate_report(self)
        _reject_unsafe_public_payload(
            "market probability source divergence report",
            self,
        )
        reject_unsafe_surface_fields("market probability source divergence report", self)
        require_paper_only_flags("MarketProbabilitySourceDivergenceDigestReport", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_market_probability_source_divergence_digest(
    inputs: list[MarketProbabilitySourceDivergenceInput]
    | tuple[MarketProbabilitySourceDivergenceInput, ...],
    *,
    config: MarketProbabilitySourceDivergenceDigestConfig,
    generated_at: datetime,
) -> MarketProbabilitySourceDivergenceDigestReport:
    if type(config) is not MarketProbabilitySourceDivergenceDigestConfig:
        raise ValueError("config must be a MarketProbabilitySourceDivergenceDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(input_row, config=config, generated_at=generated_at_utc)
                for input_row in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    divergent_count = _count(sum(1 for row in rows if row.status != "clear"))
    return MarketProbabilitySourceDivergenceDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=market_count,
        clear_market_count=_count(sum(1 for row in rows if row.status == "clear")),
        watch_market_count=_count(sum(1 for row in rows if row.status == "watch")),
        blocked_market_count=_count(sum(1 for row in rows if row.status == "blocked")),
        divergent_market_count=divergent_count,
        divergent_market_ratio=(
            None if market_count == _count(0) else _ratio(divergent_count, market_count)
        ),
        status=_status_rollup(tuple(row.status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows),
    )


def market_probability_source_divergence_digest_payload(
    report: MarketProbabilitySourceDivergenceDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not MarketProbabilitySourceDivergenceDigestReport:
        if type(report) is dict:
            _reject_unsafe_public_payload(
                "market probability source divergence digest payload",
                report,
            )
            _require_public_payload_fields(report, PUBLIC_REPORT_FIELDS, "payload")
            _validate_public_payload(report)
            return dict(report)
        raise ValueError("report must be a MarketProbabilitySourceDivergenceDigestReport")
    require_paper_only_flags("report", report)
    _reject_unsafe_public_payload("market probability source divergence report", report)
    reject_unsafe_surface_fields("market probability source divergence report", report)
    _validate_report_derived_validation_digest(report)
    payload = _report_public_payload_values(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    _validate_public_payload(payload)
    return payload


def _build_row(
    input_row: MarketProbabilitySourceDivergenceInput,
    *,
    config: MarketProbabilitySourceDivergenceDigestConfig,
    generated_at: datetime,
) -> MarketProbabilitySourceDivergenceRow:
    forecasts = input_row.forecasts
    source_count = _count(len(forecasts))
    family_count = _count(len({forecast.source_family for forecast in forecasts}))
    latest_observed_at = max((forecast.observed_at for forecast in forecasts), default=None)
    stale_source_count = _count(
        sum(
            1
            for forecast in forecasts
            if _age_seconds(generated_at, forecast.observed_at) > config.stale_after_seconds
        ),
    )
    weighted_forecast = _weighted_forecast_probability(
        forecasts,
        config=config,
        generated_at=generated_at,
    )
    probability_gap = (
        None
        if weighted_forecast is None
        else _abs_decimal(input_row.market_implied_probability - weighted_forecast)
    )
    family_disagreement = _source_family_disagreement(forecasts)
    confidence_dispersion = _confidence_dispersion(forecasts)
    reason_codes = _row_reason_codes(
        probability_gap,
        family_disagreement,
        confidence_dispersion,
        stale_source_count,
        config=config,
    )
    return MarketProbabilitySourceDivergenceRow(
        market_id=input_row.market_id,
        status=_row_status(reason_codes),
        market_implied_probability=input_row.market_implied_probability,
        recency_weighted_forecast_probability=weighted_forecast,
        probability_gap=probability_gap,
        source_count=source_count,
        source_family_count=family_count,
        stale_source_count=stale_source_count,
        source_family_disagreement=family_disagreement,
        confidence_dispersion=confidence_dispersion,
        latest_observed_at=latest_observed_at,
        reason_codes=reason_codes,
    )


def _weighted_forecast_probability(
    forecasts: tuple[MarketProbabilitySourceForecast, ...],
    *,
    config: MarketProbabilitySourceDivergenceDigestConfig,
    generated_at: datetime,
) -> Decimal | None:
    if not forecasts:
        return None
    weighted_sum = ZERO
    total_weight = ZERO
    for forecast in forecasts:
        age_seconds = _age_seconds(generated_at, forecast.observed_at)
        age_days = _ratio(age_seconds, config.recency_half_life_seconds)
        recency_weight = _ratio(ONE, ONE + age_days)
        weight = _normalize_probability_delta(
            "source_weight",
            forecast.confidence * recency_weight,
        )
        weighted_sum += forecast.forecast_probability * weight
        total_weight += weight
    if total_weight == ZERO:
        return None
    return _normalize_probability("recency_weighted_forecast_probability", weighted_sum / total_weight)


def _source_family_disagreement(
    forecasts: tuple[MarketProbabilitySourceForecast, ...],
) -> Decimal | None:
    family_values = tuple(
        _average(
            tuple(
                forecast.forecast_probability
                for forecast in forecasts
                if forecast.source_family == family
            ),
        )
        for family in sorted({forecast.source_family for forecast in forecasts})
    )
    if len(family_values) < 2:
        return None
    return _normalize_probability_delta(
        "source_family_disagreement",
        max(family_values) - min(family_values),
    )


def _confidence_dispersion(
    forecasts: tuple[MarketProbabilitySourceForecast, ...],
) -> Decimal | None:
    if len(forecasts) < 2:
        return None
    values = tuple(forecast.confidence for forecast in forecasts)
    return _normalize_probability_delta(
        "confidence_dispersion",
        max(values) - min(values),
    )


def _row_reason_codes(
    probability_gap: Decimal | None,
    family_disagreement: Decimal | None,
    confidence_dispersion: Decimal | None,
    stale_source_count: Decimal,
    *,
    config: MarketProbabilitySourceDivergenceDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if probability_gap is None:
        codes.append("forecast_recency_degraded")
    elif probability_gap >= config.blocked_probability_gap:
        codes.append("market_probability_source_gap_blocked")
    elif probability_gap >= config.watch_probability_gap:
        codes.append("market_probability_source_gap_watch")
    if family_disagreement is not None:
        if family_disagreement >= config.blocked_family_disagreement:
            codes.append("source_family_disagreement_blocked")
        elif family_disagreement >= config.watch_family_disagreement:
            codes.append("source_family_disagreement_watch")
    if stale_source_count > _count(0):
        codes.append("forecast_recency_degraded")
    if confidence_dispersion is not None:
        if confidence_dispersion >= config.blocked_confidence_dispersion:
            codes.append("confidence_dispersion_blocked")
        elif confidence_dispersion >= config.watch_confidence_dispersion:
            codes.append("confidence_dispersion_watch")
    if not codes:
        codes.append("market_probability_aligned")
    return tuple(dict.fromkeys(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if reason_codes != ("market_probability_aligned",):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketProbabilitySourceDivergenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_market_probability_source_divergence_inputs",)
    codes: list[str] = []
    status = _status_rollup(tuple(row.status for row in rows))
    if status == "blocked":
        codes.append("market_probability_source_divergence_blocked")
    elif status == "watch":
        codes.append("market_probability_source_divergence_watch")
    else:
        codes.append("market_probability_source_divergence_clear")
    if any(
        reason_code.startswith("source_family_disagreement")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("market_source_family_disagreement_present")
    if any("recency" in reason_code for row in rows for reason_code in row.reason_codes):
        codes.append("market_forecast_recency_degraded")
    if any(
        reason_code.startswith("confidence_dispersion")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("market_confidence_dispersion_present")
    return tuple(codes)


def _reason_rollups(
    rows: tuple[MarketProbabilitySourceDivergenceRow, ...],
) -> tuple[MarketProbabilitySourceReasonRollup, ...]:
    counts: dict[str, Decimal] = {}
    market_count = _count(len(rows))
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, _count(0)) + _count(1)
    return tuple(
        MarketProbabilitySourceReasonRollup(
            reason_code=reason_code,
            market_count=count,
            market_ratio=None if market_count == _count(0) else _ratio(count, market_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "clear"


def _row_sort_key(
    row: MarketProbabilitySourceDivergenceRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -(row.probability_gap or ZERO),
        -(row.source_family_disagreement or ZERO),
        row.market_id,
    )


def _normalize_inputs(
    inputs: list[MarketProbabilitySourceDivergenceInput]
    | tuple[MarketProbabilitySourceDivergenceInput, ...],
) -> tuple[MarketProbabilitySourceDivergenceInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketProbabilitySourceDivergenceInput:
            raise ValueError(
                "inputs must contain MarketProbabilitySourceDivergenceInput values",
            )
        require_paper_only_flags("input", row)
        if row.market_id in seen_market_ids:
            raise ValueError("inputs must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return rows


def _normalize_forecasts(value: object) -> tuple[MarketProbabilitySourceForecast, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("forecasts must be a tuple")
    try:
        forecasts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("forecasts must be a tuple") from exc
    seen_source_ids: set[str] = set()
    for forecast in forecasts:
        if type(forecast) is not MarketProbabilitySourceForecast:
            raise ValueError(
                "forecasts must contain MarketProbabilitySourceForecast values",
            )
        require_paper_only_flags("forecast", forecast)
        if forecast.source_id in seen_source_ids:
            raise ValueError("forecasts must not contain duplicate source_id values")
        seen_source_ids.add(forecast.source_id)
    return forecasts


def _normalize_rows(value: object) -> tuple[MarketProbabilitySourceDivergenceRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketProbabilitySourceDivergenceRow:
            raise ValueError("rows must contain MarketProbabilitySourceDivergenceRow values")
        require_paper_only_flags("row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return rows


def _normalize_rollups(value: object) -> tuple[MarketProbabilitySourceReasonRollup, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_rollups must be a tuple")
    try:
        rollups = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_rollups must be a tuple") from exc
    seen_reason_codes: set[str] = set()
    for rollup in rollups:
        if type(rollup) is not MarketProbabilitySourceReasonRollup:
            raise ValueError(
                "reason_rollups must contain MarketProbabilitySourceReasonRollup values",
            )
        require_paper_only_flags("reason rollup", rollup)
        if rollup.reason_code in seen_reason_codes:
            raise ValueError("reason_rollups must not contain duplicate reason_code values")
        seen_reason_codes.add(rollup.reason_code)
    if rollups != tuple(
        sorted(
            rollups,
            key=lambda rollup: (-rollup.market_count, rollup.reason_code),
        ),
    ):
        raise ValueError("reason_rollups must use deterministic ordering")
    return rollups


def _validate_row(row: MarketProbabilitySourceDivergenceRow) -> None:
    if row.source_count == _count(0):
        if row.recency_weighted_forecast_probability is not None:
            raise ValueError("empty rows must not include weighted forecasts")
        if row.probability_gap is not None:
            raise ValueError("empty rows must not include probability_gap")
        if row.source_family_disagreement is not None:
            raise ValueError("empty rows must not include source_family_disagreement")
        if row.confidence_dispersion is not None:
            raise ValueError("empty rows must not include confidence_dispersion")
        if row.latest_observed_at is not None:
            raise ValueError("empty rows must not include latest_observed_at")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: MarketProbabilitySourceDivergenceDigestReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.clear_market_count != _count(sum(1 for row in report.rows if row.status == "clear")):
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _count(
        sum(1 for row in report.rows if row.status == "blocked"),
    ):
        raise ValueError("blocked_market_count must match rows")
    if report.divergent_market_count != _count(
        sum(1 for row in report.rows if row.status != "clear"),
    ):
        raise ValueError("divergent_market_count must match rows")
    expected_ratio = (
        None
        if report.market_count == _count(0)
        else _ratio(report.divergent_market_count, report.market_count)
    )
    if report.divergent_market_ratio != expected_ratio:
        raise ValueError("divergent_market_ratio must match rows")
    if report.status != _status_rollup(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_rollups != _reason_rollups(report.rows):
        raise ValueError("reason_rollups must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_member(field_name, reason_code, allowed)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    quantized = _quantize_ratio(decimal_value)
    if quantized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be nonzero")
    return _quantize_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _ratio(sum(values, ZERO), _count(len(values)))


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize_ratio(-value)
    return _quantize_ratio(value)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    age = seconds + microseconds
    if age < Decimal("0"):
        return ZERO
    return _quantize_ratio(age)


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


def _report_public_payload_values(
    report: MarketProbabilitySourceDivergenceDigestReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "market_count": _decimal_payload(report.market_count),
        "clear_market_count": _decimal_payload(report.clear_market_count),
        "watch_market_count": _decimal_payload(report.watch_market_count),
        "blocked_market_count": _decimal_payload(report.blocked_market_count),
        "divergent_market_count": _decimal_payload(report.divergent_market_count),
        "divergent_market_ratio": _optional_decimal_payload(
            report.divergent_market_ratio,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload_values(row) for row in report.rows],
        "reason_rollups": [
            _rollup_public_payload_values(rollup)
            for rollup in report.reason_rollups
        ],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_public_payload_values(
    row: MarketProbabilitySourceDivergenceRow,
) -> dict[str, Any]:
    return {
        "market_id": row.market_id,
        "status": row.status,
        "market_implied_probability": _decimal_payload(
            row.market_implied_probability,
        ),
        "recency_weighted_forecast_probability": _optional_decimal_payload(
            row.recency_weighted_forecast_probability,
        ),
        "probability_gap": _optional_decimal_payload(row.probability_gap),
        "source_count": _decimal_payload(row.source_count),
        "source_family_count": _decimal_payload(row.source_family_count),
        "stale_source_count": _decimal_payload(row.stale_source_count),
        "source_family_disagreement": _optional_decimal_payload(
            row.source_family_disagreement,
        ),
        "confidence_dispersion": _optional_decimal_payload(row.confidence_dispersion),
        "latest_observed_at": (
            None
            if row.latest_observed_at is None
            else _datetime_payload(row.latest_observed_at)
        ),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _rollup_public_payload_values(
    rollup: MarketProbabilitySourceReasonRollup,
) -> dict[str, Any]:
    return {
        "reason_code": rollup.reason_code,
        "market_count": _decimal_payload(rollup.market_count),
        "market_ratio": _optional_decimal_payload(rollup.market_ratio),
        "paper_only": rollup.paper_only,
        "report_only": rollup.report_only,
        "readonly": rollup.readonly,
    }


def _report_derived_validation_digest(
    report: MarketProbabilitySourceDivergenceDigestReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: MarketProbabilitySourceDivergenceDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST
    )
    return hashlib.sha256(
        (
            "market_probability_source_divergence_digest_derived|"
            + "|".join(values)
        ).encode("utf-8"),
    ).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + "|".join(
            f"{key}:{_digest_payload_value(item)}"
            for key, item in _ordered_payload_items(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    return str(value)


def _ordered_payload_items(value: dict[Any, Any]) -> tuple[tuple[str, Any], ...]:
    if set(value) == set(PUBLIC_ROW_FIELDS):
        field_names = PUBLIC_ROW_FIELDS
    elif set(value) == set(PUBLIC_ROLLUP_FIELDS):
        field_names = PUBLIC_ROLLUP_FIELDS
    elif set(value) == set(PUBLIC_REPORT_FIELDS):
        field_names = PUBLIC_REPORT_FIELDS
    elif set(value) == set(PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST):
        field_names = PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST
    else:
        field_names = tuple(sorted(value))
    return tuple((field_name, value[field_name]) for field_name in field_names)


def _validate_public_payload(payload: dict[str, Any]) -> None:
    for field_name in ("generated_at",):
        _require_datetime_payload_string(field_name, payload[field_name])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "market_count",
        "clear_market_count",
        "watch_market_count",
        "blocked_market_count",
        "divergent_market_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], count=True)
    _require_optional_decimal_payload_string(
        "divergent_market_ratio",
        payload["divergent_market_ratio"],
        probability=True,
    )
    _require_member("status", payload["status"], ROW_STATUSES)
    _normalize_public_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _validate_public_rows(payload["rows"])
    _validate_public_rollups(payload["reason_rollups"])
    _require_payload_hard_flags("payload", payload)
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_public_payload_fields(row, PUBLIC_ROW_FIELDS, "row")
        _require_canonical_string("market_id", row["market_id"])
        _require_member("status", row["status"], ROW_STATUSES)
        _require_decimal_payload_string(
            "market_implied_probability",
            row["market_implied_probability"],
            probability=True,
        )
        for field_name in (
            "recency_weighted_forecast_probability",
            "probability_gap",
            "source_family_disagreement",
            "confidence_dispersion",
        ):
            _require_optional_decimal_payload_string(
                field_name,
                row[field_name],
                probability=True,
            )
        for field_name in (
            "source_count",
            "source_family_count",
            "stale_source_count",
        ):
            _require_decimal_payload_string(field_name, row[field_name], count=True)
        _require_optional_datetime_payload_string(
            "latest_observed_at",
            row["latest_observed_at"],
        )
        _normalize_public_reason_codes(
            "reason_codes",
            row["reason_codes"],
            ROW_REASON_CODES,
        )
        _require_payload_hard_flags("row", row)


def _validate_public_rollups(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_rollups must be a list")
    for rollup in value:
        if type(rollup) is not dict:
            raise ValueError("reason_rollups must contain objects")
        _require_public_payload_fields(rollup, PUBLIC_ROLLUP_FIELDS, "reason_rollup")
        _require_member("reason_code", rollup["reason_code"], ROW_REASON_CODES)
        _require_decimal_payload_string(
            "market_count",
            rollup["market_count"],
            count=True,
        )
        _require_optional_decimal_payload_string(
            "market_ratio",
            rollup["market_ratio"],
            probability=True,
        )
        _require_payload_hard_flags("reason_rollup", rollup)


def _require_public_payload_fields(
    payload: dict[Any, Any],
    expected_fields: tuple[str, ...],
    label: str,
) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    for field_name in expected_fields:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_member(field_name, reason_code, allowed)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        normalized.append(reason_code)
        seen.add(reason_code)
    return tuple(normalized)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    count: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if count:
        normalized_count = _normalize_nonnegative_count(field_name, decimal_value)
        if _decimal_payload(normalized_count) != value:
            raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
        return normalized_count
    normalized_ratio = _normalize_probability_delta(field_name, decimal_value)
    if _decimal_payload(normalized_ratio) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if probability and normalized_ratio > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized_ratio


def _require_optional_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal_payload_string(
        field_name,
        value,
        probability=probability,
    )


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if _datetime_payload(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_optional_datetime_payload_string(
    field_name: str,
    value: object,
) -> datetime | None:
    if value is None:
        return None
    return _require_datetime_payload_string(field_name, value)


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _decimal_payload(value: Decimal) -> str:
    return str(value)


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_payload(value)


def _datetime_payload(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _is_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe live surface field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)


def _is_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        return True
    tokens = _surface_text_tokens(normalized)
    return any(token in tokens for token in UNSAFE_PUBLIC_TEXT_TOKENS)


def _surface_text_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


__all__ = (
    "DEFAULT_MARKET_PROBABILITY_SOURCE_DIVERGENCE_DIGEST_CONFIG_VERSION",
    "MarketProbabilitySourceDivergenceDigestConfig",
    "MarketProbabilitySourceDivergenceDigestReport",
    "MarketProbabilitySourceDivergenceInput",
    "MarketProbabilitySourceDivergenceRow",
    "MarketProbabilitySourceForecast",
    "MarketProbabilitySourceReasonRollup",
    "market_probability_source_divergence_digest_payload",
    "build_market_probability_source_divergence_digest",
)
