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
    / "strategy_market_information_half_life_score_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_information_half_life_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values = {
        "market_id": "alpha_event",
        "market_slug": "alpha-event",
        "information_half_life_hours": d("96"),
        "source_age_hours": d("12"),
        "source_diversity_score": d("0.800000"),
        "evidence_quality_score": d("0.900000"),
        "consensus_stability_score": d("0.850000"),
    }
    values.update(overrides)
    return module.StrategyMarketInformationHalfLifeScoreV2Input(**values)


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
            observation(market_id="alpha_event", market_slug="alpha-event"),
            observation(
                market_id="beta_fast_decay",
                market_slug="beta-fast-decay",
                information_half_life_hours=d("12"),
                source_age_hours=d("12"),
                source_diversity_score=d("0.600000"),
                evidence_quality_score=d("0.700000"),
                consensus_stability_score=d("0.650000"),
            ),
            observation(
                market_id="gamma_stale_sources",
                market_slug="gamma-stale-sources",
                information_half_life_hours=d("96"),
                source_age_hours=d("144"),
                source_diversity_score=d("0.550000"),
                evidence_quality_score=d("0.600000"),
                consensus_stability_score=d("0.500000"),
            ),
        )
    return module.build_strategy_market_information_half_life_score_v2(
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


def test_scores_information_half_life_and_source_recency_penalties() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.score_status == "blocked"
    assert report.market_count == d("3")
    assert report.pass_market_count == d("1")
    assert report.watch_market_count == d("1")
    assert report.blocked_market_count == d("1")
    assert report.average_half_life_score == d("0.670324")
    assert report.top_half_life_score == d("0.899722")
    assert report.bottom_half_life_score == d("0.483750")
    assert report.reason_codes == (
        "market_information_half_life_score_blocked_rows",
        "market_information_half_life_score_watch_rows",
    )

    rows = report.rows
    assert tuple(row.market_id for row in rows) == (
        "alpha_event",
        "gamma_stale_sources",
        "beta_fast_decay",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert rows[0].information_decay_score == d("1.000000")
    assert rows[0].source_recency_score == d("0.888889")
    assert rows[0].source_recency_penalty == d("0.111111")
    assert rows[0].market_information_half_life_score == d("0.899722")
    assert rows[0].score_status == "pass"
    assert rows[1].source_recency_score == d("0.400000")
    assert rows[1].source_recency_penalty == d("0.600000")
    assert rows[1].score_status == "watch"
    assert rows[2].information_decay_score == d("0.125000")
    assert rows[2].market_information_half_life_score == d("0.483750")
    assert rows[2].score_status == "blocked"


def test_fast_decay_market_with_fresh_sources_still_penalizes_decay() -> None:
    report = build_report(
        observation(
            information_half_life_hours=d("6"),
            source_age_hours=d("1"),
            source_diversity_score=d("0.950000"),
            evidence_quality_score=d("0.950000"),
            consensus_stability_score=d("0.900000"),
        ),
    )

    row = report.rows[0]
    assert row.information_decay_score == d("0.062500")
    assert row.source_recency_score == d("0.857143")
    assert row.source_recency_penalty == d("0.142857")
    assert row.market_information_half_life_score == d("0.697411")
    assert row.score_status == "watch"
    assert "information_decay_fast" in row.reason_codes


def test_source_recency_penalty_blocks_stale_sources() -> None:
    report = build_report(
        observation(
            information_half_life_hours=d("48"),
            source_age_hours=d("336"),
            source_diversity_score=d("0.900000"),
            evidence_quality_score=d("0.950000"),
            consensus_stability_score=d("0.900000"),
        ),
    )

    row = report.rows[0]
    assert row.source_recency_score == d("0.125000")
    assert row.source_recency_penalty == d("0.875000")
    assert row.market_information_half_life_score == d("0.616250")
    assert row.score_status == "blocked"
    assert "source_recency_stale" in row.reason_codes


def test_payload_serializes_decimals_as_strings_and_uses_hard_flags() -> None:
    report = build_report()
    payload = report.payload

    assert payload["market_count"] == "3"
    assert payload["average_half_life_score"] == "0.670324"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["source_recency_penalty"] == "0.111111"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyMarketInformationHalfLifeScoreV2Config()
    sample = observation()
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
                "stable_half_life_reference_hours",
                "information_decay_weight",
                "source_recency_weight",
                "source_diversity_weight",
                "evidence_quality_weight",
                "consensus_stability_weight",
                "pass_score_floor",
                "watch_score_floor",
                "information_half_life_hours",
                "source_age_hours",
                "source_diversity_score",
                "evidence_quality_score",
                "consensus_stability_score",
                "rank",
                "information_decay_score",
                "source_recency_score",
                "source_recency_penalty",
                "market_information_half_life_score",
                "market_count",
                "pass_market_count",
                "watch_market_count",
                "blocked_market_count",
                "average_half_life_score",
                "top_half_life_score",
                "bottom_half_life_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "information_half_life_hours",
            _DecimalSubclass("12"),
            "information_half_life_hours must be exactly Decimal",
        ),
        (
            "information_half_life_hours",
            d("0"),
            "information_half_life_hours must be positive",
        ),
        (
            "source_age_hours",
            d("-1"),
            "source_age_hours must be >= 0.000000",
        ),
        (
            "source_diversity_score",
            d("1.000001"),
            "source_diversity_score must be <= 1.000000",
        ),
        (
            "evidence_quality_score",
            d("0.9500004"),
            "evidence_quality_score must use six decimal places or fewer",
        ),
        (
            "consensus_stability_score",
            Decimal("NaN"),
            "consensus_stability_score must be finite",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        observation(**{field_name: bad_value})


def test_config_validation_rejects_bad_weights_thresholds_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="information_decay_weight must be exactly Decimal"):
        module.StrategyMarketInformationHalfLifeScoreV2Config(
            information_decay_weight=0,
        )
    with pytest.raises(
        ValueError,
        match="score weights must sum to 1.000000",
    ):
        module.StrategyMarketInformationHalfLifeScoreV2Config(
            source_recency_weight=d("0.260000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.StrategyMarketInformationHalfLifeScoreV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyMarketInformationHalfLifeScoreV2Config(paper_only=False)


def test_build_validation_rejects_wrong_types_and_disabled_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_observations must be an iterable"):
        module.build_strategy_market_information_half_life_score_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="market observation items must be StrategyMarketInformationHalfLifeScoreV2Input",
    ):
        module.build_strategy_market_information_half_life_score_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_market_information_half_life_score_v2(
            [observation()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_half_life_score=d("0.650000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_market",
        "auth_market",
        "wallet_market",
        "order_market",
        "network_market",
        "database_market",
        "persist_market",
        "signing_market",
        "mutation_market",
        "buy_market",
        "sell_market",
        "trade_market",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            observation(market_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_reason_codes_and_digest() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_market_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match score_status"):
        replace(report, reason_codes=("market_information_half_life_score_passed",))


def test_module_scope_has_no_network_auth_wallet_order_db_persistence_or_trading_surface() -> None:
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
