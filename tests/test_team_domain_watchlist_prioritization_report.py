from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_domain_watchlist_prioritization_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 9, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_domain_watchlist_prioritization_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_ref": "candidate_alpha",
        "team_code": "team_macro",
        "domain": "politics",
        "information_freshness": d("0.900000"),
        "source_quorum": d("0.900000"),
        "edge_to_threshold": d("0.900000"),
        "liquidity": d("0.900000"),
        "cost_burden": d("0.100000"),
        "settlement_timing": d("0.900000"),
        "team_memory_calibration_readiness": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamDomainWatchlistPrioritizationCandidate(**values)


def report(*candidates: object):
    module = api()
    return module.build_team_domain_watchlist_prioritization_report(
        candidates,
        config=module.TeamDomainWatchlistPrioritizationConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_prioritizes_watchlist_by_team_domain_score_band_and_blockers() -> None:
    module = api()
    rows = (
        candidate(
            candidate_ref="candidate_ready",
            team_code="team_macro",
            domain="politics",
            information_freshness=d("0.940000"),
            source_quorum=d("0.930000"),
            edge_to_threshold=d("0.920000"),
            liquidity=d("0.910000"),
            cost_burden=d("0.080000"),
            settlement_timing=d("0.900000"),
            team_memory_calibration_readiness=d("0.890000"),
        ),
        candidate(
            candidate_ref="candidate_watch",
            team_code="team_crypto",
            domain="crypto",
            information_freshness=d("0.680000"),
            source_quorum=d("0.720000"),
            edge_to_threshold=d("0.610000"),
            liquidity=d("0.650000"),
            cost_burden=d("0.420000"),
            settlement_timing=d("0.580000"),
            team_memory_calibration_readiness=d("0.620000"),
        ),
        candidate(
            candidate_ref="candidate_block",
            team_code="team_sports",
            domain="soccer",
            information_freshness=d("0.300000"),
            source_quorum=d("0.490000"),
            edge_to_threshold=d("0.510000"),
            liquidity=d("0.400000"),
            cost_burden=d("0.830000"),
            settlement_timing=d("0.420000"),
            team_memory_calibration_readiness=d("0.450000"),
        ),
    )

    result = report(*reversed(rows))

    assert is_dataclass(result)
    assert module.TEAM_DOMAIN_WATCHLIST_PRIORITY_BANDS == ("ready", "watch", "defer")
    assert result.generated_at == GENERATED_AT
    assert (
        result.config_version
        == "team-domain-watchlist-prioritization-report-v1"
    )
    assert result.report_status == "block"
    assert result.candidate_count == d("3.000000")
    assert result.ready_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.defer_count == d("1.000000")
    assert result.average_priority_score == d("0.652267")
    assert result.max_priority_score == d("0.918600")
    assert result.min_priority_score == d("0.395700")
    assert result.reason_codes == (
        "team_domain_watchlist_prioritization_block",
        "candidate_defer_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert [(row.priority_rank, row.candidate_ref) for row in result.rows] == [
        (d("1.000000"), "candidate_ready"),
        (d("2.000000"), "candidate_watch"),
        (d("3.000000"), "candidate_block"),
    ]
    assert [(row.team_code, row.domain) for row in result.rows] == [
        ("team_macro", "politics"),
        ("team_crypto", "crypto"),
        ("team_sports", "soccer"),
    ]
    assert [row.priority_score for row in result.rows] == [
        d("0.918600"),
        d("0.642500"),
        d("0.395700"),
    ]
    assert [row.priority_band for row in result.rows] == ["ready", "watch", "defer"]
    assert result.rows[0].top_blockers == ("watchlist_candidate_ready",)
    assert result.rows[1].top_blockers == (
        "settlement_timing_watch",
        "edge_to_threshold_watch",
        "team_memory_calibration_readiness_watch",
    )
    assert result.rows[2].top_blockers == (
        "information_freshness_block",
        "liquidity_block",
        "settlement_timing_block",
    )


def test_payload_is_json_ready_decimal_stringed_deterministic_and_report_only() -> None:
    module = api()
    first = report(
        candidate(candidate_ref="candidate_ready"),
        candidate(
            candidate_ref="candidate_watch",
            team_code="team_crypto",
            domain="crypto",
            information_freshness=d("0.680000"),
            source_quorum=d("0.720000"),
            edge_to_threshold=d("0.610000"),
            liquidity=d("0.650000"),
            cost_burden=d("0.420000"),
            settlement_timing=d("0.580000"),
            team_memory_calibration_readiness=d("0.620000"),
        ),
    )
    second = report(*reversed(first.input_candidates))

    first_payload = module.team_domain_watchlist_prioritization_report_payload(first)
    second_payload = module.team_domain_watchlist_prioritization_report_payload(second)

    assert first_payload == first.payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["candidate_count"] == "2.000000"
    assert first_payload["rows"][0]["priority_score"] == "0.900000"
    assert first_payload["rows"][0]["priority_band"] == "ready"
    assert first_payload["validation_digest"] == first.validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_float_or_int_values(first_payload)
    assert module.validate_team_domain_watchlist_prioritization_report_payload(
        first_payload,
    )


def test_validation_requires_frozen_decimal_only_public_codes_and_hard_flags() -> None:
    module = api()
    result = report(candidate())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="information_freshness must be a Decimal"):
        candidate(information_freshness=1)

    with pytest.raises(ValueError, match="source_quorum must be a Decimal"):
        candidate(source_quorum=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="cost_burden must be between 0 and 1"):
        candidate(cost_burden=d("1.000001"))

    with pytest.raises(ValueError, match="candidate_ref must be a public code"):
        candidate(candidate_ref="raw candidate")

    with pytest.raises(ValueError, match="team_code must be a public code"):
        candidate(team_code="Team Macro")

    with pytest.raises(ValueError, match="domain must be supported"):
        candidate(domain="tennis")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="priority_band must be supported"):
        module.TeamDomainWatchlistPrioritizationRow(
            priority_rank=d("1.000000"),
            candidate_ref="candidate_ready",
            team_code="team_macro",
            domain="politics",
            information_freshness=d("0.900000"),
            source_quorum=d("0.900000"),
            edge_to_threshold=d("0.900000"),
            liquidity=d("0.900000"),
            cost_burden=d("0.100000"),
            settlement_timing=d("0.900000"),
            team_memory_calibration_readiness=d("0.900000"),
            priority_score=d("0.910000"),
            priority_band="trade",
            top_blockers=("watchlist_candidate_ready",),
        )


