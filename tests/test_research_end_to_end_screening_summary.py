from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_end_to_end_screening_summary import (
    DEFAULT_RESEARCH_END_TO_END_SCREENING_SUMMARY_CONFIG_VERSION,
    ResearchEndToEndScreeningInput,
    ResearchEndToEndScreeningPublicPayloadItem,
    ResearchEndToEndScreeningSummaryConfig,
    ResearchEndToEndScreeningSummaryReport,
    ResearchEndToEndScreeningSummaryRow,
    build_research_end_to_end_screening_summary,
    research_end_to_end_screening_summary_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_summary_with_redacted_decimal_payload_strings() -> None:
    report = build_research_end_to_end_screening_summary(
        (
            _input("item-b"),
            _input("item-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
        public_payload=(
            ResearchEndToEndScreeningPublicPayloadItem(
                key="review_scope",
                value="human research only",
            ),
        ),
    )

    assert isinstance(report, ResearchEndToEndScreeningSummaryReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_RESEARCH_END_TO_END_SCREENING_SUMMARY_CONFIG_VERSION
    )
    assert report.screening_status == "pass"
    assert report.manual_review_next_step == "human_research_standard_review"
    assert report.item_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_selection_quality_score == Decimal("0.850000")
    assert report.average_watchlist_fit_score == Decimal("0.800000")
    assert report.average_evidence_quality_score == Decimal("0.900000")
    assert report.average_cost_discipline_score == Decimal("0.800000")
    assert report.max_rule_risk_score == Decimal("0.100000")
    assert report.average_team_capacity_score == Decimal("0.700000")
    assert report.average_quality_assurance_score == Decimal("0.850000")
    assert report.average_aggregate_score == Decimal("0.828571")
    assert report.max_manual_review_priority_score == Decimal("0.180000")
    assert report.reason_codes == ("screening_summary_pass",)
    assert report.deterministic_summary == (
        "pass|items=2.000000|pass=2.000000|watch=0.000000|block=0.000000|"
        "selection_avg=0.850000|watchlist_avg=0.800000|evidence_avg=0.900000|"
        "cost_avg=0.800000|rule_risk_max=0.100000|team_avg=0.700000|"
        "qa_avg=0.850000|aggregate_avg=0.828571|reasons=screening_summary_pass"
    )
    assert tuple(row.screening_item_key for row in report.rows) == ("item-a", "item-b")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_end_to_end_screening_summary_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["screening_status"] == "pass"
    assert payload["item_count"] == "2.000000"
    assert payload["average_aggregate_score"] == "0.828571"
    assert payload["rows"][0]["aggregate_score"] == "0.828571"
    assert payload["rows"][0]["manual_review_priority_score"] == "0.180000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_watch_and_block_statuses_roll_up_deterministically() -> None:
    watch_report = build_research_end_to_end_screening_summary(
        (
            _input(
                "item-watch",
                selection_quality_score=Decimal("0.700000"),
                watchlist_fit_score=Decimal("0.600000"),
                rule_risk_score=Decimal("0.450000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )
    block_report = build_research_end_to_end_screening_summary(
        (
            _input("item-pass"),
            _input(
                "item-block",
                evidence_quality_score=Decimal("0.300000"),
                rule_risk_score=Decimal("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )

    assert watch_report.screening_status == "watch"
    assert watch_report.manual_review_next_step == "human_research_watchlist_review"
    assert watch_report.watch_count == Decimal("1.000000")
    assert watch_report.rows[0].reason_codes == (
        "selection_quality_watch",
        "watchlist_fit_watch",
        "rule_risk_watch",
    )

    assert block_report.screening_status == "block"
    assert block_report.manual_review_next_step == "human_research_hold_rework"
    assert block_report.block_count == Decimal("1.000000")
    assert tuple(row.screening_status for row in block_report.rows) == ("block", "pass")
    assert block_report.rows[0].reason_codes == (
        "evidence_quality_block",
        "rule_risk_block",
    )
    assert block_report.reason_codes == (
        "evidence_quality_block",
        "rule_risk_block",
        "screening_summary_pass",
    )


def test_empty_inputs_are_report_only_block() -> None:
    report = build_research_end_to_end_screening_summary(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )

    assert report.screening_status == "block"
    assert report.manual_review_next_step == "human_research_hold_rework"
    assert report.reason_codes == ("empty_input",)
    assert report.item_count == Decimal("0.000000")
    assert report.pass_ratio is None
    assert report.rows == ()
    assert report.average_aggregate_score == Decimal("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(ResearchEndToEndScreeningSummaryConfig)
    assert is_dataclass(ResearchEndToEndScreeningInput)
    assert is_dataclass(ResearchEndToEndScreeningSummaryRow)
    assert is_dataclass(ResearchEndToEndScreeningSummaryReport)

    with pytest.raises(ValueError, match="config_version"):
        ResearchEndToEndScreeningSummaryConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_selection_quality_score"):
        ResearchEndToEndScreeningSummaryConfig(min_selection_quality_score=1)
    with pytest.raises(ValueError, match="min_selection_quality_score"):
        ResearchEndToEndScreeningSummaryConfig(
            min_selection_quality_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="selection_quality_score"):
        _input("item-a", selection_quality_score="0.900000")
    with pytest.raises(ValueError, match="selection_quality_score"):
        _input("item-a", selection_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="cost_discipline_score"):
        _input("item-a", cost_discipline_score=Decimal("0.70"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        _input("item-a", team_capacity_score=0.7)
    with pytest.raises(ValueError, match="screening_status"):
        ResearchEndToEndScreeningSummaryRow(
            screening_item_key="item-a",
            selection_quality_score=Decimal("0.850000"),
            watchlist_fit_score=Decimal("0.800000"),
            evidence_quality_score=Decimal("0.900000"),
            cost_discipline_score=Decimal("0.800000"),
            rule_risk_score=Decimal("0.100000"),
            rule_clearance_score=Decimal("0.900000"),
            team_capacity_score=Decimal("0.700000"),
            quality_assurance_score=Decimal("0.850000"),
            aggregate_score=Decimal("0.828571"),
            manual_review_priority_score=Decimal("0.180000"),
            screening_status="blocked",
            manual_review_next_step="human_research_hold_rework",
            reason_codes=("screening_summary_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input("item-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchEndToEndScreeningSummaryConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchEndToEndScreeningSummaryConfig(readonly=False)

    report = build_research_end_to_end_screening_summary(
        (_input("item-a"),),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].screening_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "screening_item_key", "candidate-abc"),
        ("input", "screening_item_key", "market-abc"),
        ("input", "screening_item_key", "question-abc"),
        ("public_payload", "key", "source_ref"),
        ("public_payload", "key", "wallet"),
        ("public_payload", "key", "market_slug"),
        ("public_payload", "value", "https://example.test/ref"),
        ("public_payload", "value", "URL copied from private notes"),
        ("public_payload", "value", "source text copied from private notes"),
        ("public_payload", "value", "buy or sell recommendation"),
        ("public_payload", "value", "wallet auth token"),
        ("public_payload", "value", "order trade position"),
        ("public_payload", "value", "dsn table name"),
        ("public_payload", "value", "raw candidate id"),
        ("public_payload", "value", "market question text"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        if factory_name == "input":
            _input("item-a", **{field_name: field_value})
        else:
            values = {"key": "safe_key", "value": "safe public note"}
            values[field_name] = field_value
            ResearchEndToEndScreeningPublicPayloadItem(**values)


def test_public_payload_rejects_forbidden_surfaces_flag_downgrades_and_tampering() -> None:
    report = build_research_end_to_end_screening_summary(
        (_input("item-a"),),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
        public_payload=(
            ResearchEndToEndScreeningPublicPayloadItem(
                key="review_scope",
                value="human research only",
            ),
        ),
    )

    payload = research_end_to_end_screening_summary_payload(report)
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_end_to_end_screening_summary_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_end_to_end_screening_summary_payload(tampered)

    tampered = dict(payload)
    tampered["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_end_to_end_screening_summary_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_report_and_digest_are_deterministic() -> None:
    inputs = (
        _input("item-c", rule_risk_score=Decimal("0.900000")),
        _input("item-a"),
        _input("item-b", watchlist_fit_score=Decimal("0.600000")),
    )

    report_a = build_research_end_to_end_screening_summary(
        inputs,
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )
    report_b = build_research_end_to_end_screening_summary(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=ResearchEndToEndScreeningSummaryConfig(),
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_end_to_end_screening_summary_payload(
        report_a,
    ) == research_end_to_end_screening_summary_payload(report_b)
    assert tuple(row.screening_item_key for row in report_a.rows) == (
        "item-c",
        "item-b",
        "item-a",
    )


def test_module_scope_excludes_fetch_storage_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_end_to_end_screening_summary",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_END_TO_END_SCREENING_SUMMARY_CONFIG_VERSION",
        "ResearchEndToEndScreeningInput",
        "ResearchEndToEndScreeningPublicPayloadItem",
        "ResearchEndToEndScreeningSummaryConfig",
        "ResearchEndToEndScreeningSummaryReport",
        "ResearchEndToEndScreeningSummaryRow",
        "build_research_end_to_end_screening_summary",
        "research_end_to_end_screening_summary_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
        "sqlite",
        "urllib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for banned_call in (
        "submit_order",
        "cancel_order",
        "replace_order",
        "execute_trade",
        "live_trading",
    ):
        assert banned_call not in source


def _input(item_key: str, **overrides: object) -> ResearchEndToEndScreeningInput:
    values = {
        "screening_item_key": item_key,
        "selection_quality_score": Decimal("0.850000"),
        "watchlist_fit_score": Decimal("0.800000"),
        "evidence_quality_score": Decimal("0.900000"),
        "cost_discipline_score": Decimal("0.800000"),
        "rule_risk_score": Decimal("0.100000"),
        "team_capacity_score": Decimal("0.700000"),
        "quality_assurance_score": Decimal("0.850000"),
    }
    values.update(overrides)
    return ResearchEndToEndScreeningInput(**values)


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
        "source",
        "ref",
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
        "blocked",
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
