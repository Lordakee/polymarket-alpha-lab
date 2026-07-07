from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_event_dependency_score"
MODULE_PATH = Path("src/polymarket_alpha_lab/candidate_decision_event_dependency_score.py")


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_candidate_ref": "redacted-candidate-alpha",
        "dependency_count": d("0"),
        "unresolved_dependency_count": d("0"),
        "dominant_dependency_weight": d("0.000000"),
        "dependency_correlation_score": d("0.000000"),
        "upstream_uncertainty_score": d("0.000000"),
        "evidence_support_score": d("1.000000"),
        "reason_codes": ("local_dependency_review_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEventDependencyScoreInput(**values)


def score(subject: object | None = None, *, config: object | None = None):
    module = api()
    kwargs = {} if config is None else {"config": config}
    return module.score_candidate_decision_event_dependency(
        score_input() if subject is None else subject,
        **kwargs,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_independent_candidate_passes_with_redacted_reference() -> None:
    module = api()

    row = score()

    assert row == module.CandidateDecisionEventDependencyScoreRow(
        config=module.CandidateDecisionEventDependencyScoreConfig(),
        config_version=module.DEFAULT_CONFIG_VERSION,
        redacted_candidate_ref="redacted-candidate-alpha",
        dependency_count=d("0"),
        unresolved_dependency_count=d("0"),
        dominant_dependency_weight=d("0.000000"),
        dependency_correlation_score=d("0.000000"),
        upstream_uncertainty_score=d("0.000000"),
        evidence_support_score=d("1.000000"),
        dependency_pressure_score=d("0.000000"),
        status="pass",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "local_dependency_review_present",
            "candidate_decision_event_dependency_score",
            "event_dependency_pass",
            "dependency_count_clear",
            "unresolved_dependencies_clear",
            "dominant_dependency_low",
            "dependency_correlation_low",
            "upstream_uncertainty_low",
            "evidence_support_strong",
            "dependency_pressure_below_watch_threshold",
        ),
        hard_flag_codes=(),
        derived_validation_digest=row.derived_validation_digest,
    )
    assert type(row.dependency_pressure_score) is Decimal
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.safety_flags == module.SAFETY_FLAGS


def test_dominant_dependency_hard_blocks_even_with_supporting_evidence() -> None:
    row = score(
        score_input(
            dependency_count=d("2"),
            unresolved_dependency_count=d("0"),
            dominant_dependency_weight=d("0.850000"),
            dependency_correlation_score=d("0.300000"),
            upstream_uncertainty_score=d("0.200000"),
            evidence_support_score=d("0.950000"),
        ),
    )

    assert row.dependency_pressure_score == d("0.340000")
    assert row.status == "block"
    assert row.hard_flag_codes == ("dominant_dependency_weight_block",)
    assert "event_dependency_block" in row.reason_codes
    assert "dominant_dependency_hard_block" in row.reason_codes


def test_unresolved_dependency_count_watches_nonblocking_candidate() -> None:
    row = score(
        score_input(
            dependency_count=d("2"),
            unresolved_dependency_count=d("1"),
            dominant_dependency_weight=d("0.200000"),
            dependency_correlation_score=d("0.250000"),
            upstream_uncertainty_score=d("0.300000"),
            evidence_support_score=d("0.900000"),
            reason_codes=(),
        ),
    )

    assert row.dependency_pressure_score == d("0.258333")
    assert row.status == "watch"
    assert row.hard_flag_codes == ()
    assert row.reason_codes == (
        "candidate_decision_event_dependency_score",
        "event_dependency_watch",
        "dependency_count_present",
        "unresolved_dependencies_present",
        "dominant_dependency_low",
        "dependency_correlation_low",
        "upstream_uncertainty_low",
        "evidence_support_strong",
        "unresolved_dependencies_require_watch",
    )


def test_decimal_fields_reject_non_exact_decimal_types() -> None:
    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="dependency_count must be a Decimal"):
        score_input(dependency_count=2)
    with pytest.raises(ValueError, match="dependency_correlation_score must be a Decimal"):
        score_input(dependency_correlation_score=0.2)
    with pytest.raises(ValueError, match="upstream_uncertainty_score must be a Decimal"):
        score_input(upstream_uncertainty_score=DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="dependency_count must be integral"):
        score_input(dependency_count=d("1.5"))
    with pytest.raises(ValueError, match="dominant_dependency_weight must be no greater than 1"):
        score_input(dominant_dependency_weight=d("1.000001"))


def test_rejects_unsafe_values_and_raw_reference_surfaces() -> None:
    module = api()
    unsafe_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "event_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "https://example.test/source",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_sizing",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            score_input(redacted_candidate_ref=f"redacted-candidate-{term}")
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.reject_candidate_decision_event_dependency_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.reject_candidate_decision_event_dependency_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_dataclasses_are_frozen_report_only_and_hard_flagged() -> None:
    module = api()
    config = module.CandidateDecisionEventDependencyScoreConfig()
    subject = score_input()
    row = score(subject)
    report = module.build_candidate_decision_event_dependency_score_report((subject,))

    assert is_dataclass(config)
    assert is_dataclass(subject)
    assert is_dataclass(row)
    assert is_dataclass(report)
    assert module.CandidateDecisionEventDependencyScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionEventDependencyScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEventDependencyScoreRow.__dataclass_params__.frozen
    assert module.CandidateDecisionEventDependencyScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.redacted_candidate_ref = "redacted-candidate-other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]

    for instance in (config, subject, row, report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.CandidateDecisionEventDependencyScoreConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="status must be one of"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="score_input"):
        score(object())
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "DerivedCandidateDecisionEventDependencyScoreInput",
            (module.CandidateDecisionEventDependencyScoreInput,),
            {},
        )


