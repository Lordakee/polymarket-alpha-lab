from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_resolution_rule_clarity_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION
        ),
        "min_pass_clarity_score": d("0.800000"),
        "min_watch_clarity_score": d("0.500000"),
        "max_pass_ambiguity_flag_count": d("0.000000"),
        "max_watch_ambiguity_flag_count": d("2.000000"),
        "max_pass_known_dispute_risk": d("0.200000"),
        "max_watch_known_dispute_risk": d("0.500000"),
    }
    values.update(overrides)
    return module.CandidateResolutionRuleClarityScoreConfig(**values)


def facts(**overrides: object):
    module = api()
    values = {
        "official_criteria_present": True,
        "measurable_outcome_definition_present": True,
        "date_timezone_clear": True,
        "oracle_source_clear": True,
        "fallback_resolution_path_present": True,
        "ambiguity_flag_count": d("0.000000"),
        "known_dispute_risk": d("0.000000"),
    }
    values.update(overrides)
    return module.CandidateResolutionRuleClarityFacts(**values)


def report(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.build_candidate_resolution_rule_clarity_score_report(
        facts() if subject is None else subject,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            walk_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            walk_payload_values(item)
    else:
        assert not isinstance(value, (Decimal, datetime, float))


def test_clear_aggregate_resolution_rules_pass_with_redacted_public_payload() -> None:
    module = api()
    clarity_report = report()

    assert type(clarity_report) is module.CandidateResolutionRuleClarityScoreReport
    assert clarity_report.generated_at == GENERATED_AT
    assert clarity_report.config_version == "candidate-resolution-rule-clarity-score-v0"
    assert clarity_report.component_clarity_score == d("1.000000")
    assert clarity_report.ambiguity_penalty_score == d("0.000000")
    assert clarity_report.known_dispute_risk_score == d("1.000000")
    assert clarity_report.clarity_score == d("1.000000")
    assert clarity_report.clarity_status == "pass"
    assert clarity_report.hard_blocker_codes == ()
    assert clarity_report.reason_codes == ("resolution_rule_clarity_pass",)
    assert len(clarity_report.derived_validation_digest) == 64
    assert clarity_report.paper_only is True
    assert clarity_report.report_only is True
    assert clarity_report.readonly is True

    payload = module.candidate_resolution_rule_clarity_score_payload(clarity_report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["clarity_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    encoded = repr(payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in encoded
    walk_payload_values(payload)


def test_watch_status_explains_partial_clarity_without_execution_language() -> None:
    clarity_report = report(
        facts(
            date_timezone_clear=False,
            fallback_resolution_path_present=False,
            ambiguity_flag_count=d("1.000000"),
            known_dispute_risk=d("0.300000"),
        ),
    )

    assert clarity_report.component_clarity_score == d("0.600000")
    assert clarity_report.ambiguity_penalty_score == d("0.500000")
    assert clarity_report.known_dispute_risk_score == d("0.700000")
    assert clarity_report.clarity_score == d("0.600000")
    assert clarity_report.clarity_status == "watch"
    assert clarity_report.hard_blocker_codes == ()
    assert clarity_report.reason_codes == (
        "date_timezone_unclear_watch",
        "fallback_resolution_path_missing_watch",
        "ambiguity_flags_watch",
        "known_dispute_risk_watch",
        "resolution_rule_clarity_score_watch",
    )


def test_block_status_uses_hard_blocker_reason_codes_and_zeroes_score() -> None:
    clarity_report = report(
        facts(
            official_criteria_present=False,
            oracle_source_clear=False,
            ambiguity_flag_count=d("3.000000"),
            known_dispute_risk=d("0.750000"),
        ),
    )

    assert clarity_report.component_clarity_score == d("0.600000")
    assert clarity_report.ambiguity_penalty_score == d("1.000000")
    assert clarity_report.known_dispute_risk_score == d("0.250000")
    assert clarity_report.clarity_score == d("0.000000")
    assert clarity_report.clarity_status == "block"
    assert clarity_report.hard_blocker_codes == (
        "official_criteria_missing_block",
        "oracle_source_unclear_block",
        "ambiguity_flags_block",
        "known_dispute_risk_block",
    )
    assert clarity_report.reason_codes == clarity_report.hard_blocker_codes


def test_config_thresholds_are_preserved_and_used_for_report_validation() -> None:
    clarity_report = report(
        facts(ambiguity_flag_count=d("3.000000")),
        cfg=config(max_watch_ambiguity_flag_count=d("3.000000")),
    )

    assert clarity_report.max_watch_ambiguity_flag_count == d("3.000000")
    assert clarity_report.hard_blocker_codes == ()
    assert clarity_report.ambiguity_penalty_score == d("1.000000")
    assert clarity_report.clarity_score == d("0.666667")
    assert clarity_report.clarity_status == "watch"
    assert clarity_report.reason_codes == (
        "ambiguity_flags_watch",
        "resolution_rule_clarity_score_watch",
    )

    payload = api().candidate_resolution_rule_clarity_score_payload(clarity_report)
    assert payload["max_watch_ambiguity_flag_count"] == "3.000000"


def test_validation_enforces_exact_types_frozen_records_flags_and_digest() -> None:
    module = api()
    subject = facts()
    clarity_report = report(subject)

    for record in (config(), subject, clarity_report):
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
            elif type(value) in (int, float):
                raise AssertionError(f"{field.name} must not be {type(value).__name__}")

    with pytest.raises(FrozenInstanceError):
        subject.known_dispute_risk = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        clarity_report.clarity_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="official_criteria_present must be a bool"):
        facts(official_criteria_present=1)
    with pytest.raises(ValueError, match="ambiguity_flag_count must be a Decimal"):
        facts(ambiguity_flag_count=1)
    with pytest.raises(ValueError, match="ambiguity_flag_count must be whole"):
        facts(ambiguity_flag_count=d("1.500000"))
    with pytest.raises(ValueError, match="known_dispute_risk must be a Decimal"):
        facts(known_dispute_risk=0.2)
    with pytest.raises(ValueError, match="known_dispute_risk must be between"):
        facts(known_dispute_risk=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        facts(paper_only=False)
    with pytest.raises(ValueError, match="config must be"):
        report(cfg=object())
    with pytest.raises(ValueError, match="facts must be"):
        report(object())
    with pytest.raises(ValueError, match="clarity_score must match"):
        replace(clarity_report, clarity_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(clarity_report, reason_codes=("resolution_rule_clarity_score_watch",))
    with pytest.raises(ValueError, match="clarity_status must be one of"):
        replace(
            clarity_report,
            clarity_status="blocked",
            derived_validation_digest=clarity_report.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(
            clarity_report,
            known_dispute_risk=d("0.100000"),
            derived_validation_digest=clarity_report.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.candidate_resolution_rule_clarity_score_payload(object())


def test_public_payload_validator_rejects_raw_ids_source_refs_and_live_surfaces() -> None:
    module = api()

    unsafe_payloads = (
        {"candidate_id": "raw-candidate"},
        {"market_id": "raw-market"},
        {"candidateId": "raw-candidate"},
        {"marketId": "raw-market"},
        {"market_slug": "raw-slug"},
        {"market slug": "raw-slug"},
        {"marketQuestion": "Will this resolve?"},
        {"question": "Will this resolve?"},
        {"source_url": "https://example.test/source"},
        {"source URL": "https://example.test/source"},
        {"sourceRef": "raw-ref"},
        {"source refs": ["raw-ref"]},
        {"source_text": "raw resolution language"},
        {"sourceText": "raw resolution language"},
        {"dsn": "postgresql://example"},
        {"table": "candidate_scores"},
        {"tableName": "candidate_scores"},
        {"auth_token": "secret"},
        {"privateKey": "secret"},
        {"wallet_address": "0xabc"},
        {"walletAddress": "0xabc"},
        {"safe": "buy or sell"},
        {"safe": "trade route"},
        {"safe": "token approval"},
        {"safe": "position sizing"},
        {"positionSizing": "10 shares"},
        {"safe": "public recommendation"},
        {"safe": "recommended allocation"},
    )
    for payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.validate_candidate_resolution_rule_clarity_score_public_payload(
                payload,
            )


def test_static_module_is_pure_decimal_only_and_report_only() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    assert module.BOUNDARY_STATEMENT == (
        "Paper-only report-only readonly candidate resolution rule clarity score; "
        "research decision-support only."
    )
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_RESOLUTION_RULE_CLARITY_SCORE_CONFIG_VERSION",
        "BOUNDARY_STATEMENT",
        "CLARITY_STATUSES",
        "REASON_CODES",
        "CandidateResolutionRuleClarityScoreConfig",
        "CandidateResolutionRuleClarityFacts",
        "CandidateResolutionRuleClarityScoreReport",
        "build_candidate_resolution_rule_clarity_score_report",
        "candidate_resolution_rule_clarity_score_payload",
        "validate_candidate_resolution_rule_clarity_score_public_payload",
    )
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "os.environ",
        "open(",
        ".read(",
        ".write(",
        "private_key",
        "submit_order",
        "place_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "wallet",
        "recommendation",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
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
            assert node.func.id != "float"

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
