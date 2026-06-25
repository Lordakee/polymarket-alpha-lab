from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
    PaperProjectScreeningRankStabilityRow,
)


GENERATED_AT = datetime(2026, 6, 25, 18, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 25, 17, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_project_screening_rank_stability_db_history_health",
    )


def d(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.000001"))


def _config(**overrides):
    values = {
        "config_version": (
            "paper-project-screening-rank-stability-db-history-health-v0"
        ),
        "min_rank_stability_report_count": 3,
        "min_latest_stable_ready_count": 1,
        "max_unstable_ready_count": 0,
        "max_watch_rank_stability_report_count": 0,
        "max_blocked_rank_stability_report_count": 0,
        "max_duplicate_latest_generated_at_count": 0,
        "max_latest_age_seconds": 86_400,
    }
    values.update(overrides)
    return _api().PaperProjectScreeningRankStabilityDbHistoryHealthConfig(**values)


def _row(
    *,
    market_slug: str = "alpha",
    stability_status: str = "stable",
    latest_research_bucket: str = "research_ready",
    reason_codes: tuple[str, ...] = ("stable_research_ready",),
) -> PaperProjectScreeningRankStabilityRow:
    return PaperProjectScreeningRankStabilityRow(
        market_slug=market_slug,
        stability_status=stability_status,
        latest_research_bucket=latest_research_bucket,
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2 if latest_research_bucket == "research_ready" else 1,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=d("0.700000"),
        latest_screening_score=d("0.710000"),
        screening_score_delta=d("0.010000"),
        max_screening_score_delta=d("0.010000"),
        scoring_side_changed=False,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=reason_codes,
    )


def _rank_report(
    *,
    generated_at: datetime = SOURCE_GENERATED_AT,
    latest_generated_at: datetime | None = SOURCE_GENERATED_AT,
    stability_status: str = "stable",
    stable_ready_count: int | None = None,
    unstable_ready_count: int | None = None,
    reason_codes: tuple[str, ...] | None = None,
    rows: tuple[PaperProjectScreeningRankStabilityRow, ...] | None = None,
) -> PaperProjectScreeningRankStabilityReport:
    if rows is None:
        rows = {
            "stable": (_row(stability_status="stable"),),
            "watch": (
                _row(
                    stability_status="watch",
                    reason_codes=("scoring_side_changed",),
                ),
            ),
            "blocked": (
                _row(
                    stability_status="blocked",
                    reason_codes=("insufficient_history",),
                ),
            ),
        }[stability_status]
    if stable_ready_count is None:
        stable_ready_count = sum(
            1
            for row in rows
            if row.stability_status == "stable"
            and row.latest_research_bucket == "research_ready"
        )
    if unstable_ready_count is None:
        unstable_ready_count = sum(
            1
            for row in rows
            if row.stability_status != "stable"
            and row.latest_research_bucket == "research_ready"
        )
    if reason_codes is None:
        reason_codes = {
            "stable": ("stable_ready_candidates_present",),
            "watch": ("unstable_ready_candidates_present",),
            "blocked": ("blocked_stability_candidates_present",),
        }[stability_status]
    top_stable = next(
        (
            row.market_slug
            for row in rows
            if row.stability_status == "stable"
            and row.latest_research_bucket == "research_ready"
        ),
        None,
    )
    return PaperProjectScreeningRankStabilityReport(
        generated_at=generated_at,
        config_version="project-screening-rank-stability-v0",
        source_report_count=2,
        candidate_count=len(rows),
        stability_status=stability_status,
        stable_count=sum(1 for row in rows if row.stability_status == "stable"),
        watch_count=sum(1 for row in rows if row.stability_status == "watch"),
        blocked_count=sum(1 for row in rows if row.stability_status == "blocked"),
        stable_ready_count=stable_ready_count,
        unstable_ready_count=unstable_ready_count,
        scoring_side_changed_count=sum(1 for row in rows if row.scoring_side_changed),
        source_status_changed_count=sum(1 for row in rows if row.source_status_changed),
        screening_status_changed_count=sum(
            1 for row in rows if row.screening_status_changed
        ),
        research_bucket_changed_count=sum(1 for row in rows if row.research_bucket_changed),
        latest_generated_at=latest_generated_at,
        top_stable_market_slug=top_stable,
        reason_codes=reason_codes,
        rows=rows,
    )


def _health_report(
    reports: tuple[PaperProjectScreeningRankStabilityReport, ...],
    **config_overrides,
):
    return _api().build_paper_project_screening_rank_stability_db_history_health_report(
        reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _corrupt_report(
    report: PaperProjectScreeningRankStabilityReport,
    **overrides,
) -> PaperProjectScreeningRankStabilityReport:
    corrupted = PaperProjectScreeningRankStabilityReport.__new__(
        PaperProjectScreeningRankStabilityReport,
    )
    values = dict(report.__dict__)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(corrupted, field_name, value)
    return corrupted


def test_health_config_defaults_are_safe_paper_report_readonly_defaults() -> None:
    api = _api()

    config = api.PaperProjectScreeningRankStabilityDbHistoryHealthConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    assert config.config_version == (
        "paper-project-screening-rank-stability-db-history-health-v0"
    )
    assert config.min_rank_stability_report_count == 3
    assert config.min_latest_stable_ready_count == 1
    assert config.max_unstable_ready_count == 0
    assert config.max_watch_rank_stability_report_count == 0
    assert config.max_blocked_rank_stability_report_count == 0
    assert config.max_duplicate_latest_generated_at_count == 0
    assert config.max_latest_age_seconds == 86_400
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_public_all_exports_constants_dataclasses_and_builder() -> None:
    api = _api()

    assert set(api.__all__) == {
        "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_CONFIG_VERSION",
        "HEALTH_STATUSES",
        "NEXT_STEP_BY_STATUS",
        "PASS_REASON_CODE",
        "BLOCKED_REASON_CODES",
        "WATCH_REASON_CODES",
        "HEALTH_REASON_CODES",
        "PaperProjectScreeningRankStabilityDbHistoryHealthConfig",
        "PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount",
        "PaperProjectScreeningRankStabilityDbHistoryHealthReport",
        "build_paper_project_screening_rank_stability_db_history_health_report",
    }
    assert api.HEALTH_STATUSES == ("pass", "watch", "blocked")
    assert api.NEXT_STEP_BY_STATUS == {
        "pass": "allow_paper_project_screening_rank_stability_review",
        "watch": "throttle_paper_project_screening_rank_stability_review",
        "blocked": "block_paper_project_screening_rank_stability_review",
    }


def test_health_blocks_empty_and_insufficient_rank_stability_report_samples() -> None:
    empty = _health_report(())
    insufficient = _health_report(
        (
            _rank_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_200),
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_260),
            ),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(seconds=600),
                latest_generated_at=GENERATED_AT - timedelta(seconds=660),
            ),
        ),
    )

    assert empty.rank_stability_report_count == 0
    assert empty.health_status == "blocked"
    assert empty.recommended_next_step == (
        "block_paper_project_screening_rank_stability_review"
    )
    assert empty.latest_rank_stability_status is None
    assert empty.latest_candidate_count is None
    assert empty.latest_stable_ready_count is None
    assert empty.latest_unstable_ready_count is None
    assert empty.latest_source_generated_at is None
    assert empty.latest_source_age_seconds is None
    assert empty.max_source_age_seconds is None
    assert empty.duplicate_latest_generated_at_count == 0
    assert empty.reason_code_counts == ()
    assert empty.reason_codes == (
        "insufficient_paper_project_screening_rank_stability_samples",
    )

    assert insufficient.rank_stability_report_count == 2
    assert insufficient.health_status == "blocked"
    assert insufficient.stable_rank_stability_report_count == 2
    assert insufficient.reason_codes == (
        "insufficient_paper_project_screening_rank_stability_samples",
    )


