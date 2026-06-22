from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningGateResult,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)


GENERATED_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
T1 = datetime(2026, 6, 22, 9, 0, tzinfo=UTC)
T2 = datetime(2026, 6, 22, 10, 0, tzinfo=UTC)
T3 = datetime(2026, 6, 22, 11, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.paper_project_screening_rank_stability",
    )


def _config(
    *,
    min_snapshot_count: int = 2,
    max_rank_movement: int = 1,
    max_screening_score_delta: Decimal = d("0.050000"),
):
    module = _module()
    return module.PaperProjectScreeningRankStabilityConfig(
        config_version="project-screening-rank-stability-v0",
        min_snapshot_count=min_snapshot_count,
        max_rank_movement=max_rank_movement,
        max_screening_score_delta=max_screening_score_delta,
    )


def _gate_results() -> tuple[PaperProjectScreeningGateResult, ...]:
    return (
        PaperProjectScreeningGateResult(
            gate_name="input_count",
            status="pass",
            reason_code="source_reports_supplied",
            message="At least one source report is supplied.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="candidate_types",
            status="pass",
            reason_code="source_report_types_ready",
            message="Every candidate source is a cost-aware event strategy report.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="unique_slugs",
            status="pass",
            reason_code="unique_market_slugs",
            message="Every source report has a unique market slug.",
            observed_value=1,
            threshold=1,
        ),
        PaperProjectScreeningGateResult(
            gate_name="screenable_candidates",
            status="pass",
            reason_code="screenable_candidates_ready",
            message="At least one candidate can be screened.",
            observed_value=1,
            threshold=1,
        ),
    )


def _candidate(
    market_slug: str,
    *,
    question: str | None = None,
    source_status: str = "paper_review_ready",
    scoring_side: str = "yes",
    valid_depth: bool = True,
    screening_score: Decimal,
    screening_status: str = "screening_ready",
    reason_codes: tuple[str, ...] = ("source_paper_review_ready", "yes_depth_ready"),
) -> PaperProjectScreeningCandidate:
    return PaperProjectScreeningCandidate(
        market_slug=market_slug,
        question=question or f"Question for {market_slug}?",
        source_status=source_status,
        scoring_side=scoring_side,
        valid_depth=valid_depth,
        net_edge_per_share=d("0.070000") if valid_depth else None,
        total_cost_per_share=d("0.000000") if valid_depth else None,
        ask_size=d("100.0000") if valid_depth else None,
        edge_component=screening_score,
        confidence_component=ZERO,
        depth_component=ZERO,
        spread_penalty=ZERO,
        resolution_risk_penalty=ZERO,
        cost_penalty=ZERO,
        screening_score=screening_score,
        screening_status=screening_status,
        reason_codes=reason_codes,
    )


def _item(
    rank: int,
    market_slug: str,
    *,
    question: str | None = None,
    research_bucket: str = "research_ready",
    screening_score: Decimal,
    source_status: str = "paper_review_ready",
    scoring_side: str = "yes",
    reason_codes: tuple[str, ...] = ("source_paper_review_ready", "yes_depth_ready"),
) -> PaperProjectScreeningQueueItem:
    return PaperProjectScreeningQueueItem(
        queue_position=rank,
        market_slug=market_slug,
        question=question or f"Question for {market_slug}?",
        research_bucket=research_bucket,
        screening_score=screening_score,
        source_status=source_status,
        scoring_side=scoring_side,
        reason_codes=reason_codes,
    )


def _ready(
    rank: int,
    market_slug: str,
    *,
    screening_score: Decimal,
    scoring_side: str = "yes",
) -> tuple[PaperProjectScreeningCandidate, PaperProjectScreeningQueueItem]:
    return (
        _candidate(
            market_slug,
            screening_score=screening_score,
            scoring_side=scoring_side,
        ),
        _item(
            rank,
            market_slug,
            screening_score=screening_score,
            scoring_side=scoring_side,
        ),
    )


