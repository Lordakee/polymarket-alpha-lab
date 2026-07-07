from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_resolution_dispute_risk_score"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


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
            module.DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION
        ),
        "max_pass_resolution_dispute_risk_score": d("0.300000"),
        "max_watch_resolution_dispute_risk_score": d("0.600000"),
        "max_ambiguous_clause_count_for_component": d("5"),
        "max_subjective_term_count_for_component": d("8"),
        "max_precedent_dispute_count_for_component": d("4"),
        "ambiguous_clause_block_count": d("5"),
        "subjective_term_block_count": d("8"),
        "precedent_dispute_block_count": d("4"),
        "source_conflict_block_score": d("0.750000"),
        "rule_clarity_block_score": d("0.300000"),
        "adjudication_readiness_block_score": d("0.300000"),
        "ambiguous_clause_weight": d("0.200000"),
        "subjective_term_weight": d("0.150000"),
        "precedent_dispute_weight": d("0.200000"),
        "source_conflict_weight": d("0.200000"),
        "rule_uncertainty_weight": d("0.125000"),
        "adjudication_unreadiness_weight": d("0.125000"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionDisputeRiskScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "redacted_candidate_ref": "candidate_ref_0123456789abcdef",
        "ambiguous_clause_count": d("0"),
        "subjective_term_count": d("0"),
        "precedent_dispute_count": d("0"),
        "source_conflict_score": d("0.100000"),
        "rule_clarity_score": d("0.950000"),
        "adjudication_readiness_score": d("0.900000"),
        "reason_codes": ("local_dispute_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionDisputeRiskScoreInput(**values)


def report(subject: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_resolution_dispute_risk_score_report(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_json_ready_no_numbers(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal value {value!r}")
    if isinstance(value, datetime):
        raise AssertionError(f"unexpected datetime value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_json_ready_no_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_json_ready_no_numbers(item)


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_low_dispute_candidate_passes() -> None:
    module = api()

    risk_report = report()

    assert type(risk_report) is module.CandidateDecisionResolutionDisputeRiskScoreReport
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.redacted_candidate_ref == "candidate_ref_0123456789abcdef"
    assert risk_report.ambiguous_clause_count == d("0")
    assert risk_report.ambiguous_clause_component == d("0.000000")
    assert risk_report.subjective_term_component == d("0.000000")
    assert risk_report.precedent_dispute_component == d("0.000000")
    assert risk_report.source_conflict_component == d("0.100000")
    assert risk_report.rule_uncertainty_component == d("0.050000")
    assert risk_report.adjudication_unreadiness_component == d("0.100000")
    assert risk_report.resolution_dispute_risk_score == d("0.038750")
    assert risk_report.resolution_dispute_risk_status == "pass"
    assert risk_report.hard_blocker_codes == ()
    assert risk_report.reason_codes == (
        "local_dispute_facts_present",
        "resolution_dispute_risk_pass",
        "ambiguous_clause_count_pass",
        "subjective_term_count_pass",
        "precedent_dispute_count_pass",
        "source_conflict_pass",
        "rule_clarity_pass",
        "adjudication_readiness_pass",
    )
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True
    assert_sha256(risk_report.derived_validation_digest)


def test_high_dispute_candidate_blocks_with_hard_flags() -> None:
    risk_report = report(
        score_input(
            ambiguous_clause_count=d("6"),
            subjective_term_count=d("9"),
            precedent_dispute_count=d("5"),
            source_conflict_score=d("0.900000"),
            rule_clarity_score=d("0.200000"),
            adjudication_readiness_score=d("0.100000"),
            reason_codes=(),
        ),
    )

    assert risk_report.resolution_dispute_risk_status == "block"
    assert risk_report.ambiguous_clause_component == d("1.000000")
    assert risk_report.subjective_term_component == d("1.000000")
    assert risk_report.precedent_dispute_component == d("1.000000")
    assert risk_report.rule_uncertainty_component == d("0.800000")
    assert risk_report.adjudication_unreadiness_component == d("0.900000")
    assert risk_report.resolution_dispute_risk_score == d("0.942500")
    assert risk_report.hard_blocker_codes == (
        "ambiguous_clause_count_block",
        "subjective_term_count_block",
        "precedent_dispute_count_block",
        "source_conflict_block",
        "rule_clarity_block",
        "adjudication_readiness_block",
        "resolution_dispute_risk_score_block",
    )
    assert "resolution_dispute_risk_block" in risk_report.reason_codes


def test_moderate_dispute_candidate_watches_public_status_vocabulary() -> None:
    risk_report = report(
        score_input(
            ambiguous_clause_count=d("2"),
            subjective_term_count=d("3"),
            precedent_dispute_count=d("1"),
            source_conflict_score=d("0.350000"),
            rule_clarity_score=d("0.700000"),
            adjudication_readiness_score=d("0.700000"),
            reason_codes=(),
        ),
    )

    assert risk_report.resolution_dispute_risk_status == "watch"
    assert risk_report.ambiguous_clause_component == d("0.400000")
    assert risk_report.subjective_term_component == d("0.375000")
    assert risk_report.precedent_dispute_component == d("0.250000")
    assert risk_report.resolution_dispute_risk_score == d("0.331250")
    assert risk_report.hard_blocker_codes == ()
    assert "resolution_dispute_risk_watch" in risk_report.reason_codes
    assert "ambiguous_clause_count_watch" in risk_report.reason_codes
    assert "subjective_term_count_watch" in risk_report.reason_codes

    module = api()
    assert module.RESOLUTION_DISPUTE_RISK_STATUSES == ("pass", "watch", "block")
    for public_status in module.RESOLUTION_DISPUTE_RISK_STATUSES:
        assert public_status in {"pass", "watch", "block"}
    assert "ready" not in module.RESOLUTION_DISPUTE_RISK_STATUSES
    assert "blocked" not in module.RESOLUTION_DISPUTE_RISK_STATUSES
    assert "matched" not in module.RESOLUTION_DISPUTE_RISK_STATUSES
    assert "supported" not in module.RESOLUTION_DISPUTE_RISK_STATUSES


def test_decimal_exact_type_rejection_and_canonical_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="ambiguous_clause_count must be a Decimal"):
        score_input(ambiguous_clause_count=0)
    with pytest.raises(ValueError, match="source_conflict_score must be a Decimal"):
        score_input(source_conflict_score=0.1)
    with pytest.raises(ValueError, match="source_conflict_score must be a Decimal"):
        score_input(source_conflict_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="ambiguous_clause_count must be integral"):
        score_input(ambiguous_clause_count=d("1.500000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        score_input(generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        score_input(redacted_candidate_ref="raw-candidate-123")
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["local_dispute_facts_present"])
    with pytest.raises(ValueError, match="weights must sum to one"):
        config(adjudication_unreadiness_weight=d("0.225000"))
    with pytest.raises(ValueError, match="pass threshold must not exceed watch"):
        config(max_pass_resolution_dispute_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="must be positive"):
        config(max_ambiguous_clause_count_for_component=d("0"))
    with pytest.raises(ValueError, match="supported version"):
        config(config_version="candidate-decision-resolution-dispute-risk-score-next")
    with pytest.raises(ValueError, match="Input"):
        report(object())
    with pytest.raises(ValueError, match="Config"):
        report(score_input(), object())

    subject = score_input()
    rebuilt = module.CandidateDecisionResolutionDisputeRiskScoreInput(
        **public_field_values(subject),
    )
    assert rebuilt == subject


def test_public_payload_rejects_leaks_status_aliases_and_numbers() -> None:
    module = api()

    unsafe_payloads = (
        ({"candidate_id": "abc"}, "raw market or candidate"),
        ({"market_id": "abc"}, "raw market or candidate"),
        ({"market_slug": "slug"}, "raw market or candidate"),
        ({"question": "will this resolve"}, "raw market or candidate"),
        ({"safe_key": "candidate_id=abc"}, "raw market or candidate"),
        ({"source_ref": "source-ref:abc123"}, "source references"),
        ({"source_url": "https://example.test/source"}, "source references"),
        ({"source_text": "raw source text"}, "source references"),
        ({"safe_key": "https://example.test/source"}, "source references"),
        ({"safe_key": "orders_table"}, "unsafe live surface"),
        ({"safe_key": "api-token"}, "unsafe live surface"),
        ({"safe_key": "wallet order trade"}, "unsafe live surface"),
        ({"safe_key": "buy sell recommendation"}, "unsafe live surface"),
        ({"safe_key": "position_size"}, "unsafe live surface"),
        ({"resolution_dispute_risk_status": "blocked"}, "public status"),
        ({"safe_key": "ready"}, "public status"),
        ({"safe_key": "matched"}, "public status"),
        ({"ambiguous_clause_count": 1}, "decimal strings"),
        ({"ambiguous_clause_count": 1.0}, "decimal strings"),
        (["not", "object"], "public payload must be a JSON object"),
    )

    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_resolution_dispute_risk_score_public_payload(
                payload,
            )


def test_hard_flags_frozen_dataclasses_and_report_only_scope() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    risk_report = report(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(risk_report)
    assert module.CandidateDecisionResolutionDisputeRiskScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionResolutionDisputeRiskScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionResolutionDisputeRiskScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.ambiguous_clause_count = d("9")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.resolution_dispute_risk_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.CandidateDecisionResolutionDisputeRiskScoreConfig):
            pass

    for instance in (cfg, subject, risk_report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(risk_report, readonly=False)


def test_deterministic_payload_is_json_ready_and_redacted() -> None:
    module = api()
    subject = score_input(
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    expected = report(subject)

    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        actual = report(subject)

    assert actual.payload == expected.payload
    payload = module.candidate_decision_resolution_dispute_risk_score_payload(actual)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == actual.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["redacted_candidate_ref"] == "candidate_ref_0123456789abcdef"
    assert payload["ambiguous_clause_count"] == "0"
    assert payload["resolution_dispute_risk_score"] == "0.038750"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == actual.derived_validation_digest
    assert_json_ready_no_numbers(payload)
    assert_sha256(payload["derived_validation_digest"])

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "raw_text",
        "http",
        "www.",
        "dsn",
        "table_name",
        "auth_token",
        "token",
        "secret",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_size",
        "position-sizing",
        "blocked",
        "ready",
        "matched",
        "supported",
    ):
        assert forbidden not in rendered


def test_report_consistency_rejects_mutated_derived_fields() -> None:
    module = api()
    risk_report = report()

    with pytest.raises(ValueError, match="resolution_dispute_risk_score"):
        replace(
            risk_report,
            resolution_dispute_risk_score=d("0.500000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="resolution_dispute_risk_status"):
        replace(
            risk_report,
            resolution_dispute_risk_status="watch",
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="hard_blocker_codes"):
        replace(
            risk_report,
            hard_blocker_codes=("resolution_dispute_risk_score_block",),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        object.__setattr__(risk_report, "derived_validation_digest", "0" * 64)
        module.candidate_decision_resolution_dispute_risk_score_payload(risk_report)

    rebuilt = module.CandidateDecisionResolutionDisputeRiskScoreReport(
        **public_field_values(report()),
    )
    assert rebuilt == report()


def test_no_unsafe_runtime_surface_or_io_is_added() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION",
        "RESOLUTION_DISPUTE_RISK_STATUSES",
        "CandidateDecisionResolutionDisputeRiskScoreConfig",
        "CandidateDecisionResolutionDisputeRiskScoreInput",
        "CandidateDecisionResolutionDisputeRiskScoreReport",
        "build_candidate_decision_resolution_dispute_risk_score_report",
        "candidate_decision_resolution_dispute_risk_score_payload",
        "validate_candidate_decision_resolution_dispute_risk_score_public_payload",
        "reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload",
    )

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
        "os",
        "pathlib",
        "subprocess",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "submit",
        "execute",
        "commit",
        "rollback",
        "getenv",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names
