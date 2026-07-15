"""Pure market-depth probability-memory scorecard for paper research.

Rows aggregate observations by exact private ``market_id``. When one market has
multiple candidate IDs, its public representative is the digest of the
lexicographically smallest ``candidate_id``. A candidate digest may therefore
repeat across different market rows; ``market_digest`` is the unique row
identity.

Each observation's ``source_count`` is a caller-deduplicated total. Row counts
sum those values without inspecting ``source_reference``. Memory age equal to
the configured stale threshold is blocking.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import (
    Context,
    Decimal,
    DecimalException,
    ROUND_HALF_EVEN,
    localcontext,
)
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION",
    "ResearchMarketDepthProbabilityMemoryScorecardConfig",
    "ResearchMarketDepthProbabilityMemoryScorecardObservation",
    "ResearchMarketDepthProbabilityMemoryScorecardReport",
    "ResearchMarketDepthProbabilityMemoryScorecardRow",
    "build_research_market_depth_probability_memory_scorecard_report",
    "research_market_depth_probability_memory_scorecard_public_payload",
    "validate_research_market_depth_probability_memory_scorecard_report_digest",
)


DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION = (
    "research-market-depth-probability-memory-scorecard-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
HEX_CHARS = frozenset("0123456789abcdef")
EMPTY_REASON = "no_market_depth_probability_memory_inputs"


class _FinalRecord:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalRecord and issubclass(base, _FinalRecord):
                raise TypeError(f"{base.__name__} cannot be subclassed")


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityMemoryScorecardConfig(_FinalRecord):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION
    )
    target_depth: Decimal = Decimal("1000.000000")
    min_source_count: Decimal = Decimal("3.000000")
    pass_score_min: Decimal = Decimal("0.750000")
    watch_score_min: Decimal = Decimal("0.450000")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    probability_memory_weight: Decimal = Decimal("0.400000")
    market_depth_weight: Decimal = Decimal("0.400000")
    source_diversity_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_record(
            self,
            ResearchMarketDepthProbabilityMemoryScorecardConfig,
            "config",
        )
        if (
            type(self.config_version) is not str
            or self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "target_depth",
            _require_positive_decimal("target_depth", self.target_depth),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_whole_decimal(
                "min_source_count",
                self.min_source_count,
            ),
        )
        for field_name in (
            "pass_score_min",
            "watch_score_min",
            "probability_memory_weight",
            "market_depth_weight",
            "source_diversity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_memory_age_seconds",
            _require_positive_decimal(
                "stale_memory_age_seconds",
                self.stale_memory_age_seconds,
            ),
        )
        if self.pass_score_min <= self.watch_score_min:
            raise ValueError("pass_score_min must be greater than watch_score_min")
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.probability_memory_weight
                + self.market_depth_weight
                + self.source_diversity_weight,
            )
        if weight_sum != ONE:
            raise ValueError("scorecard weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityMemoryScorecardObservation(_FinalRecord):
    candidate_id: str
    market_id: str
    source_reference: str
    probability: Decimal
    previous_probability: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    source_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_record(
            self,
            ResearchMarketDepthProbabilityMemoryScorecardObservation,
            "observation",
        )
        for field_name in ("candidate_id", "market_id", "source_reference"):
            object.__setattr__(
                self,
                field_name,
                _require_private_text(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability", "previous_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_depth", "ask_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_whole_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityMemoryScorecardRow(_FinalRecord):
    candidate_digest: str
    market_digest: str
    observation_count: Decimal
    latest_memory_age_seconds: Decimal
    average_probability: Decimal
    average_probability_delta_abs: Decimal
    probability_memory_score: Decimal
    average_depth: Decimal
    market_depth_score: Decimal
    source_count: Decimal
    source_diversity_score: Decimal
    score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_record(
            self,
            ResearchMarketDepthProbabilityMemoryScorecardRow,
            "row",
        )
        _require_private_digest("candidate_digest", self.candidate_digest)
        _require_private_digest("market_digest", self.market_digest)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_whole_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_memory_age_seconds",
            _require_nonnegative_decimal(
                "latest_memory_age_seconds",
                self.latest_memory_age_seconds,
            ),
        )
        for field_name in (
            "average_probability",
            "average_probability_delta_abs",
            "probability_memory_score",
            "market_depth_score",
            "source_diversity_score",
            "score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_depth",
            _require_nonnegative_decimal("average_depth", self.average_depth),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_whole_decimal("source_count", self.source_count),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_shape(self)

    @property
    def decimals(self) -> tuple[Decimal, ...]:
        return (
            self.observation_count,
            self.latest_memory_age_seconds,
            self.average_probability,
            self.average_probability_delta_abs,
            self.probability_memory_score,
            self.average_depth,
            self.market_depth_score,
            self.source_count,
            self.source_diversity_score,
            self.score,
        )


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityMemoryScorecardReport(_FinalRecord):
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketDepthProbabilityMemoryScorecardRow, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig = field(
        default_factory=ResearchMarketDepthProbabilityMemoryScorecardConfig,
    )

    def __post_init__(self) -> None:
        _require_exact_record(
            self,
            ResearchMarketDepthProbabilityMemoryScorecardReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _revalidate_config(self.config)
        if (
            type(self.config_version) is not str
            or self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.average_score is not None:
            object.__setattr__(
                self,
                "average_score",
                _require_ratio_decimal("average_score", self.average_score),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_rows(self.rows, config=self.config),
        )
        _require_hard_flags("report", self)
        _validate_report(self, config=self.config)
        expected_digest = _digest_payload(
            _report_public_body(self, config=self.config),
        )
        if self.validation_digest == "":
            object.__setattr__(self, "validation_digest", expected_digest)
        else:
            _require_validation_digest("validation_digest", self.validation_digest)
            if self.validation_digest != expected_digest:
                raise ValueError("validation_digest does not match public payload")


def build_research_market_depth_probability_memory_scorecard_report(
    observations: Iterable[ResearchMarketDepthProbabilityMemoryScorecardObservation],
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketDepthProbabilityMemoryScorecardReport:
    if type(config) is not ResearchMarketDepthProbabilityMemoryScorecardConfig:
        raise ValueError(
            "config must be a "
            "ResearchMarketDepthProbabilityMemoryScorecardConfig",
        )
    _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchMarketDepthProbabilityMemoryScorecardObservation]] = {}
    for item in normalized:
        grouped.setdefault(item.market_id, []).append(item)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    tuple(group),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for group in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketDepthProbabilityMemoryScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_score=_average_decimal(tuple(row.score for row in rows)) if rows else None,
        status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
        config=config,
    )


def research_market_depth_probability_memory_scorecard_public_payload(
    report: ResearchMarketDepthProbabilityMemoryScorecardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthProbabilityMemoryScorecardReport:
        raise ValueError(
            "report must be a "
            "ResearchMarketDepthProbabilityMemoryScorecardReport",
        )
    config = report.config
    _require_hard_flags("report", report)
    _validate_report(report, config=config)
    body = _report_public_body(report, config=config)
    expected_digest = _digest_payload(body)
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest does not match public payload")
    return {**body, "validation_digest": report.validation_digest}


def validate_research_market_depth_probability_memory_scorecard_report_digest(
    report: object,
) -> bool:
    if type(report) is not ResearchMarketDepthProbabilityMemoryScorecardReport:
        return False
    try:
        config = report.config
        _require_hard_flags("report", report)
        _validate_report(report, config=config)
        _require_validation_digest("validation_digest", report.validation_digest)
        return report.validation_digest == _digest_payload(
            _report_public_body(report, config=config),
        )
    except (DecimalException, TypeError, ValueError):
        return False


def _row_from_observations(
    observations: tuple[ResearchMarketDepthProbabilityMemoryScorecardObservation, ...],
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
    generated_at: datetime,
) -> ResearchMarketDepthProbabilityMemoryScorecardRow:
    values = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.observed_at.isoformat(),
                item.candidate_id,
                item.source_reference,
                str(item.probability),
                str(item.previous_probability),
                str(item.bid_depth),
                str(item.ask_depth),
                str(item.source_count),
            ),
        ),
    )
    probabilities = tuple(item.probability for item in values)
    with localcontext(DECIMAL_CONTEXT):
        probability_deltas = tuple(
            _quantize(abs(item.probability - item.previous_probability))
            for item in values
        )
        depths = tuple(_quantize(item.bid_depth + item.ask_depth) for item in values)
    average_probability = _average_decimal(probabilities)
    average_probability_delta_abs = _average_decimal(probability_deltas)
    with localcontext(DECIMAL_CONTEXT):
        probability_memory_score = _quantize(ONE - average_probability_delta_abs)
    average_depth = _average_decimal(depths)
    market_depth_score = _capped_ratio(average_depth, config.target_depth)
    source_count = _sum_decimals(tuple(item.source_count for item in values))
    source_diversity_score = _capped_ratio(source_count, config.min_source_count)
    score = _weighted_score(
        probability_memory_score=probability_memory_score,
        market_depth_score=market_depth_score,
        source_diversity_score=source_diversity_score,
        config=config,
    )
    newest_observed_at = max(item.observed_at for item in values)
    latest_memory_age_seconds = _seconds_between(newest_observed_at, generated_at)
    status = _row_status(
        score=score,
        latest_memory_age_seconds=latest_memory_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        values,
        status=status,
        probability_memory_score=probability_memory_score,
        average_depth=average_depth,
        source_count=source_count,
        latest_memory_age_seconds=latest_memory_age_seconds,
        config=config,
    )
    row = ResearchMarketDepthProbabilityMemoryScorecardRow(
        candidate_digest=_private_digest(min(item.candidate_id for item in values)),
        market_digest=_private_digest(values[0].market_id),
        observation_count=_decimal_count(len(values)),
        latest_memory_age_seconds=latest_memory_age_seconds,
        average_probability=average_probability,
        average_probability_delta_abs=average_probability_delta_abs,
        probability_memory_score=probability_memory_score,
        average_depth=average_depth,
        market_depth_score=market_depth_score,
        source_count=source_count,
        source_diversity_score=source_diversity_score,
        score=score,
        status=status,
        reason_codes=reason_codes,
    )
    _validate_row(row, config=config)
    return row


def _weighted_score(
    *,
    probability_memory_score: Decimal,
    market_depth_score: Decimal,
    source_diversity_score: Decimal,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            probability_memory_score * config.probability_memory_weight
            + market_depth_score * config.market_depth_weight
            + source_diversity_score * config.source_diversity_weight,
        )


def _row_status(
    *,
    score: Decimal,
    latest_memory_age_seconds: Decimal,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> str:
    if latest_memory_age_seconds >= config.stale_memory_age_seconds:
        return "block"
    if score >= config.pass_score_min:
        return "pass"
    if score >= config.watch_score_min:
        return "watch"
    return "block"


def _row_reason_codes(
    observations: tuple[ResearchMarketDepthProbabilityMemoryScorecardObservation, ...],
    *,
    status: str,
    probability_memory_score: Decimal,
    average_depth: Decimal,
    source_count: Decimal,
    latest_memory_age_seconds: Decimal,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> tuple[str, ...]:
    input_reason_codes = tuple(
        sorted(
            {
                f"input_{reason_code}"
                for item in observations
                for reason_code in item.reason_codes
            },
        ),
    )
    return _row_reason_codes_from_input_reasons(
        input_reason_codes,
        status=status,
        probability_memory_score=probability_memory_score,
        average_depth=average_depth,
        source_count=source_count,
        latest_memory_age_seconds=latest_memory_age_seconds,
        config=config,
    )


def _row_reason_codes_from_input_reasons(
    input_reason_codes: tuple[str, ...],
    *,
    status: str,
    probability_memory_score: Decimal,
    average_depth: Decimal,
    source_count: Decimal,
    latest_memory_age_seconds: Decimal,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> tuple[str, ...]:
    values = set(input_reason_codes)
    values.add(f"market_depth_probability_memory_{status}")
    if probability_memory_score >= config.pass_score_min:
        values.add("probability_memory_stable")
    elif probability_memory_score >= config.watch_score_min:
        values.add("probability_memory_watch")
    else:
        values.add("probability_memory_unstable")
    values.add(
        "sufficient_depth"
        if average_depth >= config.target_depth
        else "insufficient_depth",
    )
    values.add(
        "sufficient_source_count"
        if source_count >= config.min_source_count
        else "insufficient_source_count",
    )
    if latest_memory_age_seconds >= config.stale_memory_age_seconds:
        values.add("stale_probability_memory")
    return tuple(sorted(values))


def _report_status(
    rows: tuple[ResearchMarketDepthProbabilityMemoryScorecardRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthProbabilityMemoryScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _report_public_body(
    report: ResearchMarketDepthProbabilityMemoryScorecardReport,
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> dict[str, Any]:
    _revalidate_config(config)
    if config is not report.config:
        raise ValueError("config must be the exact report config")
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "config": _config_public_payload(config),
        "row_count": _decimal_payload(report.row_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_score": (
            None
            if report.average_score is None
            else _decimal_payload(report.average_score)
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _config_public_payload(
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> dict[str, Any]:
    return {
        "config_version": config.config_version,
        "target_depth": _decimal_payload(config.target_depth),
        "min_source_count": _decimal_payload(config.min_source_count),
        "pass_score_min": _decimal_payload(config.pass_score_min),
        "watch_score_min": _decimal_payload(config.watch_score_min),
        "stale_memory_age_seconds": _decimal_payload(
            config.stale_memory_age_seconds,
        ),
        "probability_memory_weight": _decimal_payload(
            config.probability_memory_weight,
        ),
        "market_depth_weight": _decimal_payload(config.market_depth_weight),
        "source_diversity_weight": _decimal_payload(
            config.source_diversity_weight,
        ),
        "paper_only": config.paper_only,
        "report_only": config.report_only,
        "readonly": config.readonly,
    }


def _row_public_payload(
    row: ResearchMarketDepthProbabilityMemoryScorecardRow,
) -> dict[str, Any]:
    return {
        "candidate_digest": row.candidate_digest,
        "market_digest": row.market_digest,
        "observation_count": _decimal_payload(row.observation_count),
        "latest_memory_age_seconds": _decimal_payload(
            row.latest_memory_age_seconds,
        ),
        "average_probability": _decimal_payload(row.average_probability),
        "average_probability_delta_abs": _decimal_payload(
            row.average_probability_delta_abs,
        ),
        "probability_memory_score": _decimal_payload(row.probability_memory_score),
        "average_depth": _decimal_payload(row.average_depth),
        "market_depth_score": _decimal_payload(row.market_depth_score),
        "source_count": _decimal_payload(row.source_count),
        "source_diversity_score": _decimal_payload(row.source_diversity_score),
        "score": _decimal_payload(row.score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_row_shape(
    row: ResearchMarketDepthProbabilityMemoryScorecardRow,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_memory_score = _quantize(ONE - row.average_probability_delta_abs)
    if row.probability_memory_score != expected_memory_score:
        raise ValueError(
            "probability_memory_score must match average_probability_delta_abs",
        )
    if row.average_depth == ZERO and row.market_depth_score != ZERO:
        raise ValueError("market_depth_score must be zero when average_depth is zero")
    if row.source_count == ZERO and row.source_diversity_score != ZERO:
        raise ValueError("source_diversity_score must be zero when source_count is zero")

    status_reasons = {
        f"market_depth_probability_memory_{value}" for value in STATUSES
    }
    expected_status_reason = f"market_depth_probability_memory_{row.status}"
    if set(row.reason_codes).intersection(status_reasons) != {expected_status_reason}:
        raise ValueError("status must match reason_codes")
    _require_one_reason(
        row.reason_codes,
        ("probability_memory_stable", "probability_memory_watch", "probability_memory_unstable"),
        "probability memory reason",
    )
    _require_one_reason(
        row.reason_codes,
        ("sufficient_depth", "insufficient_depth"),
        "depth reason",
    )
    _require_one_reason(
        row.reason_codes,
        ("sufficient_source_count", "insufficient_source_count"),
        "source count reason",
    )
    if "stale_probability_memory" in row.reason_codes and row.status != "block":
        raise ValueError("stale_probability_memory requires block status")


def _validate_row(
    row: ResearchMarketDepthProbabilityMemoryScorecardRow,
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> None:
    _validate_row_shape(row)
    _revalidate_config(config)
    expected_market_depth_score = _capped_ratio(
        row.average_depth,
        config.target_depth,
    )
    if row.market_depth_score != expected_market_depth_score:
        raise ValueError("market_depth_score must match average_depth and config")
    expected_source_diversity_score = _capped_ratio(
        row.source_count,
        config.min_source_count,
    )
    if row.source_diversity_score != expected_source_diversity_score:
        raise ValueError("source_diversity_score must match source_count and config")
    expected_score = _weighted_score(
        probability_memory_score=row.probability_memory_score,
        market_depth_score=expected_market_depth_score,
        source_diversity_score=expected_source_diversity_score,
        config=config,
    )
    if row.score != expected_score:
        raise ValueError("score must match component scores and config")
    expected_status = _row_status(
        score=expected_score,
        latest_memory_age_seconds=row.latest_memory_age_seconds,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match score, memory age, and config")
    input_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code.startswith("input_")
    )
    expected_reason_codes = _row_reason_codes_from_input_reasons(
        input_reason_codes,
        status=expected_status,
        probability_memory_score=row.probability_memory_score,
        average_depth=row.average_depth,
        source_count=row.source_count,
        latest_memory_age_seconds=row.latest_memory_age_seconds,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row values and config")


def _validate_report(
    report: ResearchMarketDepthProbabilityMemoryScorecardReport,
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> None:
    if type(report) is not ResearchMarketDepthProbabilityMemoryScorecardReport:
        raise ValueError(
            "report must be a "
            "ResearchMarketDepthProbabilityMemoryScorecardReport",
        )
    _revalidate_config(config)
    if config is not report.config:
        raise ValueError("config must be the exact report config")
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if report.generated_at.tzinfo is not UTC or report.generated_at != normalized_generated_at:
        raise ValueError("generated_at must be stored in UTC")
    if (
        type(report.config_version) is not str
        or report.config_version
        != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_MEMORY_SCORECARD_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    if report.config_version != config.config_version:
        raise ValueError("config_version must match config")
    for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
        _require_canonical_stored_decimal(
            field_name,
            getattr(report, field_name),
            _require_nonnegative_whole_decimal,
        )
    if report.average_score is not None:
        _require_canonical_stored_decimal(
            "average_score",
            report.average_score,
            _require_ratio_decimal,
        )
    _require_status("status", report.status)
    normalized_reasons = _normalize_reason_codes(
        "reason_codes",
        report.reason_codes,
        allow_empty=False,
    )
    if type(report.reason_codes) is not tuple or report.reason_codes != normalized_reasons:
        raise ValueError("reason_codes must be a canonical tuple")
    _require_hard_flags("report", report)

    rows = report.rows
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized_rows = _normalize_rows(rows, config=config)
    if rows != normalized_rows:
        raise ValueError("rows must be in canonical sequence")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    with localcontext(DECIMAL_CONTEXT):
        status_count = _quantize(
            report.pass_count + report.watch_count + report.block_count,
        )
    if report.row_count != status_count:
        raise ValueError("status counts must match row_count")
    expected_average = (
        _average_decimal(tuple(row.score for row in rows)) if rows else None
    )
    if report.average_score != expected_average:
        raise ValueError("average_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: object,
) -> tuple[ResearchMarketDepthProbabilityMemoryScorecardObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchMarketDepthProbabilityMemoryScorecardObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketDepthProbabilityMemoryScorecardObservation",
            )
        _revalidate_observation(item)
    return normalized


def _normalize_rows(
    rows: object,
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> tuple[ResearchMarketDepthProbabilityMemoryScorecardRow, ...]:
    _revalidate_config(config)
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_markets: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketDepthProbabilityMemoryScorecardRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketDepthProbabilityMemoryScorecardRow",
            )
        _revalidate_row(row, config=config)
        if row.market_digest in seen_markets:
            raise ValueError("rows must contain unique market_digest values")
        seen_markets.add(row.market_digest)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchMarketDepthProbabilityMemoryScorecardRow,
) -> tuple[int, Decimal, str, str]:
    return (STATUS_RANK[row.status], row.score, row.market_digest, row.candidate_digest)


def _revalidate_config(
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> None:
    if type(config) is not ResearchMarketDepthProbabilityMemoryScorecardConfig:
        raise ValueError(
            "config must be a "
            "ResearchMarketDepthProbabilityMemoryScorecardConfig",
        )
    rebuilt = ResearchMarketDepthProbabilityMemoryScorecardConfig(
        config_version=config.config_version,
        target_depth=config.target_depth,
        min_source_count=config.min_source_count,
        pass_score_min=config.pass_score_min,
        watch_score_min=config.watch_score_min,
        stale_memory_age_seconds=config.stale_memory_age_seconds,
        probability_memory_weight=config.probability_memory_weight,
        market_depth_weight=config.market_depth_weight,
        source_diversity_weight=config.source_diversity_weight,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )
    decimal_fields = (
        "target_depth",
        "min_source_count",
        "pass_score_min",
        "watch_score_min",
        "stale_memory_age_seconds",
        "probability_memory_weight",
        "market_depth_weight",
        "source_diversity_weight",
    )
    if rebuilt != config or any(
        getattr(rebuilt, field_name).as_tuple()
        != getattr(config, field_name).as_tuple()
        for field_name in decimal_fields
    ):
        raise ValueError("config fields must be canonical")


def _revalidate_observation(
    item: ResearchMarketDepthProbabilityMemoryScorecardObservation,
) -> None:
    rebuilt = ResearchMarketDepthProbabilityMemoryScorecardObservation(
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        source_reference=item.source_reference,
        probability=item.probability,
        previous_probability=item.previous_probability,
        bid_depth=item.bid_depth,
        ask_depth=item.ask_depth,
        source_count=item.source_count,
        observed_at=item.observed_at,
        reason_codes=item.reason_codes,
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )
    decimal_fields = (
        "probability",
        "previous_probability",
        "bid_depth",
        "ask_depth",
        "source_count",
    )
    if (
        rebuilt != item
        or item.observed_at.tzinfo is not UTC
        or any(
            getattr(rebuilt, field_name).as_tuple()
            != getattr(item, field_name).as_tuple()
            for field_name in decimal_fields
        )
    ):
        raise ValueError("observation fields must be canonical")


def _revalidate_row(
    row: ResearchMarketDepthProbabilityMemoryScorecardRow,
    *,
    config: ResearchMarketDepthProbabilityMemoryScorecardConfig,
) -> None:
    rebuilt = ResearchMarketDepthProbabilityMemoryScorecardRow(
        candidate_digest=row.candidate_digest,
        market_digest=row.market_digest,
        observation_count=row.observation_count,
        latest_memory_age_seconds=row.latest_memory_age_seconds,
        average_probability=row.average_probability,
        average_probability_delta_abs=row.average_probability_delta_abs,
        probability_memory_score=row.probability_memory_score,
        average_depth=row.average_depth,
        market_depth_score=row.market_depth_score,
        source_count=row.source_count,
        source_diversity_score=row.source_diversity_score,
        score=row.score,
        status=row.status,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    if rebuilt != row or any(
        left.as_tuple() != right.as_tuple()
        for left, right in zip(rebuilt.decimals, row.decimals, strict=True)
    ):
        raise ValueError("row fields must be canonical")
    _validate_row(rebuilt, config=config)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_reason_code(field_name, value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must contain unique values")
    return tuple(sorted(normalized))


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value or len(value) > 128:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value[0] == "_":
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if not all("a" <= char <= "z" or "0" <= char <= "9" or char == "_" for char in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return value


def _require_one_reason(
    reason_codes: tuple[str, ...],
    choices: tuple[str, ...],
    label: str,
) -> None:
    if len(set(reason_codes).intersection(choices)) != 1:
        raise ValueError(f"reason_codes must contain exactly one {label}")


def _status_count(
    rows: tuple[ResearchMarketDepthProbabilityMemoryScorecardRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("cannot average empty values")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, _quantize(numerator / denominator))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = Decimal(
        delta.days * 86400 * 1000000
        + delta.seconds * 1000000
        + delta.microseconds,
    )
    if total_microseconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("public decimal values must be exactly Decimal and finite")
    return format(ZERO if value.is_zero() else value, "f")


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _private_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_validation_digest(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in HEX_CHARS for char in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a prefixed SHA-256 digest")
    _require_validation_digest(field_name, value[7:])
    return value


def _require_private_text(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or value != value.strip()
        or "\0" in value
        or len(value) > 4096
    ):
        raise ValueError(f"{field_name} must be non-empty private text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_exact_record(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_canonical_stored_decimal(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal:
    normalized = validator(field_name, value)
    if type(value) is not Decimal or value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{field_name} must be stored with six decimal places")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = _quantize(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be quantizable to six places") from exc
    return ZERO if normalized.is_zero() else normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must have a valid UTC offset") from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    try:
        return value.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} must have a valid UTC offset") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