def test_payload_is_deterministic_decimal_safe_and_revalidates_digest() -> None:
    module = api()
    row = score(
        score_input(
            dependency_count=d("2"),
            unresolved_dependency_count=d("1"),
            dominant_dependency_weight=d("0.200000"),
            dependency_correlation_score=d("0.250000"),
            upstream_uncertainty_score=d("0.300000"),
            evidence_support_score=d("0.900000"),
            reason_codes=(),
        ),
    )

    payload = module.candidate_decision_event_dependency_score_payload(row)

    assert payload == row.payload
    assert payload["redacted_candidate_ref"] == "redacted-candidate-alpha"
    assert payload["dependency_count"] == "2"
    assert payload["dependency_pressure_score"] == "0.258333"
    assert payload["status"] == "watch"
    assert payload["reason_codes"] == list(row.reason_codes)
    assert payload["hard_flag_codes"] == []
    assert payload["safety_flags"] == list(module.SAFETY_FLAGS)
    assert "candidate_id" not in payload
    assert "market_id" not in payload
    assert "market_slug" not in payload
    assert "source_refs" not in payload
    assert_no_float_values(payload)
    assert module.candidate_decision_event_dependency_score_payload(row) == payload

    object.__setattr__(row, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_event_dependency_score_payload(row)


def test_report_sorts_deterministically_and_validates_consistency() -> None:
    module = api()
    candidates = (
        score_input(redacted_candidate_ref="redacted-candidate-z"),
        score_input(
            redacted_candidate_ref="redacted-candidate-watch",
            dependency_count=d("2"),
            unresolved_dependency_count=d("1"),
            dominant_dependency_weight=d("0.200000"),
            dependency_correlation_score=d("0.250000"),
            upstream_uncertainty_score=d("0.300000"),
            evidence_support_score=d("0.900000"),
            reason_codes=(),
        ),
        score_input(redacted_candidate_ref="redacted-candidate-a"),
        score_input(
            redacted_candidate_ref="redacted-candidate-block",
            dependency_count=d("2"),
            dominant_dependency_weight=d("0.850000"),
            dependency_correlation_score=d("0.300000"),
            upstream_uncertainty_score=d("0.200000"),
            evidence_support_score=d("0.950000"),
            reason_codes=(),
        ),
    )
    expected_report = module.build_candidate_decision_event_dependency_score_report(candidates)

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual_report = module.build_candidate_decision_event_dependency_score_report(candidates)

    assert actual_report.payload == expected_report.payload
    assert tuple(row.redacted_candidate_ref for row in actual_report.rows) == (
        "redacted-candidate-block",
        "redacted-candidate-watch",
        "redacted-candidate-a",
        "redacted-candidate-z",
    )
    assert actual_report.candidate_count == d("4")
    assert actual_report.pass_count == d("2")
    assert actual_report.watch_count == d("1")
    assert actual_report.block_count == d("1")
    assert actual_report.max_dependency_pressure_score == d("0.340000")
    assert actual_report.min_dependency_pressure_score == d("0.000000")
    assert actual_report.average_dependency_pressure_score == d("0.149583")
    assert actual_report.report_status == "block"
    assert actual_report.reason_codes == (
        "candidate_decision_event_dependency_report_block",
        "event_dependency_block_candidate_present",
        "event_dependency_watch_candidate_present",
        "event_dependency_pass_candidate_present",
    )

    with pytest.raises(ValueError, match="dependency_pressure_score must match"):
        replace(actual_report.rows[0], dependency_pressure_score=d("0.000000"))
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(actual_report, pass_count=d("3"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(actual_report, rows=tuple(reversed(actual_report.rows)))


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "getenv",
        "environ",
        "open(",
        "Path(",
        "connect(",
        "execute(",
        "commit(",
        "rollback(",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "recommendation",
        "position_sizing",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.STATUS_VALUES == ("pass", "watch", "block")
    assert "blocked" not in module.STATUS_VALUES
    assert module.__all__ == (
        "STATUS_VALUES",
        "SAFETY_FLAGS",
        "CandidateDecisionEventDependencyScoreConfig",
        "CandidateDecisionEventDependencyScoreInput",
        "CandidateDecisionEventDependencyScoreRow",
        "CandidateDecisionEventDependencyScoreReport",
        "score_candidate_decision_event_dependency",
        "build_candidate_decision_event_dependency_score_report",
        "candidate_decision_event_dependency_score_payload",
        "reject_candidate_decision_event_dependency_score_unsafe_payload",
    )
