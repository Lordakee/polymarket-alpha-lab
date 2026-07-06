from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_cross_category_learning_router_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_cross_category_learning_router_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "specialist_id": "alpha_specialist",
        "source_category_id": "macro_rates",
        "target_category_id": "election_policy",
        "specialist_fit_score": d("0.950000"),
        "category_overlap_score": d("0.900000"),
        "transfer_signal_score": d("0.880000"),
        "evidence_quality_score": d("0.900000"),
        "stale_memory_days": d("0"),
    }
    values.update(overrides)
    return module.TeamSpecialistCrossCategoryLearningRouterV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            candidate(specialist_id="alpha_specialist"),
            candidate(
                specialist_id="beta_specialist",
                source_category_id="sports_liquidity",
                target_category_id="macro_rates",
                specialist_fit_score=d("0.720000"),
                category_overlap_score=d("0.650000"),
                transfer_signal_score=d("0.600000"),
                evidence_quality_score=d("0.700000"),
                stale_memory_days=d("6"),
            ),
            candidate(
                specialist_id="gamma_specialist",
                source_category_id="weather_events",
                target_category_id="sports_liquidity",
                specialist_fit_score=d("0.440000"),
                category_overlap_score=d("0.400000"),
                transfer_signal_score=d("0.350000"),
                evidence_quality_score=d("0.300000"),
                stale_memory_days=d("30"),
            ),
        )
    return module.build_team_specialist_cross_category_learning_router_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_routes_cross_category_learning_candidates_and_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.router_status == "blocked"
    assert report.candidate_count == d("3")
    assert report.route_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.average_learning_route_score == d("0.556167")
    assert report.top_learning_route_score == d("0.912500")
    assert report.bottom_learning_route_score == d("0.136500")
    assert report.reason_codes == (
        "cross_category_learning_router_blocked_rows",
        "cross_category_learning_router_watch_rows",
    )

    rows = report.rows
    assert tuple(row.specialist_id for row in rows) == (
        "alpha_specialist",
        "beta_specialist",
        "gamma_specialist",
    )
    assert tuple(row.category_pair_id for row in rows) == (
        "macro_rates__election_policy",
        "sports_liquidity__macro_rates",
        "weather_events__sports_liquidity",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.learning_route_score for row in rows) == (
        d("0.912500"),
        d("0.619500"),
        d("0.136500"),
    )
    assert tuple(row.route_status for row in rows) == ("route", "watch", "blocked")

    payload = report.payload
    assert payload["candidate_count"] == "3"
    assert payload["average_learning_route_score"] == "0.556167"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["learning_route_score"] == "0.912500"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_specialist_fit_scoring_controls_ranking() -> None:
    low_fit = candidate(
        specialist_id="low_fit_specialist",
        specialist_fit_score=d("0.300000"),
        category_overlap_score=d("0.900000"),
        transfer_signal_score=d("0.900000"),
        evidence_quality_score=d("0.900000"),
        stale_memory_days=d("0"),
    )
    high_fit = candidate(
        specialist_id="high_fit_specialist",
        specialist_fit_score=d("0.900000"),
        category_overlap_score=d("0.900000"),
        transfer_signal_score=d("0.900000"),
        evidence_quality_score=d("0.900000"),
        stale_memory_days=d("0"),
    )

    report = build_report(low_fit, high_fit)

    assert tuple(row.specialist_id for row in report.rows) == (
        "high_fit_specialist",
        "low_fit_specialist",
    )
    assert report.rows[0].learning_route_score == d("0.900000")
    assert report.rows[1].learning_route_score == d("0.690000")
    assert report.rows[0].reason_codes[:2] == (
        "cross_category_learning_route",
        "specialist_fit_strong",
    )
    assert report.rows[1].reason_codes[:2] == (
        "cross_category_learning_watch",
        "specialist_fit_weak",
    )


