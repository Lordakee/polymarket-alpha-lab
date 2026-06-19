from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperRecommendationPipelineTrendReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    first_generated_at: datetime
    last_generated_at: datetime
    average_stage_count: Decimal
    blocked_share: Decimal
    latest_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_utc(self.first_generated_at),
        )
        object.__setattr__(self, "last_generated_at", _as_utc(self.last_generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("source_report_count", self.source_report_count)
        for field_name in ("pass_count", "watch_count", "blocked_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "average_stage_count",
            _normalize_nonnegative_decimal(
                "average_stage_count",
                self.average_stage_count,
            ),
        )
        object.__setattr__(
            self,
            "blocked_share",
            _normalize_probability("blocked_share", self.blocked_share),
        )
        _require_status("latest_status", self.latest_status)
        _require_hard_flags("trend report", self)
        _validate_trend_report_consistency(self)


def build_paper_recommendation_pipeline_trend_report(
    *,
    generated_at: datetime,
    config_version: str,
    reports: object,
) -> PaperRecommendationPipelineTrendReport:
    generated_at = _as_utc(generated_at)
    _require_canonical_string("config_version", config_version)
    source_reports = _normalize_reports(reports)
    source_report_count = len(source_reports)
    stage_count_total = sum(report.stage_count for report in source_reports)
    blocked_count = _status_count(source_reports, "blocked")
    generated_ats = tuple(report.generated_at for report in source_reports)
    latest_index = _latest_report_index(source_reports)

    return PaperRecommendationPipelineTrendReport(
        generated_at=generated_at,
        config_version=config_version,
        source_report_count=source_report_count,
        pass_count=_status_count(source_reports, "pass"),
        watch_count=_status_count(source_reports, "watch"),
        blocked_count=blocked_count,
        first_generated_at=min(generated_ats),
        last_generated_at=max(generated_ats),
        average_stage_count=_quantize(
            Decimal(stage_count_total) / Decimal(source_report_count),
        ),
        blocked_share=_quantize(Decimal(blocked_count) / Decimal(source_report_count)),
        latest_status=source_reports[latest_index].final_status,
    )


@dataclass(frozen=True)
class _SourceReport:
    generated_at: datetime
    final_status: str
    stage_count: int


def _normalize_reports(reports: object) -> tuple[_SourceReport, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable")
    try:
        items = tuple(reports)
    except TypeError as exc:
        raise ValueError("reports must be an iterable") from exc
    if not items:
        raise ValueError("reports must contain at least one value")
    return tuple(_coerce_report(item) for item in items)


def _coerce_report(value: object) -> _SourceReport:
    stage_count = _required_stage_count(value)
    final_status = _required_attr(value, "final_status")
    generated_at = _required_attr(value, "generated_at")
    _require_status("final_status", final_status)
    _require_hard_flags("source report", value)
    return _SourceReport(
        generated_at=_as_utc(generated_at),
        final_status=final_status,
        stage_count=stage_count,
    )


def _required_stage_count(value: object) -> int:
    if hasattr(value, "stage_count"):
        stage_count = getattr(value, "stage_count")
        field_name = "stage_count"
    elif hasattr(value, "artifact_count"):
        stage_count = getattr(value, "artifact_count")
        field_name = "artifact_count"
    else:
        raise ValueError("stage_count is required")
    _require_nonnegative_int(field_name, stage_count)
    return stage_count


def _status_count(reports: tuple[_SourceReport, ...], status: str) -> int:
    return sum(1 for report in reports if report.final_status == status)


def _latest_report_index(reports: tuple[_SourceReport, ...]) -> int:
    latest_index = 0
    latest_generated_at = reports[0].generated_at
    for index, report in enumerate(reports[1:], start=1):
        if report.generated_at >= latest_generated_at:
            latest_index = index
            latest_generated_at = report.generated_at
    return latest_index


def _validate_trend_report_consistency(
    report: PaperRecommendationPipelineTrendReport,
) -> None:
    if report.source_report_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("source_report_count must match status counts")
    if report.first_generated_at > report.last_generated_at:
        raise ValueError("first_generated_at must not be after last_generated_at")
    expected_blocked_share = _quantize(
        Decimal(report.blocked_count) / Decimal(report.source_report_count),
    )
    if report.blocked_share != expected_blocked_share:
        raise ValueError("blocked_share must match blocked_count and source_report_count")


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
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)
