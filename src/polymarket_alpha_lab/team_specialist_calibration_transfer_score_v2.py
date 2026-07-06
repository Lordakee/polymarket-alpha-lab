"""Readonly Decimal scorecard for specialist calibration transfer fit."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CALIBRATION_TRANSFER_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-calibration-transfer-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

TRANSFER_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "calibration_transfer_pass",
    "calibration_transfer_watch",
    "calibration_transfer_blocked",
    "source_calibration_strong",
    "source_calibration_watch",
    "source_calibration_weak",
    "domain_similarity_strong",
    "domain_similarity_watch",
    "domain_similarity_weak",
    "recent_transfer_error_low",
    "recent_transfer_error_watch",
    "recent_transfer_error_high",
    "sample_depth_full",
    "sample_depth_partial",
    "sample_depth_sparse",
    "stale_samples_clear",
    "stale_sample_penalty_applied",
    "stale_samples_blocking",
    "specialist_fit_boosted",
    "specialist_fit_supported",
    "specialist_fit_weak",
)
REPORT_REASON_CODES = (
    "calibration_transfer_scorecard_passed",
    "calibration_transfer_scorecard_watch_rows",
    "calibration_transfer_scorecard_blocked_rows",
    "calibration_transfer_scorecard_empty",
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
    "DEFAULT_TEAM_SPECIALIST_CALIBRATION_TRANSFER_SCORE_V2_CONFIG_VERSION",
    "TeamSpecialistCalibrationTransferScoreV2Config",
    "TeamSpecialistCalibrationTransferScoreV2Input",
    "TeamSpecialistCalibrationTransferScoreV2Row",
    "TeamSpecialistCalibrationTransferScoreV2Report",
    "build_team_specialist_calibration_transfer_score_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationTransferScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CALIBRATION_TRANSFER_SCORE_V2_CONFIG_VERSION
    )
    source_calibration_weight: Decimal = Decimal("0.300000")
    domain_similarity_weight: Decimal = Decimal("0.200000")
    recent_transfer_accuracy_weight: Decimal = Decimal("0.200000")
    sample_depth_weight: Decimal = Decimal("0.150000")
    specialist_fit_weight: Decimal = Decimal("0.150000")
    full_sample_count: Decimal = Decimal("10")
    stale_sample_penalty_count: Decimal = Decimal("5")
    stale_sample_penalty_weight: Decimal = Decimal("0.250000")
    specialist_fit_boost_floor: Decimal = Decimal("0.800000")
    specialist_fit_boost_weight: Decimal = Decimal("0.050000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCalibrationTransferScoreV2Config:
            raise TypeError(
                "TeamSpecialistCalibrationTransferScoreV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCalibrationTransferScoreV2Config:
            raise ValueError(
                "config must be exactly TeamSpecialistCalibrationTransferScoreV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CALIBRATION_TRANSFER_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_calibration_weight",
            "domain_similarity_weight",
            "recent_transfer_accuracy_weight",
            "sample_depth_weight",
            "specialist_fit_weight",
            "stale_sample_penalty_weight",
            "specialist_fit_boost_floor",
            "specialist_fit_boost_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "full_sample_count",
            "stale_sample_penalty_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags(
            "TeamSpecialistCalibrationTransferScoreV2Config",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationTransferScoreV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationTransferScoreV2Input:
    team_id: str
    specialist_id: str
    source_domain_id: str
    target_domain_id: str
    source_calibration_score: Decimal
    target_domain_similarity_score: Decimal
    recent_transfer_error: Decimal
    transfer_sample_count: Decimal
    stale_sample_count: Decimal
    specialist_fit_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCalibrationTransferScoreV2Input:
            raise TypeError(
                "TeamSpecialistCalibrationTransferScoreV2Input does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCalibrationTransferScoreV2Input:
            raise ValueError(
                "input must be exactly TeamSpecialistCalibrationTransferScoreV2Input",
            )
        for field_name in (
            "team_id",
            "specialist_id",
            "source_domain_id",
            "target_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_calibration_score",
            "target_domain_similarity_score",
            "recent_transfer_error",
            "specialist_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("transfer_sample_count", "stale_sample_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.stale_sample_count > self.transfer_sample_count:
            raise ValueError("stale_sample_count must not exceed transfer_sample_count")
        _require_hard_flags(
            "TeamSpecialistCalibrationTransferScoreV2Input",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationTransferScoreV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationTransferScoreV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    source_domain_id: str
    target_domain_id: str
    source_calibration_score: Decimal
    target_domain_similarity_score: Decimal
    recent_transfer_error: Decimal
    recent_transfer_accuracy_score: Decimal
    transfer_sample_count: Decimal
    sample_depth_score: Decimal
    stale_sample_count: Decimal
    stale_sample_penalty: Decimal
    specialist_fit_score: Decimal
    specialist_fit_boost: Decimal
    cross_domain_transfer_score: Decimal
    transfer_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCalibrationTransferScoreV2Row:
            raise TypeError(
                "TeamSpecialistCalibrationTransferScoreV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCalibrationTransferScoreV2Row:
            raise ValueError(
                "row must be exactly TeamSpecialistCalibrationTransferScoreV2Row",
            )
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in (
            "team_id",
            "specialist_id",
            "source_domain_id",
            "target_domain_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_calibration_score",
            "target_domain_similarity_score",
            "recent_transfer_error",
            "recent_transfer_accuracy_score",
            "sample_depth_score",
            "stale_sample_penalty",
            "specialist_fit_score",
            "specialist_fit_boost",
            "cross_domain_transfer_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("transfer_sample_count", "stale_sample_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.stale_sample_count > self.transfer_sample_count:
            raise ValueError("stale_sample_count must not exceed transfer_sample_count")
        _require_transfer_status("transfer_status", self.transfer_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _require_hard_flags("TeamSpecialistCalibrationTransferScoreV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationTransferScoreV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCalibrationTransferScoreV2Report:
    generated_at: datetime
    config_version: str
    transfer_scorecard_status: str
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_cross_domain_transfer_score: Decimal
    top_cross_domain_transfer_score: Decimal
    bottom_cross_domain_transfer_score: Decimal
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCalibrationTransferScoreV2Report:
            raise TypeError(
                "TeamSpecialistCalibrationTransferScoreV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCalibrationTransferScoreV2Report:
            raise ValueError(
                "report must be exactly TeamSpecialistCalibrationTransferScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_transfer_status(
            "transfer_scorecard_status",
            self.transfer_scorecard_status,
        )
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
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
            "average_cross_domain_transfer_score",
            "top_cross_domain_transfer_score",
            "bottom_cross_domain_transfer_score",
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
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCalibrationTransferScoreV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationTransferScoreV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationTransferScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_calibration_transfer_score_v2(
    transfer_inputs: object,
    *,
    config: TeamSpecialistCalibrationTransferScoreV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCalibrationTransferScoreV2Report:
    if config is None:
        config = TeamSpecialistCalibrationTransferScoreV2Config()
    if type(config) is not TeamSpecialistCalibrationTransferScoreV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCalibrationTransferScoreV2Config",
        )
    _require_hard_flags("TeamSpecialistCalibrationTransferScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_transfer_inputs(transfer_inputs)

    rows = tuple(
        _row_for_transfer_input(rank=index, item=item, config=config)
        for index, item in enumerate(_sorted_transfer_inputs(items, config), start=1)
    )
    status = _scorecard_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "transfer_scorecard_status": status,
        "candidate_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_candidate_count": _status_count(rows, "pass"),
        "watch_candidate_count": _status_count(rows, "watch"),
        "blocked_candidate_count": _status_count(rows, "blocked"),
        "average_cross_domain_transfer_score": _average_score(rows),
        "top_cross_domain_transfer_score": _top_score(rows),
        "bottom_cross_domain_transfer_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCalibrationTransferScoreV2Report(**values)


def _sorted_transfer_inputs(
    items: tuple[TeamSpecialistCalibrationTransferScoreV2Input, ...],
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> tuple[TeamSpecialistCalibrationTransferScoreV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_score_for_transfer_input(item, config),
                item.team_id,
                item.specialist_id,
                item.source_domain_id,
                item.target_domain_id,
            ),
        ),
    )


def _row_for_transfer_input(
    *,
    rank: int,
    item: TeamSpecialistCalibrationTransferScoreV2Input,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> TeamSpecialistCalibrationTransferScoreV2Row:
    sample_depth_score = _sample_depth_score(item.transfer_sample_count, config)
    stale_sample_penalty = _stale_sample_penalty(item.stale_sample_count, config)
    specialist_fit_boost = _specialist_fit_boost(item.specialist_fit_score, config)
    score = _score_for_transfer_input(item, config)
    status = _transfer_status(score, config)
    return TeamSpecialistCalibrationTransferScoreV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        source_domain_id=item.source_domain_id,
        target_domain_id=item.target_domain_id,
        source_calibration_score=item.source_calibration_score,
        target_domain_similarity_score=item.target_domain_similarity_score,
        recent_transfer_error=item.recent_transfer_error,
        recent_transfer_accuracy_score=_recent_transfer_accuracy_score(
            item.recent_transfer_error,
        ),
        transfer_sample_count=item.transfer_sample_count,
        sample_depth_score=sample_depth_score,
        stale_sample_count=item.stale_sample_count,
        stale_sample_penalty=stale_sample_penalty,
        specialist_fit_score=item.specialist_fit_score,
        specialist_fit_boost=specialist_fit_boost,
        cross_domain_transfer_score=score,
        transfer_status=status,
        reason_codes=_row_reason_codes(
            item,
            status,
            sample_depth_score,
            stale_sample_penalty,
            specialist_fit_boost,
            config,
        ),
    )


def _score_for_transfer_input(
    item: TeamSpecialistCalibrationTransferScoreV2Input,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.source_calibration_score * config.source_calibration_weight
            + item.target_domain_similarity_score * config.domain_similarity_weight
            + _recent_transfer_accuracy_score(item.recent_transfer_error)
            * config.recent_transfer_accuracy_weight
            + _sample_depth_score(item.transfer_sample_count, config)
            * config.sample_depth_weight
            + item.specialist_fit_score * config.specialist_fit_weight
            + _specialist_fit_boost(item.specialist_fit_score, config)
            - _stale_sample_penalty(item.stale_sample_count, config)
        )
        return _clamp_ratio(score)


def _recent_transfer_accuracy_score(recent_transfer_error: Decimal) -> Decimal:
    return _clamp_ratio(ONE - recent_transfer_error)


def _sample_depth_score(
    transfer_sample_count: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(transfer_sample_count / config.full_sample_count)


def _stale_sample_penalty(
    stale_sample_count: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        stale_ratio = _clamp_ratio(stale_sample_count / config.stale_sample_penalty_count)
        return _clamp_ratio(stale_ratio * config.stale_sample_penalty_weight)


def _specialist_fit_boost(
    specialist_fit_score: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> Decimal:
    if specialist_fit_score <= config.specialist_fit_boost_floor:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        denominator = ONE - config.specialist_fit_boost_floor
        if denominator <= ZERO:
            return ZERO
        boost_ratio = (specialist_fit_score - config.specialist_fit_boost_floor) / denominator
        return _clamp_ratio(boost_ratio * config.specialist_fit_boost_weight)


def _transfer_status(
    score: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _scorecard_status(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.transfer_status == "blocked" for row in rows):
        return "blocked"
    if any(row.transfer_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: TeamSpecialistCalibrationTransferScoreV2Input,
    status: str,
    sample_depth_score: Decimal,
    stale_sample_penalty: Decimal,
    specialist_fit_boost: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> tuple[str, ...]:
    return (
        f"calibration_transfer_{status}",
        _tier_reason(
            item.source_calibration_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_calibration_strong",
            watch_reason="source_calibration_watch",
            weak_reason="source_calibration_weak",
        ),
        _tier_reason(
            item.target_domain_similarity_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.500000"),
            strong_reason="domain_similarity_strong",
            watch_reason="domain_similarity_watch",
            weak_reason="domain_similarity_weak",
        ),
        _recent_transfer_error_reason(item.recent_transfer_error),
        _sample_depth_reason(sample_depth_score),
        _stale_sample_reason(stale_sample_penalty, config),
        _specialist_fit_reason(
            item.specialist_fit_score,
            specialist_fit_boost,
        ),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("calibration_transfer_scorecard_empty",)
    reasons: list[str] = []
    if any(row.transfer_status == "blocked" for row in rows):
        reasons.append("calibration_transfer_scorecard_blocked_rows")
    if any(row.transfer_status == "watch" for row in rows):
        reasons.append("calibration_transfer_scorecard_watch_rows")
    if not reasons and status == "pass":
        reasons.append("calibration_transfer_scorecard_passed")
    return tuple(reasons)


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


def _recent_transfer_error_reason(value: Decimal) -> str:
    if value <= Decimal("0.120000"):
        return "recent_transfer_error_low"
    if value <= Decimal("0.250000"):
        return "recent_transfer_error_watch"
    return "recent_transfer_error_high"


def _sample_depth_reason(value: Decimal) -> str:
    if value >= Decimal("0.800000"):
        return "sample_depth_full"
    if value >= Decimal("0.400000"):
        return "sample_depth_partial"
    return "sample_depth_sparse"


def _stale_sample_reason(
    value: Decimal,
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> str:
    if value == ZERO:
        return "stale_samples_clear"
    if value < config.stale_sample_penalty_weight:
        return "stale_sample_penalty_applied"
    return "stale_samples_blocking"


def _specialist_fit_reason(
    specialist_fit_score: Decimal,
    specialist_fit_boost: Decimal,
) -> str:
    if specialist_fit_boost > ZERO:
        return "specialist_fit_boosted"
    if specialist_fit_score >= Decimal("0.600000"):
        return "specialist_fit_supported"
    return "specialist_fit_weak"


def _status_count(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.transfer_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.cross_domain_transfer_score for row in rows) / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.cross_domain_transfer_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.cross_domain_transfer_score for row in rows)


def _normalize_transfer_inputs(
    value: object,
) -> tuple[TeamSpecialistCalibrationTransferScoreV2Input, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("transfer_inputs must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistCalibrationTransferScoreV2Input:
            raise ValueError(
                "transfer items must be TeamSpecialistCalibrationTransferScoreV2Input",
            )
        _require_hard_flags("TeamSpecialistCalibrationTransferScoreV2Input", item)
    keys = tuple(
        (
            item.team_id,
            item.specialist_id,
            item.source_domain_id,
            item.target_domain_id,
        )
        for item in items
    )
    if len(set(keys)) != len(keys):
        raise ValueError("transfer items must not contain duplicate transfer keys")
    return items


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistCalibrationTransferScoreV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCalibrationTransferScoreV2Row",
            )
    return value


def _validate_config(
    config: TeamSpecialistCalibrationTransferScoreV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.source_calibration_weight
            + config.domain_similarity_weight
            + config.recent_transfer_accuracy_weight
            + config.sample_depth_weight
            + config.specialist_fit_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("transfer score weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")
    if config.specialist_fit_boost_floor >= ONE and config.specialist_fit_boost_weight > ZERO:
        raise ValueError("specialist_fit_boost_floor must leave room for a boost")


def _validate_row_consistency(row: TeamSpecialistCalibrationTransferScoreV2Row) -> None:
    if row.recent_transfer_accuracy_score != _recent_transfer_accuracy_score(
        row.recent_transfer_error,
    ):
        raise ValueError("recent_transfer_accuracy_score must match recent_transfer_error")
    if row.stale_sample_penalty > ZERO and row.stale_sample_count == ZERO:
        raise ValueError("stale_sample_penalty requires stale samples")
    if row.specialist_fit_boost > ZERO and row.specialist_fit_score <= Decimal("0.800000"):
        raise ValueError("specialist_fit_boost requires specialist fit above boost floor")


def _validate_report_consistency(
    report: TeamSpecialistCalibrationTransferScoreV2Report,
) -> None:
    rows = report.rows
    if report.candidate_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("candidate_count must match rows")
    if (
        report.pass_candidate_count != _status_count(rows, "pass")
        or report.watch_candidate_count != _status_count(rows, "watch")
        or report.blocked_candidate_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_candidate_count
        + report.watch_candidate_count
        + report.blocked_candidate_count
        != report.candidate_count
    ):
        raise ValueError("status counts must sum to candidate_count")
    _validate_rows_sorted(rows)
    expected_status = _scorecard_status(rows)
    if report.transfer_scorecard_status != expected_status:
        raise ValueError("transfer_scorecard_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.transfer_scorecard_status):
        raise ValueError("reason_codes must match transfer_scorecard_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_cross_domain_transfer_score != _average_score(rows):
        raise ValueError("average_cross_domain_transfer_score must match rows")
    if report.top_cross_domain_transfer_score != _top_score(rows):
        raise ValueError("top_cross_domain_transfer_score must match rows")
    if report.bottom_cross_domain_transfer_score != _bottom_score(rows):
        raise ValueError("bottom_cross_domain_transfer_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCalibrationTransferScoreV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.cross_domain_transfer_score,
                row.team_id,
                row.specialist_id,
                row.source_domain_id,
                row.target_domain_id,
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
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_transfer_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in TRANSFER_STATUSES:
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
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload contains unsafe numeric value")
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
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
