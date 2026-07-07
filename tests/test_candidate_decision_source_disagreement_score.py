from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_source_disagreement_score"
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_SOURCE_DISAGREEMENT_SCORE_CONFIG_VERSION
        ),
        "max_pass_disagreement_risk_score": d("0.300000"),
        "max_watch_disagreement_risk_score": d("0.650000"),
        "min_pass_source_count": d("3"),
        "min_watch_source_count": d("1"),
        "max_pass_disagreement_ratio": d("0.100000"),
        "max_watch_disagreement_ratio": d("0.300000"),
        "max_pass_disagreement_severity_score": d("0.250000"),
        "max_watch_disagreement_severity_score": d("0.600000"),
        "min_pass_source_quality_score": d("0.700000"),
        "min_watch_source_quality_score": d("0.400000"),
        "min_pass_independent_source_ratio": d("0.670000"),
        "min_watch_independent_source_ratio": d("0.340000"),
        "min_pass_recency_score": d("0.700000"),
        "min_watch_recency_score": d("0.400000"),
        "disagreement_ratio_weight": d("0.300000"),
        "disagreement_severity_weight": d("0.300000"),
        "source_quality_gap_weight": d("0.150000"),
        "independent_source_gap_weight": d("0.150000"),
        "recency_gap_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceDisagreementScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": "redacted-candidate-alpha",
        "source_count": d("5"),
        "disagreeing_source_count": d("0"),
        "disagreement_severity_score": d("0.050000"),
        "source_quality_score": d("0.900000"),
        "independent_source_ratio": d("0.800000"),
        "recency_score": d("0.900000"),
        "reason_codes": ("local_public_source_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceDisagreementScoreInput(**values)


def score(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_source_disagreement(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def report(*subjects: object, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_source_disagreement_score_report(
        subjects,
        config=config() if cfg is None else cfg,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal payload value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float payload value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_public_payload_safe(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    forbidden = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
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
        "position-sizing",
        "position_sizing",
    )
    for term in forbidden:
        assert term not in rendered
    for public_status_alias in ("ready", "blocked", "matched", "supported"):
        assert public_status_alias not in rendered
    assert_no_public_numeric_values(payload)


def test_agreement_pass_scores_zero_risk_and_report_only_payload() -> None:
    module = api()

    row = score()

    assert row == module.CandidateDecisionSourceDisagreementScoreRow(
        redacted_candidate_ref="redacted-candidate-alpha",
        source_count=d("5"),
        disagreeing_source_count=d("0"),
        disagreement_ratio=ZERO,
        disagreement_severity_score=d("0.050000"),
        source_quality_score=d("0.900000"),
        independent_source_ratio=d("0.800000"),
        recency_score=d("0.900000"),
        disagreement_ratio_component=ZERO,
        disagreement_severity_component=ZERO,
        source_quality_gap_component=ZERO,
        independent_source_gap_component=ZERO,
        recency_gap_component=ZERO,
        disagreement_risk_score=ZERO,
        disagreement_status="pass",
        hard_flag_codes=(),
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "local_public_source_facts_present",
            "source_disagreement_risk_pass",
            "source_count_pass",
            "disagreement_ratio_pass",
            "disagreement_severity_pass",
            "source_quality_pass",
            "independent_source_ratio_pass",
            "recency_score_pass",
            "disagreement_risk_score_pass",
        ),
        derived_validation_digest=row.derived_validation_digest,
    )
    assert type(row.disagreement_risk_score) is Decimal
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert_sha256(row.derived_validation_digest)
    assert_public_payload_safe(row.payload)


def test_severe_disagreement_blocks_with_hard_flags() -> None:
    row = score(
        score_input(
            source_count=d("3"),
            disagreeing_source_count=d("2"),
            disagreement_severity_score=d("0.850000"),
            source_quality_score=d("0.300000"),
            independent_source_ratio=d("0.200000"),
            recency_score=d("0.200000"),
            reason_codes=(),
        ),
    )

    assert row.disagreement_ratio == d("0.666667")
    assert row.disagreement_risk_score == d("1.000000")
    assert row.disagreement_status == "block"
    assert row.hard_flag_codes == (
        "disagreement_ratio_block",
        "disagreement_severity_block",
        "source_quality_block",
        "independent_source_ratio_block",
        "recency_score_block",
        "disagreement_risk_score_block",
    )
    assert row.reason_codes == (
        "source_disagreement_risk_block",
        "source_count_pass",
        "disagreement_ratio_block",
        "disagreement_severity_block",
        "source_quality_block",
        "independent_source_ratio_block",
        "recency_score_block",
        "disagreement_risk_score_block",
    )


def test_moderate_disagreement_watches_without_hard_flags() -> None:
    row = score(
        score_input(
            source_count=d("4"),
            disagreeing_source_count=d("1"),
            disagreement_severity_score=d("0.450000"),
            source_quality_score=d("0.600000"),
            independent_source_ratio=d("0.500000"),
            recency_score=d("0.600000"),
            reason_codes=(),
        ),
    )

    assert row.disagreement_ratio == d("0.250000")
    assert row.disagreement_ratio_component == d("0.750000")
    assert row.disagreement_severity_component == d("0.571429")
    assert row.source_quality_gap_component == d("0.333333")
    assert row.independent_source_gap_component == d("0.515152")
    assert row.recency_gap_component == d("0.333333")
    assert row.disagreement_risk_score == d("0.557035")
    assert row.disagreement_status == "watch"
    assert row.hard_flag_codes == ()
    assert row.reason_codes == (
        "source_disagreement_risk_watch",
        "source_count_pass",
        "disagreement_ratio_watch",
        "disagreement_severity_watch",
        "source_quality_watch",
        "independent_source_ratio_watch",
        "recency_score_watch",
        "disagreement_risk_score_watch",
    )


def test_dataclasses_are_frozen_decimal_exact_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    row = score(subject, cfg)
    score_report = report(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionSourceDisagreementScoreConfig,
        module.CandidateDecisionSourceDisagreementScoreInput,
        module.CandidateDecisionSourceDisagreementScoreRow,
        module.CandidateDecisionSourceDisagreementScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.source_count = d("10")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.disagreement_status = "block"  # type: ignore[misc]

    for instance in (cfg, subject, row, score_report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        score_input(source_count=3)
    with pytest.raises(ValueError, match="disagreement_severity_score must be a Decimal"):
        score_input(disagreement_severity_score=0.5)
    with pytest.raises(ValueError, match="source_quality_score must be an exact Decimal"):
        score_input(source_quality_score=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="source_count must be integral"):
        score_input(source_count=d("1.5"))
    with pytest.raises(ValueError, match="disagreeing_source_count must not exceed source_count"):
        score_input(source_count=d("1"), disagreeing_source_count=d("2"))
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        score_input(redacted_candidate_ref="candidate-alpha")
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_leak_rejection_blocks_public_reference_live_and_secret_terms() -> None:
    module = api()

    unsafe_values = (
        "candidate_id=abc123",
        "market_slug=will-event-resolve",
        "question=Will this happen?",
        "source_ref=https://example.invalid/item",
        "source_text=quoted public source text",
        "dsn=postgresql://host/db",
        "api_auth_token_present",
        "wallet_order_trade_buy_sell",
        "recommendation_position-sizing",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="public payload"):
            score_input(reason_codes=(value,))

    with pytest.raises(ValueError, match="public payload"):
        module.validate_candidate_decision_source_disagreement_score_public_payload(
            {"redacted_candidate_ref": "redacted-candidate-alpha", "status": "blocked"},
        )

    with pytest.raises(ValueError, match="public payload"):
        score_input(
            redacted_candidate_ref="redacted-candidate-secret-wallet-token",
            reason_codes=(),
        )


def test_deterministic_payload_and_report_consistency() -> None:
    module = api()
    candidates = (
        score_input(redacted_candidate_ref="redacted-candidate-pass"),
        score_input(
            redacted_candidate_ref="redacted-candidate-watch",
            source_count=d("4"),
            disagreeing_source_count=d("1"),
            disagreement_severity_score=d("0.450000"),
            source_quality_score=d("0.600000"),
            independent_source_ratio=d("0.500000"),
            recency_score=d("0.600000"),
            reason_codes=(),
        ),
        score_input(
            redacted_candidate_ref="redacted-candidate-block",
            source_count=d("3"),
            disagreeing_source_count=d("2"),
            disagreement_severity_score=d("0.850000"),
            source_quality_score=d("0.300000"),
            independent_source_ratio=d("0.200000"),
            recency_score=d("0.200000"),
            reason_codes=(),
        ),
    )
    expected = module.build_candidate_decision_source_disagreement_score_report(
        candidates,
        config=config(),
    )

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual = module.build_candidate_decision_source_disagreement_score_report(
            candidates,
            config=config(),
        )

    assert actual.payload == expected.payload
    assert tuple(row.redacted_candidate_ref for row in actual.rows) == (
        "redacted-candidate-block",
        "redacted-candidate-watch",
        "redacted-candidate-pass",
    )
    assert actual.candidate_count == d("3")
    assert actual.pass_count == d("1")
    assert actual.watch_count == d("1")
    assert actual.block_count == d("1")
    assert actual.max_disagreement_risk_score == d("1.000000")
    assert actual.min_disagreement_risk_score == ZERO
    assert actual.average_disagreement_risk_score == d("0.519012")
    assert actual.report_status == "block"
    assert actual.reason_codes == (
        "source_disagreement_score_report_block",
        "source_disagreement_score_report_has_pass",
        "source_disagreement_score_report_has_watch",
        "source_disagreement_score_report_has_block",
        "source_disagreement_score_report_hard_flags",
    )
    assert_sha256(actual.derived_validation_digest)
    assert_public_payload_safe(actual.payload)

    with pytest.raises(ValueError, match="average_disagreement_risk_score"):
        replace(actual, average_disagreement_risk_score=d("0.999999"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(actual, rows=tuple(reversed(actual.rows)))
    object.__setattr__(actual, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_source_disagreement_score_payload(actual)


def test_source_has_no_io_persistence_network_or_live_action_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            if isinstance(func, ast.Attribute):
                calls.append(func.attr)

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imports) & banned_import_roots)
    assert "open" not in calls
    assert "connect" not in calls
    assert "request" not in calls
    assert "urlopen" not in calls
