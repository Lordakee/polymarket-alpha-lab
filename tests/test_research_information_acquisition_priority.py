from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_information_acquisition_priority import (
    DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION,
    ResearchInformationAcquisitionPriorityConfig,
    ResearchInformationAcquisitionPriorityInput,
    ResearchInformationAcquisitionPriorityReport,
    build_research_information_acquisition_priority_report,
    research_information_acquisition_priority_payload,
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_build_report_assigns_pass_watch_and_block_acquisition_priorities() -> None:
    report = build_research_information_acquisition_priority_report(
        (
            _input(
                "item-pass",
                evidence_gap_score=Decimal("0.000000"),
                source_age_hours=Decimal("2.000000"),
                source_reliability_score=Decimal("0.950000"),
                event_starts_in_hours=Decimal("96.000000"),
                team_sla_hours=Decimal("72.000000"),
            ),
            _input(
                "item-watch",
                evidence_gap_score=Decimal("0.400000"),
                source_age_hours=Decimal("36.000000"),
                source_reliability_score=Decimal("0.750000"),
                event_starts_in_hours=Decimal("24.000000"),
                team_sla_hours=Decimal("24.000000"),
            ),
            _input(
                "item-block",
                evidence_gap_score=Decimal("1.000000"),
                source_age_hours=Decimal("72.000000"),
                source_reliability_score=Decimal("0.200000"),
                event_starts_in_hours=Decimal("6.000000"),
                team_sla_hours=Decimal("6.000000"),
            ),
        ),
    )

    assert isinstance(report, ResearchInformationAcquisitionPriorityReport)
    assert report.config_version == DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION
    assert report.status == "block"
    assert report.acquisition_plan == "report_only_hold_until_collection_plan"
    assert report.item_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.acquisition_slot_ref for row in report.rows) == (
        "acquisition-slot-000001",
        "acquisition-slot-000002",
        "acquisition-slot-000003",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        Decimal("1.000000"),
        Decimal("2.000000"),
        Decimal("3.000000"),
    )
    assert report.rows[0].acquisition_priority == "collect_before_research_use"
    assert "evidence_gap_priority" in report.rows[0].reason_codes
    assert "source_stale_priority" in report.rows[0].reason_codes
    assert "event_timeline_compressed" in report.rows[0].reason_codes
    assert report.rows[-1].acquisition_priority == "defer_collection"
    assert len(report.derived_validation_digest) == 64


def test_empty_inputs_are_report_only_block() -> None:
    report = build_research_information_acquisition_priority_report(())

    assert report.status == "block"
    assert report.acquisition_plan == "report_only_hold_until_collection_plan"
    assert report.item_count == Decimal("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("information_acquisition_no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("evidence_gap_score", "0.100000"),
        ("source_age_hours", 1),
        ("source_reliability_score", 0.9),
        ("event_starts_in_hours", None),
        ("team_sla_hours", _DecimalSubclass("24.000000")),
    ),
)
def test_input_rejects_non_exact_decimal_driver_types(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "research_item_ref": "item-decimal",
        "evidence_gap_score": Decimal("0.100000"),
        "source_age_hours": Decimal("1.000000"),
        "source_reliability_score": Decimal("0.900000"),
        "event_starts_in_hours": Decimal("24.000000"),
        "team_sla_hours": Decimal("24.000000"),
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=f"{field_name} must be a Decimal"):
        ResearchInformationAcquisitionPriorityInput(**values)


def test_config_rejects_string_subclasses_and_decimal_subclasses() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchInformationAcquisitionPriorityConfig(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="watch_priority_score"):
        ResearchInformationAcquisitionPriorityConfig(
            watch_priority_score=_DecimalSubclass("0.250000"),
        )


@pytest.mark.parametrize(
    "unsafe_ref",
    (
        "candidate_123",
        "market_id_abc",
        "market_slug_abc",
        "question_will-this-resolve",
        "source_ref_private",
        "source_url_https_example",
        "source_text_private",
        "dsn_main",
        "orders_table",
        "token_secret",
        "wallet_alpha",
        "auth_header",
        "order_trade_position",
        "buy_signal",
        "sell_signal",
        "recommendation_signal",
    ),
)
def test_leak_rejection_for_input_references(unsafe_ref: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        _input(unsafe_ref)


def test_public_payload_does_not_expose_forbidden_or_raw_surfaces() -> None:
    report = build_research_information_acquisition_priority_report(
        (
            _input("item-safe-a"),
            _input(
                "item-safe-b",
                evidence_gap_score=Decimal("1.000000"),
                source_age_hours=Decimal("72.000000"),
                source_reliability_score=Decimal("0.250000"),
                event_starts_in_hours=Decimal("2.000000"),
                team_sla_hours=Decimal("6.000000"),
            ),
        ),
    )

    payload = research_information_acquisition_priority_payload(report)
    rendered = repr(payload).casefold()
    assert "item-safe-a" not in rendered
    assert "item-safe-b" not in rendered
    for token in (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
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
    ):
        assert token not in rendered

    tampered = dict(payload)
    tampered["private_note"] = "wallet auth token"
    with pytest.raises(ValueError, match="unsafe public"):
        research_information_acquisition_priority_payload(tampered)


def test_report_requires_hard_paper_report_readonly_flags() -> None:
    config = ResearchInformationAcquisitionPriorityConfig()
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    report = build_research_information_acquisition_priority_report(
        (_input("item-flags"),),
        config=config,
    )
    payload = research_information_acquisition_priority_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["acquisition_rows"][0]["paper_only"] is True
    assert payload["acquisition_rows"][0]["report_only"] is True
    assert payload["acquisition_rows"][0]["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        report.readonly = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(_input("item-report-only"), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_report_payload_and_digest_are_deterministic() -> None:
    rows = (
        _input("item-c", evidence_gap_score=Decimal("1.000000")),
        _input("item-a"),
        _input("item-b", evidence_gap_score=Decimal("0.400000")),
    )

    report_a = build_research_information_acquisition_priority_report(rows)
    report_b = build_research_information_acquisition_priority_report(tuple(reversed(rows)))
    payload_a = research_information_acquisition_priority_payload(report_a)
    payload_b = research_information_acquisition_priority_payload(report_b)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload_a == payload_b
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(payload_b, sort_keys=True)
    assert tuple(row.acquisition_slot_ref for row in report_a.rows) == (
        "acquisition-slot-000001",
        "acquisition-slot-000002",
        "acquisition-slot-000003",
    )


def test_module_scope_excludes_fetch_storage_persistence_and_trading_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_information_acquisition_priority",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION",
        "ResearchInformationAcquisitionPriorityConfig",
        "ResearchInformationAcquisitionPriorityInput",
        "ResearchInformationAcquisitionPriorityReport",
        "ResearchInformationAcquisitionPriorityRow",
        "STATUSES",
        "build_research_information_acquisition_priority_report",
        "research_information_acquisition_priority_payload",
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
        "sqlalchemy",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _input(
    research_item_ref: str,
    **overrides: object,
) -> ResearchInformationAcquisitionPriorityInput:
    values: dict[str, object] = {
        "research_item_ref": research_item_ref,
        "evidence_gap_score": Decimal("0.000000"),
        "source_age_hours": Decimal("1.000000"),
        "source_reliability_score": Decimal("0.950000"),
        "event_starts_in_hours": Decimal("96.000000"),
        "team_sla_hours": Decimal("48.000000"),
    }
    values.update(overrides)
    return ResearchInformationAcquisitionPriorityInput(**values)
