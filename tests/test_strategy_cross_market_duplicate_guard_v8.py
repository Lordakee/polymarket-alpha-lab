from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 14, 0, tzinfo=timezone(timedelta(hours=-4)))


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_cross_market_duplicate_guard_v8",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {"config_version": "strategy-cross-market-duplicate-guard-v8-test"}
    values.update(overrides)
    return module.StrategyCrossMarketDuplicateGuardV8Config(**values)


def market(
    market_slug: str = "fed-september-cut-main",
    *,
    event_slug: str | None = "fomc-september-2026-rate-cut",
    question: str = "Will the Fed cut rates by September 17, 2026?",
    resolution_criteria: str = (
        "This market resolves Yes if the Federal Reserve lowers the target "
        "federal funds rate on or before September 17 2026."
    ),
    research_priority_score: Decimal = d("0.800000"),
    **overrides: object,
) -> Any:
    module = api()
    values = {
        "market_slug": market_slug,
        "event_slug": event_slug,
        "question": question,
        "resolution_criteria": resolution_criteria,
        "research_priority_score": research_priority_score,
    }
    values.update(overrides)
    return module.StrategyCrossMarketDuplicateGuardV8Market(**values)


def build_report(*markets: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_cross_market_duplicate_guard_v8_report(
        markets,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def row_by_slug(report: Any, slug: str) -> Any:
    return {row.market_slug: row for row in report.rows}[slug]


def test_same_event_markets_are_grouped_with_one_canonical_market() -> None:
    report = build_report(
        market(
            "fed-september-cut-main",
            research_priority_score=d("0.910000"),
        ),
        market(
            "fed-september-cut-copy",
            research_priority_score=d("0.420000"),
        ),
        market(
            "wti-above-90",
            event_slug="wti-above-90-december-2026",
            question="Will WTI crude oil be above 90 dollars on December 31, 2026?",
            resolution_criteria=(
                "This market resolves Yes if WTI crude oil settles above 90 "
                "dollars on December 31 2026."
            ),
            research_priority_score=d("0.600000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == datetime(2026, 7, 6, 18, 0, tzinfo=UTC)
    assert report.config_version == "strategy-cross-market-duplicate-guard-v8-test"
    assert report.duplicate_status == "duplicates_found"
    assert report.market_count == d("3")
    assert report.duplicate_group_count == d("1")
    assert report.canonical_market_count == d("1")
    assert report.duplicate_market_count == d("1")
    assert report.unique_market_count == d("1")
    assert report.reason_codes == ("same_event_slug", "cross_market_duplicates_found")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    canonical = row_by_slug(report, "fed-september-cut-main")
    duplicate = row_by_slug(report, "fed-september-cut-copy")
    unique = row_by_slug(report, "wti-above-90")

    assert canonical.duplicate_status == "canonical"
    assert canonical.canonical_market_slug == "fed-september-cut-main"
    assert canonical.duplicate_group_id == "event:fomc-september-2026-rate-cut"
    assert canonical.group_market_count == d("2")
    assert canonical.reason_codes == ("same_event_slug", "canonical_market_selected")

    assert duplicate.duplicate_status == "duplicate"
    assert duplicate.canonical_market_slug == "fed-september-cut-main"
    assert duplicate.duplicate_group_id == "event:fomc-september-2026-rate-cut"
    assert duplicate.group_market_count == d("2")
    assert duplicate.reason_codes == ("same_event_slug", "duplicate_of_canonical_market")

    assert unique.duplicate_status == "unique"
    assert unique.canonical_market_slug == "wti-above-90"
    assert unique.duplicate_group_id == "unique:wti-above-90"
    assert unique.group_market_count == d("1")
    assert unique.reason_codes == ("no_cross_market_duplicate_detected",)


def test_highly_similar_resolution_criteria_are_grouped_across_events() -> None:
    report = build_report(
        market(
            "fed-lowers-rates-official",
            event_slug="fed-lowers-rates-official-event",
            resolution_criteria=(
                "Resolves Yes if the Federal Reserve lowers the target federal "
                "funds rate on or before September 17 2026."
            ),
            research_priority_score=d("0.880000"),
        ),
        market(
            "fomc-rate-cut-lookalike",
            event_slug="fomc-rate-cut-lookalike-event",
            resolution_criteria=(
                "Resolves Yes if the Federal Reserve lowers the target federal "
                "funds rate before September 17 2026."
            ),
            research_priority_score=d("0.550000"),
        ),
        market(
            "fed-hikes-rates",
            event_slug="fed-hikes-rates-event",
            resolution_criteria=(
                "Resolves Yes if the Federal Reserve raises the target federal "
                "funds rate after December 2026."
            ),
            research_priority_score=d("0.600000"),
        ),
        cfg=config(criteria_similarity_duplicate_threshold=d("0.700000")),
    )

    canonical = row_by_slug(report, "fed-lowers-rates-official")
    duplicate = row_by_slug(report, "fomc-rate-cut-lookalike")
    unrelated = row_by_slug(report, "fed-hikes-rates")

    assert report.duplicate_status == "duplicates_found"
    assert report.duplicate_group_count == d("1")
    assert report.reason_codes == (
        "resolution_criteria_highly_similar",
        "cross_market_duplicates_found",
    )

    assert canonical.duplicate_status == "canonical"
    assert canonical.canonical_market_slug == "fed-lowers-rates-official"
    assert canonical.duplicate_group_id == "criteria:fed-lowers-rates-official"
    assert canonical.criteria_similarity_score == d("1.000000")
    assert canonical.reason_codes == (
        "resolution_criteria_highly_similar",
        "canonical_market_selected",
    )

    assert duplicate.duplicate_status == "duplicate"
    assert duplicate.canonical_market_slug == "fed-lowers-rates-official"
    assert duplicate.duplicate_group_id == "criteria:fed-lowers-rates-official"
    assert duplicate.criteria_similarity_score == d("0.923077")
    assert duplicate.reason_codes == (
        "resolution_criteria_highly_similar",
        "duplicate_of_canonical_market",
    )

    assert unrelated.duplicate_status == "unique"
    assert unrelated.reason_codes == ("no_cross_market_duplicate_detected",)


def test_empty_report_is_clear_readonly_and_decimal_counted() -> None:
    report = build_report()

    assert report.generated_at == datetime(2026, 7, 6, 18, 0, tzinfo=UTC)
    assert report.duplicate_status == "clear"
    assert report.market_count == d("0")
    assert report.duplicate_group_count == d("0")
    assert report.canonical_market_count == d("0")
    assert report.duplicate_market_count == d("0")
    assert report.unique_market_count == d("0")
    assert report.reason_codes == ("no_markets_supplied",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_non_decimal_numerics_bad_thresholds_flags_and_naive_times() -> None:
    module = api()

    with pytest.raises(ValueError, match="research_priority_score must be a Decimal"):
        market(research_priority_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="research_priority_score must be a Decimal"):
        market(research_priority_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="criteria_similarity_duplicate_threshold must be between 0 and 1",
    ):
        config(criteria_similarity_duplicate_threshold=d("1.100000"))
    with pytest.raises(ValueError, match="market_slug must be a canonical nonblank string"):
        market(market_slug=" fed-september-cut-main ")
    with pytest.raises(ValueError, match="paper_only must be True"):
        market(paper_only=False)
    with pytest.raises(ValueError, match="markets must be a tuple"):
        module.build_strategy_cross_market_duplicate_guard_v8_report(
            [market()],  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_cross_market_duplicate_guard_v8_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 18, 0),
        )


def test_public_dataclasses_are_frozen_and_exports_are_stable() -> None:
    module = api()
    report = build_report(market("fed-september-cut-main"))

    assert module.__all__ == (
        "DEFAULT_STRATEGY_CROSS_MARKET_DUPLICATE_GUARD_V8_CONFIG_VERSION",
        "StrategyCrossMarketDuplicateGuardV8Config",
        "StrategyCrossMarketDuplicateGuardV8Market",
        "StrategyCrossMarketDuplicateGuardV8Report",
        "StrategyCrossMarketDuplicateGuardV8Row",
        "build_strategy_cross_market_duplicate_guard_v8_report",
        "strategy_cross_market_duplicate_guard_v8_payload",
    )
    assert is_dataclass(module.StrategyCrossMarketDuplicateGuardV8Config())
    assert is_dataclass(market("fed-september-cut-main"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.duplicate_status = "clear"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].duplicate_status = "duplicate"
    with pytest.raises(FrozenInstanceError):
        module.StrategyCrossMarketDuplicateGuardV8Config().criteria_similarity_duplicate_threshold = d(
            "0.700000",
        )


def test_payload_is_json_ready_decimal_stringed_and_float_free() -> None:
    module = api()
    report = build_report(
        market(
            "fed-september-cut-main",
            research_priority_score=d("0.910000"),
        ),
        market(
            "fed-september-cut-copy",
            research_priority_score=d("0.420000"),
        ),
    )

    payload = module.strategy_cross_market_duplicate_guard_v8_payload(report)

    assert payload["generated_at"] == "2026-07-06T18:00:00+00:00"
    assert payload["market_count"] == "2"
    assert payload["duplicate_market_count"] == "1"
    assert payload["rows"][0]["research_priority_score"] == "0.910000"
    assert payload["rows"][0]["criteria_similarity_score"] == "1.000000"
    json.dumps(payload)

    def assert_no_float_or_decimal_values(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_or_decimal_values(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_or_decimal_values(item)
        else:
            assert type(value) is not float
            assert type(value) is not Decimal

    assert_no_float_or_decimal_values(payload)


def test_module_scope_is_pure_readonly_report_without_io_db_or_live_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "subprocess",
        "broker",
        "wallet",
        "private_key",
        "credential",
        "submit",
        "cancel",
        "execute",
        "connect",
        "trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "post",
                "put",
                "delete",
                "send",
                "submit",
                "cancel",
            }
