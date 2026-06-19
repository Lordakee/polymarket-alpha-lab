"""Pure paper-only reducer for supplied recommendation report stages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationPipelineReport",
    "PaperRecommendationPipelineStage",
    "build_paper_recommendation_pipeline_report",
)


STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperRecommendationPipelineStage:
    stage_name: str
    status: str
    message: str
    input_count: int
    output_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("stage_name", self.stage_name)
        _require_status("status", self.status)
        _require_canonical_string("message", self.message)
        _require_nonnegative_int("input_count", self.input_count)
        _require_nonnegative_int("output_count", self.output_count)
        _require_hard_flags("pipeline stage", self)


@dataclass(frozen=True)
class PaperRecommendationPipelineReport:
    generated_at: datetime
    config_version: str
    stage_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    stages: tuple[PaperRecommendationPipelineStage, ...]
    final_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("stage_count", self.stage_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        object.__setattr__(self, "stages", _normalize_stages(self.stages))
        _require_status("final_status", self.final_status)
        _validate_report_consistency(self)
        _require_hard_flags("pipeline report", self)


def build_paper_recommendation_pipeline_report(
    *,
    generated_at: datetime,
    config_version: str,
    stages: tuple[object, ...] | list[object],
) -> PaperRecommendationPipelineReport:
    generated_at = _as_utc(generated_at)
    _require_canonical_string("config_version", config_version)
    normalized_stages = _normalize_supplied_stages(stages)
    pass_count = _status_count(normalized_stages, "pass")
    watch_count = _status_count(normalized_stages, "watch")
    blocked_count = _status_count(normalized_stages, "blocked")

    return PaperRecommendationPipelineReport(
        generated_at=generated_at,
        config_version=config_version,
        stage_count=_decimal_to_int(_decimal_len(normalized_stages)),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        stages=normalized_stages,
        final_status=_final_status(
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
    )


def _normalize_supplied_stages(
    stages: tuple[object, ...] | list[object],
) -> tuple[PaperRecommendationPipelineStage, ...]:
    if isinstance(stages, (str, bytes)):
        raise ValueError("stages must be an iterable")
    try:
        values = tuple(stages)
    except TypeError as exc:
        raise ValueError("stages must be an iterable") from exc
    return tuple(_coerce_stage(value) for value in values)


def _coerce_stage(value: object) -> PaperRecommendationPipelineStage:
    if type(value) is PaperRecommendationPipelineStage:
        _require_hard_flags("pipeline stage", value)
        return value
    return PaperRecommendationPipelineStage(
        stage_name=_required_attr(value, "stage_name"),
        status=_required_attr(value, "status"),
        message=_required_attr(value, "message"),
        input_count=_required_attr(value, "input_count"),
        output_count=_required_attr(value, "output_count"),
        paper_only=_required_attr(value, "paper_only"),
        report_only=_required_attr(value, "report_only"),
        readonly=_required_attr(value, "readonly"),
    )


def _normalize_stages(
    stages: tuple[PaperRecommendationPipelineStage, ...],
) -> tuple[PaperRecommendationPipelineStage, ...]:
    if isinstance(stages, (str, bytes)):
        raise ValueError("stages must be an iterable")
    try:
        values = tuple(stages)
    except TypeError as exc:
        raise ValueError("stages must be an iterable") from exc
    for value in values:
        if type(value) is not PaperRecommendationPipelineStage:
            raise ValueError("stages must contain pipeline stages")
        _require_hard_flags("pipeline stage", value)
    return values


def _status_count(
    stages: tuple[PaperRecommendationPipelineStage, ...],
    status: str,
) -> int:
    count = ZERO
    for stage in stages:
        if stage.status == status:
            count += ONE
    return _decimal_to_int(count)


def _decimal_len(values: tuple[object, ...]) -> Decimal:
    count = ZERO
    for _value in values:
        count += ONE
    return count


def _decimal_to_int(value: Decimal) -> int:
    return int(value)


def _final_status(*, watch_count: int, blocked_count: int) -> str:
    if Decimal(blocked_count) > ZERO:
        return "blocked"
    if Decimal(watch_count) > ZERO:
        return "watch"
    return "pass"


def _validate_report_consistency(report: PaperRecommendationPipelineReport) -> None:
    if report.stage_count != _decimal_to_int(_decimal_len(report.stages)):
        raise ValueError("stage_count must match stages")
    if report.pass_count != _status_count(report.stages, "pass"):
        raise ValueError("pass_count must match stages")
    if report.watch_count != _status_count(report.stages, "watch"):
        raise ValueError("watch_count must match stages")
    if report.blocked_count != _status_count(report.stages, "blocked"):
        raise ValueError("blocked_count must match stages")
    total_status_count = (
        Decimal(report.pass_count)
        + Decimal(report.watch_count)
        + Decimal(report.blocked_count)
    )
    if Decimal(report.stage_count) != total_status_count:
        raise ValueError("stage_count must match status counts")
    if report.final_status != _final_status(
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("final_status must match stage statuses")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if Decimal(value) < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
