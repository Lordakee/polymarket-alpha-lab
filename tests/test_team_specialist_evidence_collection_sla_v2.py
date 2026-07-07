from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
SOURCE_CONFIG_VERSION = "phase1-source-manifest-v2"


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_evidence_collection_sla_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "first_source_sla_seconds": d("900.000000"),
        "official_source_sla_seconds": d("1800.000000"),
        "independent_corroboration_sla_seconds": d("3600.000000"),
        "stale_evidence_sla_seconds": d("7200.000000"),
        "contradiction_followup_sla_seconds": d("1200.000000"),
        "high_queue_urgency_threshold": d("0.750000"),
    }
    values.update(overrides)
    return api().TeamSpecialistEvidenceCollectionSlaV2Config(**values)


def task(
    task_id: str,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    assigned_at: datetime = GENERATED_AT - timedelta(minutes=15),
    first_source_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    official_source_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    independent_corroboration_at: datetime | None = GENERATED_AT - timedelta(minutes=2),
    latest_evidence_at: datetime | None = GENERATED_AT - timedelta(minutes=2),
    contradiction_detected_at: datetime | None = None,
    contradiction_followed_up_at: datetime | None = None,
    queue_priority: str = "low",
    source_config_version: str = SOURCE_CONFIG_VERSION,
):
    return api().TeamSpecialistEvidenceCollectionSlaV2InputRow(
        task_id=task_id,
        team_id=team_id,
        category_id=category_id,
        assigned_at=assigned_at,
        first_source_at=first_source_at,
        official_source_at=official_source_at,
        independent_corroboration_at=independent_corroboration_at,
        latest_evidence_at=latest_evidence_at,
        contradiction_detected_at=contradiction_detected_at,
        contradiction_followed_up_at=contradiction_followed_up_at,
        queue_priority=queue_priority,
        source_config_version=source_config_version,
    )


def report(*rows: object, **config_overrides: object):
    return api().build_team_specialist_evidence_collection_sla_v2_report(
        rows,
        config=config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)


def assert_no_float_or_decimal_payload_values(value: object) -> None:
    values = walk_payload_values(value)
    assert not any(type(item) is float for item in values)
    assert not any(type(item) is Decimal for item in values)


