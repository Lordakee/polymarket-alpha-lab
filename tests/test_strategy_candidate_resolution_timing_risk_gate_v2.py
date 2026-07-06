import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_resolution_timing_risk_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_reference: str = "candidate-alpha",
    *,
    market_slug: str = "election-result-certified-by-deadline",
    expected_resolution_at: datetime | None = None,
    latest_resolution_source_at: datetime | None = None,
    rule_clarity_score: str = "0.950000",
    official_source_count: str = "3",
    dispute_risk_score: str = "0.100000",
    resolution_dependency_count: str = "0",
):
    api = module()
    return api.StrategyCandidateResolutionTimingRiskCandidateV2(
        candidate_reference=candidate_reference,
        market_slug=market_slug,
        observed_at=GENERATED_AT - timedelta(hours=2),
        expected_resolution_at=(
            expected_resolution_at or GENERATED_AT + timedelta(hours=48)
        ),
        latest_resolution_source_at=(
            latest_resolution_source_at or GENERATED_AT - timedelta(hours=1)
        ),
        rule_clarity_score=d(rule_clarity_score),
        official_source_count=d(official_source_count),
        dispute_risk_score=d(dispute_risk_score),
        resolution_dependency_count=d(resolution_dependency_count),
    )


def report(*rows: object, config: object | None = None):
    api = module()
    return api.build_strategy_candidate_resolution_timing_risk_gate_v2(
        rows,
        config=config or api.StrategyCandidateResolutionTimingRiskGateConfigV2(),
        generated_at=GENERATED_AT,
    )


def test_scores_resolution_timing_candidates_and_rolls_up_gate_status() -> None:
    digest_report = report(
        candidate("candidate-pass"),
        candidate(
            "candidate-watch",
            market_slug="court-decision-published-before-close",
            expected_resolution_at=GENERATED_AT + timedelta(hours=10),
            latest_resolution_source_at=GENERATED_AT - timedelta(hours=10),
            rule_clarity_score="0.650000",
            official_source_count="1",
            dispute_risk_score="0.400000",
            resolution_dependency_count="2",
        ),
        candidate(
            "candidate-blocked",
            market_slug="agency-rule-effective-by-deadline",
            expected_resolution_at=GENERATED_AT + timedelta(hours=2),
            latest_resolution_source_at=GENERATED_AT - timedelta(hours=36),
            rule_clarity_score="0.400000",
            official_source_count="0",
            dispute_risk_score="0.800000",
            resolution_dependency_count="4",
        ),
    )

    assert digest_report.gate_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_resolution_timing_candidates"
    )
    assert digest_report.candidate_count == d("3.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.max_timing_risk_score == d("1.000000")
    assert digest_report.min_hours_to_resolution == d("2.000000")
    assert digest_report.max_resolution_source_age_hours == d("36.000000")
    assert digest_report.reason_codes == (
        "resolution_window_imminent",
        "resolution_source_stale",
        "resolution_rule_ambiguity_block",
        "resolution_source_quorum_missing",
        "resolution_dispute_risk_high",
        "resolution_dependency_block",
        "resolution_window_near",
        "resolution_source_aging",
        "resolution_rule_clarity_watch",
        "resolution_source_quorum_limited",
        "resolution_dispute_risk_elevated",
        "resolution_dependency_watch",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.redacted_candidate_reference.startswith("candidate:")
    assert blocked.gate_status == "blocked"
    assert blocked.hours_to_resolution == d("2.000000")
    assert blocked.resolution_source_age_hours == d("36.000000")
    assert blocked.timing_risk_score == d("1.000000")
    assert blocked.reason_codes == (
        "resolution_window_imminent",
        "resolution_source_stale",
        "resolution_rule_ambiguity_block",
        "resolution_source_quorum_missing",
        "resolution_dispute_risk_high",
        "resolution_dependency_block",
    )
    assert watch.gate_status == "watch"
    assert watch.timing_risk_score == d("0.500000")
    assert passed.gate_status == "pass"
    assert passed.timing_risk_score == d("0.000000")
    assert passed.reason_codes == ("resolution_timing_gate_passed",)
    assert all(len(row.derived_validation_digest) == 64 for row in digest_report.rows)
    assert len(digest_report.derived_validation_digest) == 64


def test_payload_serializes_decimals_as_strings_and_has_hard_flags() -> None:
    api = module()
    digest_report = report(candidate("candidate-payload"))

    payload = api.strategy_candidate_resolution_timing_risk_gate_v2_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1.000000"
    assert payload["max_timing_risk_score"] == "0.000000"
    assert payload["rows"][0]["hours_to_resolution"] == "48.000000"
    assert payload["rows"][0]["rule_clarity_score"] == "0.950000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        digest_report.rows[0].derived_validation_digest
    )

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk(payload)


def test_public_records_are_frozen_and_decimal_only_for_numeric_fields() -> None:
    api = module()
    digest_report = report(candidate("candidate-frozen"))
    public_records = (
        api.StrategyCandidateResolutionTimingRiskGateConfigV2(),
        candidate("candidate-record"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )

    for record in public_records:
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
            elif type(value) in (int, float):
                raise AssertionError(f"{field.name} must not be {type(value).__name__}")

    frozen_candidate = candidate("candidate-immutable")
    with pytest.raises(FrozenInstanceError):
        frozen_candidate.market_slug = "changed"  # type: ignore[misc]


def test_hard_paper_report_readonly_flags_are_enforced() -> None:
    api = module()
    digest_report = report(candidate("candidate-flags"))

    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="paper_only must be True"):
        api.StrategyCandidateResolutionTimingRiskGateConfigV2(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(candidate("candidate-report-only"), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_derived_validation_digest_rejects_row_and_report_tampering() -> None:
    digest_report = report(candidate("candidate-digest"))
    row = digest_report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(row, rule_clarity_score=d("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(digest_report, derived_validation_digest="f" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(digest_report, max_timing_risk_score=d("0.500000"))


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    api = module()

    with pytest.raises(ValueError, match="unsafe public surface"):
        api.validate_strategy_candidate_resolution_timing_risk_gate_v2_public_payload(
            {"wallet_id": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        api.validate_strategy_candidate_resolution_timing_risk_gate_v2_public_payload(
            {"safe_key": "send trade now"},
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        candidate("candidate-unsafe-value", market_slug="network-route-check")


def test_module_has_no_unsafe_external_or_execution_surfaces() -> None:
    api = module()
    source_path = Path(
        "src/polymarket_alpha_lab/strategy_candidate_resolution_timing_risk_gate_v2.py",
    )
    source = source_path.read_text()
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    forbidden_calls = {
        "connect",
        "execute",
        "request",
        "urlopen",
        "submit_order",
        "cancel_order",
        "replace_order",
    }
    assert call_names.isdisjoint(forbidden_calls)

    forbidden_public_fragments = (
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
    )
    assert not any(
        fragment in public_name.lower()
        for public_name in api.__all__
        for fragment in forbidden_public_fragments
    )
