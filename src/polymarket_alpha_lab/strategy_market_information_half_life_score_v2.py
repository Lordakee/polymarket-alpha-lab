"""Readonly Decimal scorecard for market information half-life quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_STRATEGY_MARKET_INFORMATION_HALF_LIFE_SCORE_V2_CONFIG_VERSION = (
    "strategy-market-information-half-life-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SCORE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "market_information_half_life_pass",
    "market_information_half_life_watch",
    "market_information_half_life_blocked",
    "information_decay_stable",
    "information_decay_watch",
    "information_decay_fast",
    "source_recency_fresh",
    "source_recency_watch",
    "source_recency_stale",
    "source_diversity_strong",
    "source_diversity_watch",
    "source_diversity_weak",
    "evidence_quality_strong",
    "evidence_quality_watch",
    "evidence_quality_weak",
    "consensus_stability_strong",
    "consensus_stability_watch",
    "consensus_stability_weak",
)
REPORT_REASON_CODES = (
    "market_information_half_life_score_passed",
    "market_information_half_life_score_watch_rows",
    "market_information_half_life_score_blocked_rows",
    "market_information_half_life_score_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_MARKET_INFORMATION_HALF_LIFE_SCORE_V2_CONFIG_VERSION",
    "StrategyMarketInformationHalfLifeScoreV2Config",
    "StrategyMarketInformationHalfLifeScoreV2Input",
    "StrategyMarketInformationHalfLifeScoreV2Row",
    "StrategyMarketInformationHalfLifeScoreV2Report",
    "build_strategy_market_information_half_life_score_v2",
)


@dataclass(frozen=True)
class StrategyMarketInformationHalfLifeScoreV2Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_INFORMATION_HALF_LIFE_SCORE_V2_CONFIG_VERSION
    stable_half_life_reference_hours: Decimal = Decimal("96")
    information_decay_weight: Decimal = Decimal("0.250000")
    source_recency_weight: Decimal = Decimal("0.250000")
    source_diversity_weight: Decimal = Decimal("0.150000")
    evidence_quality_weight: Decimal = Decimal("0.200000")
    consensus_stability_weight: Decimal = Decimal("0.150000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    stale_source_recency_floor: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "stable_half_life_reference_hours",
            _normalize_positive_decimal(
                "stable_half_life_reference_hours",
                self.stable_half_life_reference_hours,
            ),
        )
        for field_name in (
            "information_decay_weight",
            "source_recency_weight",
            "source_diversity_weight",
            "evidence_quality_weight",
            "consensus_stability_weight",
            "pass_score_floor",
            "watch_score_floor",
            "stale_source_recency_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Config", self)
        _reject_unsafe_public_payload(
            "StrategyMarketInformationHalfLifeScoreV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyMarketInformationHalfLifeScoreV2Input:
    market_id: str
    market_slug: str
    information_half_life_hours: Decimal
    source_age_hours: Decimal
    source_diversity_score: Decimal
    evidence_quality_score: Decimal
    consensus_stability_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_non_empty_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_non_empty_string("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "information_half_life_hours",
            _normalize_positive_decimal(
                "information_half_life_hours",
                self.information_half_life_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_decimal("source_age_hours", self.source_age_hours),
        )
        for field_name in (
            "source_diversity_score",
            "evidence_quality_score",
            "consensus_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Input", self)
        _reject_unsafe_public_payload(
            "StrategyMarketInformationHalfLifeScoreV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyMarketInformationHalfLifeScoreV2Row:
    rank: Decimal
    market_id: str
    market_slug: str
    information_half_life_hours: Decimal
    source_age_hours: Decimal
    source_diversity_score: Decimal
    evidence_quality_score: Decimal
    consensus_stability_score: Decimal
    information_decay_score: Decimal
    source_recency_score: Decimal
    source_recency_penalty: Decimal
    market_information_half_life_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "market_id",
            _require_non_empty_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_non_empty_string("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "information_half_life_hours",
            _normalize_positive_decimal(
                "information_half_life_hours",
                self.information_half_life_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_decimal("source_age_hours", self.source_age_hours),
        )
        for field_name in (
            "source_diversity_score",
            "evidence_quality_score",
            "consensus_stability_score",
            "information_decay_score",
            "source_recency_score",
            "source_recency_penalty",
            "market_information_half_life_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_score_status("score_status", self.score_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Row", self)
        _reject_unsafe_public_payload(
            "StrategyMarketInformationHalfLifeScoreV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyMarketInformationHalfLifeScoreV2Report:
    generated_at: datetime
    config_version: str
    score_status: str
    market_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    average_half_life_score: Decimal
    top_half_life_score: Decimal
    bottom_half_life_score: Decimal
    rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_score_status("score_status", self.score_status)
        for field_name in (
            "market_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_half_life_score",
            "top_half_life_score",
            "bottom_half_life_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Report", self)
        _reject_unsafe_public_payload(
            "StrategyMarketInformationHalfLifeScoreV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyMarketInformationHalfLifeScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_market_information_half_life_score_v2(
    market_observations: object,
    *,
    config: StrategyMarketInformationHalfLifeScoreV2Config | None = None,
    generated_at: datetime,
) -> StrategyMarketInformationHalfLifeScoreV2Report:
    if config is None:
        config = StrategyMarketInformationHalfLifeScoreV2Config()
    if type(config) is not StrategyMarketInformationHalfLifeScoreV2Config:
        raise ValueError(
            "config must be a StrategyMarketInformationHalfLifeScoreV2Config",
        )
    _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_market_observations(market_observations)

    rows = tuple(
        _row_for_observation(rank=index, observation=item, config=config)
        for index, item in enumerate(_sorted_observations(observations, config), start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "score_status": status,
        "market_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_market_count": _status_count(rows, "pass"),
        "watch_market_count": _status_count(rows, "watch"),
        "blocked_market_count": _status_count(rows, "blocked"),
        "average_half_life_score": _average_score(rows),
        "top_half_life_score": _top_score(rows),
        "bottom_half_life_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyMarketInformationHalfLifeScoreV2Report(**values)


def _sorted_observations(
    observations: tuple[StrategyMarketInformationHalfLifeScoreV2Input, ...],
    config: StrategyMarketInformationHalfLifeScoreV2Config,
) -> tuple[StrategyMarketInformationHalfLifeScoreV2Input, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                -_score_for_observation(item, config),
                item.market_id,
                item.market_slug,
            ),
        ),
    )


def _row_for_observation(
    *,
    rank: int,
    observation: StrategyMarketInformationHalfLifeScoreV2Input,
    config: StrategyMarketInformationHalfLifeScoreV2Config,
) -> StrategyMarketInformationHalfLifeScoreV2Row:
    information_decay_score = _information_decay_score(observation, config)
    source_recency_score = _source_recency_score(observation)
    source_recency_penalty = _clamp_ratio(ONE - source_recency_score)
    score = _score_for_observation(observation, config)
    status = _score_status(score, source_recency_score, config)
    return StrategyMarketInformationHalfLifeScoreV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        market_id=observation.market_id,
        market_slug=observation.market_slug,
        information_half_life_hours=observation.information_half_life_hours,
        source_age_hours=observation.source_age_hours,
        source_diversity_score=observation.source_diversity_score,
        evidence_quality_score=observation.evidence_quality_score,
        consensus_stability_score=observation.consensus_stability_score,
        information_decay_score=information_decay_score,
        source_recency_score=source_recency_score,
        source_recency_penalty=source_recency_penalty,
        market_information_half_life_score=score,
        score_status=status,
        reason_codes=_row_reason_codes(
            information_decay_score=information_decay_score,
            source_recency_score=source_recency_score,
            observation=observation,
            status=status,
        ),
    )


def _score_for_observation(
    observation: StrategyMarketInformationHalfLifeScoreV2Input,
    config: StrategyMarketInformationHalfLifeScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _information_decay_score(observation, config) * config.information_decay_weight
            + _source_recency_score(observation) * config.source_recency_weight
            + observation.source_diversity_score * config.source_diversity_weight
            + observation.evidence_quality_score * config.evidence_quality_weight
            + observation.consensus_stability_score * config.consensus_stability_weight
        )
        return _clamp_ratio(score)


def _information_decay_score(
    observation: StrategyMarketInformationHalfLifeScoreV2Input,
    config: StrategyMarketInformationHalfLifeScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            observation.information_half_life_hours
            / config.stable_half_life_reference_hours,
        )


def _source_recency_score(
    observation: StrategyMarketInformationHalfLifeScoreV2Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        denominator = observation.information_half_life_hours + observation.source_age_hours
        return _clamp_ratio(observation.information_half_life_hours / denominator)


def _score_status(
    score: Decimal,
    source_recency_score: Decimal,
    config: StrategyMarketInformationHalfLifeScoreV2Config,
) -> str:
    if source_recency_score < config.stale_source_recency_floor:
        return "blocked"
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _report_status(rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.score_status == "blocked" for row in rows):
        return "blocked"
    if any(row.score_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    information_decay_score: Decimal,
    source_recency_score: Decimal,
    observation: StrategyMarketInformationHalfLifeScoreV2Input,
    status: str,
) -> tuple[str, ...]:
    return (
        f"market_information_half_life_{status}",
        _tier_reason(
            information_decay_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.250000"),
            strong_reason="information_decay_stable",
            watch_reason="information_decay_watch",
            weak_reason="information_decay_fast",
        ),
        _tier_reason(
            source_recency_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.200000"),
            strong_reason="source_recency_fresh",
            watch_reason="source_recency_watch",
            weak_reason="source_recency_stale",
        ),
        _tier_reason(
            observation.source_diversity_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_diversity_strong",
            watch_reason="source_diversity_watch",
            weak_reason="source_diversity_weak",
        ),
        _tier_reason(
            observation.evidence_quality_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="evidence_quality_strong",
            watch_reason="evidence_quality_watch",
            weak_reason="evidence_quality_weak",
        ),
        _tier_reason(
            observation.consensus_stability_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="consensus_stability_strong",
            watch_reason="consensus_stability_watch",
            weak_reason="consensus_stability_weak",
        ),
    )


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _report_reason_codes(
    rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("market_information_half_life_score_empty",)
    reasons: list[str] = []
    if any(row.score_status == "blocked" for row in rows):
        reasons.append("market_information_half_life_score_blocked_rows")
    if any(row.score_status == "watch" for row in rows):
        reasons.append("market_information_half_life_score_watch_rows")
    if not reasons and status == "pass":
        reasons.append("market_information_half_life_score_passed")
    return tuple(reasons)


def _status_count(
    rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.score_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.market_information_half_life_score for row in rows) / Decimal(len(rows)),
        )


def _top_score(rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.market_information_half_life_score for row in rows)


def _bottom_score(rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.market_information_half_life_score for row in rows)


def _normalize_market_observations(
    value: object,
) -> tuple[StrategyMarketInformationHalfLifeScoreV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("market_observations must be an iterable")
    observations = tuple(value)
    for item in observations:
        if type(item) is not StrategyMarketInformationHalfLifeScoreV2Input:
            raise ValueError(
                "market observation items must be StrategyMarketInformationHalfLifeScoreV2Input",
            )
        _require_hard_flags("StrategyMarketInformationHalfLifeScoreV2Input", item)
    keys = tuple((item.market_id, item.market_slug) for item in observations)
    if len(set(keys)) != len(keys):
        raise ValueError("market observation items must not contain duplicate market keys")
    return observations


def _normalize_rows(value: object) -> tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyMarketInformationHalfLifeScoreV2Row:
            raise ValueError(
                "rows must contain StrategyMarketInformationHalfLifeScoreV2Row",
            )
    return value


def _validate_config(config: StrategyMarketInformationHalfLifeScoreV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.information_decay_weight
            + config.source_recency_weight
            + config.source_diversity_weight
            + config.evidence_quality_weight
            + config.consensus_stability_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_row_consistency(row: StrategyMarketInformationHalfLifeScoreV2Row) -> None:
    if row.source_recency_penalty != _clamp_ratio(ONE - row.source_recency_score):
        raise ValueError("source_recency_penalty must match source_recency_score")


def _validate_report_consistency(
    report: StrategyMarketInformationHalfLifeScoreV2Report,
) -> None:
    rows = report.rows
    if report.market_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("market_count must match rows")
    if (
        report.pass_market_count != _status_count(rows, "pass")
        or report.watch_market_count != _status_count(rows, "watch")
        or report.blocked_market_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_market_count
        + report.watch_market_count
        + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("status counts must sum to market_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.score_status != expected_status:
        raise ValueError("score_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.score_status):
        raise ValueError("reason_codes must match score_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_half_life_score != _average_score(rows):
        raise ValueError("average_half_life_score must match rows")
    if report.top_half_life_score != _top_score(rows):
        raise ValueError("top_half_life_score must match rows")
    if report.bottom_half_life_score != _bottom_score(rows):
        raise ValueError("bottom_half_life_score must match rows")


def _validate_rows_sorted(rows: tuple[StrategyMarketInformationHalfLifeScoreV2Row, ...]) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.market_information_half_life_score,
                row.market_id,
                row.market_slug,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_score_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