def test_stale_memory_penalties_reduce_scores_and_can_block_routes() -> None:
    fresh = candidate(
        specialist_id="fresh_specialist",
        specialist_fit_score=d("0.700000"),
        category_overlap_score=d("0.700000"),
        transfer_signal_score=d("0.700000"),
        evidence_quality_score=d("0.700000"),
        stale_memory_days=d("0"),
    )
    stale = candidate(
        specialist_id="stale_specialist",
        specialist_fit_score=d("0.700000"),
        category_overlap_score=d("0.700000"),
        transfer_signal_score=d("0.700000"),
        evidence_quality_score=d("0.700000"),
        stale_memory_days=d("30"),
    )

    report = build_report(fresh, stale)

    assert tuple(row.specialist_id for row in report.rows) == (
        "fresh_specialist",
        "stale_specialist",
    )
    assert report.rows[0].stale_memory_penalty == d("0.000000")
    assert report.rows[1].stale_memory_penalty == d("0.250000")
    assert report.rows[0].learning_route_score == d("0.700000")
    assert report.rows[1].learning_route_score == d("0.450000")
    assert report.rows[1].route_status == "blocked"
    assert "stale_memory_stale" in report.rows[1].reason_codes


def test_empty_router_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.router_status == "blocked"
    assert report.candidate_count == d("0")
    assert report.average_learning_route_score == d("0.000000")
    assert report.top_learning_route_score == d("0.000000")
    assert report.bottom_learning_route_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("cross_category_learning_router_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistCrossCategoryLearningRouterV2Config()
    sample = candidate()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "category_overlap_weight",
                "specialist_fit_weight",
                "transfer_signal_weight",
                "evidence_quality_weight",
                "stale_memory_penalty_weight",
                "max_stale_memory_days",
                "route_score_floor",
                "watch_score_floor",
                "specialist_fit_score",
                "category_overlap_score",
                "transfer_signal_score",
                "evidence_quality_score",
                "stale_memory_days",
                "rank",
                "stale_memory_penalty",
                "learning_route_score",
                "candidate_count",
                "route_count",
                "watch_count",
                "blocked_count",
                "average_learning_route_score",
                "top_learning_route_score",
                "bottom_learning_route_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "specialist_fit_score",
            _DecimalSubclass("0.900000"),
            "specialist_fit_score must be exactly Decimal",
        ),
        (
            "category_overlap_score",
            d("1.000001"),
            "category_overlap_score must be <= 1.000000",
        ),
        (
            "transfer_signal_score",
            d("0.8500004"),
            "transfer_signal_score must use six decimal places or fewer",
        ),
        (
            "evidence_quality_score",
            Decimal("NaN"),
            "evidence_quality_score must be finite",
        ),
        (
            "stale_memory_days",
            d("1.5"),
            "stale_memory_days must be an integral Decimal",
        ),
        (
            "stale_memory_days",
            d("-1"),
            "stale_memory_days must be >= 0.000000",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        candidate(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="category_overlap_weight must be exactly Decimal"):
        module.TeamSpecialistCrossCategoryLearningRouterV2Config(
            category_overlap_weight=0,
        )
    with pytest.raises(
        ValueError,
        match="router weights must sum to 1.000000",
    ):
        module.TeamSpecialistCrossCategoryLearningRouterV2Config(
            transfer_signal_weight=d("0.260000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed route_score_floor"):
        module.TeamSpecialistCrossCategoryLearningRouterV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCrossCategoryLearningRouterV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="learning_candidates must be an iterable"):
        module.build_team_specialist_cross_category_learning_router_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="learning candidate items must be TeamSpecialistCrossCategoryLearningRouterV2Input",
    ):
        module.build_team_specialist_cross_category_learning_router_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_cross_category_learning_router_v2(
            [candidate()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        candidate(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_learning_route_score=d("0.550000"),
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_specialist",
        "auth_specialist",
        "wallet_specialist",
        "order_specialist",
        "network_specialist",
        "database_specialist",
        "persist_specialist",
        "signing_specialist",
        "mutation_specialist",
        "buy_specialist",
        "sell_specialist",
        "trade_specialist",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            candidate(specialist_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": 0.5})


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            route_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match router_status"):
        replace(
            report,
            reason_codes=("cross_category_learning_router_routed",),
        )


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