def test_public_numeric_fields_are_decimal_only_and_payload_rejects_tampering() -> None:
    module = api()
    decimal_fields = {
        "ready_priority_score",
        "watch_priority_score",
        "freshness_block_floor",
        "source_quorum_block_floor",
        "edge_to_threshold_block_floor",
        "liquidity_block_floor",
        "cost_burden_block_ceiling",
        "settlement_timing_block_floor",
        "team_memory_calibration_readiness_block_floor",
        "freshness_watch_floor",
        "source_quorum_watch_floor",
        "edge_to_threshold_watch_floor",
        "liquidity_watch_floor",
        "cost_burden_watch_ceiling",
        "settlement_timing_watch_floor",
        "team_memory_calibration_readiness_watch_floor",
        "information_freshness",
        "source_quorum",
        "edge_to_threshold",
        "liquidity",
        "cost_burden",
        "settlement_timing",
        "team_memory_calibration_readiness",
        "priority_rank",
        "priority_score",
        "candidate_count",
        "ready_count",
        "watch_count",
        "defer_count",
        "average_priority_score",
        "max_priority_score",
        "min_priority_score",
        "count",
    }

    for cls in (
        module.TeamDomainWatchlistPrioritizationConfig,
        module.TeamDomainWatchlistPrioritizationCandidate,
        module.TeamDomainWatchlistPrioritizationRow,
        module.TeamDomainWatchlistPrioritizationReasonCodeCount,
        module.TeamDomainWatchlistPrioritizationReport,
    ):
        for item in fields(cls):
            if item.name in decimal_fields:
                assert get_type_hints(cls)[item.name] is Decimal

    payload = module.team_domain_watchlist_prioritization_report_payload(
        report(candidate()),
    )
    assert module.team_domain_watchlist_prioritization_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["candidate_count"] = "2.000000"
    with pytest.raises(ValueError, match="validation_digest|candidate_count"):
        module.team_domain_watchlist_prioritization_report_payload(tampered)

    with pytest.raises(ValueError, match="Decimal"):
        numeric_payload = dict(payload)
        numeric_payload["candidate_count"] = 1
        module.team_domain_watchlist_prioritization_report_payload(numeric_payload)

    with pytest.raises(ValueError, match="paper_only"):
        flag_payload = dict(payload)
        flag_payload["paper_only"] = False
        module.team_domain_watchlist_prioritization_report_payload(flag_payload)


def test_empty_report_is_readonly_pass_with_decimal_zero_counts() -> None:
    empty = report()

    assert empty.candidate_count == d("0.000000")
    assert empty.ready_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.defer_count == d("0.000000")
    assert empty.average_priority_score == d("0.000000")
    assert empty.max_priority_score == d("0.000000")
    assert empty.min_priority_score == d("0.000000")
    assert empty.report_status == "pass"
    assert empty.reason_codes == ("team_domain_watchlist_prioritization_clear",)
    assert empty.rows == ()
    assert empty.reason_code_counts == (
        module_reason_count("team_domain_watchlist_prioritization_clear", d("1.000000")),
    )
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def module_reason_count(reason_code: str, count: Decimal):
    module = api()
    return module.TeamDomainWatchlistPrioritizationReasonCodeCount(
        reason_code=reason_code,
        count=count,
    )


def test_module_surface_is_pure_report_only_without_io_or_trading_terms() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_client",
        "insert",
        "update",
        "delete",
        "execute",
    }
    forbidden_text = (
        "wallet",
        "auth",
        "private_key",
        "live trading",
        "place_order",
        "database",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

    lowered = source.lower()
    for token in forbidden_text:
        assert token not in lowered
