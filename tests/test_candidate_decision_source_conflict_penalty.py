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


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_source_conflict_penalty"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing source conflict penalty module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def aggregate(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_key": "redacted_candidate_alpha",
        "observed_at": GENERATED_AT,
        "supporting_stance_count": d("4"),
        "contradictory_stance_count": d("0"),
        "neutral_stance_count": d("1"),
        "source_independence_score": d("0.900000"),
        "authority_score": d("0.800000"),
        "freshness_score": d("0.900000"),
        "conflict_severity_score": d("0.900000"),
        "aggregate_version": "aggregate-v1",
    }
    values.update(overrides)
    return module.CandidateDecisionSourceConflictPenaltyAggregate(**values)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION,
        "pass_penalty_threshold": d("0.250000"),
        "watch_penalty_threshold": d("0.600000"),
        "max_pass_contradictory_stance_ratio": d("0.250000"),
        "max_watch_contradictory_stance_ratio": d("0.500000"),
        "max_pass_independence_conflict_score": d("0.500000"),
        "max_watch_independence_conflict_score": d("0.800000"),
        "max_pass_authority_conflict_score": d("0.500000"),
        "max_watch_authority_conflict_score": d("0.800000"),
        "max_pass_freshness_conflict_score": d("0.500000"),
        "max_watch_freshness_conflict_score": d("0.800000"),
        "max_pass_conflict_severity_score": d("0.300000"),
        "max_watch_conflict_severity_score": d("0.700000"),
        "contradictory_stance_ratio_weight": d("0.300000"),
        "source_independence_weight": d("0.200000"),
        "authority_weight": d("0.200000"),
        "freshness_weight": d("0.150000"),
        "conflict_severity_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.CandidateDecisionSourceConflictPenaltyConfig(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_candidate_decision_source_conflict_penalty(
        tuple(items),
        generated_at=generated_at,
        config=cfg if cfg is not None else config(),
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


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


