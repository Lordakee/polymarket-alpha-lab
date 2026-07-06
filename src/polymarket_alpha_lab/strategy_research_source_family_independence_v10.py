"""Pure read-only research source family independence v10 evaluator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


CONFIG_VERSION = "strategy-research-source-family-independence-v10"

DECIMAL_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

FAMILY_COUNT_WEIGHT = Decimal("0.350000")
CONCENTRATION_WEIGHT = Decimal("0.200000")
DIRECT_SOURCE_WEIGHT = Decimal("0.200000")
CONTRADICTION_WEIGHT = Decimal("0.150000")
RECENCY_WEIGHT = Decimal("0.100000")

INDEPENDENT_SCORE_FLOOR = Decimal("0.800000")
WATCH_SCORE_FLOOR = Decimal("0.600000")
BALANCED_CONCENTRATION_CEILING = Decimal("0.500000")
WATCH_CONCENTRATION_CEILING = Decimal("0.700000")
STRONG_DIRECT_SHARE_FLOOR = Decimal("0.500000")
ADEQUATE_DIRECT_SHARE_FLOOR = Decimal("0.250000")
LOW_CONTRADICTION_CEILING = Decimal("0.100000")
MODERATE_CONTRADICTION_CEILING = Decimal("0.250000")
BLOCKING_CONTRADICTION_FLOOR = Decimal("0.500000")
CURRENT_RECENCY_FLOOR = Decimal("0.750000")
PARTIAL_RECENCY_FLOOR = Decimal("0.500000")

INDEPENDENCE_STATUSES = ("independent", "watch", "thin", "blocked")
RECOMMENDATIONS = (
    "use_packet",
    "add_confirming_direct_source",
    "expand_source_families",
    "block_until_family_quorum",
)
PAYLOAD_FIELDS = (
    "config_version",
    "packet_id",
    "market_slug",
    "source_count",
    "source_family_count",
    "required_family_count",
    "largest_source_family_count",
    "direct_source_count",
    "contradicting_source_count",
    "recent_source_count",
    "family_count_score",
    "repeated_source_concentration",
    "concentration_independence_score",
    "direct_source_share",
    "contradiction_rate",
    "contradiction_quality_score",
    "recency_coverage",
    "independence_score",
    "independence_status",
    "recommendation",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ResearchSourceFamilyIndependenceV10Input:
    packet_id: str
    market_slug: str
    source_count: Decimal
    source_family_count: Decimal
    required_family_count: Decimal
    largest_source_family_count: Decimal
    direct_source_count: Decimal
    contradicting_source_count: Decimal
    recent_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "source_count",
            "source_family_count",
            "largest_source_family_count",
            "direct_source_count",
            "contradicting_source_count",
            "recent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_family_count",
            _normalize_positive_count("required_family_count", self.required_family_count),
        )
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceFamilyIndependenceV10Report:
    packet_id: str
    market_slug: str
    source_count: Decimal
    source_family_count: Decimal
    required_family_count: Decimal
    largest_source_family_count: Decimal
    direct_source_count: Decimal
    contradicting_source_count: Decimal
    recent_source_count: Decimal
    family_count_score: Decimal
    repeated_source_concentration: Decimal
    concentration_independence_score: Decimal
    direct_source_share: Decimal
    contradiction_rate: Decimal
    contradiction_quality_score: Decimal
    recency_coverage: Decimal
    independence_score: Decimal
    independence_status: str
    recommendation: str
    reason_codes: tuple[str, ...]
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_count",
            "source_family_count",
            "largest_source_family_count",
            "direct_source_count",
            "contradicting_source_count",
            "recent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_family_count",
            _normalize_positive_count("required_family_count", self.required_family_count),
        )
        for field_name in (
            "family_count_score",
            "repeated_source_concentration",
            "concentration_independence_score",
            "direct_source_share",
            "contradiction_rate",
            "contradiction_quality_score",
            "recency_coverage",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independence_status",
            _require_member(
                "independence_status",
                self.independence_status,
                INDEPENDENCE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "recommendation",
            _require_member("recommendation", self.recommendation, RECOMMENDATIONS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_source_family_independence_v10_payload(self)


@dataclass(frozen=True)
class _Metrics:
    family_count_score: Decimal
    repeated_source_concentration: Decimal
    concentration_independence_score: Decimal
    direct_source_share: Decimal
    contradiction_rate: Decimal
    contradiction_quality_score: Decimal
    recency_coverage: Decimal
    independence_score: Decimal


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def strategy_research_source_family_independence_v10(
    value: ResearchSourceFamilyIndependenceV10Input,
) -> ResearchSourceFamilyIndependenceV10Report:
    if type(value) is not ResearchSourceFamilyIndependenceV10Input:
        raise ValueError("value must be a ResearchSourceFamilyIndependenceV10Input")
    _require_hard_flags("input", value)
    metrics = _metrics(value)
    status = _independence_status(value, metrics)
    recommendation = _recommendation(status)
    return ResearchSourceFamilyIndependenceV10Report(
        packet_id=value.packet_id,
        market_slug=value.market_slug,
        source_count=value.source_count,
        source_family_count=value.source_family_count,
        required_family_count=value.required_family_count,
        largest_source_family_count=value.largest_source_family_count,
        direct_source_count=value.direct_source_count,
        contradicting_source_count=value.contradicting_source_count,
        recent_source_count=value.recent_source_count,
        family_count_score=metrics.family_count_score,
        repeated_source_concentration=metrics.repeated_source_concentration,
        concentration_independence_score=metrics.concentration_independence_score,
        direct_source_share=metrics.direct_source_share,
        contradiction_rate=metrics.contradiction_rate,
        contradiction_quality_score=metrics.contradiction_quality_score,
        recency_coverage=metrics.recency_coverage,
        independence_score=metrics.independence_score,
        independence_status=status,
        recommendation=recommendation,
        reason_codes=_reason_codes(value, metrics, status),
    )


def evaluate_strategy_research_source_family_independence_v10(
    value: ResearchSourceFamilyIndependenceV10Input,
) -> ResearchSourceFamilyIndependenceV10Report:
    return strategy_research_source_family_independence_v10(value)


def strategy_research_source_family_independence_v10_payload(
    report: ResearchSourceFamilyIndependenceV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceFamilyIndependenceV10Report:
        _require_hard_flags("report", report)
        payload: object = _report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _validate_payload_fields(report)
        payload = report
    else:
        raise ValueError("report must be a ResearchSourceFamilyIndependenceV10Report")

    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _validate_payload_fields(ready)
    return ready


def _metrics(value: ResearchSourceFamilyIndependenceV10Input) -> _Metrics:
    repeated_source_concentration = _share(
        value.largest_source_family_count,
        value.source_count,
    )
    direct_source_share = _share(value.direct_source_count, value.source_count)
    contradiction_rate = _share(value.contradicting_source_count, value.source_count)
    recency_coverage = _share(value.recent_source_count, value.source_count)
    family_count_score = _capped_ratio(
        value.source_family_count,
        value.required_family_count,
    )
    if value.source_count == ZERO:
        concentration_independence_score = ZERO
        contradiction_quality_score = ZERO
    else:
        with localcontext(DECIMAL_CONTEXT):
            concentration_independence_score = (
                ONE - repeated_source_concentration
            ).quantize(DECIMAL_QUANTUM)
            contradiction_quality_score = (ONE - contradiction_rate).quantize(
                DECIMAL_QUANTUM,
            )
    independence_score = _independence_score(
        family_count_score=family_count_score,
        concentration_independence_score=concentration_independence_score,
        direct_source_share=direct_source_share,
        contradiction_quality_score=contradiction_quality_score,
        recency_coverage=recency_coverage,
    )
    return _Metrics(
        family_count_score=family_count_score,
        repeated_source_concentration=repeated_source_concentration,
        concentration_independence_score=concentration_independence_score,
        direct_source_share=direct_source_share,
        contradiction_rate=contradiction_rate,
        contradiction_quality_score=contradiction_quality_score,
        recency_coverage=recency_coverage,
        independence_score=independence_score,
    )


def _independence_score(
    *,
    family_count_score: Decimal,
    concentration_independence_score: Decimal,
    direct_source_share: Decimal,
    contradiction_quality_score: Decimal,
    recency_coverage: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            (family_count_score * FAMILY_COUNT_WEIGHT)
            + (concentration_independence_score * CONCENTRATION_WEIGHT)
            + (direct_source_share * DIRECT_SOURCE_WEIGHT)
            + (contradiction_quality_score * CONTRADICTION_WEIGHT)
            + (recency_coverage * RECENCY_WEIGHT)
        )
        if score > ONE:
            return ONE
        if score < ZERO:
            return ZERO
        return score.quantize(DECIMAL_QUANTUM)


def _independence_status(
    value: ResearchSourceFamilyIndependenceV10Input,
    metrics: _Metrics,
) -> str:
    if value.source_count == ZERO:
        return "blocked"
    if value.source_family_count < value.required_family_count:
        return "blocked"
    if metrics.contradiction_rate >= BLOCKING_CONTRADICTION_FLOOR:
        return "blocked"
    if (
        metrics.independence_score >= INDEPENDENT_SCORE_FLOOR
        and metrics.repeated_source_concentration <= BALANCED_CONCENTRATION_CEILING
        and metrics.direct_source_share >= STRONG_DIRECT_SHARE_FLOOR
        and metrics.contradiction_rate <= LOW_CONTRADICTION_CEILING
        and metrics.recency_coverage >= CURRENT_RECENCY_FLOOR
    ):
        return "independent"
    if (
        metrics.independence_score >= WATCH_SCORE_FLOOR
        and metrics.repeated_source_concentration <= WATCH_CONCENTRATION_CEILING
        and metrics.contradiction_rate <= MODERATE_CONTRADICTION_CEILING
        and metrics.recency_coverage >= PARTIAL_RECENCY_FLOOR
    ):
        return "watch"
    return "thin"


def _recommendation(independence_status: str) -> str:
    if independence_status == "independent":
        return "use_packet"
    if independence_status == "watch":
        return "add_confirming_direct_source"
    if independence_status == "blocked":
        return "block_until_family_quorum"
    return "expand_source_families"


def _reason_codes(
    value: ResearchSourceFamilyIndependenceV10Input,
    metrics: _Metrics,
    independence_status: str,
) -> tuple[str, ...]:
    return (
        _family_count_reason(value),
        _concentration_reason(value, metrics),
        _direct_share_reason(metrics.direct_source_share),
        _contradiction_reason(value, metrics),
        _recency_reason(metrics.recency_coverage),
        f"independence_{independence_status}",
    )


def _family_count_reason(value: ResearchSourceFamilyIndependenceV10Input) -> str:
    if value.source_count == ZERO:
        return "family_count_empty"
    if value.source_family_count < value.required_family_count:
        return "family_count_insufficient"
    return "family_count_met"


def _concentration_reason(
    value: ResearchSourceFamilyIndependenceV10Input,
    metrics: _Metrics,
) -> str:
    if value.source_count == ZERO:
        return "concentration_empty"
    if metrics.repeated_source_concentration <= BALANCED_CONCENTRATION_CEILING:
        return "concentration_balanced"
    if metrics.repeated_source_concentration <= WATCH_CONCENTRATION_CEILING:
        return "concentration_elevated"
    return "concentration_dominant"


def _direct_share_reason(direct_source_share: Decimal) -> str:
    if direct_source_share >= STRONG_DIRECT_SHARE_FLOOR:
        return "direct_share_strong"
    if direct_source_share >= ADEQUATE_DIRECT_SHARE_FLOOR:
        return "direct_share_adequate"
    return "direct_share_thin"


def _contradiction_reason(
    value: ResearchSourceFamilyIndependenceV10Input,
    metrics: _Metrics,
) -> str:
    if value.source_count == ZERO:
        return "contradiction_rate_uncovered"
    if metrics.contradiction_rate <= LOW_CONTRADICTION_CEILING:
        return "contradiction_rate_low"
    if metrics.contradiction_rate <= MODERATE_CONTRADICTION_CEILING:
        return "contradiction_rate_moderate"
    return "contradiction_rate_high"


def _recency_reason(recency_coverage: Decimal) -> str:
    if recency_coverage >= CURRENT_RECENCY_FLOOR:
        return "recency_coverage_current"
    if recency_coverage >= PARTIAL_RECENCY_FLOOR:
        return "recency_coverage_partial"
    return "recency_coverage_stale"


def _validate_report(report: ResearchSourceFamilyIndependenceV10Report) -> None:
    value = ResearchSourceFamilyIndependenceV10Input(
        packet_id=report.packet_id,
        market_slug=report.market_slug,
        source_count=report.source_count,
        source_family_count=report.source_family_count,
        required_family_count=report.required_family_count,
        largest_source_family_count=report.largest_source_family_count,
        direct_source_count=report.direct_source_count,
        contradicting_source_count=report.contradicting_source_count,
        recent_source_count=report.recent_source_count,
    )
    metrics = _metrics(value)
    expected_status = _independence_status(value, metrics)
    expected_recommendation = _recommendation(expected_status)
    if report.family_count_score != metrics.family_count_score:
        raise ValueError("family_count_score must match input fields")
    if report.repeated_source_concentration != metrics.repeated_source_concentration:
        raise ValueError("repeated_source_concentration must match input fields")
    if report.concentration_independence_score != metrics.concentration_independence_score:
        raise ValueError("concentration_independence_score must match input fields")
    if report.direct_source_share != metrics.direct_source_share:
        raise ValueError("direct_source_share must match input fields")
    if report.contradiction_rate != metrics.contradiction_rate:
        raise ValueError("contradiction_rate must match input fields")
    if report.contradiction_quality_score != metrics.contradiction_quality_score:
        raise ValueError("contradiction_quality_score must match input fields")
    if report.recency_coverage != metrics.recency_coverage:
        raise ValueError("recency_coverage must match input fields")
    if report.independence_score != metrics.independence_score:
        raise ValueError("independence_score must match input fields")
    if report.independence_status != expected_status:
        raise ValueError("independence_status must match input fields")
    if report.recommendation != expected_recommendation:
        raise ValueError("recommendation must match independence_status")
    if report.reason_codes != _reason_codes(value, metrics, expected_status):
        raise ValueError("reason_codes must match input fields")


def _report_payload(report: ResearchSourceFamilyIndependenceV10Report) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "packet_id": report.packet_id,
        "market_slug": report.market_slug,
        "source_count": report.source_count,
        "source_family_count": report.source_family_count,
        "required_family_count": report.required_family_count,
        "largest_source_family_count": report.largest_source_family_count,
        "direct_source_count": report.direct_source_count,
        "contradicting_source_count": report.contradicting_source_count,
        "recent_source_count": report.recent_source_count,
        "family_count_score": report.family_count_score,
        "repeated_source_concentration": report.repeated_source_concentration,
        "concentration_independence_score": report.concentration_independence_score,
        "direct_source_share": report.direct_source_share,
        "contradiction_rate": report.contradiction_rate,
        "contradiction_quality_score": report.contradiction_quality_score,
        "recency_coverage": report.recency_coverage,
        "independence_score": report.independence_score,
        "independence_status": report.independence_status,
        "recommendation": report.recommendation,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(DECIMAL_QUANTUM))
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    integral = normalized.to_integral_value().quantize(DECIMAL_QUANTUM)
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _validate_input_counts(value: ResearchSourceFamilyIndependenceV10Input) -> None:
    for field_name in (
        "source_family_count",
        "largest_source_family_count",
        "direct_source_count",
        "contradicting_source_count",
        "recent_source_count",
    ):
        if getattr(value, field_name) > value.source_count:
            raise ValueError(f"{field_name} must not exceed source_count")
    if value.source_count == ZERO:
        return
    if value.source_family_count == ZERO:
        raise ValueError("source_family_count must be positive when source_count is positive")
    if value.largest_source_family_count == ZERO:
        raise ValueError(
            "largest_source_family_count must be positive when source_count is positive",
        )


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _share(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _capped_ratio(numerator, denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
        if ratio > ONE:
            return ONE
        if ratio < ZERO:
            return ZERO
        return ratio.quantize(DECIMAL_QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        if label == "payload":
            raise ValueError("payload paper_only must be True")
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        if label == "payload":
            raise ValueError("payload report_only must be True")
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        if label == "payload":
            raise ValueError("payload readonly must be True")
        raise ValueError(f"{label} must be readonly")


__all__ = (
    "CONFIG_VERSION",
    "INDEPENDENCE_STATUSES",
    "RECOMMENDATIONS",
    "ResearchSourceFamilyIndependenceV10Input",
    "ResearchSourceFamilyIndependenceV10Report",
    "evaluate_strategy_research_source_family_independence_v10",
    "strategy_research_source_family_independence_v10",
    "strategy_research_source_family_independence_v10_payload",
)
