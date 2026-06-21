from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperRecommendationCycleSnapshotTrendReport:
    generated_at: datetime
    config_version: str
    snapshot_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    first_generated_at: datetime
    last_generated_at: datetime
    latest_status: str
    stage_count_total: int
    artifact_count_total: int
    blocked_share: Decimal
    watch_share: Decimal
    average_stage_count: Decimal
    average_artifact_count: Decimal
    reason_code_counts: tuple[tuple[str, int], ...] = ()
    latest_reason_codes: tuple[str, ...] = ()
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
        _require_positive_int("snapshot_count", self.snapshot_count)
        for field_name in (
            "pass_count",
            "watch_count",
            "blocked_count",
            "stage_count_total",
            "artifact_count_total",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_status("latest_status", self.latest_status)
        object.__setattr__(
            self,
            "blocked_share",
            _normalize_probability("blocked_share", self.blocked_share),
        )
        object.__setattr__(
            self,
            "watch_share",
            _normalize_probability("watch_share", self.watch_share),
        )
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
            "average_artifact_count",
            _normalize_nonnegative_decimal(
                "average_artifact_count",
                self.average_artifact_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _validate_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "latest_reason_codes",
            _validate_latest_reason_codes(self.latest_reason_codes),
        )
        _require_hard_flags("trend report", self)
        _validate_trend_report_consistency(self)


def build_paper_recommendation_cycle_snapshot_trend_report(
    *,
    generated_at: datetime,
    config_version: str,
    snapshots: object,
) -> PaperRecommendationCycleSnapshotTrendReport:
    generated_at = _as_utc(generated_at)
    _require_canonical_string("config_version", config_version)
    source_snapshots = _normalize_snapshots(snapshots)
    snapshot_count = len(source_snapshots)
    stage_count_total = sum(snapshot.stage_count for snapshot in source_snapshots)
    artifact_count_total = sum(snapshot.artifact_count for snapshot in source_snapshots)
    pass_count = _status_count(source_snapshots, "pass")
    watch_count = _status_count(source_snapshots, "watch")
    blocked_count = _status_count(source_snapshots, "blocked")
    generated_ats = tuple(snapshot.generated_at for snapshot in source_snapshots)
    latest_index = _latest_snapshot_index(source_snapshots)
    reason_code_counts = _reason_code_counts(source_snapshots)

    return PaperRecommendationCycleSnapshotTrendReport(
        generated_at=generated_at,
        config_version=config_version,
        snapshot_count=snapshot_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        first_generated_at=min(generated_ats),
        last_generated_at=max(generated_ats),
        latest_status=source_snapshots[latest_index].final_status,
        stage_count_total=stage_count_total,
        artifact_count_total=artifact_count_total,
        blocked_share=_quantize(Decimal(blocked_count) / Decimal(snapshot_count)),
        watch_share=_quantize(Decimal(watch_count) / Decimal(snapshot_count)),
        average_stage_count=_quantize(
            Decimal(stage_count_total) / Decimal(snapshot_count),
        ),
        average_artifact_count=_quantize(
            Decimal(artifact_count_total) / Decimal(snapshot_count),
        ),
        reason_code_counts=reason_code_counts,
        latest_reason_codes=source_snapshots[latest_index].reason_codes,
    )


@dataclass(frozen=True)
class _SourceSnapshot:
    generated_at: datetime
    final_status: str
    stage_count: int
    artifact_count: int
    reason_codes: tuple[str, ...]


def _normalize_snapshots(snapshots: object) -> tuple[_SourceSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        items = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    if not items:
        raise ValueError("snapshots must contain at least one value")
    return tuple(_coerce_snapshot(item) for item in items)


def _coerce_snapshot(value: object) -> _SourceSnapshot:
    stage_count = _required_attr(value, "stage_count")
    artifact_count = _required_attr(value, "artifact_count")
    generated_at = _required_attr(value, "generated_at")
    final_status = _required_attr(value, "final_status")
    _require_status("final_status", final_status)
    _require_nonnegative_int("stage_count", stage_count)
    _require_nonnegative_int("artifact_count", artifact_count)
    _require_hard_flags("source snapshot", value)
    reason_codes: tuple[str, ...] = ()
    if hasattr(value, "reason_codes"):
        reason_codes = _normalize_source_reason_codes(getattr(value, "reason_codes"))
    return _SourceSnapshot(
        generated_at=_as_utc(generated_at),
        final_status=final_status,
        stage_count=stage_count,
        artifact_count=artifact_count,
        reason_codes=reason_codes,
    )


def _status_count(snapshots: tuple[_SourceSnapshot, ...], status: str) -> int:
    return sum(1 for snapshot in snapshots if snapshot.final_status == status)


def _reason_code_counts(
    snapshots: tuple[_SourceSnapshot, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for snapshot in snapshots:
        for reason_code in snapshot.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple((reason_code, counts[reason_code]) for reason_code in sorted(counts))


def _normalize_source_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in items:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(items)))


def _latest_snapshot_index(snapshots: tuple[_SourceSnapshot, ...]) -> int:
    latest_index = 0
    latest_generated_at = snapshots[0].generated_at
    for index, snapshot in enumerate(snapshots[1:], start=1):
        if snapshot.generated_at >= latest_generated_at:
            latest_index = index
            latest_generated_at = snapshot.generated_at
    return latest_index


def _validate_trend_report_consistency(
    report: PaperRecommendationCycleSnapshotTrendReport,
) -> None:
    if report.snapshot_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("snapshot_count must match status counts")
    if report.first_generated_at > report.last_generated_at:
        raise ValueError("first_generated_at must not be after last_generated_at")
    expected_blocked_share = _quantize(
        Decimal(report.blocked_count) / Decimal(report.snapshot_count),
    )
    if report.blocked_share != expected_blocked_share:
        raise ValueError("blocked_share must match blocked_count and snapshot_count")
    expected_watch_share = _quantize(
        Decimal(report.watch_count) / Decimal(report.snapshot_count),
    )
    if report.watch_share != expected_watch_share:
        raise ValueError("watch_share must match watch_count and snapshot_count")
    expected_average_stage_count = _quantize(
        Decimal(report.stage_count_total) / Decimal(report.snapshot_count),
    )
    if report.average_stage_count != expected_average_stage_count:
        raise ValueError(
            "average_stage_count must match stage_count_total and snapshot_count",
        )
    expected_average_artifact_count = _quantize(
        Decimal(report.artifact_count_total) / Decimal(report.snapshot_count),
    )
    if report.average_artifact_count != expected_average_artifact_count:
        raise ValueError(
            "average_artifact_count must match artifact_count_total and snapshot_count",
        )


def _validate_reason_code_counts(value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, int]] = []
    previous_reason_code: str | None = None
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("reason_code_counts must contain exact pairs")
        reason_code, count = pair
        _require_canonical_string("reason_code_counts", reason_code)
        _require_nonnegative_int("reason_code_counts", count)
        if previous_reason_code is not None and reason_code <= previous_reason_code:
            raise ValueError("reason_code_counts must be sorted by unique reason code")
        previous_reason_code = reason_code
        normalized.append((reason_code, count))
    return tuple(normalized)


def _validate_latest_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("latest_reason_codes must be a tuple")
    normalized: list[str] = []
    previous_reason_code: str | None = None
    for reason_code in value:
        _require_canonical_string("latest_reason_codes", reason_code)
        if previous_reason_code is not None and reason_code <= previous_reason_code:
            raise ValueError("latest_reason_codes must be sorted unique reason codes")
        previous_reason_code = reason_code
        normalized.append(reason_code)
    return tuple(normalized)


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


__all__ = (
    "PaperRecommendationCycleSnapshotTrendReport",
    "build_paper_recommendation_cycle_snapshot_trend_report",
)
