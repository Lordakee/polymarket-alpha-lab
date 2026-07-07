from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_evidence_independence_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "config_version": module.DEFAULT_CONFIG_VERSION,
        "min_pass_independence_score": d("0.700000"),
        "min_watch_independence_score": d("0.400000"),
        "min_pass_independent_source_count": d("3"),
        "min_watch_independent_source_count": d("2"),
        "min_watch_evidence_source_count": d("2"),
        "max_watch_shared_origin_ratio": d("0.350000"),
        "max_block_shared_origin_ratio": d("0.700000"),
        "max_watch_circular_reference_ratio": d("0.150000"),
        "max_block_circular_reference_ratio": d("0.400000"),
        "independent_source_weight": d("0.300000"),
        "shared_origin_weight": d("0.200000"),
        "circular_reference_weight": d("0.200000"),
        "corroboration_weight": d("0.150000"),
        "source_quality_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceIndependenceScoreConfig(**values)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_candidate_ref": "redacted-candidate-alpha",
        "evidence_source_count": d("4"),
        "independent_source_count": d("3"),
        "shared_origin_ratio": d("0.100000"),
        "circular_reference_ratio": d("0.000000"),
        "corroboration_score": d("0.800000"),
        "source_quality_score": d("0.900000"),
        "reason_codes": ("redacted_candidate_evidence_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceIndependenceScoreInput(**values)


def score(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_evidence_independence(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def report(*subjects: object, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_evidence_independence_score_report(
        subjects or (score_input(),),
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_independent_evidence_passes_for_manual_research_priority() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionEvidenceIndependenceScoreRow(
        config_version=module.DEFAULT_CONFIG_VERSION,
        redacted_candidate_ref="redacted-candidate-alpha",
        evidence_source_count=d("4"),
        independent_source_count=d("3"),
        independent_source_ratio=d("0.750000"),
        shared_origin_ratio=d("0.100000"),
        circular_reference_ratio=d("0.000000"),
        corroboration_score=d("0.800000"),
        source_quality_score=d("0.900000"),
        evidence_independence_score=d("0.935000"),
        status="pass",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "redacted_candidate_evidence_present",
            "candidate_decision_evidence_independence_score",
            "evidence_independence_pass",
            "independent_source_count_pass",
            "shared_origin_ratio_low",
            "circular_reference_ratio_low",
            "corroboration_score_strong",
            "source_quality_score_strong",
            "independence_score_pass_threshold_met",
        ),
        hard_flag_codes=(),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert type(result.evidence_independence_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_circular_evidence_blocks_manual_research_priority() -> None:
    result = score(
        score_input(
            circular_reference_ratio=d("0.450000"),
            corroboration_score=d("0.700000"),
            source_quality_score=d("0.800000"),
            reason_codes=(),
        ),
    )

    assert result.evidence_independence_score == d("0.770000")
    assert result.status == "block"
    assert result.hard_flag_codes == ("circular_reference_ratio_block",)
    assert "evidence_independence_block" in result.reason_codes
    assert "circular_reference_ratio_block" in result.reason_codes


def test_partial_source_overlap_is_watch_even_when_score_is_high() -> None:
    result = score(
        score_input(
            redacted_candidate_ref="redacted-candidate-overlap",
            evidence_source_count=d("5"),
            independent_source_count=d("3"),
            shared_origin_ratio=d("0.450000"),
            circular_reference_ratio=d("0.100000"),
            corroboration_score=d("0.700000"),
            source_quality_score=d("0.800000"),
            reason_codes=(),
        ),
    )

    assert result.independent_source_ratio == d("0.600000")
    assert result.evidence_independence_score == d("0.815000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "shared_origin_ratio_watch" in result.reason_codes
    assert "independence_score_pass_but_overlap_watch" in result.reason_codes


def test_decimal_exact_type_rejection_and_status_vocabulary() -> None:
    module = api()
    valid_result = score()

    with pytest.raises(ValueError, match="evidence_source_count must be a Decimal"):
        score_input(evidence_source_count=4)
    with pytest.raises(ValueError, match="shared_origin_ratio must be a Decimal"):
        score_input(shared_origin_ratio=0.1)
    with pytest.raises(ValueError, match="exact Decimal"):
        score_input(source_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="independent_source_weight must be a Decimal"):
        config(independent_source_weight=1)
    with pytest.raises(ValueError, match="weight fields must sum"):
        config(source_quality_weight=d("0.140000"))
    with pytest.raises(ValueError, match="status"):
        module.CandidateDecisionEvidenceIndependenceScoreRow(
            **{
                **public_field_values(valid_result),
                "status": "blocked",
                "derived_validation_digest": "",
            },
        )
    assert module.STATUS_VALUES == ("pass", "watch", "block")


def test_leak_rejection_for_public_values_and_payload_surface() -> None:
    module = api()

    unsafe_values = (
        "candidate_id_alpha",
        "market_slug_alpha",
        "normalized_market_question_alpha",
        "https://example.invalid/source",
        "source_ref_alpha",
        "source_text_alpha",
        "dsn_alpha",
        "table_alpha",
        "token_alpha",
        "secret_alpha",
        "auth_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "buy_alpha",
        "sell_alpha",
        "recommendation_alpha",
        "position_sizing_alpha",
    )
    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe|redacted"):
            score_input(reason_codes=(unsafe_value,))
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_evidence_independence_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": unsafe_value},
            )

    result = score(
        score_input(
            redacted_candidate_ref="redacted-candidate-secret-token-wallet",
        ),
    )
    rendered = repr(result).lower()
    payload_rendered = repr(result.payload).lower()
    assert "secret" not in rendered
    assert "token" not in rendered
    assert "wallet" not in rendered
    assert "secret" not in payload_rendered
    assert "token" not in payload_rendered
    assert "wallet" not in payload_rendered


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg)
    aggregate = report(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionEvidenceIndependenceScoreConfig,
        module.CandidateDecisionEvidenceIndependenceScoreInput,
        module.CandidateDecisionEvidenceIndependenceScoreRow,
        module.CandidateDecisionEvidenceIndependenceScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(subject, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(aggregate, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object(), cfg)
    with pytest.raises(ValueError, match="config"):
        score(subject, object())


def test_payload_is_deterministic_decimal_string_only_and_public_status_only() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload["evidence_independence_score"] == "0.935000"
    assert first.payload["evidence_source_count"] == "4"
    assert first.payload["status"] == "pass"
    assert first.payload["reason_codes"] == list(first.reason_codes)
    assert first.payload["paper_only"] is True
    assert first.payload["report_only"] is True
    assert first.payload["readonly"] is True
    assert_no_float_or_int_values(first.payload)

    rendered = repr(first.payload).lower()
    for public_status in ("pass", "watch", "block"):
        assert public_status in ("pass", "watch", "block")
    for forbidden_status in ("ready", "blocked", "matched", "supported"):
        assert forbidden_status not in rendered


def test_report_consistency_counts_sorting_and_digest_validation() -> None:
    module = api()
    pass_input = score_input(redacted_candidate_ref="redacted-candidate-c")
    watch_input = score_input(
        redacted_candidate_ref="redacted-candidate-b",
        shared_origin_ratio=d("0.450000"),
        circular_reference_ratio=d("0.100000"),
        corroboration_score=d("0.700000"),
        source_quality_score=d("0.800000"),
        reason_codes=(),
    )
    block_input = score_input(
        redacted_candidate_ref="redacted-candidate-a",
        circular_reference_ratio=d("0.450000"),
        corroboration_score=d("0.700000"),
        source_quality_score=d("0.800000"),
        reason_codes=(),
    )

    aggregate = report(pass_input, watch_input, block_input)

    assert aggregate == module.CandidateDecisionEvidenceIndependenceScoreReport(
        config_version=module.DEFAULT_CONFIG_VERSION,
        candidate_count=d("3"),
        pass_count=d("1"),
        watch_count=d("1"),
        block_count=d("1"),
        max_evidence_independence_score=d("0.935000"),
        min_evidence_independence_score=d("0.770000"),
        average_evidence_independence_score=d("0.840000"),
        report_status="block",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "candidate_decision_evidence_independence_score_report",
            "block_status_present",
            "watch_status_present",
            "pass_status_present",
        ),
        rows=aggregate.rows,
        derived_validation_digest=aggregate.derived_validation_digest,
    )
    assert tuple(row.redacted_candidate_ref for row in aggregate.rows) == (
        "redacted-candidate-a",
        "redacted-candidate-b",
        "redacted-candidate-c",
    )
    assert tuple(row.status for row in aggregate.rows) == ("block", "watch", "pass")
    assert_no_float_or_int_values(aggregate.payload)

    with pytest.raises(ValueError, match="candidate_count"):
        module.CandidateDecisionEvidenceIndependenceScoreReport(
            **{
                **public_field_values(aggregate),
                "candidate_count": d("9"),
                "derived_validation_digest": "",
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceIndependenceScoreReport(
            **{
                **public_field_values(aggregate),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="duplicate redacted_candidate_ref"):
        report(pass_input, pass_input)


def test_module_has_no_runtime_io_or_action_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
        "ready",
        "blocked",
        "matched",
        "supported",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "supabase",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

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
    assert module.__all__ == (
        "DEFAULT_CONFIG_VERSION",
        "STATUS_VALUES",
        "SAFETY_FLAGS",
        "CandidateDecisionEvidenceIndependenceScoreConfig",
        "CandidateDecisionEvidenceIndependenceScoreInput",
        "CandidateDecisionEvidenceIndependenceScoreRow",
        "CandidateDecisionEvidenceIndependenceScoreReport",
        "score_candidate_decision_evidence_independence",
        "build_candidate_decision_evidence_independence_score_report",
        "candidate_decision_evidence_independence_score_payload",
        "reject_candidate_decision_evidence_independence_score_unsafe_payload",
    )
