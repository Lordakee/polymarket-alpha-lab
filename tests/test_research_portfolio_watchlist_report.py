from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_portfolio_watchlist_report import (
    DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION,
    ResearchPortfolioWatchlistInput,
    ResearchPortfolioWatchlistPublicPayloadItem,
    ResearchPortfolioWatchlistReport,
    ResearchPortfolioWatchlistReportConfig,
    ResearchPortfolioWatchlistRow,
    build_research_portfolio_watchlist_report,
    research_portfolio_watchlist_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_watchlist_report_with_redacted_decimal_payload_strings() -> None:
    report = build_research_portfolio_watchlist_report(
        (
            _input("watch-b"),
            _input("watch-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )

    assert isinstance(report, ResearchPortfolioWatchlistReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION
    )
    assert report.watchlist_status == "pass"
    assert report.top_sorting_bucket == "ready_queue"
    assert report.item_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_aggregate_watchlist_score == Decimal("0.830000")
    assert report.max_rule_risk_score == Decimal("0.100000")
    assert report.reason_codes == ("watchlist_pass",)
    assert tuple(row.watchlist_item_key for row in report.rows) == (
        "watch-a",
        "watch-b",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_portfolio_watchlist_report_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["watchlist_status"] == "pass"
    assert payload["item_count"] == "2.000000"
    assert payload["rows"][0]["aggregate_watchlist_score"] == "0.830000"
    assert payload["rows"][0]["manual_review_priority_score"] == "0.192500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_watch_and_block_items_route_to_sorting_buckets() -> None:
    watch_report = build_research_portfolio_watchlist_report(
        (
            _input(
                "watch-item",
                strategy_scorecard_score=Decimal("0.700000"),
                rule_risk_score=Decimal("0.450000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )
    block_report = build_research_portfolio_watchlist_report(
        (
            _input("pass-item"),
            _input("block-item", cost_score=Decimal("0.200000")),
        ),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )

    assert watch_report.watchlist_status == "watch"
    assert watch_report.top_sorting_bucket == "watch_queue"
    assert watch_report.watch_count == Decimal("1.000000")
    assert watch_report.rows[0].sorting_bucket == "watch_queue"
    assert watch_report.rows[0].reason_codes == (
        "strategy_scorecard_watch",
        "rule_risk_watch",
    )

    assert block_report.watchlist_status == "block"
    assert block_report.top_sorting_bucket == "hold_rework"
    assert block_report.block_count == Decimal("1.000000")
    assert tuple(row.watchlist_status for row in block_report.rows) == (
        "block",
        "pass",
    )
    assert block_report.rows[0].sorting_bucket == "hold_rework"
    assert block_report.rows[0].reason_codes == ("cost_threshold_block",)
    assert block_report.reason_codes == ("cost_threshold_block", "watchlist_pass")


def test_empty_inputs_are_readonly_report_only_block() -> None:
    report = build_research_portfolio_watchlist_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )

    assert report.watchlist_status == "block"
    assert report.top_sorting_bucket == "hold_rework"
    assert report.reason_codes == ("empty_input",)
    assert report.item_count == Decimal("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(ResearchPortfolioWatchlistReportConfig)
    assert is_dataclass(ResearchPortfolioWatchlistInput)
    assert is_dataclass(ResearchPortfolioWatchlistRow)
    assert is_dataclass(ResearchPortfolioWatchlistReport)

    with pytest.raises(ValueError, match="config_version"):
        ResearchPortfolioWatchlistReportConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_snapshot_quality_score"):
        ResearchPortfolioWatchlistReportConfig(min_snapshot_quality_score=1)
    with pytest.raises(ValueError, match="min_snapshot_quality_score"):
        ResearchPortfolioWatchlistReportConfig(
            min_snapshot_quality_score=_DecimalSubclass("0.600000"),
        )
    with pytest.raises(ValueError, match="snapshot_quality_score"):
        _input("watch-a", snapshot_quality_score="0.900000")
    with pytest.raises(ValueError, match="snapshot_quality_score"):
        _input("watch-a", snapshot_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="cost_score"):
        _input("watch-a", cost_score=Decimal("0.70"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        _input("watch-a", team_capacity_score=0.7)
    with pytest.raises(ValueError, match="watchlist_status"):
        ResearchPortfolioWatchlistRow(
            watchlist_item_key="watch-a",
            snapshot_quality_score=Decimal("0.900000"),
            strategy_scorecard_score=Decimal("0.850000"),
            cost_score=Decimal("0.800000"),
            rule_risk_score=Decimal("0.100000"),
            rule_clearance_score=Decimal("0.900000"),
            team_capacity_score=Decimal("0.700000"),
            aggregate_watchlist_score=Decimal("0.830000"),
            manual_review_priority_score=Decimal("0.192500"),
            watchlist_status="blocked",
            sorting_bucket="hold_rework",
            reason_codes=("watchlist_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input("watch-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchPortfolioWatchlistReportConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchPortfolioWatchlistReportConfig(readonly=False)

    report = build_research_portfolio_watchlist_report(
        (_input("watch-a"),),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].watchlist_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "watchlist_item_key", "candidate-abc"),
        ("input", "watchlist_item_key", "market-abc"),
        ("input", "watchlist_item_key", "question-abc"),
        ("public_payload", "key", "raw_candidate_id"),
        ("public_payload", "key", "market_slug"),
        ("public_payload", "key", "source_ref"),
        ("public_payload", "key", "wallet"),
        ("public_payload", "value", "https://example.test/ref"),
        ("public_payload", "value", "source text copied from private notes"),
        ("public_payload", "value", "buy or sell recommendation"),
        ("public_payload", "value", "wallet auth token"),
        ("public_payload", "value", "order trade position"),
        ("public_payload", "value", "dsn table name"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        if factory_name == "input":
            _input("watch-a", **{field_name: field_value})
        else:
            values = {"key": "safe_key", "value": "safe public note"}
            values[field_name] = field_value
            ResearchPortfolioWatchlistPublicPayloadItem(**values)


def test_public_payload_does_not_expose_forbidden_surfaces_or_flag_downgrades() -> None:
    report = build_research_portfolio_watchlist_report(
        (_input("watch-a"),),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
        public_payload=(
            ResearchPortfolioWatchlistPublicPayloadItem(
                key="review_scope",
                value="human watchlist review only",
            ),
        ),
    )

    payload = research_portfolio_watchlist_report_payload(report)
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_portfolio_watchlist_report_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_portfolio_watchlist_report_payload(tampered)

    tampered = dict(payload)
    tampered["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_portfolio_watchlist_report_payload(tampered)


def test_report_digest_is_tamper_evident() -> None:
    report = build_research_portfolio_watchlist_report(
        (_input("watch-a"),),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())


def test_report_and_digest_are_deterministic() -> None:
    rows = (
        _input("watch-c", rule_risk_score=Decimal("0.900000")),
        _input("watch-a"),
        _input("watch-b", strategy_scorecard_score=Decimal("0.700000")),
    )

    report_a = build_research_portfolio_watchlist_report(
        rows,
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )
    report_b = build_research_portfolio_watchlist_report(
        tuple(reversed(rows)),
        generated_at=GENERATED_AT,
        config=ResearchPortfolioWatchlistReportConfig(),
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_portfolio_watchlist_report_payload(
        report_a,
    ) == research_portfolio_watchlist_report_payload(report_b)
    assert tuple(row.watchlist_item_key for row in report_a.rows) == (
        "watch-c",
        "watch-b",
        "watch-a",
    )


def test_module_scope_excludes_fetch_storage_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_portfolio_watchlist_report",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION",
        "ResearchPortfolioWatchlistInput",
        "ResearchPortfolioWatchlistPublicPayloadItem",
        "ResearchPortfolioWatchlistReport",
        "ResearchPortfolioWatchlistReportConfig",
        "ResearchPortfolioWatchlistRow",
        "build_research_portfolio_watchlist_report",
        "research_portfolio_watchlist_report_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _input(item_key: str, **overrides: object) -> ResearchPortfolioWatchlistInput:
    values = {
        "watchlist_item_key": item_key,
        "snapshot_quality_score": Decimal("0.900000"),
        "strategy_scorecard_score": Decimal("0.850000"),
        "cost_score": Decimal("0.800000"),
        "rule_risk_score": Decimal("0.100000"),
        "team_capacity_score": Decimal("0.700000"),
    }
    values.update(overrides)
    return ResearchPortfolioWatchlistInput(**values)


def _decimal_values_are_strings(value: object) -> bool:
    if isinstance(value, Decimal):
        return False
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return True


def _assert_public_payload_has_no_blocked_terms(payload: dict[str, object]) -> None:
    rendered = repr(payload).casefold()
    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "blocked",
    ):
        assert token not in rendered
