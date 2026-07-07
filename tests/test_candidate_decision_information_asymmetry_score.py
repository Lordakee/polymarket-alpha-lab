from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_information_asymmetry_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_INFORMATION_ASYMMETRY_SCORE_CONFIG_VERSION
        ),
        "min_pass_public_source_count": d("3.000000"),
        "min_watch_public_source_count": d("1.000000"),
        "min_pass_specialist_edge_score": d("0.650000"),
        "min_watch_specialist_edge_score": d("0.350000"),
        "max_pass_crowd_attention_score": d("0.450000"),
        "max_watch_crowd_attention_score": d("0.750000"),
        "min_pass_information_dispersion_score": d("0.650000"),
        "min_watch_information_dispersion_score": d("0.350000"),
        "min_pass_stale_consensus_score": d("0.500000"),
        "min_watch_stale_consensus_score": d("0.250000"),
        "min_pass_source_quality_score": d("0.700000"),
        "min_watch_source_quality_score": d("0.400000"),
        "min_pass_public_information_priority_score": d("0.650000"),
        "min_watch_public_information_priority_score": d("0.400000"),
        "public_source_depth_weight": d("0.200000"),
        "specialist_edge_weight": d("0.200000"),
        "crowd_underattention_weight": d("0.150000"),
        "information_dispersion_weight": d("0.150000"),
        "stale_consensus_weight": d("0.150000"),
        "source_quality_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.CandidateDecisionInformationAsymmetryScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "redacted-info-alpha-001",
        "public_source_count": d("5.000000"),
        "specialist_edge_score": d("0.800000"),
        "crowd_attention_score": d("0.200000"),
        "information_dispersion_score": d("0.700000"),
        "stale_consensus_score": d("0.650000"),
        "source_quality_score": d("0.850000"),
    }
    values.update(overrides)
    return module.CandidateDecisionInformationAsymmetryScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_information_asymmetry(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_json_scalars(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_public_json_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_json_scalars(item)


def test_sufficient_public_information_passes() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionInformationAsymmetryScoreReport(
        config_version="candidate-decision-information-asymmetry-score-v0",
        redacted_candidate_ref="redacted-info-alpha-001",
        public_source_count=d("5.000000"),
        specialist_edge_score=d("0.800000"),
        crowd_attention_score=d("0.200000"),
        information_dispersion_score=d("0.700000"),
        stale_consensus_score=d("0.650000"),
        source_quality_score=d("0.850000"),
        public_source_depth_score=d("1.000000"),
        crowd_underattention_score=d("0.800000"),
        public_information_priority_score=d("0.810000"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "candidate_decision_information_asymmetry_score",
            "status_pass",
            "public_source_count_pass",
            "specialist_edge_score_pass",
            "crowd_attention_score_pass",
            "information_dispersion_score_pass",
            "stale_consensus_score_pass",
            "source_quality_score_pass",
            "public_information_priority_score_pass",
            "hard_flags_absent",
        ),
        min_pass_public_source_count=d("3.000000"),
        min_watch_public_source_count=d("1.000000"),
        min_pass_specialist_edge_score=d("0.650000"),
        min_watch_specialist_edge_score=d("0.350000"),
        max_pass_crowd_attention_score=d("0.450000"),
        max_watch_crowd_attention_score=d("0.750000"),
        min_pass_information_dispersion_score=d("0.650000"),
        min_watch_information_dispersion_score=d("0.350000"),
        min_pass_stale_consensus_score=d("0.500000"),
        min_watch_stale_consensus_score=d("0.250000"),
        min_pass_source_quality_score=d("0.700000"),
        min_watch_source_quality_score=d("0.400000"),
        min_pass_public_information_priority_score=d("0.650000"),
        min_watch_public_information_priority_score=d("0.400000"),
        public_source_depth_weight=d("0.200000"),
        specialist_edge_weight=d("0.200000"),
        crowd_underattention_weight=d("0.150000"),
        information_dispersion_weight=d("0.150000"),
        stale_consensus_weight=d("0.150000"),
        source_quality_weight=d("0.150000"),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert result.payload == module.candidate_decision_information_asymmetry_score_payload(
        result,
    )


def test_low_public_source_count_blocks() -> None:
    result = score(score_input(public_source_count=d("0.000000")))

    assert result.public_source_depth_score == d("0.000000")
    assert result.public_information_priority_score == d("0.610000")
    assert result.status == "block"
    assert result.hard_flag_codes == ("public_source_count_block",)
    assert "public_source_count_block" in result.reason_codes


def test_crowded_no_edge_public_profile_watches() -> None:
    result = score(
        score_input(
            specialist_edge_score=d("0.400000"),
            crowd_attention_score=d("0.700000"),
        ),
    )

    assert result.public_information_priority_score == d("0.655000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "specialist_edge_score_watch" in result.reason_codes
    assert "crowd_attention_score_watch" in result.reason_codes


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="public_source_count must be a Decimal"):
        score_input(public_source_count=5)
    with pytest.raises(ValueError, match="specialist_edge_score must be a Decimal"):
        score_input(specialist_edge_score=0.8)
    with pytest.raises(ValueError, match="source_quality_score must be an exact Decimal"):
        score_input(source_quality_score=DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="public_source_count must be a whole"):
        score_input(public_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="crowd_attention_score must be between 0 and 1"):
        score_input(crowd_attention_score=d("1.000001"))
    with pytest.raises(ValueError, match="specialist_edge_weight must be an exact Decimal"):
        config(specialist_edge_weight=DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(source_quality_weight=d("0.160000"))


def test_leak_rejection_for_public_payload() -> None:
    module = api()
    payload = score().payload

    with pytest.raises(ValueError, match="unsafe"):
        score_input(redacted_candidate_ref="candidate_id-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        score_input(redacted_candidate_ref="https://example.invalid/raw")

    unsafe_payloads = (
        {"candidate_id": "candidate-123"},
        {"market_id": "market-123"},
        {"market_slug": "will-event-resolve"},
        {"market_question": "Will this event resolve?"},
        {"source_ref": "source-123"},
        {"source_url": "https://example.invalid/source"},
        {"source_text": "raw source text"},
        {"dsn": "postgresql://example.invalid/db"},
        {"table_name": "candidate_scores"},
        {"secret_token": "redacted"},
        {"status_note": "wallet"},
        {"status_note": "auth"},
        {"status_note": "order"},
        {"status_note": "trade"},
        {"status_note": "buy"},
        {"status_note": "sell"},
        {"status_note": "recommendation"},
        {"status_note": "position-sizing"},
        {"status_note": "blocked"},
        {"diagnostic_count": 1},
    )
    for extra_payload in unsafe_payloads:
        with pytest.raises(ValueError):
            module.validate_candidate_decision_information_asymmetry_score_public_payload(
                {**payload, **extra_payload},
            )


def test_hard_flags_and_report_only_flags_are_enforced() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionInformationAsymmetryScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionInformationAsymmetryScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionInformationAsymmetryScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.public_source_count = d("6.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    multi_flag = score(
        score_input(
            public_source_count=d("0.000000"),
            specialist_edge_score=d("0.100000"),
            crowd_attention_score=d("0.900000"),
            information_dispersion_score=d("0.100000"),
            stale_consensus_score=d("0.100000"),
            source_quality_score=d("0.200000"),
        ),
    )
    assert multi_flag.status == "block"
    assert multi_flag.hard_flag_codes == (
        "public_source_count_block",
        "specialist_edge_score_block",
        "crowd_attention_score_block",
        "information_dispersion_score_block",
        "stale_consensus_score_block",
        "source_quality_score_block",
        "public_information_priority_score_block",
    )

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionInformationAsymmetryScoreConfig(
            **{**public_values(cfg), "readonly": False},
        )
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_deterministic_payload_and_public_status_vocabulary() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload
    assert json.dumps(first.payload, allow_nan=False, sort_keys=True) == json.dumps(
        second.payload,
        allow_nan=False,
        sort_keys=True,
    )

    payload = first.payload
    assert payload["public_source_count"] == "5.000000"
    assert payload["public_information_priority_score"] == "0.810000"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_json_scalars(payload)

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position-sizing",
        "position_size",
        "ready",
        "blocked",
        "matched",
        "supported",
    ):
        assert forbidden not in rendered


def test_report_consistency_is_validated() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionInformationAsymmetryScoreReport(
        **public_values(result),
    )
    assert rebuilt == result

    with pytest.raises(ValueError, match="public_information_priority_score"):
        replace(result, public_information_priority_score=d("0.800000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("candidate_decision_information_asymmetry_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionInformationAsymmetryScoreReport(
            **{**public_values(result), "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="min_watch_public_source_count"):
        config(min_watch_public_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="max_pass_crowd_attention_score"):
        config(max_pass_crowd_attention_score=d("0.800000"))
    with pytest.raises(ValueError, match="min_watch_source_quality_score"):
        config(min_watch_source_quality_score=d("0.800000"))


def test_module_has_report_only_boundary_no_io_or_live_surface_and_no_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
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
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "private_key",
        "secret_token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "dsn",
        "table_name",
        "position_size",
        "position-sizing",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        "path(",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
        "ready",
        "blocked",
        "matched",
        "supported",
    ):
        assert forbidden not in lowered

    assert module.INFORMATION_ASYMMETRY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_INFORMATION_ASYMMETRY_SCORE_CONFIG_VERSION",
        "INFORMATION_ASYMMETRY_STATUSES",
        "CandidateDecisionInformationAsymmetryScoreConfig",
        "CandidateDecisionInformationAsymmetryScoreInput",
        "CandidateDecisionInformationAsymmetryScoreReport",
        "score_candidate_decision_information_asymmetry",
        "candidate_decision_information_asymmetry_score_payload",
        "validate_candidate_decision_information_asymmetry_score_public_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_information_asymmetry_score" not in getattr(
        root,
        "__all__",
        (),
    )
