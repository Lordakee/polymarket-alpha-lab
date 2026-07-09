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


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_team_signal_memory_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_domain_team_signal_memory_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)


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
        "min_pass_domain_memory_score": d("0.700000"),
        "min_watch_domain_memory_score": d("0.500000"),
        "min_pass_team_signal_score": d("0.700000"),
        "min_watch_team_signal_score": d("0.500000"),
        "max_pass_memory_age_seconds": d("604800.000000"),
        "max_watch_memory_age_seconds": d("1209600.000000"),
        "max_pass_router_conflict_score": d("0.250000"),
        "max_watch_router_conflict_score": d("0.500000"),
    }
    values |= overrides
    return module.ResearchStrategyDomainTeamSignalMemoryRouterConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "route_ref": "route-alpha",
        "domain_label": "macro",
        "team_label": "research-desk",
        "signal_label": "event-timing",
        "domain_memory_score": d("0.850000"),
        "team_signal_score": d("0.900000"),
        "memory_observed_at": GENERATED_AT - timedelta(days=3),
        "router_conflict_score": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values |= overrides
    return module.ResearchStrategyDomainTeamSignalMemoryRouterSignal(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_domain_team_signal_memory_router_report(
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


def test_builds_domain_team_signal_memory_router_pass_watch_and_block() -> None:
    module = api()
    result = report(
        signal(
            route_ref="route-watch",
            domain_label="rates",
            team_label="macro-desk",
            signal_label="policy-window",
            domain_memory_score=d("0.620000"),
            team_signal_score=d("0.650000"),
            memory_observed_at=GENERATED_AT - timedelta(days=10),
            router_conflict_score=d("0.350000"),
        ),
        signal(
            route_ref="route-pass",
            domain_label="weather",
            team_label="event-desk",
            signal_label="resolution-clock",
            domain_memory_score=d("0.850000"),
            team_signal_score=d("0.900000"),
            memory_observed_at=GENERATED_AT - timedelta(days=3),
            router_conflict_score=d("0.100000"),
        ),
        signal(
            route_ref="route-block",
            domain_label="crypto",
            team_label="source-desk",
            signal_label="source-drift",
            domain_memory_score=d("0.400000"),
            team_signal_score=d("0.450000"),
            memory_observed_at=GENERATED_AT - timedelta(days=20),
            router_conflict_score=d("0.700000"),
        ),
    )

    assert module.RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.signal_count == d("3")
    assert result.domain_count == d("3")
    assert result.team_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.average_router_score == d("0.565952")
    assert result.lowest_domain_memory_score == d("0.400000")
    assert result.lowest_team_signal_score == d("0.450000")
    assert result.highest_router_conflict_score == d("0.700000")
    assert result.highest_memory_age_seconds == d("1728000.000000")
    assert result.status == "block"
    assert result.reason_codes == (
        "domain_memory_block",
        "team_signal_block",
        "memory_age_block",
        "router_conflict_block",
        "domain_memory_watch",
        "team_signal_watch",
        "memory_age_watch",
        "router_conflict_watch",
        "domain_team_signal_memory_router_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.route_ref for row in result.rows) == (
        "route-block",
        "route-watch",
        "route-pass",
    )

    blocked = result.rows[0]
    assert blocked.status == "block"
    assert blocked.memory_age_seconds == d("1728000.000000")
    assert blocked.memory_freshness_score == d("0.000000")
    assert blocked.router_score == d("0.287500")
    assert blocked.router_next_step == "block_signal_until_domain_team_memory_review"
    assert blocked.reason_codes == (
        "domain_memory_block",
        "team_signal_block",
        "memory_age_block",
        "router_conflict_block",
    )

    watched = result.rows[1]
    assert watched.status == "watch"
    assert watched.memory_age_seconds == d("864000.000000")
    assert watched.memory_freshness_score == d("0.285714")
    assert watched.router_score == d("0.551428")
    assert watched.router_next_step == "watch_signal_before_research_packet_use"
    assert watched.reason_codes == (
        "domain_memory_watch",
        "team_signal_watch",
        "memory_age_watch",
        "router_conflict_watch",
    )

    passed = result.rows[2]
    assert passed.status == "pass"
    assert passed.memory_freshness_score == d("0.785714")
    assert passed.router_score == d("0.858928")
    assert passed.router_next_step == "pass_signal_to_research_packet"
    assert passed.reason_codes == ("domain_team_signal_memory_router_pass",)


def test_threshold_boundaries_are_inclusive_for_pass_and_watch() -> None:
    at_pass = report(
        signal(
            route_ref="route-pass-edge",
            domain_memory_score=d("0.700000"),
            team_signal_score=d("0.700000"),
            memory_observed_at=GENERATED_AT - timedelta(seconds=604800),
            router_conflict_score=d("0.250000"),
        ),
    )
    just_watch = report(
        signal(
            route_ref="route-watch-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=604801),
        ),
    )
    just_block = report(
        signal(
            route_ref="route-block-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=1209601),
        ),
    )

    assert at_pass.rows[0].status == "pass"
    assert at_pass.rows[0].reason_codes == ("domain_team_signal_memory_router_pass",)
    assert just_watch.rows[0].status == "watch"
    assert just_watch.rows[0].reason_codes == ("memory_age_watch",)
    assert just_block.rows[0].status == "block"
    assert just_block.rows[0].reason_codes == ("memory_age_block",)


def test_public_payload_digest_is_deterministic_and_rejects_leaks() -> None:
    module = api()
    first = report(
        signal(route_ref="route-beta", domain_label="rates"),
        signal(route_ref="route-alpha", domain_label="weather"),
    )
    second = report(
        signal(route_ref="route-alpha", domain_label="weather"),
        signal(route_ref="route-beta", domain_label="rates"),
    )

    first_payload = (
        module.research_strategy_domain_team_signal_memory_router_report_payload(first)
    )
    second_payload = (
        module.research_strategy_domain_team_signal_memory_router_report_payload(second)
    )
    encoded = json.dumps(first_payload, sort_keys=True, allow_nan=False)

    assert first == second
    assert first_payload == second_payload
    assert first.public_payload == first_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert (
        module.research_strategy_domain_team_signal_memory_router_report_digest(first)
        == first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert first_payload["signal_count"] == "2"
    assert first_payload["rows"][0]["router_score"] == "0.858928"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_raw_numbers(first_payload)
    assert '"0.858928"' in encoded

    forbidden_public_terms = (
        "candidate_id",
        "candidate",
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
        "sizing",
        "recommendation",
    )
    for term in forbidden_public_terms:
        assert term not in encoded

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_domain_team_signal_memory_router_report_payload(
            tampered,
        )

    unsafe_key = dict(first_payload)
    unsafe_key["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_domain_team_signal_memory_router_report_payload(
            unsafe_key,
        )

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "domain_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_domain_team_signal_memory_router_report_payload(
            unsafe_value,
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_domain_team_signal_memory_router_report_payload(
            {**first_payload, "signal_count": 2},
        )


def test_config_validation_flags_datetimes_unique_routes_and_freezing() -> None:
    module = api()
    stricter = config(
        min_pass_domain_memory_score=d("0.900000"),
        min_watch_domain_memory_score=d("0.700000"),
        max_pass_memory_age_seconds=d("3600.000000"),
        max_watch_memory_age_seconds=d("7200.000000"),
    )
    result = report(
        signal(
            domain_memory_score=d("0.800000"),
            memory_observed_at=GENERATED_AT - timedelta(seconds=5000),
        ),
        cfg=stricter,
    )
    assert result.rows[0].status == "watch"
    assert result.rows[0].reason_codes == (
        "domain_memory_watch",
        "memory_age_watch",
    )

    with pytest.raises(ValueError, match="min_watch_domain_memory_score"):
        config(
            min_pass_domain_memory_score=d("0.700000"),
            min_watch_domain_memory_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="max_watch_memory_age_seconds"):
        config(
            max_pass_memory_age_seconds=d("7200.000000"),
            max_watch_memory_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="max_pass_router_conflict_score"):
        config(
            max_pass_router_conflict_score=d("0.700000"),
            max_watch_router_conflict_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="domain_memory_score must be a Decimal"):
        signal(domain_memory_score=1)
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="unsafe public text"):
        signal(route_ref="candidate_id=secret")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_domain_team_signal_memory_router_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 15, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_domain_team_signal_memory_router_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="route_ref values must be unique"):
        report(signal(), signal(domain_label="rates"))

    frozen = report(signal())
    with pytest.raises(FrozenInstanceError):
        frozen.rows[0].status = "block"


def test_report_and_row_validation_recompute_digest_bound_fields() -> None:
    result = report(signal())
    row = result.rows[0]

    with pytest.raises(ValueError, match="memory_freshness_score must match"):
        replace(row, memory_freshness_score=row.memory_freshness_score + d("0.000001"))
    with pytest.raises(ValueError, match="router_score must match"):
        replace(row, router_score=row.router_score + d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="watch")
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))
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


def router_row(route_ref: str) -> Any:
    return report(signal(route_ref=route_ref)).rows[0]


def test_module_scope_is_report_only_readonly_and_public_api_is_narrow() -> None:
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
        "position",
        "sizing",
        "recommend",
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
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES",
        "ResearchStrategyDomainTeamSignalMemoryRouterConfig",
        "ResearchStrategyDomainTeamSignalMemoryRouterReport",
        "ResearchStrategyDomainTeamSignalMemoryRouterRow",
        "ResearchStrategyDomainTeamSignalMemoryRouterSignal",
        "build_research_strategy_domain_team_signal_memory_router_report",
        "research_strategy_domain_team_signal_memory_router_report_digest",
        "research_strategy_domain_team_signal_memory_router_report_payload",
    )
    for public_name in module.__all__:
        assert [
            fragment
            for fragment in forbidden_public_name_fragments
            if fragment in public_name.lower()
        ] == []
