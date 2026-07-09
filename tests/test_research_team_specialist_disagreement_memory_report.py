from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_team_specialist_disagreement_memory_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION,
    SPECIALIST_DISAGREEMENT_MEMORY_STATUSES,
    ResearchTeamSpecialistDisagreementMemoryConfig,
    ResearchTeamSpecialistDisagreementMemoryObservation,
    ResearchTeamSpecialistDisagreementMemoryReasonCodeCount,
    ResearchTeamSpecialistDisagreementMemoryReport,
    ResearchTeamSpecialistDisagreementMemoryRow,
    build_research_team_specialist_disagreement_memory_report,
    research_team_specialist_disagreement_memory_report_digest,
    research_team_specialist_disagreement_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_disagreement_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    domain_label: str = "finance.crypto",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    disagreement_case_count: Decimal = d("10.000000"),
    severe_disagreement_count: Decimal = d("10.000000"),
    severe_disagreement_captured_count: Decimal = d("10.000000"),
    evidence_required_count: Decimal = d("10.000000"),
    evidence_documented_count: Decimal = d("9.000000"),
    resolution_due_count: Decimal = d("10.000000"),
    resolution_followed_up_count: Decimal = d("9.000000"),
    calibration_case_count: Decimal = d("10.000000"),
    calibration_moved_count: Decimal = d("8.000000"),
    stale_memory_item_count: Decimal = d("10.000000"),
    stale_memory_handled_count: Decimal = d("9.000000"),
    peer_review_latency_seconds: Decimal = d("43200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistDisagreementMemoryObservation:
    return ResearchTeamSpecialistDisagreementMemoryObservation(
        domain_label=domain_label,
        observed_at=observed_at,
        disagreement_case_count=disagreement_case_count,
        severe_disagreement_count=severe_disagreement_count,
        severe_disagreement_captured_count=severe_disagreement_captured_count,
        evidence_required_count=evidence_required_count,
        evidence_documented_count=evidence_documented_count,
        resolution_due_count=resolution_due_count,
        resolution_followed_up_count=resolution_followed_up_count,
        calibration_case_count=calibration_case_count,
        calibration_moved_count=calibration_moved_count,
        stale_memory_item_count=stale_memory_item_count,
        stale_memory_handled_count=stale_memory_handled_count,
        peer_review_latency_seconds=peer_review_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistDisagreementMemoryObservation,
    config: ResearchTeamSpecialistDisagreementMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistDisagreementMemoryReport:
    return build_research_team_specialist_disagreement_memory_report(
        items,
        config=config or ResearchTeamSpecialistDisagreementMemoryConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_observations_block_as_readonly_report_only_disagreement_memory() -> None:
    memory_report = report()

    assert type(memory_report) is ResearchTeamSpecialistDisagreementMemoryReport
    assert SPECIALIST_DISAGREEMENT_MEMORY_STATUSES == ("pass", "watch", "block")
    assert memory_report.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_DISAGREEMENT_MEMORY_REPORT_CONFIG_VERSION
    )
    assert memory_report.status == "block"
    assert memory_report.next_review_step == (
        "block_specialist_disagreement_memory_until_review"
    )
    assert memory_report.observation_count == d("0.000000")
    assert memory_report.domain_count == d("0.000000")
    assert memory_report.disagreement_case_count == d("0.000000")
    assert memory_report.severe_disagreement_count == d("0.000000")
    assert memory_report.severe_disagreement_captured_count == d("0.000000")
    assert memory_report.evidence_required_count == d("0.000000")
    assert memory_report.evidence_documented_count == d("0.000000")
    assert memory_report.resolution_due_count == d("0.000000")
    assert memory_report.resolution_followed_up_count == d("0.000000")
    assert memory_report.calibration_case_count == d("0.000000")
    assert memory_report.calibration_moved_count == d("0.000000")
    assert memory_report.stale_memory_item_count == d("0.000000")
    assert memory_report.stale_memory_handled_count == d("0.000000")
    assert memory_report.peer_review_latency_seconds == d("0.000000")
    assert memory_report.pass_count == d("0.000000")
    assert memory_report.watch_count == d("0.000000")
    assert memory_report.block_count == d("0.000000")
    assert memory_report.severity_capture_ratio == d("1.000000")
    assert memory_report.evidence_coverage_ratio == d("1.000000")
    assert memory_report.resolution_follow_up_ratio == d("1.000000")
    assert memory_report.calibration_movement_ratio == d("1.000000")
    assert memory_report.stale_memory_handling_ratio == d("1.000000")
    assert memory_report.peer_review_timeliness_score == d("0.000000")
    assert memory_report.disagreement_memory_score == d("0.000000")
    assert memory_report.rows == ()
    assert memory_report.reason_codes == (
        "specialist_disagreement_memory_no_observations",
    )
    assert memory_report.reason_code_counts == (
        ResearchTeamSpecialistDisagreementMemoryReasonCodeCount(
            reason_code="specialist_disagreement_memory_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True
    assert len(memory_report.derived_validation_digest) == 64


def test_scores_disagreement_memory_capture_by_domain_from_all_components() -> None:
    memory_report = report(
        observation(),
        observation(
            "policy.regulation",
            severe_disagreement_captured_count=d("7.000000"),
            evidence_documented_count=d("7.000000"),
            resolution_followed_up_count=d("7.000000"),
            calibration_moved_count=d("6.000000"),
            stale_memory_handled_count=d("7.000000"),
            peer_review_latency_seconds=d("172800.000000"),
        ),
        observation(
            "sports.soccer",
            severe_disagreement_captured_count=d("4.000000"),
            evidence_documented_count=d("4.000000"),
            resolution_followed_up_count=d("4.000000"),
            calibration_moved_count=d("3.000000"),
            stale_memory_handled_count=d("2.000000"),
            peer_review_latency_seconds=d("345600.000000"),
        ),
    )

    assert memory_report.status == "block"
    assert memory_report.next_review_step == (
        "block_specialist_disagreement_memory_until_review"
    )
    assert memory_report.observation_count == d("3.000000")
    assert memory_report.domain_count == d("3.000000")
    assert memory_report.disagreement_case_count == d("30.000000")
    assert memory_report.severe_disagreement_count == d("30.000000")
    assert memory_report.severe_disagreement_captured_count == d("21.000000")
    assert memory_report.evidence_required_count == d("30.000000")
    assert memory_report.evidence_documented_count == d("20.000000")
    assert memory_report.resolution_due_count == d("30.000000")
    assert memory_report.resolution_followed_up_count == d("20.000000")
    assert memory_report.calibration_case_count == d("30.000000")
    assert memory_report.calibration_moved_count == d("17.000000")
    assert memory_report.stale_memory_item_count == d("30.000000")
    assert memory_report.stale_memory_handled_count == d("18.000000")
    assert memory_report.peer_review_latency_seconds == d("187200.000000")
    assert memory_report.pass_count == d("1.000000")
    assert memory_report.watch_count == d("1.000000")
    assert memory_report.block_count == d("1.000000")
    assert memory_report.severity_capture_ratio == d("0.700000")
    assert memory_report.evidence_coverage_ratio == d("0.666667")
    assert memory_report.resolution_follow_up_ratio == d("0.666667")
    assert memory_report.calibration_movement_ratio == d("0.566667")
    assert memory_report.stale_memory_handling_ratio == d("0.600000")
    assert memory_report.peer_review_timeliness_score == d("0.500000")
    assert memory_report.disagreement_memory_score == d("0.616667")
    assert memory_report.reason_codes == (
        "specialist_disagreement_memory_block_present",
        "specialist_disagreement_memory_watch_present",
        "disagreement_severity_capture_gap_present",
        "evidence_coverage_gap_present",
        "resolution_follow_up_gap_present",
        "calibration_movement_gap_present",
        "stale_memory_handling_gap_present",
        "peer_review_latency_gap_present",
    )

    assert tuple((row.domain_label, row.status) for row in memory_report.rows) == (
        ("sports.soccer", "block"),
        ("policy.regulation", "watch"),
        ("finance.crypto", "pass"),
    )
    blocked, watched, passed = memory_report.rows
    assert blocked.snapshot_age_seconds == d("3600.000000")
    assert blocked.severity_capture_ratio == d("0.400000")
    assert blocked.evidence_coverage_ratio == d("0.400000")
    assert blocked.resolution_follow_up_ratio == d("0.400000")
    assert blocked.calibration_movement_ratio == d("0.300000")
    assert blocked.stale_memory_handling_ratio == d("0.200000")
    assert blocked.peer_review_timeliness_score == d("0.000000")
    assert blocked.disagreement_memory_score == d("0.283333")
    assert blocked.reason_codes == (
        "disagreement_severity_capture_block",
        "evidence_coverage_block",
        "resolution_follow_up_block",
        "calibration_movement_block",
        "stale_memory_handling_block",
        "peer_review_latency_block",
    )
    assert watched.disagreement_memory_score == d("0.650000")
    assert watched.reason_codes == (
        "disagreement_severity_capture_watch",
        "evidence_coverage_watch",
        "resolution_follow_up_watch",
        "calibration_movement_watch",
        "stale_memory_handling_watch",
        "peer_review_latency_watch",
    )
    assert passed.disagreement_memory_score == d("0.916667")
    assert passed.reason_codes == ("specialist_disagreement_memory_clear",)

    assert memory_report.reason_code_counts[0].reason_code == (
        "disagreement_severity_capture_block"
    )
    assert memory_report.reason_code_counts[0].count == d("1.000000")
    assert memory_report.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    first = report(
        observation("policy.regulation"),
        observation("finance.crypto"),
    )
    second = report(
        observation("finance.crypto"),
        observation("policy.regulation"),
    )

    first_payload = research_team_specialist_disagreement_memory_report_payload(first)
    second_payload = research_team_specialist_disagreement_memory_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_disagreement_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first.payload == first_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["rows"][0]["disagreement_memory_score"] == "0.916667"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.916667"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_disagreement_memory_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_disagreement_memory_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "domain_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_disagreement_memory_report_payload(unsafe_value)


def test_payload_rejects_signed_noncanonical_shape_and_status_values() -> None:
    payload = research_team_specialist_disagreement_memory_report_payload(
        report(observation()),
    )

    extra_field_payload = {**payload, "diagnostic_note": "safe"}
    extra_field_payload["derived_validation_digest"] = canonical_digest(
        extra_field_payload,
    )
    with pytest.raises(ValueError, match="unexpected public payload keys"):
        research_team_specialist_disagreement_memory_report_payload(extra_field_payload)

    invalid_report_status = {**payload, "status": "ready"}
    invalid_report_status["derived_validation_digest"] = canonical_digest(
        invalid_report_status,
    )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        research_team_specialist_disagreement_memory_report_payload(
            invalid_report_status,
        )

    invalid_row = {**payload["rows"][0], "status": "ready"}
    invalid_row_status = {**payload, "rows": [invalid_row]}
    invalid_row_status["derived_validation_digest"] = canonical_digest(
        invalid_row_status,
    )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        research_team_specialist_disagreement_memory_report_payload(invalid_row_status)


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    memory_report = report(observation())

    assert memory_report.generated_at == GENERATED_AT
    assert memory_report.rows[0].observed_at == GENERATED_AT - timedelta(hours=1)
    assert memory_report.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in memory_report.rows)

    for public_type in (
        ResearchTeamSpecialistDisagreementMemoryConfig,
        ResearchTeamSpecialistDisagreementMemoryObservation,
        ResearchTeamSpecialistDisagreementMemoryRow,
        ResearchTeamSpecialistDisagreementMemoryReasonCodeCount,
        ResearchTeamSpecialistDisagreementMemoryReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchTeamSpecialistDisagreementMemoryConfig(),
        observation(),
        memory_report.rows[0],
        memory_report.reason_code_counts[0],
        memory_report,
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True

    with pytest.raises(FrozenInstanceError):
        memory_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="disagreement_case_count must be exactly Decimal"):
        observation(disagreement_case_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="disagreement_case_count must be positive"):
        observation(disagreement_case_count=d("0.000000"))
    with pytest.raises(ValueError, match="severe_disagreement_captured_count"):
        observation(severe_disagreement_captured_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="domain_label values must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="min_watch_severity_capture_ratio"):
        ResearchTeamSpecialistDisagreementMemoryConfig(
            min_pass_severity_capture_ratio=d("0.700000"),
            min_watch_severity_capture_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(memory_report.rows[0], status="ready")
    with pytest.raises(ValueError, match="severity_capture_ratio must match row counts"):
        replace(memory_report.rows[0], severity_capture_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(memory_report, derived_validation_digest="0" * 64)


def test_module_scope_is_static_report_only_public_safe_without_action_surfaces() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "requests",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {"connect", "execute", "open", "request", "write_bytes", "write_text"}
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


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"payload contains raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_no_forbidden_public_payload_surface(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
    ):
        assert forbidden not in encoded


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_ratio")
        or name.endswith("_score")
        or name.endswith("_seconds")
    )
