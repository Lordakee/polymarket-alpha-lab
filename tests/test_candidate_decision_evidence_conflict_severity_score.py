from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_evidence_conflict_severity_score"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing evidence conflict severity score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_EVIDENCE_CONFLICT_SEVERITY_SCORE_VERSION
        ),
        "max_pass_evidence_conflict_severity_score": d("0.250000"),
        "max_watch_evidence_conflict_severity_score": d("0.650000"),
        "max_pass_conflicting_claim_count": d("1"),
        "max_watch_conflicting_claim_count": d("3"),
        "max_conflicting_claim_count_for_score": d("5"),
        "min_pass_independent_public_evidence_count": d("3"),
        "min_watch_independent_public_evidence_count": d("1"),
        "min_pass_primary_evidence_alignment_score": d("0.750000"),
        "min_watch_primary_evidence_alignment_score": d("0.500000"),
        "max_pass_recency_skew_score": d("0.200000"),
        "max_watch_recency_skew_score": d("0.600000"),
        "max_pass_resolution_rule_ambiguity_score": d("0.250000"),
        "max_watch_resolution_rule_ambiguity_score": d("0.600000"),
        "conflict_severity_weight": d("0.350000"),
        "claim_count_weight": d("0.200000"),
        "primary_alignment_gap_weight": d("0.200000"),
        "independence_gap_weight": d("0.150000"),
        "recency_skew_weight": d("0.050000"),
        "rule_ambiguity_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceConflictSeverityScoreConfig(**values)


def facts(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "observed_at": GENERATED_AT,
        "conflicting_claim_count": d("0"),
        "highest_conflict_severity_score": d("0.050000"),
        "primary_evidence_alignment_score": d("0.900000"),
        "independent_public_evidence_count": d("4"),
        "recency_skew_score": d("0.100000"),
        "resolution_rule_ambiguity_score": d("0.100000"),
        "evidence_batch_version": "evidence-batch-v1",
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceConflictSeverityFacts(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_decision_evidence_conflict_severity_score(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_numeric_payload_values(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal payload value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float payload value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_values(item)


def assert_public_payload_safe(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    forbidden = (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "raw_text",
        "https://",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    for term in forbidden:
        assert term not in rendered
    assert_no_numeric_payload_values(payload)


def test_scores_pass_watch_block_and_sorts_highest_severity_first() -> None:
    result = report(
        facts(
            redacted_candidate_ref="candidate_ref_pass",
            conflicting_claim_count=d("0"),
            highest_conflict_severity_score=d("0.050000"),
            primary_evidence_alignment_score=d("0.900000"),
            independent_public_evidence_count=d("4"),
            recency_skew_score=d("0.100000"),
            resolution_rule_ambiguity_score=d("0.100000"),
        ),
        facts(
            redacted_candidate_ref="candidate_ref_watch",
            conflicting_claim_count=d("2"),
            highest_conflict_severity_score=d("0.400000"),
            primary_evidence_alignment_score=d("0.650000"),
            independent_public_evidence_count=d("1"),
            recency_skew_score=d("0.350000"),
            resolution_rule_ambiguity_score=d("0.450000"),
        ),
        facts(
            redacted_candidate_ref="candidate_ref_block",
            conflicting_claim_count=d("5"),
            highest_conflict_severity_score=d("0.900000"),
            primary_evidence_alignment_score=d("0.350000"),
            independent_public_evidence_count=d("0"),
            recency_skew_score=d("0.750000"),
            resolution_rule_ambiguity_score=d("0.850000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-decision-evidence-conflict-severity-score-v1"
    assert result.public_status == "block"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.max_evidence_conflict_severity_score == d("0.875000")
    assert result.min_evidence_conflict_severity_score == d("0.047500")
    assert result.average_evidence_conflict_severity_score == d("0.450833")
    assert result.max_conflicting_claim_count == d("5")
    assert result.max_highest_conflict_severity_score == d("0.900000")
    assert result.reason_codes == (
        "evidence_conflict_severity_report_block",
        "conflicting_claim_count_block",
        "conflicting_claim_count_watch",
        "highest_conflict_severity_block",
        "highest_conflict_severity_watch",
        "primary_evidence_alignment_block",
        "primary_evidence_alignment_watch",
        "independent_public_evidence_block",
        "independent_public_evidence_watch",
        "recency_skew_block",
        "recency_skew_watch",
        "resolution_rule_ambiguity_block",
        "resolution_rule_ambiguity_watch",
        "evidence_conflict_severity_score_block",
        "evidence_conflict_severity_score_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)

    assert tuple(row.redacted_candidate_ref for row in result.rows) == (
        "candidate_ref_block",
        "candidate_ref_watch",
        "candidate_ref_pass",
    )
    blocked, watched, passed = result.rows
    assert blocked.rank == d("1")
    assert blocked.evidence_conflict_severity_score == d("0.875000")
    assert blocked.public_status == "block"
    assert blocked.reason_codes == (
        "conflicting_claim_count_block",
        "highest_conflict_severity_block",
        "primary_evidence_alignment_block",
        "independent_public_evidence_block",
        "recency_skew_block",
        "resolution_rule_ambiguity_block",
        "evidence_conflict_severity_score_block",
    )
    assert_sha256(blocked.row_sha256)
    assert_sha256(blocked.derived_validation_digest)

    assert watched.evidence_conflict_severity_score == d("0.430000")
    assert watched.public_status == "watch"
    assert watched.reason_codes == (
        "conflicting_claim_count_watch",
        "highest_conflict_severity_watch",
        "primary_evidence_alignment_watch",
        "independent_public_evidence_watch",
        "recency_skew_watch",
        "resolution_rule_ambiguity_watch",
        "evidence_conflict_severity_score_watch",
    )

    assert passed.evidence_conflict_severity_score == d("0.047500")
    assert passed.public_status == "pass"
    assert passed.reason_codes == ("evidence_conflict_severity_pass",)


def test_payload_is_public_decimal_stringed_and_rejects_leaks() -> None:
    module = api()
    result = report(
        facts(redacted_candidate_ref="candidate_ref_payload"),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.candidate_decision_evidence_conflict_severity_score_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert module.validate_candidate_decision_evidence_conflict_severity_score_payload(payload) is True
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["redacted_candidate_ref"] == "candidate_ref_payload"
    assert payload["rows"][0]["conflicting_claim_count"] == "0.000000"
    assert payload["rows"][0]["evidence_conflict_severity_score"] == "0.047500"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload_values(payload)
    assert_public_payload_safe(payload)

    assert payload == json.loads(rendered)
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_evidence_conflict_severity_score_payload(
            {**payload, "market_id": "must-not-be-public"},
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_evidence_conflict_severity_score_payload(
            {**payload, "rows": [{**payload["rows"][0], "source_url": "must-not-be-public"}]},
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_evidence_conflict_severity_score_payload(
            {
                **payload,
                "rows": [
                    {**payload["rows"][0], "redacted_candidate_ref": "candidate_ref_wallet"}
                ],
            },
        )


def test_decimal_exact_frozen_dataclasses_and_hard_flags() -> None:
    module = api()
    result = report(facts())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.public_status = "block"  # type: ignore[misc]

    for klass in (
        module.CandidateDecisionEvidenceConflictSeverityScoreConfig,
        module.CandidateDecisionEvidenceConflictSeverityFacts,
        module.CandidateDecisionEvidenceConflictSeverityScoreRow,
        module.CandidateDecisionEvidenceConflictSeverityScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for value in (config(), facts(), row, result):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_score", "rank")):
                assert type(item_value) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        facts(highest_conflict_severity_score=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        facts(highest_conflict_severity_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        module.build_candidate_decision_evidence_conflict_severity_score(
            [facts()],
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        facts(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.validate_candidate_decision_evidence_conflict_severity_score_payload(
            {
                **module.candidate_decision_evidence_conflict_severity_score_payload(result),
                "readonly": False,
            },
        )


def test_payload_and_digests_are_deterministic_across_input_order() -> None:
    module = api()
    pass_item = facts(redacted_candidate_ref="candidate_ref_pass")
    watch_item = facts(
        redacted_candidate_ref="candidate_ref_watch",
        conflicting_claim_count=d("2"),
        highest_conflict_severity_score=d("0.400000"),
        primary_evidence_alignment_score=d("0.650000"),
        independent_public_evidence_count=d("1"),
        recency_skew_score=d("0.350000"),
        resolution_rule_ambiguity_score=d("0.450000"),
    )
    block_item = facts(
        redacted_candidate_ref="candidate_ref_block",
        conflicting_claim_count=d("5"),
        highest_conflict_severity_score=d("0.900000"),
        primary_evidence_alignment_score=d("0.350000"),
        independent_public_evidence_count=d("0"),
        recency_skew_score=d("0.750000"),
        resolution_rule_ambiguity_score=d("0.850000"),
    )

    first = report(pass_item, watch_item, block_item)
    second = report(block_item, pass_item, watch_item)
    first_payload = module.candidate_decision_evidence_conflict_severity_score_payload(first)
    second_payload = module.candidate_decision_evidence_conflict_severity_score_payload(second)

    assert first_payload == second_payload
    assert first.report_sha256 == second.report_sha256
    assert first.derived_validation_digest == second.derived_validation_digest
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_report_and_digest_consistency_rejects_tampering() -> None:
    module = api()
    result = report(facts(redacted_candidate_ref="candidate_ref_consistency"))
    payload = module.candidate_decision_evidence_conflict_severity_score_payload(result)

    assert module.validate_candidate_decision_evidence_conflict_severity_score_report(result) is True
    assert module.validate_candidate_decision_evidence_conflict_severity_score_payload(payload) is True
    assert payload["report_sha256"] == result.report_sha256
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["rows"][0]["row_sha256"] == result.rows[0].row_sha256
    assert payload["rows"][0]["derived_validation_digest"] == result.rows[0].derived_validation_digest

    with pytest.raises(ValueError, match="severity_score must match"):
        replace(result.rows[0], evidence_conflict_severity_score=d("0.999999"))
    with pytest.raises(ValueError, match="row_sha256 must match"):
        replace(result.rows[0], row_sha256="0" * 64)
    with pytest.raises(ValueError, match="average_evidence_conflict_severity_score"):
        replace(result, average_evidence_conflict_severity_score=d("0.999999"))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(result, report_sha256="0" * 64)


def test_empty_report_is_blocked_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.public_status == "block"
    assert empty.reason_codes == ("evidence_conflict_severity_report_empty",)
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.max_evidence_conflict_severity_score == ZERO
    assert empty.average_evidence_conflict_severity_score == ZERO
    assert empty.max_conflicting_claim_count == ZERO
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_rejects_invalid_inputs_thresholds_duplicates_and_unsafe_statuses() -> None:
    module = api()
    valid_facts = facts()
    cfg = config()

    with pytest.raises(ValueError, match="facts"):
        module.build_candidate_decision_evidence_conflict_severity_score(
            "not-facts",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="CandidateDecisionEvidenceConflictSeverityFacts"):
        module.build_candidate_decision_evidence_conflict_severity_score(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_candidate_decision_evidence_conflict_severity_score(
            [valid_facts],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate redacted_candidate_ref"):
        report(valid_facts, valid_facts)
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        facts(redacted_candidate_ref="candidate-secret-alpha")
    with pytest.raises(ValueError, match="conflicting_claim_count"):
        facts(conflicting_claim_count=d("1.5"))
    with pytest.raises(ValueError, match="highest_conflict_severity_score"):
        facts(highest_conflict_severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="primary_evidence_alignment_score"):
        facts(primary_evidence_alignment_score=d("-0.000001"))
    with pytest.raises(ValueError, match="max_pass_evidence_conflict_severity_score"):
        config(max_pass_evidence_conflict_severity_score=d("0.900000"))
    with pytest.raises(ValueError, match="min_pass_independent_public_evidence_count"):
        config(min_pass_independent_public_evidence_count=d("0"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(rule_ambiguity_weight=d("0.040000"))
    with pytest.raises(ValueError, match="public_status"):
        replace(report(valid_facts), public_status="blocked")


def test_source_has_no_io_db_network_or_execution_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
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
        "csv",
        "http",
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
    assert not ({name.split(".")[0] for name in imports} & banned_import_roots)

    lowered = source.lower()
    for term in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "account",
        "auth",
        "buy",
        "sell",
        "order",
        "sizing",
        "trade",
        "position",
        "recommend",
        "database",
        "getenv",
        "environ",
        "open(",
        "market_id",
        "market_slug",
        "source_ref",
        "source_url",
        "source_text",
        "raw_text",
    ):
        assert term not in lowered
