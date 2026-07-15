"""Readonly Decimal scorecard for prediction-market specialist teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SCORE_BANDS = ("strong", "watch", "blocked")
IMPROVEMENT_REASON_CODES = (
    "ready_ratio_strong",
    "ready_ratio_watch",
    "ready_ratio_weak",
    "recommendation_block_rate_strong",
    "recommendation_block_rate_watch",
    "recommendation_block_rate_high",
    "edge_to_threshold_strong",
    "edge_to_threshold_watch",
    "edge_to_threshold_weak",
    "source_reliability_strong",
    "source_reliability_watch",
    "source_reliability_weak",
    "memory_quality_strong",
    "memory_quality_watch",
    "memory_quality_weak",
    "settled_feedback_strong",
    "settled_feedback_adequate",
    "settled_feedback_thin",
    "prediction_market_team_scorecard_strong",
    "prediction_market_team_scorecard_watch",
    "prediction_market_team_scorecard_blocked",
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
    "PredictionMarketTeamScorecardReport",
    "build_prediction_market_team_scorecard_report",
)


@dataclass(frozen=True)
class PredictionMarketTeamScorecardReport:
    team_code: str
    domain: str
    screened_market_count: Decimal
    ready_recommendation_count: Decimal
    blocked_recommendation_count: Decimal
    average_edge_to_threshold_probability: Decimal
    average_source_reliability_score: Decimal
    average_memory_quality_score: Decimal
    settled_feedback_sample_count: Decimal
    ready_ratio: Decimal
    team_score: Decimal
    score_band: str
    improvement_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_code",
            _require_public_label("team_code", self.team_code),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_label("domain", self.domain),
        )
        for field_name in (
            "screened_market_count",
            "ready_recommendation_count",
            "blocked_recommendation_count",
            "settled_feedback_sample_count",
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
            "average_edge_to_threshold_probability",
            "average_source_reliability_score",
            "average_memory_quality_score",
            "ready_ratio",
            "team_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_score_band("score_band", self.score_band)
        object.__setattr__(
            self,
            "improvement_reason_codes",
            _normalize_reason_codes(self.improvement_reason_codes),
        )
        _require_hard_flags("PredictionMarketTeamScorecardReport", self)
        _reject_unsafe_public_payload(
            "PredictionMarketTeamScorecardReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)
        if self.digest == "":
            object.__setattr__(self, "digest", _digest_for_report(self))
        else:
            _require_sha256_digest("digest", self.digest)
            if self.digest != _digest_for_report(self):
                raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        _require_hard_flags("PredictionMarketTeamScorecardReport", self)
        _validate_report_consistency(self)
        if self.digest != _digest_for_report(self):
            raise ValueError("digest must match public payload")
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a dict")
        _reject_unsafe_public_payload("public_payload", payload)
        return payload


def build_prediction_market_team_scorecard_report(
    *,
    team_code: str,
    domain: str,
    screened_market_count: Decimal,
    ready_recommendation_count: Decimal,
    blocked_recommendation_count: Decimal,
    average_edge_to_threshold_probability: Decimal,
    average_source_reliability_score: Decimal,
    average_memory_quality_score: Decimal,
    settled_feedback_sample_count: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PredictionMarketTeamScorecardReport:
    screened_market_count = _normalize_nonnegative_integral_decimal(
        "screened_market_count",
        screened_market_count,
    )
    ready_recommendation_count = _normalize_nonnegative_integral_decimal(
        "ready_recommendation_count",
        ready_recommendation_count,
    )
    blocked_recommendation_count = _normalize_nonnegative_integral_decimal(
        "blocked_recommendation_count",
        blocked_recommendation_count,
    )
    average_edge_to_threshold_probability = _normalize_ratio(
        "average_edge_to_threshold_probability",
        average_edge_to_threshold_probability,
    )
    average_source_reliability_score = _normalize_ratio(
        "average_source_reliability_score",
        average_source_reliability_score,
    )
    average_memory_quality_score = _normalize_ratio(
        "average_memory_quality_score",
        average_memory_quality_score,
    )
    settled_feedback_sample_count = _normalize_nonnegative_integral_decimal(
        "settled_feedback_sample_count",
        settled_feedback_sample_count,
    )
    values = {
        "team_code": team_code,
        "domain": domain,
        "screened_market_count": screened_market_count,
        "ready_recommendation_count": ready_recommendation_count,
        "blocked_recommendation_count": blocked_recommendation_count,
        "average_edge_to_threshold_probability": average_edge_to_threshold_probability,
        "average_source_reliability_score": average_source_reliability_score,
        "average_memory_quality_score": average_memory_quality_score,
        "settled_feedback_sample_count": settled_feedback_sample_count,
        "ready_ratio": _ready_ratio(
            ready_recommendation_count,
            screened_market_count,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    values["team_score"] = _team_score(values)
    values["score_band"] = _score_band(
        values["team_score"],
        screened_market_count,
    )
    values["improvement_reason_codes"] = _improvement_reason_codes(values)
    return PredictionMarketTeamScorecardReport(**values)


def _team_score(values: dict[str, object]) -> Decimal:
    screened_market_count = _expect_decimal(values["screened_market_count"])
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _expect_decimal(values["ready_ratio"]) * Decimal("0.300000")
            + _expect_decimal(values["average_edge_to_threshold_probability"])
            * Decimal("0.250000")
            + _expect_decimal(values["average_source_reliability_score"])
            * Decimal("0.200000")
            + _expect_decimal(values["average_memory_quality_score"]) * Decimal("0.150000")
            + _feedback_score(_expect_decimal(values["settled_feedback_sample_count"]))
            * Decimal("0.100000")
        )
        if screened_market_count > ZERO:
            score += Decimal("0.020000")
        return _clamp_ratio(score)


def _ready_ratio(ready_count: Decimal, screened_count: Decimal) -> Decimal:
    if screened_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ready_count / screened_count)


def _blocked_ratio(blocked_count: Decimal, screened_count: Decimal) -> Decimal:
    if screened_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(blocked_count / screened_count)


def _feedback_score(settled_feedback_sample_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(settled_feedback_sample_count / Decimal("10"))


def _score_band(team_score: object, screened_market_count: Decimal) -> str:
    score = _expect_decimal(team_score)
    if screened_market_count == ZERO:
        return "blocked"
    if score >= Decimal("0.850000"):
        return "strong"
    if score >= Decimal("0.500000"):
        return "watch"
    return "blocked"


def _improvement_reason_codes(values: dict[str, object]) -> tuple[str, ...]:
    screened_market_count = _expect_decimal(values["screened_market_count"])
    blocked_ratio = _blocked_ratio(
        _expect_decimal(values["blocked_recommendation_count"]),
        screened_market_count,
    )
    score_band = values["score_band"]
    if type(score_band) is not str:
        raise ValueError("score_band must be a string")
    return (
        _minimum_tier_reason(
            _expect_decimal(values["ready_ratio"]),
            strong=Decimal("0.750000"),
            watch=Decimal("0.400000"),
            strong_reason="ready_ratio_strong",
            watch_reason="ready_ratio_watch",
            weak_reason="ready_ratio_weak",
        ),
        _maximum_tier_reason(
            blocked_ratio,
            strong=Decimal("0.050000"),
            watch=Decimal("0.200000"),
            strong_reason="recommendation_block_rate_strong",
            watch_reason="recommendation_block_rate_watch",
            weak_reason="recommendation_block_rate_high",
        ),
        _minimum_tier_reason(
            _expect_decimal(values["average_edge_to_threshold_probability"]),
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="edge_to_threshold_strong",
            watch_reason="edge_to_threshold_watch",
            weak_reason="edge_to_threshold_weak",
        ),
        _minimum_tier_reason(
            _expect_decimal(values["average_source_reliability_score"]),
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_reliability_strong",
            watch_reason="source_reliability_watch",
            weak_reason="source_reliability_weak",
        ),
        _minimum_tier_reason(
            _expect_decimal(values["average_memory_quality_score"]),
            strong=Decimal("0.750000"),
            watch=Decimal("0.550000"),
            strong_reason="memory_quality_strong",
            watch_reason="memory_quality_watch",
            weak_reason="memory_quality_weak",
        ),
        _feedback_reason(_expect_decimal(values["settled_feedback_sample_count"])),
        f"prediction_market_team_scorecard_{score_band}",
    )


def _feedback_reason(settled_feedback_sample_count: Decimal) -> str:
    if settled_feedback_sample_count >= Decimal("10"):
        return "settled_feedback_strong"
    if settled_feedback_sample_count >= Decimal("5"):
        return "settled_feedback_adequate"
    return "settled_feedback_thin"


def _minimum_tier_reason(
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


def _maximum_tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value <= strong:
        return strong_reason
    if value <= watch:
        return watch_reason
    return weak_reason


def _validate_report_consistency(report: PredictionMarketTeamScorecardReport) -> None:
    if (
        report.ready_recommendation_count + report.blocked_recommendation_count
        > report.screened_market_count
    ):
        raise ValueError(
            "ready and blocked recommendation counts must not exceed "
            "screened_market_count",
        )
    if report.ready_ratio != _ready_ratio(
        report.ready_recommendation_count,
        report.screened_market_count,
    ):
        raise ValueError("ready_ratio must match recommendation counts")
    expected_score = _team_score(asdict(report))
    if report.team_score != expected_score:
        raise ValueError("team_score must match score inputs")
    if report.score_band != _score_band(report.team_score, report.screened_market_count):
        raise ValueError("score_band must match team_score")
    if report.improvement_reason_codes != _improvement_reason_codes(asdict(report)):
        raise ValueError("improvement_reason_codes must match score inputs")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_score_band(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if value not in SCORE_BANDS:
        raise ValueError(f"{field_name} must be strong, watch, or blocked")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("improvement_reason_codes must be a non-empty tuple")
    normalized = tuple(
        _require_public_label("improvement_reason_codes", item) for item in value
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError("improvement_reason_codes must not contain duplicates")
    if any(item not in IMPROVEMENT_REASON_CODES for item in normalized):
        raise ValueError("improvement_reason_codes must contain known reason codes")
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


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _expect_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("score inputs must be Decimal")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _digest_for_report(report: PredictionMarketTeamScorecardReport) -> str:
    values = asdict(report)
    values["digest"] = ""
    digest_payload = _payload_value(values)
    if type(digest_payload) is not dict:
        raise ValueError("digest payload must be a dict")
    digest_payload = {
        key: item for key, item in digest_payload.items() if key != "digest"
    }
    _reject_unsafe_public_payload("digest payload", digest_payload)
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
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
