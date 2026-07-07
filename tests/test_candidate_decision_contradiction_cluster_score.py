from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_contradiction_cluster_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "watch_risk_threshold": d("0.300000"),
        "block_risk_threshold": d("0.650000"),
        "clustered_score_threshold": d("0.650000"),
        "independent_contradiction_ratio_weight": d("0.350000"),
        "contradiction_source_ratio_weight": d("0.150000"),
        "contradiction_severity_weight": d("0.250000"),
        "resolution_conflict_weight": d("0.150000"),
        "source_quality_weight": d("0.050000"),
        "recency_weight": d("0.050000"),
        "hard_block_severity_score": d("0.900000"),
        "hard_block_resolution_conflict_score": d("0.850000"),
        "hard_block_independent_contradiction_count": d("3"),
    }
    values.update(overrides)
    return module.CandidateDecisionContradictionClusterScoreConfig(**values)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_candidate_ref": "redacted:contradiction-cluster-alpha",
        "contradiction_count": d("6"),
        "evidence_source_count": d("10"),
        "independent_contradiction_count": d("2"),
        "contradiction_severity_score": d("0.400000"),
        "resolution_conflict_score": d("0.350000"),
        "source_quality_score": d("0.500000"),
        "recency_score": d("0.200000"),
        "config": config(),
    }
    values.update(overrides)
    return module.CandidateDecisionContradictionClusterScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_contradiction_cluster_score(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def public_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            items.append(key)
            items.extend(public_strings(item))
        return tuple(items)
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(public_strings(item))
        return tuple(items)
    return ()


def test_no_contradiction_pass_lowers_manual_research_priority() -> None:
    result = score(
        score_input(
            contradiction_count=d("0"),
            evidence_source_count=d("8"),
            independent_contradiction_count=d("0"),
            contradiction_severity_score=d("0.000000"),
            resolution_conflict_score=d("0.000000"),
            source_quality_score=d("0.000000"),
            recency_score=d("0.000000"),
        ),
    )

    assert result.independent_contradiction_ratio == d("0.000000")
    assert result.contradiction_source_ratio == d("0.000000")
    assert result.contradiction_cluster_score == d("1.000000")
    assert result.contradiction_cluster_risk_score == d("0.000000")
    assert result.hard_flags == ()
    assert result.cluster_status == "pass"
    assert result.manual_research_priority_effect == "lower"
    assert result.reason_codes == (
        "candidate_decision_contradiction_cluster_score",
        "score_pass",
        "no_contradictions_present",
        "contradictions_absent",
        "risk_below_watch_threshold",
        "hard_flags_clear",
        "manual_research_priority_lower",
    )


def test_severe_contradiction_blocks_priority_lowering() -> None:
    result = score(
        score_input(
            contradiction_count=d("4"),
            evidence_source_count=d("4"),
            independent_contradiction_count=d("4"),
            contradiction_severity_score=d("0.950000"),
            resolution_conflict_score=d("0.900000"),
            source_quality_score=d("0.800000"),
            recency_score=d("0.800000"),
        ),
    )

    assert result.independent_contradiction_ratio == d("1.000000")
    assert result.contradiction_source_ratio == d("1.000000")
    assert result.contradiction_cluster_score == d("0.000000")
    assert result.contradiction_cluster_risk_score == d("0.952500")
    assert result.hard_flags == (
        "severity_hard_flag",
        "resolution_conflict_hard_flag",
        "independent_contradictions_hard_flag",
    )
    assert result.cluster_status == "block"
    assert result.manual_research_priority_effect == "raise"
    assert "score_block" in result.reason_codes
    assert "hard_flags_present" in result.reason_codes


def test_mixed_contradiction_watches_clustered_but_not_clear_case() -> None:
    result = score()

    assert result.independent_contradiction_ratio == d("0.333333")
    assert result.contradiction_source_ratio == d("0.600000")
    assert result.contradiction_cluster_score == d("0.666667")
    assert result.contradiction_cluster_risk_score == d("0.394167")
    assert result.hard_flags == ()
    assert result.cluster_status == "watch"
    assert result.manual_research_priority_effect == "hold"
    assert result.reason_codes == (
        "candidate_decision_contradiction_cluster_score",
        "score_watch",
        "contradictions_present",
        "contradictions_clustered",
        "risk_at_or_above_watch_threshold",
        "hard_flags_clear",
        "manual_research_priority_hold",
    )


def test_decimal_exact_type_rejection_and_count_validation() -> None:
    module = api()

    with pytest.raises(ValueError, match="contradiction_count must be a Decimal"):
        score_input(contradiction_count=1)
    with pytest.raises(ValueError, match="source_quality_score must be a Decimal"):
        score_input(source_quality_score=1.0)
    with pytest.raises(ValueError, match="recency_score must be a Decimal"):
        score_input(recency_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="contradiction_count must be integral"):
        score_input(contradiction_count=d("1.500000"))
    with pytest.raises(ValueError, match="evidence_source_count must be positive"):
        score_input(evidence_source_count=d("0"))
    with pytest.raises(ValueError, match="independent_contradiction_count must not exceed"):
        score_input(independent_contradiction_count=d("7"))
    with pytest.raises(ValueError, match="must be positive with contradictions"):
        score_input(independent_contradiction_count=d("0"))
    with pytest.raises(ValueError, match="contradiction_severity_score must be between"):
        score_input(contradiction_severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="config must be"):
        score_input(config=object())
    with pytest.raises(ValueError, match="block_risk_threshold must be at least"):
        config(block_risk_threshold=d("0.299999"))
    with pytest.raises(ValueError, match="score_input"):
        score(object())
    with pytest.raises(ValueError, match="result"):
        module.candidate_decision_contradiction_cluster_score_payload(object())


def test_rejects_public_payload_leaks_and_raw_candidate_refs() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        score_input(redacted_candidate_ref="candidate-raw-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        score_input(redacted_candidate_ref="redacted:market-alpha")

    unsafe_terms = (
        "market_id",
        "candidate_id",
        "market_slug",
        "question",
        "url",
        "source_ref",
        "source_text",
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
        "position",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_contradiction_cluster_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )

    payload = score().payload
    for item in public_strings(payload):
        lowered = item.lower()
        assert "candidate_id" not in lowered
        assert "market_id" not in lowered
        assert "market_slug" not in lowered
        assert "question" not in lowered
        assert "source_ref" not in lowered
        assert "source_text" not in lowered
        assert "token" not in lowered
        assert "secret" not in lowered
        assert "auth" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered
        assert "buy" not in lowered
        assert "sell" not in lowered
        assert "recommendation" not in lowered
        assert "position" not in lowered


def test_hard_flags_block_even_when_weighted_risk_is_below_block_threshold() -> None:
    result = score(
        score_input(
            contradiction_count=d("3"),
            evidence_source_count=d("20"),
            independent_contradiction_count=d("3"),
            contradiction_severity_score=d("0.100000"),
            resolution_conflict_score=d("0.100000"),
            source_quality_score=d("0.100000"),
            recency_score=d("0.100000"),
            config=config(
                block_risk_threshold=d("0.950000"),
                hard_block_independent_contradiction_count=d("3"),
            ),
        ),
    )

    assert result.contradiction_cluster_risk_score == d("0.422500")
    assert result.hard_flags == ("independent_contradictions_hard_flag",)
    assert result.cluster_status == "block"
    assert result.manual_research_priority_effect == "raise"


def test_deterministic_payload_is_decimal_string_only_and_report_only() -> None:
    module = api()
    result = score()
    repeated = score()

    assert result.payload == module.candidate_decision_contradiction_cluster_score_payload(
        result,
    )
    assert result.payload == repeated.payload
    assert result.derived_validation_digest == repeated.derived_validation_digest
    dumps(result.payload, sort_keys=True)
    assert result.payload["contradiction_cluster_risk_score"] == "0.394167"
    assert result.payload["config"]["watch_risk_threshold"] == "0.300000"
    assert result.payload["cluster_status"] == "watch"
    assert result.payload["paper_only"] is True
    assert result.payload["report_only"] is True
    assert result.payload["readonly"] is True
    assert_no_float_or_int(result.payload)
    assert result.payload["derived_validation_digest"] == result.derived_validation_digest

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_contradiction_cluster_score_payload(result)


def test_dataclasses_are_frozen_hard_flagged_and_report_consistent() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionContradictionClusterScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionContradictionClusterScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionContradictionClusterScoreResult.__dataclass_params__.frozen
    assert module.SCORE_STATUSES == ("pass", "watch", "block")
    assert "ready" not in module.SCORE_STATUSES
    assert "blocked" not in module.SCORE_STATUSES
    assert "matched" not in module.SCORE_STATUSES
    assert "supported" not in module.SCORE_STATUSES

    with pytest.raises(FrozenInstanceError):
        subject.redacted_candidate_ref = "redacted:other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.cluster_status = "pass"  # type: ignore[misc]

    for instance in (subject, result, result.config):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    rebuilt = module.CandidateDecisionContradictionClusterScoreResult(
        **public_field_values(result),
    )
    assert rebuilt == result

    with pytest.raises(ValueError, match="contradiction_cluster_score must match"):
        replace(result, contradiction_cluster_score=d("0.700000"))
    with pytest.raises(ValueError, match="contradiction_cluster_risk_score must match"):
        replace(result, contradiction_cluster_risk_score=d("0.400000"))
    with pytest.raises(ValueError, match="hard_flags must match"):
        replace(result, hard_flags=("severity_hard_flag",))
    with pytest.raises(ValueError, match="cluster_status must match"):
        replace(result, cluster_status="pass")
    with pytest.raises(ValueError, match="manual_research_priority_effect must match"):
        replace(result, manual_research_priority_effect="lower")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("candidate_decision_contradiction_cluster_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionContradictionClusterScoreResult(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_contradiction_cluster_score.py",
    ).read_text(encoding="utf-8")
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
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    assert set(module.__all__) == {
        "SCORE_STATUSES",
        "MANUAL_RESEARCH_PRIORITY_EFFECTS",
        "HARD_FLAGS",
        "CandidateDecisionContradictionClusterScoreConfig",
        "CandidateDecisionContradictionClusterScoreInput",
        "CandidateDecisionContradictionClusterScoreResult",
        "score_candidate_decision_contradiction_cluster_score",
        "estimate_candidate_decision_contradiction_cluster_score",
        "candidate_decision_contradiction_cluster_score_payload",
        "reject_candidate_decision_contradiction_cluster_score_unsafe_payload",
    }
