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
    "research_strategy_team_signal_conflict_memory_router_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


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
        "min_pass_calibration_memory_score": d("0.700000"),
        "min_watch_calibration_memory_score": d("0.500000"),
        "max_pass_memory_age_seconds": d("7776000.000000"),
        "max_watch_memory_age_seconds": d("15552000.000000"),
        "max_pass_evidence_age_seconds": d("86400.000000"),
        "max_watch_evidence_age_seconds": d("259200.000000"),
        "max_pass_disagreement_severity": d("0.250000"),
        "max_watch_disagreement_severity": d("0.500000"),
        "max_pass_liquidity_cost_pressure": d("0.300000"),
        "max_watch_liquidity_cost_pressure": d("0.600000"),
    }
    values |= overrides
    return module.ResearchStrategyTeamSignalConflictMemoryRouterConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "route_ref": "route-alpha",
        "participant_role": "analyst",
        "analyst_label": "analyst-alpha",
        "team_label": "macro-desk",
        "analyst_signal_direction": "support",
        "team_signal_direction": "neutral",
        "calibration_memory_score": d("0.850000"),
        "memory_observed_at": GENERATED_AT - timedelta(days=30),
        "evidence_observed_at": GENERATED_AT - timedelta(hours=6),
        "disagreement_severity": d("0.200000"),
        "liquidity_cost_pressure": d("0.150000"),
    }
    values |= overrides
    return module.ResearchStrategyTeamSignalConflictMemoryRouterSignal(**values)


def report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_team_signal_conflict_memory_router_report(
        signals,
        config=cfg if cfg is not None else config(),
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
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_routes_conflicting_analyst_signals_with_memory_freshness_and_cost_pressure() -> None:
    result = report(
        signal(
            route_ref="route-watch",
            analyst_label="analyst-beta",
            team_label="resolution-desk",
            analyst_signal_direction="support",
            team_signal_direction="oppose",
            calibration_memory_score=d("0.600000"),
            memory_observed_at=GENERATED_AT - timedelta(days=100),
            evidence_observed_at=GENERATED_AT - timedelta(days=2),
            disagreement_severity=d("0.400000"),
            liquidity_cost_pressure=d("0.400000"),
        ),
        signal(
            route_ref="route-pass",
            analyst_label="analyst-alpha",
            team_label="macro-desk",
            analyst_signal_direction="support",
            team_signal_direction="neutral",
            calibration_memory_score=d("0.850000"),
            memory_observed_at=GENERATED_AT - timedelta(days=30),
            evidence_observed_at=GENERATED_AT - timedelta(hours=6),
            disagreement_severity=d("0.200000"),
            liquidity_cost_pressure=d("0.150000"),
        ),
        signal(
            route_ref="route-block",
            analyst_label="analyst-gamma",
            team_label="liquidity-desk",
            analyst_signal_direction="oppose",
            team_signal_direction="support",
            calibration_memory_score=d("0.450000"),
            memory_observed_at=GENERATED_AT - timedelta(days=200),
            evidence_observed_at=GENERATED_AT - timedelta(days=4),
            disagreement_severity=d("0.700000"),
            liquidity_cost_pressure=d("0.750000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.signal_count == d("3")
    assert result.analyst_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.average_route_score == d("0.521852")
    assert result.max_disagreement_severity == d("0.700000")
    assert result.max_liquidity_cost_pressure == d("0.750000")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "calibration_memory_block",
        "memory_freshness_block",
        "evidence_freshness_block",
        "disagreement_severity_block",
        "liquidity_cost_pressure_block",
        "calibration_memory_watch",
        "memory_freshness_watch",
        "evidence_freshness_watch",
        "disagreement_severity_watch",
        "liquidity_cost_pressure_watch",
        "analyst_signal_conflict_route_pass",
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
    assert blocked.route_status == "block"
    assert blocked.memory_age_seconds == d("17280000.000000")
    assert blocked.evidence_age_seconds == d("345600.000000")
    assert blocked.memory_freshness_score == d("0.000000")
    assert blocked.evidence_freshness_score == d("0.000000")
    assert blocked.conflict_pressure_score == d("0.725000")
    assert blocked.route_score == d("0.200000")
    assert blocked.analyst_next_step == "block_analyst_signal_until_memory_review"
    assert blocked.reason_codes == (
        "calibration_memory_block",
        "memory_freshness_block",
        "evidence_freshness_block",
        "disagreement_severity_block",
        "liquidity_cost_pressure_block",
    )

    watched = result.rows[1]
    assert watched.route_status == "watch"
    assert watched.memory_age_seconds == d("8640000.000000")
    assert watched.evidence_age_seconds == d("172800.000000")
    assert watched.memory_freshness_score == d("0.444444")
    assert watched.evidence_freshness_score == d("0.333333")
    assert watched.conflict_pressure_score == d("0.400000")
    assert watched.route_score == d("0.515555")
    assert watched.analyst_next_step == "watch_analyst_signal_before_packet_use"
    assert watched.reason_codes == (
        "calibration_memory_watch",
        "memory_freshness_watch",
        "evidence_freshness_watch",
        "disagreement_severity_watch",
        "liquidity_cost_pressure_watch",
    )

    passed = result.rows[2]
    assert passed.route_status == "pass"
    assert passed.memory_freshness_score == d("0.833333")
    assert passed.evidence_freshness_score == d("0.916667")
    assert passed.conflict_pressure_score == d("0.175000")
    assert passed.route_score == d("0.850000")
    assert passed.analyst_next_step == "pass_analyst_signal_to_research_packet"
    assert passed.reason_codes == ("analyst_signal_conflict_route_pass",)


def test_memory_freshness_thresholds_are_boundary_aware() -> None:
    module = api()

    at_pass = report(
        signal(
            route_ref="route-pass-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=7776000),
        ),
    )
    just_watch = report(
        signal(
            route_ref="route-watch-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=7776001),
        ),
    )
    just_block = report(
        signal(
            route_ref="route-block-edge",
            memory_observed_at=GENERATED_AT - timedelta(seconds=15552001),
        ),
    )

    assert module.SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES == ("pass", "watch", "block")
    assert at_pass.rows[0].route_status == "pass"
    assert at_pass.rows[0].reason_codes == ("analyst_signal_conflict_route_pass",)
    assert just_watch.rows[0].route_status == "watch"
    assert just_watch.rows[0].reason_codes == ("memory_freshness_watch",)
    assert just_block.rows[0].route_status == "block"
    assert just_block.rows[0].reason_codes == ("memory_freshness_block",)


def test_public_payload_digest_is_deterministic_and_leak_checked() -> None:
    module = api()
    first = report(
        signal(route_ref="route-beta", analyst_label="analyst-beta"),
        signal(route_ref="route-alpha", analyst_label="analyst-alpha"),
    )
    second = report(
        signal(route_ref="route-alpha", analyst_label="analyst-alpha"),
        signal(route_ref="route-beta", analyst_label="analyst-beta"),
    )

    first_payload = (
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            first,
        )
    )
    second_payload = (
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            second,
        )
    )
    encoded = json.dumps(first_payload, sort_keys=True, allow_nan=False)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert (
        module.research_strategy_team_signal_conflict_memory_router_report_digest(first)
        == first.derived_validation_digest
    )
    assert first.public_payload == first_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["signal_count"] == "2"
    assert first_payload["rows"][0]["route_score"] == "0.850000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_float_or_int_values(first_payload)
    assert '"0.850000"' in encoded

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
        "sizing",
        "recommendation",
    )
    for term in forbidden_public_terms:
        assert term not in encoded

    tampered = dict(first_payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            tampered,
        )

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            unsafe_key,
        )

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "analyst_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            unsafe_value,
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_team_signal_conflict_memory_router_report_public_payload(
            {**first_payload, "signal_count": 2},
        )


