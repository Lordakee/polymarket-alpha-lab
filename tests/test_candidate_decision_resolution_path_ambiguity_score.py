from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_resolution_path_ambiguity_score"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing candidate decision module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_RESOLUTION_PATH_AMBIGUITY_SCORE_CONFIG_VERSION
        ),
        "max_pass_ambiguity_score": d("0.250000"),
        "max_watch_ambiguity_score": d("0.550000"),
        "max_pass_distinct_resolution_path_count": d("1"),
        "max_watch_distinct_resolution_path_count": d("3"),
        "max_pass_conflicting_path_count": d("0"),
        "max_watch_conflicting_path_count": d("2"),
        "max_pass_rule_branch_count": d("1"),
        "max_watch_rule_branch_count": d("4"),
        "max_pass_adjudication_touchpoint_count": d("0"),
        "max_watch_adjudication_touchpoint_count": d("2"),
        "min_pass_ambiguity_evidence_coverage": d("0.800000"),
        "min_watch_ambiguity_evidence_coverage": d("0.550000"),
        "min_pass_primary_path_confidence": d("0.750000"),
        "min_watch_primary_path_confidence": d("0.500000"),
        "max_distinct_resolution_path_count_for_score": d("5"),
        "max_conflicting_path_count_for_score": d("4"),
        "max_rule_branch_count_for_score": d("6"),
        "max_adjudication_touchpoint_count_for_score": d("4"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionPathAmbiguityScoreConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-secret-alpha",
        "distinct_resolution_path_count": d("1"),
        "conflicting_path_count": d("0"),
        "rule_branch_count": d("1"),
        "adjudication_touchpoint_count": d("0"),
        "ambiguity_evidence_coverage": d("0.950000"),
        "primary_path_confidence": d("0.900000"),
    }
    values.update(overrides)
    return module.CandidateDecisionResolutionPathAmbiguityScoreCandidate(**values)


