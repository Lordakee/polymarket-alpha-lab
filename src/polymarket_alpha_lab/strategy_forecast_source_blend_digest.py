"""Pure Phase 1 reducer for strategy forecast source blend diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_FORECAST_SOURCE_BLEND_DIGEST_CONFIG_VERSION = (
    "strategy-forecast-source-blend-digest-v0"
)

ROW_STATUSES = ("clear", "watch", "blocked")
SOURCE_KINDS = ("model", "team", "market", "research", "other")
SOURCE_REASON_CODES = (
    "model_forecast",
    "manual_team_forecast",
    "market_price",
    "research_source",
)
ROW_REASON_CODES = (
    "source_weighted_blend_available",
    "forecast_source_disagreement_watch",
    "forecast_source_disagreement_blocked",
    "disagreement_cap_applied",
    "missing_forecast_sources",
)
REPORT_REASON_CODES = (
    "strategy_forecast_source_blend_clear",
    "strategy_forecast_source_blend_watch",
    "strategy_forecast_source_blend_blocked",
    "source_weighted_blend_available",
    "forecast_source_disagreement_present",
    "disagreement_cap_limited_candidates",
    "empty_strategy_forecast_blend_inputs",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_WEIGHT = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "clear": Decimal("2"),
}
REDACTED_REFERENCE = "<redacted>"
SENSITIVE_REFERENCE_FRAGMENTS = (
    "private_key",
    "secret",
    "token",
    "credential",
    "password",
)


@dataclass(frozen=True)
class StrategyForecastSourceBlendDigestConfig:
    config_version: str = DEFAULT_STRATEGY_FORECAST_SOURCE_BLEND_DIGEST_CONFIG_VERSION
    model_weight: Decimal = Decimal("0.300000")
    team_weight: Decimal = Decimal("0.300000")
    market_weight: Decimal = Decimal("0.200000")
    source_blend_weight: Decimal = Decimal("0.200000")
    watch_disagreement_gap: Decimal = Decimal("0.050000")
    blocked_disagreement_gap: Decimal = Decimal("0.250000")
    max_market_disagreement_gap: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "model_weight",
            "team_weight",
            "market_weight",
            "source_blend_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_disagreement_gap",
            "blocked_disagreement_gap",
            "max_market_disagreement_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_delta(field_name, getattr(self, field_name)),
            )
        if self.watch_disagreement_gap > self.blocked_disagreement_gap:
            raise ValueError("watch_disagreement_gap must not exceed blocked_disagreement_gap")
        require_paper_only_flags("StrategyForecastSourceBlendDigestConfig", self)


@dataclass(frozen=True)
class StrategyForecastBlendSource:
    candidate_id: str
    source_id: str
    source_kind: str
    probability: Decimal
    reliability_weight: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "probability",
            _normalize_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "reliability_weight",
            _normalize_nonnegative_decimal(
                "reliability_weight",
                self.reliability_weight,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, SOURCE_REASON_CODES),
        )
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        require_paper_only_flags("StrategyForecastBlendSource", self)


@dataclass(frozen=True)
class StrategyForecastBlendCandidate:
    candidate_id: str
    model_forecast: Decimal | None
    team_forecast: Decimal | None
    market_price: Decimal | None
    sources: tuple[StrategyForecastBlendSource, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in ("model_forecast", "team_forecast", "market_price"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_probability(field_name, value),
                )
        object.__setattr__(self, "sources", _normalize_sources(self.candidate_id, self.sources))
        require_paper_only_flags("StrategyForecastBlendCandidate", self)


@dataclass(frozen=True)
class StrategyForecastBlendSourceRow:
    source_id: str
    source_kind: str
    probability: Decimal
    reliability_weight: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    reference: str | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_id", self.source_id)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "probability",
            _normalize_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "reliability_weight",
            _normalize_nonnegative_decimal(
                "reliability_weight",
                self.reliability_weight,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, SOURCE_REASON_CODES),
        )
        object.__setattr__(self, "reference", _redact_reference(self.reference))
        require_paper_only_flags("StrategyForecastBlendSourceRow", self)


@dataclass(frozen=True)
class StrategyForecastSourceBlendRow:
    candidate_id: str
    status: str
    model_forecast: Decimal | None
    team_forecast: Decimal | None
    market_price: Decimal | None
    source_weighted_probability: Decimal | None
    blended_probability: Decimal | None
    disagreement_gap: Decimal | None
    applied_disagreement_cap: Decimal
    candidate_probability: Decimal | None
    source_count: Decimal
    source_reliability_weight: Decimal
    latest_observed_at: datetime | None
    reason_codes: tuple[str, ...]
    sources: tuple[StrategyForecastBlendSourceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_member("status", self.status, ROW_STATUSES)
        for field_name in (
            "model_forecast",
            "team_forecast",
            "market_price",
            "source_weighted_probability",
            "blended_probability",
            "disagreement_gap",
            "candidate_probability",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_probability(field_name, value),
                )
        object.__setattr__(
            self,
            "applied_disagreement_cap",
            _normalize_probability_delta(
                "applied_disagreement_cap",
                self.applied_disagreement_cap,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "source_reliability_weight",
            _normalize_nonnegative_decimal(
                "source_reliability_weight",
                self.source_reliability_weight,
            ),
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
        object.__setattr__(self, "sources", _normalize_source_rows(self.sources))
        _validate_row(self)
        require_paper_only_flags("StrategyForecastSourceBlendRow", self)


@dataclass(frozen=True)
class StrategyForecastSourceBlendReasonRollup:
    reason_code: str
    candidate_count: Decimal
    candidate_ratio: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_nonnegative_count("candidate_count", self.candidate_count),
        )
        if self.candidate_ratio is not None:
            object.__setattr__(
                self,
                "candidate_ratio",
                _normalize_probability("candidate_ratio", self.candidate_ratio),
            )
        require_paper_only_flags("StrategyForecastSourceBlendReasonRollup", self)


@dataclass(frozen=True)
class StrategyForecastSourceBlendDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    clear_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    capped_candidate_count: Decimal
    capped_candidate_ratio: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyForecastSourceBlendRow, ...]
    reason_rollups: tuple[StrategyForecastSourceBlendReasonRollup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "clear_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
            "capped_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.capped_candidate_ratio is not None:
            object.__setattr__(
                self,
                "capped_candidate_ratio",
                _normalize_probability("capped_candidate_ratio", self.capped_candidate_ratio),
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
        object.__setattr__(self, "reason_rollups", _normalize_rollups(self.reason_rollups))
        _validate_report(self)
        require_paper_only_flags("StrategyForecastSourceBlendDigestReport", self)


def build_strategy_forecast_source_blend_digest(
    candidates: list[StrategyForecastBlendCandidate]
    | tuple[StrategyForecastBlendCandidate, ...],
    *,
    config: StrategyForecastSourceBlendDigestConfig,
    generated_at: datetime,
) -> StrategyForecastSourceBlendDigestReport:
    if type(config) is not StrategyForecastSourceBlendDigestConfig:
        raise ValueError("config must be a StrategyForecastSourceBlendDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(candidate, config=config)
                for candidate in _normalize_candidates(candidates)
            ),
            key=_row_sort_key,
        ),
    )
    candidate_count = _count(len(rows))
    capped_count = _count(
        sum(1 for row in rows if row.applied_disagreement_cap > ZERO),
    )
    return StrategyForecastSourceBlendDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=candidate_count,
        clear_candidate_count=_count(sum(1 for row in rows if row.status == "clear")),
        watch_candidate_count=_count(sum(1 for row in rows if row.status == "watch")),
        blocked_candidate_count=_count(sum(1 for row in rows if row.status == "blocked")),
        capped_candidate_count=capped_count,
        capped_candidate_ratio=(
            None if candidate_count == _count(0) else _ratio(capped_count, candidate_count)
        ),
        status=_status_rollup(tuple(row.status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        reason_rollups=_reason_rollups(rows),
    )


def strategy_forecast_source_blend_digest_payload(
    report: StrategyForecastSourceBlendDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyForecastSourceBlendDigestReport:
        raise ValueError("report must be a StrategyForecastSourceBlendDigestReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy forecast source blend digest report", report)
    payload = json_ready_no_floats(report)
    reject_unsafe_surface_fields("strategy forecast source blend digest payload", payload)
    return payload


def _build_row(
    candidate: StrategyForecastBlendCandidate,
    *,
    config: StrategyForecastSourceBlendDigestConfig,
) -> StrategyForecastSourceBlendRow:
    sources = tuple(
        StrategyForecastBlendSourceRow(
            source_id=source.source_id,
            source_kind=source.source_kind,
            probability=source.probability,
            reliability_weight=source.reliability_weight,
            observed_at=source.observed_at,
            reason_codes=source.reason_codes,
            reference=source.reference,
        )
        for source in sorted(candidate.sources, key=_source_sort_key)
    )
    source_count = _count(len(sources))
    source_reliability_weight = _normalize_nonnegative_decimal(
        "source_reliability_weight",
        sum((source.reliability_weight for source in sources), ZERO),
    )
    source_weighted_probability = _source_weighted_probability(sources)
    blended_probability = _blended_probability(
        candidate,
        source_weighted_probability=source_weighted_probability,
        config=config,
    )
    disagreement_gap = _disagreement_gap(candidate, source_weighted_probability)
    applied_cap = _applied_disagreement_cap(
        blended_probability=blended_probability,
        market_price=candidate.market_price,
        disagreement_gap=disagreement_gap,
        config=config,
    )
    candidate_probability = _capped_candidate_probability(
        blended_probability=blended_probability,
        market_price=candidate.market_price,
        applied_cap=applied_cap,
    )
    reason_codes = _row_reason_codes(
        source_weighted_probability=source_weighted_probability,
        disagreement_gap=disagreement_gap,
        applied_cap=applied_cap,
        config=config,
    )
    return StrategyForecastSourceBlendRow(
        candidate_id=candidate.candidate_id,
        status=_row_status(reason_codes),
        model_forecast=candidate.model_forecast,
        team_forecast=candidate.team_forecast,
        market_price=candidate.market_price,
        source_weighted_probability=source_weighted_probability,
        blended_probability=blended_probability,
        disagreement_gap=disagreement_gap,
        applied_disagreement_cap=applied_cap,
        candidate_probability=candidate_probability,
        source_count=source_count,
        source_reliability_weight=source_reliability_weight,
        latest_observed_at=max((source.observed_at for source in sources), default=None),
        reason_codes=reason_codes,
        sources=sources,
    )


def _source_weighted_probability(
    sources: tuple[StrategyForecastBlendSourceRow, ...],
) -> Decimal | None:
    if not sources:
        return None
    total_weight = sum((source.reliability_weight for source in sources), ZERO)
    if total_weight == ZERO:
        return None
    weighted_sum = sum(
        (source.probability * source.reliability_weight for source in sources),
        ZERO,
    )
    return _normalize_probability("source_weighted_probability", weighted_sum / total_weight)


def _blended_probability(
    candidate: StrategyForecastBlendCandidate,
    *,
    source_weighted_probability: Decimal | None,
    config: StrategyForecastSourceBlendDigestConfig,
) -> Decimal | None:
    weighted_sum = ZERO
    total_weight = ZERO
    weighted_sum, total_weight = _add_optional_weight(
        weighted_sum,
        total_weight,
        candidate.model_forecast,
        config.model_weight,
    )
    weighted_sum, total_weight = _add_optional_weight(
        weighted_sum,
        total_weight,
        candidate.team_forecast,
        config.team_weight,
    )
    weighted_sum, total_weight = _add_optional_weight(
        weighted_sum,
        total_weight,
        candidate.market_price,
        config.market_weight,
    )
    weighted_sum, total_weight = _add_optional_weight(
        weighted_sum,
        total_weight,
        source_weighted_probability,
        config.source_blend_weight,
    )
    if total_weight == ZERO:
        return None
    return _normalize_probability("blended_probability", weighted_sum / total_weight)


def _add_optional_weight(
    weighted_sum: Decimal,
    total_weight: Decimal,
    value: Decimal | None,
    weight: Decimal,
) -> tuple[Decimal, Decimal]:
    if value is None or weight == ZERO:
        return weighted_sum, total_weight
    return weighted_sum + value * weight, total_weight + weight


def _disagreement_gap(
    candidate: StrategyForecastBlendCandidate,
    source_weighted_probability: Decimal | None,
) -> Decimal | None:
    values = tuple(
        value
        for value in (
            candidate.model_forecast,
            candidate.team_forecast,
            candidate.market_price,
            source_weighted_probability,
        )
        if value is not None
    )
    if len(values) < 2:
        return None
    return _normalize_probability_delta("disagreement_gap", max(values) - min(values))


def _applied_disagreement_cap(
    *,
    blended_probability: Decimal | None,
    market_price: Decimal | None,
    disagreement_gap: Decimal | None,
    config: StrategyForecastSourceBlendDigestConfig,
) -> Decimal:
    if blended_probability is None or market_price is None or disagreement_gap is None:
        return ZERO
    if disagreement_gap < config.blocked_disagreement_gap:
        return ZERO
    market_gap = _abs_decimal(blended_probability - market_price)
    if market_gap <= config.max_market_disagreement_gap:
        return ZERO
    return config.max_market_disagreement_gap


def _capped_candidate_probability(
    *,
    blended_probability: Decimal | None,
    market_price: Decimal | None,
    applied_cap: Decimal,
) -> Decimal | None:
    if blended_probability is None:
        return None
    if market_price is None or applied_cap == ZERO:
        return blended_probability
    if blended_probability > market_price:
        return _normalize_probability(
            "candidate_probability",
            market_price + applied_cap,
        )
    return _normalize_probability("candidate_probability", market_price - applied_cap)


def _row_reason_codes(
    *,
    source_weighted_probability: Decimal | None,
    disagreement_gap: Decimal | None,
    applied_cap: Decimal,
    config: StrategyForecastSourceBlendDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if source_weighted_probability is None:
        codes.append("missing_forecast_sources")
    else:
        codes.append("source_weighted_blend_available")
    if disagreement_gap is not None:
        if disagreement_gap >= config.blocked_disagreement_gap:
            codes.append("forecast_source_disagreement_blocked")
        elif disagreement_gap >= config.watch_disagreement_gap:
            codes.append("forecast_source_disagreement_watch")
    if applied_cap > ZERO:
        codes.append("disagreement_cap_applied")
    return tuple(dict.fromkeys(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "forecast_source_disagreement_blocked" in reason_codes:
        return "blocked"
    if reason_codes != ("source_weighted_blend_available",):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[StrategyForecastSourceBlendRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_strategy_forecast_blend_inputs",)
    codes: list[str] = []
    status = _status_rollup(tuple(row.status for row in rows))
    if status == "blocked":
        codes.append("strategy_forecast_source_blend_blocked")
    elif status == "watch":
        codes.append("strategy_forecast_source_blend_watch")
    else:
        codes.append("strategy_forecast_source_blend_clear")
    if any("source_weighted_blend_available" in row.reason_codes for row in rows):
        codes.append("source_weighted_blend_available")
    if any(
        reason_code.startswith("forecast_source_disagreement")
        for row in rows
        for reason_code in row.reason_codes
    ):
        codes.append("forecast_source_disagreement_present")
    if any("disagreement_cap_applied" in row.reason_codes for row in rows):
        codes.append("disagreement_cap_limited_candidates")
    return tuple(codes)


def _reason_rollups(
    rows: tuple[StrategyForecastSourceBlendRow, ...],
) -> tuple[StrategyForecastSourceBlendReasonRollup, ...]:
    counts: dict[str, Decimal] = {}
    candidate_count = _count(len(rows))
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, _count(0)) + _count(1)
    return tuple(
        StrategyForecastSourceBlendReasonRollup(
            reason_code=reason_code,
            candidate_count=count,
            candidate_ratio=(
                None if candidate_count == _count(0) else _ratio(count, candidate_count)
            ),
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


def _row_sort_key(row: StrategyForecastSourceBlendRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -(row.disagreement_gap or ZERO),
        row.candidate_id,
    )


def _source_sort_key(
    source: StrategyForecastBlendSource,
) -> tuple[Decimal, Decimal, str]:
    return (-source.reliability_weight, source.probability, source.source_id)


def _normalize_candidates(
    candidates: list[StrategyForecastBlendCandidate]
    | tuple[StrategyForecastBlendCandidate, ...],
) -> tuple[StrategyForecastBlendCandidate, ...]:
    if type(candidates) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    rows = tuple(candidates)
    seen_candidate_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyForecastBlendCandidate:
            raise ValueError("candidates must contain StrategyForecastBlendCandidate values")
        require_paper_only_flags("candidate", row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("duplicate candidate_id values are not allowed")
        seen_candidate_ids.add(row.candidate_id)
    return rows


def _normalize_sources(
    candidate_id: str,
    sources: tuple[StrategyForecastBlendSource, ...],
) -> tuple[StrategyForecastBlendSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    rows = tuple(sources)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyForecastBlendSource:
            raise ValueError("sources must contain StrategyForecastBlendSource values")
        require_paper_only_flags("source", row)
        if row.candidate_id != candidate_id:
            raise ValueError("source candidate_id must match candidate_id")
        if row.source_id in seen_source_ids:
            raise ValueError("duplicate source_id values are not allowed")
        seen_source_ids.add(row.source_id)
    return rows


def _normalize_source_rows(
    sources: tuple[StrategyForecastBlendSourceRow, ...],
) -> tuple[StrategyForecastBlendSourceRow, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    rows = tuple(sources)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyForecastBlendSourceRow:
            raise ValueError("sources must contain StrategyForecastBlendSourceRow values")
        require_paper_only_flags("source row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("duplicate source_id values are not allowed")
        seen_source_ids.add(row.source_id)
    if rows != tuple(sorted(rows, key=lambda row: (-row.reliability_weight, row.probability, row.source_id))):
        raise ValueError("sources must be sorted by reliability_weight and source_id")
    return rows


def _normalize_rows(
    rows: tuple[StrategyForecastSourceBlendRow, ...],
) -> tuple[StrategyForecastSourceBlendRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_candidate_ids: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyForecastSourceBlendRow:
            raise ValueError("rows must contain StrategyForecastSourceBlendRow values")
        require_paper_only_flags("row", row)
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("duplicate row candidate_id values are not allowed")
        seen_candidate_ids.add(row.candidate_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and candidate_id")
    return normalized


def _normalize_rollups(
    rollups: tuple[StrategyForecastSourceBlendReasonRollup, ...],
) -> tuple[StrategyForecastSourceBlendReasonRollup, ...]:
    if type(rollups) not in (list, tuple):
        raise ValueError("reason_rollups must be a list or tuple")
    normalized = tuple(rollups)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyForecastSourceBlendReasonRollup:
            raise ValueError("reason_rollups must contain reason rollup values")
        require_paper_only_flags("reason rollup", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("duplicate reason_code values are not allowed")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda row: (-row.candidate_count, row.reason_code)),
    ):
        raise ValueError("reason_rollups must be sorted by candidate_count and reason_code")
    return normalized


def _validate_row(row: StrategyForecastSourceBlendRow) -> None:
    if row.source_count != _count(len(row.sources)):
        raise ValueError("source_count must match sources")
    expected_reliability = _normalize_nonnegative_decimal(
        "source_reliability_weight",
        sum((source.reliability_weight for source in row.sources), ZERO),
    )
    if row.source_reliability_weight != expected_reliability:
        raise ValueError("source_reliability_weight must match sources")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.applied_disagreement_cap > ZERO and "disagreement_cap_applied" not in row.reason_codes:
        raise ValueError("applied_disagreement_cap must match reason_codes")


def _validate_report(report: StrategyForecastSourceBlendDigestReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    expected_clear = _count(sum(1 for row in report.rows if row.status == "clear"))
    expected_watch = _count(sum(1 for row in report.rows if row.status == "watch"))
    expected_blocked = _count(sum(1 for row in report.rows if row.status == "blocked"))
    expected_capped = _count(
        sum(1 for row in report.rows if row.applied_disagreement_cap > ZERO),
    )
    if report.clear_candidate_count != expected_clear:
        raise ValueError("clear_candidate_count must match rows")
    if report.watch_candidate_count != expected_watch:
        raise ValueError("watch_candidate_count must match rows")
    if report.blocked_candidate_count != expected_blocked:
        raise ValueError("blocked_candidate_count must match rows")
    if report.capped_candidate_count != expected_capped:
        raise ValueError("capped_candidate_count must match rows")
    expected_ratio = (
        None
        if report.candidate_count == _count(0)
        else _ratio(report.capped_candidate_count, report.candidate_count)
    )
    if report.capped_candidate_ratio != expected_ratio:
        raise ValueError("capped_candidate_ratio must match capped_candidate_count")
    if report.status != _status_rollup(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_rollups != _reason_rollups(report.rows):
        raise ValueError("reason_rollups must match rows")


def _redact_reference(value: str | None) -> str | None:
    if value is None:
        return None
    _require_canonical_string("reference", value)
    lowered = value.lower()
    if _has_reference_risk(lowered):
        return REDACTED_REFERENCE
    return value


def _has_reference_risk(value: str) -> bool:
    return any(fragment in value for fragment in SENSITIVE_REFERENCE_FRAGMENTS) or any(
        fragment in value for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS
    )


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _normalize_reason_codes(
    name: str,
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    codes = tuple(reason_codes)
    seen_codes: set[str] = set()
    for reason_code in codes:
        _require_member(name, reason_code, allowed)
        if reason_code in seen_codes:
            raise ValueError(f"{name} must not contain duplicates")
        seen_codes.add(reason_code)
    return tuple(reason_code for reason_code in allowed if reason_code in seen_codes)


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _normalize_probability(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_probability_delta(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, RATIO_QUANTUM)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal, COUNT_QUANTUM)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator, RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    return -value if value < ZERO else value


__all__ = (
    "DEFAULT_STRATEGY_FORECAST_SOURCE_BLEND_DIGEST_CONFIG_VERSION",
    "StrategyForecastSourceBlendDigestConfig",
    "StrategyForecastBlendSource",
    "StrategyForecastBlendCandidate",
    "StrategyForecastBlendSourceRow",
    "StrategyForecastSourceBlendRow",
    "StrategyForecastSourceBlendReasonRollup",
    "StrategyForecastSourceBlendDigestReport",
    "build_strategy_forecast_source_blend_digest",
    "strategy_forecast_source_blend_digest_payload",
)