def test_phase1_evidence_collection_sla_reports_all_required_milestones() -> None:
    module = api()

    pass_task = task(
        "task-pass",
        assigned_at=GENERATED_AT - timedelta(minutes=15),
        first_source_at=GENERATED_AT - timedelta(minutes=10),
        official_source_at=GENERATED_AT - timedelta(minutes=5),
        independent_corroboration_at=GENERATED_AT - timedelta(minutes=2),
        latest_evidence_at=GENERATED_AT - timedelta(minutes=2),
        queue_priority="low",
    )
    watch_task = task(
        "task-watch",
        team_id="macro_rates",
        category_id="finance.macro.rates",
        assigned_at=GENERATED_AT - timedelta(minutes=25),
        first_source_at=None,
        official_source_at=None,
        independent_corroboration_at=None,
        latest_evidence_at=None,
        queue_priority="medium",
    )
    blocked_task = task(
        "task-blocked",
        assigned_at=GENERATED_AT - timedelta(hours=3),
        first_source_at=GENERATED_AT - timedelta(hours=2, minutes=40),
        official_source_at=None,
        independent_corroboration_at=None,
        latest_evidence_at=GENERATED_AT - timedelta(hours=2, minutes=30),
        contradiction_detected_at=GENERATED_AT - timedelta(hours=2),
        contradiction_followed_up_at=None,
        queue_priority="critical",
    )

    sla_report = report(pass_task, watch_task, blocked_task)
    payload = module.team_specialist_evidence_collection_sla_v2_report_to_payload(
        sla_report,
    )

    assert is_dataclass(sla_report)
    assert type(sla_report) is module.TeamSpecialistEvidenceCollectionSlaV2Report
    assert sla_report.generated_at == GENERATED_AT
    assert sla_report.config_version == "team-specialist-evidence-collection-sla-v2"
    assert sla_report.report_status == "blocked"
    assert sla_report.task_count == d("3.000000")
    assert sla_report.pass_row_count == d("1.000000")
    assert sla_report.watch_row_count == d("1.000000")
    assert sla_report.blocked_row_count == d("1.000000")
    assert sla_report.issue_row_count == d("2.000000")
    assert sla_report.issue_ratio == d("0.666667")
    assert sla_report.first_source_sla_breach_count == d("2.000000")
    assert sla_report.official_source_sla_breach_count == d("1.000000")
    assert sla_report.independent_corroboration_sla_breach_count == d("1.000000")
    assert sla_report.stale_evidence_count == d("1.000000")
    assert sla_report.contradiction_followup_sla_breach_count == d("1.000000")
    assert sla_report.high_queue_urgency_count == d("2.000000")
    assert sla_report.max_queue_urgency_score == d("1.000000")
    assert sla_report.reason_codes == (
        "specialist_evidence_collection_sla_blocked",
        "first_source_sla_breached",
        "official_source_sla_breached",
        "independent_corroboration_sla_breached",
        "evidence_stale",
        "contradiction_followup_sla_breached",
        "queue_urgency_high",
    )
    assert len(sla_report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in sla_report.derived_validation_digest)
    assert sla_report.paper_only is True
    assert sla_report.report_only is True
    assert sla_report.readonly is True

    assert tuple(row.task_id for row in sla_report.rows) == (
        "task-blocked",
        "task-watch",
        "task-pass",
    )

    blocked = sla_report.rows[0]
    assert type(blocked) is module.TeamSpecialistEvidenceCollectionSlaV2Row
    assert blocked.row_status == "blocked"
    assert blocked.assigned_age_seconds == d("10800.000000")
    assert blocked.first_source_latency_seconds == d("1200.000000")
    assert blocked.official_source_latency_seconds == d("10800.000000")
    assert blocked.independent_corroboration_latency_seconds == d("10800.000000")
    assert blocked.latest_evidence_age_seconds == d("9000.000000")
    assert blocked.contradiction_followup_latency_seconds == d("7200.000000")
    assert blocked.queue_urgency_score == d("1.000000")
    assert blocked.reason_codes == (
        "first_source_sla_breached",
        "official_source_sla_breached",
        "independent_corroboration_sla_breached",
        "evidence_stale",
        "contradiction_followup_sla_breached",
        "queue_urgency_high",
    )

    watch = sla_report.rows[1]
    assert watch.row_status == "watch"
    assert watch.first_source_at is None
    assert watch.first_source_latency_seconds == d("1500.000000")
    assert watch.official_source_latency_seconds == d("1500.000000")
    assert watch.independent_corroboration_latency_seconds == d("1500.000000")
    assert watch.latest_evidence_age_seconds == d("1500.000000")
    assert watch.contradiction_followup_latency_seconds == d("0.000000")
    assert watch.queue_urgency_score == d("1.000000")
    assert watch.reason_codes == (
        "first_source_sla_breached",
        "queue_urgency_high",
    )

    passed = sla_report.rows[2]
    assert passed.row_status == "pass"
    assert passed.assigned_age_seconds == d("900.000000")
    assert passed.first_source_latency_seconds == d("300.000000")
    assert passed.official_source_latency_seconds == d("600.000000")
    assert passed.independent_corroboration_latency_seconds == d("780.000000")
    assert passed.latest_evidence_age_seconds == d("120.000000")
    assert passed.queue_urgency_score == d("0.333333")
    assert passed.reason_codes == ("specialist_evidence_collection_sla_pass",)

    assert payload["task_count"] == "3.000000"
    assert payload["issue_ratio"] == "0.666667"
    assert payload["max_queue_urgency_score"] == "1.000000"
    assert payload["rows"][0]["assigned_at"] == "2026-07-07T09:00:00+00:00"
    assert payload["rows"][0]["first_source_at"] == "2026-07-07T09:20:00+00:00"
    assert payload["rows"][0]["official_source_at"] is None
    assert payload["rows"][0]["latest_evidence_age_seconds"] == "9000.000000"
    assert payload["rows"][1]["first_source_at"] is None
    assert payload["rows"][2]["queue_urgency_score"] == "0.333333"
    assert payload["derived_validation_digest"] == sla_report.derived_validation_digest
    assert_no_float_or_decimal_payload_values(payload)
    json.dumps(payload, sort_keys=True)

    reordered_report = report(blocked_task, pass_task, watch_task)
    assert reordered_report.derived_validation_digest == sla_report.derived_validation_digest


def test_empty_report_is_pass_with_decimal_zero_metrics() -> None:
    sla_report = report()

    assert sla_report.report_status == "pass"
    assert sla_report.task_count == d("0.000000")
    assert sla_report.pass_row_count == d("0.000000")
    assert sla_report.watch_row_count == d("0.000000")
    assert sla_report.blocked_row_count == d("0.000000")
    assert sla_report.issue_row_count == d("0.000000")
    assert sla_report.issue_ratio == d("0.000000")
    assert sla_report.first_source_sla_breach_count == d("0.000000")
    assert sla_report.official_source_sla_breach_count == d("0.000000")
    assert sla_report.independent_corroboration_sla_breach_count == d("0.000000")
    assert sla_report.stale_evidence_count == d("0.000000")
    assert sla_report.contradiction_followup_sla_breach_count == d("0.000000")
    assert sla_report.high_queue_urgency_count == d("0.000000")
    assert sla_report.max_queue_urgency_score == d("0.000000")
    assert sla_report.rows == ()
    assert sla_report.reason_codes == ("specialist_evidence_collection_sla_pass",)