def _watch(
    rank: int,
    market_slug: str,
    *,
    screening_score: Decimal,
    source_status: str = "watch",
) -> tuple[PaperProjectScreeningCandidate, PaperProjectScreeningQueueItem]:
    reason_codes = (f"source_{source_status}", "yes_depth_ready")
    return (
        _candidate(
            market_slug,
            source_status=source_status,
            screening_score=screening_score,
            screening_status="screening_watch",
            reason_codes=reason_codes,
        ),
        _item(
            rank,
            market_slug,
            research_bucket="watch",
            screening_score=screening_score,
            source_status=source_status,
            reason_codes=reason_codes,
        ),
    )


def _blocked(
    rank: int,
    market_slug: str,
    *,
    screening_score: Decimal = ZERO,
) -> tuple[PaperProjectScreeningCandidate, PaperProjectScreeningQueueItem]:
    reason_codes = ("source_blocked_by_inputs", "missing_scoring_side")
    return (
        _candidate(
            market_slug,
            source_status="blocked_by_inputs",
            scoring_side="none",
            valid_depth=False,
            screening_score=screening_score,
            screening_status="screening_blocked",
            reason_codes=reason_codes,
        ),
        _item(
            rank,
            market_slug,
            research_bucket="blocked",
            screening_score=screening_score,
            source_status="blocked_by_inputs",
            scoring_side="none",
            reason_codes=reason_codes,
        ),
    )


def _report(
    generated_at: datetime,
    rows: tuple[tuple[PaperProjectScreeningCandidate, PaperProjectScreeningQueueItem], ...],
) -> PaperProjectScreeningReport:
    candidates = tuple(candidate for candidate, _ in rows)
    queue_items = tuple(item for _, item in rows)
    return PaperProjectScreeningReport(
        generated_at=generated_at,
        config_version="project-screening-v1",
        candidate_count=len(queue_items),
        ready_count=sum(1 for item in queue_items if item.research_bucket == "research_ready"),
        watch_count=sum(1 for item in queue_items if item.research_bucket == "watch"),
        defer_count=sum(1 for item in queue_items if item.research_bucket == "defer"),
        blocked_count=sum(1 for item in queue_items if item.research_bucket == "blocked"),
        gate_results=_gate_results(),
        candidates=candidates,
        queue_items=queue_items,
    )


