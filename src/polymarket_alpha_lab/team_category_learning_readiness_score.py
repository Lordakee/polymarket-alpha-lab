"""Pure Phase 1 team/category learning readiness score."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import InitVar, asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import (
    require_category_id,
    require_team_category_pair,
    require_team_id,
)


DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION = (
    "team-category-learning-readiness-score-v1"
)
TEAM_CATEGORY_LEARNING_READINESS_STATUSES = ("pass", "watch", "block")
TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES = (
    "team_category_learning_readiness_pass",
    "team_category_learning_readiness_watch",
    "team_category_learning_readiness_block",
    "settled_sample_count_full",
    "settled_sample_count_watch",
    "settled_sample_count_thin",
    "recent_calibration_quality_strong",
    "recent_calibration_quality_watch",
    "recent_calibration_quality_weak",
    "postmortem_completion_complete",
    "postmortem_completion_partial",
    "postmortem_completion_gap",
    "source_reliability_trend_positive",
    "source_reliability_trend_flat",
    "source_reliability_trend_weak",
    "specialist_coverage_full",
    "specialist_coverage_partial",
    "specialist_coverage_thin",
    "readiness_score_below_pass",
    "readiness_score_below_watch",
    "team_category_learning_readiness_empty_inputs",
    "team_category_learning_readiness_passed",
    "team_category_learning_readiness_watch_rows",
    "team_category_learning_readiness_block_rows",
)

SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_COMPONENT_COUNT = Decimal("5")

_ROW_REASON_CODES = TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES[:20]
_REPORT_REASON_CODES = TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES[20:]
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_PAYLOAD_FIELD_DENY_FRAGMENTS = (
    "candidate",
    "market" + "_id",
    "market" + "_slug",
    "question",
    "slug",
    "source" + "_ref",
    "source" + "_url",
    "source" + "_text",
    "reference",
    "ref",
    "url",
    "text",
    "d" + "sn",
    "table" + "_name",
    "table",
    "acc" + "ount",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "reco" + "mmend",
    "://",
    "www.",
    "token",
    "secret",
    "credential",
    "private",
    "key",
    "position",
    "size",
)


__all__ = (
    "DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION",
    "TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES",
    "TEAM_CATEGORY_LEARNING_READINESS_STATUSES",
    "TeamCategoryLearningReadinessScore",
    "TeamCategoryLearningReadinessScoreConfig",
    "TeamCategoryLearningReadinessScoreInput",
    "TeamCategoryLearningReadinessScoreReport",
    "build_team_category_learning_readiness_score_report",
    "team_category_learning_readiness_score_payload",
)


@dataclass(frozen=True)
class TeamCategoryLearningReadinessScoreConfig:
    config_version: str = DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION
    settled_sample_weight: Decimal = Decimal("0.250000")
    recent_calibration_quality_weight: Decimal = Decimal("0.300000")
    postmortem_completion_weight: Decimal = Decimal("0.200000")
    source_reliability_trend_weight: Decimal = Decimal("0.150000")
    specialist_coverage_weight: Decimal = Decimal("0.100000")
    target_settled_sample_count: Decimal = Decimal("40")
    minimum_settled_sample_count: Decimal = Decimal("10")
    pass_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCategoryLearningReadinessScoreConfig:
            raise TypeError(
                "TeamCategoryLearningReadinessScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamCategoryLearningReadinessScoreConfig:
            raise ValueError(
                "config must be exactly TeamCategoryLearningReadinessScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "settled_sample_weight",
            "recent_calibration_quality_weight",
            "postmortem_completion_weight",
            "source_reliability_trend_weight",
            "specialist_coverage_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_settled_sample_count",
            _require_positive_count(
                "target_settled_sample_count",
                self.target_settled_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "minimum_settled_sample_count",
            _require_nonnegative_count(
                "minimum_settled_sample_count",
                self.minimum_settled_sample_count,
            ),
        )
        _validate_config(self)
        require_paper_only_flags("team category learning readiness config", self)


@dataclass(frozen=True)
class TeamCategoryLearningReadinessScoreInput:
    team_id: str
    category_id: str
    settled_sample_count: Decimal
    recent_calibration_quality_score: Decimal
    postmortem_completion_score: Decimal
    source_reliability_trend_score: Decimal
    specialist_coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCategoryLearningReadinessScoreInput:
            raise TypeError(
                "TeamCategoryLearningReadinessScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamCategoryLearningReadinessScoreInput:
            raise ValueError(
                "input must be exactly TeamCategoryLearningReadinessScoreInput",
            )
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "settled_sample_count",
            _require_nonnegative_count("settled_sample_count", self.settled_sample_count),
        )
        for field_name in (
            "recent_calibration_quality_score",
            "postmortem_completion_score",
            "source_reliability_trend_score",
            "specialist_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("team category learning readiness input", self)


@dataclass(frozen=True)
class TeamCategoryLearningReadinessScore:
    team_id: str
    category_id: str
    settled_sample_count: Decimal
    settled_sample_score: Decimal
    recent_calibration_quality_score: Decimal
    postmortem_completion_score: Decimal
    source_reliability_trend_score: Decimal
    specialist_coverage_score: Decimal
    readiness_score: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[TeamCategoryLearningReadinessScoreConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCategoryLearningReadinessScore:
            raise TypeError(
                "TeamCategoryLearningReadinessScore does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: TeamCategoryLearningReadinessScoreConfig | None,
    ) -> None:
        if type(self) is not TeamCategoryLearningReadinessScore:
            raise ValueError("row must be exactly TeamCategoryLearningReadinessScore")
        row_config = _normalize_row_validation_config(validation_config)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "settled_sample_count",
            _require_nonnegative_count("settled_sample_count", self.settled_sample_count),
        )
        for field_name in (
            "settled_sample_score",
            "recent_calibration_quality_score",
            "postmortem_completion_score",
            "source_reliability_trend_score",
            "specialist_coverage_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("readiness_status", self.readiness_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODES),
        )
        _validate_row(self, row_config)
        require_paper_only_flags("team category learning readiness row", self)


@dataclass(frozen=True)
class TeamCategoryLearningReadinessScoreReport:
    generated_at: datetime
    config_version: str
    readiness_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    rows: tuple[TeamCategoryLearningReadinessScore, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamCategoryLearningReadinessScoreReport:
            raise TypeError(
                "TeamCategoryLearningReadinessScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamCategoryLearningReadinessScoreReport:
            raise ValueError(
                "report must be exactly TeamCategoryLearningReadinessScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("readiness_status", self.readiness_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_readiness_score",
            _require_ratio_decimal(
                "average_readiness_score",
                self.average_readiness_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODES),
        )
        _validate_report(self)
        require_paper_only_flags("team category learning readiness report", self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(payload)
        _validate_public_payload_taxonomy_labels(payload)
        _validate_public_payload_status_vocabulary(payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_category_learning_readiness_score_report(
    inputs: Sequence[TeamCategoryLearningReadinessScoreInput],
    *,
    generated_at: datetime,
    config: TeamCategoryLearningReadinessScoreConfig | None = None,
) -> TeamCategoryLearningReadinessScoreReport:
    if config is None:
        config = TeamCategoryLearningReadinessScoreConfig()
    if type(config) is not TeamCategoryLearningReadinessScoreConfig:
        raise ValueError(
            "config must be a TeamCategoryLearningReadinessScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("team category learning readiness config", config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in normalized_inputs),
            key=lambda row: (row.team_id, row.category_id),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return TeamCategoryLearningReadinessScoreReport(
        generated_at=generated_at,
        config_version=config.config_version,
        readiness_status=_report_status(rows),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_readiness_score=_average(tuple(row.readiness_score for row in rows)),
        rows=rows,
        reason_codes=reason_codes,
    )


def team_category_learning_readiness_score_payload(
    report: TeamCategoryLearningReadinessScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamCategoryLearningReadinessScoreReport:
        require_paper_only_flags("team category learning readiness report", report)
        payload = report.payload
        require_paper_only_flags("team category learning readiness payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_public_payload_taxonomy_labels(payload)
        _validate_public_payload_status_vocabulary(payload)
        require_paper_only_flags("team category learning readiness payload", _DictFlags(payload))
        return payload
    raise ValueError(
        "report must be a TeamCategoryLearningReadinessScoreReport or payload",
    )


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


def _row_from_input(
    item: TeamCategoryLearningReadinessScoreInput,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> TeamCategoryLearningReadinessScore:
    settled_sample_score = _clamp_ratio(
        item.settled_sample_count / config.target_settled_sample_count,
    )
    readiness_score = _readiness_score(
        settled_sample_score=settled_sample_score,
        recent_calibration_quality_score=item.recent_calibration_quality_score,
        postmortem_completion_score=item.postmortem_completion_score,
        source_reliability_trend_score=item.source_reliability_trend_score,
        specialist_coverage_score=item.specialist_coverage_score,
        config=config,
    )
    readiness_status = _row_status(
        settled_sample_count=item.settled_sample_count,
        readiness_score=readiness_score,
        config=config,
    )
    return TeamCategoryLearningReadinessScore(
        team_id=item.team_id,
        category_id=item.category_id,
        settled_sample_count=item.settled_sample_count,
        settled_sample_score=settled_sample_score,
        recent_calibration_quality_score=item.recent_calibration_quality_score,
        postmortem_completion_score=item.postmortem_completion_score,
        source_reliability_trend_score=item.source_reliability_trend_score,
        specialist_coverage_score=item.specialist_coverage_score,
        readiness_score=readiness_score,
        readiness_status=readiness_status,
        reason_codes=_row_reason_codes(
            settled_sample_count=item.settled_sample_count,
            settled_sample_score=settled_sample_score,
            recent_calibration_quality_score=item.recent_calibration_quality_score,
            postmortem_completion_score=item.postmortem_completion_score,
            source_reliability_trend_score=item.source_reliability_trend_score,
            specialist_coverage_score=item.specialist_coverage_score,
            readiness_score=readiness_score,
            readiness_status=readiness_status,
            config=config,
        ),
        validation_config=config,
    )


def _readiness_score(
    *,
    settled_sample_score: Decimal,
    recent_calibration_quality_score: Decimal,
    postmortem_completion_score: Decimal,
    source_reliability_trend_score: Decimal,
    specialist_coverage_score: Decimal,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> Decimal:
    return _clamp_ratio(
        settled_sample_score * config.settled_sample_weight
        + recent_calibration_quality_score * config.recent_calibration_quality_weight
        + postmortem_completion_score * config.postmortem_completion_weight
        + source_reliability_trend_score * config.source_reliability_trend_weight
        + specialist_coverage_score * config.specialist_coverage_weight,
    )


def _row_status(
    *,
    settled_sample_count: Decimal,
    readiness_score: Decimal,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> str:
    if (
        settled_sample_count < config.minimum_settled_sample_count
        or readiness_score < config.watch_score_floor
    ):
        return "block"
    if readiness_score < config.pass_score_floor:
        return "watch"
    return "pass"


def _report_status(rows: tuple[TeamCategoryLearningReadinessScore, ...]) -> str:
    if not rows:
        return "block"
    if any(row.readiness_status == "block" for row in rows):
        return "block"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    settled_sample_count: Decimal,
    settled_sample_score: Decimal,
    recent_calibration_quality_score: Decimal,
    postmortem_completion_score: Decimal,
    source_reliability_trend_score: Decimal,
    specialist_coverage_score: Decimal,
    readiness_score: Decimal,
    readiness_status: str,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> tuple[str, ...]:
    reasons = (
        f"team_category_learning_readiness_{readiness_status}",
        _settled_sample_reason(settled_sample_count, settled_sample_score, config),
        _tier_reason(
            recent_calibration_quality_score,
            strong=Decimal("0.850000"),
            watch=Decimal("0.600000"),
            strong_reason="recent_calibration_quality_strong",
            watch_reason="recent_calibration_quality_watch",
            weak_reason="recent_calibration_quality_weak",
        ),
        _tier_reason(
            postmortem_completion_score,
            strong=Decimal("0.900000"),
            watch=Decimal("0.600000"),
            strong_reason="postmortem_completion_complete",
            watch_reason="postmortem_completion_partial",
            weak_reason="postmortem_completion_gap",
        ),
        _tier_reason(
            source_reliability_trend_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.500000"),
            strong_reason="source_reliability_trend_positive",
            watch_reason="source_reliability_trend_flat",
            weak_reason="source_reliability_trend_weak",
        ),
        _tier_reason(
            specialist_coverage_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="specialist_coverage_full",
            watch_reason="specialist_coverage_partial",
            weak_reason="specialist_coverage_thin",
        ),
        _readiness_floor_reason(readiness_score, config),
    )
    return _normalize_reason_codes(
        tuple(reason for reason in reasons if reason is not None),
        _ROW_REASON_CODES,
    )


def _settled_sample_reason(
    settled_sample_count: Decimal,
    settled_sample_score: Decimal,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> str:
    if settled_sample_score >= ONE:
        return "settled_sample_count_full"
    if settled_sample_count >= config.minimum_settled_sample_count:
        return "settled_sample_count_watch"
    return "settled_sample_count_thin"


def _readiness_floor_reason(
    readiness_score: Decimal,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> str | None:
    if readiness_score < config.watch_score_floor:
        return "readiness_score_below_watch"
    if readiness_score < config.pass_score_floor:
        return "readiness_score_below_pass"
    return None


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
    rows: tuple[TeamCategoryLearningReadinessScore, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_category_learning_readiness_empty_inputs",)
    reasons: tuple[str, ...] = ()
    if all(row.readiness_status == "pass" for row in rows):
        reasons += ("team_category_learning_readiness_passed",)
    if any(row.readiness_status == "watch" for row in rows):
        reasons += ("team_category_learning_readiness_watch_rows",)
    if any(row.readiness_status == "block" for row in rows):
        reasons += ("team_category_learning_readiness_block_rows",)
    return _normalize_reason_codes(reasons, _REPORT_REASON_CODES)


def _validate_config(config: TeamCategoryLearningReadinessScoreConfig) -> None:
    weight_sum = (
        config.settled_sample_weight
        + config.recent_calibration_quality_weight
        + config.postmortem_completion_weight
        + config.source_reliability_trend_weight
        + config.specialist_coverage_weight
    ).quantize(SCORE_QUANT)
    if weight_sum != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.target_settled_sample_count <= Decimal("0"):
        raise ValueError("target_settled_sample_count must be positive")
    if config.minimum_settled_sample_count > config.target_settled_sample_count:
        raise ValueError(
            "minimum_settled_sample_count must not exceed target_settled_sample_count",
        )
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _normalize_row_validation_config(
    config: TeamCategoryLearningReadinessScoreConfig | None,
) -> TeamCategoryLearningReadinessScoreConfig:
    if config is None:
        return TeamCategoryLearningReadinessScoreConfig()
    if type(config) is not TeamCategoryLearningReadinessScoreConfig:
        raise ValueError("validation_config must be a TeamCategoryLearningReadinessScoreConfig")
    require_paper_only_flags("team category learning readiness row config", config)
    return config


def _validate_row(
    row: TeamCategoryLearningReadinessScore,
    config: TeamCategoryLearningReadinessScoreConfig,
) -> None:
    expected_score = _readiness_score(
        settled_sample_score=row.settled_sample_score,
        recent_calibration_quality_score=row.recent_calibration_quality_score,
        postmortem_completion_score=row.postmortem_completion_score,
        source_reliability_trend_score=row.source_reliability_trend_score,
        specialist_coverage_score=row.specialist_coverage_score,
        config=config,
    )
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score must match readiness components")
    expected_status = _row_status(
        settled_sample_count=row.settled_sample_count,
        readiness_score=row.readiness_score,
        config=config,
    )
    if row.readiness_status != expected_status:
        raise ValueError("readiness_status must match readiness score")
    expected_reasons = _row_reason_codes(
        settled_sample_count=row.settled_sample_count,
        settled_sample_score=row.settled_sample_score,
        recent_calibration_quality_score=row.recent_calibration_quality_score,
        postmortem_completion_score=row.postmortem_completion_score,
        source_reliability_trend_score=row.source_reliability_trend_score,
        specialist_coverage_score=row.specialist_coverage_score,
        readiness_score=row.readiness_score,
        readiness_status=row.readiness_status,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match readiness inputs")


def _validate_report(report: TeamCategoryLearningReadinessScoreReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: (row.team_id, row.category_id))):
        raise ValueError("rows must be deterministically sorted")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.readiness_status != _report_status(report.rows):
        raise ValueError("readiness_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Sequence[TeamCategoryLearningReadinessScoreInput],
) -> tuple[TeamCategoryLearningReadinessScoreInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    items = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamCategoryLearningReadinessScoreInput:
            raise ValueError(
                "inputs must contain TeamCategoryLearningReadinessScoreInput values",
            )
        require_paper_only_flags("team category learning readiness input", item)
        key = (item.team_id, item.category_id)
        if key in seen:
            raise ValueError("duplicate team/category")
        seen.add(key)
    return items


def _normalize_rows(
    rows: tuple[TeamCategoryLearningReadinessScore, ...],
) -> tuple[TeamCategoryLearningReadinessScore, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain TeamCategoryLearningReadinessScore values")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must contain TeamCategoryLearningReadinessScore values",
        ) from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not TeamCategoryLearningReadinessScore:
            raise ValueError(
                "rows must contain TeamCategoryLearningReadinessScore values",
            )
        require_paper_only_flags("team category learning readiness row", item)
        key = (item.team_id, item.category_id)
        if key in seen:
            raise ValueError("duplicate team/category")
        seen.add(key)
    return items


def _normalize_reason_codes(value: object, allowed: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in allowed:
            raise ValueError("reason_codes must contain known values")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in value)
    if value != expected:
        raise ValueError("reason_codes must be deterministic")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TEAM_CATEGORY_LEARNING_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(COUNT_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    count = _require_nonnegative_count(field_name, value)
    if count <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return count


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = value.quantize(SCORE_QUANT)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _status_count(rows: tuple[TeamCategoryLearningReadinessScore, ...], status: str) -> int:
    return sum(1 for row in rows if row.readiness_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return (sum(values, ZERO) / Decimal(len(values))).quantize(SCORE_QUANT)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload values must be exactly Decimal")
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(value: Any) -> None:
    if type(value) is dict:
        if _requires_payload_phase_flags(value):
            for phase_flag in _PHASE_FLAG_FIELDS:
                if value.get(phase_flag) is not True:
                    raise ValueError(f"{phase_flag} must be True for public payload")
        for field_name, item in value.items():
            if type(field_name) is not str:
                raise ValueError("payload field names must be strings")
            if field_name in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{field_name} must be True for public payload")
            field_text = field_name.casefold()
            if _has_unsafe_public_payload_fragment(field_text):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif type(value) is str and _has_unsafe_public_payload_fragment(value.casefold()):
        raise ValueError("unsafe public payload value")


def _has_unsafe_public_payload_fragment(value: str) -> bool:
    return any(fragment in value for fragment in _PAYLOAD_FIELD_DENY_FRAGMENTS)


def _requires_payload_phase_flags(value: dict[Any, Any]) -> bool:
    return any(field_name in value for field_name in _PHASE_FLAG_FIELDS) or (
        "team_id" in value and "category_id" in value
    )


def _validate_public_payload_taxonomy_labels(value: Any) -> None:
    if type(value) is dict:
        has_team_id = "team_id" in value
        has_category_id = "category_id" in value
        if has_team_id and has_category_id:
            require_team_category_pair(
                "team_id",
                value["team_id"],
                "category_id",
                value["category_id"],
            )
        elif has_team_id:
            require_team_id("team_id", value["team_id"])
        elif has_category_id:
            require_category_id("category_id", value["category_id"])
        for item in value.values():
            _validate_public_payload_taxonomy_labels(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_public_payload_taxonomy_labels(item)


def _validate_public_payload_status_vocabulary(value: Any) -> None:
    if type(value) is dict:
        for field_name, item in value.items():
            if field_name == "status" or field_name.endswith("_status"):
                _require_status(field_name, item)
            elif field_name == "reason_codes":
                _validate_public_reason_codes(item)
            _validate_public_payload_status_vocabulary(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_public_payload_status_vocabulary(item)


def _validate_public_reason_codes(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("reason_codes must be a list")
    if not value:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    expected = [
        reason_code
        for reason_code in TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES
        if reason_code in value
    ]
    if value != expected:
        raise ValueError("reason_codes must be deterministic")