def test_health_passes_clean_recent_stable_history() -> None:
    report = _health_report(
        (
            _rank_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_800),
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_860),
            ),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(seconds=1_200),
                latest_generated_at=GENERATED_AT - timedelta(seconds=1_260),
            ),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(seconds=600),
                latest_generated_at=GENERATED_AT - timedelta(seconds=660),
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_project_screening_rank_stability_review"
    )
    assert report.rank_stability_report_count == 3
    assert report.stable_rank_stability_report_count == 3
    assert report.watch_rank_stability_report_count == 0
    assert report.blocked_rank_stability_report_count == 0
    assert report.latest_rank_stability_status == "stable"
    assert report.latest_candidate_count == 1
    assert report.latest_stable_ready_count == 1
    assert report.latest_unstable_ready_count == 0
    assert report.latest_source_generated_at == GENERATED_AT - timedelta(seconds=660)
    assert report.latest_source_age_seconds == 660
    assert report.max_source_age_seconds == 1_860
    assert report.duplicate_latest_generated_at_count == 0
    assert report.reason_code_counts == (
        _api().PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount(
            "stable_ready_candidates_present",
            3,
        ),
    )
    assert report.reason_codes == (
        "paper_project_screening_rank_stability_db_history_health_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_blocks_latest_blocked_report_and_blocked_report_count() -> None:
    latest_blocked = _health_report(
        (
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(minutes=1),
                latest_generated_at=GENERATED_AT - timedelta(hours=1),
                stability_status="blocked",
            ),
        ),
        max_blocked_rank_stability_report_count=2,
        min_latest_stable_ready_count=0,
        max_unstable_ready_count=2,
    )
    any_blocked = _health_report(
        (
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(hours=3),
                stability_status="blocked",
            ),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    assert latest_blocked.health_status == "blocked"
    assert latest_blocked.latest_rank_stability_status == "blocked"
    assert latest_blocked.reason_codes == (
        "latest_paper_project_screening_rank_stability_blocked",
    )

    assert any_blocked.health_status == "blocked"
    assert any_blocked.blocked_rank_stability_report_count == 1
    assert any_blocked.reason_codes == (
        "blocked_paper_project_screening_rank_stability_count_threshold_exceeded",
    )


def test_health_blocks_missing_latest_source_timestamp() -> None:
    source = _corrupt_report(
        _rank_report(),
        latest_generated_at=None,
    )

    report = _health_report((source,), min_rank_stability_report_count=1)

    assert report.health_status == "blocked"
    assert report.latest_source_generated_at is None
    assert report.latest_source_age_seconds is None
    assert report.max_source_age_seconds is None
    assert report.reason_codes == (
        "missing_latest_paper_project_screening_rank_stability_source_timestamp",
    )


def test_health_watches_latest_watch_low_stable_ready_unstable_ready_and_stale_history() -> None:
    latest_watch = _health_report(
        (
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(minutes=1),
                latest_generated_at=GENERATED_AT - timedelta(hours=1),
                stability_status="watch",
            ),
        ),
        max_watch_rank_stability_report_count=2,
        max_unstable_ready_count=2,
        min_latest_stable_ready_count=0,
    )
    low_stable_ready = _health_report(
        (
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(seconds=900)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(seconds=800)),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(minutes=1),
                latest_generated_at=GENERATED_AT - timedelta(seconds=700),
                rows=(),
                stability_status="watch",
                stable_ready_count=0,
                unstable_ready_count=0,
                reason_codes=("no_latest_candidates",),
            ),
        ),
        max_watch_rank_stability_report_count=2,
    )
    unstable_ready = _health_report(
        (
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(seconds=900)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(seconds=800)),
            _rank_report(
                generated_at=GENERATED_AT - timedelta(minutes=1),
                latest_generated_at=GENERATED_AT - timedelta(seconds=700),
                stability_status="watch",
            ),
        ),
        max_watch_rank_stability_report_count=2,
        min_latest_stable_ready_count=0,
    )
    stale = _health_report(
        (
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_403),
            ),
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_402),
            ),
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=86_401),
            ),
        ),
    )

    assert latest_watch.health_status == "watch"
    assert latest_watch.latest_rank_stability_status == "watch"
    assert latest_watch.reason_codes == (
        "latest_paper_project_screening_rank_stability_watch",
    )

    assert low_stable_ready.health_status == "watch"
    assert (
        "low_paper_project_screening_rank_stability_stable_ready_count"
        in low_stable_ready.reason_codes
    )

    assert unstable_ready.health_status == "watch"
    assert unstable_ready.latest_unstable_ready_count == 1
    assert (
        "unstable_paper_project_screening_rank_stability_ready_candidates_present"
        in unstable_ready.reason_codes
    )

    assert stale.health_status == "watch"
    assert stale.latest_source_age_seconds == 86_401
    assert stale.max_source_age_seconds == 86_403
    assert stale.reason_codes == (
        "stale_paper_project_screening_rank_stability_source_history",
    )


