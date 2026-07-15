from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
import inspect

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.probability_event_duplicate_exposure_collision_report",
    )


def candidate(
    *,
    candidate_id: str = "candidate_alpha",
    event_ref: str = "event_2026_macro_rates",
    market_ref: str = "market_fed_cut_july",
    correlated_event_count: Decimal = d("0"),
    same_resolution_source_count: Decimal = d("0"),
    existing_watchlist_overlap_count: Decimal = d("0"),
    portfolio_exposure_overlap_probability: Decimal = d("0.000000"),
):
    return api().ProbabilityEventDuplicateExposureCollisionInput(
        candidate_id=candidate_id,
        event_ref=event_ref,
        market_ref=market_ref,
        correlated_event_count=correlated_event_count,
        same_resolution_source_count=same_resolution_source_count,
        existing_watchlist_overlap_count=existing_watchlist_overlap_count,
        portfolio_exposure_overlap_probability=portfolio_exposure_overlap_probability,
    )


def report(*rows, **config_overrides):
    module = api()
    return module.build_probability_event_duplicate_exposure_collision_report(
        rows,
        config=module.ProbabilityEventDuplicateExposureCollisionReportConfig(
            **config_overrides,
        ),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, tuple):
            for item in value:
                if is_dataclass(item):
                    assert_public_numeric_fields_are_decimal(item)


def test_duplicate_exposure_collision_report_blocks_direct_duplicate_exposure() -> None:
    result = report(
        candidate(
            candidate_id="candidate_block",
            event_ref="event_fed_cut",
            market_ref="market_fed_cut_yes",
            correlated_event_count=d("2"),
            same_resolution_source_count=d("1"),
            existing_watchlist_overlap_count=d("1"),
            portfolio_exposure_overlap_probability=d("0.750000"),
        ),
        candidate(
            candidate_id="candidate_watch",
            event_ref="event_fed_path",
            market_ref="market_fed_path_yes",
            correlated_event_count=d("1"),
            same_resolution_source_count=d("0"),
            existing_watchlist_overlap_count=d("0"),
            portfolio_exposure_overlap_probability=d("0.300000"),
        ),
        candidate(
            candidate_id="candidate_clear",
            event_ref="event_oil_inventory",
            market_ref="market_oil_inventory_yes",
            correlated_event_count=d("0"),
            same_resolution_source_count=d("0"),
            existing_watchlist_overlap_count=d("0"),
            portfolio_exposure_overlap_probability=d("0.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.config_version == "probability-event-duplicate-exposure-collision-report-v0"
    assert result.candidate_count == d("3")
    assert result.blocker_count == d("1")
    assert result.attention_count == d("1")
    assert result.clear_count == d("1")
    assert result.collision_status == "block"
    assert result.reason_codes == (
        "same_resolution_source_collision",
        "watchlist_overlap_collision",
        "portfolio_exposure_overlap_block",
        "correlated_event_overlap_watch",
    )
    assert result.manual_next_step == "manual_review_block_duplicate_exposure"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    assert tuple(row.candidate_id for row in result.rows) == (
        "candidate_block",
        "candidate_clear",
        "candidate_watch",
    )
    blocked, cleared, watched = result.rows
    assert blocked.collision_status == "block"
    assert blocked.reason_codes == (
        "same_resolution_source_collision",
        "watchlist_overlap_collision",
        "portfolio_exposure_overlap_block",
        "correlated_event_overlap_watch",
    )
    assert blocked.manual_next_step == "manual_review_block_duplicate_exposure"

    assert cleared.collision_status == "clear"
    assert cleared.reason_codes == ("duplicate_exposure_collision_clear",)
    assert cleared.manual_next_step == "no_manual_action_required"

    assert watched.collision_status == "watch"
    assert watched.reason_codes == ("correlated_event_overlap_watch",)
    assert watched.manual_next_step == "manual_review_correlated_exposure"


def test_empty_duplicate_exposure_collision_report_is_clear_and_decimal_zeroed() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.blocker_count == d("0")
    assert result.attention_count == d("0")
    assert result.clear_count == d("0")
    assert result.collision_status == "clear"
    assert result.reason_codes == ("duplicate_exposure_collision_clear",)
    assert result.manual_next_step == "no_manual_action_required"
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_duplicate_exposure_collision_report_watches_threshold_overlaps() -> None:
    result = report(
        candidate(
            candidate_id="candidate_watch",
            correlated_event_count=d("0"),
            same_resolution_source_count=d("0"),
            existing_watchlist_overlap_count=d("1"),
            portfolio_exposure_overlap_probability=d("0.500000"),
        ),
        portfolio_exposure_overlap_watch_probability=d("0.250000"),
        portfolio_exposure_overlap_block_probability=d("0.750000"),
        correlated_event_watch_count=d("1"),
    )

    assert result.collision_status == "watch"
    assert result.reason_codes == (
        "watchlist_overlap_collision",
        "portfolio_exposure_overlap_watch",
    )
    assert result.manual_next_step == "manual_review_correlated_exposure"
    assert result.rows[0].collision_status == "watch"
    assert result.rows[0].reason_codes == (
        "watchlist_overlap_collision",
        "portfolio_exposure_overlap_watch",
    )


def test_direct_constructors_revalidate_decimal_boundaries_consistency_and_flags() -> None:
    module = api()
    result = report(
        candidate(
            candidate_id="candidate_block",
            same_resolution_source_count=d("1"),
            portfolio_exposure_overlap_probability=d("0.800000"),
        ),
    )

    rebuilt_row = module.ProbabilityEventDuplicateExposureCollisionRow(
        **{field.name: getattr(result.rows[0], field.name) for field in fields(result.rows[0])},
    )
    assert rebuilt_row == result.rows[0]

    with pytest.raises(ValueError, match="correlated_event_count"):
        candidate(correlated_event_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="portfolio_exposure_overlap_probability"):
        candidate(portfolio_exposure_overlap_probability=d("1.000001"))
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=" candidate_alpha")
    with pytest.raises(ValueError, match="unsafe public payload value"):
        candidate(event_ref="live_market_ref")
    with pytest.raises(ValueError, match="rows"):
        module.build_probability_event_duplicate_exposure_collision_report(
            (object(),),
            config=module.ProbabilityEventDuplicateExposureCollisionReportConfig(),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_probability_event_duplicate_exposure_collision_report(
            (),
            config=object(),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="collision_status"):
        replace(result.rows[0], collision_status="clear")
    with pytest.raises(FrozenInstanceError):
        result.collision_status = "clear"


def test_duplicate_exposure_collision_report_module_stays_leaf_readonly_report_only() -> None:
    import polymarket_alpha_lab.probability_event_duplicate_exposure_collision_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)
    project_imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported = node.module or ""
            if imported.startswith("polymarket_alpha_lab."):
                project_imports.add(imported)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("polymarket_alpha_lab."):
                    project_imports.add(alias.name)

    assert project_imports == set()
    lowered = source.lower()
    for forbidden in (
        ".read(",
        ".write(",
        "open(",
        "path",
        "logging",
        "logger",
        "client",
        "request",
        "response",
        "socket",
        "supabase",
        "database",
        "db",
        "persist",
        "live",
        "auth",
        "wallet",
        "order",
        "position",
        "trade",
    ):
        assert forbidden not in lowered
    assert "float" not in lowered
    assert "paper_only: bool = true" in lowered
    assert "report_only: bool = true" in lowered
    assert "readonly: bool = true" in lowered
