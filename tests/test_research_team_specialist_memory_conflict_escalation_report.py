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

from polymarket_alpha_lab.research_team_specialist_memory_conflict_escalation_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION,
    SPECIALIST_MEMORY_CONFLICT_ESCALATION_STATUSES,
    ResearchTeamSpecialistMemoryConflictEscalationConfig,
    ResearchTeamSpecialistMemoryConflictEscalationDomainSummary,
    ResearchTeamSpecialistMemoryConflictEscalationObservation,
    ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount,
    ResearchTeamSpecialistMemoryConflictEscalationReport,
    ResearchTeamSpecialistMemoryConflictEscalationRow,
    build_research_team_specialist_memory_conflict_escalation_report,
    research_team_specialist_memory_conflict_escalation_report_digest,
    research_team_specialist_memory_conflict_escalation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_conflict_escalation_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    domain_label: str = "finance.crypto",
    specialist_label: str = "crypto_memory",
    memory_bucket_label: str = "resolution_boundary",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    reviewed_memory_count: Decimal = d("10.000000"),
    open_conflict_count: Decimal = d("0.000000"),
    reopened_conflict_count: Decimal = d("0.000000"),
    peer_review_count: Decimal = d("10.000000"),
    peer_agreement_count: Decimal = d("9.000000"),
    evidence_check_count: Decimal = d("10.000000"),
    evidence_aligned_count: Decimal = d("9.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryConflictEscalationObservation:
    return ResearchTeamSpecialistMemoryConflictEscalationObservation(
        domain_label=domain_label,
        specialist_label=specialist_label,
        memory_bucket_label=memory_bucket_label,
        observed_at=observed_at,
        reviewed_memory_count=reviewed_memory_count,
        open_conflict_count=open_conflict_count,
        reopened_conflict_count=reopened_conflict_count,
        peer_review_count=peer_review_count,
        peer_agreement_count=peer_agreement_count,
        evidence_check_count=evidence_check_count,
        evidence_aligned_count=evidence_aligned_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistMemoryConflictEscalationObservation,
    config: ResearchTeamSpecialistMemoryConflictEscalationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryConflictEscalationReport:
    return build_research_team_specialist_memory_conflict_escalation_report(
        items,
        config=config or ResearchTeamSpecialistMemoryConflictEscalationConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_observations_block_as_readonly_report_only_conflict_gap() -> None:
    escalation = report()

    assert type(escalation) is ResearchTeamSpecialistMemoryConflictEscalationReport
    assert SPECIALIST_MEMORY_CONFLICT_ESCALATION_STATUSES == ("pass", "watch", "block")
    assert escalation.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_CONFLICT_ESCALATION_REPORT_CONFIG_VERSION
    )
    assert escalation.status == "block"
    assert escalation.next_review_step == "block_memory_reuse_until_conflict_review"
    assert escalation.observation_count == d("0.000000")
    assert escalation.domain_count == d("0.000000")
    assert escalation.specialist_count == d("0.000000")
    assert escalation.reviewed_memory_count == d("0.000000")
    assert escalation.open_conflict_count == d("0.000000")
    assert escalation.reopened_conflict_count == d("0.000000")
    assert escalation.pass_count == d("0.000000")
    assert escalation.watch_count == d("0.000000")
    assert escalation.block_count == d("0.000000")
    assert escalation.open_conflict_ratio == d("0.000000")
    assert escalation.reopened_conflict_ratio == d("0.000000")
    assert escalation.peer_agreement_ratio == d("0.000000")
    assert escalation.evidence_alignment_ratio == d("0.000000")
    assert escalation.escalation_score == d("0.000000")
    assert escalation.rows == ()
    assert escalation.domain_summaries == ()
    assert escalation.reason_codes == (
        "specialist_memory_conflict_escalation_no_observations",
    )
    assert escalation.reason_code_counts == (
        ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount(
            reason_code="specialist_memory_conflict_escalation_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert escalation.paper_only is True
    assert escalation.report_only is True
    assert escalation.readonly is True
    assert len(escalation.derived_validation_digest) == 64


def test_report_scores_specialist_memory_conflicts_into_escalation_rows() -> None:
    escalation = report(
        observation(),
        observation(
            "policy.regulation",
            "policy_memory",
            "review_boundary",
            open_conflict_count=d("2.000000"),
            reopened_conflict_count=d("1.000000"),
            peer_agreement_count=d("7.000000"),
            evidence_aligned_count=d("7.000000"),
        ),
        observation(
            "sports.soccer",
            "soccer_memory",
            "injury_boundary",
            open_conflict_count=d("4.000000"),
            reopened_conflict_count=d("2.000000"),
            peer_agreement_count=d("5.000000"),
            evidence_aligned_count=d("5.000000"),
        ),
    )

    assert escalation.status == "block"
    assert escalation.next_review_step == "block_memory_reuse_until_conflict_review"
    assert escalation.observation_count == d("3.000000")
    assert escalation.domain_count == d("3.000000")
    assert escalation.specialist_count == d("3.000000")
    assert escalation.reviewed_memory_count == d("30.000000")
    assert escalation.open_conflict_count == d("6.000000")
    assert escalation.reopened_conflict_count == d("3.000000")
    assert escalation.peer_review_count == d("30.000000")
    assert escalation.peer_agreement_count == d("21.000000")
    assert escalation.evidence_check_count == d("30.000000")
    assert escalation.evidence_aligned_count == d("21.000000")
    assert escalation.pass_count == d("1.000000")
    assert escalation.watch_count == d("1.000000")
    assert escalation.block_count == d("1.000000")
    assert escalation.open_conflict_ratio == d("0.200000")
    assert escalation.reopened_conflict_ratio == d("0.100000")
    assert escalation.peer_agreement_ratio == d("0.700000")
    assert escalation.evidence_alignment_ratio == d("0.700000")
    assert escalation.escalation_score == d("0.225000")
    assert escalation.reason_codes == (
        "specialist_memory_conflict_escalation_block_present",
        "specialist_memory_conflict_escalation_watch_present",
        "open_memory_conflict_present",
        "reopened_memory_conflict_present",
        "peer_agreement_gap_present",
        "evidence_alignment_gap_present",
    )

    assert tuple(
        (row.domain_label, row.specialist_label, row.memory_bucket_label, row.status)
        for row in escalation.rows
    ) == (
        ("sports.soccer", "soccer_memory", "injury_boundary", "block"),
        ("policy.regulation", "policy_memory", "review_boundary", "watch"),
        ("finance.crypto", "crypto_memory", "resolution_boundary", "pass"),
    )
    blocked, watched, passed = escalation.rows
    assert blocked.open_conflict_ratio == d("0.400000")
    assert blocked.reopened_conflict_ratio == d("0.200000")
    assert blocked.peer_agreement_ratio == d("0.500000")
    assert blocked.evidence_alignment_ratio == d("0.500000")
    assert blocked.escalation_score == d("0.400000")
    assert blocked.reason_codes == (
        "open_memory_conflict_block",
        "reopened_memory_conflict_block",
        "peer_agreement_block",
        "evidence_alignment_block",
    )
    assert watched.reason_codes == (
        "open_memory_conflict_watch",
        "reopened_memory_conflict_watch",
        "peer_agreement_watch",
        "evidence_alignment_watch",
    )
    assert watched.escalation_score == d("0.225000")
    assert passed.reason_codes == ("specialist_memory_conflict_escalation_clear",)

    assert tuple(summary.domain_label for summary in escalation.domain_summaries) == (
        "finance.crypto",
        "policy.regulation",
        "sports.soccer",
    )
    assert escalation.domain_summaries[0] == ResearchTeamSpecialistMemoryConflictEscalationDomainSummary(
        domain_label="finance.crypto",
        specialist_count=d("1.000000"),
        reviewed_memory_count=d("10.000000"),
        open_conflict_count=d("0.000000"),
        reopened_conflict_count=d("0.000000"),
        open_conflict_ratio=d("0.000000"),
        reopened_conflict_ratio=d("0.000000"),
        worst_status="pass",
    )
    assert escalation.reason_code_counts[0].reason_code == "open_memory_conflict_block"
    assert escalation.reason_code_counts[0].count == d("1.000000")
    assert escalation.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    first = report(
        observation("policy.regulation", "policy_memory", "review_boundary"),
        observation("finance.crypto", "crypto_memory", "resolution_boundary"),
    )
    second = report(
        observation("finance.crypto", "crypto_memory", "resolution_boundary"),
        observation("policy.regulation", "policy_memory", "review_boundary"),
    )

    first_payload = research_team_specialist_memory_conflict_escalation_report_payload(first)
    second_payload = research_team_specialist_memory_conflict_escalation_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_memory_conflict_escalation_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["rows"][0]["escalation_score"] == "0.050000"
    assert first_payload["domain_summaries"][0]["domain_label"] == "finance.crypto"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.050000"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_conflict_escalation_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_conflict_escalation_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "specialist_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_conflict_escalation_report_payload(unsafe_value)


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    escalation = report(observation())

    assert escalation.generated_at == GENERATED_AT
    assert escalation.rows[0].observed_at == GENERATED_AT - timedelta(hours=1)
    assert escalation.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in escalation.rows)

    for public_type in (
        ResearchTeamSpecialistMemoryConflictEscalationConfig,
        ResearchTeamSpecialistMemoryConflictEscalationObservation,
        ResearchTeamSpecialistMemoryConflictEscalationRow,
        ResearchTeamSpecialistMemoryConflictEscalationDomainSummary,
        ResearchTeamSpecialistMemoryConflictEscalationReasonCodeCount,
        ResearchTeamSpecialistMemoryConflictEscalationReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchTeamSpecialistMemoryConflictEscalationConfig(),
        observation(),
        escalation.rows[0],
        escalation.domain_summaries[0],
        escalation.reason_code_counts[0],
        escalation,
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        escalation.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="reviewed_memory_count must be exactly Decimal"):
        observation(reviewed_memory_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="reviewed_memory_count must be positive"):
        observation(reviewed_memory_count=d("0.000000"))
    with pytest.raises(ValueError, match="open_conflict_count must not exceed"):
        observation(open_conflict_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="triples must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="max_pass_open_conflict_ratio"):
        ResearchTeamSpecialistMemoryConflictEscalationConfig(
            max_pass_open_conflict_ratio=d("0.300000"),
            max_watch_open_conflict_ratio=d("0.200000"),
        )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(escalation.rows[0], status="ready")
    with pytest.raises(ValueError, match="open_conflict_ratio must match row counts"):
        replace(escalation.rows[0], open_conflict_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(escalation, derived_validation_digest="0" * 64)


def test_builder_rejects_falsey_non_config_values() -> None:
    with pytest.raises(
        ValueError,
        match="config must be exactly ResearchTeamSpecialistMemoryConflictEscalationConfig",
    ):
        build_research_team_specialist_memory_conflict_escalation_report(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_payload_requires_a_signed_report_or_signed_report_dict() -> None:
    escalation = report(observation())
    payload = research_team_specialist_memory_conflict_escalation_report_payload(escalation)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")

    with pytest.raises(ValueError, match="derived_validation_digest must be present"):
        research_team_specialist_memory_conflict_escalation_report_payload(unsigned_payload)
    with pytest.raises(
        ValueError,
        match="value must be a ResearchTeamSpecialistMemoryConflictEscalationReport or dict",
    ):
        research_team_specialist_memory_conflict_escalation_report_payload(
            ResearchTeamSpecialistMemoryConflictEscalationConfig(),
        )
    with pytest.raises(ValueError, match="derived_validation_digest must be present"):
        research_team_specialist_memory_conflict_escalation_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    signed_arbitrary_payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    signed_arbitrary_payload["derived_validation_digest"] = canonical_digest(
        signed_arbitrary_payload,
    )
    with pytest.raises(ValueError, match="payload must match report fields"):
        research_team_specialist_memory_conflict_escalation_report_payload(
            signed_arbitrary_payload,
        )

    invalid_status_payload = dict(payload)
    invalid_status_payload["status"] = "ready"
    invalid_status_payload["derived_validation_digest"] = canonical_digest(
        invalid_status_payload,
    )
    with pytest.raises(ValueError, match="payload status must be one of pass, watch, block"):
        research_team_specialist_memory_conflict_escalation_report_payload(
            invalid_status_payload,
        )


def test_report_rejects_unsupported_config_version_when_recomputing_digest() -> None:
    escalation = report(observation())

    with pytest.raises(ValueError, match="config_version must be the supported config version"):
        replace(
            escalation,
            config_version="unsupported",
            derived_validation_digest="",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("domain_label", "123456"),
        ("specialist_label", "0x1234567890abcdef1234567890abcdef12345678"),
        ("memory_bucket_label", "will-btc-hit-100k"),
    ),
)
def test_public_labels_reject_opaque_and_slug_shaped_references(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be a public-safe aggregate label"):
        observation(**{field_name: value})


def test_module_scope_is_static_report_only_public_safe_without_action_surfaces() -> None:
    source_body = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_body.lower()
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

    tree = ast.parse(source_body)
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