def test_custom_config_validation_flags_datetimes_and_analysts_only() -> None:
    module = api()

    stricter = config(
        min_pass_calibration_memory_score=d("0.900000"),
        min_watch_calibration_memory_score=d("0.700000"),
        max_pass_memory_age_seconds=d("3600.000000"),
        max_watch_memory_age_seconds=d("7200.000000"),
        max_pass_evidence_age_seconds=d("3600.000000"),
        max_watch_evidence_age_seconds=d("7200.000000"),
    )
    result = report(
        signal(
            calibration_memory_score=d("0.800000"),
            memory_observed_at=GENERATED_AT - timedelta(seconds=5000),
            evidence_observed_at=GENERATED_AT - timedelta(seconds=5000),
        ),
        cfg=stricter,
    )
    assert result.rows[0].route_status == "watch"
    assert result.rows[0].reason_codes == (
        "calibration_memory_watch",
        "memory_freshness_watch",
        "evidence_freshness_watch",
    )

    with pytest.raises(ValueError, match="min_watch_calibration_memory_score"):
        config(
            min_pass_calibration_memory_score=d("0.700000"),
            min_watch_calibration_memory_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="max_watch_memory_age_seconds"):
        config(
            max_pass_memory_age_seconds=d("7200.000000"),
            max_watch_memory_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="max_pass_disagreement_severity"):
        config(
            max_pass_disagreement_severity=d("0.700000"),
            max_watch_disagreement_severity=d("0.600000"),
        )
    with pytest.raises(ValueError, match="calibration_memory_score must be a Decimal"):
        signal(calibration_memory_score=1)
    with pytest.raises(ValueError, match="participant_role must be analyst"):
        signal(participant_role="team")
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(
        ValueError,
        match="config must be exactly ResearchStrategyTeamSignalConflictMemoryRouterConfig",
    ):
        module.build_research_strategy_team_signal_conflict_memory_router_report(
            (signal(),),
            config=False,
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_team_signal_conflict_memory_router_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_team_signal_conflict_memory_router_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="route_ref values must be unique"):
        report(signal(), signal(analyst_label="analyst-beta"))

    frozen = report(signal())
    with pytest.raises(FrozenInstanceError):
        frozen.rows[0].route_status = "block"


def test_report_and_row_validation_recompute_digest_bound_fields() -> None:
    result = report(signal())
    row = result.rows[0]

    with pytest.raises(ValueError, match="memory_freshness_score must match"):
        replace(row, memory_freshness_score=row.memory_freshness_score + d("0.000001"))

    with pytest.raises(ValueError, match="route_score must match"):
        replace(row, route_score=row.route_score + d("0.000001"))

    with pytest.raises(ValueError, match="route_status must match"):
        replace(row, route_status="watch")

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
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_team_signal_conflict_memory_router_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))

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
        "DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_CONFLICT_MEMORY_ROUTER_CONFIG_VERSION",
        "SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES",
        "ResearchStrategyTeamSignalConflictMemoryRouterConfig",
        "ResearchStrategyTeamSignalConflictMemoryRouterReport",
        "ResearchStrategyTeamSignalConflictMemoryRouterRow",
        "ResearchStrategyTeamSignalConflictMemoryRouterSignal",
        "build_research_strategy_team_signal_conflict_memory_router_report",
        "research_strategy_team_signal_conflict_memory_router_report_digest",
        "research_strategy_team_signal_conflict_memory_router_report_public_payload",
    )
    for public_name in module.__all__:
        assert [
            fragment
            for fragment in forbidden_public_name_fragments
            if fragment in public_name.lower()
        ] == []