def _build(reports, *, generated_at=GENERATED_AT, config=None):
    module = _module()
    return module.build_paper_project_screening_rank_stability_report(
        reports,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_history_yields_watch_report_without_rows():
    report = _build(())

    module = _module()
    assert isinstance(report, module.PaperProjectScreeningRankStabilityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "project-screening-rank-stability-v0"
    assert report.source_report_count == 0
    assert report.candidate_count == 0
    assert report.stability_status == "watch"
    assert report.stable_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.stable_ready_count == 0
    assert report.unstable_ready_count == 0
    assert report.scoring_side_changed_count == 0
    assert report.source_status_changed_count == 0
    assert report.screening_status_changed_count == 0
    assert report.research_bucket_changed_count == 0
    assert report.latest_generated_at is None
    assert report.top_stable_market_slug is None
    assert report.rows == ()
    assert report.reason_codes == ("no_latest_candidates",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_single_snapshot_ready_candidate_is_blocked_until_history_is_sufficient():
    report = _build(
        (_report(T1, (_ready(1, "alpha", screening_score=d("0.700000")),)),),
    )

    assert report.stability_status == "blocked"
    assert report.source_report_count == 1
    assert report.candidate_count == 1
    assert report.blocked_count == 1
    assert report.stable_ready_count == 0
    assert report.unstable_ready_count == 1
    assert report.reason_codes == ("blocked_stability_candidates_present",)

    row = report.rows[0]
    assert row.market_slug == "alpha"
    assert row.stability_status == "blocked"
    assert row.latest_research_bucket == "research_ready"
    assert row.latest_screening_status == "screening_ready"
    assert row.latest_source_status == "paper_review_ready"
    assert row.latest_scoring_side == "yes"
    assert row.present_snapshot_count == 1
    assert row.ready_snapshot_count == 1
    assert row.first_rank == 1
    assert row.latest_rank == 1
    assert row.rank_delta == 0
    assert row.max_rank_movement == 0
    assert row.first_screening_score == d("0.700000")
    assert row.latest_screening_score == d("0.700000")
    assert row.screening_score_delta == ZERO
    assert row.max_screening_score_delta == ZERO
    assert row.scoring_side_changed is False
    assert row.source_status_changed is False
    assert row.screening_status_changed is False
    assert row.research_bucket_changed is False
    assert row.reason_codes == ("insufficient_history",)


def test_two_snapshot_research_ready_candidate_is_stable_when_rank_score_and_status_hold():
    report = _build(
        (
            _report(T1, (_ready(1, "alpha", screening_score=d("0.700000")),)),
            _report(T2, (_ready(1, "alpha", screening_score=d("0.720000")),)),
        ),
    )

    assert report.stability_status == "stable"
    assert report.source_report_count == 2
    assert report.candidate_count == 1
    assert report.stable_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.stable_ready_count == 1
    assert report.unstable_ready_count == 0
    assert report.top_stable_market_slug == "alpha"
    assert report.latest_generated_at == T2
    assert report.reason_codes == ("stable_ready_candidates_present",)

    row = report.rows[0]
    assert row.market_slug == "alpha"
    assert row.stability_status == "stable"
    assert row.latest_research_bucket == "research_ready"
    assert row.latest_screening_status == "screening_ready"
    assert row.present_snapshot_count == 2
    assert row.ready_snapshot_count == 2
    assert row.first_rank == 1
    assert row.latest_rank == 1
    assert row.rank_delta == 0
    assert row.max_rank_movement == 0
    assert row.first_screening_score == d("0.700000")
    assert row.latest_screening_score == d("0.720000")
    assert row.screening_score_delta == d("0.020000")
    assert row.max_screening_score_delta == d("0.020000")
    assert row.reason_codes == ("stable_research_ready",)


def test_rank_and_screening_score_churn_block_latest_ready_candidate():
    report = _build(
        (
            _report(
                T1,
                (
                    _ready(1, "alpha", screening_score=d("0.900000")),
                    _watch(2, "beta", screening_score=d("0.500000")),
                    _watch(3, "gamma", screening_score=d("0.400000")),
                ),
            ),
            _report(
                T2,
                (
                    _ready(1, "gamma", screening_score=d("0.920000")),
                    _ready(2, "beta", screening_score=d("0.880000")),
                    _ready(3, "alpha", screening_score=d("0.760000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=1, max_screening_score_delta=d("0.050000")),
    )

    alpha = next(row for row in report.rows if row.market_slug == "alpha")
    assert report.stability_status == "blocked"
    assert alpha.stability_status == "blocked"
    assert alpha.rank_delta == 2
    assert alpha.max_rank_movement == 2
    assert alpha.screening_score_delta == d("-0.140000")
    assert alpha.max_screening_score_delta == d("0.140000")
    assert alpha.reason_codes == (
        "rank_movement_exceeds_threshold",
        "screening_score_delta_exceeds_threshold",
    )


def test_status_bucket_and_scoring_side_changes_are_watch_when_latest_candidate_is_ready():
    report = _build(
        (
            _report(
                T1,
                (_watch(1, "alpha", screening_score=d("0.700000"), source_status="watch"),),
            ),
            _report(
                T2,
                (_ready(1, "alpha", screening_score=d("0.710000"), scoring_side="no"),),
            ),
        ),
    )

    assert report.stability_status == "watch"
    assert report.watch_count == 1
    assert report.unstable_ready_count == 1
    assert report.scoring_side_changed_count == 1
    assert report.source_status_changed_count == 1
    assert report.screening_status_changed_count == 1
    assert report.research_bucket_changed_count == 1

    row = report.rows[0]
    assert row.stability_status == "watch"
    assert row.latest_research_bucket == "research_ready"
    assert row.latest_screening_status == "screening_ready"
    assert row.latest_source_status == "paper_review_ready"
    assert row.latest_scoring_side == "no"
    assert row.scoring_side_changed is True
    assert row.source_status_changed is True
    assert row.screening_status_changed is True
    assert row.research_bucket_changed is True
    assert row.reason_codes == (
        "scoring_side_changed",
        "source_status_changed",
        "screening_status_changed",
        "research_bucket_changed",
    )


def test_latest_blocked_candidate_blocks_even_when_history_is_sufficient():
    report = _build(
        (
            _report(T1, (_ready(1, "alpha", screening_score=d("0.700000")),)),
            _report(T2, (_blocked(1, "alpha"),)),
        ),
    )

    assert report.stability_status == "blocked"
    assert report.blocked_count == 1
    assert report.rows[0].stability_status == "blocked"
    assert report.rows[0].reason_codes == (
        "latest_candidate_blocked",
        "ready_to_blocked_transition",
    )


def test_report_rows_are_ordered_deterministically_for_review():
    report = _build(
        (
            _report(
                T1,
                (
                    _ready(1, "alpha", screening_score=d("0.900000")),
                    _watch(2, "beta", screening_score=d("0.600000")),
                ),
            ),
            _report(
                T2,
                (
                    _ready(1, "gamma", screening_score=d("0.910000")),
                    _ready(2, "alpha", screening_score=d("0.880000")),
                    _watch(3, "beta", screening_score=d("0.610000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=3),
    )

    assert tuple(row.market_slug for row in report.rows) == (
        "alpha",
        "gamma",
        "beta",
    )
    assert tuple(row.stability_status for row in report.rows) == (
        "stable",
        "blocked",
        "watch",
    )


def test_config_rows_and_reports_validate_decimal_precision_flags_and_are_frozen():
    module = _module()
    config = _config(max_screening_score_delta=d("0.050000"))
    with pytest.raises(FrozenInstanceError):
        config.max_rank_movement = 10
    with pytest.raises(ValueError, match="max_screening_score_delta"):
        module.PaperProjectScreeningRankStabilityConfig(
            config_version="project-screening-rank-stability-v0",
            min_snapshot_count=2,
            max_rank_movement=1,
            max_screening_score_delta=d("0.0500001"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.PaperProjectScreeningRankStabilityConfig(
            config_version="project-screening-rank-stability-v0",
            min_snapshot_count=2,
            max_rank_movement=1,
            max_screening_score_delta=d("0.050000"),
            paper_only=False,
        )

    report = _build(
        (
            _report(T1, (_ready(1, "alpha", screening_score=d("0.700000")),)),
            _report(T2, (_ready(1, "alpha", screening_score=d("0.710000")),)),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].market_slug = "mutated"
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_direct_rows_and_reports_enforce_hard_flags_and_consistency():
    module = _module()
    valid_row = module.PaperProjectScreeningRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_research_bucket="research_ready",
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=d("0.700000"),
        latest_screening_score=d("0.700000"),
        screening_score_delta=ZERO,
        max_screening_score_delta=ZERO,
        scoring_side_changed=False,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=("stable_research_ready",),
    )

    with pytest.raises(ValueError, match="report_only"):
        replace(valid_row, report_only=False)
    with pytest.raises(ValueError, match="candidate_count"):
        module.PaperProjectScreeningRankStabilityReport(
            generated_at=GENERATED_AT,
            config_version="project-screening-rank-stability-v0",
            source_report_count=1,
            candidate_count=2,
            stability_status="stable",
            stable_count=1,
            watch_count=0,
            blocked_count=0,
            stable_ready_count=1,
            unstable_ready_count=0,
            scoring_side_changed_count=0,
            source_status_changed_count=0,
            screening_status_changed_count=0,
            research_bucket_changed_count=0,
            latest_generated_at=T2,
            top_stable_market_slug="alpha",
            reason_codes=("stable_ready_candidates_present",),
            rows=(valid_row,),
        )

    bypassed_row = object.__new__(module.PaperProjectScreeningRankStabilityRow)
    for field_name, value in valid_row.__dict__.items():
        object.__setattr__(bypassed_row, field_name, value)
    object.__setattr__(bypassed_row, "screening_score_delta", d("0.500000"))

    with pytest.raises(ValueError, match="screening_score_delta"):
        module.PaperProjectScreeningRankStabilityReport(
            generated_at=GENERATED_AT,
            config_version="project-screening-rank-stability-v0",
            source_report_count=1,
            candidate_count=1,
            stability_status="stable",
            stable_count=1,
            watch_count=0,
            blocked_count=0,
            stable_ready_count=1,
            unstable_ready_count=0,
            scoring_side_changed_count=0,
            source_status_changed_count=0,
            screening_status_changed_count=0,
            research_bucket_changed_count=0,
            latest_generated_at=T2,
            top_stable_market_slug="alpha",
            reason_codes=("stable_ready_candidates_present",),
            rows=(bypassed_row,),
        )


def test_decimal_values_are_canonicalized_to_six_places():
    module = _module()
    row = module.PaperProjectScreeningRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_research_bucket="research_ready",
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=Decimal("0.7"),
        latest_screening_score=Decimal("0.7"),
        screening_score_delta=Decimal("0"),
        max_screening_score_delta=Decimal("0"),
        scoring_side_changed=False,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=("stable_research_ready",),
    )

    assert row.first_screening_score == d("0.700000")
    assert row.first_screening_score.as_tuple().exponent == -6
    assert row.max_screening_score_delta == ZERO


def test_threshold_boundaries_are_inclusive_for_stable_candidates():
    report = _build(
        (
            _report(
                T1,
                (
                    _ready(1, "alpha", screening_score=d("0.700000")),
                    _watch(2, "beta", screening_score=d("0.500000")),
                ),
            ),
            _report(
                T2,
                (
                    _ready(1, "beta", screening_score=d("0.900000")),
                    _ready(2, "alpha", screening_score=d("0.650000")),
                ),
            ),
        ),
        config=_config(max_rank_movement=1, max_screening_score_delta=d("0.050000")),
    )

    alpha = next(row for row in report.rows if row.market_slug == "alpha")
    assert alpha.max_rank_movement == 1
    assert alpha.max_screening_score_delta == d("0.050000")
    assert alpha.stability_status == "stable"


def test_nonempty_sources_with_empty_latest_queue_keep_latest_timestamp():
    report = _build((_report(T1, ()),))

    assert report.source_report_count == 1
    assert report.latest_generated_at == T1
    assert report.candidate_count == 0
    assert report.stability_status == "watch"
    assert report.reason_codes == ("no_latest_candidates",)


def test_builder_rejects_invalid_inputs_and_unsafe_source_reports():
    safe_report = _report(
        T1,
        (_ready(1, "alpha", screening_score=d("0.700000")),),
    )

    with pytest.raises(ValueError, match="list or tuple"):
        _build("not reports")
    with pytest.raises(ValueError, match="PaperProjectScreeningRankStabilityConfig"):
        _build((safe_report,), config=object())
    with pytest.raises(ValueError, match="datetime"):
        _build((safe_report,), generated_at="2026-06-22T12:00:00Z")
    with pytest.raises(ValueError, match="PaperProjectScreeningReport"):
        _build((object(),))

    unsafe_report = object.__new__(PaperProjectScreeningReport)
    for field_name, value in safe_report.__dict__.items():
        object.__setattr__(unsafe_report, field_name, value)
    object.__setattr__(unsafe_report, "report_only", False)

    with pytest.raises(ValueError, match="report_only"):
        _build((unsafe_report,))

    class ScreeningReportSubclass(PaperProjectScreeningReport):
        pass

    subclass_report = ScreeningReportSubclass(**safe_report.__dict__)
    with pytest.raises(ValueError, match="PaperProjectScreeningReport"):
        _build((subclass_report,))


def test_module_import_scope_stays_paper_only_and_readonly():
    spec = importlib.util.find_spec(
        "polymarket_alpha_lab.paper_project_screening_rank_stability",
    )
    assert spec is not None
    assert spec.origin is not None
    source = Path(spec.origin).read_text(encoding="utf-8")
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
        "decimal",
        "typing",
        "polymarket_alpha_lab",
    }
    forbidden_tokens = (
        "trade",
        "wallet",
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
    )
    assert not any(token in source.lower() for token in forbidden_tokens)
