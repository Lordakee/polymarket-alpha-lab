from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_conflict_resolution_score"
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
        pytest.fail(f"missing conflict resolution score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_CONFLICT_RESOLUTION_SCORE_VERSION,
        "max_pass_unresolved_contradiction_count": d("1"),
        "max_watch_unresolved_contradiction_count": d("3"),
        "max_unresolved_contradiction_count_for_score": d("5"),
        "max_pass_unresolved_contradiction_severity": d("0.300000"),
        "max_watch_unresolved_contradiction_severity": d("0.700000"),
        "min_pass_official_hierarchy_strength": d("0.750000"),
        "min_watch_official_hierarchy_strength": d("0.500000"),
        "min_pass_independent_corroboration_count": d("3"),
        "min_watch_independent_corroboration_count": d("1"),
        "max_pass_analyst_dissent_score": d("0.200000"),
        "max_watch_analyst_dissent_score": d("0.500000"),
        "max_pass_ambiguity_dispute_risk_score": d("0.250000"),
        "max_watch_ambiguity_dispute_risk_score": d("0.600000"),
        "min_pass_conflict_resolution_confidence": d("0.750000"),
        "min_watch_conflict_resolution_confidence": d("0.500000"),
        "official_hierarchy_weight": d("0.300000"),
        "independent_corroboration_weight": d("0.250000"),
        "contradiction_count_weight": d("0.200000"),
        "contradiction_severity_weight": d("0.150000"),
        "analyst_consensus_weight": d("0.050000"),
        "low_ambiguity_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionConflictResolutionScoreConfig(**values)


def facts(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "observed_at": GENERATED_AT,
        "unresolved_contradiction_count": d("0"),
        "highest_unresolved_contradiction_severity": d("0.000000"),
        "official_hierarchy_strength": d("0.900000"),
        "independent_corroboration_count": d("4"),
        "analyst_dissent_score": d("0.100000"),
        "ambiguity_dispute_risk_score": d("0.100000"),
        "fact_set_version": "facts-v1",
    }
    values.update(overrides)
    return module.CandidateDecisionConflictResolutionFacts(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_decision_conflict_resolution_score(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def with_fresh_validation_digest(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    digest_payload = dict(result)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    result["derived_validation_digest"] = sha256(encoded).hexdigest()
    return result


def test_scores_candidate_conflict_resolution_support_and_sorts_weakest_first() -> None:
    result = report(
        facts(
            redacted_candidate_ref="candidate_ref_pass",
            unresolved_contradiction_count=d("0"),
            highest_unresolved_contradiction_severity=d("0.000000"),
            official_hierarchy_strength=d("0.900000"),
            independent_corroboration_count=d("4"),
            analyst_dissent_score=d("0.100000"),
            ambiguity_dispute_risk_score=d("0.100000"),
        ),
        facts(
            redacted_candidate_ref="candidate_ref_watch",
            unresolved_contradiction_count=d("2"),
            highest_unresolved_contradiction_severity=d("0.400000"),
            official_hierarchy_strength=d("0.650000"),
            independent_corroboration_count=d("1"),
            analyst_dissent_score=d("0.350000"),
            ambiguity_dispute_risk_score=d("0.450000"),
        ),
        facts(
            redacted_candidate_ref="candidate_ref_blocked",
            unresolved_contradiction_count=d("5"),
            highest_unresolved_contradiction_severity=d("0.900000"),
            official_hierarchy_strength=d("0.350000"),
            independent_corroboration_count=d("0"),
            analyst_dissent_score=d("0.750000"),
            ambiguity_dispute_risk_score=d("0.850000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "candidate-decision-conflict-resolution-score-v1"
    assert result.support_status == "block"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.min_conflict_resolution_confidence == d("0.140000")
    assert result.average_conflict_resolution_confidence == d("0.549444")
    assert result.max_unresolved_contradiction_count == d("5")
    assert result.max_unresolved_contradiction_severity == d("0.900000")
    assert result.max_ambiguity_dispute_risk_score == d("0.850000")
    assert result.reason_codes == (
        "conflict_resolution_report_block",
        "unresolved_contradictions_blocked",
        "unresolved_contradictions_watch",
        "unresolved_contradiction_severity_blocked",
        "unresolved_contradiction_severity_watch",
        "official_hierarchy_strength_blocked",
        "official_hierarchy_strength_watch",
        "independent_corroboration_blocked",
        "independent_corroboration_watch",
        "analyst_dissent_blocked",
        "analyst_dissent_watch",
        "ambiguity_dispute_risk_blocked",
        "ambiguity_dispute_risk_watch",
        "conflict_resolution_confidence_blocked_score",
        "conflict_resolution_confidence_watch_score",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)

    assert tuple(row.redacted_candidate_ref for row in result.rows) == (
        "candidate_ref_blocked",
        "candidate_ref_watch",
        "candidate_ref_pass",
    )
    blocked, watched, passed = result.rows

    assert blocked.rank == d("1")
    assert blocked.conflict_resolution_confidence == d("0.140000")
    assert blocked.support_status == "block"
    assert blocked.reason_codes == (
        "unresolved_contradictions_blocked",
        "unresolved_contradiction_severity_blocked",
        "official_hierarchy_strength_blocked",
        "independent_corroboration_blocked",
        "analyst_dissent_blocked",
        "ambiguity_dispute_risk_blocked",
        "conflict_resolution_confidence_blocked_score",
    )
    assert_sha256(blocked.row_sha256)
    assert_sha256(blocked.derived_validation_digest)

    assert watched.conflict_resolution_confidence == d("0.548333")
    assert watched.support_status == "watch"
    assert watched.reason_codes == (
        "unresolved_contradictions_watch",
        "unresolved_contradiction_severity_watch",
        "official_hierarchy_strength_watch",
        "independent_corroboration_watch",
        "analyst_dissent_watch",
        "ambiguity_dispute_risk_watch",
        "conflict_resolution_confidence_watch_score",
    )

    assert passed.conflict_resolution_confidence == d("0.960000")
    assert passed.support_status == "pass"
    assert passed.reason_codes == ("conflict_resolution_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_payload_is_redacted_decimal_stringed_and_tamper_validated() -> None:
    module = api()
    result = report(
        facts(
            redacted_candidate_ref="candidate_ref_payload",
            unresolved_contradiction_count=d("1"),
            highest_unresolved_contradiction_severity=d("0.200000"),
            official_hierarchy_strength=d("0.800000"),
            independent_corroboration_count=d("3"),
            analyst_dissent_score=d("0.150000"),
            ambiguity_dispute_risk_score=d("0.200000"),
        ),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.candidate_decision_conflict_resolution_score_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert module.validate_candidate_decision_conflict_resolution_score_payload(payload) is True
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_conflict_resolution_confidence"] == "0.852500"
    assert payload["rows"][0]["redacted_candidate_ref"] == "candidate_ref_payload"
    assert payload["rows"][0]["unresolved_contradiction_count"] == "1.000000"
    assert payload["rows"][0]["conflict_resolution_confidence"] == "0.852500"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    for forbidden in (
        "http",
        "market_id",
        "market_slug",
        "question",
        "raw_text",
        "wallet",
        "order",
        "auth",
        "trade",
        "position",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="confidence must match"):
        replace(result.rows[0], conflict_resolution_confidence=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_conflict_resolution_confidence"):
        replace(result, average_conflict_resolution_confidence=d("0.100000"))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(result, report_sha256="0" * 64)


def test_empty_report_is_blocked_zeroed_and_readonly() -> None:
    empty = report()

    assert empty.support_status == "block"
    assert empty.reason_codes == ("conflict_resolution_report_empty",)
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.min_conflict_resolution_confidence == ZERO
    assert empty.average_conflict_resolution_confidence == ZERO
    assert empty.max_unresolved_contradiction_count == ZERO
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_report_rejects_rank_rewritten_rows_that_are_not_weakest_first() -> None:
    module = api()
    result = report(
        facts(redacted_candidate_ref="candidate_ref_strong"),
        facts(
            redacted_candidate_ref="candidate_ref_weak",
            unresolved_contradiction_count=d("5"),
            highest_unresolved_contradiction_severity=d("0.900000"),
            official_hierarchy_strength=d("0.350000"),
            independent_corroboration_count=d("0"),
            analyst_dissent_score=d("0.750000"),
            ambiguity_dispute_risk_score=d("0.850000"),
        ),
    )
    weak, strong = result.rows

    def with_rank(row: object, rank: Decimal):
        values = {field.name: getattr(row, field.name) for field in fields(row)}
        values.update(
            {
                "rank": rank,
                "row_sha256": "",
                "derived_validation_digest": "",
            },
        )
        return module.CandidateDecisionConflictResolutionScoreRow(**values)

    reordered_rows = (
        with_rank(strong, d("1")),
        with_rank(weak, d("2")),
    )

    with pytest.raises(ValueError, match="rows must be sorted"):
        module.CandidateDecisionConflictResolutionScoreReport(
            generated_at=result.generated_at,
            config_version=result.config_version,
            support_status=result.support_status,
            candidate_count=result.candidate_count,
            pass_count=result.pass_count,
            watch_count=result.watch_count,
            blocked_count=result.blocked_count,
            min_conflict_resolution_confidence=result.min_conflict_resolution_confidence,
            max_conflict_resolution_confidence=result.max_conflict_resolution_confidence,
            average_conflict_resolution_confidence=(
                result.average_conflict_resolution_confidence
            ),
            max_unresolved_contradiction_count=result.max_unresolved_contradiction_count,
            max_unresolved_contradiction_severity=(
                result.max_unresolved_contradiction_severity
            ),
            max_analyst_dissent_score=result.max_analyst_dissent_score,
            max_ambiguity_dispute_risk_score=result.max_ambiguity_dispute_risk_score,
            rows=reordered_rows,
            fact_set_versions=result.fact_set_versions,
            reason_codes=result.reason_codes,
        )


def test_report_rejects_noncontiguous_row_ranks() -> None:
    module = api()
    result = report(
        facts(redacted_candidate_ref="candidate_ref_strong"),
        facts(
            redacted_candidate_ref="candidate_ref_weak",
            unresolved_contradiction_count=d("5"),
            highest_unresolved_contradiction_severity=d("0.900000"),
            official_hierarchy_strength=d("0.350000"),
            independent_corroboration_count=d("0"),
            analyst_dissent_score=d("0.750000"),
            ambiguity_dispute_risk_score=d("0.850000"),
        ),
    )
    weak, strong = result.rows
    values = {field.name: getattr(strong, field.name) for field in fields(strong)}
    values.update(
        {
            "rank": d("3"),
            "row_sha256": "",
            "derived_validation_digest": "",
        },
    )
    row_with_gap = module.CandidateDecisionConflictResolutionScoreRow(**values)

    with pytest.raises(ValueError, match="ranks must be contiguous"):
        module.CandidateDecisionConflictResolutionScoreReport(
            generated_at=result.generated_at,
            config_version=result.config_version,
            support_status=result.support_status,
            candidate_count=result.candidate_count,
            pass_count=result.pass_count,
            watch_count=result.watch_count,
            blocked_count=result.blocked_count,
            min_conflict_resolution_confidence=result.min_conflict_resolution_confidence,
            max_conflict_resolution_confidence=result.max_conflict_resolution_confidence,
            average_conflict_resolution_confidence=(
                result.average_conflict_resolution_confidence
            ),
            max_unresolved_contradiction_count=result.max_unresolved_contradiction_count,
            max_unresolved_contradiction_severity=(
                result.max_unresolved_contradiction_severity
            ),
            max_analyst_dissent_score=result.max_analyst_dissent_score,
            max_ambiguity_dispute_risk_score=result.max_ambiguity_dispute_risk_score,
            rows=(weak, row_with_gap),
            fact_set_versions=result.fact_set_versions,
            reason_codes=result.reason_codes,
        )


def test_report_rejects_duplicate_row_redacted_candidate_refs() -> None:
    module = api()
    result = report(
        facts(redacted_candidate_ref="candidate_ref_strong"),
        facts(
            redacted_candidate_ref="candidate_ref_weak",
            unresolved_contradiction_count=d("5"),
            highest_unresolved_contradiction_severity=d("0.900000"),
            official_hierarchy_strength=d("0.350000"),
            independent_corroboration_count=d("0"),
            analyst_dissent_score=d("0.750000"),
            ambiguity_dispute_risk_score=d("0.850000"),
        ),
    )
    weak, strong = result.rows
    values = {field.name: getattr(strong, field.name) for field in fields(strong)}
    values.update(
        {
            "redacted_candidate_ref": weak.redacted_candidate_ref,
            "row_sha256": "",
            "derived_validation_digest": "",
        },
    )
    duplicate_ref_row = module.CandidateDecisionConflictResolutionScoreRow(**values)
    fact_set_versions = tuple(
        sorted(
            (row.redacted_candidate_ref, row.fact_set_version)
            for row in (weak, duplicate_ref_row)
        ),
    )

    with pytest.raises(ValueError, match="duplicate redacted_candidate_ref"):
        module.CandidateDecisionConflictResolutionScoreReport(
            generated_at=result.generated_at,
            config_version=result.config_version,
            support_status=result.support_status,
            candidate_count=result.candidate_count,
            pass_count=result.pass_count,
            watch_count=result.watch_count,
            blocked_count=result.blocked_count,
            min_conflict_resolution_confidence=result.min_conflict_resolution_confidence,
            max_conflict_resolution_confidence=result.max_conflict_resolution_confidence,
            average_conflict_resolution_confidence=(
                result.average_conflict_resolution_confidence
            ),
            max_unresolved_contradiction_count=result.max_unresolved_contradiction_count,
            max_unresolved_contradiction_severity=(
                result.max_unresolved_contradiction_severity
            ),
            max_analyst_dissent_score=result.max_analyst_dissent_score,
            max_ambiguity_dispute_risk_score=result.max_ambiguity_dispute_risk_score,
            rows=(weak, duplicate_ref_row),
            fact_set_versions=fact_set_versions,
            reason_codes=result.reason_codes,
        )


def test_rejects_invalid_inputs_thresholds_duplicates_and_flags() -> None:
    module = api()
    valid_facts = facts()
    cfg = config()

    with pytest.raises(ValueError, match="facts"):
        module.build_candidate_decision_conflict_resolution_score(
            "not-facts",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="CandidateDecisionConflictResolutionFacts"):
        module.build_candidate_decision_conflict_resolution_score(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_candidate_decision_conflict_resolution_score(
            [valid_facts],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_candidate_decision_conflict_resolution_score(
            [valid_facts],
            config=cfg,
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate redacted_candidate_ref"):
        report(valid_facts, valid_facts)
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        facts(redacted_candidate_ref="candidate-secret-alpha")
    with pytest.raises(ValueError, match="unresolved_contradiction_count"):
        facts(unresolved_contradiction_count=d("1.5"))
    with pytest.raises(ValueError, match="official_hierarchy_strength"):
        facts(official_hierarchy_strength=d("1.000001"))
    with pytest.raises(ValueError, match="analyst_dissent_score"):
        facts(analyst_dissent_score=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        module.CandidateDecisionConflictResolutionFacts(
            **{
                **valid_facts.__dict__,
                "paper_only": False,
            },
        )
    with pytest.raises(ValueError, match="max_pass_unresolved_contradiction_count"):
        config(max_pass_unresolved_contradiction_count=d("4"))
    with pytest.raises(ValueError, match="max_pass_unresolved_contradiction_severity"):
        config(max_pass_unresolved_contradiction_severity=d("0.800000"))
    with pytest.raises(ValueError, match="min_pass_official_hierarchy_strength"):
        config(min_pass_official_hierarchy_strength=d("0.400000"))
    with pytest.raises(ValueError, match="min_pass_independent_corroboration_count"):
        config(min_pass_independent_corroboration_count=d("0"))
    with pytest.raises(ValueError, match="max_pass_analyst_dissent_score"):
        config(max_pass_analyst_dissent_score=d("0.700000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(low_ambiguity_weight=d("0.040000"))


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report(facts())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.support_status = "block"  # type: ignore[misc]

    for klass in (
        module.CandidateDecisionConflictResolutionScoreConfig,
        module.CandidateDecisionConflictResolutionFacts,
        module.CandidateDecisionConflictResolutionScoreRow,
        module.CandidateDecisionConflictResolutionScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for value in (config(), facts(), row, result):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_severity", "_strength", "_score", "_risk", "_confidence", "rank")):
                assert type(item_value) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        facts(official_hierarchy_strength=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        facts(official_hierarchy_strength=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        module.build_candidate_decision_conflict_resolution_score(
            [facts()],
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, tzinfo=UTC),
        )
    with pytest.raises(TypeError, match="subclassing is not allowed"):
        type(
            "CandidateDecisionConflictResolutionFactsChild",
            (module.CandidateDecisionConflictResolutionFacts,),
            {},
        )


def test_payload_validator_rejects_unsafe_surfaces_and_bad_flags() -> None:
    module = api()
    payload = module.candidate_decision_conflict_resolution_score_payload(
        report(facts(redacted_candidate_ref="candidate_ref_safe")),
    )

    unsafe_top_level = {**payload, "market_id": "must-not-be-public"}
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_conflict_resolution_score_payload(unsafe_top_level)

    unsafe_source = {**payload, "source_ref": "must-not-be-public"}
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_conflict_resolution_score_payload(unsafe_source)

    unsafe_row = {
        **payload,
        "rows": [{**payload["rows"][0], "raw_question": "must-not-be-public"}],
    }
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_conflict_resolution_score_payload(unsafe_row)

    unsafe_value = {
        **payload,
        "rows": [{**payload["rows"][0], "redacted_candidate_ref": "candidate_ref_wallet"}],
    }
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_conflict_resolution_score_payload(unsafe_value)

    bad_flag = {**payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only"):
        module.validate_candidate_decision_conflict_resolution_score_payload(bad_flag)


def test_payload_validator_rejects_forged_public_payload_shape_and_values() -> None:
    module = api()
    payload = module.candidate_decision_conflict_resolution_score_payload(
        report(facts(redacted_candidate_ref="candidate_ref_forged")),
    )

    extra_top_level = with_fresh_validation_digest({**payload, "safe_extra": "ok"})
    with pytest.raises(ValueError, match="payload"):
        module.validate_candidate_decision_conflict_resolution_score_payload(extra_top_level)

    extra_row = with_fresh_validation_digest(
        {
            **payload["rows"][0],
            "safe_extra": "ok",
        },
    )
    payload_with_extra_row = with_fresh_validation_digest({**payload, "rows": [extra_row]})
    with pytest.raises(ValueError, match="payload"):
        module.validate_candidate_decision_conflict_resolution_score_payload(
            payload_with_extra_row,
        )

    bad_status = with_fresh_validation_digest({**payload, "support_status": "PASS"})
    with pytest.raises(ValueError, match="support_status"):
        module.validate_candidate_decision_conflict_resolution_score_payload(bad_status)

    changed_score_row = with_fresh_validation_digest(
        {
            **payload["rows"][0],
            "conflict_resolution_confidence": "0.100000",
        },
    )
    payload_with_changed_score = with_fresh_validation_digest(
        {**payload, "rows": [changed_score_row]},
    )
    with pytest.raises(ValueError, match="row_sha256"):
        module.validate_candidate_decision_conflict_resolution_score_payload(
            payload_with_changed_score,
        )


def test_source_has_no_io_db_network_or_live_mutation_surface() -> None:
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
        "live",
        "database",
        "getenv",
        "environ",
        "open(",
        "market",
        "source",
        "market_id",
        "market_slug",
        "raw_text",
    ):
        assert term not in lowered
