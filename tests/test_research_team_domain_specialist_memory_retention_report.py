from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_specialist_memory_retention_report.py"
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_team_domain_specialist_memory_retention_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values = {
        "team_key": "research_macro",
        "domain_key": "macro_policy",
        "specialist_key": "policy_specialist",
        "memory_age_seconds": d("86400.000000"),
        "reuse_count": d("5.000000"),
        "outcome_feedback_count": d("3.000000"),
        "contradiction_count": d("0.000000"),
        "calibration_drift": d("0.020000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistMemoryRetentionObservation(**values)


def build_report(*rows: object):
    return api().build_research_team_domain_specialist_memory_retention_report(
        rows,
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resigned(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated["derived_validation_digest"] = canonical_digest(updated)
    return updated


def test_reducer_assigns_retained_watch_and_weak_quality_buckets() -> None:
    report = build_report(
        observation(
            team_key="team_retained",
            domain_key="domain_retained",
            specialist_key="specialist_retained",
        ),
        observation(
            team_key="team_watch",
            domain_key="domain_watch",
            specialist_key="specialist_watch",
            memory_age_seconds=d("2592000.000001"),
            reuse_count=d("2.000000"),
            outcome_feedback_count=d("1.000000"),
            contradiction_count=d("1.000000"),
            calibration_drift=d("0.050001"),
        ),
        observation(
            team_key="team_weak",
            domain_key="domain_weak",
            specialist_key="specialist_weak",
            memory_age_seconds=d("7776000.000001"),
            reuse_count=d("0.000000"),
            outcome_feedback_count=d("0.000000"),
            contradiction_count=d("2.000000"),
            calibration_drift=d("0.150001"),
        ),
    )

    assert report.report_quality_bucket == "weak"
    assert report.memory_count == d("3.000000")
    assert report.retained_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.weak_count == d("1.000000")
    assert tuple(row.quality_bucket for row in report.rows) == (
        "weak",
        "watch",
        "retained",
    )

    weak, watch, retained = report.rows
    assert weak.reason_codes == (
        "memory_retention_age_weak",
        "memory_retention_reuse_absent",
        "memory_retention_feedback_absent",
        "memory_retention_contradiction_weak",
        "memory_retention_calibration_drift_weak",
    )
    assert watch.reason_codes == (
        "memory_retention_age_watch",
        "memory_retention_reuse_watch",
        "memory_retention_feedback_watch",
        "memory_retention_contradiction_watch",
        "memory_retention_calibration_drift_watch",
    )
    assert retained.reason_codes == ("memory_retention_retained",)
    assert report.reason_codes == (
        "memory_retention_report_weak",
        *weak.reason_codes,
        *watch.reason_codes,
        *retained.reason_codes,
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_bucket",
        "expected_reason",
        "expected_score",
    ),
    (
        (
            "memory_age_seconds",
            "2592000.000000",
            "retained",
            "memory_retention_retained",
            "1.000000",
        ),
        (
            "memory_age_seconds",
            "2592000.000001",
            "watch",
            "memory_retention_age_watch",
            "0.900000",
        ),
        (
            "memory_age_seconds",
            "7776000.000000",
            "watch",
            "memory_retention_age_watch",
            "0.900000",
        ),
        (
            "memory_age_seconds",
            "7776000.000001",
            "weak",
            "memory_retention_age_weak",
            "0.800000",
        ),
        (
            "calibration_drift",
            "0.050000",
            "retained",
            "memory_retention_retained",
            "1.000000",
        ),
        (
            "calibration_drift",
            "0.050001",
            "watch",
            "memory_retention_calibration_drift_watch",
            "0.900000",
        ),
        (
            "calibration_drift",
            "0.150000",
            "watch",
            "memory_retention_calibration_drift_watch",
            "0.900000",
        ),
        (
            "calibration_drift",
            "0.150001",
            "weak",
            "memory_retention_calibration_drift_weak",
            "0.800000",
        ),
        (
            "reuse_count",
            "3.000000",
            "retained",
            "memory_retention_retained",
            "1.000000",
        ),
        (
            "reuse_count",
            "2.000000",
            "watch",
            "memory_retention_reuse_watch",
            "0.900000",
        ),
        (
            "reuse_count",
            "1.000000",
            "watch",
            "memory_retention_reuse_watch",
            "0.900000",
        ),
        (
            "reuse_count",
            "0.000000",
            "weak",
            "memory_retention_reuse_absent",
            "0.800000",
        ),
        (
            "outcome_feedback_count",
            "2.000000",
            "retained",
            "memory_retention_retained",
            "1.000000",
        ),
        (
            "outcome_feedback_count",
            "1.000000",
            "watch",
            "memory_retention_feedback_watch",
            "0.900000",
        ),
        (
            "outcome_feedback_count",
            "0.000000",
            "weak",
            "memory_retention_feedback_absent",
            "0.800000",
        ),
        (
            "contradiction_count",
            "0.000000",
            "retained",
            "memory_retention_retained",
            "1.000000",
        ),
        (
            "contradiction_count",
            "1.000000",
            "watch",
            "memory_retention_contradiction_watch",
            "0.900000",
        ),
        (
            "contradiction_count",
            "2.000000",
            "weak",
            "memory_retention_contradiction_weak",
            "0.800000",
        ),
    ),
)
def test_threshold_equalities_preserve_retained_watch_and_weak_semantics(
    field_name: str,
    value: str,
    expected_bucket: str,
    expected_reason: str,
    expected_score: str,
) -> None:
    row = build_report(observation(**{field_name: d(value)})).rows[0]

    assert row.quality_bucket == expected_bucket
    assert row.reason_codes == (expected_reason,)
    assert row.retention_score == d(expected_score)


def test_all_retained_rows_produce_retained_report() -> None:
    report = build_report(
        observation(
            team_key="team_retained_a",
            domain_key="domain_retained_a",
            specialist_key="specialist_retained_a",
        ),
        observation(
            team_key="team_retained_b",
            domain_key="domain_retained_b",
            specialist_key="specialist_retained_b",
        ),
    )

    assert report.report_quality_bucket == "retained"
    assert report.retained_count == d("2.000000")
    assert report.watch_count == d("0.000000")
    assert report.weak_count == d("0.000000")
    assert report.average_retention_score == d("1.000000")
    assert report.reason_codes == (
        "memory_retention_report_retained",
        "memory_retention_retained",
    )


def test_watch_rows_without_weak_rows_produce_watch_report() -> None:
    report = build_report(
        observation(
            team_key="team_age_watch",
            domain_key="domain_age_watch",
            specialist_key="specialist_age_watch",
            memory_age_seconds=d("2592000.000001"),
        ),
        observation(
            team_key="team_reuse_watch",
            domain_key="domain_reuse_watch",
            specialist_key="specialist_reuse_watch",
            reuse_count=d("2.000000"),
        ),
    )

    assert report.report_quality_bucket == "watch"
    assert report.retained_count == d("0.000000")
    assert report.watch_count == d("2.000000")
    assert report.weak_count == d("0.000000")
    assert report.average_retention_score == d("0.900000")
    assert report.reason_codes == (
        "memory_retention_report_watch",
        "memory_retention_age_watch",
        "memory_retention_reuse_watch",
    )


def test_empty_input_returns_weak_report_with_only_no_input_reason() -> None:
    report = build_report()

    assert report.report_quality_bucket == "weak"
    assert report.memory_count == d("0.000000")
    assert report.retained_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.weak_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("memory_retention_no_inputs",)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    source = observation()
    report = build_report(source)
    row = report.rows[0]

    for value in (source, row, report):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        _assert_public_numeric_values_are_decimal(value)

    with pytest.raises(ValueError, match="Decimal"):
        observation(memory_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(calibration_drift=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole"):
        observation(reuse_count=d("1.500000"))
    with pytest.raises(ValueError, match="unit interval"):
        observation(calibration_drift=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    for target_name, target in (("row", row), ("report", report)):
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(
                ValueError,
                match=rf"{target_name}.*{flag_name}|{flag_name}",
            ):
                replace(target, **{flag_name: False})
    with pytest.raises(TypeError):
        type("ForgedObservation", (module.ResearchTeamDomainSpecialistMemoryRetentionObservation,), {})
    with pytest.raises(TypeError):
        type("ForgedRow", (module.ResearchTeamDomainSpecialistMemoryRetentionRow,), {})
    with pytest.raises(TypeError):
        type("ForgedReport", (module.ResearchTeamDomainSpecialistMemoryRetentionReport,), {})


def test_raw_bounds_signed_zero_non_finite_and_fractional_counts_are_rejected() -> None:
    for field_name in (
        "memory_age_seconds",
        "reuse_count",
        "outcome_feedback_count",
        "contradiction_count",
        "calibration_drift",
    ):
        with pytest.raises(ValueError, match="signed zero"):
            observation(**{field_name: d("-0.000000")})

    with pytest.raises(ValueError, match="nonnegative"):
        observation(memory_age_seconds=d("-0.0000004"))
    with pytest.raises(ValueError, match="unit interval"):
        observation(calibration_drift=d("1.0000004"))
    with pytest.raises(ValueError, match="whole"):
        observation(reuse_count=d("1.0000004"))
    with pytest.raises(ValueError, match="whole"):
        observation(outcome_feedback_count=d("1.500000"))
    with pytest.raises(ValueError, match="whole"):
        observation(contradiction_count=d("0.500000"))

    for value in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            observation(memory_age_seconds=d(value))


def test_score_rank_aggregates_and_complete_tie_break_are_deterministic() -> None:
    weak = observation(
        team_key="team_shared",
        domain_key="domain_shared",
        specialist_key="specialist_weak",
        memory_age_seconds=d("7776000.000001"),
    )
    age_watch = observation(
        team_key="team_shared",
        domain_key="domain_shared",
        specialist_key="specialist_age_watch",
        memory_age_seconds=d("2592000.000001"),
    )
    reuse_watch = observation(
        team_key="team_shared",
        domain_key="domain_other",
        specialist_key="specialist_reuse_watch",
        reuse_count=d("2.000000"),
    )
    retained = observation(
        team_key="team_other",
        domain_key="domain_other",
        specialist_key="specialist_retained",
    )

    first = build_report(retained, reuse_watch, age_watch, weak)
    second = build_report(weak, age_watch, reuse_watch, retained)

    assert first == second
    assert tuple(row.specialist_key for row in first.rows) == (
        "specialist_weak",
        "specialist_age_watch",
        "specialist_reuse_watch",
        "specialist_retained",
    )
    assert tuple(row.priority_rank for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )
    assert tuple(row.retention_score for row in first.rows) == (
        d("0.800000"),
        d("0.900000"),
        d("0.900000"),
        d("1.000000"),
    )
    assert first.team_count == d("2.000000")
    assert first.domain_count == d("2.000000")
    assert first.specialist_count == d("4.000000")
    assert first.average_retention_score == d("0.900000")

    with pytest.raises(ValueError, match="unique"):
        build_report(retained, replace(retained, memory_age_seconds=d("2.000000")))


def test_same_score_tie_break_uses_all_public_sort_dimensions_before_identifiers() -> None:
    age_watch = observation(
        team_key="z_team",
        domain_key="z_domain",
        specialist_key="z_specialist",
        memory_age_seconds=d("2592000.000001"),
    )
    reuse_watch = observation(
        team_key="y_team",
        domain_key="y_domain",
        specialist_key="y_specialist",
        reuse_count=d("2.000000"),
    )
    feedback_watch = observation(
        team_key="x_team",
        domain_key="x_domain",
        specialist_key="x_specialist",
        outcome_feedback_count=d("1.000000"),
    )
    contradiction_watch = observation(
        team_key="w_team",
        domain_key="w_domain",
        specialist_key="w_specialist",
        contradiction_count=d("1.000000"),
    )
    drift_watch = observation(
        team_key="a_team",
        domain_key="a_domain",
        specialist_key="a_specialist",
        calibration_drift=d("0.050001"),
    )

    identifier_order_input = (
        drift_watch,
        contradiction_watch,
        feedback_watch,
        reuse_watch,
        age_watch,
    )
    first = build_report(*identifier_order_input)
    second = build_report(*reversed(identifier_order_input))

    assert first == second
    assert tuple(row.team_key for row in first.rows) == (
        "z_team",
        "y_team",
        "x_team",
        "w_team",
        "a_team",
    )
    assert tuple(row.retention_score for row in first.rows) == (
        d("0.900000"),
        d("0.900000"),
        d("0.900000"),
        d("0.900000"),
        d("0.900000"),
    )
    assert tuple(row.priority_rank for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
        d("5.000000"),
    )


def test_decimal_arithmetic_is_independent_of_ambient_context() -> None:
    retained = observation(
        team_key="team_retained_context",
        domain_key="domain_retained_context",
        specialist_key="specialist_retained_context",
    )
    age_watch = observation(
        team_key="team_age_watch_context",
        domain_key="domain_age_watch_context",
        specialist_key="specialist_age_watch_context",
        memory_age_seconds=d("2592000.000001"),
    )
    reuse_watch = observation(
        team_key="team_reuse_watch_context",
        domain_key="domain_reuse_watch_context",
        specialist_key="specialist_reuse_watch_context",
        reuse_count=d("2.000000"),
    )
    expected = build_report(retained, age_watch, reuse_watch)

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        actual = build_report(reuse_watch, age_watch, retained)

    assert actual == expected
    assert (
        actual.memory_count,
        actual.team_count,
        actual.domain_count,
        actual.specialist_count,
        actual.retained_count,
        actual.watch_count,
        actual.weak_count,
        actual.average_retention_score,
    ) == (
        d("3.000000"),
        d("3.000000"),
        d("3.000000"),
        d("3.000000"),
        d("1.000000"),
        d("2.000000"),
        d("0.000000"),
        d("0.933333"),
    )
    assert tuple(row.retention_score for row in actual.rows) == (
        d("0.900000"),
        d("0.900000"),
        d("1.000000"),
    )


def test_payload_is_canonical_deterministic_and_sha256_validated() -> None:
    module = api()
    first = build_report(
        observation(team_key="team_b", domain_key="domain_b"),
        observation(team_key="team_a", domain_key="domain_a"),
    )
    second = build_report(
        observation(team_key="team_a", domain_key="domain_a"),
        observation(team_key="team_b", domain_key="domain_b"),
    )

    first_payload = module.research_team_domain_specialist_memory_retention_report_payload(
        first,
    )
    second_payload = module.research_team_domain_specialist_memory_retention_report_payload(
        second,
    )

    assert first_payload == second_payload
    assert first_payload == first.public_payload
    assert first_payload["generated_at"] == "2026-07-09T12:00:00Z"
    assert first_payload["memory_count"] == "2.000000"
    assert first_payload["rows"][0]["memory_age_seconds"] == "86400.000000"
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first_payload["derived_validation_digest"]) == 64
    int(first_payload["derived_validation_digest"], 16)
    assert (
        module.research_team_domain_specialist_memory_retention_report_digest(first)
        == first_payload["derived_validation_digest"]
    )
    assert (
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            dict(first_payload),
        )
        == first_payload
    )
    _assert_payload_has_no_runtime_numbers(first_payload)

    bad_digest = dict(first_payload)
    bad_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            bad_digest,
        )


def test_public_validator_rejects_forged_resigned_derived_logic() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    forged_row_bucket = json.loads(json.dumps(payload))
    forged_row_bucket["rows"][0]["quality_bucket"] = "weak"
    forged_row_bucket["rows"][0]["reason_codes"] = ["memory_retention_age_weak"]
    with pytest.raises(ValueError, match="quality_bucket|reason_codes"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_row_bucket),
        )

    forged_metrics = json.loads(json.dumps(payload))
    forged_metrics["rows"][0]["memory_age_seconds"] = "7776000.000001"
    with pytest.raises(ValueError, match="quality_bucket|reason_codes"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_metrics),
        )

    forged_report = json.loads(json.dumps(payload))
    forged_report["report_quality_bucket"] = "watch"
    forged_report["reason_codes"] = ["memory_retention_report_watch"]
    with pytest.raises(ValueError, match="report_quality_bucket|reason_codes"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_report),
        )

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["retention_score"] = "0.999999"
    with pytest.raises(ValueError, match="retention_score"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_score),
        )

    forged_rank = json.loads(json.dumps(payload))
    forged_rank["rows"][0]["priority_rank"] = "2.000000"
    with pytest.raises(ValueError, match="priority_rank"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_rank),
        )

    aggregate_count_fields = (
        "memory_count",
        "team_count",
        "domain_count",
        "specialist_count",
    )
    assert {field_name: payload[field_name] for field_name in aggregate_count_fields} == {
        "memory_count": "1.000000",
        "team_count": "1.000000",
        "domain_count": "1.000000",
        "specialist_count": "1.000000",
    }
    for field_name in aggregate_count_fields:
        forged_value = str(Decimal(payload[field_name]) + d("1.000000"))
        assert forged_value != payload[field_name]
        forged_aggregate = json.loads(json.dumps(payload))
        forged_aggregate[field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_team_domain_specialist_memory_retention_report_payload(
                resigned(forged_aggregate),
            )

    forged_average = json.loads(json.dumps(payload))
    forged_average["average_retention_score"] = "0.999999"
    with pytest.raises(ValueError, match="average_retention_score"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(forged_average),
        )


def test_resigned_payload_requires_exact_canonical_schema_and_rejects_private_ids() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    extra_report_field = copy.deepcopy(payload)
    extra_report_field["source_url"] = "redacted"
    with pytest.raises(ValueError, match="schema fields"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(extra_report_field),
        )

    missing_report_field = copy.deepcopy(payload)
    missing_report_field.pop("reason_codes")
    with pytest.raises(ValueError, match="schema fields"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(missing_report_field),
        )

    extra_row_field = copy.deepcopy(payload)
    extra_row_field["rows"][0]["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="schema fields"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(extra_row_field),
        )

    noncanonical_decimal = copy.deepcopy(payload)
    noncanonical_decimal["memory_count"] = "1"
    with pytest.raises(ValueError, match="canonical|schema values"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(noncanonical_decimal),
        )

    reordered = {key: payload[key] for key in reversed(tuple(payload))}
    with pytest.raises(ValueError, match="canonical field order"):
        module.validate_research_team_domain_specialist_memory_retention_report_payload(
            resigned(reordered),
        )

    for field_name, value in (
        ("team_key", "candidate_id_123"),
        ("domain_key", "market_slug_macro"),
        ("specialist_key", "private_wallet_owner"),
    ):
        with pytest.raises(ValueError, match="public|privacy"):
            observation(**{field_name: value})

    safe_public_categories = observation(
        team_key="border_policy",
        domain_key="market_research",
        specialist_key="source_quality",
    )
    assert safe_public_categories.team_key == "border_policy"
    assert safe_public_categories.domain_key == "market_research"
    assert safe_public_categories.specialist_key == "source_quality"


def test_resigned_payload_rejects_signed_zero_for_raw_and_derived_decimals() -> None:
    module = api()
    payload = build_report(observation()).public_payload

    for path in (
        ("memory_count",),
        ("team_count",),
        ("domain_count",),
        ("specialist_count",),
        ("average_retention_score",),
        ("rows", 0, "memory_age_seconds"),
        ("rows", 0, "retention_score"),
        ("rows", 0, "priority_rank"),
    ):
        forged = copy.deepcopy(payload)
        target: Any = forged
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = "-0.000000"
        with pytest.raises(ValueError, match="signed zero"):
            module.validate_research_team_domain_specialist_memory_retention_report_payload(
                resigned(forged),
            )


def test_module_has_strict_phase_one_report_only_boundary() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "aiohttp",
        "builtins",
        "http",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write",
        "write_text",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_constants == []
    assert {
        "ResearchTeamDomainSpecialistMemoryRetentionObservation",
        "ResearchTeamDomainSpecialistMemoryRetentionRow",
        "ResearchTeamDomainSpecialistMemoryRetentionReport",
        "build_research_team_domain_specialist_memory_retention_report",
        "research_team_domain_specialist_memory_retention_report_payload",
        "research_team_domain_specialist_memory_retention_report_digest",
        "validate_research_team_domain_specialist_memory_retention_report_payload",
    } <= set(module.__all__)


def _assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)


def _assert_payload_has_no_runtime_numbers(value: object) -> None:
    if type(value) is bool or value is None or isinstance(value, str):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"payload contains runtime numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_payload_has_no_runtime_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_payload_has_no_runtime_numbers(item)
        return
    raise AssertionError(f"unexpected payload value {value!r}")
