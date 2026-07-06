from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_paper_candidate_execution_readiness_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_paper_candidate_execution_readiness_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-pass",
        "market_id": "market-pass",
        "outcome_id": "outcome-pass",
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.560000"),
        "source_verified_edge_probability": d("0.060000"),
        "expected_value_probability": d("0.060000"),
        "uncertainty_band_low_probability": d("0.580000"),
        "uncertainty_band_high_probability": d("0.650000"),
        "research_readiness_score": d("0.920000"),
        "liquidity_exit_feasibility_score": d("0.910000"),
        "resolution_ambiguity_score": d("0.100000"),
        "portfolio_impact_score": d("0.150000"),
        "specialist_quorum_score": d("0.880000"),
    }
    values.update(overrides)
    return module.StrategyPaperCandidateExecutionReadinessV2Candidate(**values)


def blocked_candidate(**overrides: object):
    values = {
        "candidate_id": "candidate-blocked",
        "market_id": "market-blocked",
        "outcome_id": "outcome-blocked",
        "forecast_probability": d("0.600000"),
        "market_probability": d("0.580000"),
        "source_verified_edge_probability": d("0.020000"),
        "expected_value_probability": d("0.100000"),
        "uncertainty_band_low_probability": d("0.400000"),
        "uncertainty_band_high_probability": d("0.800000"),
        "research_readiness_score": d("0.800000"),
        "liquidity_exit_feasibility_score": d("0.700000"),
        "resolution_ambiguity_score": d("0.400000"),
        "portfolio_impact_score": d("0.350000"),
        "specialist_quorum_score": d("0.600000"),
    }
    values.update(overrides)
    return candidate(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            candidate(candidate_id="candidate-pass", market_id="market-pass"),
            blocked_candidate(
                candidate_id="candidate-blocked",
                market_id="market-blocked",
            ),
        )
    return module.build_strategy_paper_candidate_execution_readiness_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_decimal_paper_execution_readiness_report_and_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.paper_execution_blocked is True
    assert report.candidate_count == d("2")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("0")
    assert report.blocked_candidate_count == d("1")
    assert report.reason_codes == (
        "research_readiness_below_floor",
        "source_verified_edge_below_floor",
        "expected_value_inconsistent",
        "uncertainty_band_too_wide",
        "liquidity_exit_not_feasible",
        "resolution_ambiguity_too_high",
        "portfolio_impact_too_high",
        "specialist_quorum_below_floor",
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-pass",
    )
    assert tuple(row.execution_readiness_status for row in report.rows) == (
        "blocked",
        "pass",
    )
    assert report.rows[1].calculated_edge_probability == d("0.060000")
    assert report.rows[1].expected_value_delta_probability == d("0.000000")
    assert report.rows[1].uncertainty_band_width_probability == d("0.070000")
    assert report.rows[1].execution_readiness_score == d("0.923750")
    assert report.rows[1].reason_codes == ("candidate_execution_readiness_pass",)
    assert "expected_value_inconsistent" in report.rows[0].reason_codes

    payload = report.payload
    assert payload["candidate_count"] == "2"
    assert payload["average_execution_readiness_score"] == "0.828750"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_execution_blocked"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][1]["execution_readiness_score"] == "0.923750"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_report_is_report_only_digest_backed_and_blocking() -> None:
    report = build_report(
        *(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert report.report_status == "blocked"
    assert report.paper_execution_blocked is True
    assert report.candidate_count == d("0")
    assert report.average_execution_readiness_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("candidate_execution_readiness_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyPaperCandidateExecutionReadinessV2Config()
    item = candidate()
    report = build_report(item)
    row = report.rows[0]

    for obj in (config, item, row, report):
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        with pytest.raises(FrozenInstanceError):
            obj.paper_only = False  # type: ignore[misc]
        for field in fields(obj):
            value = getattr(obj, field.name)
            if (
                field.name.endswith("_score")
                or field.name.endswith("_floor")
                or field.name.endswith("_probability")
                or field.name.endswith("_count")
            ):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="forecast_probability must be exactly Decimal"):
        candidate(forecast_probability=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="market_probability must be exactly Decimal"):
        candidate(market_probability=0)
    with pytest.raises(ValueError, match="research_readiness_score must be <= 1.000000"):
        candidate(research_readiness_score=d("1.000001"))
    with pytest.raises(
        ValueError,
        match="source_verified_edge_probability must use six decimal places or fewer",
    ):
        candidate(source_verified_edge_probability=d("0.0400004"))
    with pytest.raises(ValueError, match="specialist_quorum_score must be finite"):
        candidate(specialist_quorum_score=Decimal("NaN"))


def test_config_and_build_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_research_readiness_score must be exactly Decimal"):
        module.StrategyPaperCandidateExecutionReadinessV2Config(
            min_research_readiness_score=0,
        )
    with pytest.raises(
        ValueError,
        match="pass_execution_readiness_score_floor must be >= min_research_readiness_score",
    ):
        module.StrategyPaperCandidateExecutionReadinessV2Config(
            pass_execution_readiness_score_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyPaperCandidateExecutionReadinessV2Config(paper_only=False)
    with pytest.raises(ValueError, match="final candidates must be an iterable"):
        module.build_strategy_paper_candidate_execution_readiness_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="final candidate items must be StrategyPaperCandidateExecutionReadinessV2Candidate",
    ):
        module.build_strategy_paper_candidate_execution_readiness_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_paper_candidate_execution_readiness_v2(
            [candidate()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="duplicate candidate_id and market_id"):
        build_report(
            candidate(candidate_id="candidate-a", market_id="market-a", outcome_id="one"),
            candidate(candidate_id="candidate-a", market_id="market-a", outcome_id="two"),
            use_default_items=False,
        )


def test_derived_validation_digest_and_public_payload_reject_tampering() -> None:
    module = api()
    report = build_report()
    payload = report.payload

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_execution_readiness_score=d("0.740000"))

    assert module.validate_strategy_paper_candidate_execution_readiness_v2_public_payload(payload)
    tampered = dict(payload)
    tampered["candidate_count"] = "3"
    with pytest.raises(ValueError, match="derived_validation_digest must match public payload"):
        module.validate_strategy_paper_candidate_execution_readiness_v2_public_payload(tampered)
    numeric_payload = dict(payload)
    numeric_payload["candidate_count"] = 2
    with pytest.raises(ValueError, match="public payload must use Decimal strings"):
        module.validate_strategy_paper_candidate_execution_readiness_v2_public_payload(
            numeric_payload,
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_candidate",
        "auth_candidate",
        "wallet_candidate",
        "order_candidate",
        "network_candidate",
        "database_candidate",
        "persist_candidate",
        "signing_candidate",
        "mutation_candidate",
        "buy_candidate",
        "sell_candidate",
        "trade_candidate",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            candidate(candidate_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by status and candidate_id"):
        replace(report, rows=(report.rows[1], report.rows[0]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_candidate_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(report, reason_codes=("candidate_execution_readiness_pass",))


def test_module_scope_has_no_file_database_network_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