def report(*candidates: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_decision_resolution_path_ambiguity_score(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_scores_pass_watch_block_and_prioritizes_most_ambiguous_paths() -> None:
    result = report(
        candidate(
            candidate_reference="pass-secret-token",
            distinct_resolution_path_count=d("1"),
            conflicting_path_count=d("0"),
            rule_branch_count=d("1"),
            adjudication_touchpoint_count=d("0"),
            ambiguity_evidence_coverage=d("0.950000"),
            primary_path_confidence=d("0.900000"),
        ),
        candidate(
            candidate_reference="watch-candidate",
            distinct_resolution_path_count=d("3"),
            conflicting_path_count=d("1"),
            rule_branch_count=d("3"),
            adjudication_touchpoint_count=d("1"),
            ambiguity_evidence_coverage=d("0.650000"),
            primary_path_confidence=d("0.600000"),
        ),
        candidate(
            candidate_reference="block-candidate",
            distinct_resolution_path_count=d("6"),
            conflicting_path_count=d("4"),
            rule_branch_count=d("7"),
            adjudication_touchpoint_count=d("4"),
            ambiguity_evidence_coverage=d("0.200000"),
            primary_path_confidence=d("0.200000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-decision-resolution-path-ambiguity-score-v1"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.min_ambiguity_score == d("0.017500")
    assert result.max_ambiguity_score == d("0.950000")
    assert result.average_ambiguity_score == d("0.432500")
    assert result.max_distinct_resolution_path_count == d("6")
    assert result.max_conflicting_path_count == d("4")
    assert result.max_rule_branch_count == d("7")
    assert result.max_adjudication_touchpoint_count == d("4")
    assert result.status == "block"
    assert result.reason_codes == (
        "distinct_resolution_paths_block",
        "distinct_resolution_paths_watch",
        "conflicting_resolution_paths_block",
        "conflicting_resolution_paths_watch",
        "resolution_rule_branches_block",
        "resolution_rule_branches_watch",
        "adjudication_touchpoints_block",
        "adjudication_touchpoints_watch",
        "ambiguity_evidence_coverage_block",
        "ambiguity_evidence_coverage_watch",
        "primary_path_confidence_block",
        "primary_path_confidence_watch",
        "resolution_path_ambiguity_score_block",
        "resolution_path_ambiguity_score_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)

    assert tuple(row.status for row in result.results) == ("block", "watch", "pass")
    blocked, watched, passed = result.results

    assert blocked.ambiguity_score == d("0.950000")
    assert blocked.path_count_pressure == d("1.000000")
    assert blocked.conflict_pressure == d("1.000000")
    assert blocked.rule_branch_pressure == d("1.000000")
    assert blocked.adjudication_pressure == d("1.000000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "distinct_resolution_paths_block",
        "conflicting_resolution_paths_block",
        "resolution_rule_branches_block",
        "adjudication_touchpoints_block",
        "ambiguity_evidence_coverage_block",
        "primary_path_confidence_block",
        "resolution_path_ambiguity_score_block",
    )
    assert_sha256(blocked.result_sha256)

    assert watched.ambiguity_score == d("0.330000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "distinct_resolution_paths_watch",
        "conflicting_resolution_paths_watch",
        "resolution_rule_branches_watch",
        "adjudication_touchpoints_watch",
        "ambiguity_evidence_coverage_watch",
        "primary_path_confidence_watch",
        "resolution_path_ambiguity_score_watch",
    )

    assert passed.ambiguity_score == d("0.017500")
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_path_ambiguity_pass",)
    assert "secret" not in passed.redacted_candidate_reference
    assert "token" not in passed.redacted_candidate_reference


def test_payload_redacts_raw_inputs_decimal_strings_and_is_deterministic() -> None:
    module = api()
    first = report(
        candidate(
            candidate_reference="secret-wallet-auth-order-trade",
            distinct_resolution_path_count=d("3"),
            conflicting_path_count=d("1"),
            rule_branch_count=d("3"),
            adjudication_touchpoint_count=d("1"),
            ambiguity_evidence_coverage=d("0.650000"),
            primary_path_confidence=d("0.600000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(
        candidate(
            candidate_reference="secret-wallet-auth-order-trade",
            distinct_resolution_path_count=d("3"),
            conflicting_path_count=d("1"),
            rule_branch_count=d("3"),
            adjudication_touchpoint_count=d("1"),
            ambiguity_evidence_coverage=d("0.650000"),
            primary_path_confidence=d("0.600000"),
        ),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )

    assert module.validate_candidate_decision_resolution_path_ambiguity_score_report(first) is True
    payload = module.candidate_decision_resolution_path_ambiguity_score_payload(first)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == module.candidate_decision_resolution_path_ambiguity_score_payload(second)
    assert first.report_sha256 == second.report_sha256
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_ambiguity_score"] == "0.330000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["results"][0]["redacted_candidate_reference"].startswith("candidate_ref_")
    assert payload["results"][0]["ambiguity_score"] == "0.330000"
    assert payload["results"][0]["status"] == "watch"
    assert_sha256(payload["results"][0]["derived_validation_digest"])
    assert payload["results"][0]["result_sha256"] == first.results[0].result_sha256
    assert_sha256(payload["derived_validation_digest"])
    assert payload["report_sha256"] == first.report_sha256
    assert_no_float_or_int_values(payload)

    for forbidden in (
        "secret",
        "wallet",
        "auth",
        "order",
        "trade",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "buy",
        "sell",
        "recommendation",
        "position",
        "dsn",
        "table",
    ):
        assert forbidden not in rendered


def test_rejects_public_payload_leaks_and_hard_flags() -> None:
    module = api()
    result = report(candidate())
    payload = module.candidate_decision_resolution_path_ambiguity_score_payload(result)

    assert module.validate_candidate_decision_resolution_path_ambiguity_score_public_payload(payload) is True

    with pytest.raises(ValueError, match="unsafe public payload field"):
        module.validate_candidate_decision_resolution_path_ambiguity_score_public_payload(
            {
                **payload,
                "market_slug": "raw-market-slug",
            },
        )

    with pytest.raises(ValueError, match="unsafe public payload value"):
        module.validate_candidate_decision_resolution_path_ambiguity_score_public_payload(
            {
                **payload,
                "notes": "place buy recommendation",
            },
        )

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)


def test_decimal_type_rejection_and_frozen_dataclasses() -> None:
    module = api()
    row = report(candidate()).results[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    for klass in (
        module.CandidateDecisionResolutionPathAmbiguityScoreConfig,
        module.CandidateDecisionResolutionPathAmbiguityScoreCandidate,
        module.CandidateDecisionResolutionPathAmbiguityScoreResult,
        module.CandidateDecisionResolutionPathAmbiguityScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="distinct_resolution_path_count must be a Decimal"):
        candidate(distinct_resolution_path_count=1)
    with pytest.raises(ValueError, match="ambiguity_evidence_coverage must be a Decimal"):
        candidate(ambiguity_evidence_coverage=0.5)
    with pytest.raises(ValueError, match="primary_path_confidence must be an exact Decimal"):
        candidate(primary_path_confidence=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="conflicting_path_count must be a whole Decimal"):
        candidate(conflicting_path_count=d("1.5"))
    with pytest.raises(ValueError, match="max_pass_ambiguity_score"):
        config(max_pass_ambiguity_score=d("0.600000"))
    with pytest.raises(ValueError, match="datetime"):
        report(candidate(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, tzinfo=UTC))

    for value in (row, report(candidate())):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_coverage", "_confidence", "_pressure", "_score")):
                assert type(item_value) is Decimal


def test_report_and_digest_consistency_rejects_tampering() -> None:
    valid = report(candidate())
    module = api()

    assert module.validate_candidate_decision_resolution_path_ambiguity_score_report(valid) is True

    with pytest.raises(ValueError, match="ambiguity_score must match"):
        replace(valid.results[0], ambiguity_score=d("0.123456"))
    with pytest.raises(ValueError, match="status must match"):
        replace(valid.results[0], status="block")
    with pytest.raises(ValueError, match="result_sha256 must match"):
        replace(valid.results[0], result_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(valid.results[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_ambiguity_score must match"):
        replace(valid, average_ambiguity_score=d("0.123456"))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(valid, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(valid, derived_validation_digest="0" * 64)


def test_empty_report_is_blocked_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.min_ambiguity_score == ZERO
    assert empty.max_ambiguity_score == ZERO
    assert empty.average_ambiguity_score == ZERO
    assert empty.status == "block"
    assert empty.reason_codes == ("resolution_path_ambiguity_empty",)
    assert empty.results == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert_sha256(empty.report_sha256)


def test_source_has_no_io_network_persistence_or_live_action_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "builtins.open",
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

    lowered = source.lower()
    for term in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "place_order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "dsn",
        "table",
    ):
        assert term not in lowered