def test_inputs_validate_decimal_only_times_duplicates_frozen_and_hard_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="first_source_sla_seconds must be a Decimal"):
        config(first_source_sla_seconds=900)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_evidence_collection_sla_v2_report(
            (task("task-naive"),),
            config=config(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )

    with pytest.raises(ValueError, match="task_id values must be unique"):
        report(task("task-dup"), task("task-dup"))

    with pytest.raises(ValueError, match="first_source_at must not be before assigned_at"):
        task(
            "task-milestone-order",
            assigned_at=GENERATED_AT - timedelta(minutes=10),
            first_source_at=GENERATED_AT - timedelta(minutes=11),
        )

    with pytest.raises(ValueError, match="first_source_at must not be after generated_at"):
        report(
            task(
                "task-future-source",
                first_source_at=GENERATED_AT + timedelta(minutes=1),
            ),
        )

    item = task("task-frozen")
    with pytest.raises(FrozenInstanceError):
        item.task_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.TeamSpecialistEvidenceCollectionSlaV2Config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(task("task-flag")), readonly=False)

    for cls in (
        module.TeamSpecialistEvidenceCollectionSlaV2Config,
        module.TeamSpecialistEvidenceCollectionSlaV2Row,
        module.TeamSpecialistEvidenceCollectionSlaV2Report,
    ):
        hints = get_type_hints(cls)
        for field in fields(cls):
            if (
                field.name.endswith("_seconds")
                or field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
            ):
                assert hints[field.name] is Decimal


def test_public_payload_is_digest_bound_and_rejects_unsafe_surfaces() -> None:
    module = api()
    sla_report = report(task("task-json"))
    payload = module.team_specialist_evidence_collection_sla_v2_report_to_payload(
        sla_report,
    )

    tampered_payload = dict(payload)
    tampered_payload["task_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_evidence_collection_sla_v2_report_to_payload(
            tampered_payload,
        )

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_evidence_collection_sla_v2_report_to_payload(
            missing_digest_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_hint"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.team_specialist_evidence_collection_sla_v2_report_to_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [
        {
            **payload["rows"][0],
            "source_config_version": "connect_wallet",
        },
    ]
    with pytest.raises(ValueError, match="unsafe"):
        module.team_specialist_evidence_collection_sla_v2_report_to_payload(
            unsafe_value_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        task("task-safe", source_config_version="connect_wallet")

    tampered_report = report(task("task-tamper"))
    object.__setattr__(tampered_report.rows[0], "queue_urgency_score", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_evidence_collection_sla_v2_report_to_payload(
            tampered_report,
        )


def test_module_scope_exposes_no_external_actions_or_float_literals() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "BLOCKED_REASON",
        "DEFAULT_TEAM_SPECIALIST_EVIDENCE_COLLECTION_SLA_V2_CONFIG_VERSION",
        "PASS_REASON",
        "REASON_CODES",
        "REPORT_STATUSES",
        "ROW_STATUSES",
        "TeamSpecialistEvidenceCollectionSlaV2Config",
        "TeamSpecialistEvidenceCollectionSlaV2InputRow",
        "TeamSpecialistEvidenceCollectionSlaV2Report",
        "TeamSpecialistEvidenceCollectionSlaV2Row",
        "build_team_specialist_evidence_collection_sla_v2_report",
        "team_specialist_evidence_collection_sla_v2_report_to_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert not imported_roots & {
        "aiohttp",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    assert {
        "connect",
        "execute",
        "executemany",
        "open",
        "post",
        "put",
        "patch",
        "request",
        "read_text",
        "send",
        "write_text",
    }.isdisjoint(called_names)

    forbidden_public_field_fragments = (
        "account",
        "auth",
        "balance",
        "order",
        "private_key",
        "wallet",
    )
    for cls in (
        module.TeamSpecialistEvidenceCollectionSlaV2Config,
        module.TeamSpecialistEvidenceCollectionSlaV2InputRow,
        module.TeamSpecialistEvidenceCollectionSlaV2Row,
        module.TeamSpecialistEvidenceCollectionSlaV2Report,
    ):
        for field in fields(cls):
            assert not any(
                fragment in field.name.lower()
                for fragment in forbidden_public_field_fragments
            )