def test_scores_source_conflict_penalties_and_sorts_highest_penalty_first() -> None:
    report = build_report(
        aggregate(
            redacted_candidate_key="redacted_candidate_pass",
            supporting_stance_count=d("5"),
            contradictory_stance_count=d("0"),
            neutral_stance_count=d("1"),
            source_independence_score=d("0.900000"),
            authority_score=d("0.800000"),
            freshness_score=d("0.900000"),
            conflict_severity_score=d("0.900000"),
        ),
        aggregate(
            redacted_candidate_key="redacted_candidate_watch",
            supporting_stance_count=d("3"),
            contradictory_stance_count=d("2"),
            neutral_stance_count=d("1"),
            source_independence_score=d("0.600000"),
            authority_score=d("0.700000"),
            freshness_score=d("0.700000"),
            conflict_severity_score=d("0.500000"),
        ),
        aggregate(
            redacted_candidate_key="redacted_candidate_block",
            supporting_stance_count=d("1"),
            contradictory_stance_count=d("5"),
            neutral_stance_count=d("0"),
            source_independence_score=d("0.900000"),
            authority_score=d("0.850000"),
            freshness_score=d("0.850000"),
            conflict_severity_score=d("0.900000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "candidate-decision-source-conflict-penalty-v1"
    assert report.penalty_status == "block"
    assert report.candidate_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_conflict_penalty_score == d("0.467500")
    assert report.max_conflict_penalty_score == d("0.862500")
    assert report.max_contradictory_stance_ratio == d("0.833333")
    assert report.max_conflict_severity_score == d("0.900000")
    assert report.reason_codes == (
        "source_conflict_penalty_report_block",
        "no_contradictory_source_stances",
        "contradictory_source_stance_watch",
        "contradictory_source_stance_block",
        "independent_source_conflict_watch",
        "independent_source_conflict_block",
        "authority_conflict_watch",
        "authority_conflict_block",
        "fresh_conflict_watch",
        "fresh_conflict_block",
        "conflict_severity_watch",
        "conflict_severity_block",
        "source_conflict_penalty_watch_score",
        "source_conflict_penalty_block_score",
        "source_conflict_penalty_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_sha256(report.derived_validation_digest)

    assert tuple(row.redacted_candidate_key for row in report.rows) == (
        "redacted_candidate_block",
        "redacted_candidate_watch",
        "redacted_candidate_pass",
    )
    blocked, watched, passed = report.rows

    assert blocked.rank == d("1.000000")
    assert blocked.total_stance_count == d("6.000000")
    assert blocked.contradictory_stance_ratio == d("0.833333")
    assert blocked.conflict_penalty_score == d("0.862500")
    assert blocked.penalty_band == "block"
    assert blocked.reason_codes == (
        "contradictory_source_stance_block",
        "independent_source_conflict_block",
        "authority_conflict_block",
        "fresh_conflict_block",
        "conflict_severity_block",
        "source_conflict_penalty_block_score",
    )
    assert_sha256(blocked.derived_validation_digest)

    assert watched.rank == d("2.000000")
    assert watched.total_stance_count == d("6.000000")
    assert watched.contradictory_stance_ratio == d("0.333333")
    assert watched.conflict_penalty_score == d("0.540000")
    assert watched.penalty_band == "watch"
    assert watched.reason_codes == (
        "contradictory_source_stance_watch",
        "independent_source_conflict_watch",
        "authority_conflict_watch",
        "fresh_conflict_watch",
        "conflict_severity_watch",
        "source_conflict_penalty_watch_score",
    )

    assert passed.rank == d("3.000000")
    assert passed.total_stance_count == d("6.000000")
    assert passed.contradictory_stance_ratio == d("0.000000")
    assert passed.conflict_penalty_score == d("0.000000")
    assert passed.penalty_band == "pass"
    assert passed.reason_codes == (
        "no_contradictory_source_stances",
        "source_conflict_penalty_pass",
    )
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_payload_is_redacted_decimal_stringed_json_ready_and_tamper_checked() -> None:
    module = api()
    report = build_report(
        aggregate(
            redacted_candidate_key="redacted_candidate_payload",
            supporting_stance_count=d("5"),
            contradictory_stance_count=d("1"),
            neutral_stance_count=d("0"),
            source_independence_score=d("0.400000"),
            authority_score=d("0.300000"),
            freshness_score=d("0.300000"),
            conflict_severity_score=d("0.200000"),
        ),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.candidate_decision_source_conflict_penalty_payload(report)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_conflict_penalty_score"] == "0.265000"
    assert payload["rows"][0]["redacted_candidate_key"] == "redacted_candidate_payload"
    assert payload["rows"][0]["contradictory_stance_ratio"] == "0.166667"
    assert payload["rows"][0]["conflict_penalty_score"] == "0.265000"
    assert payload["rows"][0]["penalty_band"] == "watch"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    for forbidden in (
        "http",
        "market_id",
        "market_slug",
        "question",
        "raw_text",
        "source_ref",
        "source_url",
        "wallet",
        "order",
        "trade",
        "auth_token",
        "private_key",
        "position_size",
        "buy",
        "sell",
        "recommendation",
        "dsn",
        "table_name",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.rows[0], conflict_penalty_score=d("0.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("2.000000"))


def test_rejects_public_leaks_phase_flag_breaks_non_decimals_and_future_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="redacted"):
        aggregate(redacted_candidate_key="candidate_123")

    with pytest.raises(ValueError, match="unsafe public"):
        aggregate(aggregate_version="https://example.invalid/path")

    with pytest.raises(ValueError, match="unsafe public"):
        aggregate(aggregate_version="source-url-v1")

    with pytest.raises(ValueError, match="unsafe public"):
        aggregate(aggregate_version="candidate-id-v1")

    with pytest.raises(ValueError, match="unsafe public"):
        aggregate(aggregate_version="sourceUrl-v1")

    with pytest.raises(ValueError, match="public identifier"):
        aggregate(aggregate_version="Associated Press calls Alpha")

    with pytest.raises(ValueError, match="public identifier"):
        aggregate(aggregate_version="aggregate_v1")

    with pytest.raises(ValueError, match="public identifier"):
        aggregate(aggregate_version="aggregate.v1")

    with pytest.raises(ValueError, match="Decimal"):
        aggregate(source_independence_score=DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="Decimal"):
        aggregate(authority_score=0.9)

    with pytest.raises(ValueError, match="required decimal precision"):
        aggregate(source_independence_score=d("0.9000001"))

    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            aggregate(observed_at=datetime(2026, 7, 7, 12, 1, tzinfo=UTC)),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="CandidateDecisionSourceConflictPenaltyConfig"):
        module.build_candidate_decision_source_conflict_penalty(
            (),
            generated_at=GENERATED_AT,
            config=object(),
        )

    empty = module.build_candidate_decision_source_conflict_penalty(
        (),
        generated_at=GENERATED_AT,
        config=config(),
    )
    assert empty.penalty_status == "block"
    assert empty.candidate_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("source_conflict_penalty_report_empty",)


def test_dataclasses_are_frozen_final_and_exports_are_scoped() -> None:
    module = api()
    report = build_report(aggregate())

    with pytest.raises(FrozenInstanceError):
        report.penalty_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadAggregate(module.CandidateDecisionSourceConflictPenaltyAggregate):
            pass

    with pytest.raises(TypeError):
        type(
            "CandidateDecisionSourceConflictPenaltyAggregate",
            (module.CandidateDecisionSourceConflictPenaltyAggregate,),
            {"__module__": module.__name__},
        )

    with pytest.raises(TypeError):
        type(
            "CandidateDecisionSourceConflictPenaltyReport",
            (module._FinalPublicDataclass,),
            {"__module__": module.__name__},
        )

    class ReportSpoof:
        @property
        def __class__(self):  # type: ignore[override]
            return module.CandidateDecisionSourceConflictPenaltyReport

    with pytest.raises(ValueError, match="CandidateDecisionSourceConflictPenaltyReport"):
        module.candidate_decision_source_conflict_penalty_payload(ReportSpoof())

    with pytest.raises(ValueError, match="Decimal"):
        replace(report.rows[0], rank=1)

    with pytest.raises(ValueError, match="Decimal"):
        replace(report, candidate_count=1)

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_SOURCE_CONFLICT_PENALTY_VERSION",
        "CandidateDecisionSourceConflictPenaltyAggregate",
        "CandidateDecisionSourceConflictPenaltyConfig",
        "CandidateDecisionSourceConflictPenaltyReport",
        "CandidateDecisionSourceConflictPenaltyRow",
        "build_candidate_decision_source_conflict_penalty",
        "candidate_decision_source_conflict_penalty_payload",
    )


def test_no_unsafe_public_surfaces_or_io_are_exposed() -> None:
    module = api()
    unsafe_name_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "raw_text",
        "dsn",
        "table",
        "wallet",
        "auth_token",
        "order",
        "trade",
        "private_key",
        "token",
        "position",
        "sizing",
        "buy",
        "sell",
        "recommendation",
        "account",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in unsafe_name_fragments)

    for cls in (
        module.CandidateDecisionSourceConflictPenaltyAggregate,
        module.CandidateDecisionSourceConflictPenaltyConfig,
        module.CandidateDecisionSourceConflictPenaltyReport,
        module.CandidateDecisionSourceConflictPenaltyRow,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_name_fragments)

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
        "web3",
        "ccxt",
        "os",
        "pathlib",
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
        "getenv",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names

    with pytest.raises(ValueError, match="unsafe public"):
        module._reject_unsafe_public_payload(
            "public payload",
            {"source---url": "redacted_safe"},
            allow_containers=True,
        )

    with pytest.raises(ValueError, match="unsafe public"):
        module._reject_unsafe_public_payload(
            "public payload",
            {"public_ref": "market.slug.v1"},
            allow_containers=True,
        )
