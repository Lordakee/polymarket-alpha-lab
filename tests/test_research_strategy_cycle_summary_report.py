from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_cycle_summary_report import (
    DEFAULT_RESEARCH_STRATEGY_CYCLE_SUMMARY_REPORT_CONFIG_VERSION,
    ResearchStrategyCycleSummaryPublicPayloadItem,
    ResearchStrategyCycleSummaryQueueItem,
    ResearchStrategyCycleSummaryReport,
    ResearchStrategyCycleSummaryReportConfig,
    ResearchStrategyCycleSummaryReportRow,
    build_research_strategy_cycle_summary_report,
    research_strategy_cycle_summary_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_summary_with_redacted_decimal_payload_strings() -> None:
    report = build_research_strategy_cycle_summary_report(
        (
            _queue_item("queue-b"),
            _queue_item("queue-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
        public_payload=(
            ResearchStrategyCycleSummaryPublicPayloadItem(
                key="review_scope",
                value="human screening only",
            ),
        ),
    )

    assert isinstance(report, ResearchStrategyCycleSummaryReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_RESEARCH_STRATEGY_CYCLE_SUMMARY_REPORT_CONFIG_VERSION
    )
    assert report.summary_status == "pass"
    assert report.queue_item_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_evidence_quality_score == Decimal("0.850000")
    assert report.average_team_capacity_score == Decimal("0.700000")
    assert report.average_cost_discipline_score == Decimal("0.800000")
    assert report.average_learning_state_score == Decimal("0.750000")
    assert report.average_cycle_summary_score == Decimal("0.775000")
    assert report.lowest_evidence_quality_score == Decimal("0.850000")
    assert report.reason_codes == ("cycle_summary_pass",)
    assert report.deterministic_summary == (
        "pass|queue_items=2.000000|pass=2.000000|watch=0.000000|"
        "block=0.000000|evidence_avg=0.850000|team_avg=0.700000|"
        "cost_avg=0.800000|learning_avg=0.750000|reasons=cycle_summary_pass"
    )
    assert tuple(row.anonymized_queue_key for row in report.rows) == (
        "queue-a",
        "queue-b",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_strategy_cycle_summary_report_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["summary_status"] == "pass"
    assert payload["queue_item_count"] == "2.000000"
    assert payload["average_cycle_summary_score"] == "0.775000"
    assert payload["rows"][0]["cycle_summary_score"] == "0.775000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_watch_and_block_statuses_roll_up_deterministically() -> None:
    report = build_research_strategy_cycle_summary_report(
        (
            _queue_item("queue-pass"),
            _queue_item(
                "queue-watch",
                evidence_quality_score=Decimal("0.700000"),
                learning_state_score=Decimal("0.600000"),
            ),
            _queue_item(
                "queue-block",
                team_capacity_score=Decimal("0.200000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
    )

    assert report.summary_status == "block"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert tuple(row.anonymized_queue_key for row in report.rows) == (
        "queue-block",
        "queue-watch",
        "queue-pass",
    )
    assert report.rows[0].summary_status == "block"
    assert report.rows[0].reason_codes == ("team_capacity_block",)
    assert report.rows[1].summary_status == "watch"
    assert report.rows[1].reason_codes == (
        "evidence_quality_watch",
        "learning_state_watch",
    )
    assert report.reason_codes == (
        "team_capacity_block",
        "evidence_quality_watch",
        "learning_state_watch",
        "cycle_summary_pass",
    )


def test_empty_queue_is_report_only_block() -> None:
    report = build_research_strategy_cycle_summary_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
    )

    assert report.summary_status == "block"
    assert report.reason_codes == ("empty_queue",)
    assert report.queue_item_count == Decimal("0.000000")
    assert report.pass_ratio is None
    assert report.average_cycle_summary_score == Decimal("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(ResearchStrategyCycleSummaryReportConfig)
    assert is_dataclass(ResearchStrategyCycleSummaryQueueItem)
    assert is_dataclass(ResearchStrategyCycleSummaryReportRow)
    assert is_dataclass(ResearchStrategyCycleSummaryReport)

    with pytest.raises(ValueError, match="config_version"):
        ResearchStrategyCycleSummaryReportConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_evidence_quality_score"):
        ResearchStrategyCycleSummaryReportConfig(min_evidence_quality_score=1)
    with pytest.raises(ValueError, match="min_evidence_quality_score"):
        ResearchStrategyCycleSummaryReportConfig(
            min_evidence_quality_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="evidence_quality_score"):
        _queue_item("queue-a", evidence_quality_score="0.900000")
    with pytest.raises(ValueError, match="evidence_quality_score"):
        _queue_item("queue-a", evidence_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="cost_discipline_score"):
        _queue_item("queue-a", cost_discipline_score=Decimal("0.70"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        _queue_item("queue-a", team_capacity_score=0.7)
    with pytest.raises(ValueError, match="summary_status"):
        ResearchStrategyCycleSummaryReportRow(
            anonymized_queue_key="queue-a",
            evidence_quality_score=Decimal("0.850000"),
            team_capacity_score=Decimal("0.700000"),
            cost_discipline_score=Decimal("0.800000"),
            learning_state_score=Decimal("0.750000"),
            cycle_summary_score=Decimal("0.775000"),
            summary_status="blocked",
            reason_codes=("cycle_summary_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_queue_item("queue-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchStrategyCycleSummaryReportConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchStrategyCycleSummaryReportConfig(readonly=False)

    report = build_research_strategy_cycle_summary_report(
        (_queue_item("queue-a"),),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].summary_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "anonymized_queue_key", "candidate-abc"),
        ("input", "anonymized_queue_key", "market-abc"),
        ("public_payload", "key", "source_ref"),
        ("public_payload", "key", "wallet"),
        ("public_payload", "value", "https://example.test/ref"),
        ("public_payload", "value", "source text copied from private notes"),
        ("public_payload", "value", "buy or sell recommendation"),
        ("public_payload", "value", "wallet auth token"),
        ("public_payload", "value", "order trade position"),
        ("public_payload", "value", "dsn table name"),
        ("public_payload", "value", "raw candidate id"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
    ) -> None:
        with pytest.raises(ValueError, match="unsafe public"):
            if factory_name == "input":
                if field_name == "anonymized_queue_key":
                    _queue_item(field_value)
                else:
                    _queue_item("queue-a", **{field_name: field_value})
            else:
                values = {"key": "safe_key", "value": "safe public note"}
                values[field_name] = field_value
            ResearchStrategyCycleSummaryPublicPayloadItem(**values)


def test_public_payload_does_not_expose_forbidden_surfaces_or_flag_downgrades() -> None:
    report = build_research_strategy_cycle_summary_report(
        (_queue_item("queue-a"),),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
        public_payload=(
            ResearchStrategyCycleSummaryPublicPayloadItem(
                key="review_scope",
                value="human screening only",
            ),
        ),
    )

    payload = research_strategy_cycle_summary_report_payload(report)
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_cycle_summary_report_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_cycle_summary_report_payload(tampered)

    tampered = dict(payload)
    tampered["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_cycle_summary_report_payload(tampered)


def test_report_digest_is_tamper_evident() -> None:
    report = build_research_strategy_cycle_summary_report(
        (_queue_item("queue-a"),),
        generated_at=GENERATED_AT,
        config=ResearchStrategyCycleSummaryReportConfig(),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_scope_stays_pure_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_strategy_cycle_summary_report.py",
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
    ):
        assert banned_call not in source


def _queue_item(
    anonymized_queue_key: str,
    *,
    evidence_quality_score: object = Decimal("0.850000"),
    team_capacity_score: object = Decimal("0.700000"),
    cost_discipline_score: object = Decimal("0.800000"),
    learning_state_score: object = Decimal("0.750000"),
) -> ResearchStrategyCycleSummaryQueueItem:
    return ResearchStrategyCycleSummaryQueueItem(
        anonymized_queue_key=anonymized_queue_key,
        evidence_quality_score=evidence_quality_score,
        team_capacity_score=team_capacity_score,
        cost_discipline_score=cost_discipline_score,
        learning_state_score=learning_state_score,
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
