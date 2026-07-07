from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


def _api():
    return import_module("polymarket_alpha_lab.evidence_queue_traceability_audit")


def _config(**overrides):
    values = {
        "config_version": "evidence-queue-traceability-audit-v0",
        "stale_trace_link_seconds": Decimal("3600"),
    }
    values.update(overrides)
    return _api().EvidenceQueueTraceabilityAuditConfig(**values)


def _evidence(
    evidence_ref: str,
    *,
    team_id: str = "politics",
    packet_ref: str = "packet-a",
    last_seen_at: datetime = GENERATED_AT - timedelta(minutes=10),
):
    return _api().EvidencePacketReference(
        redacted_evidence_ref=evidence_ref,
        redacted_packet_ref=packet_ref,
        team_id=team_id,
        last_seen_at=last_seen_at,
        source_config_version="evidence-source-v0",
    )


def _queue(
    queue_ref: str,
    *,
    team_id: str = "politics",
    packet_ref: str | None = "packet-a",
    evidence_refs: tuple[str, ...] = ("evidence-a",),
    created_at: datetime = GENERATED_AT - timedelta(minutes=5),
):
    return _api().EvidenceQueueTraceabilityQueueRow(
        redacted_queue_ref=queue_ref,
        team_id=team_id,
        redacted_packet_ref=packet_ref,
        redacted_evidence_refs=evidence_refs,
        created_at=created_at,
        queue_status="report_pending",
        source_config_version="queue-source-v0",
    )


