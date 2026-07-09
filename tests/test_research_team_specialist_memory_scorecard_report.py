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

from polymarket_alpha_lab.research_team_specialist_memory_scorecard_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION,
    SPECIALIST_MEMORY_SCORECARD_STATUSES,
    ResearchTeamSpecialistMemoryScorecardConfig,
    ResearchTeamSpecialistMemoryScorecardObservation,
    ResearchTeamSpecialistMemoryScorecardReasonCodeCount,
    ResearchTeamSpecialistMemoryScorecardReport,
    ResearchTeamSpecialistMemoryScorecardRow,
    build_research_team_specialist_memory_scorecard_report,
    research_team_specialist_memory_scorecard_report_digest,
    research_team_specialist_memory_scorecard_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_scorecard_report.py"
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
    specialist_count: Decimal = d("2.000000"),
    memory_item_count: Decimal = d("10.000000"),
    fresh_memory_item_count: Decimal = d("9.000000"),
    calibration_case_count: Decimal = d("10.000000"),
    calibration_evidence_count: Decimal = d("8.000000"),
    caveat_count: Decimal = d("10.000000"),
    unresolved_caveat_count: Decimal = d("0.000000"),
    correction_due_count: Decimal = d("10.000000"),
    correction_completed_count: Decimal = d("9.000000"),
    active_assignment_count: Decimal = d("5.000000"),
    assignment_capacity_count: Decimal = d("10.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryScorecardObservation:
    return ResearchTeamSpecialistMemoryScorecardObservation(
        domain_label=domain_label,
        observed_at=observed_at,
        specialist_count=specialist_count,
        memory_item_count=memory_item_count,
        fresh_memory_item_count=fresh_memory_item_count,
        calibration_case_count=calibration_case_count,
        calibration_evidence_count=calibration_evidence_count,
        caveat_count=caveat_count,
        unresolved_caveat_count=unresolved_caveat_count,
        correction_due_count=correction_due_count,
        correction_completed_count=correction_completed_count,
        active_assignment_count=active_assignment_count,
        assignment_capacity_count=assignment_capacity_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistMemoryScorecardObservation,
    config: ResearchTeamSpecialistMemoryScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryScorecardReport:
    return build_research_team_specialist_memory_scorecard_report(
        items,
        config=config or ResearchTeamSpecialistMemoryScorecardConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def redigest(payload: dict[str, Any]) -> dict[str, Any]:
    redigested = json.loads(json.dumps(payload))
    redigested["derived_validation_digest"] = canonical_digest(redigested)
    return redigested


def test_empty_observations_block_as_readonly_report_only_scorecard() -> None:
    scorecard = report()

    assert type(scorecard) is ResearchTeamSpecialistMemoryScorecardReport
    assert SPECIALIST_MEMORY_SCORECARD_STATUSES == ("pass", "watch", "block")
    assert scorecard.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
    )
    assert scorecard.status == "block"
    assert scorecard.next_review_step == "block_specialist_memory_until_quality_review"
    assert scorecard.observation_count == d("0.000000")
    assert scorecard.domain_count == d("0.000000")
    assert scorecard.specialist_count == d("0.000000")
    assert scorecard.memory_item_count == d("0.000000")
    assert scorecard.fresh_memory_item_count == d("0.000000")
    assert scorecard.calibration_case_count == d("0.000000")
    assert scorecard.calibration_evidence_count == d("0.000000")
    assert scorecard.caveat_count == d("0.000000")
    assert scorecard.unresolved_caveat_count == d("0.000000")
    assert scorecard.correction_due_count == d("0.000000")
    assert scorecard.correction_completed_count == d("0.000000")
    assert scorecard.active_assignment_count == d("0.000000")
    assert scorecard.assignment_capacity_count == d("0.000000")
    assert scorecard.pass_count == d("0.000000")
    assert scorecard.watch_count == d("0.000000")
    assert scorecard.block_count == d("0.000000")
    assert scorecard.freshness_ratio == d("0.000000")
    assert scorecard.calibration_evidence_ratio == d("0.000000")
    assert scorecard.unresolved_caveat_ratio == d("0.000000")
    assert scorecard.correction_follow_through_ratio == d("0.000000")
    assert scorecard.workload_pressure_ratio == d("0.000000")
    assert scorecard.memory_quality_score == d("0.000000")
    assert scorecard.rows == ()
    assert scorecard.reason_codes == ("specialist_memory_scorecard_no_observations",)
    assert scorecard.reason_code_counts == (
        ResearchTeamSpecialistMemoryScorecardReasonCodeCount(
            reason_code="specialist_memory_scorecard_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True
    assert len(scorecard.derived_validation_digest) == 64


def test_scores_specialist_memory_quality_by_domain_from_all_components() -> None:
    scorecard = report(
        observation(),
        observation(
            "policy.regulation",
            specialist_count=d("3.000000"),
            fresh_memory_item_count=d("6.000000"),
            calibration_evidence_count=d("6.000000"),
            unresolved_caveat_count=d("2.000000"),
            correction_completed_count=d("7.000000"),
            active_assignment_count=d("9.000000"),
        ),
        observation(
            "sports.soccer",
            specialist_count=d("1.000000"),
            fresh_memory_item_count=d("4.000000"),
            calibration_evidence_count=d("4.000000"),
            unresolved_caveat_count=d("4.000000"),
            correction_completed_count=d("5.000000"),
            active_assignment_count=d("12.000000"),
        ),
    )

    assert scorecard.status == "block"
    assert scorecard.next_review_step == "block_specialist_memory_until_quality_review"
    assert scorecard.observation_count == d("3.000000")
    assert scorecard.domain_count == d("3.000000")
    assert scorecard.specialist_count == d("6.000000")
    assert scorecard.memory_item_count == d("30.000000")
    assert scorecard.fresh_memory_item_count == d("19.000000")
    assert scorecard.calibration_case_count == d("30.000000")
    assert scorecard.calibration_evidence_count == d("18.000000")
    assert scorecard.caveat_count == d("30.000000")
    assert scorecard.unresolved_caveat_count == d("6.000000")
    assert scorecard.correction_due_count == d("30.000000")
    assert scorecard.correction_completed_count == d("21.000000")
    assert scorecard.active_assignment_count == d("26.000000")
    assert scorecard.assignment_capacity_count == d("30.000000")
    assert scorecard.pass_count == d("1.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.block_count == d("1.000000")
    assert scorecard.freshness_ratio == d("0.633333")
    assert scorecard.calibration_evidence_ratio == d("0.600000")
    assert scorecard.unresolved_caveat_ratio == d("0.200000")
    assert scorecard.correction_follow_through_ratio == d("0.700000")
    assert scorecard.workload_pressure_ratio == d("0.866667")
    assert scorecard.memory_quality_score == d("0.573333")
    assert scorecard.reason_codes == (
        "specialist_memory_scorecard_block_present",
        "specialist_memory_scorecard_watch_present",
        "freshness_gap_present",
        "calibration_evidence_gap_present",
        "unresolved_caveats_present",
        "correction_follow_through_gap_present",
        "workload_pressure_present",
    )

    assert tuple((row.domain_label, row.status) for row in scorecard.rows) == (
        ("sports.soccer", "block"),
        ("policy.regulation", "watch"),
        ("finance.crypto", "pass"),
    )
    blocked, watched, passed = scorecard.rows
    assert blocked.snapshot_age_seconds == d("3600.000000")
    assert blocked.freshness_ratio == d("0.400000")
    assert blocked.calibration_evidence_ratio == d("0.400000")
    assert blocked.unresolved_caveat_ratio == d("0.400000")
    assert blocked.correction_follow_through_ratio == d("0.500000")
    assert blocked.workload_pressure_ratio == d("1.000000")
    assert blocked.memory_quality_score == d("0.380000")
    assert blocked.reason_codes == (
        "freshness_block",
        "calibration_evidence_block",
        "unresolved_caveats_block",
        "correction_follow_through_block",
        "workload_pressure_block",
    )
    assert watched.memory_quality_score == d("0.560000")
    assert watched.reason_codes == (
        "freshness_watch",
        "calibration_evidence_watch",
        "unresolved_caveats_watch",
        "correction_follow_through_watch",
        "workload_pressure_watch",
    )
    assert passed.memory_quality_score == d("0.820000")
    assert passed.reason_codes == ("specialist_memory_scorecard_clear",)

    assert scorecard.reason_code_counts[0].reason_code == "freshness_block"
    assert scorecard.reason_code_counts[0].count == d("1.000000")
    assert scorecard.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    first = report(
        observation("policy.regulation"),
        observation("finance.crypto"),
    )
    second = report(
        observation("finance.crypto"),
        observation("policy.regulation"),
    )

    first_payload = research_team_specialist_memory_scorecard_report_payload(first)
    second_payload = research_team_specialist_memory_scorecard_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_memory_scorecard_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first.payload == first_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["rows"][0]["memory_quality_score"] == "0.820000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.820000"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_scorecard_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_scorecard_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "domain_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_scorecard_report_payload(unsafe_value)

    invalid_status = json.loads(json.dumps(first_payload))
    invalid_status["status"] = "ready"
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        research_team_specialist_memory_scorecard_report_payload(redigest(invalid_status))

    missing_flags = json.loads(json.dumps(first_payload))
    for flag in ("paper_only", "report_only", "readonly"):
        missing_flags.pop(flag)
    with pytest.raises(ValueError, match="payload keys must match report schema"):
        research_team_specialist_memory_scorecard_report_payload(redigest(missing_flags))

    unexpected_identifier = json.loads(json.dumps(first_payload))
    unexpected_identifier["opaque_identifier"] = "7f4d0d3b-5b66-4e30-8f14-23f52c4dc898"
    with pytest.raises(ValueError, match="payload keys must match report schema"):
        research_team_specialist_memory_scorecard_report_payload(
            redigest(unexpected_identifier),
        )

    transport_reference = json.loads(json.dumps(first_payload))
    transport_reference["rows"][0]["domain_label"] = "https://example.com/feed"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_scorecard_report_payload(
            redigest(transport_reference),
        )


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    scorecard = report(observation())

    assert scorecard.generated_at == GENERATED_AT
    assert scorecard.rows[0].observed_at == GENERATED_AT - timedelta(hours=1)
    assert scorecard.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in scorecard.rows)

    for public_type in (
        ResearchTeamSpecialistMemoryScorecardConfig,
        ResearchTeamSpecialistMemoryScorecardObservation,
        ResearchTeamSpecialistMemoryScorecardRow,
        ResearchTeamSpecialistMemoryScorecardReasonCodeCount,
        ResearchTeamSpecialistMemoryScorecardReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchTeamSpecialistMemoryScorecardConfig(),
        observation(),
        scorecard.rows[0],
        scorecard.reason_code_counts[0],
        scorecard,
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        scorecard.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="memory_item_count must be exactly Decimal"):
        observation(memory_item_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="memory_item_count must be positive"):
        observation(memory_item_count=d("0.000000"))
    with pytest.raises(ValueError, match="fresh_memory_item_count must not exceed"):
        observation(fresh_memory_item_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="domain_label values must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="min_watch_freshness_ratio"):
        ResearchTeamSpecialistMemoryScorecardConfig(
            min_pass_freshness_ratio=d("0.700000"),
            min_watch_freshness_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(scorecard.rows[0], status="ready")
    with pytest.raises(ValueError, match="freshness_ratio must match row counts"):
        replace(scorecard.rows[0], freshness_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard, derived_validation_digest="0" * 64)


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
        "recommend",
        "recommendation",
        "position sizing",
        "sizing",
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
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_ratio")
        or name.endswith("_score")
        or name.endswith("_seconds")
    )
