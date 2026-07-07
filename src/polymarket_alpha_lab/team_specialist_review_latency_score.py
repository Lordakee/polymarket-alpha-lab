"""Pure readonly report for specialist review latency score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_CONFIG_VERSION = (
    "team-specialist-review-latency-score-v1"
)
TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODES = (
    "review_latency_pass",
    "review_latency_watch",
    "review_latency_block",
    "median_research_latency_clear",
    "median_research_latency_watch",
    "median_research_latency_over_sla",
    "p90_review_latency_clear",
    "p90_review_latency_watch",
    "p90_review_latency_over_sla",
    "oldest_unreviewed_event_clear",
    "oldest_unreviewed_event_watch",
    "oldest_unreviewed_event_over_sla",
    "delayed_event_share_clear",
    "delayed_event_share_watch",
    "delayed_event_share_block",
)
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii")
    for value in (
        "3a2f2f",
        "40",
        "3f",
        "7261775f63616e6469646174655f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "6d61726b65745f7175657374696f6e",
        "7175657374696f6e",
        "736f757263655f726566",
        "736f757263655f72656673",
        "736f75726365",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "7461626c65",
        "746f6b656e",
        "736563726574",
        "77616c6c6574",
        "61757468",
        "6f72646572",
        "7472616465",
        "706f736974696f6e",
        "706f736974696f6e2d73697a696e67",
        "706f736974696f6e5f73697a696e67",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "6c697665",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7375706162617365",
        "626c6f636b6564",
    )
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_STATUSES",
    "TeamSpecialistReviewLatencyScoreConfig",
    "TeamSpecialistReviewLatencyScoreInput",
    "TeamSpecialistReviewLatencyScoreReport",
    "score_team_specialist_review_latency",
    "team_specialist_review_latency_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistReviewLatencyScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_CONFIG_VERSION
    response_sla_hours: Decimal = Decimal("12.000000")
    median_research_weight: Decimal = Decimal("0.300000")
    p90_review_weight: Decimal = Decimal("0.300000")
    oldest_unreviewed_weight: Decimal = Decimal("0.250000")
    delayed_event_share_weight: Decimal = Decimal("0.150000")
    watch_latency_ratio: Decimal = Decimal("0.750000")
    block_latency_ratio: Decimal = Decimal("1.000000")
    delayed_event_share_watch_floor: Decimal = Decimal("0.100000")
    delayed_event_share_block_floor: Decimal = Decimal("0.500000")
    score_watch_floor: Decimal = Decimal("0.500000")
    score_block_floor: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "response_sla_hours",
            _normalize_positive_decimal("response_sla_hours", self.response_sla_hours),
        )
        for field_name in (
            "median_research_weight",
            "p90_review_weight",
            "oldest_unreviewed_weight",
            "delayed_event_share_weight",
            "watch_latency_ratio",
            "block_latency_ratio",
            "delayed_event_share_watch_floor",
            "delayed_event_share_block_floor",
            "score_watch_floor",
            "score_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistReviewLatencyScoreConfig", self)
        _reject_public_payload(
            "TeamSpecialistReviewLatencyScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewLatencyScoreInput:
    team_id: str
    specialist_id: str
    observed_event_count: Decimal
    delayed_event_count: Decimal
    median_research_latency_hours: Decimal
    p90_review_latency_hours: Decimal
    oldest_unreviewed_event_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in ("observed_event_count", "delayed_event_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "median_research_latency_hours",
            "p90_review_latency_hours",
            "oldest_unreviewed_event_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.delayed_event_count > self.observed_event_count:
            raise ValueError("delayed_event_count must not exceed observed_event_count")
        _require_hard_flags("TeamSpecialistReviewLatencyScoreInput", self)
        _reject_public_payload(
            "TeamSpecialistReviewLatencyScoreInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewLatencyScoreReport:
    config: TeamSpecialistReviewLatencyScoreConfig
    team_id: str
    specialist_id: str
    observed_event_count: Decimal
    delayed_event_count: Decimal
    median_research_latency_hours: Decimal
    p90_review_latency_hours: Decimal
    oldest_unreviewed_event_age_hours: Decimal
    delayed_event_ratio: Decimal
    median_research_sla_ratio: Decimal
    p90_review_sla_ratio: Decimal
    oldest_unreviewed_sla_ratio: Decimal
    review_latency_score: Decimal
    timeliness_impact_status: str
    workflow_priority_status: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.config) is not TeamSpecialistReviewLatencyScoreConfig:
            raise ValueError("config must be a TeamSpecialistReviewLatencyScoreConfig")
        _require_hard_flags("TeamSpecialistReviewLatencyScoreConfig", self.config)
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in ("observed_event_count", "delayed_event_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "median_research_latency_hours",
            "p90_review_latency_hours",
            "oldest_unreviewed_event_age_hours",
            "delayed_event_ratio",
            "median_research_sla_ratio",
            "p90_review_sla_ratio",
            "oldest_unreviewed_sla_ratio",
            "review_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.delayed_event_count > self.observed_event_count:
            raise ValueError("delayed_event_count must not exceed observed_event_count")
        _require_status("timeliness_impact_status", self.timeliness_impact_status)
        _require_status("workflow_priority_status", self.workflow_priority_status)
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistReviewLatencyScoreReport", self)
        _reject_public_payload(
            "TeamSpecialistReviewLatencyScoreReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_public_payload("TeamSpecialistReviewLatencyScoreReport.payload", payload)
        _verify_payload_digest(payload)
        return payload


def score_team_specialist_review_latency(
    latency_signal: TeamSpecialistReviewLatencyScoreInput,
    *,
    config: TeamSpecialistReviewLatencyScoreConfig | None = None,
) -> TeamSpecialistReviewLatencyScoreReport:
    if type(latency_signal) is not TeamSpecialistReviewLatencyScoreInput:
        raise ValueError(
            "latency_signal must be a TeamSpecialistReviewLatencyScoreInput",
        )
    if config is None:
        config = TeamSpecialistReviewLatencyScoreConfig()
    if type(config) is not TeamSpecialistReviewLatencyScoreConfig:
        raise ValueError("config must be a TeamSpecialistReviewLatencyScoreConfig")
    _require_hard_flags("TeamSpecialistReviewLatencyScoreInput", latency_signal)
    _require_hard_flags("TeamSpecialistReviewLatencyScoreConfig", config)

    delayed_ratio = _delayed_event_ratio(latency_signal)
    median_ratio = _median_research_sla_ratio(latency_signal, config)
    p90_ratio = _p90_review_sla_ratio(latency_signal, config)
    oldest_ratio = _oldest_unreviewed_sla_ratio(latency_signal, config)
    score = _review_latency_score(
        config=config,
        delayed_event_ratio=delayed_ratio,
        median_research_sla_ratio=median_ratio,
        p90_review_sla_ratio=p90_ratio,
        oldest_unreviewed_sla_ratio=oldest_ratio,
    )
    timeliness_status = _timeliness_impact_status(
        config=config,
        delayed_event_ratio=delayed_ratio,
        median_research_sla_ratio=median_ratio,
        p90_review_sla_ratio=p90_ratio,
        oldest_unreviewed_sla_ratio=oldest_ratio,
        review_latency_score=score,
    )
    workflow_status = _workflow_priority_status(timeliness_status)
    values: dict[str, object] = {
        "config": config,
        "team_id": latency_signal.team_id,
        "specialist_id": latency_signal.specialist_id,
        "observed_event_count": latency_signal.observed_event_count,
        "delayed_event_count": latency_signal.delayed_event_count,
        "median_research_latency_hours": latency_signal.median_research_latency_hours,
        "p90_review_latency_hours": latency_signal.p90_review_latency_hours,
        "oldest_unreviewed_event_age_hours": (
            latency_signal.oldest_unreviewed_event_age_hours
        ),
        "delayed_event_ratio": delayed_ratio,
        "median_research_sla_ratio": median_ratio,
        "p90_review_sla_ratio": p90_ratio,
        "oldest_unreviewed_sla_ratio": oldest_ratio,
        "review_latency_score": score,
        "timeliness_impact_status": timeliness_status,
        "workflow_priority_status": workflow_status,
        "report_status": workflow_status,
        "reason_codes": _reason_codes(
            config=config,
            timeliness_status=timeliness_status,
            delayed_event_ratio=delayed_ratio,
            median_research_sla_ratio=median_ratio,
            p90_review_sla_ratio=p90_ratio,
            oldest_unreviewed_sla_ratio=oldest_ratio,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistReviewLatencyScoreReport(**values)


def team_specialist_review_latency_score_payload(
    report: TeamSpecialistReviewLatencyScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistReviewLatencyScoreReport:
        _require_hard_flags("TeamSpecialistReviewLatencyScoreReport", report)
        return report.payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_public_payload("TeamSpecialistReviewLatencyScoreReport.payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_statuses(payload)
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistReviewLatencyScoreReport")


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


def _delayed_event_ratio(
    latency_signal: TeamSpecialistReviewLatencyScoreInput
    | TeamSpecialistReviewLatencyScoreReport,
) -> Decimal:
    if latency_signal.observed_event_count == ZERO:
        return ZERO
    return _clamp_ratio(
        _ratio(latency_signal.delayed_event_count, latency_signal.observed_event_count),
    )


def _median_research_sla_ratio(
    latency_signal: TeamSpecialistReviewLatencyScoreInput
    | TeamSpecialistReviewLatencyScoreReport,
    config: TeamSpecialistReviewLatencyScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        _ratio(latency_signal.median_research_latency_hours, config.response_sla_hours),
    )


def _p90_review_sla_ratio(
    latency_signal: TeamSpecialistReviewLatencyScoreInput
    | TeamSpecialistReviewLatencyScoreReport,
    config: TeamSpecialistReviewLatencyScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        _ratio(latency_signal.p90_review_latency_hours, config.response_sla_hours),
    )


def _oldest_unreviewed_sla_ratio(
    latency_signal: TeamSpecialistReviewLatencyScoreInput
    | TeamSpecialistReviewLatencyScoreReport,
    config: TeamSpecialistReviewLatencyScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        _ratio(
            latency_signal.oldest_unreviewed_event_age_hours,
            config.response_sla_hours,
        ),
    )


def _review_latency_score(
    *,
    config: TeamSpecialistReviewLatencyScoreConfig,
    delayed_event_ratio: Decimal,
    median_research_sla_ratio: Decimal,
    p90_review_sla_ratio: Decimal,
    oldest_unreviewed_sla_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            median_research_sla_ratio * config.median_research_weight
            + p90_review_sla_ratio * config.p90_review_weight
            + oldest_unreviewed_sla_ratio * config.oldest_unreviewed_weight
            + delayed_event_ratio * config.delayed_event_share_weight,
        )


def _timeliness_impact_status(
    *,
    config: TeamSpecialistReviewLatencyScoreConfig,
    delayed_event_ratio: Decimal,
    median_research_sla_ratio: Decimal,
    p90_review_sla_ratio: Decimal,
    oldest_unreviewed_sla_ratio: Decimal,
    review_latency_score: Decimal,
) -> str:
    if (
        review_latency_score >= config.score_block_floor
        or delayed_event_ratio >= config.delayed_event_share_block_floor
        or median_research_sla_ratio >= config.block_latency_ratio
        or p90_review_sla_ratio >= config.block_latency_ratio
        or oldest_unreviewed_sla_ratio >= config.block_latency_ratio
    ):
        return "block"
    if (
        review_latency_score >= config.score_watch_floor
        or delayed_event_ratio >= config.delayed_event_share_watch_floor
        or median_research_sla_ratio >= config.watch_latency_ratio
        or p90_review_sla_ratio >= config.watch_latency_ratio
        or oldest_unreviewed_sla_ratio >= config.watch_latency_ratio
    ):
        return "watch"
    return "pass"


def _workflow_priority_status(timeliness_status: str) -> str:
    return timeliness_status


def _reason_codes(
    *,
    config: TeamSpecialistReviewLatencyScoreConfig,
    timeliness_status: str,
    delayed_event_ratio: Decimal,
    median_research_sla_ratio: Decimal,
    p90_review_sla_ratio: Decimal,
    oldest_unreviewed_sla_ratio: Decimal,
) -> tuple[str, ...]:
    reasons = (
        f"review_latency_{timeliness_status}",
        _latency_reason(
            median_research_sla_ratio,
            config=config,
            clear_reason="median_research_latency_clear",
            watch_reason="median_research_latency_watch",
            block_reason="median_research_latency_over_sla",
        ),
        _latency_reason(
            p90_review_sla_ratio,
            config=config,
            clear_reason="p90_review_latency_clear",
            watch_reason="p90_review_latency_watch",
            block_reason="p90_review_latency_over_sla",
        ),
        _latency_reason(
            oldest_unreviewed_sla_ratio,
            config=config,
            clear_reason="oldest_unreviewed_event_clear",
            watch_reason="oldest_unreviewed_event_watch",
            block_reason="oldest_unreviewed_event_over_sla",
        ),
        _delayed_event_share_reason(delayed_event_ratio, config),
    )
    return _normalize_reason_codes("reason_codes", reasons)


def _latency_reason(
    value: Decimal,
    *,
    config: TeamSpecialistReviewLatencyScoreConfig,
    clear_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= config.block_latency_ratio:
        return block_reason
    if value >= config.watch_latency_ratio:
        return watch_reason
    return clear_reason


def _delayed_event_share_reason(
    delayed_event_ratio: Decimal,
    config: TeamSpecialistReviewLatencyScoreConfig,
) -> str:
    if delayed_event_ratio >= config.delayed_event_share_block_floor:
        return "delayed_event_share_block"
    if delayed_event_ratio >= config.delayed_event_share_watch_floor:
        return "delayed_event_share_watch"
    return "delayed_event_share_clear"


def _validate_config(config: TeamSpecialistReviewLatencyScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.median_research_weight
            + config.p90_review_weight
            + config.oldest_unreviewed_weight
            + config.delayed_event_share_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("latency weights must sum to 1.000000")
    if config.watch_latency_ratio > config.block_latency_ratio:
        raise ValueError("watch_latency_ratio must not exceed block_latency_ratio")
    if config.delayed_event_share_watch_floor > config.delayed_event_share_block_floor:
        raise ValueError(
            "delayed_event_share_watch_floor must not exceed "
            "delayed_event_share_block_floor",
        )
    if config.score_watch_floor > config.score_block_floor:
        raise ValueError("score_watch_floor must not exceed score_block_floor")


def _validate_report_consistency(report: TeamSpecialistReviewLatencyScoreReport) -> None:
    expected_delayed_ratio = _delayed_event_ratio(report)
    if report.delayed_event_ratio != expected_delayed_ratio:
        raise ValueError("delayed_event_ratio must match input fields")
    expected_median_ratio = _median_research_sla_ratio(report, report.config)
    if report.median_research_sla_ratio != expected_median_ratio:
        raise ValueError("median_research_sla_ratio must match input fields")
    expected_p90_ratio = _p90_review_sla_ratio(report, report.config)
    if report.p90_review_sla_ratio != expected_p90_ratio:
        raise ValueError("p90_review_sla_ratio must match input fields")
    expected_oldest_ratio = _oldest_unreviewed_sla_ratio(report, report.config)
    if report.oldest_unreviewed_sla_ratio != expected_oldest_ratio:
        raise ValueError("oldest_unreviewed_sla_ratio must match input fields")
    expected_score = _review_latency_score(
        config=report.config,
        delayed_event_ratio=report.delayed_event_ratio,
        median_research_sla_ratio=report.median_research_sla_ratio,
        p90_review_sla_ratio=report.p90_review_sla_ratio,
        oldest_unreviewed_sla_ratio=report.oldest_unreviewed_sla_ratio,
    )
    if report.review_latency_score != expected_score:
        raise ValueError("review_latency_score must match components")
    expected_status = _timeliness_impact_status(
        config=report.config,
        delayed_event_ratio=report.delayed_event_ratio,
        median_research_sla_ratio=report.median_research_sla_ratio,
        p90_review_sla_ratio=report.p90_review_sla_ratio,
        oldest_unreviewed_sla_ratio=report.oldest_unreviewed_sla_ratio,
        review_latency_score=report.review_latency_score,
    )
    if report.timeliness_impact_status != expected_status:
        raise ValueError("timeliness_impact_status must match score")
    expected_workflow_status = _workflow_priority_status(report.timeliness_impact_status)
    if report.workflow_priority_status != expected_workflow_status:
        raise ValueError("workflow_priority_status must match timeliness_impact_status")
    if report.report_status != report.workflow_priority_status:
        raise ValueError("report_status must match workflow_priority_status")
    expected_reasons = _reason_codes(
        config=report.config,
        timeliness_status=report.timeliness_impact_status,
        delayed_event_ratio=report.delayed_event_ratio,
        median_research_sla_ratio=report.median_research_sla_ratio,
        p90_review_sla_ratio=report.p90_review_sla_ratio,
        oldest_unreviewed_sla_ratio=report.oldest_unreviewed_sla_ratio,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report fields")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    _reject_public_text("value", value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in TEAM_SPECIALIST_REVIEW_LATENCY_SCORE_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in REASON_CODES for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_public_payload("digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_payload_statuses(payload: dict[str, Any]) -> None:
    for field_name in (
        "timeliness_impact_status",
        "workflow_priority_status",
        "report_status",
    ):
        _require_status(field_name, payload.get(field_name))


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    _reject_public_payload("public payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _verify_payload_statuses(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    expected_digest = _derived_validation_digest(payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _reject_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_text("key", key)
            _reject_public_payload(label, item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError(f"unsafe public value in {label}")
    if type(value) is str:
        _reject_public_text("value", value)


def _reject_public_text(role: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public {role}")
