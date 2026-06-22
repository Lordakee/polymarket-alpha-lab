"""Paper project screening rank stability reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.project_screening import PaperProjectScreeningReport


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
STABILITY_STATUSES = ("stable", "watch", "blocked")
RESEARCH_BUCKETS = ("research_ready", "watch", "defer", "blocked")
SCREENING_STATUSES = (
    "screening_ready",
    "screening_watch",
    "screening_defer",
    "screening_blocked",
)
SIDES = ("yes", "no", "none")
STATUS_RANK = {"stable": 0, "blocked": 1, "watch": 2}
BUCKET_RANK = {"research_ready": 0, "watch": 1, "defer": 2, "blocked": 3}


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityConfig:
    config_version: str
    min_snapshot_count: int
    max_rank_movement: int
    max_screening_score_delta: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_snapshot_count", self.min_snapshot_count)
        _require_nonnegative_int("max_rank_movement", self.max_rank_movement)
        object.__setattr__(
            self,
            "max_screening_score_delta",
            _require_six_place_decimal(
                "max_screening_score_delta",
                self.max_screening_score_delta,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityRow:
    market_slug: str
    stability_status: str
    latest_research_bucket: str
    latest_screening_status: str
    latest_source_status: str
    latest_scoring_side: str
    present_snapshot_count: int
    ready_snapshot_count: int
    first_rank: int
    latest_rank: int
    rank_delta: int
    max_rank_movement: int
    first_screening_score: Decimal
    latest_screening_score: Decimal
    screening_score_delta: Decimal
    max_screening_score_delta: Decimal
    scoring_side_changed: bool
    source_status_changed: bool
    screening_status_changed: bool
    research_bucket_changed: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_stability_status("stability_status", self.stability_status)
        _require_research_bucket("latest_research_bucket", self.latest_research_bucket)
        _require_screening_status("latest_screening_status", self.latest_screening_status)
        _require_canonical_string("latest_source_status", self.latest_source_status)
        _require_side("latest_scoring_side", self.latest_scoring_side)
        for field_name in (
            "present_snapshot_count",
            "ready_snapshot_count",
            "max_rank_movement",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_positive_int("first_rank", self.first_rank)
        _require_positive_int("latest_rank", self.latest_rank)
        _require_int("rank_delta", self.rank_delta)
        for field_name in (
            "first_screening_score",
            "latest_screening_score",
            "screening_score_delta",
            "max_screening_score_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scoring_side_changed",
            "source_status_changed",
            "screening_status_changed",
            "research_bucket_changed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("rank stability row", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    candidate_count: int
    stability_status: str
    stable_count: int
    watch_count: int
    blocked_count: int
    stable_ready_count: int
    unstable_ready_count: int
    scoring_side_changed_count: int
    source_status_changed_count: int
    screening_status_changed_count: int
    research_bucket_changed_count: int
    latest_generated_at: datetime | None
    top_stable_market_slug: str | None
    reason_codes: tuple[str, ...]
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_report_count",
            "candidate_count",
            "stable_count",
            "watch_count",
            "blocked_count",
            "stable_ready_count",
            "unstable_ready_count",
            "scoring_side_changed_count",
            "source_status_changed_count",
            "screening_status_changed_count",
            "research_bucket_changed_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_stability_status("stability_status", self.stability_status)
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        if self.top_stable_market_slug is not None:
            _require_canonical_string("top_stable_market_slug", self.top_stable_market_slug)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("rank stability report", self)


@dataclass(frozen=True)
class _SeenRow:
    market_slug: str
    rank: int
    research_bucket: str
    screening_score: Decimal
    source_status: str
    scoring_side: str
    screening_status: str


def build_paper_project_screening_rank_stability_report(
    screening_reports: object,
    *,
    config: PaperProjectScreeningRankStabilityConfig,
    generated_at: datetime,
) -> PaperProjectScreeningRankStabilityReport:
    if type(config) is not PaperProjectScreeningRankStabilityConfig:
        raise ValueError("config must be a PaperProjectScreeningRankStabilityConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    reports = _normalize_screening_reports(screening_reports)
    snapshots = _chronological_reports(reports)
    latest = snapshots[-1] if snapshots else None
    rows = (
        _rows_for_latest(latest, snapshots, config=config)
        if latest is not None
        else ()
    )
    rows = _sort_rows(rows)

    return PaperProjectScreeningRankStabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(snapshots),
        candidate_count=len(rows),
        stability_status=_report_status(rows),
        stable_count=_stability_count(rows, "stable"),
        watch_count=_stability_count(rows, "watch"),
        blocked_count=_stability_count(rows, "blocked"),
        stable_ready_count=_stable_ready_count(rows),
        unstable_ready_count=_unstable_ready_count(rows),
        scoring_side_changed_count=sum(1 for row in rows if row.scoring_side_changed),
        source_status_changed_count=sum(1 for row in rows if row.source_status_changed),
        screening_status_changed_count=sum(
            1 for row in rows if row.screening_status_changed
        ),
        research_bucket_changed_count=sum(
            1 for row in rows if row.research_bucket_changed
        ),
        latest_generated_at=latest.generated_at if latest is not None else None,
        top_stable_market_slug=_top_stable_market_slug(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def _normalize_screening_reports(
    screening_reports: object,
) -> tuple[PaperProjectScreeningReport, ...]:
    if type(screening_reports) not in (list, tuple):
        raise ValueError("screening_reports must be a list or tuple")
    reports = tuple(screening_reports)
    for report in reports:
        if type(report) is not PaperProjectScreeningReport:
            raise ValueError(
                "screening_reports must contain PaperProjectScreeningReport values",
            )
        _require_source_flags("screening report", report)
        _require_unique_market_slugs(report.queue_items)
    return reports


def _chronological_reports(
    reports: tuple[PaperProjectScreeningReport, ...],
) -> tuple[PaperProjectScreeningReport, ...]:
    return tuple(
        report
        for _, report in sorted(
            enumerate(reports),
            key=lambda item: (item[1].generated_at, item[0]),
        )
    )


def _rows_for_latest(
    latest: PaperProjectScreeningReport,
    reports: tuple[PaperProjectScreeningReport, ...],
    *,
    config: PaperProjectScreeningRankStabilityConfig,
) -> tuple[PaperProjectScreeningRankStabilityRow, ...]:
    by_slug = _history_by_slug(reports)
    return tuple(
        _row_from_seen(item.market_slug, by_slug[item.market_slug], config=config)
        for item in latest.queue_items
    )


def _history_by_slug(
    reports: tuple[PaperProjectScreeningReport, ...],
) -> dict[str, tuple[_SeenRow, ...]]:
    values: dict[str, list[_SeenRow]] = {}
    for report in reports:
        screening_status_by_slug = {
            candidate.market_slug: candidate.screening_status
            for candidate in report.candidates
        }
        for item in report.queue_items:
            values.setdefault(item.market_slug, []).append(
                _SeenRow(
                    market_slug=item.market_slug,
                    rank=item.queue_position,
                    research_bucket=item.research_bucket,
                    screening_score=item.screening_score,
                    source_status=item.source_status,
                    scoring_side=item.scoring_side,
                    screening_status=screening_status_by_slug[item.market_slug],
                ),
            )
    return {market_slug: tuple(rows) for market_slug, rows in values.items()}


def _row_from_seen(
    market_slug: str,
    rows: tuple[_SeenRow, ...],
    *,
    config: PaperProjectScreeningRankStabilityConfig,
) -> PaperProjectScreeningRankStabilityRow:
    first = rows[0]
    latest = rows[-1]
    scoring_side_changed = _changed(row.scoring_side for row in rows)
    source_status_changed = _changed(row.source_status for row in rows)
    screening_status_changed = _changed(row.screening_status for row in rows)
    research_bucket_changed = _changed(row.research_bucket for row in rows)
    max_rank_movement = _int_spread(tuple(row.rank for row in rows))
    max_screening_score_delta = _decimal_spread(
        tuple(row.screening_score for row in rows),
    )
    screening_score_delta = _quantize_decimal(
        "screening_score_delta",
        latest.screening_score - first.screening_score,
    )
    reason_codes = _row_reason_codes(
        rows,
        scoring_side_changed=scoring_side_changed,
        source_status_changed=source_status_changed,
        screening_status_changed=screening_status_changed,
        research_bucket_changed=research_bucket_changed,
        max_rank_movement=max_rank_movement,
        max_screening_score_delta=max_screening_score_delta,
        config=config,
    )

    return PaperProjectScreeningRankStabilityRow(
        market_slug=market_slug,
        stability_status=_row_status(reason_codes),
        latest_research_bucket=latest.research_bucket,
        latest_screening_status=latest.screening_status,
        latest_source_status=latest.source_status,
        latest_scoring_side=latest.scoring_side,
        present_snapshot_count=len(rows),
        ready_snapshot_count=sum(1 for row in rows if row.research_bucket == "research_ready"),
        first_rank=first.rank,
        latest_rank=latest.rank,
        rank_delta=latest.rank - first.rank,
        max_rank_movement=max_rank_movement,
        first_screening_score=first.screening_score,
        latest_screening_score=latest.screening_score,
        screening_score_delta=screening_score_delta,
        max_screening_score_delta=max_screening_score_delta,
        scoring_side_changed=scoring_side_changed,
        source_status_changed=source_status_changed,
        screening_status_changed=screening_status_changed,
        research_bucket_changed=research_bucket_changed,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    rows: tuple[_SeenRow, ...],
    *,
    scoring_side_changed: bool,
    source_status_changed: bool,
    screening_status_changed: bool,
    research_bucket_changed: bool,
    max_rank_movement: int,
    max_screening_score_delta: Decimal,
    config: PaperProjectScreeningRankStabilityConfig,
) -> tuple[str, ...]:
    latest = rows[-1]
    if latest.research_bucket == "blocked":
        reason_codes = ["latest_candidate_blocked"]
        if any(row.research_bucket == "research_ready" for row in rows[:-1]):
            reason_codes.append("ready_to_blocked_transition")
        return tuple(reason_codes)
    if len(rows) < config.min_snapshot_count:
        return ("insufficient_history",)
    if latest.research_bucket != "research_ready":
        return (f"latest_candidate_{latest.research_bucket}",)
    blocking_reasons: list[str] = []
    if max_rank_movement > config.max_rank_movement:
        blocking_reasons.append("rank_movement_exceeds_threshold")
    if max_screening_score_delta > config.max_screening_score_delta:
        blocking_reasons.append("screening_score_delta_exceeds_threshold")
    if blocking_reasons:
        return tuple(blocking_reasons)

    watch_reasons: list[str] = []
    if scoring_side_changed:
        watch_reasons.append("scoring_side_changed")
    if source_status_changed:
        watch_reasons.append("source_status_changed")
    if screening_status_changed:
        watch_reasons.append("screening_status_changed")
    if research_bucket_changed:
        watch_reasons.append("research_bucket_changed")
    if watch_reasons:
        return tuple(watch_reasons)
    return ("stable_research_ready",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            "insufficient_history",
            "latest_candidate_blocked",
            "rank_movement_exceeds_threshold",
            "screening_score_delta_exceeds_threshold",
        )
    ):
        return "blocked"
    if reason_codes == ("stable_research_ready",):
        return "stable"
    return "watch"


def _sort_rows(
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...],
) -> tuple[PaperProjectScreeningRankStabilityRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.stability_status],
                BUCKET_RANK[row.latest_research_bucket],
                -row.latest_screening_score,
                row.latest_rank,
                row.market_slug,
            ),
        ),
    )


def _report_status(rows: tuple[PaperProjectScreeningRankStabilityRow, ...]) -> str:
    if any(row.stability_status == "blocked" for row in rows):
        return "blocked"
    if not rows:
        return "watch"
    if all(row.stability_status == "stable" for row in rows):
        return "stable"
    return "watch"


def _report_reason_codes(
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_latest_candidates",)
    if any(row.stability_status == "blocked" for row in rows):
        return ("blocked_stability_candidates_present",)
    if _unstable_ready_count(rows) > 0:
        return ("unstable_ready_candidates_present",)
    if _stable_ready_count(rows) > 0:
        return ("stable_ready_candidates_present",)
    return ("no_stable_ready_candidates",)


def _stability_count(
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...],
    stability_status: str,
) -> int:
    return sum(1 for row in rows if row.stability_status == stability_status)


def _stable_ready_count(rows: tuple[PaperProjectScreeningRankStabilityRow, ...]) -> int:
    return sum(
        1
        for row in rows
        if row.stability_status == "stable"
        and row.latest_research_bucket == "research_ready"
    )


def _unstable_ready_count(rows: tuple[PaperProjectScreeningRankStabilityRow, ...]) -> int:
    return sum(
        1
        for row in rows
        if row.stability_status != "stable"
        and row.latest_research_bucket == "research_ready"
    )


def _top_stable_market_slug(
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...],
) -> str | None:
    for row in rows:
        if row.stability_status == "stable" and row.latest_research_bucket == "research_ready":
            return row.market_slug
    return None


def _changed(values: Any) -> bool:
    return len(set(values)) > 1


def _int_spread(values: tuple[int, ...]) -> int:
    if not values:
        return 0
    return max(values) - min(values)


def _decimal_spread(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _quantize_decimal("decimal spread", max(values) - min(values))


def _validate_row_consistency(row: PaperProjectScreeningRankStabilityRow) -> None:
    if row.ready_snapshot_count > row.present_snapshot_count:
        raise ValueError("ready_snapshot_count must not exceed present_snapshot_count")
    if row.rank_delta != row.latest_rank - row.first_rank:
        raise ValueError("rank_delta must equal latest_rank minus first_rank")
    if row.max_rank_movement < abs(row.rank_delta):
        raise ValueError("max_rank_movement must cover rank_delta")
    if row.screening_score_delta != _quantize_decimal(
        "screening_score_delta",
        row.latest_screening_score - row.first_screening_score,
    ):
        raise ValueError("screening_score_delta must match first and latest scores")
    if row.max_screening_score_delta < abs(row.screening_score_delta):
        raise ValueError("max_screening_score_delta must cover screening_score_delta")
    if row.stability_status == "stable":
        if row.latest_research_bucket != "research_ready":
            raise ValueError("stable rows must have latest research_ready bucket")
        if row.reason_codes != ("stable_research_ready",):
            raise ValueError("stable rows must have stable_research_ready reason")


def _validate_report_consistency(
    report: PaperProjectScreeningRankStabilityReport,
) -> None:
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    if report.stable_count != _stability_count(report.rows, "stable"):
        raise ValueError("stable_count must match rows")
    if report.watch_count != _stability_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _stability_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.stable_ready_count != _stable_ready_count(report.rows):
        raise ValueError("stable_ready_count must match rows")
    if report.unstable_ready_count != _unstable_ready_count(report.rows):
        raise ValueError("unstable_ready_count must match rows")
    if report.scoring_side_changed_count != sum(
        1 for row in report.rows if row.scoring_side_changed
    ):
        raise ValueError("scoring_side_changed_count must match rows")
    if report.source_status_changed_count != sum(
        1 for row in report.rows if row.source_status_changed
    ):
        raise ValueError("source_status_changed_count must match rows")
    if report.screening_status_changed_count != sum(
        1 for row in report.rows if row.screening_status_changed
    ):
        raise ValueError("screening_status_changed_count must match rows")
    if report.research_bucket_changed_count != sum(
        1 for row in report.rows if row.research_bucket_changed
    ):
        raise ValueError("research_bucket_changed_count must match rows")
    if report.rows != _sort_rows(report.rows):
        raise ValueError("rows must use deterministic sort")
    if report.stability_status != _report_status(report.rows):
        raise ValueError("stability_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.top_stable_market_slug != _top_stable_market_slug(report.rows):
        raise ValueError("top_stable_market_slug must match rows")
    if report.source_report_count == 0:
        if report.latest_generated_at is not None:
            raise ValueError("latest_generated_at must be absent without sources")
        if report.candidate_count != 0:
            raise ValueError("candidate_count must be zero without sources")
    elif report.latest_generated_at is None:
        raise ValueError("latest_generated_at is required with sources")


def _normalize_rows(rows: object) -> tuple[PaperProjectScreeningRankStabilityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperProjectScreeningRankStabilityRow:
            raise ValueError(
                "rows must contain PaperProjectScreeningRankStabilityRow values",
            )
        _require_hard_flags("rank stability row", row)
        _validate_row_consistency(row)
    return normalized


def _require_unique_market_slugs(rows: object) -> None:
    market_slugs = tuple(row.market_slug for row in rows)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("queue_items must have unique market_slug values")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_six_place_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use 0.000001 precision")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_stability_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_research_bucket(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_BUCKETS:
        raise ValueError(f"{field_name} must be a known research bucket")


def _require_screening_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SCREENING_STATUSES:
        raise ValueError(f"{field_name} must be a known screening status")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    _require_int(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_source_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperProjectScreeningRankStabilityConfig",
    "PaperProjectScreeningRankStabilityReport",
    "PaperProjectScreeningRankStabilityRow",
    "build_paper_project_screening_rank_stability_report",
)
