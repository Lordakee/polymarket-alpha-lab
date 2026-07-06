from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_rule_sensitivity_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(**overrides: object):
    module = api()
    values = {
        "rule_id": "rule-alpha",
        "rule_text_excerpt": (
            "Resolves yes if the official agency publishes a final certified count."
        ),
        "objective_resolution_clause_count": d("4.000000"),
        "source_backed_clause_count": d("3.000000"),
        "ambiguous_wording_count": d("0.000000"),
        "edge_case_exception_count": d("2.000000"),
        "adjudication_path_count": d("1.000000"),
    }
    values.update(overrides)
    return module.StrategyResolutionRuleSensitivityScoreV2Input(**values)


def build(row: object | None = None):
    return api().build_strategy_resolution_rule_sensitivity_score_v2(
        row if row is not None else input_row(),
    )


def test_rule_sensitivity_score_rolls_up_decimal_components_and_status() -> None:
    report = build(
        input_row(
            rule_id="rule-watch",
            objective_resolution_clause_count=d("2.000000"),
            source_backed_clause_count=d("1.000000"),
            ambiguous_wording_count=d("2.000000"),
            edge_case_exception_count=d("1.000000"),
            adjudication_path_count=d("0.000000"),
        ),
    )

    assert report.objective_clause_gap_score == d("0.500000")
    assert report.source_backed_clarity_boost_score == d("0.333333")
    assert report.source_backing_gap_score == d("0.666667")
    assert report.ambiguous_wording_penalty_score == d("0.400000")
    assert report.edge_case_gap_score == d("0.500000")
    assert report.adjudication_path_gap_score == d("1.000000")
    assert report.rule_sensitivity_score == d("0.556667")
    assert report.sensitivity_status == "watch"
    assert report.recommended_action == "review_resolution_wording_before_scoring"
    assert report.reason_codes == (
        "sensitivity_status_watch",
        "objective_resolution_clauses_partial",
        "source_backed_clarity_partial",
        "ambiguous_wording_present",
        "edge_case_exceptions_partial",
        "adjudication_paths_missing",
    )

    for value in (
        report.objective_resolution_clause_count,
        report.source_backed_clause_count,
        report.ambiguous_wording_count,
        report.edge_case_exception_count,
        report.adjudication_path_count,
        report.objective_clause_gap_score,
        report.source_backed_clarity_boost_score,
        report.source_backing_gap_score,
        report.ambiguous_wording_penalty_score,
        report.edge_case_gap_score,
        report.adjudication_path_gap_score,
        report.rule_sensitivity_score,
    ):
        assert type(value) is Decimal


def test_ambiguous_wording_penalties_and_source_backed_clarity_boosts() -> None:
    clear_backed = build(input_row(rule_id="rule-clear-backed"))
    ambiguous_backed = build(
        input_row(
            rule_id="rule-ambiguous-backed",
            ambiguous_wording_count=d("3.000000"),
        ),
    )
    ambiguous_unbacked = build(
        input_row(
            rule_id="rule-ambiguous-unbacked",
            source_backed_clause_count=d("0.000000"),
            ambiguous_wording_count=d("3.000000"),
        ),
    )

    assert clear_backed.rule_sensitivity_score == d("0.000000")
    assert ambiguous_backed.ambiguous_wording_penalty_score == d("0.600000")
    assert ambiguous_backed.rule_sensitivity_score == d("0.210000")
    assert ambiguous_backed.reason_codes[3] == "ambiguous_wording_present"
    assert ambiguous_unbacked.source_backed_clarity_boost_score == d("0.000000")
    assert ambiguous_unbacked.source_backing_gap_score == d("1.000000")
    assert ambiguous_unbacked.rule_sensitivity_score == d("0.460000")
    assert ambiguous_unbacked.rule_sensitivity_score > ambiguous_backed.rule_sensitivity_score


def test_public_payload_serializes_decimal_strings_and_round_trips() -> None:
    module = api()
    report = build(
        input_row(
            rule_id="rule-payload",
            objective_resolution_clause_count=d("2.000000"),
            source_backed_clause_count=d("1.000000"),
            ambiguous_wording_count=d("2.000000"),
            edge_case_exception_count=d("1.000000"),
            adjudication_path_count=d("0.000000"),
        ),
    )

    payload = module.strategy_resolution_rule_sensitivity_score_v2_payload(report)

    assert payload == report.payload
    assert payload["objective_resolution_clause_count"] == "2.000000"
    assert payload["source_backed_clarity_boost_score"] == "0.333333"
    assert payload["rule_sensitivity_score"] == "0.556667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert_no_decimal_or_float_payload_values(payload)

    restored = module.StrategyResolutionRuleSensitivityScoreV2Report.from_payload(payload)
    assert restored == report


