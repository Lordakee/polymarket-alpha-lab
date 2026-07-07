from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_candidate_priority_ranker_report"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)


class DerivedDecimal(Decimal):
    pass


class DerivedDatetime(datetime):
    pass


def module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "min_pass_priority_score": d("0.400000"),
        "min_watch_priority_score": d("0.150000"),
        "min_pass_confidence": d("0.700000"),
        "min_watch_confidence": d("0.400000"),
        "max_watch_evidence_gap": d("0.600000"),
        "max_block_evidence_gap": d("0.850000"),
        "max_watch_cost_friction": d("0.400000"),
        "max_block_cost_friction": d("0.750000"),
        "max_watch_resolution_risk": d("0.400000"),
        "max_block_resolution_risk": d("0.750000"),
        "min_pass_freshness": d("0.550000"),
        "min_watch_freshness": d("0.200000"),
        "confidence_weight": d("0.300000"),
        "evidence_gap_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "cost_friction_weight": d("0.100000"),
        "resolution_risk_weight": d("0.150000"),
    }
    values.update(overrides)
    return report_module.ResearchCandidatePriorityRankerConfig(**values)


def candidate(**overrides: object) -> Any:
    report_module = module()
    values = {
        "candidate_id": "candidate-alpha",
        "event_id": "event-alpha",
        "event_slug": "event-alpha",
        "evaluated_at": EVALUATED_AT,
        "confidence": d("0.900000"),
        "evidence_gap": d("0.200000"),
        "cost_friction": d("0.050000"),
        "resolution_risk": d("0.100000"),
        "freshness": d("0.850000"),
        "source_config_version": (
            report_module.DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION
        ),
    }
    values.update(overrides)
    return report_module.ResearchCandidatePriorityRankerCandidate(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_research_candidate_priority_ranker_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_manual_research_priority_report_and_safe_payload() -> None:
    report_module = module()
    report = build_report(
        candidate(
            candidate_id="candidate-watch",
            event_id="event-watch",
            event_slug="event-watch",
            confidence=d("0.650000"),
            evidence_gap=d("0.550000"),
            cost_friction=d("0.100000"),
            resolution_risk=d("0.200000"),
            freshness=d("0.700000"),
        ),
        candidate(
            candidate_id="candidate-block",
            event_id="event-block",
            event_slug="event-block",
            confidence=d("0.800000"),
            evidence_gap=d("0.900000"),
            cost_friction=d("0.200000"),
            resolution_risk=d("0.200000"),
            freshness=d("0.600000"),
        ),
        candidate(
            candidate_id="candidate-beta",
            event_id="event-beta",
            event_slug="event-beta",
            confidence=d("0.850000"),
            evidence_gap=d("0.400000"),
            cost_friction=d("0.060000"),
            resolution_risk=d("0.080000"),
            freshness=d("0.900000"),
        ),
        candidate(),
    )

    assert report.generated_at == GENERATED_AT
    assert report.candidate_count == d("4.000000")
    assert report.pass_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.top_candidate_id == "candidate-beta"
    assert report.max_priority_score == d("0.535000")
    assert report.average_priority_score == d("0.488625")
    assert report.research_queue_status == "block"
    assert report.next_research_step == "hold_manual_research_queue"
    assert report.reason_codes == (
        "evidence_gap_above_block_limit",
        "confidence_below_pass_minimum",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.priority_rank, row.candidate_id, row.research_status) for row in report.rows) == (
        (d("1.000000"), "candidate-beta", "pass"),
        (d("2.000000"), "candidate-alpha", "pass"),
        (d("3.000000"), "candidate-watch", "watch"),
        (d("4.000000"), "candidate-block", "block"),
    )
    assert report.rows[0].priority_score == d("0.517000")
    assert report.rows[1].priority_score == d("0.470000")
    assert report.rows[2].priority_score == d("0.432500")
    assert report.rows[3].priority_score == d("0.535000")

    payload = report_module.research_candidate_priority_ranker_report_public_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "4.000000"
    assert payload["top_priority_rank"] == "1.000000"
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "0.517000"
    assert payload["rows"][0]["evaluated_at"] == "2026-07-06T11:45:00+00:00"
    assert_no_public_sensitive_keys(payload)
    assert report_module.validate_research_candidate_priority_ranker_report_public_payload(
        payload,
    )
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_and_all_pass_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.candidate_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.top_candidate_id is None
    assert empty.max_priority_score == d("0.000000")
    assert empty.average_priority_score is None
    assert empty.research_queue_status == "pass"
    assert empty.reason_codes == ("research_candidate_priority_ranker_empty",)
    assert empty.rows == ()

    all_pass = build_report(
        candidate(
            candidate_id="candidate-beta",
            event_id="event-beta",
            event_slug="event-beta",
            confidence=d("0.850000"),
            evidence_gap=d("0.400000"),
            freshness=d("0.900000"),
        ),
        candidate(),
    )

    assert all_pass.candidate_count == d("2.000000")
    assert all_pass.pass_count == d("2.000000")
    assert all_pass.reason_codes == ("research_candidate_priority_ranker_pass",)
    assert tuple(row.candidate_id for row in all_pass.rows) == (
        "candidate-beta",
        "candidate-alpha",
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_RESEARCH_CANDIDATE_PRIORITY_RANKER_REPORT_CONFIG_VERSION",
        "ResearchCandidatePriorityRankerCandidate",
        "ResearchCandidatePriorityRankerConfig",
        "ResearchCandidatePriorityRankerReport",
        "ResearchCandidatePriorityRankerRow",
        "build_research_candidate_priority_ranker_report",
        "research_candidate_priority_ranker_report_public_payload",
        "validate_research_candidate_priority_ranker_report_public_payload",
    )
    for exported_name in report_module.__all__:
        exported = getattr(report_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(candidate())
    for item in (cfg(), candidate(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            assert type(value) is not int
            if field.name.endswith(("_count", "_score", "_risk", "_gap", "_friction")):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="confidence must be a Decimal"):
        candidate(confidence=DerivedDecimal("0.900000"))
    with pytest.raises(ValueError, match="min_pass_priority_score must be a Decimal"):
        cfg(min_pass_priority_score=DerivedDecimal("0.400000"))

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.ResearchCandidatePriorityRankerConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeCandidate(report_module.ResearchCandidatePriorityRankerCandidate):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.ResearchCandidatePriorityRankerRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.ResearchCandidatePriorityRankerReport):
            pass


def test_validation_rejects_invalid_inputs_flags_duplicates_and_dates() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_research_candidate_priority_ranker_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="evaluated_at must be timezone-aware"):
        candidate(evaluated_at=datetime(2026, 7, 6, 11, 45))
    with pytest.raises(ValueError, match="evaluated_at must be a datetime"):
        candidate(evaluated_at=DerivedDatetime(2026, 7, 6, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        build_report(candidate(evaluated_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="confidence"):
        candidate(confidence=d("1.100000"))
    with pytest.raises(ValueError, match="candidates"):
        report_module.build_research_candidate_priority_ranker_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_research_candidate_priority_ranker_report(
            (candidate(),),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        build_report(candidate(), candidate(event_id="event-beta"))
    with pytest.raises(ValueError, match="duplicate event_id"):
        build_report(candidate(), candidate(candidate_id="candidate-beta"))


def test_manual_report_consistency_and_payload_safety_are_enforced() -> None:
    report_module = module()
    report = build_report(candidate())

    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="priority_rank"):
        replace(report, rows=(replace(report.rows[0], priority_rank=d("2.000000")),))
    with pytest.raises(ValueError, match="research_status"):
        replace(report.rows[0], research_status="watch")

    payload = report_module.research_candidate_priority_ranker_report_public_payload(report)
    unsafe_payload_key = dict(payload)
    unsafe_payload_key["".join(("wal", "let"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_research_candidate_priority_ranker_report_public_payload(
            unsafe_payload_key,
        )

    unsafe_payload_value = dict(payload)
    unsafe_payload_value["top_candidate_id"] = "candidate-" + "".join(("tra", "de"))
    with pytest.raises(ValueError, match="unsafe public"):
        report_module.validate_research_candidate_priority_ranker_report_public_payload(
            unsafe_payload_value,
        )

    for forbidden_key in (
        "candidate_id",
        "event_id",
        "event_slug",
        "source_config_version",
        "top_candidate_id",
    ):
        keyed_payload = dict(payload)
        keyed_payload[forbidden_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report_module.validate_research_candidate_priority_ranker_report_public_payload(
                keyed_payload,
            )

        nested_payload = dict(payload)
        nested_payload["rows"] = [dict(payload["rows"][0], **{forbidden_key: "redacted"})]
        with pytest.raises(ValueError, match="unsafe public"):
            report_module.validate_research_candidate_priority_ranker_report_public_payload(
                nested_payload,
            )

    numeric_payload = dict(payload)
    numeric_payload["candidate_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_research_candidate_priority_ranker_report_public_payload(
            numeric_payload,
        )


def test_module_omits_runtime_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_candidate_priority_ranker_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "socket",
        "psycopg",
        "sqlalchemy",
        "private_key",
        "broker",
        "authorization",
    ):
        assert forbidden not in lowered

    for forbidden in (
        "".join(("wal", "let")),
        "".join(("ord", "er")),
        "".join(("tra", "de")),
        "".join(("bu", "y")),
        "".join(("sel", "l")),
        "".join(("pos", "ition")),
        "".join(("not", "ional")),
        "".join(("mut", "ation")),
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("float found in public payload")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError("int found in public payload")
    if isinstance(value, Decimal):
        raise AssertionError("Decimal found in public payload")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_public_numeric(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            assert_no_public_numeric(nested)


def assert_no_public_sensitive_keys(value: Any) -> None:
    forbidden_keys = {
        "candidate_id",
        "event_id",
        "event_slug",
        "source_config_version",
        "top_candidate_id",
    }
    if isinstance(value, dict):
        assert not (set(value) & forbidden_keys)
        for nested in value.values():
            assert_no_public_sensitive_keys(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            assert_no_public_sensitive_keys(nested)
