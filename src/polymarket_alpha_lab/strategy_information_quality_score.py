from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext, Context
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_INFORMATION_QUALITY_SCORE_CONFIG_VERSION",
    "StrategyInformationQualityScoreConfig",
    "StrategyInformationQualityScoreInput",
    "StrategyInformationQualityScoreResult",
    "build_strategy_information_quality_score",
    "strategy_information_quality_score_payload",
)


DEFAULT_STRATEGY_INFORMATION_QUALITY_SCORE_CONFIG_VERSION = (
    "strategy-information-quality-score-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "blocked")
READY_REASON_CODE = "information_quality_ready"


@dataclass(frozen=True)
class StrategyInformationQualityScoreConfig:
    config_version: str = DEFAULT_STRATEGY_INFORMATION_QUALITY_SCORE_CONFIG_VERSION
    min_watch_source_count: Decimal = Decimal("2")
    min_pass_source_count: Decimal = Decimal("3")
    max_pass_freshness_minutes: Decimal = Decimal("30")
    max_watch_freshness_minutes: Decimal = Decimal("60")
    min_watch_source_reliability_score: Decimal = Decimal("0.600000")
    min_pass_source_reliability_score: Decimal = Decimal("0.800000")
    min_watch_source_diversity_score: Decimal = Decimal("0.300000")
    min_pass_source_diversity_score: Decimal = Decimal("0.600000")
    max_pass_evidence_conflict_score: Decimal = Decimal("0.100000")
    max_watch_evidence_conflict_score: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyInformationQualityScoreConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyInformationQualityScoreConfig:
            raise ValueError("config must be exactly StrategyInformationQualityScoreConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_watch_source_count",
            "min_pass_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_freshness_minutes",
            "max_watch_freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_watch_source_reliability_score",
            "min_pass_source_reliability_score",
            "min_watch_source_diversity_score",
            "min_pass_source_diversity_score",
            "max_pass_evidence_conflict_score",
            "max_watch_evidence_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.min_watch_source_count > self.min_pass_source_count:
            raise ValueError(
                "min_watch_source_count must be less than or equal to min_pass_source_count",
            )
        if self.max_pass_freshness_minutes > self.max_watch_freshness_minutes:
            raise ValueError(
                "max_pass_freshness_minutes must be less than or equal to "
                "max_watch_freshness_minutes",
            )
        if (
            self.min_watch_source_reliability_score
            > self.min_pass_source_reliability_score
        ):
            raise ValueError(
                "min_watch_source_reliability_score must be less than or equal to "
                "min_pass_source_reliability_score",
            )
        if self.min_watch_source_diversity_score > self.min_pass_source_diversity_score:
            raise ValueError(
                "min_watch_source_diversity_score must be less than or equal to "
                "min_pass_source_diversity_score",
            )
        if self.max_pass_evidence_conflict_score > self.max_watch_evidence_conflict_score:
            raise ValueError(
                "max_pass_evidence_conflict_score must be less than or equal to "
                "max_watch_evidence_conflict_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyInformationQualityScoreInput:
    source_count: Decimal
    freshness_minutes: Decimal
    source_reliability_score: Decimal
    source_diversity_score: Decimal
    evidence_conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyInformationQualityScoreInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyInformationQualityScoreInput:
            raise ValueError("input must be exactly StrategyInformationQualityScoreInput")
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_integral_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "freshness_minutes",
            _require_nonnegative_decimal("freshness_minutes", self.freshness_minutes),
        )
        for field_name in (
            "source_reliability_score",
            "source_diversity_score",
            "evidence_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyInformationQualityScoreResult:
    source_count: Decimal
    freshness_minutes: Decimal
    source_reliability_score: Decimal
    source_diversity_score: Decimal
    evidence_conflict_score: Decimal
    component_scores: tuple[tuple[str, Decimal], ...]
    information_quality_score: Decimal
    information_quality_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyInformationQualityScoreResult does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyInformationQualityScoreResult:
            raise ValueError("result must be exactly StrategyInformationQualityScoreResult")
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_integral_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "freshness_minutes",
            _require_nonnegative_decimal("freshness_minutes", self.freshness_minutes),
        )
        for field_name in (
            "source_reliability_score",
            "source_diversity_score",
            "evidence_conflict_score",
            "information_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "component_scores",
            _normalize_component_scores(self.component_scores),
        )
        _require_status("information_quality_status", self.information_quality_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes is required")
        _require_hard_flags("result", self)


def build_strategy_information_quality_score(
    source: StrategyInformationQualityScoreInput,
    *,
    config: StrategyInformationQualityScoreConfig,
) -> StrategyInformationQualityScoreResult:
    if type(config) is not StrategyInformationQualityScoreConfig:
        raise ValueError("config must be exactly StrategyInformationQualityScoreConfig")
    if type(source) is not StrategyInformationQualityScoreInput:
        raise ValueError("source must be exactly StrategyInformationQualityScoreInput")
    _require_hard_flags("config", config)
    _require_hard_flags("input", source)
    reason_codes = _reason_codes(source, config)
    component_scores = _component_scores(source, config)
    return StrategyInformationQualityScoreResult(
        source_count=source.source_count,
        freshness_minutes=source.freshness_minutes,
        source_reliability_score=source.source_reliability_score,
        source_diversity_score=source.source_diversity_score,
        evidence_conflict_score=source.evidence_conflict_score,
        component_scores=component_scores,
        information_quality_score=_average(score for _name, score in component_scores),
        information_quality_status=_status(reason_codes),
        reason_codes=reason_codes,
    )


def strategy_information_quality_score_payload(
    result: StrategyInformationQualityScoreResult,
) -> dict[str, Any]:
    if type(result) is not StrategyInformationQualityScoreResult:
        raise ValueError("result must be exactly StrategyInformationQualityScoreResult")
    return _payload_value(result)


def _reason_codes(
    source: StrategyInformationQualityScoreInput,
    config: StrategyInformationQualityScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if source.source_count < config.min_watch_source_count:
        codes.append("insufficient_source_count")
    elif source.source_count < config.min_pass_source_count:
        codes.append("low_source_count_watch")
    if source.freshness_minutes > config.max_watch_freshness_minutes:
        codes.append("stale_evidence_blocked")
    elif source.freshness_minutes > config.max_pass_freshness_minutes:
        codes.append("stale_evidence_watch")
    if source.source_reliability_score < config.min_watch_source_reliability_score:
        codes.append("low_source_reliability_blocked")
    elif source.source_reliability_score < config.min_pass_source_reliability_score:
        codes.append("low_source_reliability_watch")
    if source.source_diversity_score < config.min_watch_source_diversity_score:
        codes.append("low_source_diversity_blocked")
    elif source.source_diversity_score < config.min_pass_source_diversity_score:
        codes.append("low_source_diversity_watch")
    if source.evidence_conflict_score > config.max_watch_evidence_conflict_score:
        codes.append("evidence_conflict_blocked")
    elif source.evidence_conflict_score > config.max_pass_evidence_conflict_score:
        codes.append("evidence_conflict_watch")
    if not codes:
        codes.append(READY_REASON_CODE)
    return tuple(sorted(dict.fromkeys(codes)))


def _status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_blocked") or code == "insufficient_source_count" for code in reason_codes):
        return "blocked"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _component_scores(
    source: StrategyInformationQualityScoreInput,
    config: StrategyInformationQualityScoreConfig,
) -> tuple[tuple[str, Decimal], ...]:
    return (
        ("evidence_conflict_score", ONE - source.evidence_conflict_score),
        (
            "freshness_minutes",
            _freshness_component(
                source.freshness_minutes,
                config.max_pass_freshness_minutes,
                config.max_watch_freshness_minutes,
            ),
        ),
        (
            "source_count",
            _ratio_capped(source.source_count, config.min_watch_source_count),
        ),
        ("source_diversity_score", source.source_diversity_score),
        ("source_reliability_score", source.source_reliability_score),
    )


def _freshness_component(
    freshness_minutes: Decimal,
    max_pass_minutes: Decimal,
    max_watch_minutes: Decimal,
) -> Decimal:
    if freshness_minutes <= max_pass_minutes:
        return ONE
    if freshness_minutes >= max_watch_minutes:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six_places(
            ONE - ((freshness_minutes - max_pass_minutes) / (max_watch_minutes - max_pass_minutes)),
        )


def _ratio_capped(value: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ratio = value / denominator
    if ratio > ONE:
        return ONE
    return _six_places(ratio)


def _average(values: object) -> Decimal:
    values_tuple = tuple(values)
    if not values_tuple:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six_places(sum(values_tuple, ZERO) / Decimal(len(values_tuple)))


def _normalize_component_scores(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("component_scores must be a tuple")
    rows: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("component_scores must contain pairs")
        name, score = item
        _require_canonical_string("component_score_name", name)
        if previous is not None and previous > name:
            raise ValueError("component_scores must be sorted")
        rows.append((name, _require_probability("component_score", score)))
        previous = name
    if not rows:
        raise ValueError("component_scores is required")
    return tuple(rows)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    return value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    _require_integral_decimal(field_name, decimal_value)
    return decimal_value


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    _require_integral_decimal(field_name, decimal_value)
    return decimal_value


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six_places(value)


def _six_places(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
