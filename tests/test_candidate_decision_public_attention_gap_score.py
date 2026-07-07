from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_public_attention_gap_score"


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
            module.DEFAULT_CANDIDATE_DECISION_PUBLIC_ATTENTION_GAP_SCORE_CONFIG_VERSION
        ),
        "max_pass_attention_coverage_delta": d("0.150000"),
        "max_watch_attention_coverage_delta": d("0.400000"),
        "min_pass_verifiable_public_info_coverage_score": d("0.700000"),
        "min_watch_verifiable_public_info_coverage_score": d("0.400000"),
        "min_pass_public_source_count": d("4.000000"),
        "min_watch_public_source_count": d("1.000000"),
        "min_pass_independent_public_source_count": d("3.000000"),
        "min_watch_independent_public_source_count": d("1.000000"),
        "min_pass_resolution_rule_coverage_score": d("0.800000"),
        "min_watch_resolution_rule_coverage_score": d("0.500000"),
        "min_pass_recent_verification_coverage_score": d("0.700000"),
        "min_watch_recent_verification_coverage_score": d("0.400000"),
        "max_pass_public_attention_gap_score": d("0.300000"),
        "max_watch_public_attention_gap_score": d("0.650000"),
        "attention_coverage_delta_weight": d("0.350000"),
        "public_info_gap_weight": d("0.250000"),
        "source_independence_gap_weight": d("0.150000"),
        "resolution_rule_gap_weight": d("0.150000"),
        "recent_verification_gap_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.CandidateDecisionPublicAttentionGapScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "redacted-candidate-public-attention-alpha-001",
        "market_attention_score": d("0.300000"),
        "verifiable_public_info_coverage_score": d("0.850000"),
        "public_source_count": d("5.000000"),
        "independent_public_source_count": d("4.000000"),
        "resolution_rule_coverage_score": d("0.900000"),
        "recent_verification_coverage_score": d("0.800000"),
    }
    values.update(overrides)
    return module.CandidateDecisionPublicAttentionGapScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_public_attention_gap(
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


def test_public_attention_gap_pass() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionPublicAttentionGapScoreReport(
        config_version="candidate-decision-public-attention-gap-score-v0",
        redacted_candidate_ref="redacted-candidate-public-attention-alpha-001",
        market_attention_score=d("0.300000"),
        verifiable_public_info_coverage_score=d("0.850000"),
        public_source_count=d("5.000000"),
        independent_public_source_count=d("4.000000"),
        resolution_rule_coverage_score=d("0.900000"),
        recent_verification_coverage_score=d("0.800000"),
        attention_coverage_delta=d("0.000000"),
        public_info_gap_score=d("0.150000"),
        source_independence_gap_score=d("0.200000"),
        resolution_rule_gap_score=d("0.100000"),
        recent_verification_gap_score=d("0.200000"),
        public_attention_gap_score=d("0.102500"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "candidate_decision_public_attention_gap_score",
            "status_pass",
            "attention_coverage_delta_pass",
            "verifiable_public_info_coverage_score_pass",
            "public_source_count_pass",
            "independent_public_source_count_pass",
            "resolution_rule_coverage_score_pass",
            "recent_verification_coverage_score_pass",
            "public_attention_gap_score_pass",
            "hard_flags_absent",
        ),
        max_pass_attention_coverage_delta=d("0.150000"),
        max_watch_attention_coverage_delta=d("0.400000"),
        min_pass_verifiable_public_info_coverage_score=d("0.700000"),
        min_watch_verifiable_public_info_coverage_score=d("0.400000"),
        min_pass_public_source_count=d("4.000000"),
        min_watch_public_source_count=d("1.000000"),
        min_pass_independent_public_source_count=d("3.000000"),
        min_watch_independent_public_source_count=d("1.000000"),
        min_pass_resolution_rule_coverage_score=d("0.800000"),
        min_watch_resolution_rule_coverage_score=d("0.500000"),
        min_pass_recent_verification_coverage_score=d("0.700000"),
        min_watch_recent_verification_coverage_score=d("0.400000"),
        max_pass_public_attention_gap_score=d("0.300000"),
        max_watch_public_attention_gap_score=d("0.650000"),
        attention_coverage_delta_weight=d("0.350000"),
        public_info_gap_weight=d("0.250000"),
        source_independence_gap_weight=d("0.150000"),
        resolution_rule_gap_weight=d("0.150000"),
        recent_verification_gap_weight=d("0.100000"),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert result.payload == module.candidate_decision_public_attention_gap_score_payload(
        result,
    )


def test_public_attention_gap_watch() -> None:
    result = score(
        score_input(
            market_attention_score=d("0.700000"),
            verifiable_public_info_coverage_score=d("0.500000"),
            public_source_count=d("3.000000"),
            independent_public_source_count=d("2.000000"),
            resolution_rule_coverage_score=d("0.600000"),
            recent_verification_coverage_score=d("0.500000"),
        ),
    )

    assert result.attention_coverage_delta == d("0.200000")
    assert result.public_info_gap_score == d("0.500000")
    assert result.source_independence_gap_score == d("0.333333")
    assert result.public_attention_gap_score == d("0.355000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "attention_coverage_delta_watch" in result.reason_codes
    assert "verifiable_public_info_coverage_score_watch" in result.reason_codes
    assert "public_source_count_watch" in result.reason_codes
    assert "independent_public_source_count_watch" in result.reason_codes
    assert "public_attention_gap_score_watch" in result.reason_codes


def test_public_attention_gap_block() -> None:
    result = score(
        score_input(
            market_attention_score=d("0.950000"),
            verifiable_public_info_coverage_score=d("0.200000"),
            public_source_count=d("0.000000"),
            independent_public_source_count=d("0.000000"),
            resolution_rule_coverage_score=d("0.200000"),
            recent_verification_coverage_score=d("0.100000"),
        ),
    )

    assert result.attention_coverage_delta == d("0.750000")
    assert result.public_info_gap_score == d("0.800000")
    assert result.source_independence_gap_score == d("1.000000")
    assert result.public_attention_gap_score == d("0.822500")
    assert result.status == "block"
    assert result.hard_flag_codes == (
        "attention_coverage_delta_block",
        "verifiable_public_info_coverage_score_block",
        "public_source_count_block",
        "independent_public_source_count_block",
        "resolution_rule_coverage_score_block",
        "recent_verification_coverage_score_block",
        "public_attention_gap_score_block",
    )
    assert "hard_flags_present" in result.reason_codes


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="market_attention_score must be a Decimal"):
        score_input(market_attention_score=1)
    with pytest.raises(
        ValueError,
        match="verifiable_public_info_coverage_score must be a Decimal",
    ):
        score_input(verifiable_public_info_coverage_score=0.2)
    with pytest.raises(
        ValueError,
        match="recent_verification_coverage_score must be an exact Decimal",
    ):
        score_input(recent_verification_coverage_score=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="public_source_count must be a whole"):
        score_input(public_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="resolution_rule_coverage_score must be between 0 and 1"):
        score_input(resolution_rule_coverage_score=d("1.000001"))
    with pytest.raises(ValueError, match="independent_public_source_count must not exceed"):
        score_input(public_source_count=d("1.000000"), independent_public_source_count=d("2.000000"))
    with pytest.raises(
        ValueError,
        match="attention_coverage_delta_weight must be an exact Decimal",
    ):
        config(attention_coverage_delta_weight=DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(recent_verification_gap_weight=d("0.110000"))


def test_leak_rejection_for_public_payload() -> None:
    module = api()
    payload = score().payload

    with pytest.raises(ValueError):
        score_input(redacted_candidate_ref="candidate_id-alpha")
    with pytest.raises(ValueError):
        score_input(redacted_candidate_ref="redacted-candidate-https://example.invalid/raw")

    unsafe_payloads = (
        {"candidate_id": "candidate-123"},
        {"raw_candidate_id": "candidate-123"},
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
        {"diagnostic_count": 1},
    )
    for extra_payload in unsafe_payloads:
        with pytest.raises(ValueError):
            module.validate_candidate_decision_public_attention_gap_score_public_payload(
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
    assert module.CandidateDecisionPublicAttentionGapScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionPublicAttentionGapScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionPublicAttentionGapScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.market_attention_score = d("0.400000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for item in fields(instance):
            value = getattr(instance, item.name)
            if item.name in {
                "config_version",
                "redacted_candidate_ref",
                "status",
                "hard_flag_codes",
                "reason_codes",
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionPublicAttentionGapScoreConfig(
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
    assert payload["public_attention_gap_score"] == "0.102500"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_json_scalars(payload)

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "raw_candidate_id",
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
    ):
        assert forbidden not in rendered

    module = api()
    assert module.PUBLIC_ATTENTION_GAP_STATUSES == ("pass", "watch", "block")


def test_report_consistency_is_validated() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionPublicAttentionGapScoreReport(**public_values(result))
    assert rebuilt == result

    with pytest.raises(ValueError, match="public_attention_gap_score"):
        replace(result, public_attention_gap_score=d("0.200000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("candidate_decision_public_attention_gap_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionPublicAttentionGapScoreReport(
            **{**public_values(result), "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="max_pass_attention_coverage_delta"):
        config(max_pass_attention_coverage_delta=d("0.900000"))
    with pytest.raises(ValueError, match="min_watch_public_source_count"):
        config(min_watch_public_source_count=d("5.000000"))
    with pytest.raises(ValueError, match="min_watch_verifiable_public_info_coverage_score"):
        config(min_watch_verifiable_public_info_coverage_score=d("0.800000"))


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
        "raw_candidate_id",
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
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_PUBLIC_ATTENTION_GAP_SCORE_CONFIG_VERSION",
        "PUBLIC_ATTENTION_GAP_STATUSES",
        "CandidateDecisionPublicAttentionGapScoreConfig",
        "CandidateDecisionPublicAttentionGapScoreInput",
        "CandidateDecisionPublicAttentionGapScoreReport",
        "score_candidate_decision_public_attention_gap",
        "candidate_decision_public_attention_gap_score_payload",
        "validate_candidate_decision_public_attention_gap_score_public_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_public_attention_gap_score" not in getattr(root, "__all__", ())
