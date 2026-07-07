from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_event_team_router_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_event_team_router_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(**overrides: object):
    module = api()
    values = {
        "packet_id": "packet-btc-etf-flows",
        "event_slug": "btc-etf-flows-july",
        "category_id": "finance.crypto.btc",
        "source_ids": ("source-sec-calendar", "source-cftc-flows"),
        "received_at": GENERATED_AT - timedelta(hours=1),
        "resolution_deadline_at": GENERATED_AT + timedelta(hours=6),
    }
    values.update(overrides)
    return module.ResearchPacketEventTeamRouterV2Packet(**values)


def profile(**overrides: object):
    module = api()
    values = {
        "team_id": "crypto_btc",
        "category_id": "finance.crypto.btc",
        "domain_fit_score": d("0.950000"),
        "calibration_score": d("0.800000"),
        "backlog_pressure_score": d("0.200000"),
        "source_familiarity_score": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchPacketEventTeamRouterV2TeamProfile(**values)


def route(packet_value: object | None = None, profiles: object | None = None):
    module = api()
    return module.route_research_packet_event_team_router_v2(
        packet_value if packet_value is not None else packet(),
        profiles=(
            profiles
            if profiles is not None
            else (
                profile(),
                profile(
                    team_id="crypto_eth",
                    category_id="finance.crypto.eth",
                    domain_fit_score=d("0.300000"),
                    calibration_score=d("0.900000"),
                    backlog_pressure_score=d("0.100000"),
                    source_familiarity_score=d("0.900000"),
                ),
                profile(
                    team_id="politics",
                    category_id="politics",
                    domain_fit_score=d("0.050000"),
                    calibration_score=d("0.950000"),
                    backlog_pressure_score=d("0.050000"),
                    source_familiarity_score=d("0.200000"),
                ),
            )
        ),
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_decimal_or_datetime(value: Any) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"unexpected raw public value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_datetime(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_or_datetime(item)


def test_routes_packet_to_best_domain_calibrated_team_with_urgent_resolution() -> None:
    decision = route()

    assert is_dataclass(decision)
    assert decision.assigned_team_id == "crypto_btc"
    assert decision.route_status == "assigned"
    assert decision.time_to_resolution_hours == d("6.000000")
    assert decision.time_to_resolution_urgency_score == d("1.000000")
    assert decision.assigned_routing_score == d("87.250000")
    assert decision.runner_up_team_id == "crypto_eth"
    assert decision.runner_up_routing_score == d("64.000000")
    assert decision.assignment_margin == d("23.250000")
    assert decision.reason_codes == (
        "domain_fit_leader",
        "calibration_supported",
        "source_familiarity_supported",
        "time_resolution_urgent",
        "team_selected_crypto_btc",
    )
    assert tuple(row.team_id for row in decision.team_scores) == (
        "crypto_btc",
        "crypto_eth",
        "politics",
    )
    assert decision.team_scores[0].rank_sequence == d("1")
    assert decision.team_scores[0].backlog_relief_score == d("0.800000")
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_backlog_pressure_can_divert_to_better_available_specialist() -> None:
    basketball_packet = packet(
        packet_id="packet-basketball-finals",
        event_slug="basketball-finals-series-score",
        category_id="sports.basketball",
        source_ids=("source-lineup-report",),
        resolution_deadline_at=GENERATED_AT + timedelta(hours=48),
    )

    decision = route(
        basketball_packet,
        (
            profile(
                team_id="sports_basketball",
                category_id="sports.basketball",
                domain_fit_score=d("0.900000"),
                calibration_score=d("0.600000"),
                backlog_pressure_score=d("0.950000"),
                source_familiarity_score=d("0.400000"),
            ),
            profile(
                team_id="sports_other",
                category_id="sports.other",
                domain_fit_score=d("0.700000"),
                calibration_score=d("0.850000"),
                backlog_pressure_score=d("0.050000"),
                source_familiarity_score=d("0.800000"),
            ),
        ),
    )

    assert decision.assigned_team_id == "sports_other"
    assert decision.time_to_resolution_urgency_score == d("0.000000")
    assert decision.assigned_routing_score == d("79.750000")
    assert decision.runner_up_team_id == "sports_basketball"
    assert decision.assignment_margin == d("18.750000")
    assert "backlog_pressure_diverted" in decision.reason_codes


def test_payload_serializes_decimals_as_strings_and_is_tamper_evident() -> None:
    module = api()
    decision = route()

    payload = module.research_packet_event_team_router_v2_payload(decision)

    assert payload["config_version"] == "research-packet-event-team-router-v2"
    assert payload["assigned_team_id"] == "crypto_btc"
    assert payload["time_to_resolution_hours"] == "6.000000"
    assert payload["assigned_routing_score"] == "87.250000"
    assert payload["team_scores"][0]["routing_score"] == "87.250000"
    assert payload["team_scores"][0]["rank_sequence"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == decision.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_public_float_or_int(payload)
    assert_no_decimal_or_datetime(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decision, assigned_team_id="crypto_eth")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decision, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="decision"):
        module.research_packet_event_team_router_v2_payload(object())


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    decision = route()

    for klass in (
        module.ResearchPacketEventTeamRouterV2Config,
        module.ResearchPacketEventTeamRouterV2Packet,
        module.ResearchPacketEventTeamRouterV2TeamProfile,
        module.ResearchPacketEventTeamRouterV2TeamScore,
        module.ResearchPacketEventTeamRouterV2Decision,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        decision.assigned_team_id = "crypto_eth"  # type: ignore[misc]

    for public_record in (
        module.ResearchPacketEventTeamRouterV2Config(),
        packet(),
        profile(),
        decision.team_scores[0],
        decision,
    ):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="domain_fit_score"):
        profile(domain_fit_score=1)
    with pytest.raises(ValueError, match="calibration_score"):
        profile(calibration_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="backlog_pressure_score"):
        profile(backlog_pressure_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(packet(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(decision, readonly=False)


def test_validation_rejects_unknown_inputs_and_unsafe_public_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="packet"):
        module.route_research_packet_event_team_router_v2(object(), profiles=(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="team_profiles"):
        route(profiles=())
    with pytest.raises(ValueError, match="category_id"):
        packet(category_id="finance.crypto.doge")
    with pytest.raises(ValueError, match="source_ids"):
        packet(source_ids=("source-sec-calendar", "source-sec-calendar"))
    with pytest.raises(ValueError, match="resolution_deadline_at"):
        route(packet(resolution_deadline_at=GENERATED_AT - timedelta(minutes=1)))
    with pytest.raises(ValueError, match="unsafe"):
        packet(event_slug=f"btc-{'li' + 've'}-event")
    with pytest.raises(ValueError, match="unsafe"):
        profile(team_id="crypto_btc", category_id=f"{'wal' + 'let'}_ops")


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in source.lower()
