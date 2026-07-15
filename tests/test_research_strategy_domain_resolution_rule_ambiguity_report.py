from __future__ import annotations

import ast
import copy
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_resolution_rule_ambiguity_report"
)
GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_domain_resolution_rule_ambiguity_report.py"
)


class DecimalSubclass(Decimal):
    pass


class StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def ambiguity_input(
    loaded: Any,
    *,
    domain_team: str,
    public_rule_key: str,
    private_source_references: tuple[str, ...],
    rule_text_completeness: Decimal,
    verifiable_source_coverage: Decimal,
    boundary_condition_coverage: Decimal,
    exception_clause_coverage: Decimal,
    contradiction_pressure: Decimal,
    unresolved_term_count: Decimal,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return loaded.ResearchStrategyDomainResolutionRuleAmbiguityInput(
        domain_team=domain_team,
        public_rule_key=public_rule_key,
        private_source_references=private_source_references,
        rule_text_completeness=rule_text_completeness,
        verifiable_source_coverage=verifiable_source_coverage,
        boundary_condition_coverage=boundary_condition_coverage,
        exception_clause_coverage=exception_clause_coverage,
        contradiction_pressure=contradiction_pressure,
        unresolved_term_count=unresolved_term_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def pass_input(
    loaded: Any,
    *,
    domain_team: str = "macro",
    public_rule_key: str = "rule-pass",
    private_source_references: tuple[str, ...] = ("private://source-a",),
    **overrides: object,
) -> Any:
    values: dict[str, object] = {
        "domain_team": domain_team,
        "public_rule_key": public_rule_key,
        "private_source_references": private_source_references,
        "rule_text_completeness": d("0.950000"),
        "verifiable_source_coverage": d("0.900000"),
        "boundary_condition_coverage": d("0.900000"),
        "exception_clause_coverage": d("0.850000"),
        "contradiction_pressure": d("0.050000"),
        "unresolved_term_count": d("0"),
    }
    values.update(overrides)
    return ambiguity_input(loaded, **values)


def build_report(loaded: Any, *items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return loaded.build_research_strategy_domain_resolution_rule_ambiguity_report(
        items,
        generated_at=generated_at,
        config=loaded.ResearchStrategyDomainResolutionRuleAmbiguityConfig(),
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict and "derived_validation_digest" in row:
                row["derived_validation_digest"] = canonical_digest(row)
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"raw numeric payload value leaked: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    if type(value) is list:
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def test_builds_stably_ordered_pass_watch_and_block_report() -> None:
    loaded = module()
    report = loaded.build_research_strategy_domain_resolution_rule_ambiguity_report(
        (
            ambiguity_input(
                loaded,
                domain_team="macro",
                public_rule_key="rule-pass",
                private_source_references=("private://pass-source",),
                rule_text_completeness=d("0.950000"),
                verifiable_source_coverage=d("0.900000"),
                boundary_condition_coverage=d("0.900000"),
                exception_clause_coverage=d("0.850000"),
                contradiction_pressure=d("0.050000"),
                unresolved_term_count=d("0"),
            ),
            ambiguity_input(
                loaded,
                domain_team="sports",
                public_rule_key="rule-watch",
                private_source_references=("private://watch-source",),
                rule_text_completeness=d("0.750000"),
                verifiable_source_coverage=d("0.700000"),
                boundary_condition_coverage=d("0.700000"),
                exception_clause_coverage=d("0.650000"),
                contradiction_pressure=d("0.300000"),
                unresolved_term_count=d("1"),
            ),
            ambiguity_input(
                loaded,
                domain_team="politics",
                public_rule_key="rule-block",
                private_source_references=(
                    "private://block-source-a",
                    "private://block-source-b",
                ),
                rule_text_completeness=d("0.400000"),
                verifiable_source_coverage=d("0.450000"),
                boundary_condition_coverage=d("0.350000"),
                exception_clause_coverage=d("0.400000"),
                contradiction_pressure=d("0.700000"),
                unresolved_term_count=d("4"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=loaded.ResearchStrategyDomainResolutionRuleAmbiguityConfig(),
    )

    assert report.status == "block"
    assert report.rule_count == d("3")
    assert report.domain_team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.urgent_review_count == d("1")
    assert report.priority_review_count == d("1")
    assert report.routine_review_count == d("1")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.manual_review_priority for row in report.rows) == (
        "urgent",
        "priority",
        "routine",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_complete_sort_tie_break_is_independent_of_input_order() -> None:
    loaded = module()
    first = build_report(
        loaded,
        pass_input(loaded, domain_team="macro", public_rule_key="rule-c"),
        pass_input(loaded, domain_team="macro", public_rule_key="rule-a"),
        pass_input(loaded, domain_team="macro", public_rule_key="rule-b"),
    )
    second = build_report(
        loaded,
        pass_input(loaded, domain_team="macro", public_rule_key="rule-b"),
        pass_input(loaded, domain_team="macro", public_rule_key="rule-c"),
        pass_input(loaded, domain_team="macro", public_rule_key="rule-a"),
    )

    expected_keys = ("rule-a", "rule-b", "rule-c")
    assert tuple(row.public_rule_key for row in first.rows) == expected_keys
    assert tuple(row.public_rule_key for row in second.rows) == expected_keys
    assert (
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(first)
        == loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            second,
        )
    )


def test_decimal_contract_rejects_nonfinite_signed_zero_and_raw_bounds() -> None:
    loaded = module()

    for invalid in (d("NaN"), d("Infinity"), d("-Infinity")):
        with pytest.raises(ValueError, match="finite"):
            pass_input(loaded, rule_text_completeness=invalid)

    with pytest.raises(ValueError, match="signed zero"):
        pass_input(loaded, contradiction_pressure=d("-0"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        pass_input(loaded, rule_text_completeness=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        pass_input(loaded, verifiable_source_coverage=d("-0.0000004"))
    with pytest.raises(ValueError, match="must be a Decimal"):
        pass_input(loaded, rule_text_completeness=DecimalSubclass("0.9"))

    with pytest.raises(ValueError, match="weights must sum to 1"):
        loaded.ResearchStrategyDomainResolutionRuleAmbiguityConfig(
            rule_text_weight=d("0.260000"),
        )
    with pytest.raises(ValueError, match="pass.*watch"):
        loaded.ResearchStrategyDomainResolutionRuleAmbiguityConfig(
            pass_rule_text_completeness=d("0.600000"),
            watch_rule_text_completeness=d("0.700000"),
        )


def test_decimal_contract_isolated_from_ambient_context() -> None:
    loaded = module()
    expected = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
        build_report(loaded, pass_input(loaded)),
    )

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[InvalidOperation] = True
        actual = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            build_report(loaded, pass_input(loaded)),
        )

    assert actual == expected


def test_average_ambiguity_score_uses_fixed_context_for_division() -> None:
    loaded = module()

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[InvalidOperation] = True
        report = build_report(loaded, pass_input(loaded))

    assert report.average_ambiguity_score == d("0.077500")


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("domain_team", "-macro"),
        ("domain_team", "macro-"),
        ("domain_team", "macro--research"),
        ("domain_team", "macro__research"),
        ("domain_team", StringSubclass("macro")),
        ("public_rule_key", "_rule"),
        ("public_rule_key", "rule_"),
        ("public_rule_key", "Rule-a"),
        ("public_rule_key", "rule.a"),
    ),
)
def test_invalid_public_identifiers_are_rejected(
    field_name: str,
    invalid_value: object,
) -> None:
    loaded = module()

    with pytest.raises(ValueError, match="identifier|canonical"):
        pass_input(loaded, **{field_name: invalid_value})


def test_all_public_dataclasses_are_exact_type_frozen_and_non_subclassable() -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    instances = (
        report.config,
        pass_input(loaded),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for instance in instances:
        instance_type = type(instance)
        assert is_dataclass(instance)
        assert type(instance) is instance_type
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Forged{instance_type.__name__}", (instance_type,), {})


def test_private_source_references_never_leak_and_dataclasses_are_frozen() -> None:
    loaded = module()
    secret = "https://private.example/rule?token=super-secret"
    item = pass_input(
        loaded,
        private_source_references=(secret,),
    )
    report = build_report(loaded, item)
    payload = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
        report,
    )

    assert is_dataclass(item)
    assert secret not in repr(item)
    assert secret not in repr(report)
    assert secret not in json.dumps(payload, sort_keys=True)
    assert "private_source_references" not in json.dumps(payload, sort_keys=True)
    assert report.rows[0].source_reference_count == d("1")
    with pytest.raises(FrozenInstanceError):
        item.domain_team = "changed"

    with pytest.raises(ValueError) as exc_info:
        pass_input(
            loaded,
            private_source_references=(secret, secret),
        )
    assert secret not in str(exc_info.value)


def test_payload_is_exact_canonical_stable_and_decimal_string_only() -> None:
    loaded = module()
    first = build_report(
        loaded,
        pass_input(loaded, domain_team="sports", public_rule_key="rule-b"),
        pass_input(loaded, domain_team="macro", public_rule_key="rule-a"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    second = build_report(
        loaded,
        pass_input(loaded, domain_team="macro", public_rule_key="rule-a"),
        pass_input(loaded, domain_team="sports", public_rule_key="rule-b"),
    )
    first_payload = (
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(first)
    )
    second_payload = (
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(second)
    )

    assert first.generated_at is not None
    assert first.generated_at.tzinfo is UTC
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    assert all(len(row.derived_validation_digest) == 64 for row in first.rows)
    assert set(first_payload) == {field.name for field in fields(type(first))}
    assert set(first_payload["config"]) == {
        field.name for field in fields(type(first.config))
    }
    assert set(first_payload["rows"][0]) == {
        field.name for field in fields(type(first.rows[0]))
    }
    assert_no_raw_numeric_payload_values(first_payload)
    assert (
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            copy.deepcopy(first_payload),
        )
        == first_payload
    )


@pytest.mark.parametrize(
    "section",
    ("report", "config", "row", "reason_code_count"),
)
def test_payload_rejects_noncanonical_key_order(section: str) -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    payload = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
        report,
    )
    reordered = copy.deepcopy(payload)

    if section == "report":
        reordered = dict(reversed(tuple(reordered.items())))
    elif section == "config":
        reordered["config"] = dict(
            reversed(tuple(reordered["config"].items())),
        )
    elif section == "row":
        reordered["rows"][0] = dict(
            reversed(tuple(reordered["rows"][0].items())),
        )
    else:
        reordered["reason_code_counts"][0] = dict(
            reversed(tuple(reordered["reason_code_counts"][0].items())),
        )
    resign_payload(reordered)

    with pytest.raises(ValueError, match="canonical|order|schema"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            reordered,
        )


def test_exact_schema_and_resigned_stale_derivations_are_rejected() -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    payload = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
        report,
    )

    extended = copy.deepcopy(payload)
    extended["unexpected"] = "signed-but-invalid"
    resign_payload(extended)
    with pytest.raises(ValueError, match="schema"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            extended,
        )

    missing = copy.deepcopy(payload)
    missing["rows"][0].pop("ambiguity_score")
    resign_payload(missing)
    with pytest.raises(ValueError, match="schema"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            missing,
        )

    stale_raw = copy.deepcopy(payload)
    stale_raw["rows"][0]["rule_text_completeness"] = "0.400000"
    resign_payload(stale_raw)
    with pytest.raises(ValueError, match="derived|canonical"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            stale_raw,
        )

    stale_status = copy.deepcopy(payload)
    stale_status["rows"][0]["status"] = "block"
    stale_status["rows"][0]["manual_review_priority"] = "urgent"
    stale_status["status"] = "block"
    resign_payload(stale_status)
    with pytest.raises(ValueError, match="derived|canonical"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            stale_status,
        )

    stale_aggregates = copy.deepcopy(payload)
    stale_aggregates["rule_count"] = "2"
    resign_payload(stale_aggregates)
    with pytest.raises(ValueError, match="derived|canonical|match rows"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            stale_aggregates,
        )


@pytest.mark.parametrize(
    ("section", "mutation"),
    (
        ("config", "missing"),
        ("config", "extra"),
        ("row", "extra"),
        ("reason_code_count", "missing"),
        ("reason_code_count", "extra"),
    ),
)
def test_nested_payload_schema_rejects_missing_and_extra_fields(
    section: str,
    mutation: str,
) -> None:
    loaded = module()
    payload = loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
        build_report(loaded, pass_input(loaded)),
    )
    invalid = copy.deepcopy(payload)
    target = {
        "config": invalid["config"],
        "row": invalid["rows"][0],
        "reason_code_count": invalid["reason_code_counts"][0],
    }[section]
    if mutation == "missing":
        target.pop(next(iter(target)))
    else:
        target["unexpected"] = "signed-but-invalid"
    resign_payload(invalid)

    with pytest.raises(ValueError, match="schema"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            invalid,
        )


def test_direct_nested_row_construction_rejects_impossible_source_coverage() -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    row = report.rows[0]

    with pytest.raises(ValueError, match="verifiable_source_coverage.*zero"):
        replace(
            row,
            source_reference_count=d("0"),
            status="block",
            manual_review_priority="urgent",
            reason_codes=("no_verifiable_source_reference_block",),
            derived_validation_digest="",
            validation_config=report.config,
        )


def test_object_tampering_is_rejected_even_after_digest_resigning() -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    row = report.rows[0]

    object.__setattr__(row, "ambiguity_score", d("0.999999"))
    object.__setattr__(row, "derived_validation_digest", loaded._digest_value(row))
    object.__setattr__(
        report,
        "derived_validation_digest",
        loaded._digest_value(report),
    )

    with pytest.raises(ValueError, match="ambiguity_score.*canonical"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            report,
        )


@pytest.mark.parametrize("target_name", ("report", "config", "row", "reason_count"))
def test_hard_flags_are_revalidated_after_object_tampering(
    target_name: str,
) -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))
    target = {
        "report": report,
        "config": report.config,
        "row": report.rows[0],
        "reason_count": report.reason_code_counts[0],
    }[target_name]

    object.__setattr__(target, "paper_only", False)
    if target_name == "row":
        object.__setattr__(
            target,
            "derived_validation_digest",
            loaded._digest_value(target),
        )
    object.__setattr__(
        report,
        "derived_validation_digest",
        loaded._digest_value(report),
    )

    with pytest.raises(ValueError, match="paper_only"):
        loaded.research_strategy_domain_resolution_rule_ambiguity_report_payload(
            report,
        )


def test_config_invariants_are_revalidated_after_object_tampering() -> None:
    loaded = module()
    config = loaded.ResearchStrategyDomainResolutionRuleAmbiguityConfig()
    object.__setattr__(config, "rule_text_weight", d("0.900000"))

    with pytest.raises(ValueError, match="weights"):
        loaded.build_research_strategy_domain_resolution_rule_ambiguity_report(
            (pass_input(loaded),),
            generated_at=GENERATED_AT,
            config=config,
        )


def test_input_private_reference_invariants_are_revalidated_after_object_tampering() -> None:
    loaded = module()
    item = pass_input(loaded)
    object.__setattr__(
        item,
        "private_source_references",
        ("private://source-a", "private://source-a"),
    )

    with pytest.raises(ValueError, match="private source references must be unique"):
        build_report(loaded, item)


def test_object_replacement_cannot_forge_derived_fields() -> None:
    loaded = module()
    report = build_report(loaded, pass_input(loaded))

    with pytest.raises(ValueError, match="rule_count"):
        replace(report, rule_count=d("2"), derived_validation_digest="")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_missing_public_evidence_reference_is_blocked_for_manual_review() -> None:
    loaded = module()
    report = build_report(
        loaded,
        pass_input(
            loaded,
            private_source_references=(),
            verifiable_source_coverage=d("0.000000"),
        ),
    )

    assert report.status == "block"
    assert report.rows[0].status == "block"
    assert report.rows[0].manual_review_priority == "urgent"
    assert "no_verifiable_source_reference_block" in report.rows[0].reason_codes


def test_duplicate_rule_keys_are_rejected_without_private_value_leaks() -> None:
    loaded = module()
    secret_a = "private://alpha?secret=one"
    secret_b = "private://beta?secret=two"
    first = pass_input(loaded, private_source_references=(secret_a,))
    second = pass_input(loaded, private_source_references=(secret_b,))

    with pytest.raises(ValueError, match="duplicate") as exc_info:
        build_report(loaded, first, second)
    assert secret_a not in str(exc_info.value)
    assert secret_b not in str(exc_info.value)


def test_module_has_no_network_persistence_wallet_or_execution_capabilities() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called_names.add(node.func.id)

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    assert called_names.isdisjoint({"open", "exec", "eval", "compile", "__import__"})
    public_dataclasses = (
        module().ResearchStrategyDomainResolutionRuleAmbiguityConfig,
        module().ResearchStrategyDomainResolutionRuleAmbiguityInput,
        module().ResearchStrategyDomainResolutionRuleAmbiguityRow,
        module().ResearchStrategyDomainResolutionRuleAmbiguityReasonCodeCount,
        module().ResearchStrategyDomainResolutionRuleAmbiguityReport,
    )
    assert all(
        "rank" not in item.name.lower()
        for dataclass_type in public_dataclasses
        for item in fields(dataclass_type)
    )
    declared_identifiers = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    } | {
        node.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.arg)
    }
    assert not {
        identifier
        for identifier in declared_identifiers
        if any(
            fragment in identifier.lower()
            for fragment in ("recommend", "rank", "sizing")
        )
    }
