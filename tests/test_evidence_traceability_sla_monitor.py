from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.evidence_traceability_sla_monitor",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(
    source_id: str,
    *,
    evidence_count: str,
    traced_evidence_count: str,
    linked_reference_count: str,
    stale_link_count: str = "0",
    duplicate_reference_count: str = "0",
    redacted_payload_count: str = "0",
    oldest_link_age_minutes: str = "0",
    previous_missing_trace_count: str | None = None,
    raw_payload_reference: str = "opaque-source-payload",
):
    monitor = module()
    return monitor.EvidenceTraceabilityAuditSnapshot(
        source_id=source_id,
        evidence_count=d(evidence_count),
        traced_evidence_count=d(traced_evidence_count),
        linked_reference_count=d(linked_reference_count),
        stale_link_count=d(stale_link_count),
        duplicate_reference_count=d(duplicate_reference_count),
        redacted_payload_count=d(redacted_payload_count),
        oldest_link_age_minutes=d(oldest_link_age_minutes),
        previous_missing_trace_count=(
            None
            if previous_missing_trace_count is None
            else d(previous_missing_trace_count)
        ),
        raw_payload_reference=raw_payload_reference,
    )


def build_report(*snapshots):
    monitor = module()
    return monitor.build_evidence_traceability_sla_report(
        snapshots,
        config=monitor.EvidenceTraceabilitySlaConfig(
            config_version="evidence-traceability-sla-monitor-test-v0",
            stale_link_watch_minutes=d("60.000000"),
            stale_link_breach_minutes=d("240.000000"),
            max_missing_trace_share=d("0.250000"),
            max_duplicate_reference_share=d("0.200000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_summarizes_traceability_pressure_and_redacted_rows() -> None:
    report = build_report(
        snapshot(
            "research-queue-b",
            evidence_count="5.000000",
            traced_evidence_count="3.000000",
            linked_reference_count="4.000000",
            stale_link_count="1.000000",
            duplicate_reference_count="1.000000",
            redacted_payload_count="2.000000",
            oldest_link_age_minutes="90.000000",
            previous_missing_trace_count="1.000000",
            raw_payload_reference="postgres://user:secret@localhost/evidence",
        ),
        snapshot(
            "research-queue-a",
            evidence_count="4.000000",
            traced_evidence_count="4.000000",
            linked_reference_count="4.000000",
            oldest_link_age_minutes="10.000000",
        ),
    )

    assert report.traceability_status == "watch"
    assert report.total_evidence_count == d("9.000000")
    assert report.total_missing_trace_count == d("2.000000")
    assert report.total_orphan_evidence_count == d("1.000000")
    assert report.total_stale_link_count == d("1.000000")
    assert report.total_duplicate_reference_count == d("1.000000")
    assert report.total_redacted_payload_count == d("2.000000")
    assert report.missing_trace_share == d("0.222222")
    assert report.orphan_evidence_share == d("0.111111")
    assert report.duplicate_reference_share == d("0.111111")
    assert report.missing_trace_delta == d("1.000000")
    assert report.reason_codes == (
        "missing_trace_trend_worsening",
        "orphan_evidence_pressure_present",
        "stale_link_watch_threshold_breached",
        "duplicate_reference_pressure_present",
        "redacted_payload_rows_present",
        "evidence_traceability_sla_watch",
    )
    assert tuple(row.source_id for row in report.rows) == (
        "research-queue-b",
        "research-queue-a",
    )
    assert report.rows[0].traceability_status == "watch"
    assert report.rows[0].missing_trace_count == d("2.000000")
    assert report.rows[0].orphan_evidence_count == d("1.000000")
    assert report.rows[0].missing_trace_delta == d("1.000000")
    assert report.rows[0].raw_payload_reference == "<redacted-evidence-payload>"
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True
    assert "secret" not in repr(report)


def test_stale_link_sla_breach_blocks_report() -> None:
    report = build_report(
        snapshot(
            "research-queue-a",
            evidence_count="3.000000",
            traced_evidence_count="3.000000",
            linked_reference_count="3.000000",
            stale_link_count="1.000000",
            oldest_link_age_minutes="300.000000",
        ),
    )

    assert report.traceability_status == "blocked"
    assert report.stale_link_sla_breach_count == d("1.000000")
    assert report.rows[0].traceability_status == "blocked"
    assert report.rows[0].reason_codes == (
        "stale_link_sla_breach_threshold_exceeded",
    )
    assert "evidence_traceability_sla_blocked" in report.reason_codes


def test_public_payload_is_json_ready_tamper_evident_and_safe() -> None:
    monitor = module()
    report = build_report(
        snapshot(
            "research-queue-a",
            evidence_count="3.000000",
            traced_evidence_count="2.000000",
            linked_reference_count="3.000000",
            duplicate_reference_count="1.000000",
            previous_missing_trace_count="0.000000",
        ),
    )
    equivalent_report = build_report(
        snapshot(
            "research-queue-a",
            evidence_count="3.000000",
            traced_evidence_count="2.000000",
            linked_reference_count="3.000000",
            duplicate_reference_count="1.000000",
            previous_missing_trace_count="0.000000",
        ),
    )

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.derived_validation_digest == equivalent_report.derived_validation_digest

    payload = monitor.evidence_traceability_sla_report_payload(report)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["total_evidence_count"] == "3.000000"
    assert payload["missing_trace_share"] == "0.333333"
    assert payload["rows"][0]["missing_trace_delta"] == "1.000000"
    assert payload["rows"][0]["raw_payload_reference"] == "<redacted-evidence-payload>"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _float_paths(payload) == ()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["total_evidence_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        monitor.evidence_traceability_sla_report_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        monitor.evidence_traceability_sla_report_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["config_version"] = "secret-report"
    with pytest.raises(ValueError, match="unsafe"):
        monitor.evidence_traceability_sla_report_payload(unsafe_value_payload)


def test_no_snapshots_blocks_without_dividing_by_zero() -> None:
    report = build_report()

    assert report.traceability_status == "blocked"
    assert report.total_source_count == d("0.000000")
    assert report.missing_trace_share == d("0.000000")
    assert report.orphan_evidence_share == d("0.000000")
    assert report.duplicate_reference_share == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("no_evidence_traceability_snapshots",)


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_local() -> None:
    monitor = module()

    assert monitor.__all__ == (
        "DEFAULT_EVIDENCE_TRACEABILITY_SLA_CONFIG_VERSION",
        "EvidenceTraceabilityAuditSnapshot",
        "EvidenceTraceabilitySlaConfig",
        "EvidenceTraceabilitySlaReport",
        "EvidenceTraceabilitySlaRow",
        "build_evidence_traceability_sla_report",
        "evidence_traceability_sla_report_payload",
    )
    for exported_name in monitor.__all__:
        value = getattr(monitor, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(
        snapshot(
            "research-queue-a",
            evidence_count="1.000000",
            traced_evidence_count="1.000000",
            linked_reference_count="1.000000",
        ),
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].evidence_count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="evidence_count must be a Decimal"):
        monitor.EvidenceTraceabilityAuditSnapshot(
            source_id="research-queue-a",
            evidence_count=1,
            traced_evidence_count=d("1.000000"),
            linked_reference_count=d("1.000000"),
            stale_link_count=d("0.000000"),
            duplicate_reference_count=d("0.000000"),
            redacted_payload_count=d("0.000000"),
            oldest_link_age_minutes=d("0.000000"),
        )


def test_generated_at_requires_timezone_and_normalizes_to_utc() -> None:
    monitor = module()

    report = monitor.build_evidence_traceability_sla_report(
        (
            snapshot(
                "research-queue-a",
                evidence_count="1.000000",
                traced_evidence_count="1.000000",
                linked_reference_count="1.000000",
            ),
        ),
        config=monitor.EvidenceTraceabilitySlaConfig(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone.utc),
    )
    assert report.generated_at == datetime(2026, 7, 2, 8, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        monitor.build_evidence_traceability_sla_report(
            (),
            config=monitor.EvidenceTraceabilitySlaConfig(),
            generated_at=datetime(2026, 7, 2, 8, 0),
        )


def test_rejects_invalid_counts_duplicates_and_unredacted_public_rows() -> None:
    monitor = module()
    report = build_report(
        snapshot(
            "research-queue-a",
            evidence_count="3.000000",
            traced_evidence_count="2.000000",
            linked_reference_count="3.000000",
            stale_link_count="1.000000",
            duplicate_reference_count="1.000000",
            previous_missing_trace_count="0.000000",
        ),
    )

    with pytest.raises(ValueError, match="traced_evidence_count must not exceed"):
        snapshot(
            "research-queue-a",
            evidence_count="1.000000",
            traced_evidence_count="2.000000",
            linked_reference_count="1.000000",
        )

    with pytest.raises(ValueError, match="duplicate source_id"):
        build_report(
            snapshot(
                "research-queue-a",
                evidence_count="1.000000",
                traced_evidence_count="1.000000",
                linked_reference_count="1.000000",
            ),
            snapshot(
                "research-queue-a",
                evidence_count="1.000000",
                traced_evidence_count="1.000000",
                linked_reference_count="1.000000",
            ),
        )

    with pytest.raises(ValueError, match="raw_payload_reference"):
        monitor.EvidenceTraceabilitySlaRow(
            source_id="research-queue-a",
            evidence_count=d("1.000000"),
            traced_evidence_count=d("1.000000"),
            missing_trace_count=d("0.000000"),
            previous_missing_trace_count=None,
            missing_trace_delta=d("0.000000"),
            linked_reference_count=d("1.000000"),
            orphan_evidence_count=d("0.000000"),
            stale_link_count=d("0.000000"),
            stale_link_sla_breach_count=d("0.000000"),
            duplicate_reference_count=d("0.000000"),
            redacted_payload_count=d("0.000000"),
            oldest_link_age_minutes=d("0.000000"),
            missing_trace_share=d("0.000000"),
            orphan_evidence_share=d("0.000000"),
            duplicate_reference_share=d("0.000000"),
            traceability_status="pass",
            reason_codes=("evidence_traceability_source_pass",),
            raw_payload_reference="unredacted",
        )

    with pytest.raises(ValueError, match="total_linked_reference_count"):
        replace(
            report,
            total_linked_reference_count=d("2.000000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="previous_missing_trace_count"):
        replace(
            report,
            previous_missing_trace_count=d("2.000000"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="missing_trace_delta"):
        replace(
            report,
            missing_trace_delta=d("2.000000"),
            derived_validation_digest="",
        )

    row = report.rows[0]
    with pytest.raises(ValueError, match="stale_link_count"):
        replace(row, stale_link_count=d("4.000000"))
    with pytest.raises(ValueError, match="stale_link_sla_breach_count"):
        replace(
            row,
            stale_link_count=d("1.000000"),
            stale_link_sla_breach_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="duplicate_reference_count"):
        replace(
            row,
            duplicate_reference_count=d("4.000000"),
            duplicate_reference_share=d("1.333333"),
        )
    with pytest.raises(ValueError, match="redacted_payload_count"):
        replace(row, redacted_payload_count=d("4.000000"))
    with pytest.raises(ValueError, match="missing_trace_delta"):
        replace(row, missing_trace_delta=d("0.000000"))


def test_module_scope_omits_persistence_execution_and_raw_identity_language() -> None:
    monitor = module()
    source = monitor.__loader__.get_source(monitor.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    for forbidden in (
        "investment advice",
        "trade instruction",
        "buy",
        "sell",
        "wallet",
        "account",
        "mutation",
    ):
        assert forbidden not in lowered


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    if type(value) is float:
        return (path,)
    return ()
