from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_cluster_correlation_v6"
GENERATED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 9, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


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
        "config_version": module.DEFAULT_STRATEGY_MARKET_CLUSTER_CORRELATION_V6_CONFIG_VERSION,
        "correlation_watch_score": d("0.450000"),
        "correlation_block_score": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyMarketClusterCorrelationV6Config(**values)


def market(
    market_slug: str = "market-alpha",
    *,
    category: str = "crypto",
    event_cluster: str = "election-2026",
    team: str = "team-alpha",
    shared_sources: tuple[str, ...] = ("polling", "liquidity"),
    probability_co_movement: Decimal = d("0.200000"),
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyMarketClusterCorrelationV6Market(
        market_slug=market_slug,
        category=category,
        event_cluster=event_cluster,
        team=team,
        shared_sources=shared_sources,
        probability_co_movement=probability_co_movement,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *markets: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_market_cluster_correlation_v6(
        markets,
        config=cfg or config(),
        generated_at=generated_at,
    )


def decimal_public_fields(value: object) -> tuple[str, ...]:
    return tuple(
        item.name
        for item in fields(value)
        if item.type is Decimal or "Decimal" in str(item.type)
    )


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_build_clusters_markets_by_category_event_team_sources_and_probability() -> None:
    result = report(
        market(
            "crypto-election-yes",
            category="crypto",
            event_cluster="election-2026",
            team="team-alpha",
            shared_sources=("polling", "liquidity"),
            probability_co_movement=d("0.780000"),
        ),
        market(
            "crypto-election-no",
            category="crypto",
            event_cluster="election-2026",
            team="team-alpha",
            shared_sources=("polling", "funding"),
            probability_co_movement=d("0.620000"),
            observed_at=GENERATED_AT - timedelta(minutes=20),
        ),
        market(
            "macro-rates",
            category="macro",
            event_cluster="fed-rates",
            team="team-macro",
            shared_sources=("fed-calendar",),
            probability_co_movement=d("0.200000"),
        ),
        market(
            "sports-finals",
            category="sports",
            event_cluster="nba-finals",
            team="team-sports",
            shared_sources=("injury-report",),
            probability_co_movement=d("0.100000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-cluster-correlation-v6"
    assert result.market_count == d("4")
    assert result.correlation_cluster_count == d("3")
    assert result.max_correlation_score == d("0.780000")
    assert result.blocked_market_count == d("1")
    assert result.watch_market_count == d("1")
    assert result.pass_market_count == d("2")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "category_overlap",
        "event_cluster_overlap",
        "probability_co_movement_blocked",
        "probability_co_movement_watch",
        "shared_sources_overlap",
        "team_overlap",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "crypto-election-yes",
        "crypto-election-no",
        "macro-rates",
        "sports-finals",
    )
    blocked = result.rows[0]
    assert blocked.rank == d("1")
    assert blocked.correlation_cluster == "crypto|election-2026|team-alpha"
    assert blocked.category_peer_count == d("1")
    assert blocked.event_cluster_peer_count == d("1")
    assert blocked.team_peer_count == d("1")
    assert blocked.shared_source_peer_count == d("1")
    assert blocked.correlation_score == d("0.780000")
    assert blocked.status == "blocked"
    assert blocked.reason_codes == (
        "category_overlap",
        "event_cluster_overlap",
        "probability_co_movement_blocked",
        "shared_sources_overlap",
        "team_overlap",
    )

    watched = result.rows[1]
    assert watched.rank == d("2")
    assert watched.correlation_score == d("0.620000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "category_overlap",
        "event_cluster_overlap",
        "probability_co_movement_watch",
        "shared_sources_overlap",
        "team_overlap",
    )

    passing = result.rows[2:]
    assert tuple(row.status for row in passing) == ("pass", "pass")
    assert tuple(row.reason_codes for row in passing) == (
        ("market_cluster_correlation_clear",),
        ("market_cluster_correlation_clear",),
    )


def test_empty_report_is_readonly_and_public_numeric_fields_are_decimal() -> None:
    empty = report()

    assert empty.market_count == d("0")
    assert empty.correlation_cluster_count == d("0")
    assert empty.max_correlation_score == ZERO
    assert empty.blocked_market_count == d("0")
    assert empty.watch_market_count == d("0")
    assert empty.pass_market_count == d("0")
    assert empty.status == "pass"
    assert empty.reason_codes == ("market_cluster_correlation_v6_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(market())
    for value in (config(), market(), *populated.rows, populated):
        for field_name in decimal_public_fields(value):
            assert type(getattr(value, field_name)) is Decimal


def test_payload_serializes_decimal_strings_and_contains_no_floats() -> None:
    module = api()
    result = report(
        market(
            observed_at=datetime(2026, 7, 6, 5, 45, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=datetime(2026, 7, 6, 6, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_market_cluster_correlation_v6_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-06T10:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["max_correlation_score"] == "0.200000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["correlation_score"] == "0.200000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T09:45:00+00:00"
    assert_no_float_values(payload)
    assert not re.search(r":\s*-?\d+\.\d+", encoded)


def test_dataclasses_validate_exact_types_times_flags_and_inputs() -> None:
    module = api()
    input_market = market()

    with pytest.raises(FrozenInstanceError):
        input_market.probability_co_movement = d("0.300000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report(input_market).rows[0].correlation_score = d("0.300000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability_co_movement must be a Decimal"):
        market(probability_co_movement=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_co_movement must be exactly Decimal"):
        market(probability_co_movement=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="category must be a nonblank trimmed string"):
        market(category=_StringSubclass("crypto"))
    with pytest.raises(ValueError, match="shared_sources must be a nonempty tuple"):
        market(shared_sources=())
    with pytest.raises(ValueError, match="shared_sources values must be unique"):
        market(shared_sources=("polling", "polling"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        market(observed_at=datetime(2026, 7, 6, 9, 45))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        market(observed_at=datetime(2026, 7, 6, 9, 45, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(input_market, generated_at=_DatetimeSubclass(2026, 7, 6, 10, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(market(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="paper_only"):
        market(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(input_market), readonly=False)
    with pytest.raises(ValueError, match="correlation_watch_score"):
        config(correlation_watch_score=d("0.800000"))
    with pytest.raises(ValueError, match="markets must be an iterable"):
        module.build_strategy_market_cluster_correlation_v6(
            "not-markets",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="markets must contain exact"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_market_cluster_correlation_v6(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_market_cluster_correlation_v6_payload(object())


def test_direct_constructors_validate_consistency_and_stable_ranking() -> None:
    result = report(
        market(
            "b-market",
            category="crypto",
            event_cluster="same-event",
            team="same-team",
            shared_sources=("same-source",),
            probability_co_movement=d("0.500000"),
        ),
        market(
            "a-market",
            category="crypto",
            event_cluster="same-event",
            team="same-team",
            shared_sources=("same-source",),
            probability_co_movement=d("0.500000"),
        ),
    )

    assert tuple(row.market_slug for row in result.rows) == ("a-market", "b-market")
    row = result.rows[0]

    with pytest.raises(ValueError, match="correlation_score"):
        replace(row, correlation_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="pass")
    with pytest.raises(ValueError, match="rank"):
        replace(row, rank=d("0"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("category_overlap", "category_overlap"))
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="market_count"):
        replace(result, market_count=d("3"))


def test_module_is_pure_report_readonly_and_has_no_runtime_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_cluster_correlation_v6.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    banned_names = {
        "open",
        "print",
        "exec",
        "eval",
        "compile",
        "connect",
        "request",
        "urlopen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_names
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    lowered = source.lower()
    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "trade",
        "database",
        "supabase",
    )
    assert [term for term in forbidden_terms if term in lowered] == []


def test_public_exports_are_explicit() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_STRATEGY_MARKET_CLUSTER_CORRELATION_V6_CONFIG_VERSION",
        "StrategyMarketClusterCorrelationV6Config",
        "StrategyMarketClusterCorrelationV6Market",
        "StrategyMarketClusterCorrelationV6Report",
        "StrategyMarketClusterCorrelationV6Row",
        "build_strategy_market_cluster_correlation_v6",
        "strategy_market_cluster_correlation_v6_payload",
    }
