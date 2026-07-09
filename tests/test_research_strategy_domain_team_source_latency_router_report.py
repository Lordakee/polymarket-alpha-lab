from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_team_source_latency_router_report.py"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_domain_team_source_latency_router_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    route_ref: str,
    domain_label: str,
    team_label: str,
    lane_label: str,
    *,
    observed_at: datetime,
    routed_at: datetime | None,
    freshness_score: Decimal,
    confidence_score: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyDomainTeamSourceLatencyRouterInput(
        route_ref=route_ref,
        domain_label=domain_label,
        team_label=team_label,
        lane_label=lane_label,
        observed_at=observed_at,
        routed_at=routed_at,
        freshness_score=freshness_score,
        confidence_score=confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchStrategyDomainTeamSourceLatencyRouterConfig(**overrides)


def _build_report(*items, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_domain_team_source_latency_router_report(
        items,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_latency_router_builds_deterministic_sanitized_public_payload() -> None:
    module = api()
    passing = _input(
        "raw-candidate-id private-market-id slug question https://example.invalid",
        "macro",
        "alpha_research",
        "official_feed",
        observed_at=GENERATED_AT - timedelta(minutes=10),
        routed_at=GENERATED_AT - timedelta(minutes=5),
        freshness_score=d("0.930000"),
        confidence_score=d("0.910000"),
    )
    watched = _input(
        "source_url source_text dsn table token wallet order trade",
        "sports",
        "event_research",
        "expert_feed",
        observed_at=GENERATED_AT - timedelta(minutes=30),
        routed_at=GENERATED_AT - timedelta(minutes=10),
        freshness_score=d("0.650000"),
        confidence_score=d("0.800000"),
    )
    blocked = _input(
        "buy sell recommendation sizing raw private route",
        "policy",
        "resolution_research",
        "authority_feed",
        observed_at=GENERATED_AT - timedelta(hours=2),
        routed_at=None,
        freshness_score=d("0.200000"),
        confidence_score=d("0.300000"),
    )

    report = _build_report(passing, watched, blocked)
    permuted = _build_report(blocked, passing, watched)
    payload = module.research_strategy_domain_team_source_latency_router_report_payload(
        report,
    )
    digest_payload = (
        module.research_strategy_domain_team_source_latency_router_digest_payload(report)
    )
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.observation_count == d("3.000000")
    assert report.group_count == d("3.000000")
    assert report.pass_count == ONE
    assert report.watch_count == ONE
    assert report.block_count == ONE
    assert report.missing_route_count == ONE
    assert report.average_latency_seconds == d("750.000000")
    assert report.max_latency_seconds == d("1200.000000")
    assert report.min_freshness_score == d("0.200000")
    assert report.min_confidence_score == d("0.300000")
    assert report.public_payload_digest == expected_digest
    assert report.public_payload_digest == (
        module.research_strategy_domain_team_source_latency_router_digest(report)
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passing_row = report.rows
    assert blocked_row.rank == ONE
    assert blocked_row.domain_label == "policy"
    assert blocked_row.team_label == "resolution_research"
    assert blocked_row.lane_label == "authority_feed"
    assert blocked_row.sample_count == ONE
    assert blocked_row.routed_count == ZERO
    assert blocked_row.missing_route_count == ONE
    assert blocked_row.average_latency_seconds == ZERO
    assert blocked_row.max_latency_seconds == ZERO
    assert blocked_row.min_freshness_score == d("0.200000")
    assert blocked_row.min_confidence_score == d("0.300000")
    assert blocked_row.reason_codes == (
        "domain_team_source_latency_router_block",
        "missing_route_timestamp",
        "freshness_below_block_threshold",
        "confidence_below_block_threshold",
    )
    assert watched_row.status == "watch"
    assert watched_row.average_latency_seconds == d("1200.000000")
    assert watched_row.reason_codes == (
        "domain_team_source_latency_router_watch",
        "latency_above_watch_threshold",
        "freshness_below_watch_threshold",
    )
    assert passing_row.status == "pass"
    assert passing_row.average_latency_seconds == d("300.000000")
    assert passing_row.reason_codes == ("domain_team_source_latency_router_pass",)

    assert payload == (
        module.research_strategy_domain_team_source_latency_router_report_payload(
            permuted,
        )
    )
    assert payload["public_payload_digest"] == report.public_payload_digest
    assert payload["rows"][0]["public_payload_digest"] == (
        blocked_row.public_payload_digest
    )
    assert payload["rows"][1]["average_latency_seconds"] == "1200.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _number_paths(payload) == ()
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-id",
        "private-market-id",
        "slug",
        "question",
        "https://example.invalid",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in encoded


def test_empty_latency_router_report_blocks_without_private_refs() -> None:
    module = api()
    generated_at = datetime(2026, 7, 9, 11, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = _build_report(generated_at=generated_at)
    payload = module.research_strategy_domain_team_source_latency_router_report_payload(
        report,
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.observation_count == ZERO
    assert report.group_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.missing_route_count == ZERO
    assert report.average_latency_seconds == ZERO
    assert report.max_latency_seconds == ZERO
    assert report.min_freshness_score == ZERO
    assert report.min_confidence_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("domain_team_source_latency_router_missing_inputs",)
    assert payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_payload_digest"] == report.public_payload_digest


def test_decimal_only_frozen_flags_and_strict_validation() -> None:
    module = api()
    report = _build_report(
        _input(
            "opaque-private-route",
            "macro",
            "alpha_research",
            "official_feed",
            observed_at=GENERATED_AT - timedelta(minutes=7),
            routed_at=GENERATED_AT - timedelta(minutes=1),
            freshness_score=d("0.900000"),
            confidence_score=d("0.900000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert is_dataclass(module.ResearchStrategyDomainTeamSourceLatencyRouterInput)
    assert is_dataclass(module.ResearchStrategyDomainTeamSourceLatencyRouterConfig)
    assert is_dataclass(module.ResearchStrategyDomainTeamSourceLatencyRouterRow)
    assert is_dataclass(module.ResearchStrategyDomainTeamSourceLatencyRouterReport)
    assert all(field.default is True for field in fields(report)[-3:])
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="freshness_score must be a Decimal"):
        _input(
            "opaque-private-route",
            "macro",
            "alpha_research",
            "official_feed",
            observed_at=GENERATED_AT,
            routed_at=GENERATED_AT,
            freshness_score=1,  # type: ignore[arg-type]
            confidence_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="confidence_score must be a Decimal"):
        _input(
            "opaque-private-route",
            "macro",
            "alpha_research",
            "official_feed",
            observed_at=GENERATED_AT,
            routed_at=GENERATED_AT,
            freshness_score=d("0.900000"),
            confidence_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        _build_report(generated_at=_DateTimeSubclass(2026, 7, 9, tzinfo=UTC))
    with pytest.raises(ValueError, match="config must be"):
        _build_report(config=object())
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.ResearchStrategyDomainTeamSourceLatencyRouterRow(
            rank=ONE,
            domain_label="macro",
            team_label="alpha_research",
            lane_label="official_feed",
            sample_count=ONE,
            routed_count=ONE,
            missing_route_count=ZERO,
            average_latency_seconds=ZERO,
            max_latency_seconds=ZERO,
            min_freshness_score=d("0.900000"),
            min_confidence_score=d("0.900000"),
            status="blocked",
            reason_codes=("domain_team_source_latency_router_pass",),
            public_payload_digest="0" * 64,
        )


def test_module_has_no_live_or_storage_surface_imports() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    }
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SOURCE_LATENCY_ROUTER_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchStrategyDomainTeamSourceLatencyRouterConfig",
        "ResearchStrategyDomainTeamSourceLatencyRouterInput",
        "ResearchStrategyDomainTeamSourceLatencyRouterReasonCodeCount",
        "ResearchStrategyDomainTeamSourceLatencyRouterReport",
        "ResearchStrategyDomainTeamSourceLatencyRouterRow",
        "build_research_strategy_domain_team_source_latency_router_report",
        "research_strategy_domain_team_source_latency_router_digest",
        "research_strategy_domain_team_source_latency_router_digest_payload",
        "research_strategy_domain_team_source_latency_router_report_payload",
    }
    public_name_blob = " ".join(module.__all__).lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "order",
        "trade",
        "auth",
        "live",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in public_name_blob


def _number_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return ()
    if isinstance(value, (int, float)):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        return tuple(
            path
            for key, item in value.items()
            for path in _number_paths(item, f"{prefix}.{key}" if prefix else str(key))
        )
    if isinstance(value, list):
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _number_paths(item, f"{prefix}[{index}]")
        )
    return ()