def _report(evidence_rows=(), queue_rows=(), **config_overrides):
    return _api().build_evidence_queue_traceability_audit_report(
        evidence_rows,
        queue_rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _assert_public_payload_has_no_runtime_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            _assert_public_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _assert_public_payload_has_no_runtime_numbers(child)


def test_passes_when_queue_rows_trace_to_supplied_evidence_without_raw_payloads() -> None:
    api = _api()
    report = _report(
        (
            _evidence("evidence-a", packet_ref="packet-a"),
            _evidence("evidence-b", packet_ref="packet-b"),
        ),
        (
            _queue("queue-a", packet_ref="packet-a", evidence_refs=("evidence-a",)),
            _queue("queue-b", packet_ref="packet-b", evidence_refs=("evidence-b",)),
        ),
    )

    assert type(report) is api.EvidenceQueueTraceabilityAuditReport
    assert report.traceability_status == "pass"
    assert report.recommended_report_action == "continue_report_only_queue_review"
    assert report.evidence_reference_count == Decimal("2")
    assert report.queue_row_count == Decimal("2")
    assert report.missing_trace_link_count == Decimal("0")
    assert report.orphan_evidence_count == Decimal("0")
    assert report.duplicate_queue_reference_count == Decimal("0")
    assert report.stale_evidence_link_count == Decimal("0")
    assert report.redacted_traceability_diagnostic_count == Decimal("0")
    assert report.reason_codes == ("evidence_queue_traceability_audit_passed",)
    assert tuple(row.trace_status for row in report.queue_trace_rows) == ("pass", "pass")
    assert tuple(row.redacted_queue_ref for row in report.queue_trace_rows) == (
        "queue-a",
        "queue-b",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    public = repr(asdict(report)).lower()
    for token in (
        "payload",
        "market_slug",
        "question",
        "investment advice",
        "trade instruction",
        "buy",
        "sell",
        "order",
        "wallet",
        "account",
        "auth",
    ):
        assert token not in public


def test_public_payload_is_decimal_stringed_deterministic_and_tamper_evident() -> None:
    api = _api()
    first = _report(
        (
            _evidence("evidence-b", packet_ref="packet-b"),
            _evidence("evidence-a", packet_ref="packet-a"),
        ),
        (
            _queue("queue-b", packet_ref="packet-b", evidence_refs=("evidence-b",)),
            _queue("queue-a", packet_ref="packet-a", evidence_refs=("evidence-a",)),
        ),
    )
    second = _report(
        (
            _evidence("evidence-a", packet_ref="packet-a"),
            _evidence("evidence-b", packet_ref="packet-b"),
        ),
        (
            _queue("queue-a", packet_ref="packet-a", evidence_refs=("evidence-a",)),
            _queue("queue-b", packet_ref="packet-b", evidence_refs=("evidence-b",)),
        ),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)

    payload = first.payload
    assert payload == api.evidence_queue_traceability_audit_payload(first)
    assert payload == api.evidence_queue_traceability_audit_payload(payload)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["evidence_reference_count"] == "2"
    assert payload["queue_row_count"] == "2"
    assert payload["queue_trace_rows"][0]["missing_trace_link_count"] == "0"
    assert payload["queue_trace_rows"][0]["newest_evidence_link_age_seconds"] == "600"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    _assert_public_payload_has_no_runtime_numbers(payload)

    tampered_payload = dict(payload)
    tampered_payload["queue_row_count"] = "3"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.evidence_queue_traceability_audit_payload(tampered_payload)

    missing_digest_payload = dict(payload)
    missing_digest_payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.evidence_queue_traceability_audit_payload(missing_digest_payload)

    object.__setattr__(first, "queue_row_count", Decimal("3"))
    with pytest.raises(ValueError, match="queue_row_count"):
        api.evidence_queue_traceability_audit_payload(first)


def test_public_payload_rejects_numeric_scalars_false_flags_and_unsafe_content() -> None:
    api = _api()
    payload = api.evidence_queue_traceability_audit_payload(
        _report((_evidence("evidence-a"),), (_queue("queue-a"),)),
    )

    numeric_payload = dict(payload)
    numeric_payload["queue_row_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        api.evidence_queue_traceability_audit_payload(numeric_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        api.evidence_queue_traceability_audit_payload(false_flag_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_ref"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.evidence_queue_traceability_audit_payload(unsafe_key_payload)

    unsafe_nested_payload = dict(payload)
    unsafe_nested_payload["queue_trace_rows"] = [
        {
            **payload["queue_trace_rows"][0],
            "next_step": "connect-wallet",
        },
    ]
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.evidence_queue_traceability_audit_payload(unsafe_nested_payload)


def test_reports_missing_orphan_duplicate_stale_and_redacted_traceability_diagnostics() -> None:
    report = _report(
        (
            _evidence(
                "evidence-old",
                packet_ref="packet-stale",
                last_seen_at=GENERATED_AT - timedelta(seconds=3_601),
            ),
            _evidence("evidence-orphan", packet_ref="packet-orphan"),
        ),
        (
            _queue(
                "queue-duplicate-a",
                packet_ref="packet-dup",
                evidence_refs=("evidence-missing",),
            ),
            _queue(
                "queue-duplicate-b",
                packet_ref="packet-dup",
                evidence_refs=("evidence-missing",),
            ),
            _queue(
                "queue-missing-packet",
                packet_ref=None,
                evidence_refs=(),
            ),
            _queue(
                "queue-stale",
                packet_ref="packet-stale",
                evidence_refs=("evidence-old",),
                created_at=GENERATED_AT - timedelta(minutes=1),
            ),
        ),
    )

    assert report.traceability_status == "blocked"
    assert report.recommended_report_action == "block_queue_rows_until_trace_links_are_repaired"
    assert report.evidence_reference_count == Decimal("2")
    assert report.queue_row_count == Decimal("4")
    assert report.missing_trace_link_count == Decimal("3")
    assert report.orphan_evidence_count == Decimal("1")
    assert report.duplicate_queue_reference_count == Decimal("2")
    assert report.stale_evidence_link_count == Decimal("1")
    assert report.redacted_traceability_diagnostic_count == Decimal("3")
    assert report.reason_codes == (
        "evidence_queue_traceability_missing_trace_links",
        "evidence_queue_traceability_orphan_evidence",
        "evidence_queue_traceability_duplicate_queue_references",
        "evidence_queue_traceability_stale_evidence_links",
        "evidence_queue_traceability_redacted_diagnostics",
    )
    assert tuple((row.redacted_queue_ref, row.trace_status) for row in report.queue_trace_rows) == (
        ("queue-duplicate-a", "blocked"),
        ("queue-duplicate-b", "blocked"),
        ("queue-missing-packet", "blocked"),
        ("queue-stale", "watch"),
    )
    assert report.queue_trace_rows[0].reason_codes == (
        "evidence_queue_traceability_missing_trace_links",
        "evidence_queue_traceability_duplicate_queue_references",
        "evidence_queue_traceability_redacted_diagnostics",
    )
    assert report.queue_trace_rows[2].reason_codes == (
        "evidence_queue_traceability_missing_trace_links",
        "evidence_queue_traceability_redacted_diagnostics",
    )
    assert report.queue_trace_rows[3].stale_evidence_link_count == Decimal("1")
    assert report.orphan_evidence_rows[0].redacted_evidence_ref == "evidence-orphan"
    assert report.orphan_evidence_rows[0].reason_codes == (
        "evidence_queue_traceability_orphan_evidence",
    )


def test_empty_inputs_block_without_dividing_or_emitting_execution_surfaces() -> None:
    report = _report()

    assert report.traceability_status == "blocked"
    assert report.evidence_reference_count == Decimal("0")
    assert report.queue_row_count == Decimal("0")
    assert report.reason_codes == ("evidence_queue_traceability_no_queue_rows",)
    assert report.queue_trace_rows == ()
    assert report.orphan_evidence_rows == ()


def test_dataclasses_are_frozen_decimal_only_and_report_only() -> None:
    api = _api()
    report = _report((_evidence("evidence-a"),), (_queue("queue-a"),))

    with pytest.raises(FrozenInstanceError):
        report.queue_trace_rows[0].trace_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.queue_trace_rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="stale_trace_link_seconds must be a Decimal"):
        _config(stale_trace_link_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_trace_link_count must be a Decimal"):
        api.EvidenceQueueTraceabilityQueueTraceRow(
            redacted_queue_ref="queue-a",
            team_id="politics",
            redacted_packet_ref="packet-a",
            queue_status="report_pending",
            missing_trace_link_count=1,  # type: ignore[arg-type]
            stale_evidence_link_count=Decimal("0"),
            duplicate_queue_reference_count=Decimal("0"),
            redacted_traceability_diagnostic_count=Decimal("0"),
            trace_status="pass",
            reason_codes=("evidence_queue_traceability_audit_passed",),
        )


def test_rejects_unsafe_public_refs_exact_types_and_datetime_inputs() -> None:
    api = _api()

    class ConfigSubclass(api.EvidenceQueueTraceabilityAuditConfig):
        pass

    class EvidenceSubclass(api.EvidencePacketReference):
        pass

    with pytest.raises(ValueError, match="unsafe public reference"):
        _evidence("wallet-secret-ref")
    with pytest.raises(ValueError, match="unsafe public reference"):
        _queue("queue-a", packet_ref="buy-side-packet")
    with pytest.raises(ValueError, match="evidence_refs must contain public references"):
        _queue("queue-a", evidence_refs=("market_order_payload",))
    with pytest.raises(ValueError, match="evidence_rows must be a list or tuple"):
        api.build_evidence_queue_traceability_audit_report(
            "rows",
            (),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="evidence_rows must contain"):
        api.build_evidence_queue_traceability_audit_report(
            (EvidenceSubclass.__new__(EvidenceSubclass),),
            (),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_evidence_queue_traceability_audit_report(
            (),
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_evidence_queue_traceability_audit_report(
            (),
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _evidence("evidence-a", last_seen_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="last_seen_at must not be in the future"):
        _report((_evidence("evidence-a", last_seen_at=GENERATED_AT + timedelta(seconds=1)),), ())


def test_normalizes_aware_datetimes_without_mutating_sources() -> None:
    offset = timezone(timedelta(hours=-4))
    source = _evidence(
        "evidence-offset",
        last_seen_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
    )
    queue = _queue(
        "queue-offset",
        evidence_refs=("evidence-offset",),
        created_at=datetime(2026, 7, 2, 7, 45, tzinfo=offset),
    )
    original_last_seen_at = source.last_seen_at
    original_created_at = queue.created_at

    report = _api().build_evidence_queue_traceability_audit_report(
        (source,),
        (queue,),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.queue_trace_rows[0].created_at == datetime(2026, 7, 2, 11, 45, tzinfo=UTC)
    assert report.queue_trace_rows[0].newest_evidence_link_age_seconds == Decimal("1800")
    assert source.last_seen_at is original_last_seen_at
    assert queue.created_at is original_created_at


def test_module_scope_is_pure_report_only_without_advice_io_or_package_root_exports() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api)
    lowered_source = source.lower()
    tree = ast.parse(source)

    package_exports = tuple(getattr(import_module("polymarket_alpha_lab"), "__all__", ()))
    assert "EvidenceQueueTraceabilityAuditReport" not in package_exports
    assert "build_evidence_queue_traceability_audit_report" not in package_exports
    assert "evidence_queue_traceability_audit_payload" in public_names
    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        "investment advice",
        "trade instruction",
        "position sizing",
        "market_slug",
        "question",
        "selected_side",
        "scoring_side",
        "raw_payload",
        "payload_json",
        "buy",
        "sell",
        "order",
        "account",
        "auth",
        "live",
        "psycopg",
        "supabase",
        "os.environ",
        "polymarketpublicclient",
        "requests",
        "httpx",
        "private_key",
        "wallet",
        "open(",
        ".write(",
    ):
        assert banned not in lowered_source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = ("db", "env", "cli", "psycopg", "requests", "socket")
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
