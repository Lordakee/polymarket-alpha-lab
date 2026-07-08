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

from polymarket_alpha_lab.research_team_specialist_memory_retention_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION,
    SPECIALIST_MEMORY_RETENTION_STATUSES,
    ResearchTeamSpecialistMemoryRetentionConfig,
    ResearchTeamSpecialistMemoryRetentionDomainCoverage,
    ResearchTeamSpecialistMemoryRetentionObservation,
    ResearchTeamSpecialistMemoryRetentionReasonCodeCount,
    ResearchTeamSpecialistMemoryRetentionReport,
    ResearchTeamSpecialistMemoryRetentionRow,
    build_research_team_specialist_memory_retention_report,
    research_team_specialist_memory_retention_report_digest,
    research_team_specialist_memory_retention_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_retention_report.py"
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
    *,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    long_term_memory_count: Decimal = d("10.000000"),
    fresh_long_term_memory_count: Decimal = d("9.000000"),
    calibration_event_count: Decimal = d("10.000000"),
    calibration_uptake_count: Decimal = d("8.000000"),
    unresolved_conflict_count: Decimal = d("10.000000"),
    carried_forward_conflict_count: Decimal = d("0.000000"),
    retrieval_attempt_count: Decimal = d("10.000000"),
    successful_retrieval_count: Decimal = d("9.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryRetentionObservation:
    return ResearchTeamSpecialistMemoryRetentionObservation(
        domain_label=domain_label,
        specialist_label=specialist_label,
        observed_at=observed_at,
        long_term_memory_count=long_term_memory_count,
        fresh_long_term_memory_count=fresh_long_term_memory_count,
        calibration_event_count=calibration_event_count,
        calibration_uptake_count=calibration_uptake_count,
        unresolved_conflict_count=unresolved_conflict_count,
        carried_forward_conflict_count=carried_forward_conflict_count,
        retrieval_attempt_count=retrieval_attempt_count,
        successful_retrieval_count=successful_retrieval_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistMemoryRetentionObservation,
    config: ResearchTeamSpecialistMemoryRetentionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryRetentionReport:
    return build_research_team_specialist_memory_retention_report(
        items,
        config=config or ResearchTeamSpecialistMemoryRetentionConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_empty_observations_block_as_readonly_report_only_retention_gap() -> None:
    retention = report()

    assert type(retention) is ResearchTeamSpecialistMemoryRetentionReport
    assert SPECIALIST_MEMORY_RETENTION_STATUSES == ("pass", "watch", "block")
    assert retention.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION
    )
    assert retention.status == "block"
    assert retention.next_review_step == "block_specialist_memory_reuse_until_review"
    assert retention.observation_count == d("0.000000")
    assert retention.domain_count == d("0.000000")
    assert retention.specialist_count == d("0.000000")
    assert retention.long_term_memory_count == d("0.000000")
    assert retention.fresh_long_term_memory_count == d("0.000000")
    assert retention.pass_count == d("0.000000")
    assert retention.watch_count == d("0.000000")
    assert retention.block_count == d("0.000000")
    assert retention.memory_freshness_ratio == d("0.000000")
    assert retention.calibration_uptake_ratio == d("0.000000")
    assert retention.conflict_carry_forward_ratio == d("0.000000")
    assert retention.retrieval_coverage_ratio == d("0.000000")
    assert retention.retention_score == d("0.000000")
    assert retention.rows == ()
    assert retention.domain_coverage == ()
    assert retention.reason_codes == (
        "specialist_memory_retention_no_observations",
    )
    assert retention.reason_code_counts == (
        ResearchTeamSpecialistMemoryRetentionReasonCodeCount(
            reason_code="specialist_memory_retention_no_observations",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert retention.paper_only is True
    assert retention.report_only is True
    assert retention.readonly is True
    assert len(retention.derived_validation_digest) == 64


def test_report_aggregates_specialist_retention_statuses_and_domain_coverage() -> None:
    retention = report(
        observation(),
        observation(
            "policy.regulation",
            "policy_memory",
            fresh_long_term_memory_count=d("6.000000"),
            calibration_uptake_count=d("6.000000"),
            carried_forward_conflict_count=d("2.000000"),
            successful_retrieval_count=d("7.000000"),
        ),
        observation(
            "sports.soccer",
            "soccer_memory",
            fresh_long_term_memory_count=d("4.000000"),
            calibration_uptake_count=d("4.000000"),
            carried_forward_conflict_count=d("4.000000"),
            successful_retrieval_count=d("5.000000"),
        ),
    )

    assert retention.status == "block"
    assert retention.observation_count == d("3.000000")
    assert retention.domain_count == d("3.000000")
    assert retention.specialist_count == d("3.000000")
    assert retention.long_term_memory_count == d("30.000000")
    assert retention.fresh_long_term_memory_count == d("19.000000")
    assert retention.calibration_event_count == d("30.000000")
    assert retention.calibration_uptake_count == d("18.000000")
    assert retention.unresolved_conflict_count == d("30.000000")
    assert retention.carried_forward_conflict_count == d("6.000000")
    assert retention.retrieval_attempt_count == d("30.000000")
    assert retention.successful_retrieval_count == d("21.000000")
    assert retention.pass_count == d("1.000000")
    assert retention.watch_count == d("1.000000")
    assert retention.block_count == d("1.000000")
    assert retention.memory_freshness_ratio == d("0.633333")
    assert retention.calibration_uptake_ratio == d("0.600000")
    assert retention.conflict_carry_forward_ratio == d("0.200000")
    assert retention.retrieval_coverage_ratio == d("0.700000")
    assert retention.retention_score == d("0.683333")
    assert retention.reason_codes == (
        "specialist_memory_retention_block_present",
        "specialist_memory_retention_watch_present",
        "memory_freshness_gap_present",
        "calibration_uptake_gap_present",
        "conflict_carry_forward_present",
        "retrieval_coverage_gap_present",
    )

    assert tuple((row.domain_label, row.specialist_label, row.status) for row in retention.rows) == (
        ("sports.soccer", "soccer_memory", "block"),
        ("policy.regulation", "policy_memory", "watch"),
        ("finance.crypto", "crypto_memory", "pass"),
    )
    blocked, watched, passed = retention.rows
    assert blocked.memory_freshness_ratio == d("0.400000")
    assert blocked.calibration_uptake_ratio == d("0.400000")
    assert blocked.conflict_carry_forward_ratio == d("0.400000")
    assert blocked.retrieval_coverage_ratio == d("0.500000")
    assert blocked.retention_score == d("0.475000")
    assert blocked.reason_codes == (
        "memory_freshness_block",
        "calibration_uptake_block",
        "conflict_carry_forward_block",
        "retrieval_coverage_block",
    )
    assert watched.retention_score == d("0.675000")
    assert watched.reason_codes == (
        "memory_freshness_watch",
        "calibration_uptake_watch",
        "conflict_carry_forward_watch",
        "retrieval_coverage_watch",
    )
    assert passed.reason_codes == ("specialist_memory_retention_clear",)

    assert tuple(domain.domain_label for domain in retention.domain_coverage) == (
        "finance.crypto",
        "policy.regulation",
        "sports.soccer",
    )
    assert retention.domain_coverage[0] == ResearchTeamSpecialistMemoryRetentionDomainCoverage(
        domain_label="finance.crypto",
        specialist_count=d("1.000000"),
        long_term_memory_count=d("10.000000"),
        fresh_long_term_memory_count=d("9.000000"),
        retrieval_attempt_count=d("10.000000"),
        successful_retrieval_count=d("9.000000"),
        memory_freshness_ratio=d("0.900000"),
        retrieval_coverage_ratio=d("0.900000"),
        worst_status="pass",
    )
    assert retention.reason_code_counts[0].reason_code == "memory_freshness_block"
    assert retention.reason_code_counts[0].count == d("1.000000")
    assert retention.reason_code_counts[0].row_ratio == d("0.333333")


def test_payload_is_deterministic_digest_bound_decimal_string_only_and_public_safe() -> None:
    first = report(
        observation("policy.regulation", "policy_memory"),
        observation("finance.crypto", "crypto_memory"),
    )
    second = report(
        observation("finance.crypto", "crypto_memory"),
        observation("policy.regulation", "policy_memory"),
    )

    first_payload = research_team_specialist_memory_retention_report_payload(first)
    second_payload = research_team_specialist_memory_retention_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_memory_retention_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["rows"][0]["retention_score"] == "0.900000"
    assert first_payload["domain_coverage"][0]["domain_label"] == "finance.crypto"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.900000"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_retention_report_payload(tampered)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_retention_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "specialist_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_retention_report_payload(unsafe_value)


def test_validation_freezing_flags_decimal_only_statuses_and_consistency() -> None:
    retention = report(observation())

    assert retention.generated_at == GENERATED_AT
    assert retention.rows[0].observed_at == GENERATED_AT - timedelta(hours=1)
    assert retention.status in {"pass", "watch", "block"}
    assert all(row.status in {"pass", "watch", "block"} for row in retention.rows)

    for public_type in (
        ResearchTeamSpecialistMemoryRetentionConfig,
        ResearchTeamSpecialistMemoryRetentionObservation,
        ResearchTeamSpecialistMemoryRetentionRow,
        ResearchTeamSpecialistMemoryRetentionDomainCoverage,
        ResearchTeamSpecialistMemoryRetentionReasonCodeCount,
        ResearchTeamSpecialistMemoryRetentionReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchTeamSpecialistMemoryRetentionConfig(),
        observation(),
        retention.rows[0],
        retention.domain_coverage[0],
        retention.reason_code_counts[0],
        retention,
    ):
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        retention.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="long_term_memory_count must be exactly Decimal"):
        observation(long_term_memory_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="long_term_memory_count must be positive"):
        observation(long_term_memory_count=d("0.000000"))
    with pytest.raises(ValueError, match="fresh_long_term_memory_count must not exceed"):
        observation(fresh_long_term_memory_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="pairs must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="min_watch_memory_freshness_ratio"):
        ResearchTeamSpecialistMemoryRetentionConfig(
            min_pass_memory_freshness_ratio=d("0.700000"),
            min_watch_memory_freshness_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(retention.rows[0], status="ready")
    with pytest.raises(ValueError, match="memory_freshness_ratio must match row counts"):
        replace(retention.rows[0], memory_freshness_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(retention, derived_validation_digest="0" * 64)


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