def test_health_watches_duplicate_latest_source_generated_at_values() -> None:
    report = _health_report(
        (
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _rank_report(
                latest_generated_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
    )

    assert report.health_status == "watch"
    assert report.duplicate_latest_generated_at_count == 1
    assert report.reason_codes == (
        "duplicate_latest_paper_project_screening_rank_stability_source_generated_at_threshold_exceeded",
    )


def test_health_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_count = api.PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount(
        "stable_ready_candidates_present",
        1,
    )
    report = _health_report(
        (
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=3)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=2)),
            _rank_report(latest_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.health_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count .*report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="health report .*readonly"):
        replace(report, readonly=False)


def test_health_public_dataclass_subclasses_are_rejected() -> None:
    api = _api()

    with pytest.raises(TypeError, match="HealthConfig .*subclassing"):
        class ConfigSubclass(api.PaperProjectScreeningRankStabilityDbHistoryHealthConfig):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(api.PaperProjectScreeningRankStabilityDbHistoryHealthReport):
            def __post_init__(self) -> None:
                pass


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_rank_stability_report_count": True}, "min_rank_stability_report_count"),
        ({"min_rank_stability_report_count": 0}, "min_rank_stability_report_count"),
        ({"min_latest_stable_ready_count": -1}, "min_latest_stable_ready_count"),
        ({"max_unstable_ready_count": True}, "max_unstable_ready_count"),
        ({"max_watch_rank_stability_report_count": -1}, "max_watch"),
        ({"max_blocked_rank_stability_report_count": -1}, "max_blocked"),
        (
            {"max_duplicate_latest_generated_at_count": -1},
            "max_duplicate_latest_generated_at_count",
        ),
        ({"max_latest_age_seconds": 1.5}, "max_latest_age_seconds"),
    ),
)
def test_health_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_health_rejects_wrong_types_naive_datetimes_and_corrupt_flags() -> None:
    api = _api()
    source = _rank_report()

    with pytest.raises(ValueError, match="rank_stability_reports"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rank_stability_reports"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            (source,),
            config=_config(min_rank_stability_report_count=1),
            generated_at=DatetimeSubclass(2026, 6, 25, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            (source,),
            config=_config(min_rank_stability_report_count=1),
            generated_at=datetime(2026, 6, 25, 18, 0),
        )
    with pytest.raises(ValueError, match="rank stability report .*paper_only"):
        api.build_paper_project_screening_rank_stability_db_history_health_report(
            (_corrupt_report(source, paper_only=False),),
            config=_config(min_rank_stability_report_count=1),
            generated_at=GENERATED_AT,
        )

    report = _health_report((source,), min_rank_stability_report_count=1)
    with pytest.raises(ValueError, match="rank_stability_report_count"):
        replace(report, rank_stability_report_count=2)
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="latest_candidate_count"):
        replace(report, latest_candidate_count=0)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report,
            reason_codes=(
                "paper_project_screening_rank_stability_db_history_health_passed",
                "stale_paper_project_screening_rank_stability_source_history",
            ),
        )


