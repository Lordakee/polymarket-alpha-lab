from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_team_router_confidence_report"
MODULE_PATH = Path("src/polymarket_alpha_lab/strategy_market_team_router_confidence_report.py")
GENERATED_AT = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_source_age_seconds": d("3600.000000"),
        "stale_source_age_seconds": d("86400.000000"),
        "min_pass_calibration_readiness_score": d("0.700000"),
        "min_watch_calibration_readiness_score": d("0.500000"),
        "min_pass_cost_gate_margin_score": d("0.250000"),
        "min_watch_cost_gate_margin_score": d("0.100000"),
        "min_pass_liquidity_score": d("0.700000"),
        "min_watch_liquidity_score": d("0.500000"),
        "max_pass_spread_score": d("0.200000"),
        "max_watch_spread_score": d("0.400000"),
    }
    values |= overrides
    return module.StrategyMarketTeamRouterConfidenceConfig(**values)


def input_item(**overrides: object) -> Any:
    module = api()
    values = {
        "routing_ref": "route-alpha",
        "market_category": "crypto",
        "domain_label": "crypto",
        "source_observed_at": GENERATED_AT - timedelta(minutes=30),
        "calibration_readiness_score": d("0.850000"),
        "cost_gate_margin_score": d("0.300000"),
        "liquidity_score": d("0.800000"),
        "spread_score": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values |= overrides
    return module.StrategyMarketTeamRouterConfidenceInput(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_market_team_router_confidence_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        if field.name.endswith(("_count", "_score", "_seconds")):
            assert type(item) is Decimal
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_raw_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_raw_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_numbers(item)


def test_builds_market_team_router_confidence_pass_watch_and_block() -> None:
    module = api()
    result = report(
        input_item(
            routing_ref="route-watch",
            market_category="sports.soccer",
            domain_label="sports.soccer",
            source_observed_at=GENERATED_AT - timedelta(hours=8),
            calibration_readiness_score=d("0.650000"),
            cost_gate_margin_score=d("0.150000"),
            liquidity_score=d("0.650000"),
            spread_score=d("0.300000"),
        ),
        input_item(
            routing_ref="route-pass",
            market_category="crypto",
            domain_label="crypto",
            source_observed_at=GENERATED_AT - timedelta(minutes=30),
            calibration_readiness_score=d("0.850000"),
            cost_gate_margin_score=d("0.300000"),
            liquidity_score=d("0.800000"),
            spread_score=d("0.100000"),
        ),
        input_item(
            routing_ref="route-block",
            market_category="macro",
            domain_label="macro",
            source_observed_at=GENERATED_AT - timedelta(days=2),
            calibration_readiness_score=d("0.400000"),
            cost_gate_margin_score=d("0.050000"),
            liquidity_score=d("0.400000"),
            spread_score=d("0.600000"),
        ),
    )

    assert module.STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS == (
        "high",
        "medium",
        "low",
    )
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.input_count == d("3")
    assert result.team_count == d("3")
    assert result.high_confidence_count == d("1")
    assert result.medium_confidence_count == d("1")
    assert result.low_confidence_count == d("1")
    assert result.average_confidence_score == d("0.537500")
    assert result.lowest_confidence_score == d("0.212500")
    assert result.highest_source_age_seconds == d("172800.000000")
    assert result.status == "block"
    assert result.blocker_reasons == (
        "source_freshness_block",
        "calibration_readiness_block",
        "cost_gate_margin_block",
        "liquidity_block",
        "spread_block",
        "source_freshness_watch",
        "calibration_readiness_watch",
        "cost_gate_margin_watch",
        "liquidity_watch",
        "spread_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.routing_ref for row in result.rows) == (
        "route-block",
        "route-watch",
        "route-pass",
    )

    blocked = result.rows[0]
    assert blocked.recommended_specialist_team == "team_macro"
    assert blocked.confidence_band == "low"
    assert blocked.source_age_seconds == d("172800.000000")
    assert blocked.source_freshness_score == d("0.000000")
    assert blocked.confidence_score == d("0.212500")
    assert blocked.blocker_reasons == (
        "source_freshness_block",
        "calibration_readiness_block",
        "cost_gate_margin_block",
        "liquidity_block",
        "spread_block",
    )

    watched = result.rows[1]
    assert watched.recommended_specialist_team == "team_soccer"
    assert watched.confidence_band == "medium"
    assert watched.source_age_seconds == d("28800.000000")
    assert watched.source_freshness_score == d("0.666667")
    assert watched.confidence_score == d("0.496667")
    assert watched.blocker_reasons == (
        "source_freshness_watch",
        "calibration_readiness_watch",
        "cost_gate_margin_watch",
        "liquidity_watch",
        "spread_watch",
    )

    passed = result.rows[2]
    assert passed.recommended_specialist_team == "team_crypto"
    assert passed.confidence_band == "high"
    assert passed.source_freshness_score == d("0.979167")
    assert passed.confidence_score == d("0.903333")
    assert passed.blocker_reasons == ("market_team_router_confidence_clear",)


def test_threshold_boundaries_are_inclusive_for_high_and_medium_bands() -> None:
    at_high = report(
        input_item(
            routing_ref="route-high-edge",
            source_observed_at=GENERATED_AT - timedelta(seconds=3600),
            calibration_readiness_score=d("0.700000"),
            cost_gate_margin_score=d("0.250000"),
            liquidity_score=d("0.700000"),
            spread_score=d("0.200000"),
        ),
    )
    just_medium = report(
        input_item(
            routing_ref="route-medium-edge",
            source_observed_at=GENERATED_AT - timedelta(seconds=3601),
        ),
    )
    just_low = report(
        input_item(
            routing_ref="route-low-edge",
            source_observed_at=GENERATED_AT - timedelta(seconds=86401),
        ),
    )

    assert at_high.rows[0].confidence_band == "high"
    assert at_high.rows[0].blocker_reasons == ("market_team_router_confidence_clear",)
    assert just_medium.rows[0].confidence_band == "medium"
    assert just_medium.rows[0].blocker_reasons == ("source_freshness_watch",)
    assert just_low.rows[0].confidence_band == "low"
    assert just_low.rows[0].blocker_reasons == ("source_freshness_block",)


def test_public_payload_digest_is_deterministic_and_rejects_leaks() -> None:
    module = api()
    first = report(
        input_item(routing_ref="route-beta", market_category="sports.tennis"),
        input_item(routing_ref="route-alpha", market_category="weather"),
    )
    second = report(
        input_item(routing_ref="route-alpha", market_category="weather"),
        input_item(routing_ref="route-beta", market_category="sports.tennis"),
    )

    first_payload = module.strategy_market_team_router_confidence_report_payload(first)
    second_payload = module.strategy_market_team_router_confidence_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True, allow_nan=False)

    assert first == second
    assert first_payload == second_payload
    assert first.public_payload == first_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert (
        module.strategy_market_team_router_confidence_report_digest(first)
        == first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-11T12:00:00+00:00"
    assert first_payload["input_count"] == "2"
    assert first_payload["rows"][0]["confidence_score"] == "0.903333"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_raw_numbers(first_payload)
    assert '"0.903333"' in encoded

    forbidden_public_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "https://",
        "postgres://",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "sizing",
        "recommendation",
    )
    for term in forbidden_public_terms:
        assert term not in encoded

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_market_team_router_confidence_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.strategy_market_team_router_confidence_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "domain_label": "market_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.strategy_market_team_router_confidence_report_payload(unsafe_value)

    with pytest.raises(ValueError, match="numeric"):
        module.strategy_market_team_router_confidence_report_payload(
            {**first_payload, "input_count": 2},
        )


def test_config_validation_flags_datetimes_unique_routes_and_freezing() -> None:
    module = api()
    stricter = config(
        min_pass_calibration_readiness_score=d("0.900000"),
        min_watch_calibration_readiness_score=d("0.700000"),
        fresh_source_age_seconds=d("1800.000000"),
        stale_source_age_seconds=d("7200.000000"),
    )
    result = report(
        input_item(
            calibration_readiness_score=d("0.800000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=5000),
        ),
        cfg=stricter,
    )
    assert result.rows[0].confidence_band == "medium"
    assert result.rows[0].blocker_reasons == (
        "source_freshness_watch",
        "calibration_readiness_watch",
    )

    with pytest.raises(ValueError, match="min_watch_calibration_readiness_score"):
        config(
            min_pass_calibration_readiness_score=d("0.700000"),
            min_watch_calibration_readiness_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="stale_source_age_seconds"):
        config(
            fresh_source_age_seconds=d("7200.000000"),
            stale_source_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="max_pass_spread_score"):
        config(max_pass_spread_score=d("0.500000"), max_watch_spread_score=d("0.400000"))
    with pytest.raises(ValueError, match="calibration_readiness_score must be a Decimal"):
        input_item(calibration_readiness_score=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        input_item(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="unsafe public text"):
        input_item(routing_ref="market_id=secret")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_market_team_router_confidence_report(
            (input_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 11, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_market_team_router_confidence_report(
            (input_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 11, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="routing_ref values must be unique"):
        report(input_item(), input_item(domain_label="macro"))

    frozen = report(input_item())
    with pytest.raises(FrozenInstanceError):
        frozen.rows[0].confidence_band = "low"


def test_report_and_row_validation_recompute_digest_bound_fields() -> None:
    result = report(input_item())
    row = result.rows[0]

    with pytest.raises(ValueError, match="source_freshness_score must match"):
        replace(row, source_freshness_score=row.source_freshness_score + d("0.000001"))
    with pytest.raises(ValueError, match="confidence_score must match"):
        replace(row, confidence_score=row.confidence_score + d("0.000001"))
    with pytest.raises(ValueError, match="confidence_band must match"):
        replace(row, confidence_band="medium")
    with pytest.raises(ValueError, match="high_confidence_count must match"):
        replace(result, high_confidence_count=result.high_confidence_count + d("1"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                router_row("route-zeta"),
                router_row("route-alpha"),
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def router_row(routing_ref: str) -> Any:
    return report(input_item(routing_ref=routing_ref)).rows[0]


def test_module_scope_is_paper_report_readonly_and_public_api_is_narrow() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_public_name_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "position",
        "sizing",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert module.__all__ == (
        "DEFAULT_STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_CONFIG_VERSION",
        "STRATEGY_MARKET_TEAM_ROUTER_CONFIDENCE_BANDS",
        "StrategyMarketTeamRouterConfidenceConfig",
        "StrategyMarketTeamRouterConfidenceInput",
        "StrategyMarketTeamRouterConfidenceReport",
        "StrategyMarketTeamRouterConfidenceRow",
        "build_strategy_market_team_router_confidence_report",
        "strategy_market_team_router_confidence_report_digest",
        "strategy_market_team_router_confidence_report_payload",
    )
    for public_name in module.__all__:
        assert [
            fragment
            for fragment in forbidden_public_name_fragments
            if fragment in public_name.lower()
        ] == []
