"""Pure paper recommendation reason-code trend reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


ZERO = Decimal("0")
QUEUE_ACTION_STATUSES = ("recommend", "watch", "reject")
QUEUE_STATUS_STATUSES = ("queued", "deferred", "blocked")
ALLOCATION_STATUSES = ("allocated", "zero")
READINESS_STATUSES = ("ready", "watch", "blocked")
SOURCE_STATUSES = (
    *QUEUE_ACTION_STATUSES,
    *QUEUE_STATUS_STATUSES,
    *ALLOCATION_STATUSES,
    *READINESS_STATUSES,
)
REASON_CODE_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class PaperRecommendationReasonTrendConfig:
    config_version: str
    window_size: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("window_size", self.window_size)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationReasonTrendRow:
    reason_code: str
    source_status: str
    count: int
    first_seen_at: datetime
    latest_seen_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        _require_source_status("source_status", self.source_status)
        _require_positive_int("count", self.count)
        object.__setattr__(self, "first_seen_at", _as_utc(self.first_seen_at))
        object.__setattr__(self, "latest_seen_at", _as_utc(self.latest_seen_at))
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class PaperRecommendationTransitionTrendRow:
    market_slug: str
    side: str
    from_status: str
    to_status: str
    transition_count: int
    latest_transition_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_source_status("from_status", self.from_status)
        _require_source_status("to_status", self.to_status)
        _require_positive_int("transition_count", self.transition_count)
        object.__setattr__(
            self,
            "latest_transition_at",
            _as_utc(self.latest_transition_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("transition row", self)


@dataclass(frozen=True)
class PaperRecommendationReasonTrendReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    reason_trend_rows: tuple[PaperRecommendationReasonTrendRow, ...]
    transition_trend_rows: tuple[PaperRecommendationTransitionTrendRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "reason_trend_rows",
            _normalize_reason_trend_rows(self.reason_trend_rows),
        )
        object.__setattr__(
            self,
            "transition_trend_rows",
            _normalize_transition_trend_rows(self.transition_trend_rows),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


@dataclass(frozen=True)
class _ObservedRow:
    market_slug: str
    side: str
    source_kind: str
    source_status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class _ObservedReport:
    generated_at: datetime
    rows: tuple[_ObservedRow, ...]


def build_paper_recommendation_reason_trend_report(
    reports: list[object] | tuple[object, ...],
    *,
    config: PaperRecommendationReasonTrendConfig,
    generated_at: datetime,
) -> PaperRecommendationReasonTrendReport:
    if type(config) is not PaperRecommendationReasonTrendConfig:
        raise ValueError("config must be a PaperRecommendationReasonTrendConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_reports = _normalize_reports(reports)
    # Recovered reports are supplied in append sequence; preserve that sequence.
    window_reports = normalized_reports[-config.window_size :]
    return PaperRecommendationReasonTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(window_reports),
        reason_trend_rows=_build_reason_trend_rows(window_reports),
        transition_trend_rows=_build_transition_trend_rows(window_reports),
    )


def _normalize_reports(reports: list[object] | tuple[object, ...]) -> tuple[_ObservedReport, ...]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple")
    normalized_reports = tuple(reports)
    return tuple(_normalize_report(report) for report in normalized_reports)


def _normalize_report(report: object) -> _ObservedReport:
    _require_hard_flags("report", report)
    generated_at = _as_utc(_required_attr(report, "generated_at"))
    rows = _normalize_report_rows(report)
    return _ObservedReport(generated_at=generated_at, rows=rows)


def _normalize_report_rows(report: object) -> tuple[_ObservedRow, ...]:
    raw_rows = _report_rows(report)
    normalized_rows = tuple(_normalize_report_row(row) for row in raw_rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized_rows:
        key = (row.market_slug, row.side, row.source_kind)
        if key in seen_keys:
            raise ValueError("report rows must not contain duplicate market and side rows")
        seen_keys.add(key)
    return normalized_rows


def _report_rows(report: object) -> tuple[object, ...]:
    # Queue reports expose queue_rows; rows is the fallback for allocation/readiness.
    if hasattr(report, "queue_rows"):
        rows = _required_attr(report, "queue_rows")
    elif hasattr(report, "rows"):
        rows = _required_attr(report, "rows")
    else:
        raise ValueError("reports must contain report-like values")
    if isinstance(rows, (str, bytes)):
        raise ValueError("report rows must be iterable")
    try:
        return tuple(rows)
    except TypeError as exc:
        raise ValueError("report rows must be iterable") from exc


def _normalize_report_row(row: object) -> _ObservedRow:
    _require_hard_flags("row", row)
    market_slug = _required_attr(row, "market_slug")
    side = _required_attr(row, "side")
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        _required_attr(row, "reason_codes"),
    )
    source_kind, source_status = _source_kind_and_status(row)
    return _ObservedRow(
        market_slug=_require_canonical_string("market_slug", market_slug),
        side=_require_side("side", side),
        source_kind=source_kind,
        source_status=source_status,
        reason_codes=reason_codes,
    )


def _source_kind_and_status(row: object) -> tuple[str, str]:
    # Precedence matters because allocation rows also carry an action field.
    if hasattr(row, "queue_status"):
        return "queue", _require_queue_status("queue_status", _required_attr(row, "queue_status"))
    if hasattr(row, "allocated_paper_notional"):
        return "allocation", _allocation_status(
            _required_attr(row, "allocated_paper_notional"),
        )
    if hasattr(row, "readiness_status"):
        return "readiness", _require_readiness_status(
            "readiness_status",
            _required_attr(row, "readiness_status"),
        )
    if hasattr(row, "action"):
        return "action", _require_action("action", _required_attr(row, "action"))
    raise ValueError("report rows must include a known status field")


def _build_reason_trend_rows(
    reports: tuple[_ObservedReport, ...],
) -> tuple[PaperRecommendationReasonTrendRow, ...]:
    counts: dict[tuple[str, str], tuple[int, datetime, datetime]] = {}
    for report in reports:
        for row in report.rows:
            for reason_code in row.reason_codes:
                key = (reason_code, row.source_status)
                entry = counts.get(key)
                if entry is None:
                    counts[key] = (1, report.generated_at, report.generated_at)
                else:
                    count, first_seen_at, _latest_seen_at = entry
                    counts[key] = (count + 1, first_seen_at, report.generated_at)
    return tuple(
        PaperRecommendationReasonTrendRow(
            reason_code=reason_code,
            source_status=source_status,
            count=count,
            first_seen_at=first_seen_at,
            latest_seen_at=latest_seen_at,
        )
        for (reason_code, source_status), (count, first_seen_at, latest_seen_at) in sorted(
            counts.items(),
            key=lambda item: (-item[1][0], item[0][0], item[0][1]),
        )
    )


def _build_transition_trend_rows(
    reports: tuple[_ObservedReport, ...],
) -> tuple[PaperRecommendationTransitionTrendRow, ...]:
    transition_counts: dict[tuple[str, str, str, str], tuple[int, datetime, tuple[str, ...]]] = {}
    previous_states: dict[tuple[str, str, str], tuple[str, tuple[str, ...]]] = {}

    for report in reports:
        current_states: dict[tuple[str, str, str], tuple[str, tuple[str, ...]]] = {}
        for row in report.rows:
            key = (row.market_slug, row.side, row.source_kind)
            if key in current_states:
                raise ValueError("report rows must not contain duplicate market and side rows")
            current_states[key] = (row.source_status, row.reason_codes)
            previous_state = previous_states.get(key)
            if previous_state is None:
                continue
            previous_status, _previous_reason_codes = previous_state
            if previous_status == row.source_status:
                continue
            transition_key = (
                row.market_slug,
                row.side,
                previous_status,
                row.source_status,
            )
            entry = transition_counts.get(transition_key)
            if entry is None:
                transition_counts[transition_key] = (
                    1,
                    report.generated_at,
                    row.reason_codes,
                )
            else:
                count, _latest_transition_at, reason_codes = entry
                transition_counts[transition_key] = (
                    count + 1,
                    report.generated_at,
                    _merge_reason_codes(reason_codes, row.reason_codes),
                )
        previous_states.update(current_states)

    return tuple(
        PaperRecommendationTransitionTrendRow(
            market_slug=market_slug,
            side=side,
            from_status=from_status,
            to_status=to_status,
            transition_count=count,
            latest_transition_at=latest_transition_at,
            reason_codes=reason_codes,
        )
        for (
            market_slug,
            side,
            from_status,
            to_status,
        ), (
            count,
            latest_transition_at,
            reason_codes,
        ) in sorted(
            transition_counts.items(),
            key=lambda item: (
                -item[1][0],
                item[0][0],
                item[0][1],
                item[0][2],
                item[0][3],
            ),
        )
    )


def _normalize_reason_trend_rows(
    rows: tuple[PaperRecommendationReasonTrendRow, ...],
) -> tuple[PaperRecommendationReasonTrendRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_trend_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_trend_rows must be an iterable") from exc
    rebuilt = tuple(_normalize_reason_trend_row(row) for row in normalized)
    if rebuilt != tuple(sorted(rebuilt, key=_reason_row_sort_key)):
        raise ValueError("reason_trend_rows must use deterministic ordering")
    return rebuilt


def _normalize_transition_trend_rows(
    rows: tuple[PaperRecommendationTransitionTrendRow, ...],
) -> tuple[PaperRecommendationTransitionTrendRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("transition_trend_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("transition_trend_rows must be an iterable") from exc
    rebuilt = tuple(_normalize_transition_trend_row(row) for row in normalized)
    if rebuilt != tuple(sorted(rebuilt, key=_transition_row_sort_key)):
        raise ValueError("transition_trend_rows must use deterministic ordering")
    return rebuilt


def _normalize_reason_trend_row(row: PaperRecommendationReasonTrendRow) -> PaperRecommendationReasonTrendRow:
    if type(row) is not PaperRecommendationReasonTrendRow:
        raise ValueError(
            "reason_trend_rows must contain PaperRecommendationReasonTrendRow values",
        )
    return PaperRecommendationReasonTrendRow(
        reason_code=row.reason_code,
        source_status=row.source_status,
        count=row.count,
        first_seen_at=row.first_seen_at,
        latest_seen_at=row.latest_seen_at,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _normalize_transition_trend_row(
    row: PaperRecommendationTransitionTrendRow,
) -> PaperRecommendationTransitionTrendRow:
    if type(row) is not PaperRecommendationTransitionTrendRow:
        raise ValueError(
            "transition_trend_rows must contain PaperRecommendationTransitionTrendRow values",
        )
    return PaperRecommendationTransitionTrendRow(
        market_slug=row.market_slug,
        side=row.side,
        from_status=row.from_status,
        to_status=row.to_status,
        transition_count=row.transition_count,
        latest_transition_at=row.latest_transition_at,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _validate_report_consistency(report: PaperRecommendationReasonTrendReport) -> None:
    if report.source_report_count == 0:
        if report.reason_trend_rows:
            raise ValueError("reason_trend_rows must be empty without reports")
        if report.transition_trend_rows:
            raise ValueError("transition_trend_rows must be empty without reports")
        return

    reason_keys = [
        (row.reason_code, row.source_status) for row in report.reason_trend_rows
    ]
    if len(set(reason_keys)) != len(reason_keys):
        raise ValueError("reason_trend_rows must not contain duplicate reason rows")

    transition_keys = [
        (row.market_slug, row.side, row.from_status, row.to_status)
        for row in report.transition_trend_rows
    ]
    if len(set(transition_keys)) != len(transition_keys):
        raise ValueError("transition_trend_rows must not contain duplicate transition rows")


def _reason_row_sort_key(
    row: PaperRecommendationReasonTrendRow,
) -> tuple[int, str, str]:
    return (-row.count, row.reason_code, row.source_status)


def _transition_row_sort_key(
    row: PaperRecommendationTransitionTrendRow,
) -> tuple[int, str, str, str, str]:
    return (
        -row.transition_count,
        row.market_slug,
        row.side,
        row.from_status,
        row.to_status,
    )


def _merge_reason_codes(
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> tuple[str, ...]:
    merged = list(left)
    for reason_code in right:
        if reason_code not in merged:
            merged.append(reason_code)
    return tuple(sorted(merged))


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_canonical_reason_code(value):
        raise ValueError(f"{field_name} must be a canonical lowercase snake_case string")
    return value


def _require_source_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SOURCE_STATUSES:
        raise ValueError(f"{field_name} must be a known paper trend status")
    return value


def _require_queue_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in QUEUE_STATUS_STATUSES:
        raise ValueError(f"{field_name} must be a known paper trend status")
    return value


def _require_readiness_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be a known paper trend status")
    return value


def _require_action(field_name: str, value: object) -> str:
    if type(value) is not str or value not in QUEUE_ACTION_STATUSES:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")
    return value


def _require_side(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ("yes", "no", "none"):
        raise ValueError(f"{field_name} must be yes, no, or none")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_positive_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _allocation_status(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("allocated_paper_notional must be a Decimal")
    if not value.is_finite():
        raise ValueError("allocated_paper_notional must be finite")
    if value < ZERO:
        raise ValueError("allocated_paper_notional must be nonnegative")
    if value > ZERO:
        return "allocated"
    return "zero"


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    unique_reason_codes: list[str] = []
    for reason_code in reason_codes:
        normalized_reason_code = _require_reason_code(field_name, reason_code)
        if normalized_reason_code not in unique_reason_codes:
            unique_reason_codes.append(normalized_reason_code)
    return tuple(sorted(unique_reason_codes))


def _is_canonical_reason_code(value: str) -> bool:
    if not value or value != value.lower():
        return False
    if value[0] not in REASON_CODE_ALPHABET:
        return False
    if value[-1] == "_":
        return False
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            return False
    return True


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperRecommendationReasonTrendConfig",
    "PaperRecommendationReasonTrendRow",
    "PaperRecommendationTransitionTrendRow",
    "PaperRecommendationReasonTrendReport",
    "build_paper_recommendation_reason_trend_report",
)
