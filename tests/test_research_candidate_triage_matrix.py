from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_candidate_triage_matrix import (
    DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION,
    ResearchCandidateTriageInput,
    ResearchCandidateTriageMatrixConfig,
    ResearchCandidateTriageMatrixPublicPayloadItem,
    ResearchCandidateTriageMatrixReport,
    ResearchCandidateTriageMatrixRow,
    build_research_candidate_triage_matrix,
    research_candidate_triage_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_report_with_decimal_payload_strings() -> None:
    report = build_research_candidate_triage_matrix(
        (
            _input("event-b"),
            _input("event-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )

    assert isinstance(report, ResearchCandidateTriageMatrixReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION
    assert report.triage_status == "pass"
    assert report.top_manual_research_bucket == "ready_queue"
    assert report.item_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_composite_triage_score == Decimal("0.812500")
    assert report.reason_codes == ("triage_matrix_pass",)
    assert tuple(row.triage_item_key for row in report.rows) == ("event-a", "event-b")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_candidate_triage_matrix_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["triage_status"] == "pass"
    assert payload["item_count"] == "2.000000"
    assert payload["rows"][0]["composite_triage_score"] == "0.812500"
    assert payload["rows"][0]["manual_research_priority_score"] == "0.170000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_public_payload_has_no_blocked_terms(payload)


def test_watch_and_block_reports_route_to_manual_research_buckets() -> None:
    watch_report = build_research_candidate_triage_matrix(
        (
            _input(
                "event-watch",
                cost_threshold_score=Decimal("0.600000"),
                team_capacity_score=Decimal("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )
    block_report = build_research_candidate_triage_matrix(
        (
            _input("event-pass"),
            _input("event-block", evidence_package_score=Decimal("0.200000")),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )

    assert watch_report.triage_status == "watch"
    assert watch_report.top_manual_research_bucket == "priority_review"
    assert watch_report.watch_count == Decimal("1.000000")
    assert watch_report.rows[0].manual_research_bucket == "priority_review"
    assert watch_report.rows[0].reason_codes == (
        "cost_threshold_watch",
        "team_capacity_watch",
    )

    assert block_report.triage_status == "block"
    assert block_report.top_manual_research_bucket == "hold_rework"
    assert block_report.block_count == Decimal("1.000000")
    assert tuple(row.triage_status for row in block_report.rows) == ("block", "pass")
    assert block_report.rows[0].manual_research_bucket == "hold_rework"
    assert block_report.rows[0].reason_codes == ("evidence_package_block",)
    assert block_report.reason_codes == (
        "evidence_package_block",
        "triage_matrix_pass",
    )


def test_empty_inputs_are_report_only_block() -> None:
    report = build_research_candidate_triage_matrix(
        (),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )

    assert report.triage_status == "block"
    assert report.top_manual_research_bucket == "hold_rework"
    assert report.reason_codes == ("empty_input",)
    assert report.item_count == Decimal("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    assert is_dataclass(ResearchCandidateTriageMatrixConfig)
    assert is_dataclass(ResearchCandidateTriageInput)
    assert is_dataclass(ResearchCandidateTriageMatrixRow)
    assert is_dataclass(ResearchCandidateTriageMatrixReport)

    with pytest.raises(ValueError, match="config_version"):
        ResearchCandidateTriageMatrixConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_research_readiness_score"):
        ResearchCandidateTriageMatrixConfig(min_research_readiness_score=1)
    with pytest.raises(ValueError, match="min_research_readiness_score"):
        ResearchCandidateTriageMatrixConfig(
            min_research_readiness_score=_DecimalSubclass("0.600000"),
        )
    with pytest.raises(ValueError, match="research_readiness_score"):
        _input("event-a", research_readiness_score="0.900000")
    with pytest.raises(ValueError, match="research_readiness_score"):
        _input("event-a", research_readiness_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="cost_threshold_score"):
        _input("event-a", cost_threshold_score=Decimal("0.70"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        _input("event-a", team_capacity_score=0.7)
    with pytest.raises(ValueError, match="triage_status"):
        ResearchCandidateTriageMatrixRow(
            triage_item_key="event-a",
            research_readiness_score=Decimal("0.900000"),
            cost_threshold_score=Decimal("0.800000"),
            evidence_package_score=Decimal("0.850000"),
            team_capacity_score=Decimal("0.700000"),
            composite_triage_score=Decimal("0.812500"),
            manual_research_priority_score=Decimal("0.170000"),
            triage_status="blocked",
            manual_research_bucket="hold_rework",
            reason_codes=("triage_matrix_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input("event-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchCandidateTriageMatrixConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchCandidateTriageMatrixConfig(readonly=False)

    report = build_research_candidate_triage_matrix(
        (_input("event-a"),),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].triage_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "triage_item_key", "candidate-abc"),
        ("input", "triage_item_key", "market-abc"),
        ("public_payload", "key", "source_ref"),
        ("public_payload", "key", "wallet"),
        ("public_payload", "value", "https://example.test/ref"),
        ("public_payload", "value", "source text copied from private notes"),
        ("public_payload", "value", "buy or sell recommendation"),
        ("public_payload", "value", "wallet auth token"),
        ("public_payload", "value", "order trade position"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        if factory_name == "input":
            _input("event-a", **{field_name: field_value})
        else:
            values = {"key": "safe_key", "value": "safe public note"}
            values[field_name] = field_value
            ResearchCandidateTriageMatrixPublicPayloadItem(**values)


def test_public_payload_does_not_expose_forbidden_surfaces() -> None:
    report = build_research_candidate_triage_matrix(
        (_input("event-a"),),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
        public_payload=(
            ResearchCandidateTriageMatrixPublicPayloadItem(
                key="review_scope",
                value="human review only",
            ),
        ),
    )

    payload = research_candidate_triage_matrix_payload(report)
    _assert_public_payload_has_no_blocked_terms(payload)

    tampered = dict(payload)
    tampered["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public"):
        research_candidate_triage_matrix_payload(tampered)

    tampered = dict(payload)
    tampered["reason_codes"] = ["buy_signal"]
    with pytest.raises(ValueError, match="unsafe public"):
        research_candidate_triage_matrix_payload(tampered)


def test_report_digest_is_tamper_evident() -> None:
    report = build_research_candidate_triage_matrix(
        (_input("event-a"),),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())


def test_report_and_digest_are_deterministic() -> None:
    rows = (
        _input("event-c", evidence_package_score=Decimal("0.200000")),
        _input("event-a"),
        _input("event-b", cost_threshold_score=Decimal("0.600000")),
    )

    report_a = build_research_candidate_triage_matrix(
        rows,
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )
    report_b = build_research_candidate_triage_matrix(
        tuple(reversed(rows)),
        generated_at=GENERATED_AT,
        config=ResearchCandidateTriageMatrixConfig(),
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_candidate_triage_matrix_payload(
        report_a,
    ) == research_candidate_triage_matrix_payload(report_b)
    assert tuple(row.triage_item_key for row in report_a.rows) == (
        "event-c",
        "event-b",
        "event-a",
    )


def test_module_scope_excludes_fetch_storage_and_execution_surfaces() -> None:
    module = importlib.import_module("polymarket_alpha_lab.research_candidate_triage_matrix")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION",
        "ResearchCandidateTriageInput",
        "ResearchCandidateTriageMatrixConfig",
        "ResearchCandidateTriageMatrixPublicPayloadItem",
        "ResearchCandidateTriageMatrixReport",
        "ResearchCandidateTriageMatrixRow",
        "build_research_candidate_triage_matrix",
        "research_candidate_triage_matrix_payload",
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
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _input(item_key: str, **overrides: object) -> ResearchCandidateTriageInput:
    values = {
        "triage_item_key": item_key,
        "research_readiness_score": Decimal("0.900000"),
        "cost_threshold_score": Decimal("0.800000"),
        "evidence_package_score": Decimal("0.850000"),
        "team_capacity_score": Decimal("0.700000"),
    }
    values.update(overrides)
    return ResearchCandidateTriageInput(**values)


def _decimal_values_are_strings(value: object) -> bool:
    if isinstance(value, Decimal):
        return False
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return True


def _assert_public_payload_has_no_blocked_terms(payload: dict[str, object]) -> None:
    rendered = repr(payload).casefold()
    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
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
    ):
        assert token not in rendered
