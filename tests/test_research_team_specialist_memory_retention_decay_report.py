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

from polymarket_alpha_lab.research_team_specialist_memory_retention_decay_report import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION,
    SPECIALIST_MEMORY_RETENTION_DECAY_STATUSES,
    ResearchTeamSpecialistMemoryRetentionDecayConfig,
    ResearchTeamSpecialistMemoryRetentionDecayDomainRow,
    ResearchTeamSpecialistMemoryRetentionDecayReasonCount,
    ResearchTeamSpecialistMemoryRetentionDecayReport,
    ResearchTeamSpecialistMemoryRetentionDecayRow,
    ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
    build_research_team_specialist_memory_retention_decay_report,
    research_team_specialist_memory_retention_decay_report_digest,
    research_team_specialist_memory_retention_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_specialist_memory_retention_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(
    domain_label: str = "finance.crypto",
    specialist_label: str = "crypto_memory",
    *,
    last_calibrated_at: datetime = GENERATED_AT - timedelta(days=2),
    long_term_memory_count: Decimal = d("10.000000"),
    error_attribution_opportunity_count: Decimal = d("10.000000"),
    reused_error_attribution_count: Decimal = d("8.000000"),
    feedback_event_count: Decimal = d("10.000000"),
    absorbed_feedback_count: Decimal = d("9.000000"),
    playbook_reference_count: Decimal = d("10.000000"),
    stale_playbook_reference_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryRetentionDecaySnapshot:
    return ResearchTeamSpecialistMemoryRetentionDecaySnapshot(
        domain_label=domain_label,
        specialist_label=specialist_label,
        last_calibrated_at=last_calibrated_at,
        long_term_memory_count=long_term_memory_count,
        error_attribution_opportunity_count=error_attribution_opportunity_count,
        reused_error_attribution_count=reused_error_attribution_count,
        feedback_event_count=feedback_event_count,
        absorbed_feedback_count=absorbed_feedback_count,
        playbook_reference_count=playbook_reference_count,
        stale_playbook_reference_count=stale_playbook_reference_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
    config: ResearchTeamSpecialistMemoryRetentionDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryRetentionDecayReport:
    return build_research_team_specialist_memory_retention_decay_report(
        items,
        config=config or ResearchTeamSpecialistMemoryRetentionDecayConfig(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def test_memory_decay_thresholds_create_pass_watch_and_block_rows() -> None:
    retention = report(
        snapshot(),
        snapshot(
            "policy.regulation",
            "policy_memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=14),
            reused_error_attribution_count=d("6.000000"),
            absorbed_feedback_count=d("6.000000"),
            stale_playbook_reference_count=d("2.000000"),
        ),
        snapshot(
            "sports.soccer",
            "soccer_memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=45),
            reused_error_attribution_count=d("4.000000"),
            absorbed_feedback_count=d("4.000000"),
            stale_playbook_reference_count=d("4.000000"),
        ),
    )

    assert SPECIALIST_MEMORY_RETENTION_DECAY_STATUSES == ("pass", "watch", "block")
    assert retention.status == "block"
    assert retention.next_review_step == "block_specialist_memory_retention_until_review"
    assert tuple((row.domain_label, row.specialist_label, row.status) for row in retention.rows) == (
        ("sports.soccer", "soccer_memory", "block"),
        ("policy.regulation", "policy_memory", "watch"),
        ("finance.crypto", "crypto_memory", "pass"),
    )

    blocked, watched, passed = retention.rows
    assert blocked.last_calibration_age_seconds == d("3888000.000000")
    assert blocked.calibration_recency_ratio == d("0.000000")
    assert blocked.error_attribution_reuse_ratio == d("0.400000")
    assert blocked.feedback_absorption_ratio == d("0.400000")
    assert blocked.stale_playbook_pressure_ratio == d("0.400000")
    assert blocked.retention_decay_score == d("0.350000")
    assert blocked.reason_codes == (
        "last_calibration_age_block",
        "error_attribution_reuse_block",
        "feedback_absorption_block",
        "stale_playbook_pressure_block",
    )

    assert watched.last_calibration_age_seconds == d("1209600.000000")
    assert watched.calibration_recency_ratio == d("0.533333")
    assert watched.retention_decay_score == d("0.633333")
    assert watched.reason_codes == (
        "last_calibration_age_watch",
        "error_attribution_reuse_watch",
        "feedback_absorption_watch",
        "stale_playbook_pressure_watch",
    )

    assert passed.calibration_recency_ratio == d("0.933333")
    assert passed.retention_decay_score == d("0.908333")
    assert passed.reason_codes == ("specialist_memory_retention_decay_clear",)


def test_domain_aggregation_summarizes_decay_by_domain() -> None:
    retention = report(
        snapshot(),
        snapshot(
            "finance.crypto",
            "event_memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=14),
            reused_error_attribution_count=d("6.000000"),
            absorbed_feedback_count=d("6.000000"),
            stale_playbook_reference_count=d("2.000000"),
        ),
        snapshot(
            "sports.soccer",
            "soccer_memory",
            last_calibrated_at=GENERATED_AT - timedelta(days=45),
            reused_error_attribution_count=d("4.000000"),
            absorbed_feedback_count=d("4.000000"),
            stale_playbook_reference_count=d("4.000000"),
        ),
    )

    assert retention.snapshot_count == d("3.000000")
    assert retention.domain_count == d("2.000000")
    assert retention.specialist_count == d("3.000000")
    assert retention.long_term_memory_count == d("30.000000")
    assert retention.reused_error_attribution_count == d("18.000000")
    assert retention.absorbed_feedback_count == d("19.000000")
    assert retention.stale_playbook_reference_count == d("6.000000")
    assert retention.pass_count == d("1.000000")
    assert retention.watch_count == d("1.000000")
    assert retention.block_count == d("1.000000")
    assert retention.error_attribution_reuse_ratio == d("0.600000")
    assert retention.feedback_absorption_ratio == d("0.633333")
    assert retention.stale_playbook_pressure_ratio == d("0.200000")
    assert retention.average_retention_decay_score == d("0.630555")
    assert retention.reason_codes == (
        "specialist_memory_retention_decay_block_present",
        "specialist_memory_retention_decay_watch_present",
        "last_calibration_age_gap_present",
        "error_attribution_reuse_gap_present",
        "feedback_absorption_gap_present",
        "stale_playbook_pressure_present",
    )

    assert retention.domain_rows == (
        ResearchTeamSpecialistMemoryRetentionDecayDomainRow(
            domain_label="finance.crypto",
            specialist_count=d("2.000000"),
            long_term_memory_count=d("20.000000"),
            max_last_calibration_age_seconds=d("1209600.000000"),
            error_attribution_opportunity_count=d("20.000000"),
            reused_error_attribution_count=d("14.000000"),
            feedback_event_count=d("20.000000"),
            absorbed_feedback_count=d("15.000000"),
            playbook_reference_count=d("20.000000"),
            stale_playbook_reference_count=d("2.000000"),
            error_attribution_reuse_ratio=d("0.700000"),
            feedback_absorption_ratio=d("0.750000"),
            stale_playbook_pressure_ratio=d("0.100000"),
            average_retention_decay_score=d("0.770833"),
            worst_status="watch",
        ),
        ResearchTeamSpecialistMemoryRetentionDecayDomainRow(
            domain_label="sports.soccer",
            specialist_count=d("1.000000"),
            long_term_memory_count=d("10.000000"),
            max_last_calibration_age_seconds=d("3888000.000000"),
            error_attribution_opportunity_count=d("10.000000"),
            reused_error_attribution_count=d("4.000000"),
            feedback_event_count=d("10.000000"),
            absorbed_feedback_count=d("4.000000"),
            playbook_reference_count=d("10.000000"),
            stale_playbook_reference_count=d("4.000000"),
            error_attribution_reuse_ratio=d("0.400000"),
            feedback_absorption_ratio=d("0.400000"),
            stale_playbook_pressure_ratio=d("0.400000"),
            average_retention_decay_score=d("0.350000"),
            worst_status="block",
        ),
    )
    assert retention.reason_counts[0] == ResearchTeamSpecialistMemoryRetentionDecayReasonCount(
        reason_code="last_calibration_age_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    )


def test_public_payload_is_deterministic_digest_bound_decimal_string_only_and_safe() -> None:
    first = report(
        snapshot("policy.regulation", "policy_memory"),
        snapshot("finance.crypto", "crypto_memory"),
    )
    second = report(
        snapshot("finance.crypto", "crypto_memory"),
        snapshot("policy.regulation", "policy_memory"),
    )

    first_payload = research_team_specialist_memory_retention_decay_report_payload(first)
    second_payload = research_team_specialist_memory_retention_decay_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first.public_payload == first_payload
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_team_specialist_memory_retention_decay_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["snapshot_count"] == "2.000000"
    assert first_payload["rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["rows"][0]["retention_decay_score"] == "0.908333"
    assert first_payload["domain_rows"][0]["domain_label"] == "finance.crypto"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.908333"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_retention_decay_report_payload(tampered)

    unsigned = dict(first_payload)
    unsigned.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_specialist_memory_retention_decay_report_payload(unsigned)

    unsafe_key = dict(first_payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_retention_decay_report_payload(unsafe_key)

    unsafe_value = dict(first_payload)
    unsafe_value["rows"] = [
        {**first_payload["rows"][0], "specialist_label": "candidate_id_linked"},
        *first_payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        research_team_specialist_memory_retention_decay_report_payload(unsafe_value)


def test_public_payload_rejects_recomputed_digest_schema_tampering() -> None:
    payload = research_team_specialist_memory_retention_decay_report_payload(
        report(snapshot()),
    )

    bad_status = dict(payload)
    bad_status["status"] = "ready"
    bad_status["derived_validation_digest"] = canonical_digest(bad_status)
    with pytest.raises(ValueError, match="status"):
        research_team_specialist_memory_retention_decay_report_payload(bad_status)

    inconsistent_count = dict(payload)
    inconsistent_count["snapshot_count"] = "2.000000"
    inconsistent_count["derived_validation_digest"] = canonical_digest(inconsistent_count)
    with pytest.raises(ValueError, match="snapshot_count must match rows"):
        research_team_specialist_memory_retention_decay_report_payload(inconsistent_count)

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["snapshot_count"] = "1"
    noncanonical_decimal["derived_validation_digest"] = canonical_digest(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        research_team_specialist_memory_retention_decay_report_payload(
            noncanonical_decimal,
        )

    extra_key = dict(payload)
    extra_key["safe_extra_code"] = "safe_code"
    extra_key["derived_validation_digest"] = canonical_digest(extra_key)
    with pytest.raises(ValueError, match="public report schema"):
        research_team_specialist_memory_retention_decay_report_payload(extra_key)

    fake_minimal_report = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    fake_minimal_report["derived_validation_digest"] = canonical_digest(fake_minimal_report)
    with pytest.raises(ValueError, match="public report schema"):
        research_team_specialist_memory_retention_decay_report_payload(
            fake_minimal_report,
        )

    with pytest.raises(ValueError, match="report must be exactly"):
        research_team_specialist_memory_retention_decay_report_payload(snapshot())


def test_custom_config_validation_and_hard_flags_are_enforced() -> None:
    custom = ResearchTeamSpecialistMemoryRetentionDecayConfig(
        max_pass_last_calibration_age_seconds=d("172800.000000"),
        max_watch_last_calibration_age_seconds=d("259200.000000"),
        min_pass_error_attribution_reuse_ratio=d("0.900000"),
        min_watch_error_attribution_reuse_ratio=d("0.850000"),
        min_pass_feedback_absorption_ratio=d("0.900000"),
        min_watch_feedback_absorption_ratio=d("0.800000"),
        max_pass_stale_playbook_pressure_ratio=d("0.050000"),
        max_watch_stale_playbook_pressure_ratio=d("0.100000"),
    )
    retention = report(
        snapshot(last_calibrated_at=GENERATED_AT - timedelta(days=4)),
        config=custom,
    )

    assert retention.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_DECAY_REPORT_CONFIG_VERSION
    )
    assert retention.rows[0].status == "block"
    assert retention.rows[0].reason_codes == (
        "last_calibration_age_block",
        "error_attribution_reuse_block",
    )

    with pytest.raises(ValueError, match="max_pass_last_calibration_age_seconds"):
        ResearchTeamSpecialistMemoryRetentionDecayConfig(
            max_pass_last_calibration_age_seconds=d("30.000000"),
            max_watch_last_calibration_age_seconds=d("20.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_error_attribution_reuse_ratio"):
        ResearchTeamSpecialistMemoryRetentionDecayConfig(
            min_pass_error_attribution_reuse_ratio=d("0.700000"),
            min_watch_error_attribution_reuse_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="max_pass_stale_playbook_pressure_ratio"):
        ResearchTeamSpecialistMemoryRetentionDecayConfig(
            max_pass_stale_playbook_pressure_ratio=d("0.200000"),
            max_watch_stale_playbook_pressure_ratio=d("0.100000"),
        )
    with pytest.raises(ValueError, match="min_pass_feedback_absorption_ratio must be exactly Decimal"):
        ResearchTeamSpecialistMemoryRetentionDecayConfig(
            min_pass_feedback_absorption_ratio=0.8,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchTeamSpecialistMemoryRetentionDecayConfig(paper_only=False)


def test_validation_freezing_decimal_only_and_consistency_checks() -> None:
    retention = report(snapshot())

    assert type(retention) is ResearchTeamSpecialistMemoryRetentionDecayReport
    assert is_dataclass(retention)
    assert retention.generated_at == GENERATED_AT
    assert retention.rows[0].last_calibrated_at == GENERATED_AT - timedelta(days=2)

    for public_type in (
        ResearchTeamSpecialistMemoryRetentionDecayConfig,
        ResearchTeamSpecialistMemoryRetentionDecaySnapshot,
        ResearchTeamSpecialistMemoryRetentionDecayRow,
        ResearchTeamSpecialistMemoryRetentionDecayDomainRow,
        ResearchTeamSpecialistMemoryRetentionDecayReasonCount,
        ResearchTeamSpecialistMemoryRetentionDecayReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchTeamSpecialistMemoryRetentionDecayConfig(),
        snapshot(),
        retention.rows[0],
        retention.domain_rows[0],
        retention.reason_counts[0],
        retention,
    ):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        retention.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="last_calibrated_at must be timezone-aware"):
        snapshot(last_calibrated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="last_calibrated_at must be exactly datetime"):
        snapshot(last_calibrated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="long_term_memory_count must be exactly Decimal"):
        snapshot(long_term_memory_count=_DecimalSubclass("10.000000"))
    with pytest.raises(ValueError, match="long_term_memory_count must be positive"):
        snapshot(long_term_memory_count=d("0.000000"))
    with pytest.raises(ValueError, match="reused_error_attribution_count must not exceed"):
        snapshot(reused_error_attribution_count=d("11.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        snapshot(readonly=False)
    with pytest.raises(ValueError, match="pairs must be unique"):
        report(snapshot(), snapshot())
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(retention.rows[0], status="ready")
    with pytest.raises(ValueError, match="error_attribution_reuse_ratio must match row counts"):
        replace(retention.rows[0], error_attribution_reuse_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(retention, derived_validation_digest="0" * 64)


def test_empty_snapshots_block_without_exposing_private_surfaces() -> None:
    retention = report()

    assert retention.status == "block"
    assert retention.snapshot_count == d("0.000000")
    assert retention.domain_count == d("0.000000")
    assert retention.specialist_count == d("0.000000")
    assert retention.average_retention_decay_score == d("0.000000")
    assert retention.rows == ()
    assert retention.domain_rows == ()
    assert retention.reason_codes == ("specialist_memory_retention_decay_no_snapshots",)
    assert retention.reason_counts == (
        ResearchTeamSpecialistMemoryRetentionDecayReasonCount(
            reason_code="specialist_memory_retention_decay_no_snapshots",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )

    payload = retention.public_payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_forbidden_public_payload_surface(payload)


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "https://example.test/source",
        "db_connection",
        "execution_plan",
    ),
)
def test_public_labels_reject_url_database_and_execution_surfaces(
    unsafe_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public payload text"):
        snapshot(domain_label=unsafe_value)


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
