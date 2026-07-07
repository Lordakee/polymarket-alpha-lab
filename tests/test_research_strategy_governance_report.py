from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_governance_report import (
    DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION,
    ResearchStrategyGovernanceCheck,
    ResearchStrategyGovernancePublicNote,
    ResearchStrategyGovernanceReport,
    ResearchStrategyGovernanceReportConfig,
    ResearchStrategyGovernanceReportRow,
    build_research_strategy_governance_report,
    research_strategy_governance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_governance_report_with_deterministic_public_payload() -> None:
    report = build_research_strategy_governance_report(
        (
            _check("research-b"),
            _check("research-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchStrategyGovernanceReportConfig(),
        public_notes=(
            ResearchStrategyGovernancePublicNote(
                key="review_scope",
                value="human research only",
            ),
        ),
    )

    assert isinstance(report, ResearchStrategyGovernanceReport)
    assert (
        report.config_version
        == DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION
    )
    assert report.generated_at == GENERATED_AT
    assert report.governance_status == "pass"
    assert report.check_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_execution_boundary_score == Decimal("0.900000")
    assert report.average_quality_assurance_score == Decimal("0.850000")
    assert report.average_team_routing_score == Decimal("0.800000")
    assert report.average_data_feed_quality_score == Decimal("0.900000")
    assert report.average_local_memory_plan_score == Decimal("0.850000")
    assert report.average_governance_score == Decimal("0.860000")
    assert report.lowest_execution_boundary_score == Decimal("0.900000")
    assert report.reason_codes == ("governance_pass",)
    assert report.deterministic_summary == (
        "pass|checks=2.000000|pass=2.000000|watch=0.000000|"
        "block=0.000000|boundary_avg=0.900000|qa_avg=0.850000|"
        "routing_avg=0.800000|feed_avg=0.900000|memory_avg=0.850000|"
        "reasons=governance_pass"
    )
    assert tuple(row.anonymized_research_key for row in report.rows) == (
        "research-a",
        "research-b",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_strategy_governance_report_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["governance_status"] == "pass"
    assert payload["check_count"] == "2.000000"
    assert payload["average_governance_score"] == "0.860000"
    assert payload["rows"][0]["governance_score"] == "0.860000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_watch_and_block_rollups_cover_all_governance_domains() -> None:
    watch_report = build_research_strategy_governance_report(
        (
            _check(
                "research-watch",
                execution_boundary_score=Decimal("0.700000"),
                quality_assurance_score=Decimal("0.700000"),
                team_routing_score=Decimal("0.600000"),
                data_feed_quality_score=Decimal("0.700000"),
                local_memory_plan_score=Decimal("0.650000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchStrategyGovernanceReportConfig(),
    )

    assert watch_report.governance_status == "watch"
    assert watch_report.watch_count == Decimal("1.000000")
    assert watch_report.block_count == Decimal("0.000000")
    assert watch_report.rows[0].governance_status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "execution_boundary_watch",
        "quality_assurance_watch",
        "team_routing_watch",
        "data_feed_quality_watch",
        "local_memory_plan_watch",
    )

    block_report = build_research_strategy_governance_report(
        (
            _check("research-pass"),
            _check(
                "research-block",
                execution_boundary_score=Decimal("0.100000"),
                quality_assurance_score=Decimal("0.200000"),
                team_routing_score=Decimal("0.200000"),
                data_feed_quality_score=Decimal("0.200000"),
                local_memory_plan_score=Decimal("0.200000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchStrategyGovernanceReportConfig(),
    )

    assert block_report.governance_status == "block"
    assert block_report.pass_count == Decimal("1.000000")
    assert block_report.watch_count == Decimal("0.000000")
    assert block_report.block_count == Decimal("1.000000")
    assert tuple(row.anonymized_research_key for row in block_report.rows) == (
        "research-block",
        "research-pass",
    )
    assert block_report.rows[0].governance_status == "block"
    assert block_report.rows[0].reason_codes == (
        "execution_boundary_block",
        "quality_assurance_block",
        "team_routing_block",
        "data_feed_quality_block",
        "local_memory_plan_block",
    )
    assert block_report.reason_codes == (
        "execution_boundary_block",
        "quality_assurance_block",
        "team_routing_block",
        "data_feed_quality_block",
        "local_memory_plan_block",
        "governance_pass",
    )


def test_empty_governance_queue_blocks_without_action_language() -> None:
    report = build_research_strategy_governance_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchStrategyGovernanceReportConfig(),
    )

    assert report.governance_status == "block"
    assert report.reason_codes == ("empty_governance_queue",)
    assert report.check_count == Decimal("0.000000")
    assert report.pass_ratio is None
    assert report.average_governance_score == Decimal("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_strictly_typed() -> None:
    assert is_dataclass(ResearchStrategyGovernanceReportConfig)
    assert is_dataclass(ResearchStrategyGovernanceCheck)
    assert is_dataclass(ResearchStrategyGovernanceReportRow)
    assert is_dataclass(ResearchStrategyGovernanceReport)

    with pytest.raises(ValueError, match="config_version"):
        ResearchStrategyGovernanceReportConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_execution_boundary_score"):
        ResearchStrategyGovernanceReportConfig(min_execution_boundary_score=1)
    with pytest.raises(ValueError, match="min_execution_boundary_score"):
        ResearchStrategyGovernanceReportConfig(
            min_execution_boundary_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="execution_boundary_score"):
        _check("research-a", execution_boundary_score="0.900000")
    with pytest.raises(ValueError, match="execution_boundary_score"):
        _check("research-a", execution_boundary_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="quality_assurance_score"):
        _check("research-a", quality_assurance_score=Decimal("0.85"))
    with pytest.raises(ValueError, match="team_routing_score"):
        _check("research-a", team_routing_score=0.8)
    with pytest.raises(ValueError, match="governance_status"):
        ResearchStrategyGovernanceReportRow(
            anonymized_research_key="research-a",
            execution_boundary_score=Decimal("0.900000"),
            quality_assurance_score=Decimal("0.850000"),
            team_routing_score=Decimal("0.800000"),
            data_feed_quality_score=Decimal("0.900000"),
            local_memory_plan_score=Decimal("0.850000"),
            governance_score=Decimal("0.860000"),
            governance_status="hold",
            reason_codes=("governance_pass",),
        )
    with pytest.raises(ValueError, match="checks must be a list or tuple"):
        build_research_strategy_governance_report(  # type: ignore[arg-type]
            (_check("research-a") for _ in range(1)),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_check("research-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchStrategyGovernanceReportConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchStrategyGovernanceReportConfig(readonly=False)

    report = build_research_strategy_governance_report(
        (_check("research-a"),),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].governance_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("check", "anonymized_research_key", "candidate-abc"),
        ("check", "anonymized_research_key", "market-abc"),
        ("check", "anonymized_research_key", "raw_candidate_id"),
        ("public_note", "key", "source_ref"),
        ("public_note", "key", "wallet"),
        ("public_note", "value", "https://example.test/ref"),
        ("public_note", "value", "source text copied from private notes"),
        ("public_note", "value", "buy or sell recommendation"),
        ("public_note", "value", "wallet auth token"),
        ("public_note", "value", "order trade position"),
        ("public_note", "value", "dsn table name"),
        ("public_note", "value", "raw candidate id"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        if factory_name == "check":
            if field_name == "anonymized_research_key":
                _check(field_value)
            else:
                _check("research-a", **{field_name: field_value})
        else:
            values = {"key": "safe_key", "value": "human research only"}
            values[field_name] = field_value
            ResearchStrategyGovernancePublicNote(**values)


def test_public_payload_rejects_forbidden_surfaces_and_flag_downgrades() -> None:
    report = build_research_strategy_governance_report(
        (_check("research-a"),),
        generated_at=GENERATED_AT,
        public_notes=(
            ResearchStrategyGovernancePublicNote(
                key="review_scope",
                value="human research only",
            ),
        ),
    )

    payload = research_strategy_governance_report_payload(report)
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_governance_report_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_governance_report_payload(tampered)

    tampered = dict(payload)
    tampered["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_governance_report_payload(tampered)


def test_report_digest_is_tamper_evident() -> None:
    report = build_research_strategy_governance_report(
        (_check("research-a"),),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_payload_output_is_deterministic_for_same_governance_inputs() -> None:
    first = research_strategy_governance_report_payload(
        build_research_strategy_governance_report(
            (_check("research-b"), _check("research-a")),
            generated_at=GENERATED_AT,
        ),
    )
    second = research_strategy_governance_report_payload(
        build_research_strategy_governance_report(
            (_check("research-a"), _check("research-b")),
            generated_at=GENERATED_AT,
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_module_scope_stays_pure_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_strategy_governance_report.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "aiohttp",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "websocket",
        "websockets",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots

    for banned_call in (
        "submit_order",
        "cancel_order",
        "replace_order",
        "execute_trade",
        "live_trading",
        "connect",
        "commit",
        "insert",
        "update",
    ):
        assert banned_call not in source


def _check(
    anonymized_research_key: str,
    *,
    execution_boundary_score: object = Decimal("0.900000"),
    quality_assurance_score: object = Decimal("0.850000"),
    team_routing_score: object = Decimal("0.800000"),
    data_feed_quality_score: object = Decimal("0.900000"),
    local_memory_plan_score: object = Decimal("0.850000"),
) -> ResearchStrategyGovernanceCheck:
    return ResearchStrategyGovernanceCheck(
        anonymized_research_key=anonymized_research_key,
        execution_boundary_score=execution_boundary_score,
        quality_assurance_score=quality_assurance_score,
        team_routing_score=team_routing_score,
        data_feed_quality_score=data_feed_quality_score,
        local_memory_plan_score=local_memory_plan_score,
    )


def _decimal_values_are_strings(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float, Decimal)):
        return False
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return True


def _assert_public_payload_has_no_blocked_terms(value: Any) -> None:
    blocked_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source ref",
        "source_url",
        "source url",
        "source_text",
        "source text",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "recommendation",
    )
    if isinstance(value, str):
        normalized = value.lower()
        assert not any(term in normalized for term in blocked_terms)
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_public_payload_has_no_blocked_terms(key)
            _assert_public_payload_has_no_blocked_terms(item)
    elif isinstance(value, list):
        for item in value:
            _assert_public_payload_has_no_blocked_terms(item)
