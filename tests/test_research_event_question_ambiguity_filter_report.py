from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_question_ambiguity_filter_report import (
    ResearchEventQuestionAmbiguityFilterConfig,
    ResearchEventQuestionAmbiguityFilterReport,
    ResearchEventQuestionAmbiguityFilterSubject,
    build_research_event_question_ambiguity_filter_report,
    research_event_question_ambiguity_filter_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def subject(
    public_event_bucket: str = "macro-policy-cluster",
    *,
    aggregate_rule_clarity: Decimal = Decimal("0.900000"),
    condition_specificity: Decimal = Decimal("0.900000"),
    edge_case_count: Decimal = Decimal("0"),
    resolution_source_consistency: Decimal = Decimal("0.900000"),
    deadline_clarity: Decimal = Decimal("0.900000"),
) -> ResearchEventQuestionAmbiguityFilterSubject:
    return ResearchEventQuestionAmbiguityFilterSubject(
        public_event_bucket=public_event_bucket,
        aggregate_rule_clarity=aggregate_rule_clarity,
        condition_specificity=condition_specificity,
        edge_case_count=edge_case_count,
        resolution_source_consistency=resolution_source_consistency,
        deadline_clarity=deadline_clarity,
    )


def test_empty_input_returns_report_only_public_pass_report() -> None:
    report = build_research_event_question_ambiguity_filter_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityFilterConfig(),
    )

    assert report == ResearchEventQuestionAmbiguityFilterReport(
        generated_at=GENERATED_AT,
        config_version="research_event_question_ambiguity_filter_report",
        event_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        lowest_rule_clarity=Decimal("0"),
        lowest_condition_specificity=Decimal("0"),
        highest_edge_case_count=Decimal("0"),
        lowest_resolution_source_consistency=Decimal("0"),
        lowest_deadline_clarity=Decimal("0"),
        highest_ambiguity_score=Decimal("0"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_pass_watch_and_block_classification_use_aggregate_public_fields_only() -> None:
    report = build_research_event_question_ambiguity_filter_report(
        (
            subject("pass-cluster"),
            subject(
                "watch-cluster",
                aggregate_rule_clarity=Decimal("0.650000"),
                condition_specificity=Decimal("0.760000"),
                edge_case_count=Decimal("2"),
                resolution_source_consistency=Decimal("0.720000"),
                deadline_clarity=Decimal("0.740000"),
            ),
            subject(
                "block-cluster",
                aggregate_rule_clarity=Decimal("0.300000"),
                condition_specificity=Decimal("0.400000"),
                edge_case_count=Decimal("5"),
                resolution_source_consistency=Decimal("0.250000"),
                deadline_clarity=Decimal("0.450000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityFilterConfig(),
    )

    assert tuple(row.public_event_bucket for row in report.rows) == (
        "block-cluster",
        "pass-cluster",
        "watch-cluster",
    )
    assert [row.public_status for row in report.rows] == ["block", "pass", "watch"]
    assert report.status == "block"
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")

    pass_row = report.rows[1]
    assert pass_row.ambiguity_score == Decimal("0.080000")
    assert pass_row.reason_codes == ()

    watch_row = report.rows[2]
    assert watch_row.reason_codes == (
        "edge_case_count_watch",
        "low_rule_clarity_watch",
        "unclear_deadline_watch",
    )

    block_row = report.rows[0]
    assert block_row.ambiguity_score == Decimal("0.720000")
    assert block_row.reason_codes == (
        "edge_case_count_block",
        "inconsistent_resolution_source_block",
        "low_condition_specificity_block",
        "low_rule_clarity_block",
        "unclear_deadline_block",
    )
    assert not _contains_forbidden_public_key(
        research_event_question_ambiguity_filter_payload(report),
    )


def test_multiple_watch_flags_do_not_escalate_to_block_without_block_threshold() -> None:
    report = build_research_event_question_ambiguity_filter_report(
        (
            subject(
                aggregate_rule_clarity=Decimal("0.700000"),
                condition_specificity=Decimal("0.700000"),
                edge_case_count=Decimal("3"),
                resolution_source_consistency=Decimal("0.700000"),
                deadline_clarity=Decimal("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityFilterConfig(),
    )

    row = report.rows[0]
    assert row.public_status == "watch"
    assert row.reason_codes == (
        "edge_case_count_watch",
        "inconsistent_resolution_source_watch",
        "low_condition_specificity_watch",
        "low_rule_clarity_watch",
        "unclear_deadline_watch",
    )


def test_payload_digest_is_deterministic_and_decimal_string_only() -> None:
    config = ResearchEventQuestionAmbiguityFilterConfig()
    subjects = (
        subject("z-cluster", aggregate_rule_clarity=Decimal("0.650000")),
        subject("a-cluster", edge_case_count=Decimal("5")),
        subject("m-cluster", deadline_clarity=Decimal("0.450000")),
    )

    report = build_research_event_question_ambiguity_filter_report(
        subjects,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_question_ambiguity_filter_report(
        tuple(reversed(subjects)),
        generated_at=GENERATED_AT,
        config=config,
    )
    payload = research_event_question_ambiguity_filter_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert [row.public_event_bucket for row in report.rows] == [
        "a-cluster",
        "m-cluster",
        "z-cluster",
    ]
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_payload_digest == report.derived_payload_digest
    assert len(report.derived_payload_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_payload_digest)
    assert payload["derived_payload_digest"] == report.derived_payload_digest
    assert payload["event_count"] == "3.000000"
    assert payload["highest_edge_case_count"] == "5.000000"
    assert payload["rows"][0]["edge_case_count"] == "5.000000"
    assert payload["reason_code_counts"][0][1] == "1.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_payload_digest"):
        research_event_question_ambiguity_filter_payload(tampered_payload)


def test_validation_rejects_non_decimal_numbers_datetimes_flags_and_public_leakage() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_question_ambiguity_filter_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchEventQuestionAmbiguityFilterConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_question_ambiguity_filter_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()),
            config=ResearchEventQuestionAmbiguityFilterConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_event_question_ambiguity_filter_report(
            (),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=ResearchEventQuestionAmbiguityFilterConfig(),
        )
    with pytest.raises(ValueError, match="aggregate_rule_clarity must be a Decimal"):
        subject(aggregate_rule_clarity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_specificity must be a Decimal"):
        subject(condition_specificity=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="edge_case_count must be an integer Decimal"):
        subject(edge_case_count=Decimal("1.500000"))
    with pytest.raises(ValueError, match="deadline_clarity must be between 0 and 1"):
        subject(deadline_clarity=Decimal("1.000001"))
    with pytest.raises(ValueError, match="resolution_source_consistency must be nonnegative"):
        subject(resolution_source_consistency=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(
            ResearchEventQuestionAmbiguityFilterConfig(),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public"):
        subject(public_event_bucket="contains-market-id")
    with pytest.raises(ValueError, match="raw question text"):
        subject(public_event_bucket="Will this happen by Friday?")

    payload = research_event_question_ambiguity_filter_payload(
        build_research_event_question_ambiguity_filter_report(
            (subject(),),
            generated_at=GENERATED_AT,
            config=ResearchEventQuestionAmbiguityFilterConfig(),
        ),
    )
    unsafe_payload = dict(payload)
    unsafe_payload["question"] = "Will this leak?"
    with pytest.raises(ValueError, match="unsafe public"):
        research_event_question_ambiguity_filter_payload(unsafe_payload)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchEventQuestionAmbiguityFilterConfig()
    input_row = subject()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.public_event_bucket = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventQuestionAmbiguityFilterConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class SubjectSubclass(ResearchEventQuestionAmbiguityFilterSubject):
            pass


def test_static_module_is_report_only_and_has_no_forbidden_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_question_ambiguity_filter_report.py",
    ).read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "database",
        "persist",
        "private_key",
        "wallet",
        "order",
        "notional",
        "position",
    )

    assert not [term for term in forbidden_terms if term in lowered_source]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _contains_forbidden_public_key(value: object) -> bool:
    forbidden_fragments = (
        "_id",
        "id_",
        "slug",
        "raw_question",
        "question_text",
        "source_ref",
        "source_reference",
        "storage",
        "auth",
        "trading",
    )
    if isinstance(value, dict):
        return any(
            any(fragment in key.lower() for fragment in forbidden_fragments)
            or _contains_forbidden_public_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_public_key(item) for item in value)
    return False