def test_health_normalizes_aware_datetimes_to_utc() -> None:
    offset = timezone(timedelta(hours=-4))
    report = _api().build_paper_project_screening_rank_stability_db_history_health_report(
        (
            _rank_report(
                generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=offset),
                latest_generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=offset),
            ),
            _rank_report(
                generated_at=datetime(2026, 6, 25, 12, 10, tzinfo=offset),
                latest_generated_at=datetime(2026, 6, 25, 12, 10, tzinfo=offset),
            ),
            _rank_report(
                generated_at=datetime(2026, 6, 25, 12, 30, tzinfo=offset),
                latest_generated_at=datetime(2026, 6, 25, 12, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 25, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_source_generated_at == datetime(2026, 6, 25, 16, 30, tzinfo=UTC)
    assert report.latest_source_age_seconds == 5_400
    assert report.max_source_age_seconds == 7_200


def test_health_module_import_scope_stays_report_only_and_readonly() -> None:
    module_under_test = _api()
    module_path = module_under_test.__file__
    assert module_path is not None
    source = Path(module_path).read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "polymarket_alpha_lab",
    }
    forbidden_tokens = (
        "wallet",
        "private_key",
        "sign",
        "order",
        "exchange",
        "requests",
        "httpx",
        "psycopg",
        "supabase",
        "insert",
        "update",
        "delete",
        "upsert",
        "commit",
        "rollback",
    )
    assert not any(token in source.lower() for token in forbidden_tokens)