def test_frozen_dataclasses_and_hard_readonly_report_only_paper_only_flags() -> None:
    module = api()
    cfg = module.StrategyResolutionRuleSensitivityScoreV2Config()
    row = input_row()
    report = build(row)

    assert cfg.paper_only is True
    assert cfg.report_only is True
    assert cfg.readonly is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        row.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.sensitivity_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyResolutionRuleSensitivityScoreV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    report = build(input_row(rule_id="rule-digest"))
    payload = module.strategy_resolution_rule_sensitivity_score_v2_payload(report)

    tampered_payload = dict(payload)
    tampered_payload["rule_sensitivity_score"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.StrategyResolutionRuleSensitivityScoreV2Report.from_payload(tampered_payload)

    bad_digest_payload = dict(payload)
    bad_digest_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.StrategyResolutionRuleSensitivityScoreV2Report.from_payload(bad_digest_payload)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, rule_id="rule-digest-tampered")


@pytest.mark.parametrize(
    "term",
    (
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
    ),
)
def test_unsafe_public_keys_and_values_are_rejected(term: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public payload"):
        input_row(rule_text_excerpt=f"contains {term} surface")

    payload = module.strategy_resolution_rule_sensitivity_score_v2_payload(build())
    unsafe_key_payload = dict(payload)
    unsafe_key_payload[term] = "blocked"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.StrategyResolutionRuleSensitivityScoreV2Report.from_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rule_text_excerpt"] = f"contains {term} surface"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.StrategyResolutionRuleSensitivityScoreV2Report.from_payload(
            unsafe_value_payload,
        )


def test_validation_rejects_subclasses_non_decimal_numbers_and_inconsistent_reports() -> None:
    module = api()
    row = input_row()
    report = build(row)

    class InputSubclass(module.StrategyResolutionRuleSensitivityScoreV2Input):
        pass

    class ReportSubclass(module.StrategyResolutionRuleSensitivityScoreV2Report):
        pass

    with pytest.raises(ValueError, match="input_row must be"):
        build(object())
    with pytest.raises(ValueError, match="input_row must be"):
        build(InputSubclass(**row.__dict__))
    with pytest.raises(ValueError, match="report must be"):
        ReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="objective_resolution_clause_count must be a Decimal"):
        input_row(objective_resolution_clause_count=4)
    with pytest.raises(ValueError, match="ambiguous_wording_count must be nonnegative"):
        input_row(ambiguous_wording_count=d("-1.000000"))
    with pytest.raises(ValueError, match="source_backed_clause_count must be a whole Decimal"):
        input_row(source_backed_clause_count=d("1.500000"))
    with pytest.raises(ValueError, match="rule_sensitivity_score must match"):
        replace(report, rule_sensitivity_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(report, reason_codes=("sensitivity_status_pass",))


def test_module_is_isolated_phase1_report_only_and_has_no_unsafe_surfaces() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_resolution_rule_sensitivity_score_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert module.StrategyResolutionRuleSensitivityScoreV2Config.__dataclass_params__.frozen
    assert module.StrategyResolutionRuleSensitivityScoreV2Input.__dataclass_params__.frozen
    assert module.StrategyResolutionRuleSensitivityScoreV2Report.__dataclass_params__.frozen
    assert module.__all__ == (
        "SENSITIVITY_STATUSES",
        "RECOMMENDED_ACTIONS",
        "REASON_CODES",
        "StrategyResolutionRuleSensitivityScoreV2Config",
        "StrategyResolutionRuleSensitivityScoreV2Input",
        "StrategyResolutionRuleSensitivityScoreV2Report",
        "build_strategy_resolution_rule_sensitivity_score_v2",
        "strategy_resolution_rule_sensitivity_score_v2_payload",
    )

    unsafe_terms = (
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
    public_names = {
        name
        for name, value in vars(module).items()
        if not name.startswith("_") and name not in {"Decimal", "Any"}
    }
    public_names.update(module.__all__)
    assert not any(
        term in public_name.lower()
        for term in unsafe_terms
        for public_name in public_names
    )

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
    }
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "connect",
        "create_order",
        "execute",
        "open",
        "place_order",
        "read_text",
        "send",
        "sign",
        "submit_order",
        "write_text",
    }
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }


def assert_no_decimal_or_float_payload_values(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_no_decimal_or_float_payload_values(child)
        return
    if isinstance(value, list):
        for child in value:
            assert_no_decimal_or_float_payload_values(child)
        return
    assert type(value) is not Decimal
    assert type(value) is not float
