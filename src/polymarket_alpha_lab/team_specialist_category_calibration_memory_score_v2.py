"""Phase 1 readonly team specialist category calibration memory score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_TEAM_SPECIALIST_CATEGORY_CALIBRATION_MEMORY_SCORE_V2_CONFIG_VERSION = (
    "team-specialist-category-calibration-memory-score-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_MEMORY_STATUSES = frozenset(("pass", "watch", "blocked"))
_UNSAFE_PUBLIC_TERMS = (
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
_ROW_REASON_CODE_SEQUENCE = (
    "category_calibration_memory_pass",
    "category_calibration_memory_watch",
    "category_calibration_memory_blocked",
    "prior_forecast_depth_full",
    "prior_forecast_depth_watch",
    "prior_forecast_depth_thin",
    "brier_error_low",
    "brier_error_watch",
    "brier_error_high",
    "stale_sources_clear",
    "stale_sources_watch",
    "stale_sources_stale",
    "evidence_complete",
    "evidence_partial",
    "evidence_gap",
    "postmortem_replay_fresh",
    "postmortem_replay_watch",
    "postmortem_replay_stale",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "empty_category_calibration_memory_records",
    "category_calibration_memory_score_passed",
    "category_calibration_memory_score_watch_rows",
    "category_calibration_memory_score_blocked_rows",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CATEGORY_CALIBRATION_MEMORY_SCORE_V2_CONFIG_VERSION",
    "TeamSpecialistCategoryCalibrationMemoryScoreV2Config",
    "TeamSpecialistCategoryCalibrationMemoryScoreV2Input",
    "TeamSpecialistCategoryCalibrationMemoryScoreV2Row",
    "TeamSpecialistCategoryCalibrationMemoryScoreV2Report",
    "build_team_specialist_category_calibration_memory_score_v2_report",
    "team_specialist_category_calibration_memory_score_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistCategoryCalibrationMemoryScoreV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CATEGORY_CALIBRATION_MEMORY_SCORE_V2_CONFIG_VERSION
    )
    prior_forecast_depth_weight: Decimal = Decimal("0.200000")
    brier_quality_weight: Decimal = Decimal("0.350000")
    stale_source_health_weight: Decimal = Decimal("0.150000")
    evidence_completeness_weight: Decimal = Decimal("0.200000")
    postmortem_replay_recency_weight: Decimal = Decimal("0.100000")
    max_prior_forecast_count: Decimal = Decimal("20.000000")
    max_brier_like_error: Decimal = Decimal("0.250000")
    max_stale_source_incident_count: Decimal = Decimal("5.000000")
    max_postmortem_replay_age_days: Decimal = Decimal("30.000000")
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryCalibrationMemoryScoreV2Config:
            raise TypeError(
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Config "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Config:
            raise ValueError(
                "config must be exactly "
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_CALIBRATION_MEMORY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "prior_forecast_depth_weight",
            "brier_quality_weight",
            "stale_source_health_weight",
            "evidence_completeness_weight",
            "postmortem_replay_recency_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_prior_forecast_count",
            "max_brier_like_error",
            "max_stale_source_incident_count",
            "max_postmortem_replay_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryCalibrationMemoryScoreV2Input:
    team_id: str
    specialist_id: str
    category_id: str
    prior_forecast_count: Decimal
    realized_brier_like_error: Decimal
    stale_source_incident_count: Decimal
    evidence_completeness_score: Decimal
    postmortem_replay_age_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryCalibrationMemoryScoreV2Input:
            raise TypeError(
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Input "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Input:
            raise ValueError(
                "memory must be exactly "
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Input",
            )
        for field_name in ("team_id", "specialist_id", "category_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "prior_forecast_count",
            _require_nonnegative_decimal(
                "prior_forecast_count",
                self.prior_forecast_count,
            ),
        )
        object.__setattr__(
            self,
            "realized_brier_like_error",
            _require_ratio_decimal(
                "realized_brier_like_error",
                self.realized_brier_like_error,
            ),
        )
        object.__setattr__(
            self,
            "stale_source_incident_count",
            _require_nonnegative_decimal(
                "stale_source_incident_count",
                self.stale_source_incident_count,
            ),
        )
        object.__setattr__(
            self,
            "evidence_completeness_score",
            _require_ratio_decimal(
                "evidence_completeness_score",
                self.evidence_completeness_score,
            ),
        )
        object.__setattr__(
            self,
            "postmortem_replay_age_days",
            _require_nonnegative_decimal(
                "postmortem_replay_age_days",
                self.postmortem_replay_age_days,
            ),
        )
        _require_hard_flags("memory", self)
        _reject_unsafe_public_payload("memory", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryCalibrationMemoryScoreV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    category_id: str
    prior_forecast_count: Decimal
    prior_forecast_depth_score: Decimal
    realized_brier_like_error: Decimal
    brier_quality_score: Decimal
    stale_source_incident_count: Decimal
    stale_source_health_score: Decimal
    evidence_completeness_score: Decimal
    postmortem_replay_age_days: Decimal
    postmortem_replay_recency_score: Decimal
    memory_score: Decimal
    memory_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryCalibrationMemoryScoreV2Row:
            raise TypeError(
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Row "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Row:
            raise ValueError(
                "row must be exactly TeamSpecialistCategoryCalibrationMemoryScoreV2Row",
            )
        for field_name in ("team_id", "specialist_id", "category_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "rank",
            "prior_forecast_count",
            "stale_source_incident_count",
            "postmortem_replay_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "prior_forecast_depth_score",
            "realized_brier_like_error",
            "brier_quality_score",
            "stale_source_health_score",
            "evidence_completeness_score",
            "postmortem_replay_recency_score",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_memory_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryCalibrationMemoryScoreV2Report:
    generated_at: datetime
    config_version: str
    memory_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_memory_score: Decimal
    top_memory_score: Decimal
    bottom_memory_score: Decimal
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryCalibrationMemoryScoreV2Report:
            raise TypeError(
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Report "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Report:
            raise ValueError(
                "report must be exactly "
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_CALIBRATION_MEMORY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_memory_status("memory_status", self.memory_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_score",
            "top_memory_score",
            "bottom_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                _REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCategoryCalibrationMemoryScoreV2Report.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_category_calibration_memory_score_v2_report(
    memories: Sequence[TeamSpecialistCategoryCalibrationMemoryScoreV2Input],
    *,
    generated_at: datetime,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config | None = None,
) -> TeamSpecialistCategoryCalibrationMemoryScoreV2Report:
    if config is None:
        config = TeamSpecialistCategoryCalibrationMemoryScoreV2Config()
    if type(config) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCategoryCalibrationMemoryScoreV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_memories = _normalize_memories(memories)
    rows = _rank_rows(
        tuple(_row_without_rank(memory, config) for memory in normalized_memories),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "memory_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_memory_score": _average(tuple(row.memory_score for row in rows)),
        "top_memory_score": _top_score(rows),
        "bottom_memory_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistCategoryCalibrationMemoryScoreV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_category_calibration_memory_score_v2_payload(
    report: TeamSpecialistCategoryCalibrationMemoryScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistCategoryCalibrationMemoryScoreV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError(
        "report must be a TeamSpecialistCategoryCalibrationMemoryScoreV2Report "
        "or payload",
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


def _row_without_rank(
    memory: TeamSpecialistCategoryCalibrationMemoryScoreV2Input,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> TeamSpecialistCategoryCalibrationMemoryScoreV2Row:
    prior_forecast_depth_score = _clamp_ratio(
        memory.prior_forecast_count / config.max_prior_forecast_count,
    )
    brier_quality_score = _clamp_ratio(
        _ONE - memory.realized_brier_like_error / config.max_brier_like_error,
    )
    stale_source_health_score = _clamp_ratio(
        _ONE
        - memory.stale_source_incident_count / config.max_stale_source_incident_count,
    )
    postmortem_replay_recency_score = _clamp_ratio(
        _ONE - memory.postmortem_replay_age_days / config.max_postmortem_replay_age_days,
    )
    memory_score = _score(
        prior_forecast_depth_score=prior_forecast_depth_score,
        brier_quality_score=brier_quality_score,
        stale_source_health_score=stale_source_health_score,
        evidence_completeness_score=memory.evidence_completeness_score,
        postmortem_replay_recency_score=postmortem_replay_recency_score,
        config=config,
    )
    memory_status = _row_status(memory_score, config)
    return TeamSpecialistCategoryCalibrationMemoryScoreV2Row(
        rank=_ZERO,
        team_id=memory.team_id,
        specialist_id=memory.specialist_id,
        category_id=memory.category_id,
        prior_forecast_count=memory.prior_forecast_count,
        prior_forecast_depth_score=prior_forecast_depth_score,
        realized_brier_like_error=memory.realized_brier_like_error,
        brier_quality_score=brier_quality_score,
        stale_source_incident_count=memory.stale_source_incident_count,
        stale_source_health_score=stale_source_health_score,
        evidence_completeness_score=memory.evidence_completeness_score,
        postmortem_replay_age_days=memory.postmortem_replay_age_days,
        postmortem_replay_recency_score=postmortem_replay_recency_score,
        memory_score=memory_score,
        memory_status=memory_status,
        reason_codes=_row_reason_codes(
            prior_forecast_depth_score=prior_forecast_depth_score,
            realized_brier_like_error=memory.realized_brier_like_error,
            stale_source_incident_count=memory.stale_source_incident_count,
            evidence_completeness_score=memory.evidence_completeness_score,
            postmortem_replay_age_days=memory.postmortem_replay_age_days,
            memory_status=memory_status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...]:
    ranked_rows = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                -item.memory_score,
                item.realized_brier_like_error,
                item.team_id,
                item.specialist_id,
                item.category_id,
            ),
        ),
        start=1,
    ):
        ranked_rows.append(replace(row, rank=_decimal_count(index)))
    return tuple(ranked_rows)


def _score(
    *,
    prior_forecast_depth_score: Decimal,
    brier_quality_score: Decimal,
    stale_source_health_score: Decimal,
    evidence_completeness_score: Decimal,
    postmortem_replay_recency_score: Decimal,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> Decimal:
    return _clamp_ratio(
        prior_forecast_depth_score * config.prior_forecast_depth_weight
        + brier_quality_score * config.brier_quality_weight
        + stale_source_health_score * config.stale_source_health_weight
        + evidence_completeness_score * config.evidence_completeness_weight
        + postmortem_replay_recency_score * config.postmortem_replay_recency_weight,
    )


def _row_status(
    memory_score: Decimal,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> str:
    if memory_score >= config.pass_score_floor:
        return "pass"
    if memory_score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _report_status(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.memory_status == "blocked" for row in rows):
        return "blocked"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    prior_forecast_depth_score: Decimal,
    realized_brier_like_error: Decimal,
    stale_source_incident_count: Decimal,
    evidence_completeness_score: Decimal,
    postmortem_replay_age_days: Decimal,
    memory_status: str,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"category_calibration_memory_{memory_status}",
            _tier_reason(
                prior_forecast_depth_score,
                strong=Decimal("1.000000"),
                watch=Decimal("0.500000"),
                strong_reason="prior_forecast_depth_full",
                watch_reason="prior_forecast_depth_watch",
                weak_reason="prior_forecast_depth_thin",
            ),
            _error_reason(realized_brier_like_error),
            _incident_reason(stale_source_incident_count, config),
            _tier_reason(
                evidence_completeness_score,
                strong=Decimal("0.800000"),
                watch=Decimal("0.600000"),
                strong_reason="evidence_complete",
                watch_reason="evidence_partial",
                weak_reason="evidence_gap",
            ),
            _age_reason(postmortem_replay_age_days, config),
        ),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_category_calibration_memory_records",)
    reason_codes: list[str] = []
    if all(row.memory_status == "pass" for row in rows):
        reason_codes.append("category_calibration_memory_score_passed")
    if any(row.memory_status == "watch" for row in rows):
        reason_codes.append("category_calibration_memory_score_watch_rows")
    if any(row.memory_status == "blocked" for row in rows):
        reason_codes.append("category_calibration_memory_score_blocked_rows")
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


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


def _error_reason(value: Decimal) -> str:
    if value <= Decimal("0.050000"):
        return "brier_error_low"
    if value <= Decimal("0.120000"):
        return "brier_error_watch"
    return "brier_error_high"


def _incident_reason(
    value: Decimal,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> str:
    if value <= _ZERO:
        return "stale_sources_clear"
    if value < config.max_stale_source_incident_count:
        return "stale_sources_watch"
    return "stale_sources_stale"


def _age_reason(
    value: Decimal,
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> str:
    if value <= Decimal("7.000000"):
        return "postmortem_replay_fresh"
    if value < config.max_postmortem_replay_age_days:
        return "postmortem_replay_watch"
    return "postmortem_replay_stale"


def _status_count(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.memory_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _top_score(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.memory_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.memory_score for row in rows)


def _validate_config(
    config: TeamSpecialistCategoryCalibrationMemoryScoreV2Config,
) -> None:
    weights_total = _quantize(
        config.prior_forecast_depth_weight
        + config.brier_quality_weight
        + config.stale_source_health_weight
        + config.evidence_completeness_weight
        + config.postmortem_replay_recency_weight,
    )
    if weights_total != _ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistCategoryCalibrationMemoryScoreV2Row,
) -> None:
    if row.rank < _ZERO:
        raise ValueError("rank must be nonnegative")
    if row.memory_status == "pass" and "category_calibration_memory_pass" not in row.reason_codes:
        raise ValueError("pass rows must include category_calibration_memory_pass")
    if row.memory_status == "watch" and "category_calibration_memory_watch" not in row.reason_codes:
        raise ValueError("watch rows must include category_calibration_memory_watch")
    if (
        row.memory_status == "blocked"
        and "category_calibration_memory_blocked" not in row.reason_codes
    ):
        raise ValueError("blocked rows must include category_calibration_memory_blocked")


def _validate_report_consistency(
    report: TeamSpecialistCategoryCalibrationMemoryScoreV2Report,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_memory_score != _average(tuple(row.memory_score for row in rows)):
        raise ValueError("average_memory_score must match rows")
    if report.top_memory_score != _top_score(rows):
        raise ValueError("top_memory_score must match rows")
    if report.bottom_memory_score != _bottom_score(rows):
        raise ValueError("bottom_memory_score must match rows")
    if report.memory_status != _report_status(rows):
        raise ValueError("memory_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_sorted(rows)


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.memory_score,
                row.realized_brier_like_error,
                row.team_id,
                row.specialist_id,
                row.category_id,
            ),
        ),
    )
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


def _normalize_memories(
    memories: Sequence[TeamSpecialistCategoryCalibrationMemoryScoreV2Input],
) -> tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Input, ...]:
    if isinstance(memories, (str, bytes)) or not isinstance(memories, Sequence):
        raise ValueError("memories must be a sequence")
    normalized: list[TeamSpecialistCategoryCalibrationMemoryScoreV2Input] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for memory in memories:
        if type(memory) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Input:
            raise ValueError(
                "memories must contain "
                "TeamSpecialistCategoryCalibrationMemoryScoreV2Input",
            )
        key = (memory.team_id, memory.specialist_id, memory.category_id)
        if key in seen_keys:
            raise ValueError("duplicate team/specialist/category memory")
        seen_keys.add(key)
        normalized.append(memory)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.team_id, item.specialist_id, item.category_id),
        ),
    )


def _normalize_rows(
    rows: Sequence[TeamSpecialistCategoryCalibrationMemoryScoreV2Row],
) -> tuple[TeamSpecialistCategoryCalibrationMemoryScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistCategoryCalibrationMemoryScoreV2Row] = []
    for row in rows:
        if type(row) is not TeamSpecialistCategoryCalibrationMemoryScoreV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCategoryCalibrationMemoryScoreV2Row",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.rank))


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _require_memory_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be a known memory status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: TeamSpecialistCategoryCalibrationMemoryScoreV2Report,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    value = _json_ready(value) if not allow_json_containers else value
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has unsafe public field")
            _reject_unsafe_public_key(key, label)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is float:
        raise ValueError(f"{label} must not contain float values")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
