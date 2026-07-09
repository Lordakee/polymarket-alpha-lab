from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_question_ambiguity_risk_report import (
    ResearchEventQuestionAmbiguityRiskConfig,
    ResearchEventQuestionAmbiguityRiskReport,
    ResearchEventQuestionAmbiguityRiskSubject,
    build_research_event_question_ambiguity_risk_report,
    research_event_question_ambiguity_risk_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def subject(
    public_event_bucket: str = "macro-policy-cluster",
    *,
    clause_clarity: Decimal = Decimal("0.900000"),
    edge_case_coverage: Decimal = Decimal("0.900000"),
    authority_traceability: Decimal = Decimal("0.900000"),
    date_boundary_precision: Decimal = Decimal("0.900000"),
    contradiction_pressure: Decimal = Decimal("0.000000"),
) -> ResearchEventQuestionAmbiguityRiskSubject:
    return ResearchEventQuestionAmbiguityRiskSubject(
        public_event_bucket=public_event_bucket,
        clause_clarity=clause_clarity,
        edge_case_coverage=edge_case_coverage,
        authority_traceability=authority_traceability,
        date_boundary_precision=date_boundary_precision,
        contradiction_pressure=contradiction_pressure,
    )


def test_empty_input_returns_report_only_public_pass_report() -> None:
    report = build_research_event_question_ambiguity_risk_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityRiskConfig(),
    )

    assert report == ResearchEventQuestionAmbiguityRiskReport(
        generated_at=GENERATED_AT,
        config_version="research_event_question_ambiguity_risk_report",
        event_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        lowest_clause_clarity=Decimal("0"),
        lowest_edge_case_coverage=Decimal("0"),
        lowest_authority_traceability=Decimal("0"),
        lowest_date_boundary_precision=Decimal("0"),
        highest_contradiction_pressure=Decimal("0"),
        highest_ambiguity_risk_score=Decimal("0"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_pass_watch_and_block_classification_use_public_aggregate_fields_only() -> None:
    report = build_research_event_question_ambiguity_risk_report(
        (
            subject("pass-cluster"),
            subject(
                "watch-cluster",
                clause_clarity=Decimal("0.650000"),
                edge_case_coverage=Decimal("0.760000"),
                authority_traceability=Decimal("0.720000"),
                date_boundary_precision=Decimal("0.740000"),
                contradiction_pressure=Decimal("0.350000"),
            ),
            subject(
                "block-cluster",
                clause_clarity=Decimal("0.300000"),
                edge_case_coverage=Decimal("0.400000"),
                authority_traceability=Decimal("0.250000"),
                date_boundary_precision=Decimal("0.450000"),
                contradiction_pressure=Decimal("0.800000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityRiskConfig(),
    )

    assert tuple(row.public_event_bucket for row in report.rows) == (
        "block-cluster",
        "pass-cluster",
        "watch-cluster",
    )
    assert [row.status for row in report.rows] == ["block", "pass", "watch"]
    assert report.status == "block"
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")

    pass_row = report.rows[1]
    assert pass_row.ambiguity_risk_score == Decimal("0.080000")
    assert pass_row.reason_codes == ()

    watch_row = report.rows[2]
    assert watch_row.reason_codes == (
        "contradiction_pressure_watch",
        "imprecise_date_boundary_watch",
        "low_clause_clarity_watch",
    )

    block_row = report.rows[0]
    assert block_row.ambiguity_risk_score == Decimal("0.670000")
    assert block_row.reason_codes == (
        "contradiction_pressure_block",
        "imprecise_date_boundary_block",
        "low_clause_clarity_block",
        "thin_edge_case_coverage_block",
        "weak_authority_traceability_block",
    )
    assert not _contains_forbidden_public_surface(
        research_event_question_ambiguity_risk_payload(report),
    )


def test_multiple_watch_flags_do_not_escalate_to_block_without_block_threshold() -> None:
    report = build_research_event_question_ambiguity_risk_report(
        (
            subject(
                clause_clarity=Decimal("0.700000"),
                edge_case_coverage=Decimal("0.700000"),
                authority_traceability=Decimal("0.700000"),
                date_boundary_precision=Decimal("0.700000"),
                contradiction_pressure=Decimal("0.400000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventQuestionAmbiguityRiskConfig(),
    )

    row = report.rows[0]
    assert row.status == "watch"
    assert row.reason_codes == (
        "contradiction_pressure_watch",
        "imprecise_date_boundary_watch",
        "low_clause_clarity_watch",
        "thin_edge_case_coverage_watch",
        "weak_authority_traceability_watch",
    )


def test_payload_digest_is_deterministic_and_decimal_string_only() -> None:
    config = ResearchEventQuestionAmbiguityRiskConfig()
    subjects = (
        subject("z-cluster", clause_clarity=Decimal("0.650000")),
        subject("a-cluster", edge_case_coverage=Decimal("0.400000")),
        subject("m-cluster", contradiction_pressure=Decimal("0.800000")),
    )

    report = build_research_event_question_ambiguity_risk_report(
        subjects,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_question_ambiguity_risk_report(
        tuple(reversed(subjects)),
        generated_at=GENERATED_AT,
        config=config,
    )
    payload = research_event_question_ambiguity_risk_payload(report)
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
    assert payload["highest_contradiction_pressure"] == "0.800000"
    assert payload["rows"][0]["edge_case_coverage"] == "0.400000"
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
        research_event_question_ambiguity_risk_payload(tampered_payload)


def test_payload_validator_rejects_resigned_unsafe_dict_surfaces() -> None:
    payload = research_event_question_ambiguity_risk_payload(
        build_research_event_question_ambiguity_risk_report(
            (subject(),),
            generated_at=GENERATED_AT,
            config=ResearchEventQuestionAmbiguityRiskConfig(),
        ),
    )

    for key, value, expected_error in (
        ("status", "review", "status"),
        ("id", "raw-123", "unsafe public"),
        ("source_excerpt", "https://example.com/source", "unsafe public"),
        ("recommendation", "increase exposure", "unsafe public"),
        ("allocation_sizing", "none", "unsafe public"),
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[key] = value
        unsafe_payload["derived_payload_digest"] = _payload_digest(unsafe_payload)
        with pytest.raises(ValueError, match=expected_error):
            research_event_question_ambiguity_risk_payload(unsafe_payload)

    unsafe_row_status_payload = dict(payload)
    unsafe_row_status_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_row_status_payload["rows"][0]["status"] = "review"
    unsafe_row_status_payload["derived_payload_digest"] = _payload_digest(
        unsafe_row_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        research_event_question_ambiguity_risk_payload(unsafe_row_status_payload)

    unsafe_row_flag_payload = dict(payload)
    unsafe_row_flag_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_row_flag_payload["rows"][0]["readonly"] = False
    unsafe_row_flag_payload["derived_payload_digest"] = _payload_digest(
        unsafe_row_flag_payload,
    )
    with pytest.raises(ValueError, match="readonly"):
        research_event_question_ambiguity_risk_payload(unsafe_row_flag_payload)


def test_validation_rejects_non_decimal_numbers_datetimes_flags_and_public_leakage() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_question_ambiguity_risk_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchEventQuestionAmbiguityRiskConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_question_ambiguity_risk_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()),
            config=ResearchEventQuestionAmbiguityRiskConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_event_question_ambiguity_risk_report(
            (),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=ResearchEventQuestionAmbiguityRiskConfig(),
        )
    with pytest.raises(ValueError, match="clause_clarity must be a Decimal"):
        subject(clause_clarity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="edge_case_coverage must be a Decimal"):
        subject(edge_case_coverage=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_traceability must be between 0 and 1"):
        subject(authority_traceability=Decimal("1.000001"))
    with pytest.raises(ValueError, match="date_boundary_precision must be nonnegative"):
        subject(date_boundary_precision=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="contradiction_pressure must be between 0 and 1"):
        subject(contradiction_pressure=Decimal("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(
            ResearchEventQuestionAmbiguityRiskConfig(),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="unsafe public"):
        subject(public_event_bucket="contains-market-id")
    with pytest.raises(ValueError, match="raw question text"):
        subject(public_event_bucket="Will this resolve yes?")

    payload = research_event_question_ambiguity_risk_payload(
        build_research_event_question_ambiguity_risk_report(
            (subject(),),
            generated_at=GENERATED_AT,
            config=ResearchEventQuestionAmbiguityRiskConfig(),
        ),
    )
    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "private-market"
    with pytest.raises(ValueError, match="unsafe public"):
        research_event_question_ambiguity_risk_payload(unsafe_payload)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchEventQuestionAmbiguityRiskConfig()
    input_row = subject()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.public_event_bucket = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventQuestionAmbiguityRiskConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class SubjectSubclass(ResearchEventQuestionAmbiguityRiskSubject):
            pass


def test_static_module_is_report_only_and_has_no_forbidden_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_question_ambiguity_risk_report.py",
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
        "ord" + "er",
        "notional",
        "position",
        "sizing",
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


def _payload_digest(payload: dict[str, object]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_payload_digest"
    }
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contains_forbidden_public_surface(value: object) -> bool:
    forbidden_fragments = (
        "_id",
        "id_",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "raw_question",
        "question_text",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "ord" + "er",
        "trad" + "e",
        "live",
    )
    if isinstance(value, dict):
        return any(
            any(fragment in key.lower() for fragment in forbidden_fragments)
            or _contains_forbidden_public_surface(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_public_surface(item) for item in value)
    if isinstance(value, str):
        return any(fragment in value.lower() for fragment in forbidden_fragments)
    return False
