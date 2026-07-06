"""Readonly Decimal report for specialist source rotation learning score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_LEARNING_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-source-rotation-learning-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

LEARNING_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "source_rotation_learning_pass",
    "source_rotation_learning_watch",
    "source_rotation_learning_blocked",
    "source_diversity_strong",
    "source_diversity_watch",
    "source_diversity_thin",
    "stale_source_mix_clear",
    "stale_source_mix_watch",
    "stale_source_mix_stale",
    "rotation_success_strong",
    "rotation_success_watch",
    "rotation_success_weak",
    "learning_capture_strong",
    "learning_capture_watch",
    "learning_capture_weak",
    "source_quality_strong",
    "source_quality_watch",
    "source_quality_weak",
    "successful_rotation_boost_applied",
    "successful_rotation_boost_absent",
)
REPORT_REASON_CODES = (
    "source_rotation_learning_report_passed",
    "source_rotation_learning_report_watch_rows",
    "source_rotation_learning_report_blocked_rows",
    "source_rotation_learning_report_empty",
    "stale_source_mix_penalty_rows",
    "successful_rotation_boost_rows",
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
    "DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_LEARNING_SCORE_V2_CONFIG_VERSION",
    "TeamSpecialistSourceRotationLearningScoreV2Config",
    "TeamSpecialistSourceRotationLearningV2Input",
    "TeamSpecialistSourceRotationLearningScoreV2Row",
    "TeamSpecialistSourceRotationLearningScoreV2Report",
    "build_team_specialist_source_rotation_learning_score_v2",
)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationLearningScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_LEARNING_SCORE_V2_CONFIG_VERSION
    )
    source_diversity_weight: Decimal = Decimal("0.300000")
    rotation_success_weight: Decimal = Decimal("0.300000")
    learning_capture_weight: Decimal = Decimal("0.250000")
    source_quality_weight: Decimal = Decimal("0.150000")
    stale_source_mix_penalty_weight: Decimal = Decimal("0.250000")
    successful_rotation_boost_weight: Decimal = Decimal("0.100000")
    target_source_count: Decimal = Decimal("5")
    stale_source_mix_watch_floor: Decimal = Decimal("0.250000")
    stale_source_mix_block_floor: Decimal = Decimal("0.500000")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "source_diversity_weight",
            "rotation_success_weight",
            "learning_capture_weight",
            "source_quality_weight",
            "stale_source_mix_penalty_weight",
            "successful_rotation_boost_weight",
            "stale_source_mix_watch_floor",
            "stale_source_mix_block_floor",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_source_count",
            _normalize_positive_integral_decimal(
                "target_source_count",
                self.target_source_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags(
            "TeamSpecialistSourceRotationLearningScoreV2Config",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistSourceRotationLearningScoreV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistSourceRotationLearningV2Input:
    specialist_id: str
    domain_id: str
    source_mix_id: str
    unique_source_count: Decimal
    rotated_source_count: Decimal
    stale_source_count: Decimal
    successful_rotation_count: Decimal
    evaluated_rotation_count: Decimal
    learning_capture_score: Decimal
    source_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("specialist_id", "domain_id", "source_mix_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unique_source_count",
            _normalize_positive_integral_decimal(
                "unique_source_count",
                self.unique_source_count,
            ),
        )
        for field_name in (
            "rotated_source_count",
            "stale_source_count",
            "successful_rotation_count",
            "evaluated_rotation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("learning_capture_score", "source_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_input(self)
        _require_hard_flags(
            "TeamSpecialistSourceRotationLearningV2Input",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistSourceRotationLearningV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistSourceRotationLearningScoreV2Row:
    rank: Decimal
    specialist_id: str
    domain_id: str
    source_mix_id: str
    unique_source_count: Decimal
    rotated_source_count: Decimal
    stale_source_count: Decimal
    successful_rotation_count: Decimal
    evaluated_rotation_count: Decimal
    source_diversity_score: Decimal
    stale_source_ratio: Decimal
    stale_source_mix_penalty: Decimal
    rotation_success_ratio: Decimal
    successful_rotation_boost: Decimal
    learning_capture_score: Decimal
    source_quality_score: Decimal
    source_rotation_learning_score: Decimal
    learning_status: str
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
        for field_name in ("specialist_id", "domain_id", "source_mix_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unique_source_count",
            _normalize_positive_integral_decimal(
                "unique_source_count",
                self.unique_source_count,
            ),
        )
        for field_name in (
            "rotated_source_count",
            "stale_source_count",
            "successful_rotation_count",
            "evaluated_rotation_count",
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
            "source_diversity_score",
            "stale_source_ratio",
            "stale_source_mix_penalty",
            "rotation_success_ratio",
            "successful_rotation_boost",
            "learning_capture_score",
            "source_quality_score",
            "source_rotation_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_learning_status("learning_status", self.learning_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags(
            "TeamSpecialistSourceRotationLearningScoreV2Row",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistSourceRotationLearningScoreV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistSourceRotationLearningScoreV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    specialist_count: Decimal
    pass_specialist_count: Decimal
    watch_specialist_count: Decimal
    blocked_specialist_count: Decimal
    stale_source_mix_count: Decimal
    successful_rotation_boosted_count: Decimal
    average_source_rotation_learning_score: Decimal
    top_source_rotation_learning_score: Decimal
    bottom_source_rotation_learning_score: Decimal
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...]
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
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "specialist_count",
            "pass_specialist_count",
            "watch_specialist_count",
            "blocked_specialist_count",
            "stale_source_mix_count",
            "successful_rotation_boosted_count",
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
            "average_source_rotation_learning_score",
            "top_source_rotation_learning_score",
            "bottom_source_rotation_learning_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags(
            "TeamSpecialistSourceRotationLearningScoreV2Report",
            self,
        )
        _reject_unsafe_public_payload(
            "TeamSpecialistSourceRotationLearningScoreV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistSourceRotationLearningScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_source_rotation_learning_score_v2(
    source_mixes: object,
    *,
    config: TeamSpecialistSourceRotationLearningScoreV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistSourceRotationLearningScoreV2Report:
    if config is None:
        config = TeamSpecialistSourceRotationLearningScoreV2Config()
    if type(config) is not TeamSpecialistSourceRotationLearningScoreV2Config:
        raise ValueError(
            "config must be a TeamSpecialistSourceRotationLearningScoreV2Config",
        )
    _require_hard_flags("TeamSpecialistSourceRotationLearningScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    mixes = _normalize_source_mixes(source_mixes)

    rows = tuple(
        _row_for_source_mix(rank=index, source_mix=item, config=config)
        for index, item in enumerate(_sorted_source_mixes(mixes, config), start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "specialist_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_specialist_count": _status_count(rows, "pass"),
        "watch_specialist_count": _status_count(rows, "watch"),
        "blocked_specialist_count": _status_count(rows, "blocked"),
        "stale_source_mix_count": _stale_source_mix_count(rows),
        "successful_rotation_boosted_count": _successful_rotation_boosted_count(rows),
        "average_source_rotation_learning_score": _average_score(rows),
        "top_source_rotation_learning_score": _top_score(rows),
        "bottom_source_rotation_learning_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistSourceRotationLearningScoreV2Report(**values)


def _sorted_source_mixes(
    source_mixes: tuple[TeamSpecialistSourceRotationLearningV2Input, ...],
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> tuple[TeamSpecialistSourceRotationLearningV2Input, ...]:
    return tuple(
        sorted(
            source_mixes,
            key=lambda item: (
                -_score_for_source_mix(item, config),
                item.specialist_id,
                item.domain_id,
                item.source_mix_id,
            ),
        ),
    )


def _row_for_source_mix(
    *,
    rank: int,
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> TeamSpecialistSourceRotationLearningScoreV2Row:
    score = _score_for_source_mix(source_mix, config)
    status = _learning_status(score, config)
    return TeamSpecialistSourceRotationLearningScoreV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        specialist_id=source_mix.specialist_id,
        domain_id=source_mix.domain_id,
        source_mix_id=source_mix.source_mix_id,
        unique_source_count=source_mix.unique_source_count,
        rotated_source_count=source_mix.rotated_source_count,
        stale_source_count=source_mix.stale_source_count,
        successful_rotation_count=source_mix.successful_rotation_count,
        evaluated_rotation_count=source_mix.evaluated_rotation_count,
        source_diversity_score=_source_diversity_score(source_mix, config),
        stale_source_ratio=_stale_source_ratio(source_mix),
        stale_source_mix_penalty=_stale_source_mix_penalty(source_mix, config),
        rotation_success_ratio=_rotation_success_ratio(source_mix),
        successful_rotation_boost=_successful_rotation_boost(source_mix, config),
        learning_capture_score=source_mix.learning_capture_score,
        source_quality_score=source_mix.source_quality_score,
        source_rotation_learning_score=score,
        learning_status=status,
        reason_codes=_row_reason_codes(source_mix, status, config),
    )


def _score_for_source_mix(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _source_diversity_score(source_mix, config) * config.source_diversity_weight
            + _rotation_success_ratio(source_mix) * config.rotation_success_weight
            + source_mix.learning_capture_score * config.learning_capture_weight
            + source_mix.source_quality_score * config.source_quality_weight
            - _stale_source_mix_penalty(source_mix, config)
            + _successful_rotation_boost(source_mix, config)
        )
        return _clamp_ratio(score)


def _source_diversity_score(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(source_mix.unique_source_count / config.target_source_count)


def _stale_source_ratio(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(source_mix.stale_source_count / source_mix.unique_source_count)


def _stale_source_mix_penalty(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(_stale_source_ratio(source_mix) * config.stale_source_mix_penalty_weight)


def _rotation_success_ratio(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
) -> Decimal:
    if source_mix.evaluated_rotation_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            source_mix.successful_rotation_count / source_mix.evaluated_rotation_count,
        )


def _successful_rotation_boost(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> Decimal:
    if source_mix.rotated_source_count == ZERO or source_mix.successful_rotation_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(_rotation_success_ratio(source_mix) * config.successful_rotation_boost_weight)


def _learning_status(
    score: Decimal,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _report_status(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.learning_status == "blocked" for row in rows):
        return "blocked"
    if any(row.learning_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    status: str,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> tuple[str, ...]:
    return (
        f"source_rotation_learning_{status}",
        _tier_reason(
            _source_diversity_score(source_mix, config),
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_diversity_strong",
            watch_reason="source_diversity_watch",
            weak_reason="source_diversity_thin",
        ),
        _stale_source_mix_reason(source_mix, config),
        _tier_reason(
            _rotation_success_ratio(source_mix),
            strong=Decimal("0.750000"),
            watch=Decimal("0.500000"),
            strong_reason="rotation_success_strong",
            watch_reason="rotation_success_watch",
            weak_reason="rotation_success_weak",
        ),
        _tier_reason(
            source_mix.learning_capture_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="learning_capture_strong",
            watch_reason="learning_capture_watch",
            weak_reason="learning_capture_weak",
        ),
        _tier_reason(
            source_mix.source_quality_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="source_quality_strong",
            watch_reason="source_quality_watch",
            weak_reason="source_quality_weak",
        ),
        (
            "successful_rotation_boost_applied"
            if _successful_rotation_boost(source_mix, config) > ZERO
            else "successful_rotation_boost_absent"
        ),
    )


def _stale_source_mix_reason(
    source_mix: TeamSpecialistSourceRotationLearningV2Input,
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> str:
    stale_ratio = _stale_source_ratio(source_mix)
    if stale_ratio < config.stale_source_mix_watch_floor:
        return "stale_source_mix_clear"
    if stale_ratio < config.stale_source_mix_block_floor:
        return "stale_source_mix_watch"
    return "stale_source_mix_stale"


def _report_reason_codes(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("source_rotation_learning_report_empty",)
    reasons: list[str] = []
    if any(row.learning_status == "blocked" for row in rows):
        reasons.append("source_rotation_learning_report_blocked_rows")
    if any(row.learning_status == "watch" for row in rows):
        reasons.append("source_rotation_learning_report_watch_rows")
    if not reasons and status == "pass":
        reasons.append("source_rotation_learning_report_passed")
    stale_reason_codes = {"stale_source_mix_watch", "stale_source_mix_stale"}
    if any(stale_reason_codes.intersection(row.reason_codes) for row in rows):
        reasons.append("stale_source_mix_penalty_rows")
    if any(row.successful_rotation_boost > ZERO for row in rows):
        reasons.append("successful_rotation_boost_rows")
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


def _status_count(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.learning_status == status)).quantize(
        COUNT_QUANT,
    )


def _stale_source_mix_count(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> Decimal:
    return Decimal(
        sum(
            1
            for row in rows
            if "stale_source_mix_watch" in row.reason_codes
            or "stale_source_mix_stale" in row.reason_codes
        ),
    ).quantize(COUNT_QUANT)


def _successful_rotation_boosted_count(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.successful_rotation_boost > ZERO)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.source_rotation_learning_score for row in rows) / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.source_rotation_learning_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.source_rotation_learning_score for row in rows)


def _normalize_source_mixes(
    value: object,
) -> tuple[TeamSpecialistSourceRotationLearningV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("source_mixes must be an iterable")
    source_mixes = tuple(value)
    for item in source_mixes:
        if type(item) is not TeamSpecialistSourceRotationLearningV2Input:
            raise ValueError(
                "source mix items must be TeamSpecialistSourceRotationLearningV2Input",
            )
        _require_hard_flags("TeamSpecialistSourceRotationLearningV2Input", item)
    keys = tuple((item.specialist_id, item.domain_id, item.source_mix_id) for item in source_mixes)
    if len(set(keys)) != len(keys):
        raise ValueError("source mix items must not contain duplicate specialist/domain/source keys")
    return source_mixes


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistSourceRotationLearningScoreV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistSourceRotationLearningScoreV2Row",
            )
    return value


def _validate_config(
    config: TeamSpecialistSourceRotationLearningScoreV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.source_diversity_weight
            + config.rotation_success_weight
            + config.learning_capture_weight
            + config.source_quality_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")
    if config.stale_source_mix_watch_floor > config.stale_source_mix_block_floor:
        raise ValueError(
            "stale_source_mix_watch_floor must not exceed stale_source_mix_block_floor",
        )


def _validate_input(source_mix: TeamSpecialistSourceRotationLearningV2Input) -> None:
    if source_mix.rotated_source_count > source_mix.unique_source_count:
        raise ValueError("rotated_source_count must not exceed unique_source_count")
    if source_mix.stale_source_count > source_mix.unique_source_count:
        raise ValueError("stale_source_count must not exceed unique_source_count")
    if source_mix.successful_rotation_count > source_mix.evaluated_rotation_count:
        raise ValueError(
            "successful_rotation_count must not exceed evaluated_rotation_count",
        )


def _validate_row_consistency(
    row: TeamSpecialistSourceRotationLearningScoreV2Row,
) -> None:
    if row.rotated_source_count > row.unique_source_count:
        raise ValueError("rotated_source_count must not exceed unique_source_count")
    if row.stale_source_count > row.unique_source_count:
        raise ValueError("stale_source_count must not exceed unique_source_count")
    if row.successful_rotation_count > row.evaluated_rotation_count:
        raise ValueError(
            "successful_rotation_count must not exceed evaluated_rotation_count",
        )
    if row.successful_rotation_boost > ZERO and row.rotation_success_ratio == ZERO:
        raise ValueError("successful_rotation_boost must require successful rotations")


def _validate_report_consistency(
    report: TeamSpecialistSourceRotationLearningScoreV2Report,
) -> None:
    rows = report.rows
    if report.specialist_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("specialist_count must match rows")
    if (
        report.pass_specialist_count != _status_count(rows, "pass")
        or report.watch_specialist_count != _status_count(rows, "watch")
        or report.blocked_specialist_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_specialist_count
        + report.watch_specialist_count
        + report.blocked_specialist_count
        != report.specialist_count
    ):
        raise ValueError("status counts must sum to specialist_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.stale_source_mix_count != _stale_source_mix_count(rows):
        raise ValueError("stale_source_mix_count must match rows")
    if report.successful_rotation_boosted_count != _successful_rotation_boosted_count(rows):
        raise ValueError("successful_rotation_boosted_count must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_source_rotation_learning_score != _average_score(rows):
        raise ValueError("average_source_rotation_learning_score must match rows")
    if report.top_source_rotation_learning_score != _top_score(rows):
        raise ValueError("top_source_rotation_learning_score must match rows")
    if report.bottom_source_rotation_learning_score != _bottom_score(rows):
        raise ValueError("bottom_source_rotation_learning_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistSourceRotationLearningScoreV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.source_rotation_learning_score,
                row.specialist_id,
                row.domain_id,
                row.source_mix_id,
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


def _require_learning_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in LEARNING_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
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
